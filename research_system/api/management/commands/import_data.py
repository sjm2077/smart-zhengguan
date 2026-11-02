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
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅预览项目导入，不写入数据库（仅适用于 --table project）'
        )
        parser.add_argument(
            '--allow-same-name-different-fields',
            action='store_true',
            help='仅在确认同名同负责人但属性不同确为独立项目时，允许新增；默认将其作为冲突跳过'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        table = options['table']
        skip_existing = options['skip_existing'] and not options['update_existing']
        update_existing = options['update_existing']
        dry_run = options.get('dry_run', False)
        allow_same_name_different_fields = options.get(
            'allow_same_name_different_fields', False
        )

        if dry_run and table != 'project':
            raise CommandError('--dry-run 目前仅支持 --table project')

        if allow_same_name_different_fields and table != 'project':
            raise CommandError(
                '--allow-same-name-different-fields 仅适用于 --table project'
            )

        if not os.path.exists(file_path):
            raise CommandError(f"文件不存在: {file_path}")

        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            raise CommandError(f"读取 Excel 文件失败: {e}")

        self.stdout.write(f"开始导入 {table} 数据，共 {len(df)} 条记录...")

        if table == 'project':
            self.import_projects(
                df,
                skip_existing,
                update_existing,
                dry_run=dry_run,
                allow_same_name_different_fields=allow_same_name_different_fields
            )
        elif table == 'achievement':
            self.import_achievements(df, skip_existing, update_existing)
        elif table == 'fund':
            self.import_funds(df, skip_existing, update_existing)

        if dry_run:
            self.stdout.write(
                self.style.WARNING('预览完成：本次没有写入数据库。')
            )
        else:
            self.stdout.write(self.style.SUCCESS('导入完成！'))

    @transaction.atomic
    def import_projects(
        self,
        df,
        skip_existing,
        update_existing,
        dry_run=False,
        allow_same_name_different_fields=False
    ):
        from decimal import Decimal, InvalidOperation
        from api.models import User, Dept, Project

        required_columns = {
            'project_name',
            'leader_name',
            'fund_amount',
            'start_date',
            'end_date',
        }
        missing_columns = required_columns - set(df.columns)

        if missing_columns:
            raise CommandError(
                f"项目 Excel 缺少必需字段：{', '.join(sorted(missing_columns))}"
            )

        created_count = 0
        updated_count = 0
        skip_count = 0
        error_count = 0
        conflict_count = 0

        # 防止同一份 Excel 中完全相同的项目被重复处理。
        seen_signatures = set()

        type_choices = {str(value) for value, _ in Project.TYPE_CHOICES}
        status_choices = {str(value) for value, _ in Project.STATUS_CHOICES}

        def text_value(row, key, default=''):
            value = row.get(key, default)
            if pd.isna(value):
                return default
            return str(value).strip()

        def make_internal_project_no(project):
            # 使用项目开始年份和数据库主键生成内部编号。
            base = f"IMP-{project.start_date.year}-{project.pk:06d}"
            candidate = base
            suffix = 1

            # 避免与已有编号发生冲突。
            while Project.objects.filter(project_no=candidate).exclude(
                pk=project.pk
            ).exists():
                candidate = f"{base}-{suffix}"
                suffix += 1

            return candidate

        for idx, row in df.iterrows():
            try:
                # 每一行使用独立保存点，单条失败不会影响其他行。
                with transaction.atomic():
                    project_name = text_value(row, 'project_name')
                    leader_name = text_value(row, 'leader_name')

                    if not project_name or not leader_name:
                        raise ValueError('项目名称或负责人为空')

                    fund_raw = row.get('fund_amount')
                    if pd.isna(fund_raw):
                        raise ValueError('经费金额为空')

                    try:
                        fund_amount = Decimal(str(fund_raw).strip()).quantize(
                            Decimal('0.01')
                        )
                    except (InvalidOperation, ValueError):
                        raise ValueError(f'经费金额格式错误：{fund_raw}')

                    if not fund_amount.is_finite() or fund_amount < 0:
                        raise ValueError(f'经费金额无效：{fund_raw}')

                    start_raw = row.get('start_date')
                    end_raw = row.get('end_date')
                    if pd.isna(start_raw) or pd.isna(end_raw):
                        raise ValueError('项目开始日期或结束日期为空')

                    start_date = pd.to_datetime(
                        start_raw, errors='raise'
                    ).date()
                    end_date = pd.to_datetime(
                        end_raw, errors='raise'
                    ).date()

                    if start_date > end_date:
                        raise ValueError('项目开始日期晚于结束日期')

                    project_type = (
                        text_value(row, 'project_type', '校级') or '校级'
                    )
                    status = text_value(row, 'status', '立项') or '立项'
                    subject = text_value(row, 'subject', '')

                    if project_type not in type_choices:
                        raise ValueError(
                            f'项目类型不符合模型选项：{project_type}'
                        )
                    if status not in status_choices:
                        raise ValueError(
                            f'项目状态不符合模型选项：{status}'
                        )

                    progress_raw = row.get('actual_progress', 0)
                    if pd.isna(progress_raw):
                        progress = 0
                    else:
                        try:
                            progress_number = float(progress_raw)
                        except (TypeError, ValueError):
                            raise ValueError(
                                f'项目进度格式错误：{progress_raw}'
                            )

                        if not progress_number.is_integer():
                            raise ValueError(
                                f'项目进度必须为整数：{progress_raw}'
                            )

                        progress = int(progress_number)

                    if not 0 <= progress <= 100:
                        raise ValueError(
                            f'项目进度必须在 0—100 之间：{progress}'
                        )

                    # 预览模式只查询负责人，不创建用户。
                    if dry_run:
                        leader = User.objects.filter(
                            real_name=leader_name
                        ).order_by('id').first()

                        if leader is None:
                            raise ValueError(
                                f'负责人不存在，预览模式不会创建用户：{leader_name}'
                            )
                    else:
                        leader, _ = User.objects.get_or_create(
                            real_name=leader_name,
                            defaults={
                                'username': f'import_{leader_name}',
                                'password': 'pbkdf2_sha256$...',
                                'role': 'teacher',
                                'title': '讲师',
                            }
                        )

                    # 部门字段允许为空。
                    dept_name = text_value(row, 'dept_name', '')
                    if dept_name:
                        if dry_run:
                            dept = Dept.objects.filter(
                                dept_name=dept_name
                            ).first()

                            if dept is None:
                                raise ValueError(
                                    f'部门不存在，预览模式不会创建部门：{dept_name}'
                                )
                        else:
                            dept, _ = Dept.objects.get_or_create(
                                dept_name=dept_name
                            )
                    else:
                        dept = None

                    # 若源 Excel 有稳定项目编号，优先使用编号匹配。
                    source_project_no = text_value(row, 'project_no', '')

                    signature_filters = {
                        'project_name': project_name,
                        'leader': leader,
                        'dept': dept,
                        'fund_amount': fund_amount,
                        'start_date': start_date,
                        'end_date': end_date,
                        'project_type': project_type,
                        'status': status,
                        'subject': subject,
                        'actual_progress': progress,
                    }

                    signature_key = (
                        source_project_no,
                        project_name,
                        leader.pk,
                        dept.pk if dept else None,
                        str(fund_amount),
                        start_date,
                        end_date,
                        project_type,
                        status,
                        subject,
                        progress,
                    )

                    if signature_key in seen_signatures:
                        skip_count += 1
                        self.stdout.write(
                            f'跳过 Excel 内重复记录：{project_name}'
                        )
                        continue

                    signature_qs = Project.objects.filter(**signature_filters)
                    existing = None

                    if source_project_no:
                        # 有明确编号时，编号优先。
                        existing = Project.objects.filter(
                            project_no=source_project_no
                        ).first()

                        if existing is None:
                            exact_count = signature_qs.count()
                            if exact_count > 1:
                                raise ValueError(
                                    '完整项目属性匹配到多条数据库记录，'
                                    '无法自动判断应使用哪条记录'
                                )
                            if exact_count == 1:
                                exact = signature_qs.first()
                                raise ValueError(
                                    f'Excel 编号 {source_project_no} 与数据库'
                                    f'同属性项目编号 {exact.project_no} 不一致，'
                                    '需要人工核实'
                                )
                    else:
                        # 没有编号时，完整属性唯一匹配才认定为已有项目。
                        exact_count = signature_qs.count()
                        if exact_count > 1:
                            raise ValueError(
                                '完整项目属性匹配到多条数据库记录，'
                                '无法安全自动合并'
                            )
                        if exact_count == 1:
                            existing = signature_qs.first()

                    seen_signatures.add(signature_key)

                    if existing is not None:
                        if skip_existing:
                            skip_count += 1
                            self.stdout.write(
                                f'跳过已存在项目：{project_name}'
                            )
                            continue

                        if not update_existing:
                            skip_count += 1
                            continue

                        project = existing
                        is_new = False
                    else:
                        project = Project()
                        is_new = True

                        if source_project_no:
                            project.project_no = source_project_no

                        # 同名同负责人但属性不同，不能仅凭字段差异就断定为独立项目。
                        # 默认保守处理：标记冲突并跳过，避免误新增重复项目。
                        similar_count = Project.objects.filter(
                            project_name=project_name,
                            leader=leader
                        ).count()

                        if similar_count and not allow_same_name_different_fields:
                            conflict_count += 1
                            skip_count += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f'冲突待人工核查：项目“{project_name}”'
                                    f'已存在同名同负责人记录，但属性不同；'
                                    f'本次默认跳过，不新增、不覆盖。'
                                )
                            )
                            continue

                        if similar_count and allow_same_name_different_fields:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'已启用显式确认选项：项目“{project_name}”'
                                    f'存在同名同负责人记录但属性不同；'
                                    f'本次按独立项目处理。'
                                )
                            )

                    # 预览模式仅计数和输出，不保存任何模型。
                    if dry_run:
                        if is_new:
                            created_count += 1
                            self.stdout.write(
                                f'[DRY-RUN] 计划新增：{project_name}；'
                                '正式执行时生成内部编号'
                            )
                        else:
                            updated_count += 1
                            self.stdout.write(
                                f'[DRY-RUN] 计划更新：{project_name}；'
                                f'保留原编号 {project.project_no}'
                            )
                        continue

                    project.project_name = project_name
                    project.leader = leader
                    project.dept = dept
                    project.fund_amount = fund_amount
                    project.start_date = start_date
                    project.end_date = end_date
                    project.project_type = project_type
                    project.status = status
                    project.subject = subject
                    project.actual_progress = progress

                    project.save()

                    # 对没有来源编号的新项目生成内部编号。
                    if not project.project_no:
                        project.project_no = make_internal_project_no(project)
                        project.save(update_fields=['project_no'])

                    if is_new:
                        created_count += 1
                        self.stdout.write(
                            f'新增项目：{project_name}（编号：{project.project_no}）'
                        )
                    else:
                        updated_count += 1
                        self.stdout.write(
                            f'更新项目：{project_name}（保留编号：{project.project_no}）'
                        )

            except Exception as e:
                error_count += 1
                self.stderr.write(f'第 {idx + 2} 行项目导入失败：{e}')

        title = '项目导入预览' if dry_run else '项目导入'
        self.stdout.write(
            f'{title}完成：新增 {created_count} 条，'
            f'更新 {updated_count} 条，跳过 {skip_count} 条，'
            f'冲突待人工核查 {conflict_count} 条，失败 {error_count} 条'
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY-RUN 模式：数据库没有被修改。')
            )

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