"""教师画像模拟数据写入后的独立只读复核。"""
from django.db.models import Count

from api.models import User, Project, TeacherScore, Cooperation
from teacher_portrait_demo_safe_common_v1 import (
    DATA_SOURCE, input_paths, pair_key, read_csv, read_json, state_fingerprint, write_json,
)
from decimal import Decimal


def main():
    paths = input_paths()
    preflight_path = paths["preflight"]
    result_path = preflight_path.with_name("teacher_portrait_demo_write_result.json")
    if not preflight_path.is_file() or not result_path.is_file():
        raise RuntimeError("缺少预检报告或写入结果报告；无法进行独立复核。")
    preflight = read_json(preflight_path)
    write_result = read_json(result_path)
    errors = []

    def check(condition, message):
        if not condition:
            errors.append(message)

    before = preflight.get("checks", {}).get("baseline_counts", {})
    check(write_result.get("status") == "PASS", "写入结果报告不是 PASS。")
    check(write_result.get("data_source") == DATA_SOURCE, "写入批次标识不一致。")
    check(TeacherScore.objects.count() == int(before.get("teacher_score_records_total", -1)) + 435, "TeacherScore 总记录数不符合预期。")
    check(Cooperation.objects.count() == int(before.get("cooperation_records_total", -1)) + 44, "Cooperation 总记录数不符合预期。")
    check(TeacherScore.objects.filter(is_demo=True, data_source=DATA_SOURCE).count() == 435, "本批次演示评分不是 435 条。")
    check(Cooperation.objects.filter(is_demo=True, data_source=DATA_SOURCE).count() == 44, "本批次演示合作关系不是 44 条。")
    check(TeacherScore.objects.filter(is_demo=False).count() == int(before.get("teacher_score_records_total", -1)), "原有非演示评分记录数发生变化。")
    check(Cooperation.objects.filter(is_demo=False).count() == int(before.get("cooperation_records_total", -1)), "原有非演示合作记录数发生变化。")
    check(Project.objects.count() == int(before.get("projects_total", -1)), "Project 数量发生变化。")
    check(User.objects.filter(role="teacher").count() == int(before.get("teachers_total", -1)), "教师总数发生变化。")

    score_candidates = read_csv(paths["scores"])
    cooperation_candidates = read_csv(paths["cooperations"])
    for row in score_candidates:
        try:
            item = TeacherScore.objects.get(teacher_id=int(row["teacher_id"]), year=int(row["year"]))
            check(item.is_demo is True, f"{row.get('candidate_id')} 未标记为演示评分。")
            check(item.data_source == DATA_SOURCE, f"{row.get('candidate_id')} 的 data_source 不正确。")
            for field, csv_field in [
                ("research_score", "proposed_research_score"),
                ("teaching_score", "proposed_teaching_score"),
                ("service_score", "proposed_service_score"),
                ("comprehensive_score", "proposed_comprehensive_score"),
            ]:
                check(Decimal(str(getattr(item, field))) == Decimal(row[csv_field]), f"{row.get('candidate_id')} 的 {field} 与候选 CSV 不一致。")
        except (TeacherScore.DoesNotExist, KeyError, ValueError, TypeError) as exc:
            errors.append(f"评分候选 {row.get('candidate_id')} 写入后未通过核验：{exc}")

    for row in cooperation_candidates:
        try:
            matched = Cooperation.objects.filter(
                source=row["proposed_source"],
                target=row["proposed_target"],
                project_id=int(row["proposed_project_id"]),
                coop_count=int(row["proposed_coop_count"]),
                is_demo=True,
                data_source=DATA_SOURCE,
            ).count()
            check(matched == 1, f"合作候选 {row.get('candidate_id')} 写入后匹配数应为 1，实际为 {matched}。")
        except (KeyError, ValueError, TypeError) as exc:
            errors.append(f"合作候选 {row.get('candidate_id')} 写入后未通过核验：{exc}")

    target_years = set(read_json(paths["plan"]).get("target_score_years", []))
    duplicates = list(
        TeacherScore.objects.filter(year__in=target_years)
        .values("teacher_id", "year").annotate(n=Count("id")).filter(n__gt=1)
    )
    check(not duplicates, f"目标年份出现重复教师年度评分键：{duplicates[:10]}")
    check(
        state_fingerprint(include_demo_rows=False) == preflight.get("protected_state_fingerprint"),
        "原有教师、项目、非演示评分或非演示合作记录指纹与写入前不同。",
    )

    demo_coops = list(Cooperation.objects.filter(is_demo=True, data_source=DATA_SOURCE).values_list("source", "target"))
    normalized_pairs = [pair_key(source, target) for source, target in demo_coops]
    check(len(normalized_pairs) == len(set(normalized_pairs)), "本批次模拟合作关系存在重复无向教师对。")

    report = {
        "report_title": "教师画像模拟数据写入后独立复核",
        "status": "PASS" if not errors else "FAIL",
        "database_write": False,
        "data_source": DATA_SOURCE,
        "current_counts": {
            "teachers_total": User.objects.filter(role="teacher").count(),
            "projects_total": Project.objects.count(),
            "teacher_score_records_total": TeacherScore.objects.count(),
            "teacher_score_demo_records": TeacherScore.objects.filter(is_demo=True, data_source=DATA_SOURCE).count(),
            "cooperation_records_total": Cooperation.objects.count(),
            "cooperation_demo_records": Cooperation.objects.filter(is_demo=True, data_source=DATA_SOURCE).count(),
        },
        "errors": errors,
    }
    write_json(preflight_path.with_name("teacher_portrait_demo_postwrite_audit.json"), report)
    print("=" * 76)
    print("教师画像模拟数据写入后独立复核：", report["status"])
    print("当前统计：", report["current_counts"])
    for error in errors:
        print(" -", error)
    print("复核报告：", preflight_path.with_name("teacher_portrait_demo_postwrite_audit.json"))
    print("数据库写入：否（本复核脚本只读）")
    print("=" * 76)
    if errors:
        raise RuntimeError("写入后独立复核未通过，请停止演示并按备份方案恢复。")


main()
