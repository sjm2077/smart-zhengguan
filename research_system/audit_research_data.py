"""
科研系统数据现状审计脚本（只读）
用法：
1. 将本文件放到 D:\\research_system 项目根目录（与 manage.py 同级）。
2. 在已激活的虚拟环境中执行：
   python manage.py shell -c "exec(open('audit_research_data.py', encoding='utf-8').read())"

只读取数据库，不新增、修改或删除任何记录。
输出：data_audit_report.json
"""
import json
from collections import Counter
from pathlib import Path
from django.db.models import Count
from api.models import (
    Dept, User, Project, FundDetail, FundBudget, Achievement,
    TeacherScore, Cooperation, DeptResource, RiskWarning
)

report = {
    "audit_type": "read_only",
    "note": "本报告只反映当前数据库记录，不验证记录内容是否真实。",
    "tables": {},
    "coverage": {},
    "quality_checks": {},
    "distributions": {},
}

def counter_dict(values):
    return dict(Counter("未填写" if v in (None, "") else str(v) for v in values))

def grouped_count(queryset, field):
    rows = queryset.values(field).annotate(n=Count("id")).order_by(field)
    return {
        ("未填写" if row[field] in (None, "") else str(row[field])): row["n"]
        for row in rows
    }

def check_queryset(queryset, fields, limit=30):
    return {
        "count": queryset.count(),
        "sample": list(queryset.values(*fields)[:limit]),
    }

def check_grouped_queryset(queryset, limit=30):
    return {
        "count": queryset.count(),
        "sample": list(queryset[:limit]),
    }

# 1. 基础记录量
models = {
    "departments": Dept,
    "users_all_roles": User,
    "projects": Project,
    "fund_details": FundDetail,
    "fund_budgets": FundBudget,
    "achievements": Achievement,
    "teacher_scores": TeacherScore,
    "cooperations": Cooperation,
    "department_resources": DeptResource,
    "risk_warnings": RiskWarning,
}
for key, model in models.items():
    report["tables"][key] = model.objects.count()

teachers = User.objects.filter(role="teacher").select_related("dept")
projects = Project.objects.select_related("leader", "dept")
funds = FundDetail.objects.select_related("project")
budgets = FundBudget.objects.select_related("project")
achievements = Achievement.objects.select_related("author", "dept")
scores = TeacherScore.objects.select_related("teacher")
cooperations = Cooperation.objects.select_related("project")
resources = DeptResource.objects.select_related("dept")
warnings = RiskWarning.objects.select_related("project")

report["tables"]["teachers"] = teachers.count()
report["tables"]["admins"] = User.objects.filter(role="admin").count()

# 2. 跨模块覆盖率
teacher_count = teachers.count()
teachers_with_projects = teachers.filter(projects__isnull=False).distinct().count()
teachers_with_achievements = teachers.filter(achievements__isnull=False).distinct().count()
teachers_with_scores = teachers.filter(scores__isnull=False).distinct().count()

teacher_names = list(teachers.values_list("real_name", flat=True))
cooperation_teacher_names = set(
    cooperations.values_list("source", flat=True)
) | set(cooperations.values_list("target", flat=True))
teachers_with_cooperation = sum(1 for name in teacher_names if name in cooperation_teacher_names)

report["coverage"] = {
    "teachers_total": teacher_count,
    "teachers_with_projects": teachers_with_projects,
    "teachers_without_projects": max(0, teacher_count - teachers_with_projects),
    "teachers_with_achievements": teachers_with_achievements,
    "teachers_without_achievements": max(0, teacher_count - teachers_with_achievements),
    "teachers_with_any_performance_score": teachers_with_scores,
    "teachers_without_performance_score": max(0, teacher_count - teachers_with_scores),
    "teachers_mentioned_in_cooperation_records": teachers_with_cooperation,
    "teachers_not_mentioned_in_cooperation_records": max(0, teacher_count - teachers_with_cooperation),
    "projects_with_fund_details": projects.filter(funds__isnull=False).distinct().count(),
    "projects_without_fund_details": max(0, projects.count() - projects.filter(funds__isnull=False).distinct().count()),
    "projects_with_risk_warning": projects.filter(riskwarning__isnull=False).distinct().count(),
    "projects_without_risk_warning": max(0, projects.count() - projects.filter(riskwarning__isnull=False).distinct().count()),
}

