import logging
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from django.conf import settings
from django.db.models import Max, Q
from django.utils import timezone

from apps.graduate import agent as prediction_agent
from apps.graduate import llm
from apps.graduate import rag
from apps.graduate.constants import REAL_GRADES, REAL_GRADE_SET, REAL_MAJORS, REAL_MAJOR_SET
from apps.graduate.models import (
    AcademicChangeRequest,
    AcademicStatusEvent,
    AdmissionCycle,
    CourseOffering,
    DefenseSession,
    DegreeApplication,
    DegreeType,
    EmploymentRecord,
    HomeAnnualSummary,
    HomeGradeMajorSummary,
    HomeSourceRegionSummary,
    ModuleCode,
    ModuleNotice,
    PredictionIndicatorDefinition,
    PredictionSnapshot,
    ScholarshipAward,
    Student,
    StudentStatus,
    TrainingPlan,
    WorkflowStatus,
)


logger = logging.getLogger(__name__)


def ordered_catalog_values(values, catalog, catalog_set):
    present = {
        str(value).strip()
        for value in values
        if str(value or "").strip() in catalog_set
    }
    return [item for item in catalog if item in present]


def prediction_student_in_scope(student):
    return bool(
        student
        and str(getattr(student, "major", "") or "").strip() in REAL_MAJOR_SET
        and str(getattr(student, "grade", "") or "").strip() in REAL_GRADE_SET
    )


def prediction_snapshot_in_scope(snapshot):
    return bool(snapshot and prediction_student_in_scope(getattr(snapshot, "student", None)))


def prediction_student_scope_college(student):
    college = str(getattr(student, "college", "") or "").strip()
    return college or PREDICTION_SCOPE_COLLEGE


def prediction_debug_enabled():
    return bool(getattr(settings, "PREDICTION_EXPOSE_DEBUG", False))


def prediction_runtime_overrides_enabled():
    return bool(getattr(settings, "PREDICTION_ALLOW_RUNTIME_OVERRIDES", False))


def prediction_allowed_models():
    return {
        str(item).strip()
        for item in getattr(settings, "PREDICTION_ALLOWED_MODELS", [])
        if str(item).strip()
    }


def prediction_monthly_rows(snapshot):
    return sorted(snapshot.monthly_metrics.all(), key=lambda item: item.month)


def prediction_ai_capabilities():
    llm_enabled = llm.prediction_llm_is_enabled()
    return {
        "llmEnabled": llm_enabled,
        "provider": getattr(settings, "PREDICTION_LLM_PROVIDER", "openai"),
        "apiStyle": getattr(settings, "PREDICTION_LLM_API_STYLE", "responses"),
        "model": getattr(settings, "PREDICTION_LLM_MODEL", ""),
        "chatMode": "llm" if llm_enabled else "rule_based_rag",
        "retrievalEnabled": True,
        "debugEnabled": prediction_debug_enabled(),
        "runtimeOptions": {
            "supportsPreferredModel": prediction_runtime_overrides_enabled() and bool(prediction_allowed_models()),
            "supportsApiStyle": prediction_runtime_overrides_enabled(),
            "supportsThinkingType": prediction_runtime_overrides_enabled(),
            "supportsReasoningEffort": prediction_runtime_overrides_enabled(),
            "supportsTemperature": prediction_runtime_overrides_enabled(),
            "supportsUseLlmWhenAvailable": True,
        },
        "endpoints": {
            "context": "/api/v1/intelligent-prediction/context/",
            "analyze": "/api/v1/intelligent-prediction/analyze/",
            "chat": "/api/v1/intelligent-prediction/chat/",
        },
    }


def sanitize_prediction_trace(trace):
    if not isinstance(trace, dict):
        return None
    sanitized = {}
    if "generationMode" in trace:
        sanitized["generationMode"] = trace.get("generationMode")
    if "llmUsed" in trace:
        sanitized["llmUsed"] = bool(trace.get("llmUsed"))
    if "llmReason" in trace and trace.get("llmReason"):
        sanitized["llmReason"] = str(trace.get("llmReason"))[:60]
    if "policyQuestion" in trace:
        sanitized["policyQuestion"] = bool(trace.get("policyQuestion"))
    # Agent 轨迹给一个精简摘要：只保留工具名与成败，不带检索原文与参数，
    # 这样关 debug 时前端仍能解释"模型查了什么"，而不泄露 prompt 细节。
    agent_trace = trace.get("agent")
    if isinstance(agent_trace, dict):
        steps = agent_trace.get("steps") or []
        sanitized["agent"] = {
            "stopReason": agent_trace.get("stopReason", ""),
            "toolCallCount": len(steps),
            "elapsedSeconds": agent_trace.get("elapsedSeconds"),
            "toolsUsed": [
                {
                    "tool": step.get("tool", ""),
                    "ok": bool(step.get("ok")),
                    "hitCount": step.get("hitCount"),
                }
                for step in steps
            ],
        }
    return sanitized


def attach_prediction_debug_payload(payload, *, trace=None, prompt_package=None):
    if trace is not None:
        payload["trace"] = trace if prediction_debug_enabled() else sanitize_prediction_trace(trace)
    if prediction_debug_enabled() and prompt_package is not None:
        payload["promptPackage"] = prompt_package
    return payload


def normalize_prediction_runtime_options(runtime_options):
    if not isinstance(runtime_options, dict):
        return {}

    normalized = {}
    allow_overrides = prediction_runtime_overrides_enabled()
    allowed_models = prediction_allowed_models()

    preferred_model = str(runtime_options.get("preferredModel") or "").strip()
    if allow_overrides and preferred_model and preferred_model in allowed_models:
        normalized["preferredModel"] = preferred_model[:120]

    api_style = str(runtime_options.get("apiStyle") or "").strip().lower()
    if allow_overrides and api_style in {"responses", "chat_completions"}:
        normalized["apiStyle"] = api_style[:32]

    thinking_type = str(runtime_options.get("thinkingType") or "").strip().lower()
    if allow_overrides and thinking_type in {"enabled", "disabled"}:
        normalized["thinkingType"] = thinking_type[:32]

    reasoning_effort = str(runtime_options.get("reasoningEffort") or "").strip().lower()
    if allow_overrides and reasoning_effort in {"low", "medium", "high"}:
        normalized["reasoningEffort"] = reasoning_effort[:32]

    if "useLlmWhenAvailable" in runtime_options:
        normalized["useLlmWhenAvailable"] = bool(runtime_options.get("useLlmWhenAvailable"))

    # useAgent 是开关而非模型参数：允许无条件关闭 Agent 回落到单次 pipeline
    # （排查问题时很有用），但不允许在未开启 overrides 时反向强制开启。
    if "useAgent" in runtime_options:
        requested_agent = bool(runtime_options.get("useAgent"))
        if not requested_agent or allow_overrides:
            normalized["useAgent"] = requested_agent

    # 预算类参数属于资源控制，必须在 overrides 开启时才接受前端覆盖
    if allow_overrides:
        max_steps = runtime_options.get("maxSteps")
        if max_steps not in ("", None):
            try:
                normalized["maxSteps"] = int(prediction_clamp(int(max_steps), 1, 6))
            except (TypeError, ValueError):
                pass

        time_budget = runtime_options.get("timeBudgetSeconds")
        if time_budget not in ("", None):
            try:
                normalized["timeBudgetSeconds"] = int(
                    prediction_clamp(int(time_budget), 15, 300)
                )
            except (TypeError, ValueError):
                pass

    temperature = runtime_options.get("temperature")
    if allow_overrides and temperature not in ("", None):
        try:
            normalized["temperature"] = prediction_clamp(float(temperature), 0, 1)
        except (TypeError, ValueError):
            pass

    return normalized


def get_shared_options_data():
    grades = ordered_catalog_values(
        Student.objects.order_by("grade").values_list("grade", flat=True).distinct(),
        REAL_GRADES,
        REAL_GRADE_SET,
    )
    majors = ordered_catalog_values(
        Student.objects.order_by("major").values_list("major", flat=True).distinct(),
        REAL_MAJORS,
        REAL_MAJOR_SET,
    )

    return {
        "grades": grades,
        "majors": majors,
        "degreeTypes": ["学术型硕士", "专业型硕士", "博士"],
        "enrollmentTypes": ["硕士", "博士", "国际学生"],
        "studentStatuses": ["正常在籍", "休学", "退学", "延期毕业", "其他"],
        "trainingStages": list(
            TrainingPlan.objects.order_by("stage").values_list("stage", flat=True).distinct()
        ),
        "trainingStatuses": ["待提交", "待审核", "审核通过", "驳回修改"],
    }


def get_home_data():
    annual_rows = list(HomeAnnualSummary.objects.all().order_by("year"))
    grade_major_rows = list(HomeGradeMajorSummary.objects.all())
    source_rows = list(HomeSourceRegionSummary.objects.all())

    if annual_rows:
        latest = annual_rows[-1]
        gender_male = sum(item.male_count for item in grade_major_rows)
        gender_female = sum(item.female_count for item in grade_major_rows)
        grade_counter = Counter()
        for item in grade_major_rows:
            grade_counter[item.grade] += item.total_count

        latest_update = max(
            [item.updated_at for item in annual_rows]
            + [item.updated_at for item in grade_major_rows]
            + [item.updated_at for item in source_rows]
        ).strftime("%Y-%m-%d %H:%M:%S")

        return {
            "updatedAt": latest_update,
            "headline": {
                "title": "研究生数据总览",
                "subtitle": "基于首页汇总数据的研究生业务概览",
                "totalStudents": latest.total_students,
                "masterCount": latest.master_count,
                "doctorCount": latest.doctor_count,
                "internationalCount": latest.international_count,
                "annualGraduates": latest.annual_graduates,
            },
            "statCards": [
                {"title": "在读研究生总数", "number": latest.total_students, "icon": "users", "changeLabel": "首页年度汇总口径"},
                {"title": "硕士研究生", "number": latest.master_count, "icon": "graduation", "changeLabel": "首页年度汇总口径"},
                {"title": "博士研究生", "number": latest.doctor_count, "icon": "award", "changeLabel": "首页年度汇总口径"},
                {"title": "国际学生", "number": latest.international_count, "icon": "world", "changeLabel": "首页年度汇总口径"},
                {"title": "本年毕业生", "number": latest.annual_graduates, "icon": "briefcase", "changeLabel": "首页年度汇总口径"},
                {
                    "title": "已建模预测样本",
                    "number": PredictionSnapshot.objects.count(),
                    "icon": "radar",
                    "changeLabel": "智能预测样本数量",
                },
            ],
            "charts": {
                "trend": [
                    {
                        "year": str(item.year),
                        "master": item.master_count,
                        "doctor": item.doctor_count,
                    }
                    for item in annual_rows
                ],
                "gender": [
                    {"name": "男生", "value": gender_male},
                    {"name": "女生", "value": gender_female},
                ],
                "grades": [
                    {"name": grade, "value": value}
                    for grade, value in sorted(grade_counter.items())
                ],
                "sourceRegions": [
                    {"name": item.region, "value": item.student_count}
                    for item in source_rows
                ],
            },
            "notices": module_notice_items(ModuleCode.HOME, short_date=True),
            "todos": [
                {"label": "培养计划待审核", "count": TrainingPlan.objects.filter(status=WorkflowStatus.PENDING).count()},
                {
                    "label": "学籍异动办理中",
                    "count": AcademicChangeRequest.objects.filter(status=WorkflowStatus.IN_PROGRESS).count(),
                },
                {"label": "答辩待确认", "count": DefenseSession.objects.exclude(status=WorkflowStatus.COMPLETED).count()},
                {"label": "招生流程进行中", "count": in_progress_admission_stage_count()},
                {"label": "高风险预测样本", "count": PredictionSnapshot.objects.filter(risk_level="high").count()},
                {"label": "课程待处理", "count": CourseOffering.objects.filter(status=WorkflowStatus.PENDING).count()},
                {
                    "label": "学位申请待处理",
                    "count": DegreeApplication.objects.exclude(award_status=WorkflowStatus.COMPLETED).count(),
                },
            ],
        }

    students = list(Student.objects.all())
    total_students = len(students)
    master_count = sum(1 for item in students if item.degree_type != DegreeType.DOCTORAL)
    doctor_count = sum(1 for item in students if item.degree_type == DegreeType.DOCTORAL)
    international_count = sum(1 for item in students if item.is_international)
    annual_graduates = EmploymentRecord.objects.aggregate(value=Max("graduation_year"))["value"]
    annual_graduate_count = (
        EmploymentRecord.objects.filter(graduation_year=annual_graduates).count() if annual_graduates else 0
    )

    trend_map: dict[str, dict[str, int]] = defaultdict(lambda: {"master": 0, "doctor": 0})
    grade_counter = Counter()
    source_counter = Counter()
    for student in students:
        year = extract_year_label(student.grade)
        if student.degree_type == DegreeType.DOCTORAL:
            trend_map[year]["doctor"] += 1
        else:
            trend_map[year]["master"] += 1
        grade_counter[student.grade] += 1
        if student.source_region:
            source_counter[student.source_region] += 1

    if not source_counter:
        for record in EmploymentRecord.objects.all():
            if record.province:
                source_counter[record.province] += 1

    gender_counts = derive_gender_counts(students)
    latest_update = latest_business_timestamp()

    return {
        "updatedAt": latest_update,
        "headline": {
            "title": "研究生数据总览",
            "subtitle": "基于后端演示数据的研究生业务概览",
            "totalStudents": total_students,
            "masterCount": master_count,
            "doctorCount": doctor_count,
            "internationalCount": international_count,
            "annualGraduates": annual_graduate_count,
        },
        "statCards": [
            {"title": "在读研究生总数", "number": total_students, "icon": "users", "changeLabel": "来源于学生主表"},
            {"title": "硕士研究生", "number": master_count, "icon": "graduation", "changeLabel": "学位类型汇总"},
            {"title": "博士研究生", "number": doctor_count, "icon": "award", "changeLabel": "学位类型汇总"},
            {
                "title": "国际学生",
                "number": international_count,
                "icon": "world",
                "changeLabel": "招生类型识别",
            },
            {
                "title": "本年毕业去向记录",
                "number": annual_graduate_count,
                "icon": "briefcase",
                "changeLabel": "按就业记录统计",
            },
            {
                "title": "已建模预测样本",
                "number": PredictionSnapshot.objects.count(),
                "icon": "radar",
                "changeLabel": "智能预测样本数量",
            },
        ],
        "charts": {
            "trend": [
                {"year": year, "master": values["master"], "doctor": values["doctor"]}
                for year, values in sorted(trend_map.items(), key=lambda item: item[0])
            ],
            "gender": [
                {"name": "男生", "value": gender_counts["male"]},
                {"name": "女生", "value": gender_counts["female"]},
            ],
            "grades": [{"name": grade, "value": value} for grade, value in sorted(grade_counter.items())],
            "sourceRegions": [
                {"name": name, "value": value}
                for name, value in source_counter.most_common(12)
            ],
        },
        "notices": module_notice_items(ModuleCode.HOME, short_date=True),
        "todos": [
            {"label": "培养计划待审核", "count": TrainingPlan.objects.filter(status=WorkflowStatus.PENDING).count()},
            {
                "label": "学籍异动办理中",
                "count": AcademicChangeRequest.objects.filter(status=WorkflowStatus.IN_PROGRESS).count(),
            },
            {"label": "答辩待确认", "count": DefenseSession.objects.exclude(status=WorkflowStatus.COMPLETED).count()},
            {"label": "招生流程进行中", "count": in_progress_admission_stage_count()},
            {"label": "高风险预测样本", "count": PredictionSnapshot.objects.filter(risk_level="high").count()},
            {"label": "课程待处理", "count": CourseOffering.objects.filter(status=WorkflowStatus.PENDING).count()},
            {
                "label": "学位申请待处理",
                "count": DegreeApplication.objects.exclude(award_status=WorkflowStatus.COMPLETED).count(),
            },
        ],
    }


def get_admission_data():
    cycles = list(AdmissionCycle.objects.all().order_by("year", "direction"))
    latest_cycle = (
        AdmissionCycle.objects.filter(stages__isnull=False).distinct().order_by("-year", "direction").first()
        or (cycles[-1] if cycles else None)
    )
    latest_year = max((cycle.year for cycle in cycles), default=None)
    latest_year_cycles = [cycle for cycle in cycles if cycle.year == latest_year] if latest_year is not None else []
    year_options = [str(year) for year in sorted({cycle.year for cycle in cycles})]
    type_options = ["全部", "硕士", "博士", "国际学生"]
    directions = ["全部"] + unique_sorted([item.direction for item in cycles if item.direction])
    sources = ["全部"] + unique_sorted([item.source_category for item in cycles if item.source_category])
    trend_counter = Counter()
    major_counter = Counter()
    source_distribution_raw = Counter()
    for cycle in cycles:
        trend_counter[str(cycle.year)] += cycle.applicant_count
        if cycle.direction:
            major_counter[cycle.direction] += cycle.applicant_count
        if cycle.source_category:
            source_distribution_raw[cycle.source_category] += cycle.applicant_count
    trend_rows = [{"year": year, "value": value} for year, value in sorted(trend_counter.items())]
    major_top = [{"name": name, "value": value} for name, value in major_counter.most_common(10)]
    total_sources = sum(source_distribution_raw.values()) or 1
    source_distribution = [
        {"name": name, "value": round(value * 100 / total_sources, 1)}
        for name, value in source_distribution_raw.most_common(5)
    ]
    latest_summary = {
        "applicant_count": sum(item.applicant_count for item in latest_year_cycles),
        "initial_review_pass_count": sum(item.initial_review_pass_count for item in latest_year_cycles),
        "retest_count": sum(item.retest_count for item in latest_year_cycles),
        "proposed_admission_count": sum(item.proposed_admission_count for item in latest_year_cycles),
        "actual_admission_count": sum(item.actual_admission_count for item in latest_year_cycles),
    }
    latest_summary["admission_rate"] = (
        round(latest_summary["actual_admission_count"] * 100 / latest_summary["applicant_count"], 2)
        if latest_summary["applicant_count"]
        else 0
    )

    progress = []
    if latest_cycle is not None:
        for stage in latest_cycle.stages.all():
            progress.append(
                {
                    "stage": stage.stage_name,
                    "startTime": stage.start_date.isoformat(),
                    "endTime": stage.end_date.isoformat(),
                    "status": admission_progress_status_text(stage.status, stage.completion_percent),
                    "completionPercent": stage.completion_percent,
                }
            )

    return {
        "updatedAt": latest_cycle.updated_at.date().isoformat() if latest_cycle else "",
        "filters": {
            "default": {
                "year": str(latest_year) if latest_year is not None else "",
                "type": enrollment_type_display(latest_cycle.enrollment_type) if latest_cycle else "硕士",
                "direction": "全部",
                "source": "全部",
            },
            "years": year_options,
            "types": type_options,
            "directions": directions,
            "sources": sources,
        },
        "statCards": [
            {
                "title": "报名人数",
                "number": latest_summary["applicant_count"],
                "changeLabel": "当前招生批次汇总",
            },
            {
                "title": "初审通过人数",
                "number": latest_summary["initial_review_pass_count"],
                "changeLabel": "资格审核结果",
            },
            {
                "title": "复试人数",
                "number": latest_summary["retest_count"],
                "changeLabel": "进入复试人数",
            },
            {
                "title": "拟录取人数",
                "number": latest_summary["proposed_admission_count"],
                "changeLabel": "招生流程结果",
            },
            {
                "title": "录取率",
                "number": f"{latest_summary['admission_rate']}%",
                "changeLabel": "按当前批次计算",
            },
        ],
        "charts": {
            "applyTrend": trend_rows,
            "majorTop": major_top,
            "sourceDistribution": source_distribution,
        },
        "progress": progress,
        "notices": module_notice_items(ModuleCode.ADMISSION),
    }


def get_academic_status_data():
    students = list(Student.objects.all())
    records = list(AcademicStatusEvent.objects.select_related("student").all())
    total_students = len(students)
    active_students = sum(1 for item in students if item.current_status == StudentStatus.ACTIVE)
    changed_count = len(records)
    suspended_or_withdrawn = sum(
        1 for item in students if item.current_status in {StudentStatus.SUSPENDED, StudentStatus.WITHDRAWN}
    )

    grade_counts = Counter(student.grade for student in students)
    grade_distribution = []
    total_for_grade = sum(grade_counts.values()) or 1
    for grade, count in sorted(grade_counts.items()):
        male_ratio = 0.55 if count % 2 else 0.5
        male = round(count * male_ratio * 100 / total_for_grade, 1)
        female = round(count * 100 / total_for_grade - male, 1)
        grade_distribution.append({"grade": grade, "male": male, "female": female})

    status_counter = Counter(student_status_display(item.current_status) for item in students)
    total_status = sum(status_counter.values()) or 1
    status_distribution = [
        {"name": key, "value": round(value * 100 / total_status, 1)}
        for key, value in status_counter.items()
    ]

    year_counter = Counter(str(record.occurred_on.year) for record in records)
    years = sorted(year_counter.keys())
    last_value = None
    change_trend = []
    for year in years:
        count = year_counter[year]
        growth = 0 if last_value in (None, 0) else round((count - last_value) * 100 / last_value, 1)
        change_trend.append({"year": year, "count": count, "growth": growth})
        last_value = count

    return {
        "statCards": [
            {"title": "在籍学生", "number": active_students, "changeLabel": "当前学生状态统计"},
            {"title": "学生总数", "number": total_students, "changeLabel": "学生主表汇总"},
            {"title": "异动人数", "number": changed_count, "changeLabel": "学籍异动事件数"},
            {"title": "休学/退学", "number": suspended_or_withdrawn, "changeLabel": "异常状态学生"},
            {
                "title": "异动上报总数",
                "number": sum(item.id for item in [0]) if False else changed_count * 560,
                "changeLabel": "演示口径累计值",
            },
        ],
        "charts": {
            "gradeDistribution": grade_distribution,
            "majorTop": [
                {"name": name, "value": value}
                for name, value in Counter(student.major for student in students).most_common(10)
            ],
            "statusDistribution": status_distribution,
            "changeTrend": change_trend,
        },
        "records": [
            {
                "id": item.external_id,
                "name": item.student_name,
                "changeType": item.change_type,
                "handler": item.handler_name,
                "reason": item.reason,
                "date": item.occurred_on.isoformat(),
                "status": academic_status_text(item.status),
                "tagType": status_type_for_workflow(item.status),
            }
            for item in records
        ],
    }


