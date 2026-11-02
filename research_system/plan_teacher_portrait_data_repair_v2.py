"""
教师画像缺失数据修复计划生成器（只读预览版）

运行方式（在 D:\research_system 项目根目录、已激活 venv 的 PowerShell 中）：
python manage.py shell -c "exec(open('plan_teacher_portrait_data_repair.py', encoding='utf-8').read())"

本脚本只读取 Django ORM 数据，并在本地生成 JSON/CSV 计划文件；不创建、更新、删除或保存任何数据库记录。
拟补齐的评分和合作关系均为模拟展示数据，正式写入前必须人工审核。
"""

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from django.utils import timezone
from api.models import User, Project, TeacherScore, Cooperation

TARGET_YEARS = list(range(2021, 2026))
OUTPUT_DIR = Path("data_repair_plan") / "teacher_portrait_repair_v2"


def clamp(value, low=65.0, high=96.0):
    return round(min(high, max(low, value)), 2)


def base_for_title(title):
    title = title or ""
    if "副教授" in title:
        return 84.0
    if "教授" in title:
        return 88.0
    if "讲师" in title:
        return 79.0
    return 82.0


def wave(teacher_id, year, salt=0):
    """
    可复现的教师个体差异，范围约为 [-3, 3]。
    使用教师 ID、年份和指标盐值共同计算，避免原公式中
    teacher_id * 7 再对 7 取模导致教师 ID 完全被抵消的问题。
    不使用随机数；相同输入始终得到相同结果。
    """
    code = (teacher_id * 37 + year * 17 + salt * 13) % 101
    return (code / 100.0) * 6.0 - 3.0


def propose_scores(teacher, year):
    base = base_for_title(teacher.title)
    dept_shift = (((teacher.dept_id or 0) % 5) - 2) * 0.35
    year_growth = (year - TARGET_YEARS[0]) * 0.55
    research = clamp(base + dept_shift + wave(teacher.id, year, 1) * 0.70 + year_growth)
    teaching = clamp(base - 1.2 + dept_shift * 0.5 + wave(teacher.id, year, 2) * 0.65 + year_growth * 0.45)
    service = clamp(base - 2.0 + wave(teacher.id, year, 3) * 0.60 + year_growth * 0.35)
    comprehensive = round(research * 0.5 + teaching * 0.3 + service * 0.2, 2)
    return {
        "research_score": research,
        "teaching_score": teaching,
        "service_score": service,
        "comprehensive_score": comprehensive,
    }


def pair_key(source, target):
    return tuple(sorted((str(source or "").strip(), str(target or "").strip())))


def teacher_info(teacher):
    return {
        "teacher_id": teacher.id,
        "teacher_name": teacher.real_name or "",
        "title": teacher.title or "",
        "department": teacher.dept.dept_name if teacher.dept else "",
        "department_id": teacher.dept_id,
    }


def choose_project(teacher_a, teacher_b, projects):
    if not projects:
        return None
    teacher_ids = {teacher_a.id, teacher_b.id}
    dept_ids = {x for x in (teacher_a.dept_id, teacher_b.dept_id) if x is not None}

    def key(project):
        leader_match = project.leader_id in teacher_ids
        dept_match = project.dept_id in dept_ids
        end_ord = project.end_date.toordinal() if getattr(project, "end_date", None) else 0
        return (0 if leader_match else 1, 0 if dept_match else 1, -end_ord, project.id)

    return sorted(projects, key=key)[0]


