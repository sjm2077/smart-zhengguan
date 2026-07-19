import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'research_system.settings')
django.setup()

from api.models import Project, FundDetail, Achievement

TEACHER_ID = 70          # 修改为您的教师 ID
DEPT_ID = 1              # 假设公共管理系 id=1，请根据实际情况修改

def fix_teacher_data():
    print(f"开始修复教师 ID={TEACHER_ID} 的数据...")

    projects = Project.objects.filter(leader_id=TEACHER_ID)
    if not projects.exists():
        print("该教师名下没有任何项目，无需修复。")
        return

    new_names = [
        "公共政策优化研究",
        "数字政府评估体系构建",
        "乡村振兴战略实施路径",
        "基层治理能力现代化",
        "社会保障体系完善研究",
    ]
    for idx, project in enumerate(projects):
        suffix = f"_{idx+1}" if len(projects) > len(new_names) else ""
        new_name = new_names[idx % len(new_names)] + suffix
        project.project_name = new_name
        project.save()
        print(f"✓ 项目 {project.id} 已更名为: {project.project_name}")   # 修正点：project.id

    deleted_count, _ = FundDetail.objects.filter(project__in=projects).delete()
    print(f"✓ 已删除 {deleted_count} 条旧的经费明细")

    usage_data = [
        ('人员费', 32),
        ('调研费', 18),
        ('设备费', 25),
        ('会议费', 12),
        ('出版费', 8),
        ('其他', 5),
    ]
    for project in projects:
        for usage_type, amount in usage_data:
            FundDetail.objects.create(
                project=project,
                source_type='横向课题',
                amount=amount,
                year=2025,
                usage_type=usage_type
            )
        print(f"✓ 为项目 {project.project_name} 添加了经费明细")

    if Achievement.objects.filter(author_id=TEACHER_ID).count() == 0:
        achievement_types = [
            ('CSSCI期刊', 3),
            ('核心期刊', 2),
            ('研究报告', 1),
            ('专著', 1),
        ]
        for atype, count in achievement_types:
            for _ in range(count):
                Achievement.objects.create(
                    title=f"{atype}成果示例",
                    author_id=TEACHER_ID,
                    dept_id=DEPT_ID,
                    achievement_type=atype,
                    level="国家级" if atype == "CSSCI期刊" else "省部级",
                    publish_year=2025,
                    citation_count=10,
                    is_international=False
                )
        print("✓ 已为该教师添加成果示例")
    else:
        print("该教师已有成果，跳过成果添加。")

    print("\n数据修复完成！请刷新教师版页面查看效果。")

if __name__ == "__main__":
    fix_teacher_data()