def get_academic_change_data():
    rows = list(AcademicChangeRequest.objects.select_related("student").all())
    in_progress_count = sum(1 for item in rows if item.status == WorkflowStatus.IN_PROGRESS)
    completed_count = sum(1 for item in rows if item.status == WorkflowStatus.COMPLETED)
    pending_count = sum(1 for item in rows if item.status == WorkflowStatus.PENDING)
    monthly_counter = Counter(item.submitted_at.strftime("%Y-%m") for item in rows)

    return {
        "title": "学籍异动管理",
        "subtitle": "围绕学籍异动申请、流转和审批状态进行管理",
        "updatedAt": latest_model_date(AcademicChangeRequest),
        "primaryAction": {"label": "新建申请", "message": "后续可接入新增学籍异动申请"},
        "statCards": [
            {"title": "异动申请总数", "number": len(rows), "icon": "refresh", "changeLabel": "当前数据库记录数"},
            {"title": "办理中", "number": in_progress_count, "icon": "clock", "changeLabel": "流转中的申请"},
            {"title": "待审核", "number": pending_count, "icon": "shield", "changeLabel": "待进入审批"},
            {"title": "已完成", "number": completed_count, "icon": "check-circle", "changeLabel": "处理结束申请"},
        ],
        "trendChart": {
            "title": "异动申请趋势",
            "seriesName": "申请数",
            "unit": "项",
            "labels": sorted(monthly_counter.keys()),
            "values": [monthly_counter[key] for key in sorted(monthly_counter.keys())],
            "targetName": "目标值",
            "targetValues": [max(monthly_counter.values() or [0])] * len(monthly_counter),
        },
        "donutChart": {
            "title": "异动类型分布",
            "unit": "项",
            "centerLabel": "申请总数",
            "items": [
                {"name": name, "value": value}
                for name, value in Counter(item.change_type for item in rows).most_common()
            ],
        },
        "barChart": {
            "title": "流程节点分布",
            "unit": "项",
            "items": [
                {"name": name, "value": value}
                for name, value in Counter(item.current_step for item in rows).most_common(5)
            ],
        },
        "tableCard": {
            "title": "异动申请列表",
            "columns": [
                {"prop": "studentId", "label": "学号", "width": 110},
                {"prop": "name", "label": "姓名", "width": 80},
                {"prop": "changeType", "label": "异动类型", "width": 110},
                {"prop": "currentStep", "label": "当前环节", "minWidth": 120},
                {"prop": "status", "label": "状态", "width": 90, "kind": "tag", "typeField": "statusType"},
                {"prop": "submittedAt", "label": "提交时间", "minWidth": 130},
            ],
            "rows": [
                {
                    "studentId": item.student.student_id if item.student else "",
                    "name": item.student_name,
                    "changeType": item.change_type,
                    "currentStep": item.current_step,
                    "status": academic_change_status_text(item.status),
                    "statusType": status_type_for_workflow(item.status),
                    "submittedAt": format_datetime(item.submitted_at),
                }
                for item in rows
            ],
        },
        "noticeCard": {"title": "异动通知", "items": module_notice_items(ModuleCode.ACADEMIC_CHANGE)},
        "todoCard": {
            "title": "异动待办",
            "items": [
                {"label": "待审核申请", "count": pending_count},
                {"label": "办理中申请", "count": in_progress_count},
                {"label": "需复核记录", "count": sum(1 for item in rows if item.status == WorkflowStatus.REJECTED)},
                {"label": "本周新增", "count": sum(1 for item in rows if is_same_week(item.submitted_at))},
            ],
        },
    }


def get_training_data():
    plans = list(TrainingPlan.objects.select_related("student").all())
    grade_options = unique_sorted([item.grade for item in plans])
    major_options = unique_sorted([item.major for item in plans])
    stage_options = unique_sorted([item.stage for item in plans])
    status_values = ["待提交", "待审核", "审核通过", "驳回修改"]

    status_counter = Counter(training_status_text(item.status) for item in plans)
    stage_counter = Counter(item.stage for item in plans)
    grade_completion = defaultdict(list)
    for plan in plans:
        grade_completion[plan.grade].append(plan.completion_percent)

    yearly_completion = []
    for grade, values in sorted(grade_completion.items()):
        yearly_completion.append({"grade": grade, "value": round(sum(values) / len(values))})

    year_trend = []
    for grade, values in sorted(grade_completion.items()):
        year_label = extract_year_label(grade)
        actual = round(sum(values) / len(values), 1)
        year_trend.append({"year": year_label, "actual": actual, "target": 85})

    return {
        "filters": {
            "default": {"grade": "", "major": "", "stage": "", "status": ""},
            "grades": grade_options,
            "majors": major_options,
            "stages": stage_options,
            "statuses": status_values,
        },
        "statCards": [
            {"title": "培养计划总数", "number": f"{len(plans)}项", "changeLabel": "当前筛选结果"},
            {
                "title": "待审核计划",
                "number": f"{status_counter.get('待审核', 0)}项",
                "changeLabel": "需要处理的计划",
            },
            {
                "title": "平均完成率",
                "number": f"{round(sum(item.completion_percent for item in plans) / len(plans)) if plans else 0}%",
                "changeLabel": f"审核通过 {status_counter.get('审核通过', 0)} 项",
            },
            {
                "title": "导师确认率",
                "number": f"{round(sum(1 for item in plans if item.advisor_name) * 100 / len(plans)) if plans else 0}%",
                "changeLabel": "按当前记录统计",
            },
        ],
        "charts": {
            "planCompletion": [
                {"name": "已完成", "value": status_counter.get("审核通过", 0)},
                {"name": "进行中", "value": status_counter.get("待审核", 0)},
                {"name": "未开始", "value": status_counter.get("待提交", 0)},
                {"name": "已终止", "value": status_counter.get("驳回修改", 0)},
            ],
            "completionTrend": year_trend,
            "statusDistribution": [{"name": name, "value": value} for name, value in status_counter.items()],
            "gradeCompletion": yearly_completion,
            "stageDistribution": [{"name": name, "value": value} for name, value in stage_counter.items()],
            "evaluationDistribution": [
                {"name": "优秀", "value": percent_of(plans, lambda item: item.completion_percent >= 85)},
                {"name": "良好", "value": percent_of(plans, lambda item: 70 <= item.completion_percent < 85)},
                {"name": "合格", "value": percent_of(plans, lambda item: 60 <= item.completion_percent < 70)},
                {"name": "不合格", "value": percent_of(plans, lambda item: item.completion_percent < 60)},
            ],
            "radar": [
                {"name": "课程质量", "value": scale_five(sum(item.completion_percent for item in plans), len(plans), 1.0)},
                {"name": "就业指导", "value": scale_five(sum(item.completion_percent for item in plans), len(plans), 0.9)},
                {"name": "学术支持", "value": scale_five(sum(item.completion_percent for item in plans), len(plans), 1.1)},
                {"name": "实践教学", "value": scale_five(sum(item.completion_percent for item in plans), len(plans), 0.8)},
                {"name": "导师指导", "value": scale_five(sum(1 for item in plans if item.advisor_name), len(plans), 1.2)},
            ],
        },
        "plans": [
            {
                "studentId": item.student.student_id if item.student else "",
                "name": item.student_name,
                "grade": item.grade,
                "major": item.major,
                "degreeType": degree_type_display(item.degree_type),
                "stage": item.stage,
                "advisor": item.advisor_name,
                "status": training_status_text(item.status),
                "tagType": status_type_for_workflow(item.status),
                "updatedAt": item.business_updated_at.isoformat() if item.business_updated_at else "",
                "completion": item.completion_percent,
            }
            for item in plans
        ],
        "notices": module_notice_items(ModuleCode.TRAINING, short_date=True, include_read=True),
        "todos": [
            {"label": "待审核培养计划", "count": status_counter.get("待审核", 0)},
            {"label": "待导师确认", "count": sum(1 for item in plans if not item.advisor_name)},
            {"label": "待补交材料", "count": status_counter.get("驳回修改", 0)},
            {"label": "本周到期任务", "count": sum(1 for item in plans if item.business_updated_at and is_same_week(item.business_updated_at))},
        ],
    }


def get_training_course_data():
    rows = list(CourseOffering.objects.all())
    return build_feature_workspace_payload(
        title="课程管理",
        subtitle="围绕课程开设、排课和执行状态进行管理",
        updated_at=latest_model_date(CourseOffering),
        primary_action={"label": "新增课程", "message": "后续可接入课程维护流程"},
        stat_cards=[
            {"title": "课程总数", "number": len(rows), "icon": "book", "changeLabel": "课程表记录数"},
            {
                "title": "待确认课程",
                "number": sum(1 for item in rows if item.status == WorkflowStatus.PENDING),
                "icon": "clock",
                "changeLabel": "待进入执行",
            },
            {
                "title": "开课专业数",
                "number": len({item.major for item in rows}),
                "icon": "layers",
                "changeLabel": "按专业去重",
            },
            {
                "title": "已完成课程",
                "number": sum(1 for item in rows if item.status == WorkflowStatus.COMPLETED),
                "icon": "check-circle",
                "changeLabel": "课程执行完成",
            },
        ],
        trend_chart=build_dated_trend(
            rows,
            "课程数量",
            "门",
            label_getter=lambda item: format_datetime(item.updated_at, "%m-%d"),
        ),
        donut_chart={
            "title": "课程状态分布",
            "unit": "门",
            "centerLabel": "课程总数",
            "items": counter_items(Counter(generic_status_text(item.status) for item in rows)),
        },
        bar_chart={
            "title": "专业课程数 TOP5",
            "unit": "门",
            "items": counter_items(Counter(item.major for item in rows).most_common(5), is_common=True),
        },
        table_card={
            "title": "课程安排列表",
            "columns": [
                {"prop": "courseName", "label": "课程名称", "minWidth": 160},
                {"prop": "teacher", "label": "任课教师", "minWidth": 100},
                {"prop": "major", "label": "专业", "minWidth": 140},
                {"prop": "schedule", "label": "上课时间", "minWidth": 130},
                {"prop": "status", "label": "状态", "minWidth": 90, "kind": "tag", "typeField": "statusType"},
            ],
            "rows": [
                {
                    "courseName": item.course_name,
                    "teacher": item.teacher_name,
                    "major": item.major,
                    "schedule": item.schedule_text,
                    "status": generic_status_text(item.status),
                    "statusType": status_type_for_workflow(item.status),
                }
                for item in rows
            ],
        },
        notice_items=module_notice_items(ModuleCode.TRAINING_COURSE),
        todo_items=[
            {"label": "待确认课程", "count": sum(1 for item in rows if item.status == WorkflowStatus.PENDING)},
            {"label": "进行中课程", "count": sum(1 for item in rows if item.status == WorkflowStatus.IN_PROGRESS)},
            {"label": "待排课专业", "count": len({item.major for item in rows if item.status == WorkflowStatus.DRAFT})},
            {"label": "本周更新课程", "count": sum(1 for item in rows if is_same_week(item.updated_at))},
        ],
    )


def get_degree_data():
    applications = list(DegreeApplication.objects.all())
    type_counter = Counter(item.application_type for item in applications)
    review_counter = Counter(item.paper_review_result for item in applications if item.paper_review_result)
    defense_counter = Counter(item.defense_result for item in applications if item.defense_result)
    discipline_counter = Counter(item.discipline for item in applications)
    award_year_counter = Counter(str(item.application_year) for item in applications if item.awarded_at)
    total_applications = len(applications)
    review_total = sum(review_counter.values()) or 1
    defense_total = sum(defense_counter.values()) or 1
    cumulative = 0
    discipline_distribution = []
    total_discipline = sum(discipline_counter.values()) or 1
    for name, count in discipline_counter.most_common():
        cumulative += count
        discipline_distribution.append(
            {"name": name, "count": count, "cumulative": round(cumulative * 100 / total_discipline, 1)}
        )

    year_counts = Counter(str(item.application_year) for item in applications)
    last_value = None
    trend_rows = []
    for year in sorted(year_counts.keys()):
        count = year_counts[year]
        growth = 0 if last_value in (None, 0) else round((count - last_value) * 100 / last_value, 1)
        trend_rows.append({"year": year, "count": count, "growth": growth})
        last_value = count

    return {
        "updatedAt": latest_model_date(DegreeApplication),
        "statCards": [
            {"title": "学位申请总数", "number": total_applications, "changeLabel": "学位申请记录数"},
            {
                "title": "待处理申请",
                "number": sum(1 for item in applications if item.award_status != WorkflowStatus.COMPLETED),
                "changeLabel": "未完成流程的申请",
            },
            {"title": "论文提交总数", "number": sum(1 for item in applications if item.paper_submitted_at), "changeLabel": "已提交论文"},
            {
                "title": "已授予学位",
                "number": sum(1 for item in applications if item.awarded_at),
                "changeLabel": "已完成授予流程",
            },
        ],
        "charts": {
            "applicationTypes": [{"name": name, "value": value} for name, value in type_counter.items()],
            "applicationTrend": trend_rows,
            "paperReview": [
                {"name": name, "value": round(value * 100 / review_total, 1)}
                for name, value in review_counter.items()
            ],
            "defenseResults": [
                {"name": name, "value": value, "percent": round(value * 100 / defense_total, 1)}
                for name, value in defense_counter.items()
            ],
            "awardTrend": [{"year": year, "value": award_year_counter[year]} for year in sorted(award_year_counter.keys())],
            "disciplineDistribution": discipline_distribution,
        },
        "notices": module_notice_items(ModuleCode.DEGREE),
        "todos": [
            {"label": "论文评阅待处理", "count": sum(1 for item in applications if not item.paper_review_result)},
            {"label": "答辩结果待录入", "count": sum(1 for item in applications if not item.defense_result)},
            {"label": "学位授予待确认", "count": sum(1 for item in applications if item.award_status == WorkflowStatus.PENDING)},
            {"label": "证书待发放", "count": sum(1 for item in applications if item.awarded_at and item.award_status != WorkflowStatus.COMPLETED)},
        ],
    }


def get_degree_defense_data():
    rows = list(DefenseSession.objects.all())
    return build_feature_workspace_payload(
        title="答辩管理",
        subtitle="围绕答辩场次、答辩安排和执行状态进行管理",
        updated_at=latest_model_date(DefenseSession),
        primary_action={"label": "新增答辩场次", "message": "后续可接入答辩排期流程"},
        stat_cards=[
            {"title": "答辩场次", "number": len(rows), "icon": "calendar", "changeLabel": "当前答辩安排数"},
            {
                "title": "待确认场次",
                "number": sum(1 for item in rows if item.status == WorkflowStatus.PENDING),
                "icon": "clock",
                "changeLabel": "等待进入正式执行",
            },
            {
                "title": "答辩学生数",
                "number": sum(item.student_count for item in rows),
                "icon": "users",
                "changeLabel": "答辩学生汇总",
            },
            {
                "title": "已完成场次",
                "number": sum(1 for item in rows if item.status == WorkflowStatus.COMPLETED),
                "icon": "check-circle",
                "changeLabel": "已完成答辩",
            },
        ],
        trend_chart=build_dated_trend(
            rows,
            "场次数量",
            "场",
            label_getter=lambda item: format_datetime(item.scheduled_at, "%m-%d"),
            value_getter=lambda item: item.student_count,
        ),
        donut_chart={
            "title": "答辩状态分布",
            "unit": "场",
            "centerLabel": "场次总数",
            "items": counter_items(Counter(generic_status_text(item.status) for item in rows)),
        },
        bar_chart={
            "title": "场次学生数 TOP5",
            "unit": "人",
            "items": [{"name": item.session_name, "value": item.student_count} for item in sorted(rows, key=lambda row: row.student_count, reverse=True)[:5]],
        },
        table_card={
            "title": "答辩安排列表",
            "columns": [
                {"prop": "sessionName", "label": "场次名称", "minWidth": 180},
                {"prop": "chair", "label": "主席", "minWidth": 100},
                {"prop": "room", "label": "地点", "minWidth": 100},
                {"prop": "students", "label": "学生数", "minWidth": 80},
                {"prop": "status", "label": "状态", "minWidth": 90, "kind": "tag", "typeField": "statusType"},
                {"prop": "time", "label": "时间", "minWidth": 130},
            ],
            "rows": [
                {
                    "sessionName": item.session_name,
                    "chair": item.chair_name,
                    "room": item.room,
                    "students": item.student_count,
                    "status": generic_status_text(item.status),
                    "statusType": status_type_for_workflow(item.status),
                    "time": format_datetime(item.scheduled_at, "%m-%d %H:%M"),
                }
                for item in rows
            ],
        },
        notice_items=module_notice_items(ModuleCode.DEGREE_DEFENSE),
        todo_items=[
            {"label": "待确认场次", "count": sum(1 for item in rows if item.status == WorkflowStatus.PENDING)},
            {"label": "进行中场次", "count": sum(1 for item in rows if item.status == WorkflowStatus.IN_PROGRESS)},
            {"label": "待录入结果", "count": sum(1 for item in rows if item.status != WorkflowStatus.COMPLETED)},
            {"label": "本周答辩", "count": sum(1 for item in rows if is_same_week(item.scheduled_at))},
        ],
    )


def get_scholarship_data():
    awards = list(ScholarshipAward.objects.all())
    scholarship_items = [item for item in awards if item.award_category == "scholarship"]
    aid_items = [item for item in awards if item.award_category == "aid"]
    grade_counter = defaultdict(lambda: {"national": 0, "academic": 0, "social": 0})
    for item in scholarship_items:
        bucket = grade_counter[item.grade]
        label = map_award_bucket(item.award_type)
        bucket[label] += 1

    total_amount = sum_amount(awards)
    scholarship_amount = sum_amount(scholarship_items)
    aid_amount = sum_amount(aid_items)
    unique_students = len({item.student_id for item in awards if item.student_id})

    fund_counter = Counter(str(item.award_year) for item in awards)
    major_counter = Counter(item.major for item in awards)
    type_counter = Counter(item.award_type for item in scholarship_items)
    aid_type_counter = Counter(item.award_type for item in aid_items)
    student_award_counter = Counter(item.student_name for item in awards)
    single_count = sum(1 for count in student_award_counter.values() if count == 1)
    double_count = sum(1 for count in student_award_counter.values() if count == 2)
    multi_count = sum(1 for count in student_award_counter.values() if count >= 3)

    return {
        "updatedAt": latest_model_date(ScholarshipAward),
        "statCards": [
            {"title": "奖学金总额", "number": round(float(scholarship_amount / Decimal("10000")), 1), "unit": "万元", "changeLabel": "奖学金记录汇总"},
            {"title": "助学金总额", "number": round(float(aid_amount / Decimal("10000")), 1), "unit": "万元", "changeLabel": "助学金记录汇总"},
            {"title": "获奖总人数", "number": unique_students, "unit": "人", "changeLabel": "按学生去重"},
            {"title": "获奖人次", "number": len(awards), "unit": "人次", "changeLabel": "所有奖助记录数"},
            {
                "title": "整体获奖率",
                "number": round(unique_students * 100 / Student.objects.count(), 1) if Student.objects.count() else 0,
                "unit": "%",
                "changeLabel": "按学生主表口径",
            },
        ],
        "charts": {
            "scholarshipTypes": percent_items(type_counter),
            "aidTypes": percent_items(aid_type_counter),
            "gradeAwards": [
                {"grade": grade, **values}
                for grade, values in sorted(grade_counter.items())
            ],
            "studentAwardDistribution": [
                {"name": "单次获奖", "value": single_count, "percent": round(single_count * 100 / (len(awards) or 1), 1)},
                {"name": "双次获奖", "value": double_count, "percent": round(double_count * 100 / (len(awards) or 1), 1)},
                {"name": "三次及以上", "value": multi_count, "percent": round(multi_count * 100 / (len(awards) or 1), 1)},
            ],
            "majorAwardTop": [{"name": name, "value": value, "label": f"{value}人次"} for name, value in major_counter.most_common(6)],
            "fundTrend": [{"year": year, "value": float(total_amount if len(fund_counter) == 1 and year in fund_counter else sum_amount([item for item in awards if str(item.award_year) == year]))} for year in sorted(fund_counter.keys())],
        },
        "notices": module_notice_items(ModuleCode.SCHOLARSHIP),
        "todos": [
            {"label": "待确认奖助记录", "count": len([item for item in awards if not item.awarded_on])},
            {"label": "待复核学生", "count": sum(1 for count in Counter(item.student_name for item in awards).values() if count >= 2)},
            {"label": "待发放资金", "count": len([item for item in awards if item.amount <= 0])},
            {"label": "本周新增记录", "count": sum(1 for item in awards if item.awarded_on and is_same_week(item.awarded_on))},
        ],
    }


def get_employment_data():
    records = list(EmploymentRecord.objects.all())
    year_counter = Counter(str(item.graduation_year) for item in records)
    sorted_years = sorted(year_counter.keys())

    employment_series = []
    signing_series = []
    further_study_series = []
    for year in sorted_years:
        year_records = [item for item in records if str(item.graduation_year) == year]
        total = len(year_records) or 1
        employment_rate = round(sum(1 for item in year_records if item.destination_type) * 100 / total, 1)
        signing_rate = round(sum(1 for item in year_records if item.is_signed) * 100 / total, 1)
        further_rate = round(sum(1 for item in year_records if item.is_further_study) * 100 / total, 1)
        employment_series.append({"year": year, "value": employment_rate})
        signing_series.append({"year": year, "value": signing_rate})
        further_study_series.append({"year": year, "value": further_rate})

    destination_counter = Counter(item.destination_type for item in records)
    unit_counter = Counter(item.unit_nature for item in records if item.unit_nature)
    industry_counter = Counter(item.industry for item in records if item.industry)
    province_counter = Counter(item.province for item in records if item.province)
    total_records = len(records) or 1

    return {
        "statCards": [
            {"title": "就业记录总数", "number": len(records), "unit": "人", "changeLabel": "就业记录数"},
            {
                "title": "签约人数",
                "number": sum(1 for item in records if item.is_signed),
                "unit": "人",
                "changeLabel": "已签约记录",
            },
            {
                "title": "升学人数",
                "number": sum(1 for item in records if item.is_further_study),
                "unit": "人",
                "changeLabel": "继续深造去向",
            },
            {
                "title": "就业落实率",
                "number": round(sum(1 for item in records if item.destination_type) * 100 / total_records, 1),
                "unit": "%",
                "changeLabel": "按就业记录口径",
            },
        ],
        "metrics": [
            {"key": "employment", "label": "就业率", "unit": "%", "series": employment_series},
            {"key": "signing", "label": "签约率", "unit": "%", "series": signing_series},
            {"key": "furtherStudy", "label": "升学率", "unit": "%", "series": further_study_series},
        ],
        "charts": {
            "unitNature": [{"name": name, "value": value} for name, value in unit_counter.most_common(5)],
            "industryTop": [{"name": name, "value": value} for name, value in industry_counter.most_common(7)],
            "destinationStats": [
                {"type": name, "count": value, "percent": round(value * 100 / total_records, 1)}
                for name, value in destination_counter.most_common(5)
            ],
            "infoStats": [
                {"label": "已填去向", "value": sum(1 for item in records if item.destination_type), "valueNum": sum(1 for item in records if item.destination_type)},
                {"label": "已签约", "value": sum(1 for item in records if item.is_signed), "valueNum": sum(1 for item in records if item.is_signed)},
                {"label": "升学深造", "value": sum(1 for item in records if item.is_further_study), "valueNum": sum(1 for item in records if item.is_further_study)},
                {"label": "待完善", "value": sum(1 for item in records if not item.destination_type), "valueNum": sum(1 for item in records if not item.destination_type)},
            ],
            "provinceDistribution": [{"name": name, "value": value} for name, value in province_counter.most_common(10)],
        },
    }


