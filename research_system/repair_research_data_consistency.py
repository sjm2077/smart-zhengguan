# -*- coding: utf-8 -*-
"""
科研系统模拟数据逻辑一致性修复脚本。

默认只读预览。只有同时设置：
  RESEARCH_DATA_REPAIR_EXECUTE=1
  RESEARCH_DATA_REPAIR_CONFIRM=YES
才会写入数据库。

修复规则（基于 2026-10-25 只读审计计划）：
1. 结束日期早于审计日、状态非“结题”的项目：状态改为“结题”，进度改为 100。
   由于该项目是模拟数据且没有延期字段，统一按“已到期项目已完成”处理。
2. 进度为 100、但结束日期尚未到且状态非“结题”的项目：状态改为“审核中”，不提前标为结题。
3. 预警日期晚于关联项目结束日期：将预警日期调整到项目结束日期前 14 天；
   若早于项目开始日期，则改为项目开始日期。
4. 关联项目已结题的预警：标记为已解决，并将建议措施改为“项目已结题，预警关闭并归档”。
5. 不修改教师/负责人、系别、项目名称、项目编号、项目起止日期、经费或其他业务记录。
6. SQLite 写入前自动备份数据库；非 SQLite 数据库将拒绝执行，避免无备份写入。
"""

import json
import os
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from django.db import connection, transaction
from django.utils import timezone
from api.models import Project, RiskWarning


ROOT = Path.cwd()
PLAN_PATH = ROOT / "data_repair_plan" / "research_data_repair_plan.json"
OUT_DIR = ROOT / "data_repair_plan"
CLOSED_ACTION = "项目已结题，预警关闭并归档"

EXECUTE_FLAG = os.environ.get("RESEARCH_DATA_REPAIR_EXECUTE", "").strip()
CONFIRM_FLAG = os.environ.get("RESEARCH_DATA_REPAIR_CONFIRM", "").strip()

if bool(EXECUTE_FLAG) != bool(CONFIRM_FLAG):
    raise RuntimeError(
        "执行开关不完整。预览时请清除两个环境变量；正式写入必须同时设置 "
        "RESEARCH_DATA_REPAIR_EXECUTE=1 和 RESEARCH_DATA_REPAIR_CONFIRM=YES。"
    )

EXECUTE = EXECUTE_FLAG == "1" and CONFIRM_FLAG == "YES"


def iso(value):
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def read_plan():
    if not PLAN_PATH.exists():
        raise FileNotFoundError(
            f"找不到只读审计计划：{PLAN_PATH}\n"
            "请先确认 data_repair_plan/research_data_repair_plan.json 存在。"
        )

    with PLAN_PATH.open("r", encoding="utf-8-sig") as f:
        plan = json.load(f)

    summary = plan.get("summary", {})
    if summary.get("mode") != "READ_ONLY":
        raise RuntimeError("审计计划不是 READ_ONLY 模式，拒绝继续。")
    if summary.get("database_modified") is not False:
        raise RuntimeError("审计计划未明确记录 database_modified=false，拒绝继续。")

    audit_date = date.fromisoformat(summary["audit_date"])
    today = timezone.localdate()
    if audit_date != today:
        raise RuntimeError(
            f"审计日期为 {audit_date}，当前 Django 日期为 {today}。"
            "请重新运行只读审计，避免使用过期计划。"
        )

    return plan, audit_date


def project_snapshot_errors(candidate, project):
    expected = candidate.get("current_values", {})
    actual = {
        "id": project.pk,
        "project_no": project.project_no,
        "project_name": project.project_name,
        "start_date": iso(project.start_date),
        "end_date": iso(project.end_date),
        "status": project.status,
        "actual_progress": project.actual_progress,
        "leader": project.leader.real_name if project.leader_id else "",
        "department": project.dept.dept_name if project.dept_id else "",
    }

    errors = []
    for key in actual:
        if key in expected and expected.get(key) != actual.get(key):
            errors.append(
                f"项目ID {project.pk} 字段 {key}: "
                f"审计值={expected.get(key)!r}, 当前值={actual.get(key)!r}"
            )
    return errors


