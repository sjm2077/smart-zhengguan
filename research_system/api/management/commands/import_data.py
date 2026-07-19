import os
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = '从 Excel 文件导入数据（支持 project, achievement, fund）'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Excel 文件路径')
        parser.add_argument('--table', type=str, choices=['project', 'achievement', 'fund'], required=True,
                            help='导入的目标表')
        parser.add_argument('--skip-existing', action='store_true', default=True,
                            help='如果记录已存在则跳过（默认）')
        parser.add_argument('--update-existing', action='store_true',
                            help='如果记录已存在则更新（默认跳过）')

    def handle(self, *args, **options):
        file_path = options['file_path']
        table = options['table']
        skip_existing = options['skip_existing'] and not options['update_existing']
        update_existing = options['update_existing']

        if not os.path.exists(file_path):
            raise CommandError(f"文件不存在: {file_path}")

        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            raise CommandError(f"读取 Excel 文件失败: {e}")

        self.stdout.write(f"开始导入 {table} 数据，共 {len(df)} 条记录...")

        if table == 'project':
            self.import_projects(df, skip_existing, update_existing)
        elif table == 'achievement':
            self.import_achievements(df, skip_existing, update_existing)
        elif table == 'fund':
            self.import_funds(df, skip_existing, update_existing)

        self.stdout.write(self.style.SUCCESS('导入完成！'))

    @transaction.atomic
    def import_projects(self, df, skip_existing, update_existing):
        from api.models import User, Dept, Project
        success_count = 0
        skip_count = 0
        error_count = 0

        for idx, row in df.iterrows():
            try:
                project_name = str(row['project_name']).strip()
                leader_name = str(row['leader_name']).strip()
                fund_amount = float(row['fund_amount'])

                try:
                    start_date = pd.to_datetime(row['start_date']).date()
                except Exception:
                    self.stderr.write(f"第 {idx + 2} 行 start_date 格式错误: {row['start_date']}")
                    error_count += 1
                    continue
                try:
                    end_date = pd.to_datetime(row['end_date']).date()
                except Exception:
                    self.stderr.write(f"第 {idx + 2} 行 end_date 格式错误: {row['end_date']}")
                    error_count += 1
                    continue

                if not project_name or not leader_name:
                    self.stderr.write(f"第 {idx + 2} 行缺少必填字段（项目名称或负责人）")
                    error_count += 1
                    continue

                leader, _ = User.objects.get_or_create(
                    real_name=leader_name,
                    defaults={
                        'username': f"import_{leader_name}",
                        'password': 'pbkdf2_sha256$...',
                        'role': 'teacher',
                        'title': '讲师',
                    }
                )

                dept_name = row.get('dept_name')
                if pd.isna(dept_name):
                    dept = None
                else:
                    dept, _ = Dept.objects.get_or_create(dept_name=str(dept_name).strip())

                existing = Project.objects.filter(project_name=project_name, leader=leader).first()
                if existing:
                    if skip_existing:
                        self.stdout.write(f"跳过已存在项目: {project_name}")
                        skip_count += 1
                        continue
                    elif update_existing:
                        project = existing
                    else:
                        skip_count += 1
                        continue
                else:
                    project = Project()

                project.project_name = project_name
                project.leader = leader
                project.dept = dept
                project.fund_amount = fund_amount
                project.start_date = start_date
                project.end_date = end_date
                project.project_type = row.get('project_type', '校级') if not pd.isna(row.get('project_type')) else '校级'
                project.status = row.get('status', '立项') if not pd.isna(row.get('status')) else '立项'
                project.subject = row.get('subject', '') if not pd.isna(row.get('subject')) else ''
                progress = row.get('actual_progress', 0)
                project.actual_progress = int(progress) if not pd.isna(progress) else 0

                project.save()
                success_count += 1
                self.stdout.write(f"导入项目: {project_name} (负责人: {leader_name})")

            except Exception as e:
                self.stderr.write(f"第 {idx + 2} 行导入失败: {e}")
                error_count += 1

        self.stdout.write(f"项目导入完成: 成功 {success_count} 条, 跳过 {skip_count} 条, 失败 {error_count} 条")

    @transaction.atomic
    def import_achievements(self, df, skip_existing, update_existing):
        from api.models import User, Dept, Achievement
        success_count = 0
        skip_count = 0
        error_count = 0

        for idx, row in df.iterrows():
            try:
                title = str(row['title']).strip()
                author_name = str(row['author_name']).strip()
                achievement_type = str(row['achievement_type']).strip()
                publish_year = int(row['publish_year'])

                if not title or not author_name or not achievement_type:
                    self.stderr.write(f"第 {idx + 2} 行缺少必填字段")
                    error_count += 1
                    continue

                author, _ = User.objects.get_or_create(
                    real_name=author_name,
                    defaults={
                        'username': f"import_{author_name}",
                        'password': 'pbkdf2_sha256$...',
                        'role': 'teacher',
                        'title': '讲师',
                    }
                )

                dept_name = row.get('dept_name')
                if pd.isna(dept_name):
                    dept = None
                else:
                    dept, _ = Dept.objects.get_or_create(dept_name=str(dept_name).strip())

                existing = Achievement.objects.filter(title=title, author=author, publish_year=publish_year).first()
                if existing:
                    if skip_existing:
                        self.stdout.write(f"跳过已存在成果: {title}")
                        skip_count += 1
                        continue
                    elif update_existing:
                        ach = existing
                    else:
                        skip_count += 1
                        continue
                else:
                    ach = Achievement()

                ach.title = title
                ach.author = author
                ach.dept = dept
                ach.achievement_type = achievement_type
                ach.level = row.get('level', '') if not pd.isna(row.get('level')) else ''
                ach.publish_year = publish_year
                ach.citation_count = int(row.get('citation_count', 0)) if not pd.isna(row.get('citation_count')) else 0
                is_intl = row.get('is_international', False)
                if not pd.isna(is_intl):
                    if isinstance(is_intl, str):
                        ach.is_international = is_intl.upper() == 'TRUE'
                    else:
                        ach.is_international = bool(is_intl)
                else:
                    ach.is_international = False

                ach.save()
                success_count += 1
                self.stdout.write(f"导入成果: {title} (作者: {author_name})")

            except Exception as e:
                self.stderr.write(f"第 {idx + 2} 行导入失败: {e}")
                error_count += 1

        self.stdout.write(f"成果导入完成: 成功 {success_count} 条, 跳过 {skip_count} 条, 失败 {error_count} 条")

    @transaction.atomic
    def import_funds(self, df, skip_existing, update_existing):
        from api.models import Project, FundDetail
        success_count = 0
        skip_count = 0
        error_count = 0

        for idx, row in df.iterrows():
            try:
                project_name = str(row['project_name']).strip()
                source_type = str(row['source_type']).strip()
                amount = float(row['amount'])
                year = int(row['year'])
                usage_type = str(row['usage_type']).strip()

                if not project_name or not source_type or not usage_type:
                    self.stderr.write(f"第 {idx + 2} 行缺少必填字段")
                    error_count += 1
                    continue

                project = Project.objects.filter(project_name=project_name).first()
                if not project:
                    self.stderr.write(f"第 {idx + 2} 行找不到项目: {project_name}")
                    error_count += 1
                    continue

                existing = FundDetail.objects.filter(
                    project=project,
                    source_type=source_type,
                    year=year,
                    usage_type=usage_type,
                    amount=amount
                ).first()
                if existing:
                    if skip_existing:
                        self.stdout.write(f"跳过已存在经费明细: {project_name} - {usage_type}")
                        skip_count += 1
                        continue
                    elif update_existing:
                        skip_count += 1
                        continue
                    else:
                        skip_count += 1
                        continue

                fd = FundDetail(
                    project=project,
                    source_type=source_type,
                    amount=amount,
                    year=year,
                    usage_type=usage_type
                )
                fd.save()
                success_count += 1
                self.stdout.write(f"导入经费明细: {project_name} - {usage_type} {amount}万元")

            except Exception as e:
                self.stderr.write(f"第 {idx + 2} 行导入失败: {e}")
                error_count += 1

        self.stdout.write(f"经费明细导入完成: 成功 {success_count} 条, 跳过 {skip_count} 条, 失败 {error_count} 条")