def get_intelligent_prediction_data():
    snapshots = build_prediction_sources()
    indicators = list(PredictionIndicatorDefinition.objects.all())
    student_rows = []
    risk_rows = []

    for snapshot in snapshots:
        monthly = prediction_monthly_rows(snapshot)
        current_snapshot = serialize_prediction_current_snapshot(snapshot)
        monthly_metrics = serialize_prediction_monthly_metrics(monthly)
        monthly_records = prediction_build_monthly_records(monthly_metrics)
        radar_values = prediction_compute_radar(current_snapshot)
        trend_actual = [prediction_compute_monthly_index(item) for item in monthly_records]
        forecast_trend = prediction_build_projection(trend_actual, mode="trend")
        factors = prediction_build_factor_breakdown(current_snapshot, radar_values)
        risk_profile = prediction_build_risk_profile(factors, snapshot)
        summary = prediction_build_summary(risk_profile, forecast_trend)
        student_rows.append(
            {
                "id": f"stu-{snapshot.student.student_id}",
                "studentId": snapshot.student.student_id,
                "name": snapshot.student.name,
                "degreeType": degree_type_display(snapshot.student.degree_type),
                "college": snapshot.student.college,
                "major": snapshot.student.major,
                "grade": snapshot.student.grade,
                "riskScore": risk_profile["riskScore"],
                "riskCategory": risk_profile["riskCategory"],
                "riskLevel": risk_level_display(snapshot.risk_level),
                "riskType": status_type_for_risk(snapshot.risk_level),
                "riskField": snapshot.risk_field or risk_profile["riskField"],
                "suggestion": snapshot.suggestion or risk_profile["suggestion"],
                "summary": summary,
                "currentSnapshot": current_snapshot,
                "monthlyMetrics": monthly_metrics,
            }
        )
        risk_rows.append(
            {
                "studentId": snapshot.student.student_id,
                "name": snapshot.student.name,
                "grade": snapshot.student.grade,
                "major": snapshot.student.major,
                "college": snapshot.student.college,
                "riskScore": risk_profile["riskScore"],
                "riskCategory": risk_profile["riskCategory"],
                "riskLevel": risk_level_display(snapshot.risk_level),
                "riskType": status_type_for_risk(snapshot.risk_level),
                "riskField": snapshot.risk_field or risk_profile["riskField"],
                "suggestion": snapshot.suggestion or risk_profile["suggestion"],
            }
        )

    high_risk = sum(1 for item in snapshots if item.risk_level in {"high", "alert"})
    alert_students = sum(1 for item in snapshots if item.risk_level != "low")
    avg_index = round(sum(composite_prediction_index(item) for item in snapshots) / len(snapshots), 1) if snapshots else 0
    delayed_feedback = round(
        sum(1 for item in snapshots if item.advisor_avg_response_days >= 8) * 100 / len(snapshots), 1
    ) if snapshots else 0

    monthly_axis = []
    trend_values = []
    peer_values = []
    if student_rows:
        monthly_axis = student_rows[0]["monthlyMetrics"]["months"][:6]
        selected = student_rows[0]["monthlyMetrics"]
        trend_values = selected["courseAverage"][:6]
        peer_values = [round(sum(student["monthlyMetrics"]["courseAverage"][index] for student in student_rows) / len(student_rows), 1) for index in range(min(6, len(selected["courseAverage"])))]

    factor_counter = Counter()
    for row in risk_rows:
        if row["riskField"]:
            for field in row["riskField"].split("、"):
                factor_counter[field.strip()] += 1

    return {
        "title": "智能预测与预警",
        "subtitle": "围绕学生发展趋势、风险预警和关键影响因素进行智能分析",
        "updatedAt": latest_prediction_payload_datetime(snapshots),
        "aiCapabilities": prediction_ai_capabilities(),
        "filters": {
            "default": {
                "college": PREDICTION_SCOPE_COLLEGE,
                "major": "全部专业",
                "grade": "全部年级",
                "range": "近6个月",
                "riskType": "全部",
            },
            "colleges": [PREDICTION_SCOPE_COLLEGE],
            "majors": ["全部专业"] + unique_sorted([item["major"] for item in student_rows]),
            "grades": ["全部年级"] + unique_sorted([item["grade"] for item in student_rows]),
            "ranges": ["近1个月", "近3个月", "近6个月"],
            "riskTypes": ["全部", "学业风险", "培养风险", "科研风险", "支持风险"],
        },
        "radarIndicators": prediction_resolve_radar_indicators(indicators),
        "students": student_rows,
        "riskStudents": sorted(risk_rows, key=risk_sort_key),
        "primaryAction": {"label": "刷新预测", "message": "预测分析结果已刷新"},
        "statCards": [
            {"title": "高风险学生", "number": high_risk, "icon": "alert-circle", "changeLabel": "当前重点关注对象"},
            {"title": "预警关注学生", "number": alert_students, "icon": "shield", "changeLabel": "需要持续跟踪"},
            {"title": "平均发展指数", "number": avg_index, "icon": "trend", "changeLabel": "按样本综合测算"},
            {"title": "导师反馈延迟率", "number": f"{delayed_feedback}%", "icon": "clock", "changeLabel": "反馈类风险占比较高"},
        ],
        "trendChart": {
            "title": "学生发展趋势分析",
            "seriesName": "综合发展指数",
            "unit": "分",
            "labels": monthly_axis,
            "values": trend_values,
            "targetName": "同年级平均",
            "targetValues": peer_values,
        },
        "donutChart": {
            "title": "风险等级分布",
            "unit": "人",
            "centerLabel": "预警总人数",
            "items": [
                {"name": "高风险", "value": sum(1 for item in snapshots if item.risk_level == "high"), "color": "#F53F3F"},
                {"name": "预警", "value": sum(1 for item in snapshots if item.risk_level == "alert"), "color": "#FA8C16"},
                {"name": "低风险", "value": sum(1 for item in snapshots if item.risk_level in {"medium", "low"}), "color": "#165DFF"},
            ],
        },
        "barChart": {
            "title": "关键影响因素 TOP5",
            "unit": "%",
            "items": [
                {"name": name, "value": round(value * 100 / (len(risk_rows) or 1), 1)}
                for name, value in factor_counter.most_common(5)
            ],
        },
        "tableCard": {
            "title": "高风险学生 TOP5",
            "columns": [
                {"prop": "studentId", "label": "学号", "width": 110},
                {"prop": "name", "label": "姓名", "width": 80},
                {"prop": "riskLevel", "label": "风险等级", "width": 100, "kind": "tag", "typeField": "riskType"},
                {"prop": "riskField", "label": "主要风险领域", "minWidth": 140},
                {"prop": "suggestion", "label": "建议动作", "minWidth": 160},
            ],
            "rows": sorted(risk_rows, key=risk_sort_key)[:5],
        },
        "noticeCard": {"title": "AI 预警提示", "items": module_notice_items(ModuleCode.INTELLIGENT_PREDICTION, short_date=True)},
        "todoCard": {
            "title": "模型与治理待办",
            "items": [
                {"label": "待复核高风险学生", "count": high_risk},
                {"label": "待更新预测样本", "count": sum(1 for item in snapshots if item.monthly_metrics.count() < 6)},
                {"label": "待补录导师反馈", "count": sum(1 for item in snapshots if item.advisor_meeting_count_60d == 0)},
                {"label": "待导出周报", "count": 2 if snapshots else 0},
            ],
        },
    }


def get_intelligent_prediction_data():
    snapshots = build_prediction_sources()
    indicators = list(PredictionIndicatorDefinition.objects.all())
    student_rows = []
    risk_rows = []

    for snapshot in snapshots:
        # The list only displays peer trends. Full peer contexts are built on
        # demand by the context/analysis endpoints, not once per list row.
        context = build_prediction_context(snapshot, snapshots, indicators, include_peer_references=False)
        student_payload = prediction_compose_student_payload(snapshot, context)
        student_rows.append(student_payload)
        risk_rows.append(
            {
                "studentId": student_payload["studentId"],
                "name": student_payload["name"],
                "grade": student_payload["grade"],
                "major": student_payload["major"],
                "college": student_payload["college"],
                "riskScore": student_payload["riskScore"],
                "riskCategory": student_payload["riskCategory"],
                "riskLevel": student_payload["riskLevel"],
                "riskType": student_payload["riskType"],
                "riskField": student_payload["riskField"],
                "suggestion": student_payload["suggestion"],
            }
        )

    prediction_populate_list_peer_trends(student_rows)

    high_risk = sum(1 for item in snapshots if item.risk_level in {"high", "alert"})
    alert_students = sum(1 for item in snapshots if item.risk_level != "low")
    avg_index = round(sum(composite_prediction_index(item) for item in snapshots) / len(snapshots), 1) if snapshots else 0
    delayed_feedback = round(
        sum(1 for item in snapshots if item.advisor_avg_response_days >= 8) * 100 / len(snapshots), 1
    ) if snapshots else 0

    monthly_axis = []
    trend_values = []
    peer_values = []
    if student_rows:
        monthly_axis = student_rows[0]["monthlyMetrics"]["months"][:6]
        selected = student_rows[0]["monthlyMetrics"]
        trend_values = selected["courseAverage"][:6]
        peer_values = [
            round(
                sum(student["monthlyMetrics"]["courseAverage"][index] for student in student_rows) / len(student_rows),
                1,
            )
            for index in range(min(6, len(selected["courseAverage"])))
        ]

    factor_counter = Counter()
    for row in risk_rows:
        if row["riskField"]:
            for field in str(row["riskField"]).replace("、", "，").split("，"):
                normalized = field.strip()
                if normalized:
                    factor_counter[normalized] += 1

    grade_options = unique_sorted([item["grade"] for item in student_rows if item["grade"]])
    # 默认不预选具体年级：原来硬编码偏好 2023 级，导致进页面时
    # 预测对象下拉只剩该年级的少数人，看起来像"数据只有几个人"。
    default_grade = "全部年级"

    return {
        "title": "智能预测与预警",
        "subtitle": "面向山东大学政治学与公共管理学院研究生的趋势预测、风险解读与治理支持。",
        "businessScope": {
            "university": PREDICTION_SCOPE_UNIVERSITY,
            "college": PREDICTION_SCOPE_COLLEGE,
            "audience": PREDICTION_SCOPE_AUDIENCE,
        },
        "updatedAt": latest_prediction_payload_datetime(snapshots),
        "aiCapabilities": prediction_ai_capabilities(),
        "filters": {
            "default": {
                "college": PREDICTION_SCOPE_COLLEGE,
                "major": "全部专业",
                "grade": default_grade,
                "range": "近6个月",
                "riskType": "全部",
            },
            "colleges": [PREDICTION_SCOPE_COLLEGE],
            "majors": ["全部专业"] + unique_sorted([item["major"] for item in student_rows if item["major"]]),
            "grades": ["全部年级"] + grade_options,
            "ranges": ["近3个月", "近6个月", "近9个月"],
            "riskTypes": ["全部", "学业风险", "培养风险", "科研风险", "支持风险"],
        },
        "radarIndicators": prediction_resolve_radar_indicators(indicators),
        "students": student_rows,
        "riskStudents": sorted(risk_rows, key=risk_sort_key),
        "primaryAction": {"label": "刷新预测", "message": "预测分析结果已刷新"},
        "statCards": [
            {"title": "高风险学生", "number": high_risk, "icon": "alert-circle", "changeLabel": "学院当前重点关注对象"},
            {"title": "预警关注学生", "number": alert_students, "icon": "shield", "changeLabel": "需持续跟踪的研究生样本"},
            {"title": "平均发展指数", "number": avg_index, "icon": "trend", "changeLabel": "按学院样本综合测算"},
            {"title": "导师反馈延迟率", "number": f"{delayed_feedback}%", "icon": "clock", "changeLabel": "反馈类风险占比较高"},
        ],
        "trendChart": {
            "title": "学院样本发展趋势分析",
            "seriesName": "综合发展指数",
            "unit": "分",
            "labels": monthly_axis,
            "values": trend_values,
            "targetName": "同年级平均",
            "targetValues": peer_values,
        },
        "donutChart": {
            "title": "风险等级分布",
            "unit": "人",
            "centerLabel": "预警总人数",
            "items": [
                {"name": "高风险", "value": sum(1 for item in snapshots if item.risk_level == "high"), "color": "#F53F3F"},
                {"name": "预警", "value": sum(1 for item in snapshots if item.risk_level == "alert"), "color": "#FA8C16"},
                {"name": "低风险", "value": sum(1 for item in snapshots if item.risk_level in {"medium", "low"}), "color": "#165DFF"},
            ],
        },
        "barChart": {
            "title": "关键影响因素 TOP5",
            "unit": "%",
            "items": [
                {"name": name, "value": round(value * 100 / (len(risk_rows) or 1), 1)}
                for name, value in factor_counter.most_common(5)
            ],
        },
        "tableCard": {
            "title": "高风险学生 TOP5",
            "columns": [
                {"prop": "studentId", "label": "学号", "width": 110},
                {"prop": "name", "label": "姓名", "width": 80},
                {"prop": "riskLevel", "label": "风险等级", "width": 100, "kind": "tag", "typeField": "riskType"},
                {"prop": "riskField", "label": "主要风险领域", "minWidth": 140},
                {"prop": "suggestion", "label": "建议动作", "minWidth": 160},
            ],
            "rows": sorted(risk_rows, key=risk_sort_key)[:5],
        },
        "noticeCard": {
            "title": "AI 预警提示",
            "items": module_notice_items(ModuleCode.INTELLIGENT_PREDICTION, short_date=True),
        },
        "todoCard": {
            "title": "模型与治理待办",
            "items": [
                {"label": "待复核高风险学生", "count": high_risk},
                {"label": "待更新预测样本", "count": sum(1 for item in snapshots if item.monthly_metrics.count() < 6)},
                {"label": "待补录导师反馈", "count": sum(1 for item in snapshots if item.advisor_meeting_count_60d == 0)},
                {"label": "待导出周报", "count": 2 if snapshots else 0},
            ],
        },
    }


DEFAULT_PREDICTION_RADAR_INDICATORS = [
    {"name": "学业投入与掌握", "max": 100},
    {"name": "科研训练与创新", "max": 100},
    {"name": "自我管理与学习策略", "max": 100},
    {"name": "导师支持与学术互动", "max": 100},
    {"name": "学术共同体融入", "max": 100},
    {"name": "实践参与与公共服务", "max": 100},
    {"name": "身心健康与持续发展", "max": 100},
]


PREDICTION_FACTOR_CATEGORY_MAP = {
    "学业投入与掌握": "学业风险",
    "科研训练与创新": "科研风险",
    "自我管理与学习策略": "培养风险",
    "导师支持与学术互动": "支持风险",
    "学术共同体融入": "培养风险",
    "实践参与与公共服务": "培养风险",
    "身心健康与持续发展": "支持风险",
}


PREDICTION_RISK_SUGGESTION_MAP = {
    "学业风险": "补强课程学习投入并开展阶段学业督导",
    "培养风险": "复核培养环节参与情况并制定阶段提升计划",
    "科研风险": "跟进科研任务、项目参与与成果产出节奏",
    "支持风险": "强化导师沟通、支持服务与身心关怀",
}


PREDICTION_ANALYSIS_EXPERIMENTS = {
    "default": {
        "promptVersion": "prediction_analyze_v2",
        "systemTemplate": "prediction_analyze_system_v1.txt",
        "userTemplate": "prediction_analyze_user_v1.txt",
        "retrievalStrategy": "local_keyword_rag",
        "model": "not_connected",
        "generationMode": "rule_based_scaffold",
    },
    "prompt_v1_compact": {
        "promptVersion": "prediction_analyze_v2_compact",
        "systemTemplate": "prediction_analyze_system_v1.txt",
        "userTemplate": "prediction_analyze_user_v1.txt",
        "retrievalStrategy": "local_keyword_rag",
        "model": "not_connected",
        "generationMode": "rule_based_scaffold",
    },
}


PREDICTION_CHAT_EXPERIMENTS = {
    "default": {
        "promptVersion": "prediction_chat_v2",
        "systemTemplate": "prediction_chat_system_v1.txt",
        "userTemplate": "prediction_chat_user_v1.txt",
        "retrievalStrategy": "local_keyword_rag",
        "model": "not_connected",
        "generationMode": "rule_based_scaffold",
    },
    "prompt_v1_compact": {
        "promptVersion": "prediction_chat_v2_compact",
        "systemTemplate": "prediction_chat_system_v1.txt",
        "userTemplate": "prediction_chat_user_v1.txt",
        "retrievalStrategy": "local_keyword_rag",
        "model": "not_connected",
        "generationMode": "rule_based_scaffold",
    },
}


def get_intelligent_prediction_context(student_id):
    text = str(student_id or "").strip()
    if not text:
        return None

    snapshots = build_prediction_sources()
    target = next((item for item in snapshots if item.student and item.student.student_id == text), None)
    if target is None:
        return None

    indicators = list(PredictionIndicatorDefinition.objects.all())
    return build_prediction_context(target, snapshots, indicators)


def prediction_populate_list_peer_trends(student_rows):
    """Aggregate monthly indices once, excluding the target from its peers."""
    totals = defaultdict(lambda: defaultdict(lambda: [Decimal(0), 0]))
    for row in student_rows:
        for record, value in zip(row["monthlyRecords"], row["trendActual"]):
            bucket = totals[row["grade"]][record["month"]]
            bucket[0] += Decimal(str(value))
            bucket[1] += 1
    for row in student_rows:
        own_values = {
            record["month"]: value
            for record, value in zip(row["monthlyRecords"], row["trendActual"])
        }
        values = []
        for month, (total, count) in sorted(totals[row["grade"]].items()):
            has_own = month in own_values
            size = count - int(has_own)
            if size:
                peer_total = total - Decimal(str(own_values.get(month, 0)))
                values.append(round(float(peer_total / size), 1))
        row["peerTrend"] = values
        row["peerAverageTrend"] = values
        row["peerAverageTrendText"] = prediction_format_series_text(values)


def build_prediction_context(snapshot, all_snapshots, indicators, *, include_peer_references=True):
    current_snapshot = serialize_prediction_current_snapshot(snapshot)
    monthly_metrics = serialize_prediction_monthly_metrics(prediction_monthly_rows(snapshot))
    monthly_records = prediction_build_monthly_records(monthly_metrics)
    radar_values = prediction_compute_radar(current_snapshot)
    trend_actual = [prediction_compute_monthly_index(item) for item in monthly_records]
    trend_forecast = prediction_build_historical_forecast(trend_actual)
    forecast_trend = prediction_build_projection(trend_actual, mode="trend")
    forecast_scenario = prediction_build_projection(trend_actual, mode="scenario")
    forecast_upper_trend = prediction_build_upper_projection(forecast_trend, padding=3.5)
    forecast_upper_scenario = prediction_build_upper_projection(forecast_scenario, padding=2.8)
    factors = prediction_build_factor_breakdown(current_snapshot, radar_values)
    risk_profile = prediction_build_risk_profile(factors, snapshot)
    gauges = prediction_build_gauges(current_snapshot, risk_profile)
    summary = prediction_build_summary(risk_profile, forecast_trend)
    peer_references = (
        build_prediction_peer_references(snapshot, all_snapshots)
        if include_peer_references
        else {"sameGrade": {}, "sameMajor": {}, "sameGradeMajor": {}}
    )

    return {
        "found": True,
        "student": serialize_prediction_student(snapshot),
        "prediction": {
            "riskScore": risk_profile["riskScore"],
            "riskLevel": risk_level_display(snapshot.risk_level),
            "riskType": status_type_for_risk(snapshot.risk_level),
            "riskCategory": risk_profile["riskCategory"],
            "riskField": snapshot.risk_field or risk_profile["riskField"],
            "suggestion": snapshot.suggestion or risk_profile["suggestion"],
            "capturedAt": format_datetime(snapshot.captured_at),
            "updatedAt": format_datetime(snapshot.updated_at),
        },
        "currentSnapshot": current_snapshot,
        "monthlyMetrics": monthly_metrics,
        "derived": {
            "radarIndicators": prediction_resolve_radar_indicators(indicators),
            "radarValues": radar_values,
            "monthlyRecords": monthly_records,
            "trendActual": trend_actual,
            "trendForecast": trend_forecast,
            "forecastTrend": forecast_trend,
            "forecastScenario": forecast_scenario,
            "forecastUpperTrend": forecast_upper_trend,
            "forecastUpperScenario": forecast_upper_scenario,
            "keyFactors": factors,
            "gauges": gauges,
            "summary": summary,
            "period": "未来 3 个月",
            "compositeIndexCurrent": round(trend_actual[-1], 1) if trend_actual else 0,
        },
        "peerReferences": peer_references,
        "promptContext": {
            "student": serialize_prediction_student(snapshot),
            "prediction": {
                "riskScore": risk_profile["riskScore"],
                "riskLevel": risk_level_display(snapshot.risk_level),
                "riskCategory": risk_profile["riskCategory"],
                "riskField": snapshot.risk_field or risk_profile["riskField"],
                "suggestion": snapshot.suggestion or risk_profile["suggestion"],
            },
            "currentSnapshot": current_snapshot,
            "keyFactors": factors[:3],
            "trend": {
                "months": monthly_metrics["months"],
                "indexValues": trend_actual,
                "forecastValues": forecast_trend,
            },
            "peerReferences": {
                "sameGrade": peer_references["sameGrade"],
                "sameMajor": peer_references["sameMajor"],
                "sameGradeMajor": peer_references["sameGradeMajor"],
            },
        },
    }


def get_intelligent_prediction_analysis(student_id, tab="trend", experiment_key="default", runtime_options=None):
    context = get_intelligent_prediction_context(student_id)
    if context is None:
        return None

    resolved_tab = normalize_prediction_analysis_tab(tab)
    experiment = resolve_prediction_analysis_experiment(experiment_key)
    runtime_options = normalize_prediction_runtime_options(runtime_options)
    retrieved_knowledge = retrieve_prediction_analysis_knowledge(context, resolved_tab)
    prompt_strategy = resolve_prediction_analysis_prompt_strategy(
        tab=resolved_tab,
        retrieved_knowledge=retrieved_knowledge,
        experiment=experiment,
    )
    fallback_result = {
        "summary": context["derived"]["summary"],
        "sections": build_prediction_analysis_sections(context, resolved_tab),
        "evidence": build_prediction_analysis_evidence(context, resolved_tab, retrieved_knowledge),
    }
    prompt_package = build_prediction_analysis_prompt_package(
        context=context,
        tab=resolved_tab,
        prompt_strategy=prompt_strategy,
        retrieved_knowledge=retrieved_knowledge,
    )
    llm_result = llm.invoke_prediction_analysis_completion(prompt_package, runtime_options=runtime_options)
    result = llm.normalize_prediction_analysis_result(llm_result.get("answer"), fallback_result)
    generation_mode = prompt_strategy["generationMode"]
    model_name = prompt_strategy["model"]
    if llm_result.get("used"):
        generation_mode = llm_result.get("apiStyle", "responses")
        model_name = llm_result.get("model") or model_name
    elif llm_result.get("reason") not in {"", "llm_disabled", "prompt_missing"}:
        generation_mode = "fallback_after_llm_error"
        model_name = llm_result.get("model") or model_name

    return attach_prediction_debug_payload({
        "studentId": context["student"]["studentId"],
        "tab": resolved_tab,
        "summary": result["summary"],
        "sections": result["sections"],
        "evidence": result["evidence"],
        "capabilities": prediction_ai_capabilities(),
    }, trace={
        "promptVersion": prompt_strategy["promptVersion"],
        "promptRoute": prompt_strategy["routeKey"],
        "promptTemplates": {
            "system": prompt_strategy["systemTemplate"],
            "user": prompt_strategy["userTemplate"],
        },
        "retrievalStrategy": prompt_strategy["retrievalStrategy"],
        "retrievedCount": len(retrieved_knowledge),
        "model": model_name,
        "generationMode": generation_mode,
        "llmUsed": llm_result.get("used", False),
        "llmReason": llm_result.get("reason", ""),
        "provider": llm_result.get("provider", ""),
        "providerResponseId": llm_result.get("responseId", ""),
        "usage": llm_result.get("usage"),
        "experimentKey": experiment_key if experiment_key in PREDICTION_ANALYSIS_EXPERIMENTS else "default",
        "runtimeOptions": runtime_options,
    }, prompt_package=prompt_package)