# 3. 按年份、类型和部门分布
report["distributions"] = {
    "teachers_by_department": grouped_count(teachers, "dept__dept_name"),
    "teachers_by_title": grouped_count(teachers, "title"),
    "projects_by_start_year": grouped_count(projects, "start_date__year"),
    "projects_by_status": grouped_count(projects, "status"),
    "projects_by_type": grouped_count(projects, "project_type"),
    "projects_by_department": grouped_count(projects, "dept__dept_name"),
    "fund_details_by_year": grouped_count(funds, "year"),
    "fund_details_by_usage": grouped_count(funds, "usage_type"),
    "fund_details_by_source": grouped_count(funds, "source_type"),
    "fund_budgets_by_year": grouped_count(budgets, "year"),
    "fund_budgets_by_demo_flag": grouped_count(budgets, "is_demo"),
    "achievements_by_year": grouped_count(achievements, "publish_year"),
    "achievements_by_type": grouped_count(achievements, "achievement_type"),
    "achievements_by_level": grouped_count(achievements, "level"),
    "achievements_by_subject": grouped_count(achievements, "subject"),
    "teacher_scores_by_year": grouped_count(scores, "year"),
    "cooperations_by_project": grouped_count(cooperations, "project__project_name"),
    "department_resources_by_year": grouped_count(resources, "year"),
    "risk_warnings_by_level": grouped_count(warnings, "risk_level"),
    "risk_warnings_by_resolved": grouped_count(warnings, "is_resolved"),
}

# 4. 质量检查：只报告可疑项，不自动修正
checks = {}

checks["teachers_missing_title"] = check_queryset(
    teachers.filter(title=""), ["id", "real_name", "dept__dept_name"]
)
checks["teachers_missing_department"] = check_queryset(
    teachers.filter(dept__isnull=True), ["id", "real_name", "title"]
)
checks["projects_missing_name_or_number"] = check_queryset(
    projects.filter(project_name="") | projects.filter(project_no=""),
    ["id", "project_no", "project_name", "leader__real_name"]
)
checks["projects_invalid_progress_outside_0_100"] = check_queryset(
    projects.filter(actual_progress__lt=0) | projects.filter(actual_progress__gt=100),
    ["id", "project_no", "project_name", "actual_progress", "status"]
)
from django.db.models import F
checks["projects_start_after_end"] = check_queryset(
    projects.filter(start_date__gt=F("end_date")),
    ["id", "project_no", "project_name", "start_date", "end_date"]
)
checks["fund_details_nonpositive_amount"] = check_queryset(
    funds.filter(amount__lte=0),
    ["id", "project__project_name", "year", "usage_type", "amount"]
)
checks["fund_budgets_nonpositive_amount"] = check_queryset(
    budgets.filter(budget_amount__lte=0),
    ["id", "project__project_name", "year", "budget_amount", "is_demo", "data_source"]
)
checks["achievements_missing_title"] = check_queryset(
    achievements.filter(title=""),
    ["id", "author__real_name", "publish_year", "achievement_type"]
)
checks["achievements_negative_citation_count"] = check_queryset(
    achievements.filter(citation_count__lt=0),
    ["id", "title", "author__real_name", "citation_count"]
)
checks["teacher_scores_outside_0_100"] = check_queryset(
    scores.filter(research_score__lt=0) | scores.filter(research_score__gt=100)
    | scores.filter(teaching_score__lt=0) | scores.filter(teaching_score__gt=100)
    | scores.filter(service_score__lt=0) | scores.filter(service_score__gt=100)
    | scores.filter(comprehensive_score__lt=0) | scores.filter(comprehensive_score__gt=100),
    ["id", "teacher__real_name", "year", "research_score", "teaching_score", "service_score", "comprehensive_score"]
)
checks["teacher_score_duplicate_teacher_year"] = check_grouped_queryset(
    scores.values("teacher_id", "teacher__real_name", "year")
    .annotate(n=Count("id"))
    .filter(n__gt=1)
    .order_by("-n")
)
checks["cooperation_nonpositive_count"] = check_queryset(
    cooperations.filter(coop_count__lte=0),
    ["id", "source", "target", "project__project_name", "coop_count"]
)
checks["cooperation_self_links"] = check_queryset(
    cooperations.filter(source=F("target")),
    ["id", "source", "target", "project__project_name", "coop_count"]
)
checks["department_resource_negative_amount"] = check_queryset(
    resources.filter(input_amount__lt=0) | resources.filter(output_amount__lt=0),
    ["id", "dept__dept_name", "year", "input_amount", "output_amount"]
)
checks["department_resource_duplicate_dept_year"] = check_grouped_queryset(
    resources.values("dept_id", "dept__dept_name", "year")
    .annotate(n=Count("id"))
    .filter(n__gt=1)
    .order_by("-n")
)
checks["risk_warnings_with_project_end_date_before_warning_date"] = check_queryset(
    warnings.filter(project__end_date__lt=F("warning_date")),
    ["id", "project__project_no", "project__project_name", "warning_date", "risk_level", "is_resolved"]
)
checks["risk_warnings_duplicate_project_level_date"] = check_grouped_queryset(
    warnings.values("project_id", "project__project_name", "risk_level", "warning_date")
    .annotate(n=Count("id"))
    .filter(n__gt=1)
    .order_by("-n")
)

