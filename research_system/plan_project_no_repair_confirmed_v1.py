import json
from collections import Counter
from pathlib import Path

from api.models import Project


OUTPUT = Path("project_no_repair_plan_confirmed_v1.json")


def norm(value):
    return str(value or "").strip()


# 只读取项目及其负责人、所属院系
projects = list(
    Project.objects
    .select_related("leader", "dept")
    .order_by("pk")
)

missing = [
    p for p in projects
    if not norm(p.project_no)
]

existing_numbers = {
    norm(p.project_no).casefold()
    for p in projects
    if norm(p.project_no)
}

print("=" * 68)
print("项目编号修复计划 V1（DRY-RUN）")
print("=" * 68)
print("数据库项目总数：", len(projects))
print("当前缺失编号：", len(missing))

# 防止数据库状态与此前审计结果不一致
expected_ids = list(range(228, 527))
actual_ids = [p.pk for p in missing]

if len(missing) != 299 or actual_ids != expected_ids:
    raise SystemExit(
        "安全检查未通过：缺失编号数量或主键范围已变化。"
        "停止生成计划，请重新审计数据库。"
    )

records = []

for p in missing:
    year = (
        str(p.start_date.year)
        if p.start_date
        else "UNDATED"
    )

    candidate = f"IMP-{year}-{p.pk:06d}"

    leader = (
        getattr(p.leader, "name", None)
        or getattr(p.leader, "username", None)
        or str(p.leader)
    ) if p.leader else ""

    dept = (
        getattr(p.dept, "dept_name", "")
        if p.dept else ""
    )

    records.append({
        "database_id": p.pk,
        "current_project_no": norm(p.project_no),
        "candidate_project_no": candidate,
        "project_name": p.project_name,
        "leader": str(leader),
        "department": str(dept),
        "start_date": (
            p.start_date.isoformat()
            if p.start_date else None
        ),
        "end_date": (
            p.end_date.isoformat()
            if p.end_date else None
        ),
        "fund_amount": str(p.fund_amount),
    })

candidate_numbers = [
    r["candidate_project_no"].casefold()
    for r in records
]

duplicate_candidates = [
    number
    for number, count in Counter(candidate_numbers).items()
    if count > 1
]

conflicts = [
    r["candidate_project_no"]
    for r in records
    if r["candidate_project_no"].casefold()
    in existing_numbers
]

ready = not duplicate_candidates and not conflicts

plan = {
    "plan_version": "v1",
    "mode": "DRY_RUN",
    "status": "READY_FOR_REVIEW" if ready else "BLOCKED",
    "database_write": False,
    "source_excel": "projects.xlsx",
    "source_excel_rows": 300,
    "matched_database_projects": 299,
    "missing_project_no_count": len(missing),
    "numbering_rule": "IMP-{start_year}-{database_primary_key:06d}",
    "number_semantics": (
        "Generated internal identifier; "
        "not an original or officially verified project number."
    ),
    "existing_numbers_overwritten": 0,
    "candidate_count": len(records),
    "candidate_duplicate_count": len(duplicate_candidates),
    "existing_number_conflict_count": len(conflicts),
    "records": records,
}

OUTPUT.write_text(
    json.dumps(plan, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print("\n候选编号数量：", len(records))
print("候选编号内部重复：", len(duplicate_candidates))
print("与现有编号冲突：", len(conflicts))
print("现有编号覆盖数量：0")
print("数据库写入：否")
print("计划状态：", plan["status"])
print("完整计划：", OUTPUT.resolve())

print("\n候选编号示例：")
for r in records[:10]:
    print(
        f"  id={r['database_id']}  "
        f"{r['candidate_project_no']}  "
        f"{r['project_name']}"
    )

print("\n本次只生成 JSON 计划，没有修改数据库。")