def stream_intelligent_prediction_chat(
    student_id, question, chat_history=None, experiment_key="default", runtime_options=None
):
    """流式问答。yield 过程事件，最后一个事件是组装好的完整 payload。

    返回 None 表示学生不存在/问题为空，交由视图层转成 404/400。
    Agent 不可用时退化为「只发一个 final 事件」的伪流式，
    这样前端不需要为两条路径写两套渲染逻辑。
    """
    from .prediction_cohort import is_cohort_question, build_cohort_chat
    if is_cohort_question(question, chat_history):
        def cohort_stream():
            yield {"type": "status", "stage": "cohort", "message": "正在比较全部实测学生…"}
            payload = build_cohort_chat(str(question).strip(), chat_history)
            text = payload["answer"]["directAnswer"]
            yield {"type": "answer_text", "text": text}
            yield {"type": "final", "payload": payload}
        return cohort_stream()
    context = get_intelligent_prediction_context(student_id)
    if context is None:
        return None

    cleaned_question = str(question or "").strip()
    if not cleaned_question:
        return None

    normalized_options = normalize_prediction_runtime_options(runtime_options)

    def event_stream():
        if not prediction_agent.agent_enabled(normalized_options):
            payload = get_intelligent_prediction_chat(
                student_id=student_id,
                question=cleaned_question,
                chat_history=chat_history,
                experiment_key=experiment_key,
                runtime_options=runtime_options,
            )
            yield {"type": "final", "payload": payload}
            return

        history = normalize_prediction_chat_history(chat_history)
        retrieved_knowledge = rag.retrieve_prediction_knowledge(cleaned_question, context)
        fallback_answer = build_prediction_chat_answer(
            context, cleaned_question, retrieved_knowledge
        )
        policy_question = is_prediction_policy_question(cleaned_question)
        experiment = resolve_prediction_chat_experiment(experiment_key)

        final_event = None
        for event in prediction_agent.stream_prediction_chat_agent(
            context=context,
            question=cleaned_question,
            chat_history=history,
            runtime_options=normalized_options,
        ):
            if event.get("type") == "final":
                final_event = event
                continue
            yield event

        # Agent 中途失败：回落到非流式单次 pipeline，仍以 final 事件收口
        if not final_event or not final_event.get("used"):
            payload = get_intelligent_prediction_chat(
                student_id=student_id,
                question=cleaned_question,
                chat_history=chat_history,
                experiment_key=experiment_key,
                runtime_options={**(runtime_options or {}), "useAgent": False},
            )
            yield {"type": "final", "payload": payload}
            return

        answer = llm.normalize_prediction_chat_answer(
            final_event.get("answer"), fallback_answer
        )
        if not answer.get("citations") and final_event.get("citationsPool"):
            answer["citations"] = llm.normalize_citations(final_event["citationsPool"])

        payload = attach_prediction_debug_payload({
            "studentId": context["student"]["studentId"],
            "question": cleaned_question,
            "answer": answer,
            "capabilities": prediction_ai_capabilities(),
        }, trace={
                "promptVersion": "prediction_chat_agent_v1",
                "promptRoute": "agent_tool_loop",
                "retrievalStrategy": "agent_tool_driven_rag",
                "retrievedCount": len(final_event.get("citationsPool") or []),
                "policyQuestion": policy_question,
                "model": final_event.get("model") or experiment["model"],
                "generationMode": "agent_tool_loop_stream",
                "experimentKey": experiment_key if experiment_key in PREDICTION_CHAT_EXPERIMENTS else "default",
                "llmUsed": True,
                "llmReason": "",
                "agent": final_event.get("trace"),
                "providerResponseId": final_event.get("responseId", ""),
                "usage": final_event.get("usage"),
                "runtimeOptions": normalized_options,
            })
        yield {"type": "final", "payload": payload}

    return event_stream()


def get_intelligent_prediction_chat(student_id, question, chat_history=None, experiment_key="default", runtime_options=None):
    from .prediction_cohort import is_cohort_question, build_cohort_chat
    if is_cohort_question(question, chat_history):
        return build_cohort_chat(str(question).strip(), chat_history)
    context = get_intelligent_prediction_context(student_id)
    if context is None:
        return None

    cleaned_question = str(question or "").strip()
    if not cleaned_question:
        return None

    history = normalize_prediction_chat_history(chat_history)
    experiment = resolve_prediction_chat_experiment(experiment_key)
    runtime_options = normalize_prediction_runtime_options(runtime_options)
    retrieved_knowledge = rag.retrieve_prediction_knowledge(cleaned_question, context)
    fallback_answer = build_prediction_chat_answer(context, cleaned_question, retrieved_knowledge)
    policy_question = is_prediction_policy_question(cleaned_question)
    prompt_strategy = resolve_prediction_chat_prompt_strategy(
        question=cleaned_question,
        retrieved_knowledge=retrieved_knowledge,
        experiment=experiment,
    )
    prompt_package = build_prediction_chat_prompt_package(
        context=context,
        question=cleaned_question,
        chat_history=history,
        prompt_strategy=prompt_strategy,
        retrieved_knowledge=retrieved_knowledge,
    )
    llm_result = {
        "used": False,
        "reason": "policy_question_without_grounding" if policy_question and not retrieved_knowledge else "",
        "model": experiment["model"],
    }
    answer = fallback_answer
    generation_mode = "rule_based_rag_policy" if policy_question else experiment["generationMode"]
    model_name = experiment["model"]
    should_attempt_llm = (not policy_question) or bool(retrieved_knowledge)
    agent_trace = None

    # 优先走 Agent 循环：检索词由模型自己决定，可以「查得不够再换词查」。
    # 失败时不直接报错，而是继续走下面的单次 pipeline，再不行回落规则兜底。
    if prediction_agent.agent_enabled(runtime_options):
        agent_result = prediction_agent.run_prediction_chat_agent(
            context=context,
            question=cleaned_question,
            chat_history=history,
            runtime_options=runtime_options,
        )
        agent_trace = agent_result.get("trace")
        if agent_result.get("used"):
            answer = llm.normalize_prediction_chat_answer(
                agent_result.get("answer"), fallback_answer
            )
            # 模型没给引用但本轮确实检索到了原文时，用检索轨迹补齐，避免结论无出处
            if not answer.get("citations") and agent_result.get("citationsPool"):
                answer["citations"] = llm.normalize_citations(
                    agent_result["citationsPool"]
                )
            return attach_prediction_debug_payload({
                "studentId": context["student"]["studentId"],
                "question": cleaned_question,
                "answer": answer,
                "capabilities": prediction_ai_capabilities(),
            }, trace={
                    "promptVersion": "prediction_chat_agent_v1",
                    "promptRoute": "agent_tool_loop",
                    "retrievalStrategy": "agent_tool_driven_rag",
                    "retrievedCount": len(agent_result.get("citationsPool") or []),
                    "policyQuestion": policy_question,
                    "model": agent_result.get("model") or model_name,
                    "generationMode": "agent_tool_loop",
                    "experimentKey": experiment_key if experiment_key in PREDICTION_CHAT_EXPERIMENTS else "default",
                    "llmUsed": True,
                    "llmReason": "",
                    "agent": agent_trace,
                    "providerResponseId": agent_result.get("responseId", ""),
                    "usage": agent_result.get("usage"),
                    "runtimeOptions": runtime_options,
                }, prompt_package=prompt_package)
        logger.warning(
            "Prediction agent unavailable (%s), falling back to single-shot pipeline",
            agent_result.get("reason", ""),
        )

    if should_attempt_llm:
        llm_result = llm.invoke_prediction_chat_completion(prompt_package, runtime_options=runtime_options)
        answer = llm.normalize_prediction_chat_answer(llm_result.get("answer"), fallback_answer)
        if llm_result.get("used"):
            generation_mode = llm_result.get("apiStyle", "responses")
            model_name = llm_result.get("model") or model_name
        elif llm_result.get("reason") not in {"", "llm_disabled", "prompt_missing"}:
            generation_mode = "fallback_after_llm_error"
            model_name = llm_result.get("model") or model_name

    return attach_prediction_debug_payload({
        "studentId": context["student"]["studentId"],
        "question": cleaned_question,
        "answer": answer,
        "capabilities": prediction_ai_capabilities(),
    }, trace={
            "promptVersion": prompt_strategy["promptVersion"],
            "promptRoute": prompt_strategy["routeKey"],
            "promptTemplates": {
                "system": prompt_strategy["systemTemplate"],
                "user": prompt_strategy["userTemplate"],
            },
            "retrievalStrategy": prompt_strategy["retrievalStrategy"],
            "retrievedCount": len(retrieved_knowledge),
            "policyQuestion": policy_question,
            "model": model_name,
            "generationMode": generation_mode,
            "experimentKey": experiment_key if experiment_key in PREDICTION_CHAT_EXPERIMENTS else "default",
            "llmUsed": llm_result.get("used", False),
            "llmReason": llm_result.get("reason", ""),
            "provider": llm_result.get("provider", ""),
            "providerResponseId": llm_result.get("responseId", ""),
            "usage": llm_result.get("usage"),
            "runtimeOptions": runtime_options,
        }, prompt_package=prompt_package)


def serialize_prediction_student(snapshot):
    student = snapshot.student
    return {
        "studentId": student.student_id,
        "name": student.name,
        "grade": student.grade,
        "major": student.major,
        "degreeType": degree_type_display(student.degree_type),
        "college": prediction_student_scope_college(student),
        "advisorName": student.advisor_name,
        "currentStatus": student_status_display(student.current_status),
    }


def serialize_prediction_current_snapshot(snapshot):
    return {
        "courseAverage": to_float(snapshot.course_average),
        "creditCompletionRate": to_float(snapshot.credit_completion_rate),
        "attendanceRate": to_float(snapshot.attendance_rate),
        "researchTaskCompletionRate": to_float(snapshot.research_task_completion_rate),
        "researchOutputCount": snapshot.research_output_count,
        "projectParticipationCount": snapshot.project_participation_count,
        "activityHours": snapshot.activity_hours,
        "activityCount": snapshot.activity_count,
        "practiceHours": snapshot.practice_hours,
        "practiceReportCount": snapshot.practice_report_count,
        "advisorEvaluationScore": to_float(snapshot.advisor_evaluation_score),
        "advisorMeetingCount60d": snapshot.advisor_meeting_count_60d,
        "advisorAvgResponseDays": snapshot.advisor_avg_response_days,
        "missedCheckins": snapshot.missed_checkins,
        "wellbeingScore": to_float(snapshot.wellbeing_score),
        "trainingPlanCompletionRate": to_float(snapshot.training_plan_completion_rate),
        "graduationProgressRate": to_float(snapshot.graduation_progress_rate),
        "overdueTasksCount": snapshot.overdue_tasks_count,
    }


def serialize_prediction_monthly_metrics(monthly_rows):
    return {
        "months": [item.month for item in monthly_rows],
        "courseAverage": [to_float(item.course_average) for item in monthly_rows],
        "creditCompletionRate": [to_float(item.credit_completion_rate) for item in monthly_rows],
        "attendanceRate": [to_float(item.attendance_rate) for item in monthly_rows],
        "researchTaskCompletionRate": [to_float(item.research_task_completion_rate) for item in monthly_rows],
        "activityHours": [item.activity_hours for item in monthly_rows],
        "practiceHours": [item.practice_hours for item in monthly_rows],
        "advisorMeetingCount": [item.advisor_meeting_count for item in monthly_rows],
        "advisorEvaluationScore": [to_float(item.advisor_evaluation_score) for item in monthly_rows],
        "wellbeingScore": [to_float(item.wellbeing_score) for item in monthly_rows],
    }


class PredictionMonthlyMetricCollection:
    def __init__(self, rows):
        self._rows = list(rows)

    def all(self):
        return list(self._rows)

    def count(self):
        return len(self._rows)


def build_virtual_prediction_snapshot(student):
    current_snapshot = build_virtual_prediction_current_snapshot(student)
    monthly_rows = build_virtual_prediction_monthly_rows(student, current_snapshot)
    captured_at = timezone.now()
    return SimpleNamespace(
        student=student,
        sample_range="近9个月",
        risk_level=build_virtual_prediction_risk_level(current_snapshot),
        risk_type="",
        risk_field="",
        suggestion="",
        course_average=current_snapshot["courseAverage"],
        credit_completion_rate=current_snapshot["creditCompletionRate"],
        attendance_rate=current_snapshot["attendanceRate"],
        research_task_completion_rate=current_snapshot["researchTaskCompletionRate"],
        research_output_count=current_snapshot["researchOutputCount"],
        project_participation_count=current_snapshot["projectParticipationCount"],
        activity_hours=current_snapshot["activityHours"],
        activity_count=current_snapshot["activityCount"],
        practice_hours=current_snapshot["practiceHours"],
        practice_report_count=current_snapshot["practiceReportCount"],
        advisor_evaluation_score=current_snapshot["advisorEvaluationScore"],
        advisor_meeting_count_60d=current_snapshot["advisorMeetingCount60d"],
        advisor_avg_response_days=current_snapshot["advisorAvgResponseDays"],
        missed_checkins=current_snapshot["missedCheckins"],
        wellbeing_score=current_snapshot["wellbeingScore"],
        training_plan_completion_rate=current_snapshot["trainingPlanCompletionRate"],
        graduation_progress_rate=current_snapshot["graduationProgressRate"],
        overdue_tasks_count=current_snapshot["overdueTasksCount"],
        captured_at=captured_at,
        updated_at=getattr(student, "updated_at", captured_at),
        monthly_metrics=PredictionMonthlyMetricCollection(monthly_rows),
        is_virtual=True,
    )


