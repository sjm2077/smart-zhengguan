"""智能预测 Agent 的工具层。

这里把已有的检索/画像/预警/横向对比能力包装成模型可调用的 function，
业务逻辑全部复用 rag.py / services.py / warning_services.py，不重写。

设计约定：
  - 每个工具都是纯读操作，不写库、不触发导出，Agent 循环可安全重试；
  - 返回值必须是可 JSON 序列化的小对象，并带 ok 字段，便于模型判断成败；
  - 返回体要控制体积（截断长文本），否则多轮循环会迅速撑爆上下文；
  - 工具内部不抛异常，失败也以 {"ok": False, "error": ...} 返回，
    让模型有机会换个关键词重试，而不是整轮对话直接失败。
"""

import logging

from django.conf import settings

from apps.graduate import rag


logger = logging.getLogger(__name__)

# 单个检索片段的最大长度，防止多轮累积把上下文吃光
MAX_SNIPPET_CHARS = 420
# 单次工具调用返回的最大条目数
MAX_ITEMS = 5


# ----------------------------------------------------------------------
# 工具 schema：交给 chat_completions 的 tools 参数
# ----------------------------------------------------------------------

SEARCH_POLICY_TOOL = {
    "type": "function",
    "function": {
        "name": "search_policy",
        "description": (
            "检索学校研究生制度文件原文（学籍管理、奖助评审、课程教学、答辩学位等）。"
            "回答任何涉及规定、条件、标准、流程、材料的问题前必须调用本工具，"
            "不要凭记忆陈述制度条款。若首次检索片段不完整，可以更换更具体的关键词再次调用。"
        ),
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "query": {
                    "type": "string",
                    "description": "检索关键词，建议使用制度术语，如『学业奖学金 评审条件』『休学 保留学籍』",
                },
                "top_k": {
                    "type": "integer",
                    "description": "返回片段数量，默认 4，最大 5",
                },
            },
            "required": ["query"],
        },
    },
}

GET_STUDENT_SNAPSHOT_TOOL = {
    "type": "function",
    "function": {
        "name": "get_student_snapshot",
        "description": (
            "获取当前学生的预测画像：风险等级、关键影响因子、综合发展指数、"
            "课程均分/出勤等当前快照与趋势预测。需要结合该生实际数据判断时调用。"
        ),
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {},
            "required": [],
        },
    },
}

COMPARE_PEERS_TOOL = {
    "type": "function",
    "function": {
        "name": "compare_peers",
        "description": (
            "获取该生与同年级/同专业/同年级同专业群体的平均指标对比，"
            "用于判断其处于什么水位、差距有多大。"
        ),
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "scope": {
                    "type": "string",
                    "enum": ["sameGrade", "sameMajor", "sameGradeMajor", "all"],
                    "description": "对比口径，默认 all 返回全部三种",
                },
            },
            "required": [],
        },
    },
}

LIST_WARNINGS_TOOL = {
    "type": "function",
    "function": {
        "name": "list_warnings",
        "description": (
            "查询该生当前命中的预警记录（规则名称、命中指标值、阈值、状态）。"
            "判断是否需要干预、或问到预警情况时调用。"
        ),
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "processing", "resolved", "all"],
                    "description": "按状态过滤，默认 all",
                },
            },
            "required": [],
        },
    },
}


PREDICTION_AGENT_TOOLS = [
    SEARCH_POLICY_TOOL,
    GET_STUDENT_SNAPSHOT_TOOL,
    COMPARE_PEERS_TOOL,
    LIST_WARNINGS_TOOL,
]


# ----------------------------------------------------------------------
# 工具实现
# ----------------------------------------------------------------------

def tool_search_policy(*, context, query, top_k=None):
    """复用既有关键词检索。与单次 pipeline 的差别是 query 由模型自己给。"""
    cleaned_query = str(query or "").strip()
    if not cleaned_query:
        return {"ok": False, "error": "query 不能为空，请给出具体检索关键词"}

    try:
        limit = int(top_k) if top_k else int(getattr(settings, "PREDICTION_KNOWLEDGE_TOP_K", 4))
    except (TypeError, ValueError):
        limit = 4
    limit = max(1, min(limit, MAX_ITEMS))

    try:
        results = rag.retrieve_prediction_knowledge(cleaned_query, context, top_k=limit)
    except Exception as exc:  # 检索失败不应中断整轮对话
        logger.warning("agent search_policy failed: %s", exc)
        return {"ok": False, "error": f"检索失败: {exc}"}

    if not results:
        return {
            "ok": True,
            "query": cleaned_query,
            "hitCount": 0,
            "results": [],
            "hint": "未检索到相关制度片段，可尝试更换关键词（如改用更正式的制度术语）或缩短关键词",
        }

    return {
        "ok": True,
        "query": cleaned_query,
        "hitCount": len(results),
        "results": [
            {
                "title": item.get("title", ""),
                "section": item.get("section", ""),
                "snippet": str(item.get("snippet", ""))[:MAX_SNIPPET_CHARS],
                "sourceType": item.get("sourceType", ""),
            }
            for item in results
        ],
    }