def warning_snapshot_errors(candidate, warning):
    expected = candidate.get("current_values", {})
    project = warning.project
    actual = {
        "warning_id": warning.pk,
        "project_id": warning.project_id,
        "project_start_date": iso(project.start_date) if project else None,
        "project_end_date": iso(project.end_date) if project else None,
        "warning_date": iso(warning.warning_date),
        "project_status": project.status if project else "",
        "project_actual_progress": project.actual_progress if project else None,
        "risk_level": warning.risk_level,
        "reason": warning.reason,
        "suggested_action": warning.suggested_action,
        "is_resolved": warning.is_resolved,
    }

    errors = []
    for key in actual:
        if key in expected and expected.get(key) != actual.get(key):
            errors.append(
                f"预警ID {warning.pk} 字段 {key}: "
                f"审计值={expected.get(key)!r}, 当前值={actual.get(key)!r}"
            )
    return errors


def validate_snapshot(plan, audit_date, lock=False):
    summary = plan["summary"]
    project_candidates = plan.get("project_candidates", [])
    warning_candidates = plan.get("risk_warning_candidates", [])

    if Project.objects.count() != summary.get("project_total"):
        raise RuntimeError(
            f"项目总数已变化：审计={summary.get('project_total')}，"
            f"当前={Project.objects.count()}。请重新审计。"
        )
    if RiskWarning.objects.count() != summary.get("risk_warning_total"):
        raise RuntimeError(
            f"风险预警总数已变化：审计={summary.get('risk_warning_total')}，"
            f"当前={RiskWarning.objects.count()}。请重新审计。"
        )

    project_ids = [row["id"] for row in project_candidates]
    project_qs = Project.objects.select_related("leader", "dept").filter(pk__in=project_ids)
    if lock:
        project_qs = project_qs.select_for_update()
    projects = {p.pk: p for p in project_qs}

    missing_projects = sorted(set(project_ids) - set(projects))
    if missing_projects:
        raise RuntimeError(f"审计候选项目已缺失，拒绝写入：{missing_projects}")

    errors = []
    for candidate in project_candidates:
        errors.extend(project_snapshot_errors(candidate, projects[candidate["id"]]))

    warning_ids = [row["id"] for row in warning_candidates]
    warning_qs = RiskWarning.objects.select_related(
        "project", "project__leader", "project__dept"
    ).filter(pk__in=warning_ids)
    if lock:
        warning_qs = warning_qs.select_for_update()
    warnings = {w.pk: w for w in warning_qs}

    missing_warnings = sorted(set(warning_ids) - set(warnings))
    if missing_warnings:
        raise RuntimeError(f"审计候选预警已缺失，拒绝写入：{missing_warnings}")

    for candidate in warning_candidates:
        errors.extend(warning_snapshot_errors(candidate, warnings[candidate["id"]]))

    if errors:
        detail = "\n".join(errors[:30])
        more = "" if len(errors) <= 30 else f"\n……另有 {len(errors) - 30} 项不一致"
        raise RuntimeError(
            "数据库与只读审计快照不一致，未执行任何修复。请重新生成审计计划。\n"
            + detail + more
        )

    # 对比完整数据库中的异常ID集合，防止审计后出现新异常或候选清单漏项。
    expected_overdue_ids = {
        row["id"] for row in project_candidates
        if "END_DATE_PASSED_NOT_CLOSED" in row.get("reason_codes", [])
        and row.get("end_date")
        and date.fromisoformat(row["end_date"]) < audit_date
        and row.get("status") != "结题"
    }
    current_overdue_ids = set(
        Project.objects.filter(end_date__lt=audit_date)
        .exclude(status="结题")
        .values_list("id", flat=True)
    )
    if current_overdue_ids != expected_overdue_ids:
        raise RuntimeError(
            "当前数据库中的到期未结题项目集合与审计计划不一致；"
            f"新增/未列入计划={sorted(current_overdue_ids - expected_overdue_ids)}，"
            f"计划中但当前已变化={sorted(expected_overdue_ids - current_overdue_ids)}。"
            "请重新生成只读审计计划。"
        )

    expected_late_warning_ids = {
        row["id"] for row in warning_candidates
        if "WARNING_AFTER_PROJECT_END" in row.get("reason_codes", [])
    }
    current_late_warning_ids = set()
    for warning in RiskWarning.objects.select_related("project").all():
        if (
            warning.project_id and warning.warning_date and warning.project
            and warning.project.end_date and warning.warning_date > warning.project.end_date
        ):
            current_late_warning_ids.add(warning.pk)
    if current_late_warning_ids != expected_late_warning_ids:
        raise RuntimeError(
            "当前数据库中的预警日期异常集合与审计计划不一致；"
            f"新增/未列入计划={sorted(current_late_warning_ids - expected_late_warning_ids)}，"
            f"计划中但当前已变化={sorted(expected_late_warning_ids - current_late_warning_ids)}。"
            "请重新生成只读审计计划。"
        )

    overdue_count = len(expected_overdue_ids)
    if overdue_count != summary.get("project_reason_counts", {}).get("END_DATE_PASSED_NOT_CLOSED"):
        raise RuntimeError(
            f"到期未结题候选数与审计摘要不一致：计算={overdue_count}，"
            f"摘要={summary.get('project_reason_counts', {}).get('END_DATE_PASSED_NOT_CLOSED')}"
        )

    return projects, warnings


