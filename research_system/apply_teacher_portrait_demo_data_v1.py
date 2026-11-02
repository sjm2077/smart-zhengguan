"""教师画像模拟数据正式写入器。默认拒绝写入；必须设置精确环境变量后才会执行。"""
from decimal import Decimal
import os

from django.db import transaction

from api.models import User, Project, TeacherScore, Cooperation
from teacher_portrait_demo_safe_common_v1 import (
    DATA_SOURCE, WRITE_CONFIRM_ENV, WRITE_CONFIRM_VALUE, UI_CONFIRM_ENV, UI_CONFIRM_VALUE, backup_sqlite,
    database_counts, input_paths, pair_key, read_csv, read_json,
    require_demo_marker_fields, sha256_file, state_fingerprint, write_json,
)


def abort(message):
    raise RuntimeError("安全写入已中止：" + message)


def main():
    if os.environ.get(WRITE_CONFIRM_ENV) != WRITE_CONFIRM_VALUE:
        print("未写入任何数据库记录。")
        print("如已完成模型迁移、审阅独立预检报告并确认要写入，请在 PowerShell 中临时设置：")
        print(f'  $env:{UI_CONFIRM_ENV} = "{UI_CONFIRM_VALUE}"  # 已确认接口/页面会明确标注演示数据')
        print(f'  $env:{WRITE_CONFIRM_ENV} = "{WRITE_CONFIRM_VALUE}"')
        print("写入完成后立即移除这两个环境变量。")
        return
    if os.environ.get(UI_CONFIRM_ENV) != UI_CONFIRM_VALUE:
        abort(f"尚未确认界面已标记模拟数据。完成 API/前端标识后，设置 {UI_CONFIRM_ENV}={UI_CONFIRM_VALUE} 再执行。")

    require_demo_marker_fields()
    paths = input_paths()
    for key in ("plan", "scores", "cooperations", "unresolved", "preflight"):
        if not paths[key].is_file():
            abort(f"缺少输入文件：{paths[key]}")

    plan = read_json(paths["plan"])
    preflight = read_json(paths["preflight"])
    score_rows = read_csv(paths["scores"])
    cooperation_rows = read_csv(paths["cooperations"])
    unresolved_rows = read_csv(paths["unresolved"])

    if preflight.get("status") != "PASS":
        abort("独立预检报告不是 PASS；请重新运行 audit_teacher_portrait_demo_prewrite_v1.py。")
    if preflight.get("database_write") is not False:
        abort("独立预检报告格式异常。")
    if plan.get("database_write") is not False:
        abort("输入计划不是只读预览生成的计划。")
    if unresolved_rows:
        abort("合作待复核 CSV 非空。")
    if len(score_rows) != 435 or len(cooperation_rows) != 44:
        abort(f"候选数量不符合本次冻结计划：评分={len(score_rows)}，合作={len(cooperation_rows)}。")

    expected_hashes = preflight.get("input_sha256", {})
    current_hashes = {
        "plan_json": sha256_file(paths["plan"]),
        "score_csv": sha256_file(paths["scores"]),
        "cooperation_csv": sha256_file(paths["cooperations"]),
        "unresolved_csv": sha256_file(paths["unresolved"]),
    }
    if current_hashes != expected_hashes:
        abort("预检后计划 JSON/CSV 文件发生变化；请重新执行独立预检。")

    previous_backup = preflight.get("backup") or {}
    previous_backup_path = previous_backup.get("backup_path")
    if not previous_backup_path or not __import__("pathlib").Path(previous_backup_path).is_file():
        abort("独立预检备份文件不存在。")
    if sha256_file(__import__("pathlib").Path(previous_backup_path)) != previous_backup.get("backup_sha256"):
        abort("独立预检备份 SHA256 不匹配。")

    counts_before = database_counts()
    if counts_before != preflight.get("checks", {}).get("baseline_counts"):
        abort(f"数据库记录数与预检时不同：预检={preflight.get('checks', {}).get('baseline_counts')}，当前={counts_before}。")
    current_fingerprint = state_fingerprint(include_demo_rows=True)
    if current_fingerprint != preflight.get("state_fingerprint"):
        abort("教师、项目、评分或合作记录在预检后发生变化；请重新生成计划并重新预检。")
    if counts_before.get("teacher_score_demo_records") != 0 or counts_before.get("cooperation_demo_records") != 0:
        abort("目标模型已有模拟记录；为防止重复批次，已停止。")

    teachers = {
        t.id: t for t in User.objects.filter(role="teacher").select_related("dept").order_by("id")
    }
    projects = {p.id: p for p in Project.objects.order_by("id")}

    # 写入前再做一轮独立于预览生成器的关键校验。
    score_keys = []
    for row in score_rows:
        try:
            teacher_id = int(row["teacher_id"])
            year = int(row["year"])
            teacher = teachers.get(teacher_id)
            if teacher is None or (teacher.real_name or "") != row["teacher_name"]:
                abort(f"评分候选 {row.get('candidate_id')} 的教师身份不匹配。")
            if TeacherScore.objects.filter(teacher_id=teacher_id, year=year).exists():
                abort(f"评分候选 {row.get('candidate_id')} 对应的教师—年度键已存在，拒绝覆盖。")
            values = [Decimal(row[k]) for k in (
                "proposed_research_score", "proposed_teaching_score",
                "proposed_service_score", "proposed_comprehensive_score"
            )]
            if not all(Decimal("65") <= value <= Decimal("96") for value in values):
                abort(f"评分候选 {row.get('candidate_id')} 存在越界分数。")
            computed = values[0] * Decimal("0.5") + values[1] * Decimal("0.3") + values[2] * Decimal("0.2")
            if abs(computed - values[3]) > Decimal("0.01"):
                abort(f"评分候选 {row.get('candidate_id')} 的综合分不符合公式。")
            score_keys.append((teacher_id, year))
        except (KeyError, ValueError, TypeError, ArithmeticError) as exc:
            abort(f"评分候选字段无效：{row.get('candidate_id', 'UNKNOWN')}：{exc}")
    if len(score_keys) != len(set(score_keys)):
        abort("评分候选存在重复教师—年度键。")

    existing_pairs = {
        pair_key(source, target)
        for source, target in Cooperation.objects.values_list("source", "target")
        if str(source or "").strip() and str(target or "").strip()
    }
    coop_pairs = []
    for row in cooperation_rows:
        try:
            source_id = int(row["source_teacher_id"])
            target_id = int(row["target_teacher_id"])
            project_id = int(row["proposed_project_id"])
            source_teacher = teachers.get(source_id)
            target_teacher = teachers.get(target_id)
            project = projects.get(project_id)
            if source_id == target_id or source_teacher is None or target_teacher is None:
                abort(f"合作候选 {row.get('candidate_id')} 的教师身份无效。")
            if source_teacher.real_name != row["proposed_source"] or target_teacher.real_name != row["proposed_target"]:
                abort(f"合作候选 {row.get('candidate_id')} 的姓名与教师 ID 不匹配。")
            if project is None or project.project_name != row["proposed_project_name"] or project.project_no != row["proposed_project_no"]:
                abort(f"合作候选 {row.get('candidate_id')} 的项目关联不匹配。")
            pair = pair_key(row["proposed_source"], row["proposed_target"])
            if pair in existing_pairs:
                abort(f"合作候选 {row.get('candidate_id')} 与现有无向教师对重复。")
            coop_pairs.append(pair)
        except (KeyError, ValueError, TypeError, ArithmeticError) as exc:
            abort(f"合作候选字段无效：{row.get('candidate_id', 'UNKNOWN')}：{exc}")
    if len(coop_pairs) != len(set(coop_pairs)):
        abort("合作候选存在重复无向教师对。")

    # 在任何 INSERT 前创建第二份、紧贴正式写入时点的数据库备份。
    immediate_backup = backup_sqlite("teacher_portrait_demo_immediate_prewrite")
    protected_fingerprint_before = state_fingerprint(include_demo_rows=False)

    try:
        with transaction.atomic():
            # 进入事务后再次确认状态未变化。
            if state_fingerprint(include_demo_rows=True) != preflight.get("state_fingerprint"):
                abort("事务开始时数据库状态已变化；事务回滚。")

            score_objects = []
            for row in score_rows:
                score_objects.append(TeacherScore(
                    teacher_id=int(row["teacher_id"]),
                    year=int(row["year"]),
                    research_score=Decimal(row["proposed_research_score"]),
                    teaching_score=Decimal(row["proposed_teaching_score"]),
                    service_score=Decimal(row["proposed_service_score"]),
                    comprehensive_score=Decimal(row["proposed_comprehensive_score"]),
                    is_demo=True,
                    data_source=DATA_SOURCE,
                ))
            TeacherScore.objects.bulk_create(score_objects, batch_size=200)

            cooperation_objects = []
            for row in cooperation_rows:
                cooperation_objects.append(Cooperation(
                    source=row["proposed_source"],
                    target=row["proposed_target"],
                    project_id=int(row["proposed_project_id"]),
                    coop_count=int(row["proposed_coop_count"]),
                    is_demo=True,
                    data_source=DATA_SOURCE,
                ))
            Cooperation.objects.bulk_create(cooperation_objects, batch_size=100)

            # 事务提交前验证新增数量、标识和历史记录不变。
            demo_score_count = TeacherScore.objects.filter(is_demo=True, data_source=DATA_SOURCE).count()
            demo_coop_count = Cooperation.objects.filter(is_demo=True, data_source=DATA_SOURCE).count()
            if demo_score_count != 435 or demo_coop_count != 44:
                abort(f"事务内新增记录数异常：demo scores={demo_score_count}, demo cooperations={demo_coop_count}。")

            for row in score_rows:
                item = TeacherScore.objects.get(teacher_id=int(row["teacher_id"]), year=int(row["year"]))
                if not item.is_demo or item.data_source != DATA_SOURCE:
                    abort(f"评分记录 {row.get('candidate_id')} 的演示标记校验失败。")
                if item.comprehensive_score != Decimal(row["proposed_comprehensive_score"]):
                    abort(f"评分记录 {row.get('candidate_id')} 的写入值与候选值不一致。")

            for row in cooperation_rows:
                matched = Cooperation.objects.filter(
                    source=row["proposed_source"],
                    target=row["proposed_target"],
                    project_id=int(row["proposed_project_id"]),
                    is_demo=True,
                    data_source=DATA_SOURCE,
                ).count()
                if matched != 1:
                    abort(f"合作记录 {row.get('candidate_id')} 的写入校验失败，匹配数量={matched}。")

            if state_fingerprint(include_demo_rows=False) != protected_fingerprint_before:
                abort("检测到教师/项目/原有非演示评分或合作记录发生变化；事务回滚。")

            expected_total_scores = counts_before["teacher_score_records_total"] + 435
            expected_total_coops = counts_before["cooperation_records_total"] + 44
            if TeacherScore.objects.count() != expected_total_scores:
                abort("事务内 TeacherScore 总记录数不符合预期；事务回滚。")
            if Cooperation.objects.count() != expected_total_coops:
                abort("事务内 Cooperation 总记录数不符合预期；事务回滚。")
    except Exception as exc:
        print("写入失败；Django 事务已回滚（若异常发生在事务内）。")
        print("立即写入前备份仍保留：", immediate_backup["backup_path"])
        raise

    after = database_counts()
    result = {
        "report_title": "教师画像模拟数据写入结果",
        "status": "PASS",
        "data_source": DATA_SOURCE,
        "created_teacher_score_demo_rows": 435,
        "created_cooperation_demo_rows": 44,
        "before": counts_before,
        "after": after,
        "prewrite_audit": str(paths["preflight"]),
        "preflight_backup": previous_backup,
        "immediate_prewrite_backup": immediate_backup,
        "protected_state_fingerprint_before": protected_fingerprint_before,
        "protected_state_fingerprint_after": state_fingerprint(include_demo_rows=False),
        "database_modified": True,
        "existing_rows_updated": 0,
        "existing_rows_deleted": 0,
        "projects_created": 0,
    }
    result_path = paths["preflight"].with_name("teacher_portrait_demo_write_result.json")
    write_json(result_path, result)

    print("=" * 76)
    print("教师画像模拟数据写入完成")
    print("本批次标识：", DATA_SOURCE)
    print("新增模拟年度评分：435")
    print("新增模拟合作关系：44")
    print("写入前状态：", counts_before)
    print("写入后状态：", after)
    print("更新/删除原有记录：0 / 0")
    print("创建 Project：0")
    print("立即写入前备份：", immediate_backup["backup_path"])
    print("写入结果报告：", result_path)
    print("请立即移除临时写入环境变量。")
    print("=" * 76)


main()
