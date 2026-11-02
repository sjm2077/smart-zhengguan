"""
科研系统项目编号补齐脚本：默认 DRY-RUN，不修改数据库。

用途：
- 为 project_no 为空/全空格的项目生成明确标识为演示用途的编号：
  DEMO-<项目开始年份>-<数据库主键>
- 不覆盖任何已有项目编号；
- 不改项目名称，不删除重复名称项目；
- 先输出完整 JSON 计划，供人工检查。

在 D:\\research_system（与 manage.py 同级）执行：
python manage.py shell -c "exec(open('repair_missing_project_numbers.py', encoding='utf-8').read())"

仅在完成数据库备份、检查 dry-run JSON 并明确决定写入后，才设置两个环境变量执行：
$env:RESEARCH_PROJECT_NO_REPAIR_EXECUTE = "1"
$env:RESEARCH_PROJECT_NO_REPAIR_CONFIRM = "YES"
python manage.py shell -c "exec(open('repair_missing_project_numbers.py', encoding='utf-8').read())"
Remove-Item Env:RESEARCH_PROJECT_NO_REPAIR_EXECUTE
Remove-Item Env:RESEARCH_PROJECT_NO_REPAIR_CONFIRM

注意：生成的 DEMO 编号是系统演示标识，不是经过核实的正式科研项目编号。
"""
import json
import os
from collections import defaultdict
from pathlib import Path

from django.db import transaction
from api.models import Project

EXECUTE = (
    os.environ.get("RESEARCH_PROJECT_NO_REPAIR_EXECUTE", "").strip() == "1"
    and os.environ.get("RESEARCH_PROJECT_NO_REPAIR_CONFIRM", "").strip() == "YES"
)

def clean(value):
    return str(value or "").strip()

def make_demo_no(project):
    year = project.start_date.year if project.start_date else "UNK"
    return f"DEMO-{year}-{project.pk:06d}"

def build_plan(projects):
    existing_numbers = {
        clean(p.project_no)
        for p in projects
        if clean(p.project_no)
    }

    missing = [p for p in projects if not clean(p.project_no)]
    plan_rows = []
    proposed_numbers = []

    for p in missing:
        proposed = make_demo_no(p)
        proposed_numbers.append(proposed)
        plan_rows.append({
            "project_id": p.pk,
            "current_project_no": p.project_no,
            "proposed_project_no": proposed,
            "project_name": p.project_name,
            "leader": getattr(p.leader, "real_name", ""),
            "department": getattr(p.dept, "dept_name", "") if p.dept_id else "",
            "project_type": p.project_type,
            "status": p.status,
            "start_date": str(p.start_date) if p.start_date else None,
            "end_date": str(p.end_date) if p.end_date else None,
        })

    collisions_with_existing = sorted(set(proposed_numbers) & existing_numbers)
    proposed_counts = defaultdict(int)
    for value in proposed_numbers:
        proposed_counts[value] += 1
    internal_duplicates = sorted(
        value for value, count in proposed_counts.items() if count > 1
    )

    by_name = defaultdict(list)
    for p in projects:
        name = clean(p.project_name)
        if name:
            by_name[name].append({
                "project_id": p.pk,
                "project_no": p.project_no,
                "leader": getattr(p.leader, "real_name", ""),
                "department": getattr(p.dept, "dept_name", "") if p.dept_id else "",
                "start_date": str(p.start_date) if p.start_date else None,
                "end_date": str(p.end_date) if p.end_date else None,
                "status": p.status,
            })

    duplicate_names = []
    for name, rows in by_name.items():
        if len(rows) > 1:
            duplicate_names.append({
                "project_name": name,
                "record_count": len(rows),
                "records": rows,
                "note": "名称重复只作为核查线索；不同负责人/年份的同名项目不自动判定为重复记录。",
            })
    duplicate_names.sort(key=lambda x: (-x["record_count"], x["project_name"]))

    return {
        "audit_type": "project_no_repair_plan",
        "mode": "EXECUTE" if EXECUTE else "DRY_RUN",
        "database_write_performed": False,
        "project_total": len(projects),
        "project_no_missing_count": len(missing),
        "existing_nonblank_project_no_count": len(existing_numbers),
        "proposed_number_scheme": "DEMO-<start_year>-<project_primary_key_6_digits>",
        "proposed_number_collision_with_existing_count": len(collisions_with_existing),
        "proposed_number_internal_duplicate_count": len(internal_duplicates),
        "proposed_number_collisions_with_existing": collisions_with_existing,
        "proposed_number_internal_duplicates": internal_duplicates,
        "project_no_candidates": plan_rows,
        "duplicate_project_name_distinct_count": len(duplicate_names),
        "records_in_duplicate_name_groups": sum(x["record_count"] for x in duplicate_names),
        "duplicate_project_name_groups": duplicate_names,
        "rules": [
            "只处理 project_no 为空或全空格的项目。",
            "不覆盖已有项目编号。",
            "不更改 project_name，不删除项目记录。",
            "候选编号以 DEMO 开头，不能当作正式科研项目编号。",
            "任何编号冲突都会阻止写入。",
        ],
    }

