import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'research_system.settings')
django.setup()

from api.models import User, Project, FundDetail, Achievement, Dept

TEACHER_ID = 70  # 张教授的 ID


def safe_fix():
    print(f"为教师 ID={TEACHER_ID} 丰富数据（保留原有项目，追加新项目）...")
    try:
        teacher = User.objects.get(id=TEACHER_ID)
    except User.DoesNotExist:
        print(f"错误：教师 ID={TEACHER_ID} 不存在！")
        return

    # 获取教师所属的系（如果没有系，则使用第一个系）
    dept = teacher.dept
    if not dept:
        dept = Dept.objects.first()
        if not dept:
            print("错误：没有任何系别，请先运行 generate_mock_data 生成基础数据。")
            return
    print(f"教师所属系别: {dept.dept_name} (id={dept.id})")

    # 1. 创建 5 个新项目（如果已存在同名项目，则跳过）
    projects_data = [
        {"name": "公共政策优化研究", "funds": [32, 18, 25, 12, 8, 5]},
        {"name": "数字政府评估体系构建", "funds": [28, 22, 30, 10, 6, 4]},
        {"name": "乡村振兴战略实施路径", "funds": [35, 15, 20, 8, 7, 5]},
        {"name": "基层治理能力现代化", "funds": [30, 20, 28, 15, 10, 7]},
        {"name": "社会保障体系完善研究", "funds": [25, 25, 22, 12, 9, 7]},
    ]
    categories = ['人员费', '调研费', '设备费', '会议费', '出版费', '其他']
    created_count = 0

    for pd in projects_data:
        # 检查是否已存在同名项目（可选：防止重复）
        existing = Project.objects.filter(project_name=pd["name"], leader=teacher).first()
        if existing:
            print(f"项目 {pd['name']} 已存在，跳过创建。")
            continue

        project = Project.objects.create(
            project_no=f"XM{date.today().year}{teacher.id}{created_count + 1:03d}",
            project_name=pd["name"],
            leader=teacher,
            dept=dept,
            subject="公共管理",  # 如果模型中无此字段，请注释或删除
            project_type="国家级",
            fund_amount=sum(pd["funds"]),
            start_date=date(2025, 1, 1),
            end_date=date(2027, 12, 31),
            status="在研",
            actual_progress=70 - created_count * 10
        )
        created_count += 1

        # 添加经费明细
        for cat, amt in zip(categories, pd["funds"]):
            FundDetail.objects.create(
                project=project,
                source_type="国家社科",
                amount=amt,
                year=2025,
                usage_type=cat
            )
        print(f"✓ 创建项目: {project.project_name}, 经费总计 {sum(pd['funds'])} 万")

    # 2. 增加成果（如果已有成果，则追加，不删除原有）
    achievement_types = [
        ("CSSCI期刊", 4),
        ("核心期刊", 3),
        ("研究报告", 2),
        ("专著", 2),
        ("决策咨询", 1),
    ]
    existing_ach_count = Achievement.objects.filter(author=teacher).count()
    added = 0
    for atype, count in achievement_types:
        for i in range(count):
            Achievement.objects.create(
                title=f"{atype}成果_{existing_ach_count + added + 1}",
                author=teacher,
                dept=dept,
                achievement_type=atype,
                level="国家级" if atype == "CSSCI期刊" else "省部级",
                publish_year=2025,
                citation_count=10,
                is_international=False
            )
            added += 1
    print(f"✓ 追加了 {added} 项成果，现有成果总数: {existing_ach_count + added}")

    print("\n数据丰富完成！刷新教师版页面即可看到新项目和新成果，经费下拉框切换项目时数据会变化。")


if __name__ == "__main__":
    safe_fix()