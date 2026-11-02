import json
import sys
from collections import Counter
from pathlib import Path

from django.db import transaction
from api.models import Project


PLAN_PATH = Path("project_no_repair_plan_confirmed_v1.json")
EXECUTE = "--execute" in sys.argv


def norm(value):
    return str(value or "").strip()


def get_leader(p):
    if not p.leader:
        return ""
    return str(
        getattr(p.leader, "name", None)
        or getattr(p.leader, "username", None)
        or p.leader
    )


def get_department(p):
    return (
        str(getattr(p.dept, "dept_name", "") or "")
        if p.dept else ""
    )


def get_date(value):
    return value.isoformat() if value else None


def validate_plan():
    if not PLAN_PATH.exists():
        raise RuntimeError(f"找不到修复计划：{PLAN_PATH.resolve()}")

    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8-sig"))

    if plan.get("mode") != "DRY_RUN":
        raise RuntimeError("计划模式不正确，停止操作。")

    if plan.get("database_write") is not False:
        raise RuntimeError("计划未明确声明只读，停止操作。")

    if plan.get("status") != "READY_FOR_REVIEW":
        raise RuntimeError("计划状态不是 READY_FOR_REVIEW，停止操作。")

    records = plan.get("records", [])
    expected_count = plan.get("missing_project_no_count")

    if expected_count != 299 or len(records) != 299:
        raise RuntimeError("计划记录数不是预期的 299 条，停止操作。")

    ids = [r.get("database_id") for r in records]
    candidates = [norm(r.get("candidate_project_no")) for r in records]

    if len(set(ids)) != len(ids) or None in ids:
        raise RuntimeError("计划中存在重复或无效的数据库主键。")

    if any(not candidate for candidate in candidates):
        raise RuntimeError("存在空候选编号。")

    if len(set(x.casefold() for x in candidates)) != len(candidates):
        raise RuntimeError("候选编号重复，停止操作。")

    if any(r.get("current_project_no") for r in records):
        raise RuntimeError("计划包含原本已有编号的记录，停止操作。")

    return plan, records


def apply_or_preview():
    plan, records = validate_plan()

    print("=" * 68)
    print("项目编号修复 V1 — 实时复核")
    print("=" * 68)
    print("模式：", "正式执行" if EXECUTE else "DRY-RUN")
    print("修复计划：", PLAN_PATH.resolve())

    with transaction.atomic():
        # 锁定并读取当前项目，确保写入前数据没有发生意外变化
        projects = list(
            Project.objects.select_for_update().order_by("pk")
        )
        by_id = {p.pk: p for p in projects}

        planned_ids = {r["database_id"] for r in records}
        live_missing_ids = {
            p.pk for p in projects if not norm(p.project_no)
        }

        if len(projects) != 377:
            raise RuntimeError("数据库项目总数已变化，停止操作。")

        if len(live_missing_ids) != 299:
            raise RuntimeError("数据库缺失编号数量已变化，停止操作。")

        if live_missing_ids != planned_ids:
            raise RuntimeError("当前缺失编号的项目与计划不一致。")

        existing_numbers = {
            norm(p.project_no).casefold()
            for p in projects if norm(p.project_no)
        }

        prepared = []

        for record in records:
            pk = record["database_id"]
            p = by_id.get(pk)

            if p is None:
                raise RuntimeError(f"数据库记录不存在：id={pk}")

            if norm(p.project_no):
                raise RuntimeError(f"id={pk} 已有编号，停止操作。")

            # 确认项目关键字段仍与生成计划时一致
            checks = {
                "project_name": p.project_name,
                "leader": get_leader(p),
                "department": get_department(p),
                "start_date": get_date(p.start_date),
                "end_date": get_date(p.end_date),
                "fund_amount": str(p.fund_amount),
            }

            for field, actual in checks.items():
                if str(actual or "") != str(record.get(field) or ""):
                    raise RuntimeError(
                        f"id={pk} 的 {field} 已发生变化，停止操作。"
                    )

            year = str(p.start_date.year) if p.start_date else "UNDATED"
            expected = f"IMP-{year}-{p.pk:06d}"
            candidate = norm(record["candidate_project_no"])

            if candidate != expected:
                raise RuntimeError(
                    f"id={pk} 的候选编号不符合编号规则。"
                )

            if candidate.casefold() in existing_numbers:
                raise RuntimeError(
                    f"候选编号与现有编号冲突：{candidate}"
                )

            prepared.append((p, candidate))

        print("\n实时复核结果：")
        print("数据库项目总数：", len(projects))
        print("缺失编号记录：", len(live_missing_ids))
        print("待处理记录：", len(prepared))
        print("现有编号覆盖：0")
        print("候选编号冲突：0")

        if not EXECUTE:
            print("\nDRY-RUN 通过：没有修改数据库。")
            print("请核对以上结果后，再明确执行正式写入。")
            return

        # 所有检查通过后才开始写入；发生异常时事务整体回滚
        for p, candidate in prepared:
            p.project_no = candidate
            p.save(update_fields=["project_no"])

        print("\n事务内已完成全部候选编号写入。")

    # 事务提交后，再次核实最终结果
    updated = list(
        Project.objects.filter(pk__in=[r["database_id"] for r in records])
        .values_list("pk", "project_no")
    )
    final_map = dict(updated)

    errors = [
        (p.pk, candidate)
        for p, candidate in prepared
        if final_map.get(p.pk) != candidate
    ]

    remaining = Project.objects.filter(
        project_no__isnull=True
    ).count() + Project.objects.filter(project_no="").count()

    if errors:
        print("警告：提交后复核发现异常：", errors[:10])
        raise RuntimeError("提交后复核失败，请停止后续数据操作。")

    print("\n正式写入完成。")
    print("本次更新记录：", len(prepared))
    print("本次编号写入失败：0")
    print("计划记录最终核验：全部一致")
    print("当前仍为空的编号记录：", remaining)


apply_or_preview()
