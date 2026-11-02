"""教师画像模拟数据写入前独立只读预检 V2。

只读取 Django 数据库；通过 SQLite backup API 创建文件备份。
不会对业务表执行 INSERT、UPDATE 或 DELETE。
输出文件名与现有写入器约定一致：teacher_portrait_demo_prewrite_audit.json
"""
from __future__ import annotations

from collections import Counter
from decimal import Decimal
from pathlib import Path

from django.db.models import Count

from api.models import User, Project, TeacherScore, Cooperation
from teacher_portrait_demo_safe_common_v1 import (
    DATA_SOURCE,
    backup_sqlite,
    database_counts,
    input_paths,
    pair_key,
    read_csv,
    read_json,
    require_demo_marker_fields,
    sha256_file,
    state_fingerprint,
    write_json,
)


EXPECTED_BASELINE = {
    "teachers_total": 104,
    "projects_total": 377,
    "teacher_score_records_total": 85,
    "cooperation_records_total": 28,
    "teacher_score_demo_records": 0,
    "cooperation_demo_records": 0,
}
EXPECTED_SCORE_CANDIDATES = 435
EXPECTED_COOPERATION_CANDIDATES = 44


def main():
    paths = input_paths()
    report_path = paths["preflight"]
    errors = []
    plan = {}
    preflight_inputs_ready = all(
        paths[key].is_file()
        for key in ("plan", "scores", "cooperations", "unresolved")
    )
    input_hashes = {}

    for key in ("plan", "scores", "cooperations", "unresolved"):
        if not paths[key].is_file():
            errors.append(f"缺少输入文件：{paths[key]}")

    score_rows = []
    cooperation_rows = []
    unresolved_rows = []

    if preflight_inputs_ready:
        try:
            plan = read_json(paths["plan"])
            score_rows = read_csv(paths["scores"])
            cooperation_rows = read_csv(paths["cooperations"])
            unresolved_rows = read_csv(paths["unresolved"])
            input_hashes = {
                "plan_json": sha256_file(paths["plan"]),
                "score_csv": sha256_file(paths["scores"]),
                "cooperation_csv": sha256_file(paths["cooperations"]),
                "unresolved_csv": sha256_file(paths["unresolved"]),
            }
        except Exception as exc:
            errors.append(f"读取计划或候选文件失败：{type(exc).__name__}: {exc}")

    try:
        require_demo_marker_fields()
    except Exception as exc:
        errors.append(f"模型演示标记字段校验失败：{exc}")

    if preflight_inputs_ready:
        if plan.get("database_write") is not False:
            errors.append("计划 JSON 不是只读预览计划（database_write 必须为 false）。")
        if not plan.get("target_score_years"):
            errors.append("计划 JSON 缺少 target_score_years。")

    if len(score_rows) != EXPECTED_SCORE_CANDIDATES:
        errors.append(
            f"评分候选数量不符合冻结计划：期望 {EXPECTED_SCORE_CANDIDATES}，实际 {len(score_rows)}。"
        )
    if len(cooperation_rows) != EXPECTED_COOPERATION_CANDIDATES:
        errors.append(
            f"合作候选数量不符合冻结计划：期望 {EXPECTED_COOPERATION_CANDIDATES}，实际 {len(cooperation_rows)}。"
        )
    if unresolved_rows:
        errors.append(f"合作待人工复核 CSV 非空：{len(unresolved_rows)} 条。")

    counts_before = database_counts()
    initial_fingerprint = state_fingerprint(include_demo_rows=True)
    protected_fingerprint = state_fingerprint(include_demo_rows=False)
    if counts_before != EXPECTED_BASELINE:
        errors.append(
            f"数据库基线与本次冻结预期不一致：期望 {EXPECTED_BASELINE}，实际 {counts_before}。"
        )

    # 确认现有记录仍按原始数据来源保存，且没有此前写入的演示批次。
    existing_score_count = TeacherScore.objects.filter(
        is_demo=False, data_source="existing"
    ).count()
    existing_cooperation_count = Cooperation.objects.filter(
        is_demo=False, data_source="existing"
    ).count()
    if existing_score_count != EXPECTED_BASELINE["teacher_score_records_total"]:
        errors.append(
            f"原有评分记录数异常：期望 85，实际 {existing_score_count}。"
        )
    if existing_cooperation_count != EXPECTED_BASELINE["cooperation_records_total"]:
        errors.append(
            f"原有合作记录数异常：期望 28，实际 {existing_cooperation_count}。"
        )

    target_years = set()
    if plan:
        try:
            target_years = {int(year) for year in plan.get("target_score_years", [])}
        except (TypeError, ValueError):
            errors.append("target_score_years 包含无效年份。")
            target_years = set()

    duplicate_existing_keys = []
    if target_years:
        duplicate_existing_keys = list(
            TeacherScore.objects.filter(year__in=target_years)
            .values("teacher_id", "year")
            .annotate(record_count=Count("id"))
            .filter(record_count__gt=1)
        )
        if duplicate_existing_keys:
            errors.append(
                f"目标年份内已有重复教师年度评分键：{duplicate_existing_keys[:10]}。"
            )

    teachers = {
        teacher.id: teacher
        for teacher in User.objects.filter(role="teacher").select_related("dept").order_by("id")
    }
    projects = {project.id: project for project in Project.objects.order_by("id")}

    score_keys = []
    seen_score_candidate_ids = set()
    for row in score_rows:
        candidate_id = row.get("candidate_id", "UNKNOWN")
        try:
            teacher_id = int(row["teacher_id"])
            year = int(row["year"])
            teacher = teachers.get(teacher_id)
            if teacher is None:
                errors.append(f"评分候选 {candidate_id} 指向不存在或非教师用户 ID {teacher_id}。")
                continue
            if (teacher.real_name or "") != row["teacher_name"]:
                errors.append(f"评分候选 {candidate_id} 的教师姓名与 ID 不匹配。")
            if target_years and year not in target_years:
                errors.append(f"评分候选 {candidate_id} 的年份 {year} 不在冻结目标年份内。")
            if TeacherScore.objects.filter(teacher_id=teacher_id, year=year).exists():
                errors.append(
                    f"评分候选 {candidate_id} 的教师—年度键 ({teacher_id}, {year}) 已存在；拒绝覆盖。"
                )

            values = [
                Decimal(row[field])
                for field in (
                    "proposed_research_score",
                    "proposed_teaching_score",
                    "proposed_service_score",
                    "proposed_comprehensive_score",
                )
            ]
            if not all(Decimal("65") <= value <= Decimal("96") for value in values):
                errors.append(f"评分候选 {candidate_id} 存在 65–96 区间外的分数。")
            computed = values[0] * Decimal("0.5") + values[1] * Decimal("0.3") + values[2] * Decimal("0.2")
            if abs(computed - values[3]) > Decimal("0.01"):
                errors.append(f"评分候选 {candidate_id} 的综合分不符合 0.5/0.3/0.2 加权公式。")

            score_keys.append((teacher_id, year))
            if candidate_id in seen_score_candidate_ids:
                errors.append(f"评分候选 ID 重复：{candidate_id}。")
            seen_score_candidate_ids.add(candidate_id)
        except (KeyError, ValueError, TypeError, ArithmeticError) as exc:
            errors.append(f"评分候选 {candidate_id} 字段无效：{exc}")

    duplicate_score_keys = [
        key for key, count in Counter(score_keys).items() if count > 1
    ]
    if duplicate_score_keys:
        errors.append(f"评分候选存在重复教师—年度键：{duplicate_score_keys[:10]}。")

    existing_pairs = {
        pair_key(source, target)
        for source, target in Cooperation.objects.values_list("source", "target")
        if str(source or "").strip() and str(target or "").strip()
    }
    cooperation_pairs = []
    seen_cooperation_candidate_ids = set()

    for row in cooperation_rows:
        candidate_id = row.get("candidate_id", "UNKNOWN")
        try:
            source_id = int(row["source_teacher_id"])
            target_id = int(row["target_teacher_id"])
            project_id = int(row["proposed_project_id"])
            source_teacher = teachers.get(source_id)
            target_teacher = teachers.get(target_id)
            project = projects.get(project_id)

            if source_id == target_id or source_teacher is None or target_teacher is None:
                errors.append(f"合作候选 {candidate_id} 的教师 ID 无效或双方为同一教师。")
                continue
            if source_teacher.real_name != row["proposed_source"]:
                errors.append(f"合作候选 {candidate_id} 的来源教师姓名与 ID 不匹配。")
            if target_teacher.real_name != row["proposed_target"]:
                errors.append(f"合作候选 {candidate_id} 的目标教师姓名与 ID 不匹配。")
            if project is None:
                errors.append(f"合作候选 {candidate_id} 指向不存在的项目 ID {project_id}。")
                continue
            if (
                project.project_name != row["proposed_project_name"]
                or project.project_no != row["proposed_project_no"]
            ):
                errors.append(f"合作候选 {candidate_id} 的项目名称/编号与项目 ID 不匹配。")

            coop_count = int(row["proposed_coop_count"])
            if coop_count < 1:
                errors.append(f"合作候选 {candidate_id} 的合作次数必须大于等于 1。")

            pair = pair_key(row["proposed_source"], row["proposed_target"])
            if pair[0] == pair[1]:
                errors.append(f"合作候选 {candidate_id} 的双方教师姓名归一化后相同。")
            if pair in existing_pairs:
                errors.append(f"合作候选 {candidate_id} 与现有合作关系重复（按无向教师对检查）。")
            cooperation_pairs.append(pair)

            if candidate_id in seen_cooperation_candidate_ids:
                errors.append(f"合作候选 ID 重复：{candidate_id}。")
            seen_cooperation_candidate_ids.add(candidate_id)
        except (KeyError, ValueError, TypeError, ArithmeticError) as exc:
            errors.append(f"合作候选 {candidate_id} 字段无效：{exc}")

    duplicate_cooperation_pairs = [
        pair for pair, count in Counter(cooperation_pairs).items() if count > 1
    ]
    if duplicate_cooperation_pairs:
        errors.append(f"合作候选存在重复无向教师对：{duplicate_cooperation_pairs[:10]}。")

    # 校验候选文件期间数据库若有变化，即使总行数不变也必须停止。
    if database_counts() != counts_before:
        errors.append("独立预检过程中数据库记录数发生变化；请停止并重新预检。")
    if state_fingerprint(include_demo_rows=True) != initial_fingerprint:
        errors.append("独立预检过程中数据库状态指纹发生变化；请停止并重新预检。")

    current_fingerprint = initial_fingerprint
    backup = None

    # 只有所有输入、候选和数据库状态校验均通过时才创建本轮预检备份。
    if not errors:
        try:
            backup = backup_sqlite("teacher_portrait_demo_prewrite")
            if backup.get("integrity_check") != "ok" or not backup.get("table_row_counts_match"):
                errors.append("预检备份完整性或表行数一致性检查未通过。")
            # 备份前后再次比较状态，防止预检期间另一个进程修改数据库。
            if database_counts() != counts_before:
                errors.append("创建预检备份期间数据库记录数发生变化；请停止并重新预检。")
            if state_fingerprint(include_demo_rows=True) != current_fingerprint:
                errors.append("创建预检备份期间数据库状态指纹发生变化；请停止并重新预检。")
        except Exception as exc:
            errors.append(f"创建/校验预检备份失败：{type(exc).__name__}: {exc}")

    report = {
        "report_title": "教师画像模拟数据写入前独立只读预检 V2",
        "status": "PASS" if not errors else "FAIL",
        "database_write": False,
        "data_source": DATA_SOURCE,
        "input_sha256": input_hashes,
        "backup": backup,
        "state_fingerprint": current_fingerprint,
        "protected_state_fingerprint": protected_fingerprint,
        "checks": {
            "baseline_counts": counts_before,
            "expected_baseline_counts": EXPECTED_BASELINE,
            "target_score_years": sorted(target_years),
            "score_candidates": len(score_rows),
            "cooperation_candidates": len(cooperation_rows),
            "unresolved_cooperation_rows": len(unresolved_rows),
            "duplicate_existing_teacher_year_keys": duplicate_existing_keys,
            "duplicate_candidate_score_keys": duplicate_score_keys,
            "duplicate_candidate_cooperation_pairs": duplicate_cooperation_pairs,
            "protected_state_fingerprint": protected_fingerprint,
        },
        "errors": errors,
        "note": "本脚本不写入业务数据库；仅在全部预检通过后生成独立 SQLite 备份文件。",
    }
    write_json(report_path, report)

    print("=" * 76)
    print("教师画像模拟数据写入前独立预检：", report["status"])
    print("数据库写入：否")
    print("当前数据库统计：", counts_before)
    print("评分候选：", len(score_rows))
    print("合作候选：", len(cooperation_rows))
    print("待人工复核合作候选：", len(unresolved_rows))
    if backup:
        print("预检备份：", backup.get("backup_path"))
        print("备份 SHA256：", backup.get("backup_sha256"))
    for error in errors:
        print(" -", error)
    print("预检报告：", report_path)
    print("=" * 76)

    if errors:
        raise RuntimeError("独立预检未通过；未写入任何业务数据库记录。")


main()