def build_repair_plan(plan, audit_date, projects, warnings):
    project_changes = []
    close_project_ids = set()
    review_project_ids = set()

    for candidate in plan.get("project_candidates", []):
        project = projects[candidate["id"]]
        reason_codes = set(candidate.get("reason_codes", []))

        if (
            "END_DATE_PASSED_NOT_CLOSED" in reason_codes
            and project.end_date is not None
            and project.end_date < audit_date
            and project.status != "结题"
        ):
            close_project_ids.add(project.pk)
            if project.status != "结题" or project.actual_progress != 100:
                project_changes.append({
                    "project_id": project.pk,
                    "project_no": project.project_no,
                    "project_name": project.project_name,
                    "reason": "模拟数据规则：结束日期已过且没有延期字段，统一归为已结题项目。",
                    "before": {
                        "status": project.status,
                        "actual_progress": project.actual_progress,
                        "end_date": iso(project.end_date),
                    },
                    "after": {
                        "status": "结题",
                        "actual_progress": 100,
                        "end_date": iso(project.end_date),
                    },
                    "fields": ["status", "actual_progress"],
                })
            continue

        if (
            "PROGRESS_100_STATUS_NOT_CLOSED" in reason_codes
            and project.end_date is not None
            and project.end_date >= audit_date
            and project.actual_progress == 100
            and project.status != "结题"
        ):
            review_project_ids.add(project.pk)
            if project.status != "审核中":
                project_changes.append({
                    "project_id": project.pk,
                    "project_no": project.project_no,
                    "project_name": project.project_name,
                    "reason": "进度已达100%，但项目结束日期尚未到；调整为审核中，不提前标记结题。",
                    "before": {
                        "status": project.status,
                        "actual_progress": project.actual_progress,
                        "end_date": iso(project.end_date),
                    },
                    "after": {
                        "status": "审核中",
                        "actual_progress": project.actual_progress,
                        "end_date": iso(project.end_date),
                    },
                    "fields": ["status"],
                })

    expected_overdue = plan["summary"]["project_reason_counts"].get(
        "END_DATE_PASSED_NOT_CLOSED", 0
    )
    if len(close_project_ids) != expected_overdue:
        raise RuntimeError(
            f"拟结题项目数与审计结果不一致：计划={len(close_project_ids)}，"
            f"审计={expected_overdue}。"
        )

    # 对所有与本轮结题项目关联的预警统一关闭；所有预警日期晚于项目结束日期的记录，
    # 都会调整到项目结束日前14天（不足14天则使用项目开始日期）。
    all_warning_qs = RiskWarning.objects.select_related("project").order_by("id")
    warning_changes = []
    for warning in all_warning_qs:
        project = warning.project
        if project is None:
            continue

        is_late = (
            warning.warning_date is not None
            and project.end_date is not None
            and warning.warning_date > project.end_date
        )
        project_will_be_closed = project.pk in close_project_ids
        if not is_late and not project_will_be_closed:
            continue

        before = {
            "warning_date": iso(warning.warning_date),
            "is_resolved": warning.is_resolved,
            "suggested_action": warning.suggested_action,
            "project_end_date": iso(project.end_date),
            "project_start_date": iso(project.start_date),
            "project_status": project.status,
        }

        after_date = warning.warning_date
        if is_late:
            if project.start_date and project.end_date and project.start_date > project.end_date:
                raise RuntimeError(
                    f"项目ID {project.pk} 起始日期晚于结束日期，无法安全修复预警ID {warning.pk}。"
                )
            target_date = project.end_date - timedelta(days=14)
            if project.start_date and target_date < project.start_date:
                target_date = project.start_date
            after_date = target_date

        after_resolved = True if project_will_be_closed else warning.is_resolved
        after_action = CLOSED_ACTION if project_will_be_closed else warning.suggested_action

        if (
            after_date != warning.warning_date
            or after_resolved != warning.is_resolved
            or after_action != warning.suggested_action
        ):
            warning_changes.append({
                "warning_id": warning.pk,
                "project_id": project.pk,
                "project_name": project.project_name,
                "reason": (
                    "预警日期晚于项目结束日期，调整到项目结束日前14天；"
                    if is_late else ""
                ) + (
                    "关联项目本轮结题，预警同步关闭并归档。"
                    if project_will_be_closed else ""
                ),
                "before": before,
                "after": {
                    "warning_date": iso(after_date),
                    "is_resolved": after_resolved,
                    "suggested_action": after_action,
                    "project_end_date": iso(project.end_date),
                },
                "fields": [
                    field for field, changed in [
                        ("warning_date", after_date != warning.warning_date),
                        ("is_resolved", after_resolved != warning.is_resolved),
                        ("suggested_action", after_action != warning.suggested_action),
                    ] if changed
                ],
            })

    audited_late_warning_ids = {
        row["id"] for row in plan.get("risk_warning_candidates", [])
        if "WARNING_AFTER_PROJECT_END" in row.get("reason_codes", [])
    }
    planned_date_ids = {
        row["warning_id"] for row in warning_changes
        if "warning_date" in row["fields"]
    }
    if not audited_late_warning_ids.issubset(planned_date_ids):
        missing = sorted(audited_late_warning_ids - planned_date_ids)
        raise RuntimeError(f"部分审计预警未纳入日期修复计划：{missing}")

    return project_changes, warning_changes, close_project_ids, review_project_ids