def main():
    if EXECUTE:
        with transaction.atomic():
            projects = list(
                Project.objects.select_for_update()
                .select_related("leader", "dept")
                .order_by("id")
            )
            report = build_plan(projects)

            if report["proposed_number_collision_with_existing_count"]:
                raise RuntimeError(
                    "发现候选编号与已有编号冲突，已中止；数据库未修改。"
                )
            if report["proposed_number_internal_duplicate_count"]:
                raise RuntimeError(
                    "发现候选编号内部重复，已中止；数据库未修改。"
                )

            candidates = {
                row["project_id"]: row["proposed_project_no"]
                for row in report["project_no_candidates"]
            }
            to_update = [
                p for p in projects
                if not clean(p.project_no) and p.pk in candidates
            ]
            for p in to_update:
                p.project_no = candidates[p.pk]

            if to_update:
                Project.objects.bulk_update(to_update, ["project_no"])

            report["database_write_performed"] = bool(to_update)
            report["updated_record_count"] = len(to_update)
            report["mode"] = "EXECUTE"
    else:
        projects = list(
            Project.objects.select_related("leader", "dept").order_by("id")
        )
        report = build_plan(projects)
        report["database_write_performed"] = False
        report["updated_record_count"] = 0

    out = Path("project_no_repair_plan.json")
    out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    print("=" * 76)
    print("科研系统项目编号补齐计划")
    print("=" * 76)
    print("运行模式：", report["mode"])
    print("项目总数：", report["project_total"])
    print("缺失项目编号：", report["project_no_missing_count"])
    print("拟生成编号数：", len(report["project_no_candidates"]))
    print("与已有编号冲突：", report["proposed_number_collision_with_existing_count"])
    print("候选编号内部重复：", report["proposed_number_internal_duplicate_count"])
    print("重复项目名称组数：", report["duplicate_project_name_distinct_count"])
    print("重复名称涉及记录数：", report["records_in_duplicate_name_groups"])
    print("本次数据库写入：", "是" if report["database_write_performed"] else "否")
    print("实际更新记录数：", report.get("updated_record_count", 0))
    print("\n候选编号示例（最多 15 条）：")
    for row in report["project_no_candidates"][:15]:
        print(
            f"  id={row['project_id']:<5} "
            f"{row['proposed_project_no']:<22} "
            f"{row['project_name']} / {row['leader']}"
        )
    print(f"\n完整计划：{out.resolve()}")

    if not EXECUTE:
        print("\n当前是只读 DRY-RUN。数据库没有修改。")
        print("先检查 JSON 中的全部候选编号；不要把 DEMO 编号当作正式项目编号。")
    else:
        print("\n写入执行结束。请再次运行只读审计，确认缺失编号数量归零且已有编号未改变。")

main()
