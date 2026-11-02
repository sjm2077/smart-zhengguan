"""教师画像模拟数据独立预检。只读 ORM；通过后生成本地备份和预检报告，不写数据库。"""
from collections import Counter
from decimal import Decimal

from django.db.models import Count

from api.models import User, Project, TeacherScore, Cooperation
from teacher_portrait_demo_safe_common_v1 import (
    backup_sqlite, database_counts, input_paths, pair_key, read_csv, read_json,
    require_demo_marker_fields, sha256_file, state_fingerprint, write_json,
)


def main():
    paths = input_paths()
    errors = []
    required_files = [paths["plan"], paths["scores"], paths["cooperations"], paths["unresolved"]]
    missing = [str(p) for p in required_files if not p.is_file()]
    if missing:
        raise RuntimeError("缺少 v2 计划文件，请先运行 plan_teacher_portrait_data_repair_v2.py：\n" + "\n".join(missing))

    require_demo_marker_fields()
    plan = read_json(paths["plan"])
    score_rows = read_csv(paths["scores"])
    cooperation_rows = read_csv(paths["cooperations"])
    unresolved_rows = read_csv(paths["unresolved"])
    expected = plan.get("current_state", {})
    target_years = {int(y) for y in plan.get("target_score_years", [])}

    def check(condition, message):
        if not condition:
            errors.append(message)

    check(plan.get("database_write") is False, "计划 JSON 的 database_write 必须为 false。")
    check(len(score_rows) == int(expected.get("missing_teacher_year_score_candidates", -1)), "评分 CSV 行数与 JSON 计划不一致。")
    check(len(cooperation_rows) == int(expected.get("cooperation_candidates", -1)), "合作 CSV 行数与 JSON 计划不一致。")
    check(len(unresolved_rows) == 0, "合作待复核 CSV 非空；本版安全写入要求先处理所有待复核项。")
    check(len(score_rows) == 435, f"评分候选应为 435 条，实际 {len(score_rows)} 条。")
    check(len(cooperation_rows) == 44, f"合作候选应为 44 条，实际 {len(cooperation_rows)} 条。")

    score_json = {x.get("candidate_id"): x for x in plan.get("score_candidates", [])}
    coop_json = {x.get("candidate_id"): x for x in plan.get("cooperation_candidates", [])}
    score_ids = [r.get("candidate_id", "") for r in score_rows]
    coop_ids = [r.get("candidate_id", "") for r in cooperation_rows]
    check(len(score_ids) == len(set(score_ids)), "评分 CSV 存在重复 candidate_id。")
    check(len(coop_ids) == len(set(coop_ids)), "合作 CSV 存在重复 candidate_id。")
    check(set(score_ids) == set(score_json), "评分 CSV 与 JSON 计划中的 candidate_id 集合不一致。")
    check(set(coop_ids) == set(coop_json), "合作 CSV 与 JSON 计划中的 candidate_id 集合不一致。")

    counts_before = database_counts()
    expected_counts = {
        "teachers_total": expected.get("teachers_total"),
        "projects_total": expected.get("project_records_available_for_cooperation"),
        "teacher_score_records_total": expected.get("existing_teacher_score_records"),
        "cooperation_records_total": expected.get("cooperation_records_total"),
    }
    for key, wanted in expected_counts.items():
        if wanted is not None:
            check(counts_before.get(key) == int(wanted), f"数据库状态已变化：{key} 当前={counts_before.get(key)}，计划={wanted}。请重新生成 v2 计划。")
    check(counts_before.get("teacher_score_demo_records") == 0, "TeacherScore 中已有 is_demo=True 记录；为避免混批，已停止。")
    check(counts_before.get("cooperation_demo_records") == 0, "Cooperation 中已有 is_demo=True 记录；为避免混批，已停止。")

    teachers = {
        t.id: t for t in User.objects.filter(role="teacher").select_related("dept").order_by("id")
    }
    projects = {p.id: p for p in Project.objects.order_by("id")}
    years = sorted(target_years)

    current_target_keys = set(
        TeacherScore.objects.filter(year__in=years).values_list("teacher_id", "year")
    )
    candidate_keys = []
    for row in score_rows:
        try:
            teacher_id = int(row["teacher_id"])
            year = int(row["year"])
            candidate_keys.append((teacher_id, year))
            teacher = teachers.get(teacher_id)
            check(teacher is not None, f"评分候选 {row.get('candidate_id')} 的教师 ID 不存在或不是教师。")
            if teacher is not None:
                check((teacher.real_name or "") == row.get("teacher_name", ""), f"评分候选 {row.get('candidate_id')} 的教师姓名与当前数据库不一致。")
                check((teacher.title or "") == row.get("title", ""), f"评分候选 {row.get('candidate_id')} 的职称与当前数据库不一致。")
                current_dept = teacher.dept.dept_name if teacher.dept else ""
                check(current_dept == row.get("department", ""), f"评分候选 {row.get('candidate_id')} 的院系与当前数据库不一致。")
            check(year in target_years, f"评分候选 {row.get('candidate_id')} 的年份不在目标年份范围内。")
            values = [Decimal(row[k]) for k in (
                "proposed_research_score", "proposed_teaching_score",
                "proposed_service_score", "proposed_comprehensive_score"
            )]
            check(all(Decimal("65") <= v <= Decimal("96") for v in values), f"评分候选 {row.get('candidate_id')} 有分数超出 65—96。")
            computed = values[0] * Decimal("0.5") + values[1] * Decimal("0.3") + values[2] * Decimal("0.2")
            check(abs(computed - values[3]) <= Decimal("0.01"), f"评分候选 {row.get('candidate_id')} 的综合分不符合加权公式。")
            planned = score_json.get(row.get("candidate_id"), {})
            planned_value = planned.get("proposed_value", {})
            for csv_key, json_key in [
                ("proposed_research_score", "research_score"),
                ("proposed_teaching_score", "teaching_score"),
                ("proposed_service_score", "service_score"),
                ("proposed_comprehensive_score", "comprehensive_score"),
            ]:
                check(Decimal(row[csv_key]) == Decimal(str(planned_value.get(json_key))), f"评分候选 {row.get('candidate_id')} 的 CSV 数值与 JSON 计划不一致。")
        except (KeyError, ValueError, TypeError, ArithmeticError) as exc:
            errors.append(f"评分候选字段或数值无效：{row.get('candidate_id', 'UNKNOWN')}：{exc}")

    check(len(candidate_keys) == len(set(candidate_keys)), "评分候选存在重复教师—年度键。")
    overlaps = sorted(set(candidate_keys) & current_target_keys)
    check(not overlaps, f"部分评分候选在数据库中已经存在，拒绝覆盖或重复写入：{overlaps[:10]}")

    existing_pairs = {
        pair_key(source, target)
        for source, target in Cooperation.objects.values_list("source", "target")
        if str(source or "").strip() and str(target or "").strip()
    }
    candidate_pairs = []
    for row in cooperation_rows:
        try:
            source_id = int(row["source_teacher_id"])
            target_id = int(row["target_teacher_id"])
            project_id = int(row["proposed_project_id"])
            source_teacher = teachers.get(source_id)
            target_teacher = teachers.get(target_id)
            project = projects.get(project_id)
            check(source_id != target_id, f"合作候选 {row.get('candidate_id')} 不能让教师与自己合作。")
            check(source_teacher is not None and target_teacher is not None, f"合作候选 {row.get('candidate_id')} 的教师 ID 无效。")
            if source_teacher is not None:
                check((source_teacher.real_name or "") == row.get("source_teacher_name", ""), f"合作候选 {row.get('candidate_id')} 的 source 教师姓名不一致。")
                check((source_teacher.real_name or "") == row.get("proposed_source", ""), f"合作候选 {row.get('candidate_id')} 的 proposed_source 不一致。")
            if target_teacher is not None:
                check((target_teacher.real_name or "") == row.get("target_teacher_name", ""), f"合作候选 {row.get('candidate_id')} 的 target 教师姓名不一致。")
                check((target_teacher.real_name or "") == row.get("proposed_target", ""), f"合作候选 {row.get('candidate_id')} 的 proposed_target 不一致。")
            check(project is not None, f"合作候选 {row.get('candidate_id')} 关联的 Project 不存在。")
            if project is not None:
                check((project.project_no or "") == row.get("proposed_project_no", ""), f"合作候选 {row.get('candidate_id')} 的项目编号不一致。")
                check((project.project_name or "") == row.get("proposed_project_name", ""), f"合作候选 {row.get('candidate_id')} 的项目名称不一致。")
            check(int(row.get("proposed_coop_count", "0")) > 0, f"合作候选 {row.get('candidate_id')} 的合作次数必须为正整数。")
            pair = pair_key(row.get("proposed_source"), row.get("proposed_target"))
            candidate_pairs.append(pair)
            check(pair[0] != pair[1], f"合作候选 {row.get('candidate_id')} 不是有效的双人关系。")
            check(pair not in existing_pairs, f"合作候选 {row.get('candidate_id')} 与现有合作关系重复。")
            planned = coop_json.get(row.get("candidate_id"), {})
            planned_value = planned.get("proposed_value", {})
            check(str(planned.get("source_teacher_id")) == str(source_id), f"合作候选 {row.get('candidate_id')} 的 JSON source_teacher_id 不一致。")
            check(str(planned.get("target_teacher_id")) == str(target_id), f"合作候选 {row.get('candidate_id')} 的 JSON target_teacher_id 不一致。")
            check(str(planned_value.get("project_id")) == str(project_id), f"合作候选 {row.get('candidate_id')} 的 JSON project_id 不一致。")
        except (KeyError, ValueError, TypeError, ArithmeticError) as exc:
            errors.append(f"合作候选字段或数值无效：{row.get('candidate_id', 'UNKNOWN')}：{exc}")

    check(len(candidate_pairs) == len(set(candidate_pairs)), "合作候选存在重复的无向教师对。")
    duplicate_current_target = list(
        TeacherScore.objects.filter(year__in=years)
        .values("teacher_id", "year")
        .annotate(n=Count("id"))
        .filter(n__gt=1)
    )
    check(not duplicate_current_target, f"当前目标年份存在重复教师年度评分键：{duplicate_current_target[:10]}")

    report = {
        "report_title": "教师画像模拟数据写入前独立预检",
        "created_at": __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "PASS" if not errors else "FAIL",
        "database_write": False,
        "checks": {
            "candidate_score_count": len(score_rows),
            "candidate_cooperation_count": len(cooperation_rows),
            "unresolved_cooperation_count": len(unresolved_rows),
            "baseline_counts": counts_before,
            "expected_baseline_counts": expected_counts,
            "score_candidate_duplicate_keys": len(candidate_keys) - len(set(candidate_keys)),
            "cooperation_candidate_duplicate_pairs": len(candidate_pairs) - len(set(candidate_pairs)),
            "existing_score_key_overlaps": len(overlaps),
            "existing_cooperation_pair_overlaps": sum(1 for pair in candidate_pairs if pair in existing_pairs),
            "current_target_year_duplicate_keys": len(duplicate_current_target),
        },
        "input_sha256": {
            "plan_json": sha256_file(paths["plan"]),
            "score_csv": sha256_file(paths["scores"]),
            "cooperation_csv": sha256_file(paths["cooperations"]),
            "unresolved_csv": sha256_file(paths["unresolved"]),
        },
        "errors": errors,
    }

    if not errors:
        backup = backup_sqlite("teacher_portrait_demo_prewrite")
        report["backup"] = backup
        report["state_fingerprint"] = state_fingerprint(include_demo_rows=True)
        report["protected_state_fingerprint"] = state_fingerprint(include_demo_rows=False)
        report["status"] = "PASS"
    else:
        report["backup"] = None
        report["state_fingerprint"] = None
        report["protected_state_fingerprint"] = None

    write_json(paths["preflight"], report)
    print("=" * 76)
    print("教师画像模拟数据写入前独立预检")
    print("状态：", report["status"])
    print("数据库写入：否")
    print("评分候选：", len(score_rows))
    print("合作候选：", len(cooperation_rows))
    print("当前数据库统计：", counts_before)
    if report.get("backup"):
        print("预写入备份：", report["backup"]["backup_path"])
        print("备份 SHA256：", report["backup"]["backup_sha256"])
    if errors:
        print("未通过项目：")
        for error in errors:
            print(" -", error)
    print("预检报告：", paths["preflight"])
    print("=" * 76)


main()