def create_sqlite_backup():
    if connection.vendor != "sqlite":
        raise RuntimeError(
            f"当前数据库后端为 {connection.vendor!r}。脚本不会在未确认数据库原生备份的情况下写入。"
            "请先进行对应数据库的正式备份，再调整脚本的备份策略。"
        )

    connection.ensure_connection()
    db_name = connection.settings_dict.get("NAME")
    if not db_name or str(db_name) == ":memory:":
        raise RuntimeError("当前 SQLite 数据库不是可备份的磁盘文件，拒绝写入。")

    db_path = Path(db_name)
    if not db_path.is_absolute():
        db_path = ROOT / db_path
    if not db_path.exists():
        raise FileNotFoundError(f"找不到 SQLite 数据库文件：{db_path}")

    backup_dir = OUT_DIR / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"db_before_consistency_repair_{stamp}.sqlite3"

    # 使用 SQLite 在线备份 API，避免直接复制正在使用的数据库文件。
    source_conn = connection.connection
    destination_conn = sqlite3.connect(str(backup_path))
    try:
        source_conn.backup(destination_conn)
    finally:
        destination_conn.close()

    if not backup_path.exists() or backup_path.stat().st_size == 0:
        raise RuntimeError("SQLite 自动备份未成功生成，已中止写入。")
    return str(backup_path)