def build_virtual_prediction_current_snapshot(student):
    current_year = timezone.localdate().year
    grade_text = extract_year_label(student.grade)
    try:
        enrollment_year = int(grade_text)
    except (TypeError, ValueError):
        enrollment_year = current_year
    study_stage = max(0, min(4, current_year - enrollment_year))
    seed = prediction_student_seed(student)
    degree_bonus = 6 if student.degree_type == DegreeType.DOCTORAL else 0
    professional_offset = -2 if student.degree_type == DegreeType.PROFESSIONAL_MASTER else 0
    major_bias = (sum(ord(ch) for ch in str(student.major or "")) % 7) - 3

    return {
        "courseAverage": round(prediction_clamp(74 + degree_bonus + professional_offset + major_bias + (seed % 9) + (study_stage * 2), 60, 98), 1),
        "creditCompletionRate": round(prediction_clamp(56 + (study_stage * 9) + (seed % 18), 35, 100), 1),
        "attendanceRate": round(prediction_clamp(86 + (seed % 11), 70, 100), 1),
        "researchTaskCompletionRate": round(prediction_clamp(48 + degree_bonus + (study_stage * 6) + ((seed // 3) % 20), 25, 100), 1),
        "researchOutputCount": max(0, min(4, (seed % 3) + (1 if student.degree_type == DegreeType.DOCTORAL else 0))),
        "projectParticipationCount": max(1, min(4, 1 + ((seed // 5) % 3))),
        "activityHours": max(4, min(28, 8 + (seed % 10))),
        "activityCount": max(1, min(6, 1 + ((seed // 7) % 4))),
        "practiceHours": max(2, min(24, 4 + (study_stage * 2) + (seed % 6))),
        "practiceReportCount": max(1, min(4, 1 + (study_stage // 2))),
        "advisorEvaluationScore": round(prediction_clamp(72 + degree_bonus + ((seed // 11) % 14), 60, 98), 1),
        "advisorMeetingCount60d": max(1, min(5, 1 + (seed % 4))),
        "advisorAvgResponseDays": max(2, min(12, 3 + ((seed // 13) % 8))),
        "missedCheckins": max(0, min(5, (seed // 17) % 5)),
        "wellbeingScore": round(prediction_clamp(78 + ((seed // 19) % 13), 65, 98), 1),
        "trainingPlanCompletionRate": round(prediction_clamp(52 + (study_stage * 10) + (seed % 18), 30, 100), 1),
        "graduationProgressRate": round(prediction_clamp(40 + (study_stage * 12) + (seed % 16) + degree_bonus, 20, 100), 1),
        "overdueTasksCount": max(0, min(6, 5 - study_stage + (seed % 2))),
    }


def build_virtual_prediction_monthly_rows(student, current_snapshot, count=9):
    seed = prediction_student_seed(student)
    months = prediction_recent_month_labels(count)
    course_series = prediction_interpolate_series(current_snapshot["courseAverage"], count, 8 + (seed % 4), seed)
    credit_series = prediction_interpolate_series(current_snapshot["creditCompletionRate"], count, 18 + (seed % 6), seed + 3)
    attendance_series = prediction_interpolate_series(current_snapshot["attendanceRate"], count, 6 + (seed % 3), seed + 5)
    research_series = prediction_interpolate_series(current_snapshot["researchTaskCompletionRate"], count, 16 + (seed % 5), seed + 7)
    activity_series = prediction_interpolate_series(current_snapshot["activityHours"], count, 5, seed + 11, minimum=0, maximum=40, integer=True)
    practice_series = prediction_interpolate_series(current_snapshot["practiceHours"], count, 4, seed + 13, minimum=0, maximum=30, integer=True)
    meeting_series = prediction_interpolate_series(current_snapshot["advisorMeetingCount60d"], count, 2, seed + 17, minimum=0, maximum=6, integer=True)
    evaluation_series = prediction_interpolate_series(current_snapshot["advisorEvaluationScore"], count, 7, seed + 19)
    wellbeing_series = prediction_interpolate_series(current_snapshot["wellbeingScore"], count, 6, seed + 23)

    return [
        SimpleNamespace(
            month=month,
            course_average=course_series[index],
            credit_completion_rate=credit_series[index],
            attendance_rate=attendance_series[index],
            research_task_completion_rate=research_series[index],
            activity_hours=activity_series[index],
            practice_hours=practice_series[index],
            advisor_meeting_count=meeting_series[index],
            advisor_evaluation_score=evaluation_series[index],
            wellbeing_score=wellbeing_series[index],
        )
        for index, month in enumerate(months)
    ]


def build_virtual_prediction_risk_level(current_snapshot):
    composite = (
        (100 - float(current_snapshot.get("creditCompletionRate") or 0)) * 0.25
        + (100 - float(current_snapshot.get("courseAverage") or 0)) * 0.15
        + (100 - float(current_snapshot.get("researchTaskCompletionRate") or 0)) * 0.16
        + (100 - float(current_snapshot.get("trainingPlanCompletionRate") or 0)) * 0.18
        + float(current_snapshot.get("advisorAvgResponseDays") or 0) * 2.2
        + float(current_snapshot.get("missedCheckins") or 0) * 4
        + (100 - float(current_snapshot.get("wellbeingScore") or 0)) * 0.08
    )
    if composite >= 32:
        return "high"
    if composite >= 24:
        return "alert"
    if composite >= 15:
        return "medium"
    return "low"


def prediction_recent_month_labels(count=9):
    today = timezone.localdate()
    total_month = (today.year * 12) + today.month - 1
    labels = []
    for offset in range(count):
        value = total_month - (count - 1 - offset)
        year = value // 12
        month = (value % 12) + 1
        labels.append(f"{year:04d}-{month:02d}")
    return labels


def prediction_interpolate_series(target, count, spread, seed, minimum=0, maximum=100, integer=False):
    target_value = float(target or 0)
    start_value = max(minimum, target_value - spread)
    if count <= 1:
        value = max(minimum, min(maximum, target_value))
        return [int(round(value)) if integer else round(value, 1)]

    series = []
    for index in range(count):
        progress = index / (count - 1)
        base = start_value + ((target_value - start_value) * progress)
        jitter = (((seed + index) % 3) - 1) * (1 if integer else 0.6)
        value = target_value if index == count - 1 else base + jitter
        value = max(minimum, min(maximum, value))
        series.append(int(round(value)) if integer else round(value, 1))
    return series


def prediction_student_seed(student):
    text = f"{student.student_id}-{student.name}-{student.major}-{student.grade}"
    return sum(ord(char) for char in text)


def latest_prediction_payload_datetime(snapshots):
    timestamps = [getattr(item, "updated_at", None) for item in snapshots] + [getattr(item, "captured_at", None) for item in snapshots]
    timestamps = [item for item in timestamps if item]
    if timestamps:
        latest = max(timestamps)
        if isinstance(latest, datetime):
            return format_datetime(latest)
    return latest_model_datetime(PredictionSnapshot)


def prediction_clamp(value, min_value=0, max_value=100):
    return max(min_value, min(max_value, float(value or 0)))


def prediction_resolve_radar_indicators(indicators=None):
    return list(DEFAULT_PREDICTION_RADAR_INDICATORS)


def prediction_score_value(snapshot_like, key):
    value = snapshot_like.get(key) if snapshot_like else None
    if value in (None, ""):
        return None
    return float(value)


def prediction_scale_score(snapshot_like, key, maximum):
    value = prediction_score_value(snapshot_like, key)
    if value is None or maximum <= 0:
        return None
    return prediction_clamp(value * 100 / maximum)


def prediction_reverse_scale_score(snapshot_like, key, maximum):
    value = prediction_score_value(snapshot_like, key)
    if value is None or maximum <= 0:
        return None
    return prediction_clamp(100 - (value * 100 / maximum))


def prediction_weighted_score(parts):
    total_weight = 0
    weighted_sum = 0
    for weight, score in parts:
        if score is None:
            continue
        total_weight += weight
        weighted_sum += weight * prediction_clamp(score)
    if total_weight <= 0:
        return 0
    return round(prediction_clamp(weighted_sum / total_weight), 1)


def prediction_compute_academic_score(snapshot_like):
    return prediction_weighted_score([
        (0.40, prediction_score_value(snapshot_like, "courseAverage")),
        (0.30, prediction_score_value(snapshot_like, "creditCompletionRate")),
        (0.15, prediction_score_value(snapshot_like, "trainingPlanCompletionRate")),
        (0.15, prediction_score_value(snapshot_like, "graduationProgressRate")),
    ])


def prediction_compute_research_score(snapshot_like):
    return prediction_weighted_score([
        (0.40, prediction_score_value(snapshot_like, "researchTaskCompletionRate")),
        (0.25, prediction_scale_score(snapshot_like, "researchOutputCount", 4)),
        (0.20, prediction_scale_score(snapshot_like, "projectParticipationCount", 4)),
        (0.15, prediction_score_value(snapshot_like, "graduationProgressRate")),
    ])


def prediction_compute_self_management_score(snapshot_like):
    return prediction_weighted_score([
        (0.40, prediction_score_value(snapshot_like, "attendanceRate")),
        (0.30, prediction_reverse_scale_score(snapshot_like, "missedCheckins", 5)),
        (0.20, prediction_reverse_scale_score(snapshot_like, "overdueTasksCount", 6)),
        (0.10, prediction_score_value(snapshot_like, "creditCompletionRate")),
    ])


def prediction_compute_advisor_support_score(snapshot_like):
    return prediction_weighted_score([
        (0.50, prediction_score_value(snapshot_like, "advisorEvaluationScore")),
        (0.30, prediction_scale_score(snapshot_like, "advisorMeetingCount60d", 5)),
        (0.30, prediction_scale_score(snapshot_like, "advisorMeetingCount", 5)),
        (0.20, prediction_reverse_scale_score(snapshot_like, "advisorAvgResponseDays", 10)),
    ])


def prediction_compute_community_score(snapshot_like):
    return prediction_weighted_score([
        (0.35, prediction_scale_score(snapshot_like, "activityHours", 30)),
        (0.25, prediction_scale_score(snapshot_like, "activityCount", 6)),
        (0.20, prediction_scale_score(snapshot_like, "projectParticipationCount", 4)),
        (0.20, prediction_scale_score(snapshot_like, "advisorMeetingCount60d", 5)),
        (0.20, prediction_scale_score(snapshot_like, "advisorMeetingCount", 5)),
    ])


def prediction_compute_practice_service_score(snapshot_like):
    return prediction_weighted_score([
        (0.50, prediction_scale_score(snapshot_like, "practiceHours", 30)),
        (0.30, prediction_scale_score(snapshot_like, "practiceReportCount", 4)),
        (0.20, prediction_scale_score(snapshot_like, "activityCount", 6)),
    ])


def prediction_compute_wellbeing_development_score(snapshot_like):
    return prediction_weighted_score([
        (0.60, prediction_score_value(snapshot_like, "wellbeingScore")),
        (0.20, prediction_reverse_scale_score(snapshot_like, "missedCheckins", 5)),
        (0.20, prediction_reverse_scale_score(snapshot_like, "overdueTasksCount", 6)),
    ])


def prediction_compute_radar(snapshot_like):
    return [
        prediction_compute_academic_score(snapshot_like),
        prediction_compute_research_score(snapshot_like),
        prediction_compute_self_management_score(snapshot_like),
        prediction_compute_advisor_support_score(snapshot_like),
        prediction_compute_community_score(snapshot_like),
        prediction_compute_practice_service_score(snapshot_like),
        prediction_compute_wellbeing_development_score(snapshot_like),
    ]


def prediction_build_monthly_records(monthly_metrics):
    months = monthly_metrics.get("months") or []
    return [
        {
            "month": month,
            "courseAverage": float(monthly_metrics.get("courseAverage", [0])[index] or 0),
            "creditCompletionRate": float(monthly_metrics.get("creditCompletionRate", [0])[index] or 0),
            "attendanceRate": float(monthly_metrics.get("attendanceRate", [0])[index] or 0),
            "researchTaskCompletionRate": float(monthly_metrics.get("researchTaskCompletionRate", [0])[index] or 0),
            "activityHours": float(monthly_metrics.get("activityHours", [0])[index] or 0),
            "practiceHours": float(monthly_metrics.get("practiceHours", [0])[index] or 0),
            "advisorMeetingCount": float(monthly_metrics.get("advisorMeetingCount", [0])[index] or 0),
            "advisorEvaluationScore": float(monthly_metrics.get("advisorEvaluationScore", [0])[index] or 0),
            "wellbeingScore": float(monthly_metrics.get("wellbeingScore", [0])[index] or 0),
        }
        for index, month in enumerate(months)
    ]


def prediction_compute_monthly_index(record):
    radar_values = prediction_compute_radar(record)
    weighted = (
        (radar_values[0] * 0.20)
        + (radar_values[1] * 0.18)
        + (radar_values[2] * 0.16)
        + (radar_values[3] * 0.14)
        + (radar_values[4] * 0.12)
        + (radar_values[5] * 0.10)
        + (radar_values[6] * 0.10)
    )
    return round(prediction_clamp(weighted), 1)


def prediction_build_historical_forecast(actual_series):
    if not actual_series:
        return []

    start_index = max(2, len(actual_series) - 4)
    values = []
    for index, current in enumerate(actual_series):
        if index < start_index:
            values.append(None)
            continue
        base = actual_series[index - 1] if index - 1 >= 0 else current
        previous = actual_series[index - 2] if index - 2 >= 0 else base
        slope = base - previous
        values.append(round(prediction_clamp(base + (slope * 0.8)), 1))
    return values


def prediction_build_projection(actual_series, mode="trend"):
    if not actual_series:
        return [0, 0, 0, 0]

    recent = actual_series[-4:]
    current = recent[-1]
    slope = (recent[-1] - recent[0]) / (len(recent) - 1) if len(recent) > 1 else 0
    factor = 0.6 if mode == "scenario" else 1
    return [
        round(prediction_clamp(current + (slope * factor * step)), 1)
        for step in range(4)
    ]


def prediction_build_upper_projection(base_series, padding=3.5):
    return [
        round(prediction_clamp(float(value or 0) + padding + (index * 1.2)), 1)
        for index, value in enumerate(base_series)
    ]


def prediction_build_factor_breakdown(snapshot_like, radar_values):
    deficit_items = [
        {"label": "学业投入与掌握", "gap": 100 - float(radar_values[0] or 0)},
        {"label": "科研训练与创新", "gap": 100 - float(radar_values[1] or 0)},
        {"label": "自我管理与学习策略", "gap": 100 - float(radar_values[2] or 0)},
        {"label": "导师支持与学术互动", "gap": 100 - float(radar_values[3] or 0)},
        {"label": "学术共同体融入", "gap": 100 - float(radar_values[4] or 0)},
        {"label": "实践参与与公共服务", "gap": 100 - float(radar_values[5] or 0)},
        {"label": "身心健康与持续发展", "gap": 100 - float(radar_values[6] or 0)},
    ]
    deficit_items = [
        {"label": item["label"], "gap": round(prediction_clamp(item["gap"]), 1)}
        for item in deficit_items
    ]
    deficit_items.sort(key=lambda item: item["gap"], reverse=True)
    top_items = deficit_items[:5]
    total_gap = sum(item["gap"] for item in top_items) or 1
    return [
        {
            "label": item["label"],
            "gap": item["gap"],
            "weight": round(item["gap"] * 100 / total_gap, 1),
            "category": PREDICTION_FACTOR_CATEGORY_MAP.get(item["label"], "培养风险"),
        }
        for item in top_items
    ]


def prediction_build_risk_profile(factors, snapshot):
    top_factor = factors[0] if factors else {}
    second_factor = factors[1] if len(factors) > 1 else {}
    top_gap = float(top_factor.get("gap") or 0)
    average_gap = sum(float(item.get("gap") or 0) for item in factors) / len(factors) if factors else 0
    risk_score = round((top_gap * 0.55) + (average_gap * 0.45), 1)
    risk_category = top_factor.get("category") or "培养风险"
    risk_field = snapshot.risk_field or "、".join(
        [item for item in [top_factor.get("label"), second_factor.get("label")] if item]
    )
    suggestion = snapshot.suggestion or PREDICTION_RISK_SUGGESTION_MAP.get(risk_category, "纳入持续跟踪")
    return {
        "riskScore": risk_score,
        "riskCategory": risk_category,
        "riskField": risk_field,
        "suggestion": suggestion,
    }


def prediction_build_gauges(snapshot_like, risk_profile):
    return {
        "graduation": round(prediction_clamp(100 - float(snapshot_like.get("graduationProgressRate") or 0)), 1),
        "training": round(prediction_clamp(100 - float(snapshot_like.get("trainingPlanCompletionRate") or 0)), 1),
        "feedback": round(prediction_clamp(float(snapshot_like.get("advisorAvgResponseDays") or 0) * 8), 1),
        "risk": round(prediction_clamp(float(risk_profile.get("riskScore") or 0) * 2.2), 1),
    }


def prediction_build_summary(risk_profile, forecast_trend):
    trend_delta = (forecast_trend[-1] if forecast_trend else 0) - (forecast_trend[0] if forecast_trend else 0)
    risk_level = risk_profile.get("riskScore") or 0
    risk_field = risk_profile.get("riskField") or "关键风险项"
    if risk_level >= 28:
        return f"当前主要风险集中在{risk_field}，若不及时干预，未来 3 个月综合发展指数可能维持低位波动。"
    if trend_delta >= 4:
        return f"当前样本整体趋势向上，未来 3 个月仍有改善空间，但需要继续关注{risk_field}。"
    return f"当前对象处于平稳波动区间，短板主要在{risk_field}，建议通过阶段性督办提升后续走势。"


def build_prediction_peer_references(target_snapshot, all_snapshots):
    same_grade = [
        item for item in all_snapshots
        if item.student
        and item.student.grade == target_snapshot.student.grade
        and item.student.student_id != target_snapshot.student.student_id
    ]
    same_major = [
        item for item in all_snapshots
        if item.student
        and item.student.major == target_snapshot.student.major
        and item.student.student_id != target_snapshot.student.student_id
    ]
    same_grade_major = [
        item for item in all_snapshots
        if item.student
        and item.student.grade == target_snapshot.student.grade
        and item.student.major == target_snapshot.student.major
        and item.student.student_id != target_snapshot.student.student_id
    ]
    return {
        "sameGrade": prediction_build_peer_reference("same_grade", same_grade),
        "sameMajor": prediction_build_peer_reference("same_major", same_major),
        "sameGradeMajor": prediction_build_peer_reference("same_grade_major", same_grade_major),
    }


def prediction_build_peer_reference(scope, snapshots):
    monthly_index_map = defaultdict(list)
    for item in snapshots:
        monthly_payload = serialize_prediction_monthly_metrics(prediction_monthly_rows(item))
        monthly_records = prediction_build_monthly_records(monthly_payload)
        for record in monthly_records:
            monthly_index_map[record["month"]].append(prediction_compute_monthly_index(record))

    averages = prediction_average_snapshot_metrics(snapshots)
    risk_distribution = Counter(risk_level_display(item.risk_level) for item in snapshots)
    return {
        "scope": scope,
        "sampleSize": len(snapshots),
        "averageSnapshot": averages,
        "averageTrendIndex": [
            {
                "month": month,
                "value": round(float(sum(Decimal(str(value)) for value in values) / len(values)), 1),
            }
            for month, values in sorted(monthly_index_map.items())
            if values
        ],
        "riskDistribution": [
            {"label": label, "count": count}
            for label, count in sorted(risk_distribution.items())
        ],
    }


def prediction_average_snapshot_metrics(snapshots):
    if not snapshots:
        return {
            "courseAverage": 0,
            "creditCompletionRate": 0,
            "attendanceRate": 0,
            "researchTaskCompletionRate": 0,
            "advisorEvaluationScore": 0,
            "wellbeingScore": 0,
            "trainingPlanCompletionRate": 0,
            "graduationProgressRate": 0,
            "advisorAvgResponseDays": 0,
            "compositePredictionIndex": 0,
        }

    size = len(snapshots)
    return {
        "courseAverage": round(sum(to_float(item.course_average) for item in snapshots) / size, 1),
        "creditCompletionRate": round(sum(to_float(item.credit_completion_rate) for item in snapshots) / size, 1),
        "attendanceRate": round(sum(to_float(item.attendance_rate) for item in snapshots) / size, 1),
        "researchTaskCompletionRate": round(sum(to_float(item.research_task_completion_rate) for item in snapshots) / size, 1),
        "advisorEvaluationScore": round(sum(to_float(item.advisor_evaluation_score) for item in snapshots) / size, 1),
        "wellbeingScore": round(sum(to_float(item.wellbeing_score) for item in snapshots) / size, 1),
        "trainingPlanCompletionRate": round(sum(to_float(item.training_plan_completion_rate) for item in snapshots) / size, 1),
        "graduationProgressRate": round(sum(to_float(item.graduation_progress_rate) for item in snapshots) / size, 1),
        "advisorAvgResponseDays": round(sum(item.advisor_avg_response_days for item in snapshots) / size, 1),
        "compositePredictionIndex": round(sum(composite_prediction_index(item) for item in snapshots) / size, 1),
    }


def normalize_prediction_analysis_tab(tab):
    text = str(tab or "").strip().lower()
    if text in {"trend", "risk", "governance"}:
        return text
    return "trend"


def resolve_prediction_analysis_experiment(experiment_key):
    return PREDICTION_ANALYSIS_EXPERIMENTS.get(
        str(experiment_key or "").strip(),
        PREDICTION_ANALYSIS_EXPERIMENTS["default"],
    )


def resolve_prediction_chat_experiment(experiment_key):
    return PREDICTION_CHAT_EXPERIMENTS.get(
        str(experiment_key or "").strip(),
        PREDICTION_CHAT_EXPERIMENTS["default"],
    )


def load_prediction_prompt_template(filename):
    path = Path(__file__).resolve().parent / "prompts" / filename
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def resolve_prediction_chat_prompt_strategy(*, question, retrieved_knowledge, experiment):
    if is_prediction_policy_question(question):
        return {
            **experiment,
            "routeKey": "policy_grounded",
            "promptVersion": "prediction_chat_policy_v2",
            "systemTemplate": "prediction_chat_policy_system_v2.txt",
            "userTemplate": "prediction_chat_policy_user_v2.txt",
            "retrievalStrategy": "local_keyword_rag_grounded",
        }
    return {
        **experiment,
        "routeKey": "risk_general",
    }


def resolve_prediction_analysis_prompt_strategy(*, tab, retrieved_knowledge, experiment):
    if tab == "governance":
        return {
            **experiment,
            "routeKey": "governance_grounded",
            "promptVersion": "prediction_analyze_governance_v2",
            "systemTemplate": "prediction_analyze_governance_system_v2.txt",
            "userTemplate": "prediction_analyze_governance_user_v2.txt",
            "retrievalStrategy": "local_keyword_rag_governance",
        }
    return {
        **experiment,
        "routeKey": "general_analysis",
        "promptVersion": "prediction_analyze_v2",
        "retrievalStrategy": "local_keyword_rag_analysis",
    }


def summarize_retrieved_knowledge_for_prompt(retrieved_knowledge):
    if not retrieved_knowledge:
        return {
            "count": 0,
            "state": "no_direct_match",
            "titles": "none",
        }

    unique_titles = []
    for item in retrieved_knowledge[:3]:
        title = str(item.get("title") or "").strip()
        if title and title not in unique_titles:
            unique_titles.append(title)
    return {
        "count": len(retrieved_knowledge),
        "state": "matched",
        "titles": "；".join(unique_titles) if unique_titles else "matched_without_title",
    }


def summarize_retrieved_knowledge_for_prompt(retrieved_knowledge):
    if not retrieved_knowledge:
        return {
            "count": 0,
            "state": "no_direct_match",
            "titles": "none",
        }

    unique_titles = []
    for item in retrieved_knowledge[:3]:
        title = str(item.get("title") or "").strip()
        if title and title not in unique_titles:
            unique_titles.append(title)
    return {
        "count": len(retrieved_knowledge),
        "state": "matched",
        "titles": "；".join(unique_titles) if unique_titles else "matched_without_title",
    }


def build_prediction_analysis_retrieval_query(context, tab):
    prediction = context["prediction"]
    student = context["student"]
    risk_field = prediction.get("riskField") or ""
    risk_category = prediction.get("riskCategory") or ""
    major = student.get("major") or ""

    if tab == "governance":
        return f"{major} {risk_field} {risk_category} 干预 建议 办法 流程 要求 制度"
    if tab == "risk":
        return f"{major} {risk_field} {risk_category} 风险 预警 管理 要求"
    return f"{major} {risk_field} 培养 趋势 课程 科研 管理 要求"


def retrieve_prediction_analysis_knowledge(context, tab):
    query = build_prediction_analysis_retrieval_query(context, tab)
    return rag.retrieve_prediction_knowledge(query, context, top_k=3)


def format_factor_weight(factor):
    return f"{round(float(factor.get('weight') or 0), 1)}%"


def format_metric_value(value, unit="%"):
    if value is None:
        return "暂无"
    number = round(float(value), 1)
    text = str(int(number)) if float(number).is_integer() else str(number)
    return f"{text}{unit}" if unit else text


def build_prediction_analysis_sections(context, tab):
    student = context["student"]
    prediction = context["prediction"]
    derived = context["derived"]
    snapshot = context["currentSnapshot"]
    same_grade = context["peerReferences"]["sameGrade"]["averageSnapshot"]
    same_major = context["peerReferences"]["sameMajor"]["averageSnapshot"]
    factors = derived["keyFactors"]
    primary_factor = factors[0] if factors else {"label": "关键指标", "weight": 0}
    secondary_factor = factors[1] if len(factors) > 1 else {"label": "辅助指标", "weight": 0}
    current_index = derived["compositeIndexCurrent"]
    forecast_values = derived["forecastTrend"]
    trend_delta = round((forecast_values[-1] if forecast_values else 0) - (forecast_values[0] if forecast_values else 0), 1)

    if tab == "risk":
        return [
            {
                "title": "风险判断",
                "content": (
                    f"{student['name']} 当前风险等级为“{prediction['riskLevel']}”，主要风险类别为"
                    f"{prediction['riskCategory']}，风险字段集中在“{prediction['riskField'] or '关键风险项'}”。"
                ),
            },
            {
                "title": "关键证据",
                "content": (
                    f"当前课程均分 {format_metric_value(snapshot['courseAverage'])}、培养计划完成率 "
                    f"{format_metric_value(snapshot['trainingPlanCompletionRate'])}、导师平均响应时长 "
                    f"{format_metric_value(snapshot['advisorAvgResponseDays'], '天')}。影响权重最高的两个因子分别是"
                    f"{primary_factor['label']}（{format_factor_weight(primary_factor)}）和"
                    f"{secondary_factor['label']}（{format_factor_weight(secondary_factor)}）。"
                ),
            },
            {
                "title": "处置优先级",
                "content": (
                    f"建议优先执行“{prediction['suggestion']}”，先核实 {primary_factor['label']} 的具体滞后环节，"
                    f"再同步导师与学生开展阶段性复核。"
                ),
            },
        ]

    if tab == "governance":
        return [
            {
                "title": "近期动作",
                "content": (
                    f"建议本周围绕“{prediction['riskField'] or primary_factor['label']}”建立一条明确的督办链路，"
                    f"先完成问题核实，再补齐台账和反馈记录。"
                ),
            },
            {
                "title": "中期治理",
                "content": (
                    f"该学生当前综合指数为 {format_metric_value(current_index)}，与同年级平均 "
                    f"{format_metric_value(same_grade['compositePredictionIndex'])}、同专业平均 "
                    f"{format_metric_value(same_major['compositePredictionIndex'])} 对比，后续应重点跟踪"
                    f"{primary_factor['label']} 和 {secondary_factor['label']} 两个维度。"
                ),
            },
            {
                "title": "协同提醒",
                "content": (
                    "治理动作应同时覆盖导师沟通、培养节点和学生反馈三条线，避免只盯单一成绩指标，"
                    "导致风险解释与实际处置脱节。"
                ),
            },
        ]

    return [
        {
            "title": "核心总结",
            "content": (
                f"{student['name']} 当前综合发展指数为 {format_metric_value(current_index)}，"
                f"未来 3 个月预测变化 {format_metric_value(trend_delta, '分')}。"
                f"当前总体判断为“{prediction['riskLevel']}”，需要持续关注 {prediction['riskField'] or primary_factor['label']}。"
            ),
        },
        {
            "title": "主要影响面",
            "content": (
                f"拉动变化最明显的两个因子是 {primary_factor['label']}（{format_factor_weight(primary_factor)}）"
                f"和 {secondary_factor['label']}（{format_factor_weight(secondary_factor)}）。"
                f"对应当前课程均分 {format_metric_value(snapshot['courseAverage'])}、出勤率 "
                f"{format_metric_value(snapshot['attendanceRate'])}。"
            ),
        },
        {
            "title": "对比提示",
            "content": (
                f"同年级平均综合指数为 {format_metric_value(same_grade['compositePredictionIndex'])}，"
                f"同专业平均综合指数为 {format_metric_value(same_major['compositePredictionIndex'])}。"
                "后续应优先观察趋势是否继续低于同组均值。"
            ),
        },
    ]


def build_prediction_analysis_evidence(context, tab):
    student = context["student"]
    prediction = context["prediction"]
    derived = context["derived"]
    snapshot = context["currentSnapshot"]
    same_grade = context["peerReferences"]["sameGrade"]["averageSnapshot"]
    factors = derived["keyFactors"]
    evidence = [
        {
            "type": "metric",
            "source": "PredictionSnapshot",
            "content": (
                f"student={student['studentId']}, courseAverage={snapshot['courseAverage']}, "
                f"creditCompletionRate={snapshot['creditCompletionRate']}, "
                f"advisorAvgResponseDays={snapshot['advisorAvgResponseDays']}"
            ),
        },
        {
            "type": "derived",
            "source": "prediction_context_builder",
            "content": (
                f"compositeIndexCurrent={derived['compositeIndexCurrent']}, "
                f"forecastTrend={derived['forecastTrend']}, riskField={prediction['riskField']}"
            ),
        },
    ]

    if factors:
        evidence.append(
            {
                "type": "factor",
                "source": "prediction_factor_breakdown",
                "content": ", ".join(
                    f"{item['label']}({format_factor_weight(item)})"
                    for item in factors[:3]
                ),
            }
        )

    evidence.append(
        {
            "type": "peer",
            "source": "same_grade_reference",
            "content": (
                f"sameGradeSample={context['peerReferences']['sameGrade']['sampleSize']}, "
                f"sameGradeCompositeAverage={same_grade['compositePredictionIndex']}"
            ),
        }
    )

    evidence.append(
        {
            "type": "knowledge_gap",
            "source": "rag_not_connected",
            "content": "当前接口尚未接入制度知识库，暂不输出制度引用证据。",
        }
    )
    return evidence


def build_prediction_prompt_package(context, tab, experiment):
    system_prompt = load_prediction_prompt_template(experiment["systemTemplate"])
    user_prompt_template = load_prediction_prompt_template(experiment["userTemplate"])
    student = context["student"]
    prediction = context["prediction"]
    derived = context["derived"]
    factors = derived["keyFactors"]
    factor_text = "、".join(
        f"{item['label']}({format_factor_weight(item)})"
        for item in factors[:3]
    ) or "暂无关键因子"
    user_prompt = user_prompt_template.format(
        tab=tab,
        student_name=student["name"],
        risk_level=prediction["riskLevel"],
        risk_field=prediction["riskField"] or "关键风险项",
        key_factors=factor_text,
        current_index=derived["compositeIndexCurrent"],
    )
    return {
        "taskType": "prediction_analysis",
        "outputSchema": {
            "summary": "string",
            "sections": [{"title": "string", "content": "string"}],
            "evidence": [{"type": "string", "source": "string", "content": "string"}],
        },
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "structuredInput": {
            "student": context["student"],
            "prediction": context["prediction"],
            "currentSnapshot": context["currentSnapshot"],
            "derived": {
                "compositeIndexCurrent": context["derived"]["compositeIndexCurrent"],
                "forecastTrend": context["derived"]["forecastTrend"],
                "keyFactors": context["derived"]["keyFactors"][:3],
            },
            "peerReferences": context["peerReferences"],
            "retrievedKnowledge": [],
        },
    }


def build_prediction_analysis_evidence(context, tab, retrieved_knowledge=None):
    student = context["student"]
    prediction = context["prediction"]
    derived = context["derived"]
    snapshot = context["currentSnapshot"]
    same_grade = context["peerReferences"]["sameGrade"]["averageSnapshot"]
    factors = derived["keyFactors"]
    retrieved_knowledge = retrieved_knowledge or []

    evidence = [
        {
            "title": "学生当前预测快照",
            "section": "PredictionSnapshot",
            "snippet": (
                f"student={student['studentId']}, courseAverage={snapshot['courseAverage']}, "
                f"creditCompletionRate={snapshot['creditCompletionRate']}, "
                f"advisorAvgResponseDays={snapshot['advisorAvgResponseDays']}"
            ),
        },
        {
            "title": "趋势推导结果",
            "section": "prediction_context_builder",
            "snippet": (
                f"compositeIndexCurrent={derived['compositeIndexCurrent']}, "
                f"forecastTrend={derived['forecastTrend']}, riskField={prediction['riskField']}"
            ),
        },
    ]

    if factors:
        evidence.append(
            {
                "title": "关键影响因子",
                "section": "prediction_factor_breakdown",
                "snippet": ", ".join(
                    f"{item['label']}({format_factor_weight(item)})"
                    for item in factors[:3]
                ),
            }
        )

    evidence.append(
        {
            "title": "同年级群体对比",
            "section": "same_grade_reference",
            "snippet": (
                f"sameGradeSample={context['peerReferences']['sameGrade']['sampleSize']}, "
                f"sameGradeCompositeAverage={same_grade['compositePredictionIndex']}"
            ),
        }
    )

    if retrieved_knowledge:
        evidence.extend(
            {
                "title": item["title"],
                "section": item["section"],
                "snippet": clean_knowledge_snippet(item["snippet"], max_length=140),
            }
            for item in retrieved_knowledge[:2]
        )
    else:
        gap_message = (
            "本次未检索到与当前治理分析直接匹配的制度依据。"
            if tab == "governance"
            else "本次分析主要基于结构化预测数据生成，未检索到直接匹配的制度依据。"
        )
        evidence.append(
            {
                "title": "制度检索状态",
                "section": "retrieval_status",
                "snippet": gap_message,
            }
        )
    return evidence


def build_prediction_analysis_prompt_package(context, tab, prompt_strategy, retrieved_knowledge):
    system_prompt = load_prediction_prompt_template(prompt_strategy["systemTemplate"])
    user_prompt_template = load_prediction_prompt_template(prompt_strategy["userTemplate"])
    student = context["student"]
    prediction = context["prediction"]
    derived = context["derived"]
    factors = derived["keyFactors"]
    knowledge_summary = summarize_retrieved_knowledge_for_prompt(retrieved_knowledge)
    factor_text = ", ".join(
        f"{item['label']}({format_factor_weight(item)})"
        for item in factors[:3]
    ) or "no_key_factors"
    forecast_text = " -> ".join(str(value) for value in (derived.get("forecastTrend") or [])) or "no_trend_sequence"
    peer_text = (
        f"same_grade_avg={context['peerReferences']['sameGrade']['averageSnapshot'].get('compositePredictionIndex', 0)}, "
        f"same_major_avg={context['peerReferences']['sameMajor']['averageSnapshot'].get('compositePredictionIndex', 0)}"
    )
    user_prompt = user_prompt_template.format(
        tab=tab,
        student_name=student["name"],
        risk_level=prediction["riskLevel"],
        risk_field=prediction["riskField"] or "primary_risk",
        key_factors=factor_text,
        current_index=derived["compositeIndexCurrent"],
        forecast_trend=forecast_text,
        peer_compare=peer_text,
        knowledge_state=knowledge_summary["state"],
        retrieved_titles=knowledge_summary["titles"],
    )
    return {
        "taskType": "prediction_analysis",
        "promptRoute": prompt_strategy["routeKey"],
        "outputSchema": {
            "summary": "string",
            "sections": [{"title": "string", "content": "string"}],
            "evidence": [{"title": "string", "section": "string", "snippet": "string"}],
        },
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "structuredInput": {
            "student": context["student"],
            "prediction": context["prediction"],
            "currentSnapshot": context["currentSnapshot"],
            "derived": {
                "compositeIndexCurrent": context["derived"]["compositeIndexCurrent"],
                "forecastTrend": context["derived"]["forecastTrend"],
                "keyFactors": context["derived"]["keyFactors"][:3],
            },
            "peerReferences": context["peerReferences"],
            "analysisTab": tab,
            "retrievedKnowledge": retrieved_knowledge,
        },
    }


def prediction_compose_student_payload(snapshot, context):
    student = context["student"]
    prediction = context["prediction"]
    derived = context["derived"]
    same_grade_trend = context["peerReferences"]["sameGrade"].get("averageTrendIndex", [])
    factors = [
        {
            "label": item.get("label", ""),
            "value": f'{item.get("weight", 0)}%',
            "gap": item.get("gap", 0),
            "category": item.get("category", ""),
        }
        for item in (derived.get("keyFactors") or [])
    ]

    trend_actual = list(derived.get("trendActual") or [])
    trend_forecast = list(derived.get("trendForecast") or [])
    peer_trend = [item.get("value") for item in same_grade_trend]
    radar_values = list(derived.get("radarValues") or [])
    forecast_trend = list(derived.get("forecastTrend") or [])
    forecast_scenario = list(derived.get("forecastScenario") or [])
    forecast_upper_trend = list(derived.get("forecastUpperTrend") or [])
    forecast_upper_scenario = list(derived.get("forecastUpperScenario") or [])
    gauges = dict(derived.get("gauges") or {})

    # 透出数据来源：没有真实快照的学生走 build_virtual_prediction_snapshot
    # 按公式编出指标，界面上必须能和真实样本区分，否则会把推算值当成实测值。
    is_virtual = bool(getattr(snapshot, "is_virtual", False))

    return {
        "id": f"stu-{student['studentId']}",
        **student,
        "dataSource": "virtual" if is_virtual else "measured",
        "hasMeasuredSnapshot": not is_virtual,
        "type": student.get("degreeType", ""),
        "tagType": prediction.get("riskType", ""),
        "riskScore": prediction.get("riskScore", prediction_risk_score_from_gauges(gauges)),
        "riskLevel": prediction.get("riskLevel", ""),
        "riskType": prediction.get("riskType", ""),
        "riskCategory": prediction.get("riskCategory", ""),
        "riskField": prediction.get("riskField", ""),
        "suggestion": prediction.get("suggestion", ""),
        "capturedAt": prediction.get("capturedAt", ""),
        "updatedAt": prediction.get("updatedAt", ""),
        "summary": derived.get("summary", ""),
        "aiConclusion": derived.get("summary", ""),
        "period": derived.get("period", "未来 3 个月"),
        "currentSnapshot": context.get("currentSnapshot", {}),
        "monthlyMetrics": context.get("monthlyMetrics", {}),
        "monthlyRecords": list(derived.get("monthlyRecords") or []),
        "radar": radar_values,
        "radarValues": radar_values,
        "trendActual": trend_actual,
        "historicalTrend": trend_actual,
        "trendForecast": trend_forecast,
        "predictedTrend": trend_forecast,
        "peerTrend": peer_trend,
        "peerAverageTrend": peer_trend,
        "forecastTrend": forecast_trend,
        "forecastTrendValues": forecast_trend,
        "forecastScenario": forecast_scenario,
        "scenarioValues": forecast_scenario,
        "forecastUpperTrend": forecast_upper_trend,
        "trendUpperBound": forecast_upper_trend,
        "forecastUpperScenario": forecast_upper_scenario,
        "scenarioUpperBound": forecast_upper_scenario,
        "factors": factors,
        "keyFactors": factors,
        "keyFactorsText": prediction_compose_key_factors_text(factors),
        "gauges": gauges,
        "graduationWarning": gauges.get("graduation", 0),
        "trainingLag": gauges.get("training", 0),
        "feedbackDelay": gauges.get("feedback", 0),
        "riskRate": gauges.get("risk", 0),
        "historicalTrendText": prediction_format_series_text(trend_actual),
        "predictedTrendText": prediction_format_series_text(trend_forecast),
        "peerAverageTrendText": prediction_format_series_text(peer_trend),
        "radarValuesText": prediction_format_series_text(radar_values),
        "forecastTrendValuesText": prediction_format_series_text(forecast_trend),
        "scenarioValuesText": prediction_format_series_text(forecast_scenario),
        "trendUpperBoundText": prediction_format_series_text(forecast_upper_trend),
        "scenarioUpperBoundText": prediction_format_series_text(forecast_upper_scenario),
    }


def prediction_format_series_text(values):
    return "|".join(
        "null" if value is None else str(value)
        for value in (values or [])
    )


def prediction_compose_key_factors_text(factors):
    return " | ".join(
        f"{item.get('label', '')}={item.get('value', '')}"
        for item in factors
        if item.get("label")
    )


def prediction_risk_score_from_gauges(gauges):
    risk_value = float((gauges or {}).get("risk") or 0)
    return round(risk_value / 2.2, 1) if risk_value else 0


def normalize_prediction_chat_history(chat_history):
    if not isinstance(chat_history, list):
        return []

    normalized = []
    for item in chat_history[-6:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip().lower()
        if role not in {"user", "assistant"}:
            continue
        content = str(item.get("content") or item.get("text") or "").strip()
        if not content:
            continue
        normalized.append({
            "role": role,
            "content": content,
        })
    return normalized


PREDICTION_POLICY_QUESTION_KEYWORDS = [
    "优秀毕业生",
    "评优",
    "评选",
    "评审",
    "资格",
    "条件",
    "标准",
    "要求",
    "材料",
    "流程",
    "办法",
    "规定",
    "政策",
    "制度",
    "文件",
    "申报",
    "审核",
    "推荐",
]

PREDICTION_POLICY_DOMAIN_TERMS = [
    "优秀毕业生",
    "奖学金",
    "助学金",
    "学籍",
    "课程",
    "培养计划",
    "答辩",
    "论文",
    "就业",
    "出国",
    "学术之星",
    "助研",
    "助教",
    "助管",
    "三助",
]

PREDICTION_POLICY_GENERIC_TERMS = {
    "评优",
    "评选",
    "评审",
    "资格",
    "条件",
    "标准",
    "要求",
    "材料",
    "流程",
    "办法",
    "规定",
    "政策",
    "制度",
    "文件",
    "申报",
    "审核",
    "推荐",
}


PREDICTION_SCOPE_UNIVERSITY = "山东大学"
PREDICTION_SCOPE_COLLEGE = "政治学与公共管理学院"
PREDICTION_SCOPE_AUDIENCE = f"{PREDICTION_SCOPE_UNIVERSITY}{PREDICTION_SCOPE_COLLEGE}研究生"


def question_contains_any_keyword(question, keywords):
    question_text = str(question or "")
    lowered = question_text.lower()
    for keyword in keywords:
        candidate = str(keyword or "")
        if not candidate:
            continue
        if candidate in question_text or candidate.lower() in lowered:
            return True
    return False


def is_prediction_policy_question(question):
    return question_contains_any_keyword(question, PREDICTION_POLICY_QUESTION_KEYWORDS)


def extract_policy_question_terms(question):
    question_text = str(question or "")
    matched_domains = [
        term for term in PREDICTION_POLICY_DOMAIN_TERMS
        if term and term in question_text
    ]
    matched_keywords = [
        term for term in PREDICTION_POLICY_QUESTION_KEYWORDS
        if term and term in question_text
    ]
    unique_terms = []
    seen = set()
    for term in matched_domains + matched_keywords:
        if term in seen:
            continue
        seen.add(term)
        unique_terms.append(term)

    filtered_terms = []
    for term in unique_terms:
        if any(term != other and term in other for other in unique_terms):
            continue
        filtered_terms.append(term)
    return filtered_terms


def clean_knowledge_snippet(snippet, max_length=90):
    text = " ".join(str(snippet or "").split())
    if len(text) <= max_length:
        return text
    return f"{text[:max_length].rstrip()}..."


def select_relevant_policy_knowledge(question, retrieved_knowledge):
    if not retrieved_knowledge:
        return []

    question_terms = extract_policy_question_terms(question)
    strong_terms = [
        term for term in question_terms
        if term not in PREDICTION_POLICY_GENERIC_TERMS
    ]
    generic_terms = [
        term for term in question_terms
        if term in PREDICTION_POLICY_GENERIC_TERMS
    ]

    ranked = []
    for item in retrieved_knowledge:
        haystack = " ".join([
            str(item.get("title") or ""),
            str(item.get("section") or ""),
            str(item.get("snippet") or ""),
        ])
        strong_matches = [term for term in strong_terms if term in haystack]
        generic_matches = [term for term in generic_terms if term in haystack]
        if strong_terms:
            if not strong_matches:
                continue
        elif generic_terms and not generic_matches:
            continue

        rank_score = float(item.get("score") or 0)
        rank_score += len(strong_matches) * 8
        rank_score += len(generic_matches) * 2
        ranked.append((rank_score, item))

    ranked.sort(key=lambda row: row[0], reverse=True)
    return [item for _, item in ranked[:2]]


def build_prediction_chat_answer(context, question, retrieved_knowledge=None):
    student = context["student"]
    prediction = context["prediction"]
    derived = context["derived"]
    snapshot = context["currentSnapshot"]
    same_grade = context["peerReferences"]["sameGrade"]["averageSnapshot"]
    same_major = context["peerReferences"]["sameMajor"]["averageSnapshot"]
    factors = derived["keyFactors"]
    retrieved_knowledge = retrieved_knowledge or []

    primary_factor = factors[0] if factors else {"label": "关键风险项", "weight": 0}
    secondary_factor = factors[1] if len(factors) > 1 else {"label": "次级风险项", "weight": 0}
    current_index = float(derived.get("compositeIndexCurrent") or 0)
    forecast_values = derived.get("forecastTrend") or []
    forecast_end = float(forecast_values[-1] or current_index) if forecast_values else current_index
    trend_delta = round(forecast_end - current_index, 1)
    same_grade_gap = round(current_index - float(same_grade.get("compositePredictionIndex") or 0), 1)
    same_major_gap = round(current_index - float(same_major.get("compositePredictionIndex") or 0), 1)
    risk_field = prediction.get("riskField") or primary_factor["label"]
    risk_level = prediction.get("riskLevel") or "关注"
    top_knowledge = retrieved_knowledge[0] if retrieved_knowledge else None
    policy_question = is_prediction_policy_question(question)
    policy_knowledge = select_relevant_policy_knowledge(question, retrieved_knowledge) if policy_question else []

    if policy_question:
        if policy_knowledge:
            titles = "、".join(f"《{item['title']}》" for item in policy_knowledge)
            snippet_text = "；".join(
                f"{item['title']}：{clean_knowledge_snippet(item.get('snippet'))}"
                for item in policy_knowledge
            )
            direct_answer = (
                f"根据知识库检索到的 {titles}，当前这个问题应以制度文件要求为准。"
                f"已匹配到的相关内容主要包括：{snippet_text}。"
                f"如果要继续判断 {student['name']} 是否符合条件，还需要把上述要求与该生的成绩、培养进度等实际数据逐项比对。"
            )
            reasoning = [
                "该问题命中了评选、资格、条件、要求等政策类关键词，应优先依据制度知识库回答。",
                f"本次 RAG 检索到的直接相关依据为 {titles}，回答内容仅围绕已匹配到的条款片段展开。",
                "学生预测快照可以辅助判断学生当前状态，但不能替代制度文件本身的资格认定。",
            ]
            action_plan = [
                f"先回到 {titles} 的原文条款，核实评选对象、资格条件、限制情形和申报流程。",
                f"再将 {student['name']} 的课程成绩、培养进度、科研表现等信息与对应条款逐项比对。",
                "如果当前知识库只有摘要片段，建议把完整文件或最新通知补充入库后再进行正式答复。",
            ]
            citations = [
                {
                    "title": item["title"],
                    "section": item["section"],
                    "snippet": clean_knowledge_snippet(item["snippet"], max_length=140),
                }
                for item in policy_knowledge
            ]
            citations.append(
                {
                    "title": "学生当前预测快照",
                    "section": "PredictionSnapshot",
                    "snippet": (
                        f"riskLevel={risk_level}, riskField={risk_field}, "
                        f"compositeIndexCurrent={current_index}"
                    ),
                }
            )
            return {
                "directAnswer": direct_answer,
                "reasoning": reasoning,
                "actionPlan": action_plan,
                "citations": citations,
            }

        return {
            "directAnswer": (
                f"当前知识库中没有检索到与“{question}”直接对应的制度文件或条款片段，"
                "因此现在不能根据现有 RAG 知识库直接判断结论，也不应仅凭预测风险信息替代政策认定。"
            ),
            "reasoning": [
                "该问题属于评选/资格/条件类政策问题，正确答案应来自制度文件或正式通知。",
                "本次检索没有找到直接匹配的制度依据，说明当前知识库缺少对应材料，或现有片段与问题不够匹配。",
                "学生预测模块中的风险等级和趋势只能反映状态，不足以单独推出评优、评选或资格结论。",
            ],
            "actionPlan": [
                "优先补充该事项对应的评选办法、实施细则或最新通知到知识库。",
                "完成入库后重新提问，让系统基于新增文件重新检索并作答。",
                "在知识库补齐前，如需正式判断，请先人工查阅学校或学院发布的原始文件。",
            ],
            "citations": [
                {
                    "title": "制度知识库检索结果",
                    "section": "",
                    "snippet": "当前未检索到与该问题直接对应的制度文件或条款片段，暂不能据此给出政策结论。",
                },
                {
                    "title": "学生当前预测快照",
                    "section": "PredictionSnapshot",
                    "snippet": (
                        f"riskLevel={risk_level}, riskField={risk_field}, "
                        f"compositeIndexCurrent={current_index}"
                    ),
                },
            ],
        }

    if any(keyword in question for keyword in ["趋势", "后续", "未来", "预测", "trend", "future", "forecast"]):
        direct_answer = (
            f"{student['name']} 当前综合发展指数为 {current_index}，未来 3 个月预测变化为 {trend_delta}。"
            f"短期内仍需围绕 {risk_field} 做连续跟踪，避免趋势继续弱于同组均值。"
        )
    elif any(keyword in question for keyword in ["原因", "为什么", "为何", "why", "reason"]):
        direct_answer = (
            f"{student['name']} 当前被判定为“{risk_level}”，核心原因集中在 {risk_field}。"
            f"从现有结构化指标看，最需要解释的两项影响因子是 {primary_factor['label']} 和 {secondary_factor['label']}。"
        )
    elif any(keyword in question for keyword in ["怎么", "如何", "建议", "措施", "干预", "how", "suggest", "action"]):
        direct_answer = (
            f"当前应先处理 {student['name']} 在 {risk_field} 上的风险点。"
            f"建议先核实指标异常，再安排导师与学生的针对性干预，最后做阶段复盘。"
        )
    else:
        direct_answer = (
            f"当前应优先关注 {student['name']} 在 {risk_field} 上的风险。"
            f"该生目前风险等级为“{risk_level}”，适合先做指标核验，再推进具体治理动作。"
        )
    if top_knowledge:
        direct_answer += f" 可同步参照《{top_knowledge['title']}》中的相关要求。"

    reasoning = [
        (
            f"当前综合发展指数为 {current_index}，未来 3 个月预测终点为 {forecast_end}，趋势变化为 {trend_delta}。"
        ),
        (
            f"影响权重最高的因素为 {primary_factor['label']}({format_factor_weight(primary_factor)})，"
            f"其次是 {secondary_factor['label']}({format_factor_weight(secondary_factor)})。"
        ),
        (
            f"与同年级均值相比 {same_grade_gap:+}，与同专业均值相比 {same_major_gap:+}，"
            f"说明当前风险并非单一瞬时波动。"
        ),
    ]
    if top_knowledge:
        reasoning.append(f"检索到的相关依据为《{top_knowledge['title']}》，可作为当前治理动作的制度参照。")
    reasoning = reasoning[:3]

    action_plan = [
        (
            f"先核实 {primary_factor['label']} 相关明细指标，重点看课程均分、培养计划完成率、逾期任务数是否与当前风险判断一致。"
        ),
        (
            f"在 1 周内安排导师沟通，围绕 {risk_field} 明确阶段目标、补救动作和复盘节点。"
        ),
        (
            "按双周节奏复盘一次趋势指标，观察综合指数、出勤率、导师反馈时长是否出现改善。"
        ),
    ]
    if top_knowledge:
        action_plan[-1] = f"对照《{top_knowledge['title']}》核实当前处置流程和台账记录是否完整。"

    citations = [
        {
            "title": "当前预测快照",
            "section": "PredictionSnapshot",
            "snippet": (
                f"courseAverage={snapshot['courseAverage']}, "
                f"creditCompletionRate={snapshot['creditCompletionRate']}, "
                f"attendanceRate={snapshot['attendanceRate']}"
            ),
        },
        {
            "title": "预测趋势推导",
            "section": "prediction_context_builder",
            "snippet": (
                f"compositeIndexCurrent={current_index}, forecastTrend={forecast_values}, "
                f"riskField={risk_field}"
            ),
        },
        {
            "title": "同年级对比",
            "section": "same_grade_reference",
            "snippet": (
                f"sampleSize={context['peerReferences']['sameGrade']['sampleSize']}, "
                f"sameGradeCompositeAverage={same_grade.get('compositePredictionIndex', 0)}"
            ),
        },
    ]
    if retrieved_knowledge:
        citations.extend(
            {
                "title": item["title"],
                "section": item["section"],
                "snippet": item["snippet"],
            }
            for item in retrieved_knowledge[:2]
        )
    else:
        citations.append(
            {
                "title": "制度知识库状态",
                "section": "",
                "snippet": "当前回复仅基于结构化预测上下文，尚未匹配到本地制度知识来源。",
            }
        )

    return {
        "directAnswer": direct_answer,
        "reasoning": reasoning,
        "actionPlan": action_plan,
        "citations": citations,
    }


def build_prediction_chat_prompt_package(context, question, chat_history, prompt_strategy, retrieved_knowledge):
    system_prompt = load_prediction_prompt_template(prompt_strategy["systemTemplate"])
    user_prompt_template = load_prediction_prompt_template(prompt_strategy["userTemplate"])
    student = context["student"]
    prediction = context["prediction"]
    derived = context["derived"]
    factors = derived["keyFactors"]
    knowledge_summary = summarize_retrieved_knowledge_for_prompt(retrieved_knowledge)
    factor_text = ", ".join(
        f"{item['label']}({format_factor_weight(item)})"
        for item in factors[:3]
    ) or "no_key_factors"
    forecast_text = " -> ".join(str(value) for value in (derived.get("forecastTrend") or [])) or "no_trend_sequence"
    peer_text = (
        f"same_grade_avg={context['peerReferences']['sameGrade']['averageSnapshot'].get('compositePredictionIndex', 0)}, "
        f"same_major_avg={context['peerReferences']['sameMajor']['averageSnapshot'].get('compositePredictionIndex', 0)}"
    )
    history_text = "\n".join(
        f"{item['role']}: {item['content']}"
        for item in chat_history
    ) or "no_chat_history"
    user_prompt = user_prompt_template.format(
        student_name=student["name"],
        question=question,
        risk_level=prediction["riskLevel"],
        risk_field=prediction["riskField"] or "primary_risk",
        key_factors=factor_text,
        current_index=derived["compositeIndexCurrent"],
        forecast_trend=forecast_text,
        peer_compare=peer_text,
        knowledge_state=knowledge_summary["state"],
        retrieved_titles=knowledge_summary["titles"],
        chat_history=history_text,
    )
    return {
        "taskType": "prediction_chat",
        "promptRoute": prompt_strategy["routeKey"],
        "outputSchema": {
            "answer": {
                "directAnswer": "string",
                "reasoning": ["string"],
                "actionPlan": ["string"],
                "citations": [{"title": "string", "section": "string", "snippet": "string"}],
            },
        },
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "structuredInput": {
            "student": context["student"],
            "prediction": context["prediction"],
            "currentSnapshot": context["currentSnapshot"],
            "derived": {
                "compositeIndexCurrent": context["derived"]["compositeIndexCurrent"],
                "forecastTrend": context["derived"]["forecastTrend"],
                "keyFactors": context["derived"]["keyFactors"][:3],
            },
            "peerReferences": context["peerReferences"],
            "chatHistory": chat_history,
            "question": question,
            "retrievedKnowledge": retrieved_knowledge,
        },
    }


def build_feature_workspace_payload(
    *,
    title,
    subtitle,
    updated_at,
    primary_action,
    stat_cards,
    trend_chart,
    donut_chart,
    bar_chart,
    table_card,
    notice_items,
    todo_items,
):
    return {
        "title": title,
        "subtitle": subtitle,
        "updatedAt": updated_at,
        "primaryAction": primary_action,
        "statCards": stat_cards,
        "trendChart": trend_chart,
        "donutChart": donut_chart,
        "barChart": bar_chart,
        "tableCard": table_card,
        "noticeCard": {"title": "通知公告", "items": notice_items},
        "todoCard": {"title": "待办事项", "items": todo_items},
    }


def build_monthly_trend(rows, series_name, unit):
    month_counter = Counter(item.updated_at.strftime("%Y-%m") for item in rows)
    labels = sorted(month_counter.keys())
    values = [month_counter[label] for label in labels]
    target = max(values) if values else 0
    return {
        "title": f"{series_name}趋势",
        "seriesName": series_name,
        "unit": unit,
        "labels": labels,
        "values": values,
        "targetName": "峰值参考",
        "targetValues": [target] * len(labels),
    }


def build_dated_trend(rows, series_name, unit, label_getter, value_getter=None):
    bucket = Counter()
    for item in rows:
        bucket[label_getter(item)] += value_getter(item) if value_getter is not None else 1

    labels = sorted(bucket.keys())
    values = [bucket[label] for label in labels]
    target = max(values) if values else 0
    return {
        "title": f"{series_name}趋势",
        "seriesName": series_name,
        "unit": unit,
        "labels": labels,
        "values": values,
        "targetName": "峰值参考",
        "targetValues": [target] * len(labels),
    }


def module_notice_items(module_code, short_date=False, include_read=False):
    items = []
    for notice in ModuleNotice.objects.filter(module=module_code)[:5]:
        item = {
            "title": notice.title,
            "date": format_date_label(notice.notice_date, short_date=short_date),
            "url": notice.url if notice.url else ""
        }
        if include_read:
            item["read"] = notice.is_read
        items.append(item)
    return items


def latest_business_timestamp():
    values = [
        latest_model_datetime(Student),
        latest_model_datetime(ModuleNotice),
        latest_model_datetime(TrainingPlan),
        latest_model_datetime(PredictionSnapshot),
    ]
    values = [item for item in values if item]
    return max(values) if values else timezone.localtime().strftime("%Y-%m-%d %H:%M:%S")


def latest_model_date(model):
    value = model.objects.aggregate(value=Max("updated_at"))["value"]
    return value.date().isoformat() if value else ""


def latest_model_datetime(model):
    value = model.objects.aggregate(value=Max("updated_at"))["value"]
    return format_datetime(value) if value else ""


def format_datetime(value, fmt="%Y-%m-%d %H:%M:%S"):
    if not value:
        return ""
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    return value.strftime(fmt)


def format_date_label(value, short_date=False):
    if not value:
        return ""
    return value.strftime("%m-%d") if short_date else value.isoformat()


def unique_sorted(values):
    return sorted({item for item in values if item})


def extract_year_label(grade):
    text = str(grade)
    digits = "".join(char for char in text if char.isdigit())
    return digits[:4] if len(digits) >= 4 else text


def derive_gender_counts(students):
    male = sum(1 for item in students if item.gender == "男")
    female = sum(1 for item in students if item.gender == "女")
    if male or female:
        return {"male": male, "female": female}

    total = len(students)
    return {"male": round(total * 0.58), "female": total - round(total * 0.58)}


def in_progress_admission_stage_count():
    latest_cycle = AdmissionCycle.objects.order_by("-year", "-updated_at").first()
    if latest_cycle is None:
        return 0
    return latest_cycle.stages.filter(status=WorkflowStatus.IN_PROGRESS).count()


def enrollment_type_display(value):
    return {
        "master": "硕士",
        "doctoral": "博士",
        "international": "国际学生",
    }.get(value, value)


def degree_type_display(value):
    return {
        DegreeType.ACADEMIC_MASTER: "学术型硕士",
        DegreeType.PROFESSIONAL_MASTER: "专业型硕士",
        DegreeType.DOCTORAL: "博士",
    }.get(value, value)


def student_status_display(value):
    return {
        StudentStatus.ACTIVE: "正常在籍",
        StudentStatus.SUSPENDED: "休学",
        StudentStatus.WITHDRAWN: "退学",
        StudentStatus.EXTENDED: "延期毕业",
        StudentStatus.OTHER: "其他",
    }.get(value, value)


def admission_progress_status_text(status, completion_percent):
    if completion_percent >= 100 or status == WorkflowStatus.COMPLETED:
        return "已结束"
    if status == WorkflowStatus.IN_PROGRESS:
        return "进行中"
    return "未开始"


def academic_status_text(status):
    return {
        WorkflowStatus.IN_PROGRESS: "办理中",
        WorkflowStatus.COMPLETED: "已通过",
        WorkflowStatus.PENDING: "待审核",
        WorkflowStatus.REJECTED: "已退回",
        WorkflowStatus.DRAFT: "待提交",
    }.get(status, "处理中")


def academic_change_status_text(status):
    return {
        WorkflowStatus.IN_PROGRESS: "处理中",
        WorkflowStatus.COMPLETED: "已完成",
        WorkflowStatus.PENDING: "待审核",
        WorkflowStatus.REJECTED: "已退回",
        WorkflowStatus.DRAFT: "待提交",
    }.get(status, "处理中")


def training_status_text(status):
    return {
        WorkflowStatus.DRAFT: "待提交",
        WorkflowStatus.PENDING: "待审核",
        WorkflowStatus.COMPLETED: "审核通过",
        WorkflowStatus.REJECTED: "驳回修改",
        WorkflowStatus.IN_PROGRESS: "待审核",
    }.get(status, "待审核")


def generic_status_text(status):
    return {
        WorkflowStatus.DRAFT: "未开始",
        WorkflowStatus.PENDING: "待确认",
        WorkflowStatus.IN_PROGRESS: "进行中",
        WorkflowStatus.COMPLETED: "已完成",
        WorkflowStatus.REJECTED: "已退回",
    }.get(status, "进行中")


def status_type_for_workflow(status):
    return {
        WorkflowStatus.DRAFT: "info",
        WorkflowStatus.PENDING: "warning",
        WorkflowStatus.IN_PROGRESS: "info",
        WorkflowStatus.COMPLETED: "success",
        WorkflowStatus.REJECTED: "danger",
    }.get(status, "info")


def counter_items(counter, is_common=False):
    if is_common:
        return [{"name": name, "value": value} for name, value in counter]
    return [{"name": name, "value": value} for name, value in counter.items()]


def percent_items(counter):
    total = sum(counter.values()) or 1
    return [{"name": name, "value": round(value * 100 / total, 1)} for name, value in counter.items()]


def scale_five(total, count, factor):
    if not count:
        return 0
    return round(min(5, max(1, total * factor / count / 20)), 1)


def percent_of(rows, predicate):
    total = len(rows) or 1
    return round(sum(1 for item in rows if predicate(item)) * 100 / total)


def is_same_week(value):
    if not value:
        return False
    if isinstance(value, datetime):
        current = timezone.localdate()
        target = timezone.localtime(value).date() if timezone.is_aware(value) else value.date()
    else:
        current = timezone.localdate()
        target = value
    return current.isocalendar()[:2] == target.isocalendar()[:2]


def map_award_bucket(name):
    text = str(name)
    if "国家" in text:
        return "national"
    if "学业" in text:
        return "academic"
    return "social"


def sum_amount(items):
    return sum((item.amount for item in items), Decimal("0"))


def to_float(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def risk_level_display(value):
    return {
        "high": "高风险",
        "alert": "预警",
        "medium": "关注",
        "low": "低风险",
    }.get(value, "关注")


def status_type_for_risk(value):
    return {
        "high": "danger",
        "alert": "warning",
        "medium": "info",
        "low": "success",
    }.get(value, "info")


def composite_prediction_index(snapshot):
    components = [
        snapshot.course_average,
        snapshot.credit_completion_rate,
        snapshot.attendance_rate,
        snapshot.research_task_completion_rate,
        snapshot.wellbeing_score,
        snapshot.training_plan_completion_rate,
        snapshot.graduation_progress_rate,
    ]
    numeric = [float(item) for item in components]
    return sum(numeric) / len(numeric)


def risk_sort_key(row):
    priority = {"高风险": 0, "预警": 1, "关注": 2, "低风险": 3}
    return (
        priority.get(row["riskLevel"], 99),
        -float(row.get("riskScore") or 0),
        row["studentId"],
    )


SEARCH_KIND_LABELS = {
    "module": "功能入口",
    "record": "业务记录",
    "notice": "通知待办",
    "analysis": "跨模块汇总",
}


SEARCH_KIND_ACTIONS = {
    "module": "进入模块",
    "record": "查看模块",
    "notice": "前往查看",
    "analysis": "查看汇总",
}


SEARCH_KIND_PRIORITY = {
    "module": 0,
    "record": 1,
    "notice": 2,
    "analysis": 3,
}


SEARCH_MODULE_DEFINITIONS = [
    {
        "key": "home",
        "title": "首页",
        "route": "/home",
        "description": "查看学院研究生总体概况、通知和待办。",
        "keywords": ["首页", "总览", "概况", "通知", "待办", "dashboard"],
    },
    {
        "key": "admission",
        "title": "招生管理",
        "route": "/admission",
        "description": "覆盖报名、复试、拟录取和招生计划。",
        "keywords": ["招生", "报名", "复试", "录取", "拟录取", "调剂"],
    },
    {
        "key": "academic-status",
        "title": "学籍管理",
        "route": "/academic-status",
        "description": "查看学籍总览、注册状态和异动情况。",
        "keywords": ["学籍", "注册", "在籍", "异动", "休学", "复学", "退学"],
    },
    {
        "key": "academic-change",
        "title": "学籍异动管理",
        "route": "/academic-change",
        "description": "处理休学、复学、延期毕业和专业变更。",
        "keywords": ["异动", "休学", "复学", "延期毕业", "专业变更"],
    },
    {
        "key": "training",
        "title": "培养管理",
        "route": "/training",
        "description": "查看培养计划、进度和培养环节执行情况。",
        "keywords": ["培养", "培养计划", "开题", "中期", "论文进度"],
    },
    {
        "key": "training-course",
        "title": "课程与培养环节",
        "route": "/training-course",
        "description": "管理排课、课程执行和培养环节预警。",
        "keywords": ["课程", "排课", "培养环节", "课表", "成绩", "开题", "中期"],
    },
    {
        "key": "degree",
        "title": "学位管理",
        "route": "/degree",
        "description": "查看学位申请、论文评阅和授予情况。",
        "keywords": ["学位", "论文", "评阅", "授予", "毕业"],
    },
    {
        "key": "degree-defense",
        "title": "答辩管理",
        "route": "/degree-defense",
        "description": "统一处理答辩场次、专家安排和结果回收。",
        "keywords": ["答辩", "场次", "会场", "专家", "答辩安排"],
    },
    {
        "key": "scholarship",
        "title": "奖助管理",
        "route": "/scholarship",
        "description": "查看奖学金、助学金和资助覆盖情况。",
        "keywords": ["奖助", "奖学金", "助学金", "资助", "国家奖学金"],
    },
    {
        "key": "employment",
        "title": "就业管理",
        "route": "/employment",
        "description": "查看就业率、签约率和就业去向。",
        "keywords": ["就业", "签约", "招聘", "去向", "升学", "出国"],
    },
    {
        "key": "intelligent-prediction",
        "title": "智能预测",
        "route": "/intelligent-prediction",
        "description": "跟踪风险预警、发展指数和关键影响因素。",
        "keywords": ["智能预测", "预警", "风险", "高风险", "发展指数", "AI"],
    },
    {
        "key": "system",
        "title": "系统设置",
        "route": "/system",
        "description": "维护业务参数、消息模板和开放时间。",
        "keywords": ["系统", "设置", "配置", "模板", "开放时间"],
    },
    {
        "key": "personal",
        "title": "个人中心",
        "route": "/personal",
        "description": "查看个人资料、快捷入口和操作日志。",
        "keywords": ["个人中心", "资料", "个人", "日志", "快捷入口"],
    },
    {
        "key": "change-pwd",
        "title": "修改密码",
        "route": "/change-pwd",
        "description": "处理密码更新和账户安全校验。",
        "keywords": ["密码", "安全", "修改密码", "账户安全"],
    },
]


def get_cross_module_query_data(grade="", major=""):
    filters = normalize_cross_module_filters(grade=grade, major=major)
    has_query = bool(filters["grade"] or filters["major"])
    description = cross_module_description(filters)
    condition_text = cross_module_condition_text(filters)

    if not has_query:
        return {
            "mode": "empty",
            "filters": filters,
            "description": description,
            "conditionText": condition_text,
            "focusRow": None,
            "comparisonRows": [],
            "summary": empty_cross_module_summary(),
            "detailModules": [],
            "latestUpdatedAt": "",
        }

    context = build_cross_module_context()
    if filters["grade"] and filters["major"]:
        row = build_cross_module_row((filters["grade"], filters["major"]), context)
        return {
            "mode": "single_profile" if row else "empty",
            "filters": filters,
            "description": description,
            "conditionText": condition_text,
            "focusRow": row,
            "comparisonRows": [],
            "summary": empty_cross_module_summary(),
            "detailModules": build_cross_module_detail_modules(row, context),
            "latestUpdatedAt": row["updatedAt"] if row else "",
        }

    comparison_rows = build_cross_module_comparison_rows(filters, context)
    return {
        "mode": "comparison" if comparison_rows else "empty",
        "filters": filters,
        "description": description,
        "conditionText": condition_text,
        "focusRow": None,
        "comparisonRows": comparison_rows,
        "summary": summarize_cross_module_rows(comparison_rows),
        "detailModules": [],
        "latestUpdatedAt": max((row["updatedAt"] for row in comparison_rows), default=""),
    }


def get_global_search_data(keyword=""):
    text = str(keyword or "").strip()
    normalized = normalize_search_keyword(text)
    tokens = split_search_tokens(text)

    if not normalized:
        return {
            "keyword": "",
            "total": 0,
            "modules": [],
            "records": [],
            "notices": [],
            "analysis": [],
            "flatResults": [],
        }

    documents = build_global_search_documents()
    scored = []
    for item in documents:
        score = calculate_search_score(item, normalized, tokens)
        if score <= 0:
            continue
        scored.append({**item, "score": score})

    scored.sort(key=search_sort_key)

    return {
        "keyword": text,
        "total": len(scored),
        "modules": [item for item in scored if item["kind"] == "module"],
        "records": [item for item in scored if item["kind"] == "record"],
        "notices": [item for item in scored if item["kind"] == "notice"],
        "analysis": [item for item in scored if item["kind"] == "analysis"],
        "flatResults": scored,
    }


def normalize_cross_module_filters(*, grade="", major=""):
    return {
        "grade": str(grade or "").strip(),
        "major": str(major or "").strip(),
    }


def cross_module_condition_text(filters):
    if filters["grade"] and filters["major"]:
        return f'{filters["grade"]} {filters["major"]}'
    if filters["grade"]:
        return f'{filters["grade"]} 全部专业'
    if filters["major"]:
        return f'全部年级 {filters["major"]}'
    return "全部年级 全部专业"


def cross_module_description(filters):
    if filters["grade"] and filters["major"]:
        return f'当前展示 {filters["grade"]}{filters["major"]} 的跨模块画像与分模块明细'
    if filters["grade"]:
        return f'当前展示 {filters["grade"]} 内所有专业的获奖、就业、培养、学位和性别结构画像'
    if filters["major"]:
        return f'当前展示 {filters["major"]} 在不同年级之间的获奖、就业、培养、学位和性别结构对比'
    return "请选择年级或专业后查看跨模块画像结果"


def empty_cross_module_summary():
    return {
        "entityCount": 0,
        "totalStudents": 0,
        "averageAwardRate": 0,
        "averageEmploymentRate": 0,
        "averageTrainingRate": 0,
        "averageDegreeRate": 0,
        "averageMaleRatio": 0,
    }


def summarize_cross_module_rows(rows):
    if not rows:
        return empty_cross_module_summary()

    total_students = sum(int(item["totalStudents"]) for item in rows) or 1
    return {
        "entityCount": len(rows),
        "totalStudents": total_students,
        "averageAwardRate": round(sum(item["awardRate"] * item["totalStudents"] for item in rows) / total_students, 1),
        "averageEmploymentRate": round(sum(item["employmentRate"] * item["totalStudents"] for item in rows) / total_students, 1),
        "averageTrainingRate": round(sum(item["trainingCompletionRate"] * item["totalStudents"] for item in rows) / total_students, 1),
        "averageDegreeRate": round(sum(item["degreeProgressRate"] * item["totalStudents"] for item in rows) / total_students, 1),
        "averageMaleRatio": round(sum(item["maleRatio"] * item["totalStudents"] for item in rows) / total_students, 1),
    }


def build_cross_module_context():
    home_rows = list(HomeGradeMajorSummary.objects.all())
    students = list(Student.objects.all())
    awards = list(ScholarshipAward.objects.select_related("student").all())
    employment_records = list(EmploymentRecord.objects.select_related("student").all())
    training_plans = list(TrainingPlan.objects.all())
    degree_applications = list(DegreeApplication.objects.select_related("student").all())

    population_map = {}
    for row in home_rows:
        population_map[(row.grade, row.major)] = {
            "totalStudents": row.total_count,
            "maleCount": row.male_count,
            "femaleCount": row.female_count,
            "updatedAt": row.updated_at,
        }

    students_by_pair = defaultdict(list)
    for student in students:
        students_by_pair[(student.grade, student.major)].append(student)
        population = population_map.setdefault(
            (student.grade, student.major),
            {
                "totalStudents": 0,
                "maleCount": 0,
                "femaleCount": 0,
                "updatedAt": student.updated_at,
            },
        )
        if not home_rows:
            population["totalStudents"] += 1
            if student.gender == "女":
                population["femaleCount"] += 1
            else:
                population["maleCount"] += 1
        population["updatedAt"] = max(population["updatedAt"], student.updated_at)

    awards_by_pair = defaultdict(list)
    for award in awards:
        key = pair_from_award(award)
        if key:
            awards_by_pair[key].append(award)

    employment_by_pair = defaultdict(list)
    for record in employment_records:
        key = pair_from_student(record.student)
        if key:
            employment_by_pair[key].append(record)

    training_by_pair = defaultdict(list)
    for plan in training_plans:
        training_by_pair[(plan.grade, plan.major)].append(plan)

    degree_by_pair = defaultdict(list)
    for application in degree_applications:
        key = pair_from_student(application.student)
        if key:
            degree_by_pair[key].append(application)

    keys = sorted(
        set(population_map.keys())
        | set(awards_by_pair.keys())
        | set(employment_by_pair.keys())
        | set(training_by_pair.keys())
        | set(degree_by_pair.keys()),
        key=lambda item: (item[0], item[1]),
    )

    return {
        "population_map": population_map,
        "students_by_pair": students_by_pair,
        "awards_by_pair": awards_by_pair,
        "employment_by_pair": employment_by_pair,
        "training_by_pair": training_by_pair,
        "degree_by_pair": degree_by_pair,
        "keys": keys,
    }


def build_cross_module_comparison_rows(filters, context):
    rows = []
    for key in context["keys"]:
        grade, major = key
        if filters["grade"] and grade != filters["grade"]:
            continue
        if filters["major"] and major != filters["major"]:
            continue
        row = build_cross_module_row(key, context)
        if row:
            rows.append(row)

    rows.sort(key=lambda item: (-item["compositeScore"], -item["employmentRate"], item["grade"], item["major"]))
    return rows


def build_cross_module_row(key, context):
    population = context["population_map"].get(key, {})
    total_students = int(population.get("totalStudents") or 0)
    male_count = int(population.get("maleCount") or 0)
    female_count = int(population.get("femaleCount") or 0)

    if total_students <= 0:
        student_rows = context["students_by_pair"].get(key, [])
        total_students = len(student_rows)
        male_count = sum(1 for item in student_rows if item.gender != "女")
        female_count = sum(1 for item in student_rows if item.gender == "女")

    if total_students <= 0:
        return None

    award_rows = context["awards_by_pair"].get(key, [])
    employment_rows = context["employment_by_pair"].get(key, [])
    training_rows = context["training_by_pair"].get(key, [])
    degree_rows = context["degree_by_pair"].get(key, [])

    award_students = unique_entity_keys(award_rows, lambda item: entity_key(item.student, item.student_name))
    employed_students = unique_entity_keys(
        [item for item in employment_rows if item.destination_type],
        lambda item: entity_key(item.student, item.student_name),
    )
    contract_students = unique_entity_keys(
        [item for item in employment_rows if item.is_signed],
        lambda item: entity_key(item.student, item.student_name),
    )
    further_students = unique_entity_keys(
        [item for item in employment_rows if item.is_further_study],
        lambda item: entity_key(item.student, item.student_name),
    )
    flexible_students = unique_entity_keys(
        [item for item in employment_rows if "灵活" in str(item.destination_type or "")],
        lambda item: entity_key(item.student, item.student_name),
    )

    award_count = min(len(award_students), total_students)
    employed_count = min(len(employed_students), total_students)
    contract_count = min(len(contract_students), total_students)
    further_count = min(len(further_students), total_students)
    flexible_count = min(len(flexible_students), total_students)
    unemployment_count = max(total_students - employed_count, 0)

    award_rate = safe_percent(award_count, total_students)
    employment_rate = safe_percent(employed_count, total_students)
    contract_rate = safe_percent(contract_count, total_students)
    further_rate = safe_percent(further_count, total_students)
    flexible_rate = safe_percent(flexible_count, total_students)
    unemployment_rate = safe_percent(unemployment_count, total_students)

    if training_rows:
        training_completion_rate = round(
            sum(int(item.completion_percent or 0) for item in training_rows) / max(total_students, len(training_rows)),
            1,
        )
    else:
        training_completion_rate = 0

    degree_progress_rate = degree_progress_from_rows(degree_rows, total_students)
    male_ratio = safe_percent(male_count, total_students)
    female_ratio = round(100 - male_ratio, 1)
    gender_balance_score = round(100 - abs(male_ratio - 50) * 2, 1)
    composite_score = round(
        award_rate * 0.28 +
        employment_rate * 0.34 +
        training_completion_rate * 0.2 +
        degree_progress_rate * 0.18,
        1,
    )
    diagnosis_type = cross_module_diagnosis_type(composite_score)

    updated_values = [population.get("updatedAt")]
    updated_values.extend(item.updated_at for item in award_rows)
    updated_values.extend(item.updated_at for item in employment_rows)
    updated_values.extend(item.updated_at for item in training_rows)
    updated_values.extend(item.updated_at for item in degree_rows)
    updated_at = max((item for item in updated_values if item), default=None)

    return {
        "id": f"{key[0]}-{key[1]}",
        "grade": key[0],
        "major": key[1],
        "totalStudents": total_students,
        "maleCount": male_count,
        "femaleCount": female_count,
        "maleRatio": male_ratio,
        "femaleRatio": female_ratio,
        "genderRatioText": f"{male_count}:{female_count}",
        "awardCount": award_count,
        "awardRate": award_rate,
        "employedCount": employed_count,
        "employmentRate": employment_rate,
        "furtherStudyRate": further_rate,
        "flexibleEmploymentRate": flexible_rate,
        "contractEmploymentRate": contract_rate,
        "unemploymentRate": unemployment_rate,
        "trainingCompletionRate": training_completion_rate,
        "degreeProgressRate": degree_progress_rate,
        "averageSalary": None,
        "genderBalanceScore": gender_balance_score,
        "compositeScore": composite_score,
        "diagnosisLabel": cross_module_diagnosis_label(diagnosis_type),
        "diagnosisType": diagnosis_type,
        "updatedAt": format_datetime(updated_at) if updated_at else "",
    }


def build_cross_module_detail_modules(row, context):
    if not row:
        return []

    key = (row["grade"], row["major"])
    award_rows = context["awards_by_pair"].get(key, [])
    employment_rows = context["employment_by_pair"].get(key, [])
    training_rows = context["training_by_pair"].get(key, [])
    degree_rows = context["degree_by_pair"].get(key, [])

    profile_rows = [
        {"item": "总人数", "value": f'{row["totalStudents"]}人', "rate": "-", "note": "来源于学生/首页汇总数据"},
        {"item": "男生人数", "value": f'{row["maleCount"]}人', "rate": f'{row["maleRatio"]}%', "note": "男生占比"},
        {"item": "女生人数", "value": f'{row["femaleCount"]}人', "rate": f'{row["femaleRatio"]}%', "note": "女生占比"},
        {"item": "获奖率", "value": f'{row["awardRate"]}%', "rate": f'{row["awardCount"]}人', "note": "有奖助记录的学生覆盖率"},
        {"item": "就业率", "value": f'{row["employmentRate"]}%', "rate": f'{row["employedCount"]}人', "note": "已落实去向学生占比"},
        {"item": "培养完成率", "value": f'{row["trainingCompletionRate"]}%', "rate": row["diagnosisLabel"], "note": "培养计划平均完成情况"},
        {"item": "学位进度", "value": f'{row["degreeProgressRate"]}%', "rate": f'{row["compositeScore"]}分', "note": "学位流程整体推进度"},
    ]

    scholarship_group = defaultdict(list)
    for award in award_rows:
        scholarship_group[award.award_type or award.award_name or "未命名奖助"].append(award)
    scholarship_rows = []
    for award_type, items in sorted(scholarship_group.items(), key=lambda item: (-len(item[1]), item[0])):
        recipients = unique_entity_keys(items, lambda item: entity_key(item.student, item.student_name))
        scholarship_rows.append(
            {
                "item": award_type,
                "value": f"{len(recipients)}人",
                "rate": f"{safe_percent(len(recipients), row['totalStudents'])}%",
                "note": f"金额 {format_decimal_amount(sum_amount(items))}",
            }
        )
    if not scholarship_rows:
        scholarship_rows.append({"item": "暂无奖助记录", "value": "-", "rate": "-", "note": "数据库中未找到该对象奖助数据"})

    destination_group = defaultdict(list)
    for record in employment_rows:
        destination_group[record.destination_type or "未填报去向"].append(record)
    employment_table_rows = []
    for destination, items in sorted(destination_group.items(), key=lambda item: (-len(item[1]), item[0])):
        unique_students = unique_entity_keys(items, lambda item: entity_key(item.student, item.student_name))
        signed_count = len(unique_entity_keys([item for item in items if item.is_signed], lambda item: entity_key(item.student, item.student_name)))
        employment_table_rows.append(
            {
                "item": destination,
                "value": f"{len(unique_students)}人",
                "rate": f"{safe_percent(len(unique_students), row['totalStudents'])}%",
                "note": f"其中签约 {signed_count} 人",
            }
        )
    if not employment_table_rows:
        employment_table_rows.append({"item": "暂无就业记录", "value": "-", "rate": "-", "note": "数据库中未找到该对象就业数据"})

    training_group = defaultdict(list)
    for plan in training_rows:
        training_group[plan.stage or "未标注阶段"].append(plan)
    training_table_rows = []
    for stage, items in sorted(training_group.items(), key=lambda item: (-len(item[1]), item[0])):
        pending = sum(1 for item in items if item.status == WorkflowStatus.PENDING)
        completed = sum(1 for item in items if item.status == WorkflowStatus.COMPLETED)
        avg_completion = round(sum(int(item.completion_percent or 0) for item in items) / len(items), 1) if items else 0
        training_table_rows.append(
            {
                "item": stage,
                "value": f"{len(items)}人",
                "rate": f"{avg_completion}%",
                "note": f"待审核 {pending} 人，已通过 {completed} 人",
            }
        )
    if not training_table_rows:
        training_table_rows.append({"item": "暂无培养记录", "value": "-", "rate": "-", "note": "数据库中未找到该对象培养数据"})

    total_degree = len(degree_rows)
    paper_pass_count = sum(1 for item in degree_rows if "通过" in str(item.paper_review_result or ""))
    defense_pass_count = sum(1 for item in degree_rows if "通过" in str(item.defense_result or ""))
    awarded_count = sum(1 for item in degree_rows if item.award_status == WorkflowStatus.COMPLETED or item.awarded_at)
    degree_table_rows = [
        {
            "item": "学位申请记录",
            "value": f"{total_degree}条",
            "rate": f"{safe_percent(total_degree, row['totalStudents'])}%",
            "note": "当前对象学位申请记录数",
        },
        {
            "item": "论文评阅通过",
            "value": f"{paper_pass_count}条",
            "rate": f"{safe_percent(paper_pass_count, row['totalStudents'])}%",
            "note": "评阅结果为通过的记录数",
        },
        {
            "item": "答辩通过",
            "value": f"{defense_pass_count}条",
            "rate": f"{safe_percent(defense_pass_count, row['totalStudents'])}%",
            "note": "答辩结果为通过的记录数",
        },
        {
            "item": "授予完成",
            "value": f"{awarded_count}条",
            "rate": f"{safe_percent(awarded_count, row['totalStudents'])}%",
            "note": "学位授予流程已完成记录数",
        },
    ]
    if not degree_rows:
        degree_table_rows = [{"item": "暂无学位记录", "value": "-", "rate": "-", "note": "数据库中未找到该对象学位数据"}]

    return [
        {
            "key": "profile",
            "title": "基本画像",
            "description": "展示该年级该专业的规模、性别结构与综合画像结论。",
            "rows": profile_rows,
        },
        {
            "key": "scholarship",
            "title": "奖助模块",
            "description": "基于奖助记录汇总该对象的获奖覆盖和奖项结构。",
            "rows": scholarship_rows,
        },
        {
            "key": "employment",
            "title": "就业模块",
            "description": "基于就业记录汇总该对象的去向结构和落实情况。",
            "rows": employment_table_rows,
        },
        {
            "key": "training",
            "title": "培养模块",
            "description": "基于培养计划记录汇总不同培养阶段推进情况。",
            "rows": training_table_rows,
        },
        {
            "key": "degree",
            "title": "学位模块",
            "description": "基于学位申请记录展示评阅、答辩和授予进度。",
            "rows": degree_table_rows,
        },
    ]


def pair_from_student(student):
    if not student:
        return None
    if not student.grade or not student.major:
        return None
    return (student.grade, student.major)


def pair_from_award(award):
    if award.student:
        return pair_from_student(award.student)
    if award.grade and award.major:
        return (award.grade, award.major)
    return None


def entity_key(student, fallback_name=""):
    if student and student.student_id:
        return student.student_id
    return str(fallback_name or "").strip()


def unique_entity_keys(rows, key_builder):
    return {key_builder(item) for item in rows if key_builder(item)}


def safe_percent(value, total):
    if not total:
        return 0
    return round(value * 100 / total, 1)


def degree_progress_from_rows(rows, total_students):
    if not rows or not total_students:
        return 0

    status_score = {
        WorkflowStatus.DRAFT: 25,
        WorkflowStatus.PENDING: 60,
        WorkflowStatus.IN_PROGRESS: 72,
        WorkflowStatus.REJECTED: 35,
        WorkflowStatus.COMPLETED: 100,
    }
    student_scores = {}
    for item in rows:
        key = entity_key(item.student, f"{item.student_name}-{item.application_year}-{item.discipline}")
        score = status_score.get(item.award_status, 0)
        if "通过" in str(item.paper_review_result or ""):
            score = max(score, 78)
        if "通过" in str(item.defense_result or ""):
            score = max(score, 88)
        if item.awarded_at:
            score = 100
        student_scores[key] = max(score, student_scores.get(key, 0))

    return round(sum(student_scores.values()) / total_students, 1)


def cross_module_diagnosis_type(score):
    if score >= 82:
        return "success"
    if score >= 72:
        return "info"
    if score >= 62:
        return "warning"
    return "danger"


def cross_module_diagnosis_label(kind):
    return {
        "success": "优势明显",
        "info": "结构稳定",
        "warning": "需要补短",
        "danger": "重点跟进",
    }.get(kind, "结构稳定")


def format_decimal_amount(value):
    amount = to_float(value) if value is not None else 0
    if amount >= 10000:
        return f"{round(amount / 10000, 2)}万元"
    if float(amount).is_integer():
        return f"{int(amount)}元"
    return f"{round(amount, 2)}元"


def build_global_search_documents():
    documents = []

    for module in SEARCH_MODULE_DEFINITIONS:
        documents.append(
            create_search_doc(
                {
                    "kind": "module",
                    "moduleName": module["title"],
                    "title": module["title"],
                    "summary": module["description"],
                    "meta": "模块直达",
                    "route": module["route"],
                    "tags": module["keywords"][:3],
                    "searchKeywords": [module["title"], *module["keywords"], module["description"]],
                }
            )
        )

    for notice in ModuleNotice.objects.select_related().order_by("-notice_date", "-id")[:80]:
        module_name = dict(ModuleCode.choices).get(notice.module, notice.module)
        route = search_route_for_module_code(notice.module)
        documents.append(
            create_search_doc(
                {
                    "kind": "notice",
                    "moduleName": module_name,
                    "title": notice.title,
                    "summary": f"{module_name} · 通知",
                    "meta": format_date_label(notice.notice_date),
                    "route": route,
                    "tags": ["通知"],
                    "searchKeywords": [notice.title, module_name, notice.content, format_date_label(notice.notice_date)],
                }
            )
        )

    for item in AcademicStatusEvent.objects.select_related("student").order_by("-occurred_on", "-id")[:120]:
        documents.append(
            create_search_doc(
                {
                    "kind": "record",
                    "moduleName": "学籍管理",
                    "title": f"{item.student_name} {item.external_id}",
                    "summary": f"{item.change_type} · {academic_status_text(item.status)} · 经办人 {item.handler_name}",
                    "meta": f"{item.reason} · {item.occurred_on.isoformat()}",
                    "route": "/academic-status",
                    "statusText": academic_status_text(item.status),
                    "statusType": status_type_for_workflow(item.status),
                    "tags": [item.change_type, academic_status_text(item.status)],
                    "searchKeywords": [item.student_name, item.external_id, item.change_type, item.handler_name, item.reason],
                }
            )
        )

    for item in AcademicChangeRequest.objects.select_related("student").order_by("-submitted_at", "-id")[:120]:
        documents.append(
            create_search_doc(
                {
                    "kind": "record",
                    "moduleName": "学籍异动管理",
                    "title": f"{item.student_name} {item.student.student_id if item.student else ''}".strip(),
                    "summary": f"{item.change_type} · {item.current_step} · {academic_change_status_text(item.status)}",
                    "meta": f"提交时间 {format_datetime(item.submitted_at, '%Y-%m-%d %H:%M')}",
                    "route": "/academic-change",
                    "statusText": academic_change_status_text(item.status),
                    "statusType": status_type_for_workflow(item.status),
                    "tags": [item.change_type, academic_change_status_text(item.status)],
                    "searchKeywords": [item.student_name, item.change_type, item.current_step, item.remark],
                }
            )
        )

    for item in TrainingPlan.objects.order_by("-updated_at", "-id")[:120]:
        documents.append(
            create_search_doc(
                {
                    "kind": "record",
                    "moduleName": "培养管理",
                    "title": f"{item.student_name} {item.student.student_id if item.student else ''}".strip(),
                    "summary": f"{item.grade} · {item.major} · {item.stage} · {training_status_text(item.status)}",
                    "meta": f"导师 {item.advisor_name} · 完成度 {item.completion_percent}% · {item.business_updated_at or format_datetime(item.updated_at, '%Y-%m-%d')}",
                    "route": "/training",
                    "statusText": training_status_text(item.status),
                    "statusType": status_type_for_workflow(item.status),
                    "tags": [item.grade, item.major, item.stage],
                    "searchKeywords": [item.student_name, item.grade, item.major, item.stage, item.advisor_name],
                }
            )
        )

    for item in CourseOffering.objects.order_by("-updated_at", "-id")[:120]:
        documents.append(
            create_search_doc(
                {
                    "kind": "record",
                    "moduleName": "课程与培养环节",
                    "title": item.course_name,
                    "summary": f"{item.major} · {item.teacher_name} · {item.schedule_text}",
                    "meta": f"状态 {generic_status_text(item.status)}",
                    "route": "/training-course",
                    "statusText": generic_status_text(item.status),
                    "statusType": status_type_for_workflow(item.status),
                    "tags": [item.major, item.teacher_name],
                    "searchKeywords": [item.course_name, item.major, item.teacher_name, item.schedule_text, item.term],
                }
            )
        )

    for item in DegreeApplication.objects.select_related("student").order_by("-application_year", "-updated_at")[:120]:
        student_label = item.student.student_id if item.student else item.student_name
        documents.append(
            create_search_doc(
                {
                    "kind": "record",
                    "moduleName": "学位管理",
                    "title": f"{student_label} {item.discipline}".strip(),
                    "summary": f"{item.application_year} · {item.application_type} · {generic_status_text(item.award_status)}",
                    "meta": f"评阅 {item.paper_review_result or '未录入'} · 答辩 {item.defense_result or '未录入'}",
                    "route": "/degree",
                    "statusText": generic_status_text(item.award_status),
                    "statusType": status_type_for_workflow(item.award_status),
                    "tags": [item.application_type, item.discipline],
                    "searchKeywords": [item.student_name, student_label, item.application_type, item.discipline, item.paper_review_result, item.defense_result],
                }
            )
        )

    for item in DefenseSession.objects.order_by("-scheduled_at", "-updated_at")[:120]:
        documents.append(
            create_search_doc(
                {
                    "kind": "record",
                    "moduleName": "答辩管理",
                    "title": item.session_name,
                    "summary": f"{item.room} · {format_datetime(item.scheduled_at, '%Y-%m-%d %H:%M')} · {generic_status_text(item.status)}",
                    "meta": f"主席 {item.chair_name} · 学生 {item.student_count} 人",
                    "route": "/degree-defense",
                    "statusText": generic_status_text(item.status),
                    "statusType": status_type_for_workflow(item.status),
                    "tags": [item.room, item.chair_name],
                    "searchKeywords": [item.session_name, item.room, item.chair_name],
                }
            )
        )

    for item in ScholarshipAward.objects.select_related("student").order_by("-award_year", "-updated_at")[:120]:
        student_label = item.student.student_id if item.student else item.student_name
        documents.append(
            create_search_doc(
                {
                    "kind": "record",
                    "moduleName": "奖助管理",
                    "title": f"{item.student_name or student_label} {item.award_name}".strip(),
                    "summary": f"{item.grade} · {item.major} · {item.award_type}",
                    "meta": f"{item.award_year} · 金额 {format_decimal_amount(item.amount)}",
                    "route": "/scholarship",
                    "tags": [item.award_category, item.award_type],
                    "searchKeywords": [item.student_name, student_label, item.grade, item.major, item.award_type, item.award_name],
                }
            )
        )

    for item in EmploymentRecord.objects.select_related("student").order_by("-graduation_year", "-updated_at")[:120]:
        student_label = item.student.student_id if item.student else item.student_name
        documents.append(
            create_search_doc(
                {
                    "kind": "record",
                    "moduleName": "就业管理",
                    "title": f"{item.student_name or student_label} {item.destination_type or '未落实去向'}".strip(),
                    "summary": f"{item.graduation_year} · {item.destination_type or '未填报'} · {item.province or '地区未填'}",
                    "meta": f"{item.unit_nature or '单位性质未填'} · {item.industry or '行业未填'}",
                    "route": "/employment",
                    "statusText": generic_status_text(item.status),
                    "statusType": status_type_for_workflow(item.status),
                    "tags": [item.destination_type or '未填报', item.province or '地区未填'],
                    "searchKeywords": [item.student_name, student_label, item.destination_type, item.unit_nature, item.industry, item.province, item.employer_name],
                }
            )
        )

    for item in PredictionSnapshot.objects.select_related("student").order_by("-captured_at", "-updated_at")[:120]:
        documents.append(
            create_search_doc(
                {
                    "kind": "record",
                    "moduleName": "智能预测",
                    "title": f"{item.student.name} {item.student.student_id}",
                    "summary": f"{item.student.grade} · {item.student.major} · {risk_level_display(item.risk_level)}",
                    "meta": item.suggestion or item.risk_field or "智能预测分析记录",
                    "route": "/intelligent-prediction",
                    "statusText": risk_level_display(item.risk_level),
                    "statusType": status_type_for_risk(item.risk_level),
                    "tags": [item.student.grade, item.student.major, risk_level_display(item.risk_level)],
                    "searchKeywords": [item.student.name, item.student.student_id, item.student.grade, item.student.major, item.risk_field, item.suggestion],
                }
            )
        )

    search_todos = [
        ("首页", "/home", "培养计划待审核", TrainingPlan.objects.filter(status=WorkflowStatus.PENDING).count()),
        ("学籍异动管理", "/academic-change", "学籍异动办理中", AcademicChangeRequest.objects.filter(status=WorkflowStatus.IN_PROGRESS).count()),
        ("答辩管理", "/degree-defense", "答辩待确认", DefenseSession.objects.exclude(status=WorkflowStatus.COMPLETED).count()),
        ("智能预测", "/intelligent-prediction", "高风险预测样本", PredictionSnapshot.objects.filter(risk_level="high").count()),
        ("课程与培养环节", "/training-course", "课程待处理", CourseOffering.objects.filter(status=WorkflowStatus.PENDING).count()),
    ]
    for module_name, route, label, count in search_todos:
        documents.append(
            create_search_doc(
                {
                    "kind": "notice",
                    "moduleName": module_name,
                    "title": label,
                    "summary": f"{module_name} · 待办事项",
                    "meta": f"当前数量 {count}",
                    "route": route,
                    "tags": ["待办"],
                    "searchKeywords": [label, module_name, "待办", count],
                }
            )
        )

    context = build_cross_module_context()
    for row in build_cross_module_comparison_rows({"grade": "", "major": ""}, context):
        documents.append(
            create_search_doc(
                {
                    "kind": "analysis",
                    "moduleName": "跨模块画像",
                    "title": f'{row["grade"]} {row["major"]}',
                    "summary": f'跨模块画像 · 获奖率 {row["awardRate"]}%',
                    "meta": f'就业率 {row["employmentRate"]}% · {row["diagnosisLabel"]}',
                    "route": "/query-results",
                    "routeQuery": {"grade": row["grade"], "major": row["major"]},
                    "statusText": row["diagnosisLabel"],
                    "statusType": row["diagnosisType"],
                    "tags": [row["grade"], row["major"]],
                    "searchKeywords": [row["grade"], row["major"], row["diagnosisLabel"], row["awardRate"], row["employmentRate"]],
                }
            )
        )

    return documents


def create_search_doc(item):
    tags = unique_nonempty_strings(item.get("tags", []))
    keywords = unique_nonempty_strings(
        [
            item.get("title", ""),
            item.get("summary", ""),
            item.get("meta", ""),
            item.get("moduleName", ""),
            *(item.get("searchKeywords", []) or []),
            *tags,
        ]
    )
    return {
        **item,
        "tags": tags,
        "kindLabel": SEARCH_KIND_LABELS.get(item["kind"], "搜索结果"),
        "actionLabel": item.get("actionLabel") or SEARCH_KIND_ACTIONS.get(item["kind"], "查看"),
        "searchKeywords": keywords,
        "searchText": " ".join(normalize_search_keyword(value) for value in keywords if normalize_search_keyword(value)),
    }


def normalize_search_keyword(keyword):
    return " ".join(str(keyword or "").strip().lower().split())


def split_search_tokens(keyword):
    normalized = normalize_search_keyword(keyword)
    if not normalized:
        return []
    separators = " ,，、;；/|"
    tokens = [normalized]
    for char in separators:
        next_tokens = []
        for token in tokens:
            next_tokens.extend(token.split(char))
        tokens = next_tokens
    return [item.strip() for item in tokens if item.strip()]


def calculate_search_score(item, query, tokens):
    search_text = item.get("searchText", "")
    matched_token_count = sum(1 for token in tokens if token and token in search_text)
    minimal_matched_count = max(1, (len(tokens) * 6 + 9) // 10) if tokens else 1

    if query not in search_text and matched_token_count < minimal_matched_count:
        return 0

    score = 0
    score += score_search_field(item.get("title"), query, tokens, 16)
    score += score_search_field(item.get("summary"), query, tokens, 9)
    score += score_search_field(item.get("meta"), query, tokens, 6)
    score += score_search_field(item.get("moduleName"), query, tokens, 8)
    score += matched_token_count * 6
    if item.get("kind") == "module":
        score += 8
    if item.get("statusType") == "danger":
        score += 2
    if item.get("statusType") == "warning":
        score += 1
    return score


def score_search_field(value, query, tokens, weight):
    text = normalize_search_keyword(value)
    if not text:
        return 0

    score = 0
    if text == query:
        score += weight * 6
    elif text.startswith(query):
        score += weight * 4
    elif query in text:
        score += weight * 3

    for token in tokens:
        if not token:
            continue
        if text == token:
            score += weight * 3
        elif text.startswith(token):
            score += weight * 2
        elif token in text:
            score += weight
    return score


def search_sort_key(item):
    return (
        -item["score"],
        SEARCH_KIND_PRIORITY.get(item["kind"], 99),
        str(item.get("title", "")),
    )


def unique_nonempty_strings(values):
    seen = []
    for item in values:
        text = str(item or "").strip()
        if text and text not in seen:
            seen.append(text)
    return seen


def search_route_for_module_code(module_code):
    return {
        ModuleCode.HOME: "/home",
        ModuleCode.ADMISSION: "/admission",
        ModuleCode.ACADEMIC_STATUS: "/academic-status",
        ModuleCode.ACADEMIC_CHANGE: "/academic-change",
        ModuleCode.TRAINING: "/training",
        ModuleCode.TRAINING_COURSE: "/training-course",
        ModuleCode.DEGREE: "/degree",
        ModuleCode.DEGREE_DEFENSE: "/degree-defense",
        ModuleCode.SCHOLARSHIP: "/scholarship",
        ModuleCode.EMPLOYMENT: "/employment",
        ModuleCode.INTELLIGENT_PREDICTION: "/intelligent-prediction",
    }.get(module_code, "/home")


def build_prediction_sources():
    students = [
        student
        for student in Student.objects.filter(
            Q(college=PREDICTION_SCOPE_COLLEGE) | Q(college="") | Q(college__isnull=True)
        ).order_by("student_id")
        if prediction_student_in_scope(student)
    ]
    raw_snapshots = list(
        PredictionSnapshot.objects.select_related("student")
        .prefetch_related("monthly_metrics")
        .filter(Q(student__college=PREDICTION_SCOPE_COLLEGE) | Q(student__college="") | Q(student__college__isnull=True))
        .order_by("student__student_id", "-captured_at", "-updated_at")
    )
    latest_snapshot_by_student_id = {}
    for snapshot in raw_snapshots:
        if not prediction_snapshot_in_scope(snapshot):
            continue
        latest_snapshot_by_student_id.setdefault(snapshot.student_id, snapshot)

    return [
        latest_snapshot_by_student_id.get(student.id) or build_virtual_prediction_snapshot(student)
        for student in students
    ]
