# -*- coding: utf-8 -*-
"""科研系统只读数据修复计划生成器。

在 D:\\research_system 项目根目录运行：
python manage.py shell -c "exec(open('plan_research_data_repair.py', encoding='utf-8').read())"

只读取 Django 模型；仅在本地生成报告文件，不写入数据库。
"""
import csv
import json
from collections import Counter
from pathlib import Path

from django.utils import timezone
from api.models import Project, RiskWarning

ROOT = Path.cwd()
OUT_DIR = ROOT / "data_repair_plan"
OUT_DIR.mkdir(parents=True, exist_ok=True)  # 仅创建本地报告目录
AUDIT_DATE = timezone.localdate()


def iso(value):
    return value.isoformat() if value is not None and hasattr(value, "isoformat") else value


def source_group(project_no):
    value = (project_no or "").strip()
    if value.startswith("IMP-"):
        return "IMP编号（疑似Excel导入）"
    if value.startswith("XM"):
        return "XM编号（疑似原有/模拟数据）"
    return "其他/待确认"


def json_text(value):
    return json.dumps(value, ensure_ascii=False, default=str)


def add_reason(reasons, codes, counter, code, message):
    reasons.append(message)
    codes.append(code)
    counter[code] += 1


def write_csv(path, columns, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


# -------------------- 项目候选记录：只读 --------------------
project_candidates = []
project_reason_counts = Counter()
project_qs = Project.objects.select_related("leader", "dept").all().order_by("id")
project_total = project_qs.count()

for p in project_qs:
    reasons, codes, proposed = [], [], {}
    status, progress = p.status, p.actual_progress
    start_date, end_date = p.start_date, p.end_date

    if end_date and end_date < AUDIT_DATE and status != "结题":
        add_reason(
            reasons, codes, project_reason_counts, "END_DATE_PASSED_NOT_CLOSED",
            "结束日期早于审计日期但状态不是‘结题’；这本身不能证明项目已结题，也不能证明已获延期。",
        )
        if progress == 100:
            proposed["status"] = {
                "current": status, "suggested": "结题",
                "note": "仅供人工审核；须先核对正式结题/验收材料，不得直接批量写入。",
            }
        else:
            proposed["status"] = {
                "current": status, "suggested": None,
                "note": "暂不预设新状态；需根据正式结题、延期或变更材料人工决定。",
            }
            proposed["end_date"] = {
                "current": iso(end_date), "suggested": None,
                "note": "不猜测新日期；如有延期，只能依据正式批复/变更文件确定。",
            }

    if progress == 100 and status != "结题":
        add_reason(
            reasons, codes, project_reason_counts, "PROGRESS_100_STATUS_NOT_CLOSED",
            "进度为100但状态不是‘结题’；需核对正式验收/结题材料及状态登记口径。",
        )
        proposed.setdefault("status", {
            "current": status, "suggested": "结题",
            "note": "仅供人工审核；须核对正式结题/验收材料后再决定。",
        })

    if status == "结题" and progress != 100:
        add_reason(
            reasons, codes, project_reason_counts, "CLOSED_PROGRESS_NOT_100",
            "状态为‘结题’但进度不是100；需核实进度字段或结题状态是否登记正确。",
        )
        proposed["actual_progress"] = {
            "current": progress, "suggested": None,
            "note": "不自动改为100；应依据正式验收材料确认正确值。",
        }

    if progress is not None and (progress < 0 or progress > 100):
        add_reason(
            reasons, codes, project_reason_counts, "PROGRESS_OUT_OF_RANGE",
            "项目进度超出0—100范围；需要回查原始数据。",
        )
        proposed["actual_progress"] = {
            "current": progress, "suggested": None,
            "note": "不采用截断或猜测值；根据原始记录核实。",
        }

    if start_date and end_date and start_date > end_date:
        add_reason(
            reasons, codes, project_reason_counts, "START_AFTER_END",
            "项目开始日期晚于结束日期；需要核对原始立项/合同/变更文件。",
        )
        proposed["start_date"] = {
            "current": iso(start_date), "suggested": None,
            "note": "需依据原始文件确认，不自动修改。",
        }
        proposed["end_date"] = {
            "current": iso(end_date), "suggested": None,
            "note": "需依据原始文件确认，不自动修改。",
        }

    if not codes:
        continue

    leader = p.leader.real_name if p.leader_id else ""
    dept = p.dept.dept_name if p.dept_id else ""
    current = {
        "id": p.id, "project_no": p.project_no, "project_name": p.project_name,
        "source_group": source_group(p.project_no), "leader": leader, "department": dept,
        "start_date": iso(start_date), "end_date": iso(end_date),
        "status": status, "actual_progress": progress,
    }
    actions = []
    if "END_DATE_PASSED_NOT_CLOSED" in codes:
        if progress == 100:
            actions.append("核对正式结题/验收材料；确认已正式结题后才考虑将状态改为‘结题’。")
        else:
            actions.append("核对延期批复、项目变更或结题材料；不得猜测新结束日期或直接改为结题。")
    if "PROGRESS_100_STATUS_NOT_CLOSED" in codes:
        actions.append("核对正式结题/验收材料；不得仅凭进度100自动改状态。")
    if "CLOSED_PROGRESS_NOT_100" in codes:
        actions.append("核对结题验收材料及进度字段；不得仅凭状态直接将进度改为100。")
    if "PROGRESS_OUT_OF_RANGE" in codes:
        actions.append("回查项目原始记录，确认正确进度后再修正。")
    if "START_AFTER_END" in codes:
        actions.append("核对立项文件、合同或变更文件，确认正确起止日期。")

    project_candidates.append({
        "id": p.id, "project_no": p.project_no, "source_group": source_group(p.project_no),
        "project_name": p.project_name, "leader": leader, "department": dept,
        "start_date": iso(start_date), "end_date": iso(end_date),
        "status": status, "actual_progress": progress,
        "reason_codes": codes, "reason": " ".join(reasons),
        "review_action": " ".join(actions), "requires_human_confirmation": True,
        "current_values": current, "proposed_values": proposed,
    })


# -------------------- 风险预警候选记录：只读 --------------------
risk_candidates = []
risk_reason_counts = Counter()
risk_qs = RiskWarning.objects.select_related("project", "project__leader", "project__dept").all().order_by("id")
risk_total = risk_qs.count()

for w in risk_qs:
    p = w.project if w.project_id else None
    reasons, codes, proposed = [], [], {}
    if p is not None:
        if w.warning_date and p.end_date and w.warning_date > p.end_date:
            add_reason(
                reasons, codes, risk_reason_counts, "WARNING_AFTER_PROJECT_END",
                "预警日期晚于项目结束日期；可能是结束后追踪/补录，也可能是日期误录，不能仅据此判错。",
            )
            proposed["warning_date"] = {
                "current": iso(w.warning_date), "suggested": None,
                "note": "暂不修改；核实原始预警记录后再决定。",
            }
        if w.warning_date and p.start_date and w.warning_date < p.start_date:
            add_reason(
                reasons, codes, risk_reason_counts, "WARNING_BEFORE_PROJECT_START",
                "预警日期早于项目开始日期；需核对预警日期及项目起始日期来源。",
            )
            proposed["warning_date"] = {
                "current": iso(w.warning_date), "suggested": None,
                "note": "不自动修改；需依据原始预警记录和项目立项文件核实。",
            }
    if not codes:
        continue

    project_no = p.project_no if p else ""
    project_name = p.project_name if p else ""
    project_start = iso(p.start_date) if p else None
    project_end = iso(p.end_date) if p else None
    project_status = p.status if p else ""
    project_progress = p.actual_progress if p else None
    current = {
        "warning_id": w.id, "project_id": w.project_id, "project_no": project_no,
        "project_name": project_name, "project_start_date": project_start,
        "project_end_date": project_end, "warning_date": iso(w.warning_date),
        "project_status": project_status, "project_actual_progress": project_progress,
        "risk_level": w.risk_level, "reason": w.reason,
        "suggested_action": w.suggested_action, "is_resolved": w.is_resolved,
    }
    risk_candidates.append({
        "id": w.id, "project_id": w.project_id, "project_no": project_no,
        "project_name": project_name, "project_start_date": project_start,
        "project_end_date": project_end, "warning_date": iso(w.warning_date),
        "project_status": project_status, "project_actual_progress": project_progress,
        "risk_level": w.risk_level, "warning_reason": w.reason,
        "suggested_action": w.suggested_action, "is_resolved": w.is_resolved,
        "reason_codes": codes, "reason": " ".join(reasons),
        "review_action": "核实是否为结束后追踪/补录，或日期误录；只有取得原始记录依据后才考虑修改。",
        "requires_human_confirmation": True,
        "current_values": current, "proposed_values": proposed,
    })


summary = {
    "audit_date": AUDIT_DATE.isoformat(),
    "mode": "READ_ONLY",
    "database_modified": False,
    "project_total": project_total,
    "project_candidate_count": len(project_candidates),
    "project_reason_counts": dict(project_reason_counts),
    "risk_warning_total": risk_total,
    "risk_warning_candidate_count": len(risk_candidates),
    "risk_warning_reason_counts": dict(risk_reason_counts),
    "note": "suggested为null表示现有信息不足以可靠推断修复值；不代表应将数据库字段改为空。所有候选项均需人工确认。",
}

report = {
    "summary": summary,
    "policy": [
        "本脚本只读取数据库，不执行数据库写入。",
        "结束日期已过且状态非结题，不等于项目必然应结题；可能存在延期、变更或历史数据问题。",
        "进度100且状态非结题，只作为核对正式验收/结题材料的线索。",
        "结题状态但进度非100时，不自动将进度改为100。",
        "预警日期晚于项目结束日期，可能是结束后追踪或补录，不自动改日期。",
        "正式写入前应备份数据库并再次核对全部拟修改值。",
    ],
    "project_candidates": project_candidates,
    "risk_warning_candidates": risk_candidates,
}

json_path = OUT_DIR / "research_data_repair_plan.json"
project_csv_path = OUT_DIR / "project_repair_candidates.csv"
risk_csv_path = OUT_DIR / "risk_warning_review_candidates.csv"
summary_path = OUT_DIR / "README_repair_plan.txt"

with json_path.open("w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2, default=str)

project_columns = [
    "id", "project_no", "source_group", "project_name", "leader", "department",
    "start_date", "end_date", "status", "actual_progress", "reason_codes", "reason",
    "review_action", "requires_human_confirmation", "current_values_json", "proposed_values_json",
]
project_csv_rows = []
for r in project_candidates:
    project_csv_rows.append({
        **{k: r.get(k) for k in project_columns if k in r},
        "reason_codes": "；".join(r["reason_codes"]),
        "current_values_json": json_text(r["current_values"]),
        "proposed_values_json": json_text(r["proposed_values"]),
    })
write_csv(project_csv_path, project_columns, project_csv_rows)

risk_columns = [
    "id", "project_id", "project_no", "project_name", "project_start_date", "project_end_date",
    "warning_date", "project_status", "project_actual_progress", "risk_level", "warning_reason",
    "suggested_action", "is_resolved", "reason_codes", "reason", "review_action",
    "requires_human_confirmation", "current_values_json", "proposed_values_json",
]
risk_csv_rows = []
for r in risk_candidates:
    risk_csv_rows.append({
        **{k: r.get(k) for k in risk_columns if k in r},
        "reason_codes": "；".join(r["reason_codes"]),
        "current_values_json": json_text(r["current_values"]),
        "proposed_values_json": json_text(r["proposed_values"]),
    })
write_csv(risk_csv_path, risk_columns, risk_csv_rows)

summary_text = "\n".join([
    "科研系统只读数据修复计划", "=" * 60,
    f"审计日期：{summary['audit_date']}", "数据库写入：否",
    f"项目总数：{project_total}", f"项目候选记录数：{len(project_candidates)}",
    f"项目候选原因计数：{json_text(dict(project_reason_counts))}",
    f"风险预警总数：{risk_total}", f"风险预警候选记录数：{len(risk_candidates)}",
    f"风险预警候选原因计数：{json_text(dict(risk_reason_counts))}", "",
    "输出文件：", str(json_path), str(project_csv_path), str(risk_csv_path),
    "", "注意：候选记录不代表应立即修改。无法可靠推断的拟修改值留空，所有候选项均需人工核对。",
]) + "\n"
summary_path.write_text(summary_text, encoding="utf-8")

print("=" * 72)
print("科研系统只读数据修复计划已生成")
print("=" * 72)
print(f"审计日期：{summary['audit_date']}")
print("数据库写入：否")
print(f"项目总数：{project_total}")
print(f"项目候选记录数：{len(project_candidates)}")
print(f"项目候选原因计数：{dict(project_reason_counts)}")
print(f"风险预警总数：{risk_total}")
print(f"风险预警候选记录数：{len(risk_candidates)}")
print(f"风险预警候选原因计数：{dict(risk_reason_counts)}")
print("-" * 72)
print(f"JSON完整计划：{json_path}")
print(f"项目候选CSV：{project_csv_path}")
print(f"风险预警候选CSV：{risk_csv_path}")
print(f"摘要说明：{summary_path}")
print("完成：只读取数据库；没有创建、更新或删除任何数据库记录。")