def save_report(report, filename):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / filename
    with path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return path


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plan, audit_date = read_plan()

    if len(plan.get("project_candidates", [])) != plan["summary"].get("project_candidate_count"):
        raise RuntimeError("项目候选清单数量与摘要不一致，拒绝继续。")
    if len(plan.get("risk_warning_candidates", [])) != plan["summary"].get("risk_warning_candidate_count"):
        raise RuntimeError("预警候选清单数量与摘要不一致，拒绝继续。")

    # 先只读核对快照。正式写入时，在备份后、事务内再核对一次。
    projects, warnings = validate_snapshot(plan, audit_date, lock=False)
    project_changes, warning_changes, close_ids, review_ids = build_repair_plan(
        plan, audit_date, projects, warnings
    )

    report = {
        "audit_date": audit_date.isoformat(),
        "mode": "EXECUTE" if EXECUTE else "DRY_RUN",
        "database_write_performed": False,
        "rules": [
            "结束日期早于审计日期且状态非结题：状态改为结题，进度改为100。",
            "进度100但结束日期尚未到：状态改为审核中，保留结束日期与进度。",
            "预警日期晚于项目结束日期：改为项目结束日前14天，必要时不早于项目开始日期。",
            "关联项目本轮结题：预警标记为已解决，建议措施更新为项目已结题、预警关闭并归档。",
            "不修改教师、负责人、系别、项目名称、项目编号、起止日期、经费，不新增或删除记录。",
        ],
        "project_total": Project.objects.count(),
        "risk_warning_total": RiskWarning.objects.count(),
        "project_candidate_count": len(plan.get("project_candidates", [])),
        "project_close_count": len(close_ids),
        "project_review_count": len(review_ids),
        "project_field_change_count": len(project_changes),
        "audited_late_warning_count": len(plan.get("risk_warning_candidates", [])),
        "warning_record_change_count": len(warning_changes),
        "warning_date_adjustment_count": sum(
            1 for row in warning_changes if "warning_date" in row["fields"]
        ),
        "warning_resolution_count": sum(
            1 for row in warning_changes if "is_resolved" in row["fields"]
        ),
        "project_changes": project_changes,
        "warning_changes": warning_changes,
        "backup_path": None,
    }

    if not EXECUTE:
        report_path = save_report(report, "consistency_repair_preview.json")
        print("=" * 78)
        print("科研系统模拟数据逻辑修复：只读预览（数据库未修改）")
        print("=" * 78)
        print(f"审计日期：{audit_date}")
        print(f"项目总数：{report['project_total']}")
        print(f"项目拟结题并将进度设为100：{report['project_close_count']}")
        print(f"进度100且结束日期未到、拟转为审核中：{report['project_review_count']}")
        print(f"拟调整预警日期：{report['warning_date_adjustment_count']}")
        print(f"拟标记为已解决的预警：{report['warning_resolution_count']}")
        print(f"拟修改预警记录数：{report['warning_record_change_count']}")
        print(f"预览报告：{report_path}")
        print("数据库写入：否")
        print("确认预览结果后，备份并执行正式写入。")
        return

    # 写入前先自动备份，然后在事务内锁定并再次校验快照。
    backup_path = create_sqlite_backup()
    with transaction.atomic():
        projects, warnings = validate_snapshot(plan, audit_date, lock=True)
        project_changes, warning_changes, close_ids, review_ids = build_repair_plan(
            plan, audit_date, projects, warnings
        )

        project_candidate_ids = {
            row["id"] for row in plan.get("project_candidates", [])
        }
        for project_id in sorted(close_ids):
            project = Project.objects.select_for_update().get(pk=project_id)
            changed = []
            if project.status != "结题":
                project.status = "结题"
                changed.append("status")
            if project.actual_progress != 100:
                project.actual_progress = 100
                changed.append("actual_progress")
            if changed:
                project.save(update_fields=changed)

        for project_id in sorted(review_ids):
            project = Project.objects.select_for_update().get(pk=project_id)
            if project.status != "审核中":
                project.status = "审核中"
                project.save(update_fields=["status"])

        # 重新读取预警，使用数据库中的最终项目状态处理预警。
        warning_queryset = RiskWarning.objects.select_related("project").select_for_update().order_by("id")
        for warning in warning_queryset:
            project = warning.project
            if project is None:
                continue

            is_late = (
                warning.warning_date is not None
                and project.end_date is not None
                and warning.warning_date > project.end_date
            )
            project_will_be_closed = project.pk in close_ids
            if not is_late and not project_will_be_closed:
                continue

            changed = []
            if is_late:
                if project.start_date and project.end_date and project.start_date > project.end_date:
                    raise RuntimeError(
                        f"项目ID {project.pk} 起始日期晚于结束日期，无法安全修复预警ID {warning.pk}。"
                    )
                target_date = project.end_date - timedelta(days=14)
                if project.start_date and target_date < project.start_date:
                    target_date = project.start_date
                if warning.warning_date != target_date:
                    warning.warning_date = target_date
                    changed.append("warning_date")

            if project_will_be_closed:
                if not warning.is_resolved:
                    warning.is_resolved = True
                    changed.append("is_resolved")
                if warning.suggested_action != CLOSED_ACTION:
                    warning.suggested_action = CLOSED_ACTION
                    changed.append("suggested_action")

            if changed:
                warning.save(update_fields=changed)

        # 写入后进行一致性验证；失败将触发事务回滚。
        remaining_overdue = Project.objects.filter(
            end_date__lt=audit_date
        ).exclude(status="结题").count()
        if remaining_overdue != 0:
            raise RuntimeError(
                f"写入后仍有 {remaining_overdue} 个结束日期已过且状态非结题的项目，事务回滚。"
            )

        remaining_late_warnings = 0
        for warning in RiskWarning.objects.select_related("project").all():
            if (
                warning.project_id
                and warning.warning_date
                and warning.project.end_date
                and warning.warning_date > warning.project.end_date
            ):
                remaining_late_warnings += 1
        if remaining_late_warnings != 0:
            raise RuntimeError(
                f"写入后仍有 {remaining_late_warnings} 条预警日期晚于项目结束日期，事务回滚。"
            )

        for project_id in close_ids:
            project = Project.objects.get(pk=project_id)
            if project.status != "结题" or project.actual_progress != 100:
                raise RuntimeError(
                    f"项目ID {project_id} 未达到结题/100%状态，事务回滚。"
                )

        unresolved_closed_warnings = RiskWarning.objects.filter(
            project_id__in=close_ids, is_resolved=False
        ).count()
        if unresolved_closed_warnings:
            raise RuntimeError(
                f"结题项目仍关联 {unresolved_closed_warnings} 条未解决预警，事务回滚。"
            )

    report["database_write_performed"] = bool(project_changes or warning_changes)
    report["backup_path"] = backup_path
    report["mode"] = "EXECUTE"
    report["post_validation"] = {
        "overdue_non_closed_project_count": Project.objects.filter(
            end_date__lt=audit_date
        ).exclude(status="结题").count(),
        "warning_after_project_end_count": sum(
            1 for w in RiskWarning.objects.select_related("project").all()
            if w.project_id and w.warning_date and w.project.end_date
            and w.warning_date > w.project.end_date
        ),
    }
    report_path = save_report(report, "consistency_repair_execution_report.json")

    print("=" * 78)
    print("科研系统模拟数据逻辑修复：执行完成")
    print("=" * 78)
    print(f"审计日期：{audit_date}")
    print(f"数据库写入：{'是' if report['database_write_performed'] else '否（无需修改）'}")
    print(f"项目结题并设为100%：{len(close_ids)}")
    print(f"项目转为审核中：{len(review_ids)}")
    print(f"预警日期调整：{report['warning_date_adjustment_count']}")
    print(f"预警标记为已解决：{report['warning_resolution_count']}")
    print(f"数据库备份：{backup_path}")
    print(f"执行报告：{report_path}")
    print("验证结果：")
    print(json.dumps(report["post_validation"], ensure_ascii=False, indent=2))


main()