report["quality_checks"] = checks

# 5. 教师覆盖概况（每位教师一行，方便定位需要补齐的画像）
teacher_rows = []
for teacher in teachers.order_by("dept__dept_name", "real_name"):
    teacher_projects = Project.objects.filter(leader=teacher)
    teacher_achievements = Achievement.objects.filter(author=teacher)
    teacher_funds = FundDetail.objects.filter(project__leader=teacher)
    teacher_scores = TeacherScore.objects.filter(teacher=teacher)
    teacher_rows.append({
        "teacher_id": teacher.id,
        "teacher_name": teacher.real_name,
        "department": teacher.dept.dept_name if teacher.dept else None,
        "title": teacher.title or None,
        "project_count": teacher_projects.count(),
        "achievement_count": teacher_achievements.count(),
        "fund_detail_count": teacher_funds.count(),
        "fund_total": round(sum(float(x or 0) for x in teacher_funds.values_list("amount", flat=True)), 2),
        "score_years": sorted(set(teacher_scores.values_list("year", flat=True))),
        "cooperation_record_count": cooperations.filter(
            # Cooperation stores names as text, so match by exact teacher name.
        ).filter(source=teacher.real_name).count()
        + cooperations.filter(target=teacher.real_name).count(),
    })
report["teacher_coverage_detail"] = teacher_rows

output_path = Path("data_audit_report.json")
output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

print("=" * 72)
print("科研系统数据现状审计完成（只读，没有修改数据库）")
print("=" * 72)
print("表记录量：")
for key, value in report["tables"].items():
    print(f"  {key:<32} {value}")
print("\n跨模块覆盖：")
for key, value in report["coverage"].items():
    print(f"  {key:<48} {value}")
print("\n可疑数据项（显示样本最多 30 条，完整汇总见 JSON）：")
for key, value in report["quality_checks"].items():
    print(f"  {key:<55} {value['count']}")
print(f"\n完整报告已写入：{output_path.resolve()}")
print("注意：审计只提示可疑记录，不会自动删除或修改数据。")
