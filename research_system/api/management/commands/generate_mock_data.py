import random
from datetime import date
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from api.models import Dept, User, Project, FundDetail, Achievement, TeacherScore, Cooperation, DeptResource, RiskWarning

class Command(BaseCommand):
    help = '生成2021-2025年的模拟数据'

    def handle(self, *args, **options):
        self.stdout.write("开始生成模拟数据...")

        # 1. 清空现有数据（仅开发测试用）
        RiskWarning.objects.all().delete()
        Cooperation.objects.all().delete()
        DeptResource.objects.all().delete()
        TeacherScore.objects.all().delete()
        Achievement.objects.all().delete()
        FundDetail.objects.all().delete()
        Project.objects.all().delete()
        User.objects.all().delete()
        Dept.objects.all().delete()
        self.stdout.write("已清空旧数据")

        # 2. 创建系别
        dept_names = ['科学社会主义系', '政治学系', '国际政治系', '公共管理系']
        depts = {}
        for name in dept_names:
            dept = Dept.objects.create(dept_name=name)
            depts[name] = dept
        self.stdout.write(f"创建 {len(depts)} 个系别")

        # 3. 创建用户（教师 + 管理员）
        teachers = []
        teacher_names = [
            ('张教授', '教授'), ('李教授', '教授'), ('王教授', '教授'), ('刘教授', '教授'),
            ('赵教授', '教授'), ('孙教授', '副教授'), ('周教授', '副教授'), ('吴教授', '副教授'),
            ('郑老师', '讲师'), ('钱老师', '讲师'), ('冯老师', '讲师'), ('陈老师', '讲师'),
            ('褚老师', '讲师'), ('卫老师', '讲师'), ('蒋老师', '讲师'), ('沈老师', '讲师')
        ]
        admin = User.objects.create(
            username='admin',
            password=make_password('admin123'),
            real_name='管理员',
            role='admin',
            title='',
            dept=None
        )
        for i, (name, title) in enumerate(teacher_names):
            dept = depts[random.choice(dept_names)]
            teacher = User.objects.create(
                username=f'teacher{i+1}',
                password=make_password('teacher123'),
                real_name=name,
                role='teacher',
                title=title,
                dept=dept
            )
            teachers.append(teacher)
        self.stdout.write(f"创建 1 位管理员, {len(teachers)} 位教师")
        # 确保每个系至少有一名教师
        for dept in depts.values():
            if not any(t.dept == dept for t in teachers):
                default_teacher = User.objects.create(
                    username=f'teacher_{dept.id}',
                    password=make_password('teacher123'),
                    real_name=f'{dept.dept_name}教师',
                    role='teacher',
                    title='讲师',
                    dept=dept
                )
                teachers.append(default_teacher)
                self.stdout.write(f"为 {dept.dept_name} 补充一名教师")

        # 4. 生成项目、经费明细、成果、绩效等（2021-2025年）
        years = list(range(2021, 2026))
        project_types = ['国家级', '省部级', '横向', '校级']
        statuses = ['在研', '结题', '立项', '审核中']
        source_types = ['国家社科', '教育部', '省级项目', '横向课题', '政府委托']
        usage_types = ['设备费', '业务费', '劳务费', '会议费', '出版费', '其他']
        achievement_types = ['期刊论文', '学术著作', '研究报告', '专利', '获奖', '决策咨询']
        levels = ['CSSCI', 'SSCI', '核心期刊', '国家级出版社', '省级采纳']

        # 为每个教师每年生成绩效数据
        for teacher in teachers:
            for year in years:
                base = 70 + (year - 2021) * 3 + random.randint(-5, 5)
                research = min(98, max(60, base))
                teaching = min(98, max(60, base + random.randint(-3, 3)))
                service = min(98, max(60, base + random.randint(-5, 5)))
                comprehensive = round((research * 0.5 + teaching * 0.3 + service * 0.2), 2)
                TeacherScore.objects.create(
                    teacher=teacher,
                    year=year,
                    research_score=research,
                    teaching_score=teaching,
                    service_score=service,
                    comprehensive_score=comprehensive
                )

        # 生成项目（每系每年约2-5个项目）
        projects = []
        subject_list = ['行政管理', '政治学理论', '公共政策', '社会保障', '国际关系']
        for dept in depts.values():
            for year in years:
                num_projects = random.randint(2, 5)
                for _ in range(num_projects):
                    leader = random.choice([t for t in teachers if t.dept == dept])
                    ptype = random.choice(project_types)
                    status = random.choice(statuses)
                    start_year = year - random.randint(0, 2)
                    start_date = date(start_year, random.randint(1, 12), random.randint(1, 28))
                    end_year = start_year + random.randint(1, 3)
                    end_date = date(end_year, random.randint(1, 12), random.randint(1, 28))
                    fund = round(random.uniform(10, 300), 2)
                    progress = random.randint(0, 100) if status != '结题' else 100
                    project = Project.objects.create(
                        project_no=f'XM{year}{dept.id}{random.randint(100,999)}',
                        project_name=f'{dept.dept_name}{year}年度{"".join(random.sample(["研究","分析","机制","路径","评估"],2))}',
                        leader=leader,
                        dept=dept,
                        subject=random.choice(subject_list),
                        project_type=ptype,
                        fund_amount=fund,
                        start_date=start_date,
                        end_date=end_date,
                        status=status,
                        actual_progress=progress
                    )
                    projects.append(project)

                    # 生成经费明细
                    num_funds = random.randint(2, 5)
                    remaining = fund
                    for i in range(num_funds):
                        if i == num_funds - 1:
                            amount = round(remaining, 2)
                        else:
                            amount = round(random.uniform(5, remaining / (num_funds - i)), 2)
                            remaining -= amount
                        source = random.choice(source_types)
                        usage = random.choice(usage_types)
                        FundDetail.objects.create(
                            project=project,
                            source_type=source,
                            amount=amount,
                            year=year,
                            usage_type=usage
                        )

        self.stdout.write(f"生成 {len(projects)} 个项目及对应经费明细")

        # 5. 生成成果
        achievements = []
        for teacher in teachers:
            for year in years:
                num_ach = random.randint(1, 4)
                for _ in range(num_ach):
                    atype = random.choice(achievement_types)
                    level_val = random.choice(levels) if atype in ['期刊论文','学术著作'] else ''
                    citation = random.randint(0, 50) if atype == '期刊论文' else 0
                    is_intl = random.choice([True, False]) if teacher.dept.dept_name == '国际政治系' else False
                    subject_list = ['行政管理', '政治学理论', '公共政策', '社会保障', '国际关系']
                    citation = random.randint(0, 80)  # 随机 0-80
                    subject = random.choice(subject_list)
                    ach = Achievement.objects.create(
                        title=f'{teacher.real_name}{year}年成果：{" ".join(random.sample(["治理","政策","现代化","创新","比较"],2))}',
                        author=teacher,
                        dept=teacher.dept,
                        achievement_type=atype,
                        level=level_val,
                        publish_year=year,
                        citation_count=citation,
                        is_international=is_intl,
                        subject=subject,
                    )
                    achievements.append(ach)
        self.stdout.write(f"生成 {len(achievements)} 项成果")

        # 6. 生成合作网络
        external_orgs = ['省政府研究室', '民政部智库', '山东大学智库', '兄弟高校公管院', '中国社科院']
        coop_count = 0
        for _ in range(30):
            if random.random() > 0.3:
                t1 = random.choice(teachers)
                t2 = random.choice([t for t in teachers if t != t1])
                source = t1.real_name
                target = t2.real_name
            else:
                source = random.choice(teachers).real_name
                target = random.choice(external_orgs)
            project = random.choice(projects)
            cnt = random.randint(1, 5)
            Cooperation.objects.create(
                source=source,
                target=target,
                project=project,
                coop_count=cnt
            )
            coop_count += 1
        self.stdout.write(f"生成 {coop_count} 条合作记录")

        # 7. 生成学科资源投入产出数据
        for dept in depts.values():
            for year in years:
                input_amt = round(random.uniform(50, 200), 2)
                output_amt = round(random.uniform(30, 180), 2)
                lab_cnt = random.randint(0, 5) if dept.dept_name in ['公共管理系','政治学系'] else random.randint(0, 2)
                DeptResource.objects.create(
                    dept=dept,
                    year=year,
                    input_amount=input_amt,
                    output_amount=output_amt,
                    lab_count=lab_cnt
                )
        self.stdout.write(f"生成 {len(depts)*len(years)} 条学科资源记录")

        # 8. 生成风险预警
        warnings = []
        for project in projects:
            if project.status in ['在研','立项'] and project.actual_progress < 50:
                level = '高' if project.actual_progress < 30 else '中'
                reason = '进度严重滞后' if project.actual_progress < 30 else '进度偏慢'
                action = '加快调研进度' if project.actual_progress < 50 else '补充中期报告'
                RiskWarning.objects.create(
                    project=project,
                    warning_date=date(2025, random.randint(1, 6), random.randint(1, 28)),
                    risk_level=level,
                    reason=reason,
                    suggested_action=action,
                    is_resolved=False
                )
                warnings.append(project)
        self.stdout.write(f"生成 {len(warnings)} 条风险预警")

        self.stdout.write(self.style.SUCCESS("模拟数据生成完成！"))