def tool_get_student_snapshot(*, context):
    student = context.get("student") or {}
    prediction = context.get("prediction") or {}
    derived = context.get("derived") or {}
    snapshot = context.get("currentSnapshot") or {}

    key_factors = [
        {"label": item.get("label", ""), "weight": item.get("weight", 0)}
        for item in (derived.get("keyFactors") or [])[:5]
    ]
    return {
        "ok": True,
        "student": {
            "name": student.get("name", ""),
            "grade": student.get("grade", ""),
            "major": student.get("major", ""),
            "degreeType": student.get("degreeType", ""),
            "currentStatus": student.get("currentStatus", ""),
            "advisorName": student.get("advisorName", ""),
        },
        "prediction": {
            "riskLevel": prediction.get("riskLevel", ""),
            "riskField": prediction.get("riskField", ""),
            "riskCategory": prediction.get("riskCategory", ""),
        },
        "currentSnapshot": {
            "courseAverage": snapshot.get("courseAverage"),
            "attendanceRate": snapshot.get("attendanceRate"),
            "creditCompletionRate": snapshot.get("creditCompletionRate"),
            "graduationProgressRate": snapshot.get("graduationProgressRate"),
            "trainingPlanCompletionRate": snapshot.get("trainingPlanCompletionRate"),
            "advisorEvaluationScore": snapshot.get("advisorEvaluationScore"),
            "wellbeingScore": snapshot.get("wellbeingScore"),
            "overdueTasksCount": snapshot.get("overdueTasksCount"),
        },
        "compositeIndexCurrent": derived.get("compositeIndexCurrent"),
        "forecastTrend": (derived.get("forecastTrend") or [])[:6],
        "keyFactors": key_factors,
    }


def tool_compare_peers(*, context, scope=None):
    peers = context.get("peerReferences") or {}
    derived = context.get("derived") or {}
    current_index = derived.get("compositeIndexCurrent")

    valid_scopes = ("sameGrade", "sameMajor", "sameGradeMajor")
    requested = str(scope or "all").strip() or "all"
    # 未知口径必须报错。否则 peers.get(key) 返回空字典，
    # 会给模型一组全 None 的"对比结果"，看起来像真有数据但全是空值。
    if requested != "all" and requested not in valid_scopes:
        return {
            "ok": False,
            "error": f"未知的对比口径 {requested}，可用值: all, {', '.join(valid_scopes)}",
        }
    scopes = list(valid_scopes) if requested == "all" else [requested]

    comparisons = {}
    for key in scopes:
        bucket = peers.get(key) or {}
        average = bucket.get("averageSnapshot") or {}
        peer_index = average.get("compositePredictionIndex")
        gap = None
        if isinstance(current_index, (int, float)) and isinstance(peer_index, (int, float)):
            gap = round(float(current_index) - float(peer_index), 1)
        comparisons[key] = {
            "peerCompositeIndex": peer_index,
            "gap": gap,
            "courseAverage": average.get("courseAverage"),
            "attendanceRate": average.get("attendanceRate"),
            "sampleSize": bucket.get("sampleSize") or bucket.get("count"),
        }

    if not comparisons:
        return {"ok": False, "error": f"未知的对比口径: {requested}"}

    return {
        "ok": True,
        "studentCompositeIndex": current_index,
        "comparisons": comparisons,
        "note": "gap 为该生指数减去群体均值，负值表示低于群体平均",
    }


def tool_list_warnings(*, context, status=None):
    student = context.get("student") or {}
    student_id = student.get("studentId")
    if not student_id:
        return {"ok": False, "error": "当前上下文缺少学号，无法查询预警"}

    # 延迟导入，避免模块级循环依赖
    from apps.graduate.models import WarningInstance

    try:
        queryset = (
            WarningInstance.objects.select_related("rule", "student")
            .filter(student__student_id=student_id)
            .order_by("-hit_at")
        )
        requested = str(status or "all").strip() or "all"
        if requested != "all":
            queryset = queryset.filter(status=requested)
        rows = list(queryset[:MAX_ITEMS])
    except Exception as exc:
        logger.warning("agent list_warnings failed: %s", exc)
        return {"ok": False, "error": f"预警查询失败: {exc}"}

    return {
        "ok": True,
        "hitCount": len(rows),
        "warnings": [
            {
                "ruleName": getattr(row.rule, "name", ""),
                "ruleCode": getattr(row.rule, "code", ""),
                "riskLevel": getattr(row.rule, "risk_level", ""),
                "targetModule": getattr(row.rule, "target_module", ""),
                "status": row.status,
                "indicatorValue": row.indicator_value,
                "thresholdAtHit": row.threshold_at_hit,
                "hitAt": row.hit_at.isoformat() if row.hit_at else "",
            }
            for row in rows
        ],
    }


TOOL_IMPLEMENTATIONS = {
    "search_policy": tool_search_policy,
    "get_student_snapshot": tool_get_student_snapshot,
    "compare_peers": tool_compare_peers,
    "list_warnings": tool_list_warnings,
}


def execute_tool(name, arguments, *, context):
    """按名字分发工具调用。未知工具与参数错误都以结构化错误返回。"""
    implementation = TOOL_IMPLEMENTATIONS.get(name)
    if implementation is None:
        return {
            "ok": False,
            "error": f"未知工具 {name}，可用工具: {', '.join(TOOL_IMPLEMENTATIONS)}",
        }

    kwargs = dict(arguments or {})
    try:
        return implementation(context=context, **kwargs)
    except TypeError as exc:
        return {"ok": False, "error": f"参数不合法: {exc}"}
    except Exception as exc:
        logger.warning("agent tool %s crashed: %s", name, exc)
        return {"ok": False, "error": f"工具执行失败: {exc}"}