def write_csv(path, columns, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    audit_date = timezone.localdate()

    # 1. 只读加载当前数据。
    teachers = list(
        User.objects.filter(role="teacher").select_related("dept")
        .order_by("dept__dept_name", "real_name", "id")
    )
    score_rows = list(TeacherScore.objects.select_related("teacher").order_by("teacher_id", "year", "id"))
    cooperation_rows = list(Cooperation.objects.select_related("project").order_by("id"))
    projects = list(Project.objects.select_related("leader", "dept").order_by("id"))

    # 2. 规划 2021—2025 年缺失的教师年度评分；已有行绝不覆盖。
    scores_by_key = defaultdict(list)
    for row in score_rows:
        scores_by_key[(row.teacher_id, row.year)].append(row)

    score_candidates = []
    teachers_missing_years = set()
    duplicate_score_keys = []
    for (teacher_id, year), rows in sorted(scores_by_key.items()):
        if year in TARGET_YEARS and len(rows) > 1:
            duplicate_score_keys.append({
                "teacher_id": teacher_id,
                "year": year,
                "record_ids": [r.id for r in rows],
                "current_values": [
                    {
                        "id": r.id,
                        "research_score": str(r.research_score),
                        "teaching_score": str(r.teaching_score),
                        "service_score": str(r.service_score),
                        "comprehensive_score": str(r.comprehensive_score),
                    }
                    for r in rows
                ],
                "action": "仅记录供人工检查；不修改或删除已有评分",
            })

    for teacher in teachers:
        for year in TARGET_YEARS:
            if scores_by_key.get((teacher.id, year)):
                continue
            proposed = propose_scores(teacher, year)
            score_candidates.append({
                "candidate_id": f"TS-{teacher.id}-{year}",
                **teacher_info(teacher),
                "year": year,
                "current_value": "不存在：该教师该年度无 TeacherScore 记录",
                "proposed_value": proposed,
                "reason": (
                    f"教师在 {year} 年没有 TeacherScore 记录；仅拟新增缺失的教师—年度组合，"
                    "不修改其他年度的已有评分。拟生成值按职称基准、可复现的轻微教师差异和年度变化构造；"
                    "综合得分按科研50%、教学30%、服务20%加权计算。"
                ),
                "action": "仅供审核；本脚本不写入数据库",
            })
            teachers_missing_years.add(teacher.id)

    # 3. 统计教师姓名在合作记录中的覆盖情况。
    teachers_by_name = defaultdict(list)
    for teacher in teachers:
        name = (teacher.real_name or "").strip()
        if name:
            teachers_by_name[name].append(teacher)
    ambiguous_names = {name: rows for name, rows in teachers_by_name.items() if len(rows) > 1}

    covered_names = set()
    existing_pairs = set()
    cooperation_degree = Counter()
    for row in cooperation_rows:
        source = (row.source or "").strip()
        target = (row.target or "").strip()
        if source:
            covered_names.add(source)
            cooperation_degree[source] += 1
        if target:
            covered_names.add(target)
            cooperation_degree[target] += 1
        if source and target and source != target:
            existing_pairs.add(pair_key(source, target))

    teachers_without_cooperation = [
        t for t in teachers
        if not (t.real_name or "").strip() or (t.real_name or "").strip() not in covered_names
    ]
    pending = {
        t.id for t in teachers_without_cooperation
        if (t.real_name or "").strip() and len(teachers_by_name.get((t.real_name or "").strip(), [])) == 1
    }
    teacher_by_id = {t.id: t for t in teachers}
    planned_pairs = set()
    cooperation_candidates = []
    unresolved = []

    for teacher in teachers_without_cooperation:
        name = (teacher.real_name or "").strip()
        if not name:
            unresolved.append({**teacher_info(teacher), "reason": "教师 real_name 为空；无法安全生成基于文本姓名的合作关系"})
        elif len(teachers_by_name.get(name, [])) > 1:
            unresolved.append({**teacher_info(teacher), "reason": "教师姓名不唯一；无法仅凭 Cooperation.source/target 文本确认对应教师"})

    def partner_key(candidate, source_teacher):
        candidate_name = (candidate.real_name or "").strip()
        same_dept = source_teacher.dept_id is not None and candidate.dept_id == source_teacher.dept_id
        candidate_pending = candidate.id in pending
        if candidate_pending and same_dept:
            priority = 0
        elif candidate_pending:
            priority = 1
        elif same_dept:
            priority = 2
        else:
            priority = 3
        return (priority, cooperation_degree[candidate_name], candidate.id)

    # 一条候选合作边可覆盖一位或两位尚未出现在合作网络中的教师。
    while pending:
        source_id = min(
            pending,
            key=lambda tid: (
                teacher_by_id[tid].dept.dept_name if teacher_by_id[tid].dept else "",
                teacher_by_id[tid].real_name or "",
                tid,
            ),
        )
        source_teacher = teacher_by_id[source_id]
        source_name = (source_teacher.real_name or "").strip()
        partners = []
        for candidate in teachers:
            target_name = (candidate.real_name or "").strip()
            if candidate.id == source_id or not target_name or target_name == source_name:
                continue
            if len(teachers_by_name.get(target_name, [])) != 1:
                continue
            pair = pair_key(source_name, target_name)
            if pair in existing_pairs or pair in planned_pairs:
                continue
            partners.append(candidate)
        partners.sort(key=lambda c: partner_key(c, source_teacher))

        if not partners:
            unresolved.append({**teacher_info(source_teacher), "reason": "未找到可安全使用的非重复合作对象；未生成候选关系"})
            pending.remove(source_id)
            continue

        target_teacher = partners[0]
        target_name = (target_teacher.real_name or "").strip()
        pair = pair_key(source_name, target_name)
        project = choose_project(source_teacher, target_teacher, projects)
        if project is None:
            unresolved.append({
                **teacher_info(source_teacher),
                "potential_partner": target_name,
                "reason": "数据库中没有 Project 记录；Cooperation.project 是必填外键，无法生成有效候选关系",
            })
            pending.remove(source_id)
            continue

        cooperation_candidates.append({
            "candidate_id": f"COOP-{len(cooperation_candidates) + 1:04d}",
            "source_teacher_id": source_teacher.id,
            "source_teacher_name": source_name,
            "target_teacher_id": target_teacher.id,
            "target_teacher_name": target_name,
            "current_value": "不存在：当前没有该教师对的合作记录（按无向教师对去重）",
            "proposed_value": {
                "source": source_name,
                "target": target_name,
                "project_id": project.id,
                "project_no": getattr(project, "project_no", ""),
                "project_name": getattr(project, "project_name", ""),
                "coop_count": 1,
            },
            "reason": (
                "该教师姓名当前未出现在 Cooperation.source/target 中；拟增加一条模拟合作关系以补齐教师画像网络。"
                "合作对象优先选择同系或同样缺少合作覆盖的教师，并关联现有项目；不创建项目、不修改现有合作记录。"
                "正式写入前应人工确认该模拟关系是否合理。"
            ),
            "action": "仅供审核；本脚本不写入数据库",
        })
        planned_pairs.add(pair)
        existing_pairs.add(pair)
        cooperation_degree[source_name] += 1
        cooperation_degree[target_name] += 1
        pending.discard(source_id)
        pending.discard(target_teacher.id)

    # 4. 汇总当前状态和计划。
    teacher_ids_with_any_score = {r.teacher_id for r in score_rows}
    teacher_ids_with_target_scores = {
        teacher_id for (teacher_id, year), rows in scores_by_key.items()
        if year in TARGET_YEARS and rows
    }
    teachers_mentioned = sum(
        1 for t in teachers if (t.real_name or "").strip() in covered_names
    )

    report = {
        "report_title": "教师画像缺失数据修复计划（只读预览）",
        "audit_date": str(audit_date),
        "database_write": False,
        "database_write_note": "本脚本仅执行 ORM 查询；JSON/CSV/说明文件写入本地磁盘，不写数据库。",
        "target_score_years": TARGET_YEARS,
        "current_state": {
            "teachers_total": len(teachers),
            "teachers_with_any_score": len(teacher_ids_with_any_score),
            "teachers_without_any_score": max(0, len(teachers) - len(teacher_ids_with_any_score)),
            "existing_teacher_score_records": len(score_rows),
            "teachers_with_any_target_year_score": len(teacher_ids_with_target_scores),
            "teachers_missing_at_least_one_target_year": len(teachers_missing_years),
            "missing_teacher_year_score_candidates": len(score_candidates),
            "duplicate_teacher_year_score_keys_in_target_years": len(duplicate_score_keys),
            "cooperation_records_total": len(cooperation_rows),
            "teachers_mentioned_in_cooperation_by_exact_name": teachers_mentioned,
            "teachers_not_mentioned_in_cooperation_by_exact_name": len(teachers_without_cooperation),
            "cooperation_candidates": len(cooperation_candidates),
            "unresolved_cooperation_teachers": len(unresolved),
            "project_records_available_for_cooperation": len(projects),
        },
        "score_generation_policy": {
            "years": TARGET_YEARS,
            "existing_rows": "保留，不覆盖",
            "base_by_title": {"教授": 88.0, "副教授": 84.0, "讲师": 79.0, "其他或未填写职称": 82.0},
            "score_bounds": [65.0, 96.0],
            "comprehensive_formula": "research_score*0.5 + teaching_score*0.3 + service_score*0.2",
            "individual_variation_formula": "((teacher_id*37 + year*17 + salt*13) % 101) / 100 * 6 - 3",
            "deterministic": True,
        },
        "cooperation_generation_policy": {
            "existing_rows": "保留，不覆盖、不删除",
            "deduplication": "按 source/target 构成的无向教师对去重",
            "partner_preference": "优先同系且缺少覆盖的教师，其次其他未覆盖教师，再考虑已有覆盖教师",
            "project_selection": "优先任一教师负责的现有项目，其次同系现有项目",
            "coop_count": 1,
            "ambiguous_or_blank_names": "不自动生成，列入人工复核",
        },
        "score_candidates": score_candidates,
        "cooperation_candidates": cooperation_candidates,
        "duplicate_teacher_year_score_keys": duplicate_score_keys,
        "unresolved_cooperation_teachers": unresolved,
        "ambiguous_teacher_names": {name: [t.id for t in rows] for name, rows in ambiguous_names.items()},
        "safety_checks": {
            "database_modified": False,
            "existing_teacher_score_rows_overwritten": 0,
            "existing_cooperation_rows_overwritten": 0,
            "database_rows_deleted": 0,
            "only_missing_teacher_year_combinations_planned": True,
            "cooperation_pairs_deduplicated_as_undirected": True,
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUTPUT_DIR / "teacher_portrait_repair_plan.json"
    score_csv_path = OUTPUT_DIR / "teacher_score_candidates.csv"
    cooperation_csv_path = OUTPUT_DIR / "cooperation_candidates.csv"
    unresolved_csv_path = OUTPUT_DIR / "cooperation_unresolved_review.csv"
    readme_path = OUTPUT_DIR / "README_teacher_portrait_repair_plan.txt"

    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    score_csv = []
    for row in score_candidates:
        p = row["proposed_value"]
        score_csv.append({
            "candidate_id": row["candidate_id"], "teacher_id": row["teacher_id"],
            "teacher_name": row["teacher_name"], "title": row["title"],
            "department": row["department"], "year": row["year"],
            "current_value": row["current_value"],
            "proposed_research_score": p["research_score"],
            "proposed_teaching_score": p["teaching_score"],
            "proposed_service_score": p["service_score"],
            "proposed_comprehensive_score": p["comprehensive_score"],
            "reason": row["reason"], "action": row["action"],
        })
    write_csv(score_csv_path, [
        "candidate_id", "teacher_id", "teacher_name", "title", "department", "year",
        "current_value", "proposed_research_score", "proposed_teaching_score",
        "proposed_service_score", "proposed_comprehensive_score", "reason", "action",
    ], score_csv)

    cooperation_csv = []
    for row in cooperation_candidates:
        p = row["proposed_value"]
        cooperation_csv.append({
            "candidate_id": row["candidate_id"],
            "source_teacher_id": row["source_teacher_id"], "source_teacher_name": row["source_teacher_name"],
            "target_teacher_id": row["target_teacher_id"], "target_teacher_name": row["target_teacher_name"],
            "current_value": row["current_value"], "proposed_source": p["source"],
            "proposed_target": p["target"], "proposed_project_id": p["project_id"],
            "proposed_project_no": p["project_no"], "proposed_project_name": p["project_name"],
            "proposed_coop_count": p["coop_count"], "reason": row["reason"], "action": row["action"],
        })
    write_csv(cooperation_csv_path, [
        "candidate_id", "source_teacher_id", "source_teacher_name", "target_teacher_id",
        "target_teacher_name", "current_value", "proposed_source", "proposed_target",
        "proposed_project_id", "proposed_project_no", "proposed_project_name",
        "proposed_coop_count", "reason", "action",
    ], cooperation_csv)

    unresolved_csv = [{
        "teacher_id": row.get("teacher_id", ""), "teacher_name": row.get("teacher_name", ""),
        "title": row.get("title", ""), "department": row.get("department", ""),
        "potential_partner": row.get("potential_partner", ""), "reason": row.get("reason", ""),
    } for row in unresolved]
    write_csv(unresolved_csv_path, [
        "teacher_id", "teacher_name", "title", "department", "potential_partner", "reason",
    ], unresolved_csv)

    readme = f"""教师画像缺失数据修复计划（只读预览）
审计日期：{audit_date}
数据库写入：否。本脚本没有创建、更新或删除任何数据库记录。

目标评分年份：{', '.join(str(y) for y in TARGET_YEARS)}
教师总数：{len(teachers)}
现有 TeacherScore 记录：{len(score_rows)}
拟新增缺失教师年度评分：{len(score_candidates)}
现有 Cooperation 记录：{len(cooperation_rows)}
拟新增合作关系候选：{len(cooperation_candidates)}
合作关系待人工复核教师：{len(unresolved)}
目标年份内重复的教师年度评分键：{len(duplicate_score_keys)}

文件说明：
1. teacher_portrait_repair_plan.json：完整计划、当前统计、逐条候选、拟生成值、修改原因和安全检查。
2. teacher_score_candidates.csv：拟新增的教师—年度评分；已有评分不会被覆盖。
3. cooperation_candidates.csv：拟新增合作关系候选；关联现有项目，不创建项目。
4. cooperation_unresolved_review.csv：姓名为空/重复、无可用合作对象或缺少项目等需人工复核的记录。

评分规则：仅规划 2021—2025 年缺失记录；按职称基准和可复现的小幅变化生成；综合得分=科研50%+教学30%+服务20%；范围65—96分；已有记录不覆盖。
合作规则：只规划未出现在 source/target 的教师；按无向教师对去重；优先同系并关联现有项目；姓名为空或重复时不自动生成。

请先审核 JSON/CSV 中的教师姓名、分数分布、合作对象和关联项目。此脚本不会执行正式写入。
"""
    readme_path.write_text(readme, encoding="utf-8")

    print("=" * 72)
    print("教师画像缺失数据修复计划已生成（只读预览）")
    print("=" * 72)
    print(f"审计日期：{audit_date}")
    print("数据库写入：否")
    print(f"教师总数：{len(teachers)}")
    print(f"现有绩效评分记录：{len(score_rows)}")
    print(f"拟新增缺失教师年度评分：{len(score_candidates)}")
    print(f"现有合作记录：{len(cooperation_rows)}")
    print(f"拟新增合作关系候选：{len(cooperation_candidates)}")
    print(f"合作关系待人工复核教师：{len(unresolved)}")
    print(f"目标年份内重复教师年度评分键：{len(duplicate_score_keys)}")
    print("-" * 72)
    print(f"完整 JSON 计划：{json_path.resolve()}")
    print(f"绩效候选 CSV：{score_csv_path.resolve()}")
    print(f"合作候选 CSV：{cooperation_csv_path.resolve()}")
    print(f"合作待复核 CSV：{unresolved_csv_path.resolve()}")
    print(f"说明文件：{readme_path.resolve()}")
    print("完成：只读取数据库；没有新增、更新或删除任何数据库记录。")


main()
