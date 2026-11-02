"""
科研系统数据深度核查脚本（只读，不修改数据库）
放在 D:\\research_system 项目根目录，与 manage.py 同级。

执行：
python manage.py shell -c "exec(open('audit_research_data_detail.py', encoding='utf-8').read())"

输出：
data_audit_detail_report.json

用途：
1. 精确拆分项目名称/编号缺失情况；
2. 检查项目编号、项目名称重复情况；
3. 查看教师绩效的年份分布及逐教师覆盖情况；
4. 查看科研合作端点与教师姓名的匹配情况；
5. 列出预警日期晚于项目结束日期的记录；
6. 补充项目经费覆盖情况。
本脚本只读，不新增、修改或删除任何数据库记录。
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

from django.db.models import Count
from api.models import (
    User, Project, FundDetail, FundBudget, Achievement,
    TeacherScore, Cooperation, DeptResource, RiskWarning
)

def norm(value):
    return str(value or "").strip()

def duplicate_values(rows, field, label_field=None):
    buckets = defaultdict(list)
    for row in rows:
        value = norm(row.get(field))
        if value:
            buckets[value].append({
                "id": row.get("id"),
                "project_no": row.get("project_no"),
                "project_name": row.get("project_name"),
                "leader": row.get("leader__real_name"),
            })
    duplicates = []
    for value, items in buckets.items():
        if len(items) > 1:
            duplicates.append({
                "value": value,
                "count": len(items),
                "records": items[:10],
            })
    return sorted(duplicates, key=lambda x: (-x["count"], x["value"]))

report = {
    "audit_type": "read_only_detail",
    "note": "本报告用于定位数据质量问题；字段缺失或姓名不匹配不自动等于错误，也不代表数据真实性已核验。",
}

# 1. 项目名称/编号缺失精确分类
project_rows = list(
    Project.objects.select_related("leader", "dept").values(
        "id", "project_no", "project_name", "leader__real_name",
        "dept__dept_name", "project_type", "status",
        "start_date", "end_date", "actual_progress", "fund_amount"
    ).order_by("id")
)

missing_no = []
missing_name = []
missing_both = []
complete = []
for row in project_rows:
    no_missing = not norm(row.get("project_no"))
    name_missing = not norm(row.get("project_name"))
    if no_missing:
        missing_no.append(row)
    if name_missing:
        missing_name.append(row)
    if no_missing and name_missing:
        missing_both.append(row)
    if not no_missing and not name_missing:
        complete.append(row)

report["project_identity"] = {
    "total_projects": len(project_rows),
    "missing_project_no_count": len(missing_no),
    "missing_project_name_count": len(missing_name),
    "missing_both_count": len(missing_both),
    "both_present_count": len(complete),
    "missing_project_no_sample": missing_no[:30],
    "missing_project_name_sample": missing_name[:30],
    "missing_both_sample": missing_both[:30],
    "duplicate_project_no": duplicate_values(project_rows, "project_no")[:50],
    "duplicate_project_name": duplicate_values(project_rows, "project_name")[:50],
}

# 2. 教师绩效年份覆盖
teachers = list(
    User.objects.filter(role="teacher")
    .values("id", "real_name", "dept__dept_name", "title")
    .order_by("dept__dept_name", "real_name")
)
teacher_names = {norm(t["real_name"]) for t in teachers if norm(t["real_name"])}

score_rows = list(
    TeacherScore.objects.select_related("teacher").values(
        "id", "teacher_id", "teacher__real_name", "year",
        "research_score", "teaching_score", "service_score", "comprehensive_score"
    ).order_by("year", "teacher__real_name")
)
scores_by_teacher = defaultdict(list)
teachers_by_year = defaultdict(set)
for row in score_rows:
    scores_by_teacher[row["teacher_id"]].append(row)
    teachers_by_year[row["year"]].add(row["teacher_id"])

score_years = sorted(teachers_by_year)
report["teacher_score_coverage"] = {
    "score_record_count": len(score_rows),
    "teachers_total": len(teachers),
    "teachers_with_scores": len(scores_by_teacher),
    "teachers_without_scores_count": sum(1 for t in teachers if t["id"] not in scores_by_teacher),
    "records_by_year": dict(sorted(Counter(str(r["year"]) for r in score_rows).items())),
    "teachers_covered_by_year": {
        str(year): len(teachers_by_year[year]) for year in score_years
    },
    "teachers_without_scores": [
        {
            "teacher_id": t["id"],
            "teacher_name": t["real_name"],
            "department": t["dept__dept_name"],
            "title": t["title"],
        }
        for t in teachers if t["id"] not in scores_by_teacher
    ],
    "teacher_years_detail": [
        {
            "teacher_id": t["id"],
            "teacher_name": t["real_name"],
            "department": t["dept__dept_name"],
            "score_years": sorted({r["year"] for r in scores_by_teacher.get(t["id"], [])}),
            "score_record_count": len(scores_by_teacher.get(t["id"], [])),
        }
        for t in teachers
    ],
    "duplicate_teacher_year": list(
        TeacherScore.objects.values("teacher_id", "teacher__real_name", "year")
        .annotate(n=Count("id")).filter(n__gt=1).order_by("-n")
    ),
}

# 3. 合作关系端点匹配情况
cooperation_rows = list(
    Cooperation.objects.select_related("project").values(
        "id", "source", "target", "project_id", "project__project_no",
        "project__project_name", "coop_count"
    ).order_by("id")
)
for row in cooperation_rows:
    row["source_matches_teacher_name"] = norm(row["source"]) in teacher_names
    row["target_matches_teacher_name"] = norm(row["target"]) in teacher_names
    row["at_least_one_teacher_endpoint"] = (
        row["source_matches_teacher_name"] or row["target_matches_teacher_name"]
    )

report["cooperation_detail"] = {
    "record_count": len(cooperation_rows),
    "records_with_both_endpoints_matching_teacher_names": sum(
        1 for r in cooperation_rows
        if r["source_matches_teacher_name"] and r["target_matches_teacher_name"]
    ),
    "records_with_at_least_one_teacher_endpoint": sum(
        1 for r in cooperation_rows if r["at_least_one_teacher_endpoint"]
    ),
    "records_with_no_exact_teacher_name_endpoint": sum(
        1 for r in cooperation_rows if not r["at_least_one_teacher_endpoint"]
    ),
    "all_records": cooperation_rows,
    "note": "source/target 可以是外部机构名称；未匹配教师姓名不应直接当作错误。请结合业务含义核实。",
}

# 4. 预警日期晚于项目结束日期的记录
warning_rows = []
for w in RiskWarning.objects.select_related("project").order_by("warning_date", "id"):
    if w.warning_date and w.project.end_date and w.warning_date > w.project.end_date:
        warning_rows.append({
            "warning_id": w.id,
            "project_id": w.project_id,
            "project_no": w.project.project_no,
            "project_name": w.project.project_name,
            "project_status": w.project.status,
            "project_start_date": w.project.start_date,
            "project_end_date": w.project.end_date,
            "actual_progress": w.project.actual_progress,
            "warning_date": w.warning_date,
            "risk_level": w.risk_level,
            "reason": w.reason,
            "suggested_action": w.suggested_action,
            "is_resolved": w.is_resolved,
        })

report["risk_warning_review"] = {
    "warning_total": RiskWarning.objects.count(),
    "warning_date_after_project_end_count": len(warning_rows),
    "records": warning_rows,
}

# 5. 经费与预算覆盖情况
projects_with_funds = Project.objects.filter(funds__isnull=False).distinct().count()
projects_with_budgets = Project.objects.filter(budgets__isnull=False).distinct().count()
report["funding_coverage"] = {
    "projects_total": Project.objects.count(),
    "projects_with_fund_details": projects_with_funds,
    "projects_without_fund_details": Project.objects.count() - projects_with_funds,
    "fund_detail_records": FundDetail.objects.count(),
    "projects_with_budgets": projects_with_budgets,
    "projects_without_budgets": Project.objects.count() - projects_with_budgets,
    "fund_budget_records": FundBudget.objects.count(),
    "demo_budget_records": FundBudget.objects.filter(is_demo=True).count(),
    "formal_budget_records": FundBudget.objects.filter(is_demo=False).count(),
    "achievement_records": Achievement.objects.count(),
    "department_resource_records": DeptResource.objects.count(),
}

out = Path("data_audit_detail_report.json")
out.write_text(
    json.dumps(report, ensure_ascii=False, indent=2, default=str),
    encoding="utf-8"
)

print("=" * 76)
print("科研系统数据深度核查完成（只读；未修改数据库）")
print("=" * 76)
print("项目字段缺失：")
for key in (
    "total_projects", "missing_project_no_count", "missing_project_name_count",
    "missing_both_count", "both_present_count"
):
    print(f"  {key:<42} {report['project_identity'][key]}")
print("重复项目编号：", len(report["project_identity"]["duplicate_project_no"]))
print("重复项目名称：", len(report["project_identity"]["duplicate_project_name"]))
print("\n教师绩效：")
for key in (
    "score_record_count", "teachers_total", "teachers_with_scores",
    "teachers_without_scores_count"
):
    print(f"  {key:<42} {report['teacher_score_coverage'][key]}")
print("绩效记录按年份：", report["teacher_score_coverage"]["records_by_year"])
print("各年份覆盖教师数：", report["teacher_score_coverage"]["teachers_covered_by_year"])
print("\n科研合作：")
for key in (
    "record_count", "records_with_both_endpoints_matching_teacher_names",
    "records_with_at_least_one_teacher_endpoint", "records_with_no_exact_teacher_name_endpoint"
):
    print(f"  {key:<58} {report['cooperation_detail'][key]}")
print("\n预警日期晚于项目结束日期：", report["risk_warning_review"]["warning_date_after_project_end_count"])
print("\n经费覆盖：")
for key, value in report["funding_coverage"].items():
    print(f"  {key:<42} {value}")
print(f"\n完整报告：{out.resolve()}")
print("请注意：脚本只定位可疑项，不自动修复；外部机构合作端点不一定是错误。")
