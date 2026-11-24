"""智能分析与预警：只读问答、正式规则预览、人工核查流程。

所有端点需 JWT 登录并具备 admin / academic 角色；DeepSeek 只能接收聚合数据。
API Key 通过服务器环境变量 DEEPSEEK_API_KEY 注入，不接受浏览器上传的密钥。
"""
import json
import logging
import os
import re
from urllib.request import Request as URLRequest, urlopen
from urllib.error import HTTPError, URLError
from django.db import transaction
from django.core.cache import cache
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .permissions import get_teaching_role
from .ai_models import AIWarningCase
from .ai_operation_stats import operation_facts
from .ai_history_stats import collect_history, history_facts
from .ai_checks import collect_overview, current_semester
from .demo_history_logic import DEMO_NOTE
from .ai_demo_replay import replay, replay_facts, NOTE as REPLAY_NOTE

LOG = logging.getLogger(__name__)
ALLOWED_ROLES = {"admin", "academic"}
ALLOWED_ROUTES = {
    "学生管理": "/student", "学生档案": "/student", "成绩管理": "/grade", "录入成绩": "/grade",
    "考试管理": "/exam", "考试日历": "/exam", "课程管理": "/course", "课程安排": "/course",
    "教师管理": "/teacher", "授课教师": "/teacher", "教学分析": "/analysis",
    "智能预警": "/ai-warning", "智能分析": "/ai-warning", "教学预警": "/ai-warning",
}
VALID_STATUSES = {v for v, _ in AIWarningCase.STATUS_CHOICES}


def guard(request):
    role = get_teaching_role(request.user)
    if role not in ALLOWED_ROLES:
        return Response({"detail": "仅系统管理员与教务管理人员可使用该功能。"}, status=403)
    return None


def to_record(row):
    return {"id": row.id, "key": row.event_key, "rule_code": row.rule_code,
            "semester_key": row.semester_key, "category": row.category, "severity": row.severity,
            "title": row.title, "description": row.description, "source": row.source,
            "route_path": row.route_path if row.route_path in ALLOWED_ROUTES.values() else "/ai-warning",
            "evidence": row.evidence, "status": row.status, "status_label": row.get_status_display(),
            "handler": row.handler, "resolution_note": row.resolution_note,
            "source_active": row.source_active,
            "source_cleared_at": row.source_cleared_at.isoformat() if row.source_cleared_at else None,
            "source_reappeared_at": row.source_reappeared_at.isoformat() if row.source_reappeared_at else None,
            "created_at": row.created_at.isoformat(), "updated_at": row.updated_at.isoformat()}


def ui_actions(question):
    """路由白名单由后端决定，永不使用 LLM 生成的任意 URL。"""
    candidates = []
    for phrase, path in ALLOWED_ROUTES.items():
        if phrase in question and path not in [x["path"] for x in candidates]:
            candidates.append({"label": f"前往{phrase}", "path": path})
    if not candidates:
        candidates = [{"label": "查看考试管理", "path": "/exam"}, {"label": "查看成绩管理", "path": "/grade"}]
    return candidates[:3]


def is_history_question(question):
    return any(word in question for word in ("历史", "趋势", "跨学期", "历年", "历学期", "不同学期", "各学期", "上学期", "往年", "纵向", "同比", "环比", "上一学期", "前一学期", "过去", "近几年"))


def grounded_fallback(question, data):
    stats = data["summary"]
    title = data["semester"]["name"] if data["semester"] else "当前学期档案未登记"
    teaching = data["analyses"]["teaching"]
    grade = data["analyses"]["grade"]
    if is_history_question(question) and not any(x in question for x in ("打开", "前往", "跳转", "进入")):
        h = data.get("history_trend")
        if not h:
            return "本次尚未读取历史学期统计，请查看历史趋势分析分区。"
        return (f"已读取{len(h['terms'])}个学期档案，其中{h['observed_terms']}期有业务记录、"
                f"{h['grade_terms']}期有有效成绩记录。请查看历史趋势分析分区的逐期数据及日期核查结果。"
                "仅凭登记统计不能判断未来趋势；当前学期可能尚未结束。")
    if not data["semester"]:
        return "当前数据库没有标记为当前学期、且起止日期覆盖今天的学期档案。请在学期管理中确认当前学期，不能以旧学期冒充当前统计。"
    if any(x in question for x in ("专业", "年级", "培养方案")) and any(x in question for x in ("必修", "授课", "考试", "课程")):
        return "现有课程、考试记录没有经过核验的专业—年级适用范围关联，不能可靠回答指定专业年级的全部课程或考试。请在课程管理和考试管理中补充正式对应关系。"
    if any(x in question for x in ("打开", "前往", "跳转", "进入")):
        return "已定位到对应的教学系统页面。请选择下方经过验证的站内跳转入口。"
    if any(x in question for x in ("考试", "考场", "第18周", "第19周")):
        week_note = (f"第18周登记{teaching['week18_exams']}场，第19周登记{teaching['week19_exams']}场。"
                     if teaching["week18_exams"] is not None else "学期开始日期缺失，暂不计算教学周。")
        scan_note = ("规则扫描完整。" if data["rules_complete"] else "超过单次扫描上限，异常检查结果不完整。")
        return (f"{title}目前登记考试{stats['exams']}场；在本次扫描范围内缺少考场地点"
                f"{teaching['missing_exam_location']}场，同考场时间重叠{teaching['venue_collisions']}组。"
                f"{week_note}{scan_note}这些数字不表示全部排考已通过审核。")
    if any(x in question for x in ("成绩", "挂科", "不及格", "平均分", "预警")):
        if not grade["records"]:
            return f"{title}已发布成绩{stats['published_grades']}条，目前没有符合百分制统计口径的有效成绩，暂不能计算分布及比率。"
        return (f"{title}已发布成绩{stats['published_grades']}条，其中有效百分制记录{grade['records']}条，"
                f"涉及有效成绩学生{grade['valid_students']}人。平均分{grade['average_score']}，中位数{grade['median_score']}，"
                f"记录及格率{grade['pass_rate']}%，低于60分记录占比{grade['below_pass_rate']}%，"
                f"90分及以上记录占比{grade['excellent_rate']}%。这些是考核记录占比，不是学生最终课程通过率。"
                "目前未配置学校正式学业预警规则，不自动判定学生风险。")
    if any(x in question for x in ("教师", "教学班", "课程", "排课")):
        return (f"{title}登记课程{stats['courses']}门、教学班{stats['teaching_classes']}个。"
                f"本次检查发现未填上课时间的教学班{teaching['missing_schedule']}个，"
                f"选课人数超出登记容量的教学班{teaching['over_capacity']}个。"
                "属于登记数据核查，并不代表教师实际教学质量评价。")
    return (f"已读取{title}的教务数据：课程{stats['courses']}门、教学班{stats['teaching_classes']}个、"
            f"考试{stats['exams']}场、已发布成绩记录{stats['published_grades']}条。"
            "可询问考试冲突、授课任务完整性或成绩汇总；涉及个体学业结论须遵循正式权限和预警规则。")


def call_deepseek(question, history, data):
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        return None, "not_configured"
    if not data["semester"]:
        return None, "no_semester"
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-flash").strip() or "deepseek-flash"
    # 只发送学院的聚合与规则信息，绝不发送学号、姓名、电话或个人成绩记录。
    teaching = data["analyses"]["teaching"]
    summary = data["summary"]
    grade = data["analyses"]["grade"]
    # 课程层面至少5名不同学生，且最多15门。外部模型不接收个人记录或小样本课程。
    eligible_courses = [x for x in grade["course_results"] if x["student_count"] >= 5]
    grade_facts = {"说明": grade["explanation"], "有效记录数": grade["records"],
                   "排除记录数": grade["excluded_records"]}
    if grade["valid_students"] >= 5:
        grade_facts.update({"记录平均分": grade["average_score"], "中位数": grade["median_score"],
                            "总体标准差": grade["std_score"], "及格记录占比百分数": grade["pass_rate"],
                            "低于60分记录占比百分数": grade["below_pass_rate"],
                            "90分及以上记录占比百分数": grade["excellent_rate"],
                            "分数段记录分布": [{"分数段": x["label"], "记录数": x["count"], "占比百分数": x["rate"]} for x in grade["distribution"]],
                            "满足5名不同学生条件的课程数": len(eligible_courses),
                            "课程样本": [{"课程": x["course_name"], "有效记录数": x["records"],
                                      "平均分": x["average_score"], "及格记录占比百分数": x["pass_rate"],
                                      "90分及以上记录占比百分数": x["excellent_rate"]} for x in eligible_courses[:15]],
                            "课程样本说明": "仅提供至多15门至少5名不同学生的课程，不保证覆盖全体课程。"})
    else:
        grade_facts["样本说明"] = "有效成绩涉及学生不足5人，不向外部模型提供详细分数统计；请查看有权限的站内成绩分析。"
    # 使用业务中文名称而非内部字段；去除无助于回答的数据库主键。
    facts = {
        "当前学期": data["semester"]["name"] if data["semester"] else None,
        "教务登记统计": {"课程数": summary["courses"], "教学班数": summary["teaching_classes"],
                       "考试场次": summary["exams"], "已发布成绩记录数": summary["published_grades"],
                       "涉及学生数": summary["graded_students"]},
        "教学运行核查": {"已扫描在开教学班数": teaching["active_classes_scanned"],
                         "未登记上课时间的教学班数": teaching["missing_schedule"],
                         "超登记容量的教学班数": teaching["over_capacity"],
                         "缺少考试地点场次": teaching["missing_exam_location"],
                         "同考场时间冲突组数": teaching["venue_collisions"],
                         "第18周登记考试数": teaching["week18_exams"],
                         "第19周登记考试数": teaching["week19_exams"]},
        "教学运行综合统计": operation_facts(teaching.get("operations")),
        "已发布成绩统计": grade_facts,
        "规则核查": {"扫描范围内命中事项数": data["rule_total"], "扫描完整": data["rules_complete"]},
        "统计说明": data["data_notes"],
    }
    if data.get("prediction_replay") is not None:
        facts["历史演示预测回放"] = replay_facts(data["prediction_replay"])
    if data.get("history_trend") is not None:
        facts["跨学期历史统计"] = history_facts(data["history_trend"])
    system_message = (
        "你是智慧政管教学子系统的教务数据分析助手，面向教务管理人员。"
        "以当前提供的聚合事实为唯一数据依据；历史对话不是当前数据库事实。"
        "只使用自然、专业、简洁的中文，不显示JSON、数据库字段名、主键、代码或英文变量。"
        "简单查询直接回答；综合问题可分为数据库事实、分析、管理建议三个部分，建议不超过三条。"
        "仅使用普通段落、Markdown二至三级标题、加粗和有序/无序列表；不要使用表格、HTML、代码块或链接。"
        "不重复列出所有指标，仅选择与问题相关的数据；建议通常控制在200至450个汉字内，必要时可稍长。"
        "明确区分数据库事实、有限推断和建议。缺少数据、学期未登记、扫描不完整时如实说明，不能把缺失值当作零。"
        "可引用明确提供的分数段、标准差和记录占比；均分接近不等于学生成绩集中。60分、90分是描述性统计线，不是正式学业预警阈值。记录占比不是学生占比或最终课程通过率，不推断个体风险、教学质量或预测结果。"
        "课程均分样本不保证覆盖全部课程，不得宣称其极值为全体课程极值。"
        "教学班容量利用率只统计正容量班级，可超过100%；选课人次不是去重学生数。教学班数不是实际学时，星期分布只包含明确可解析的登记格式，考试地点数不是考场占用率。"
        "聚合事实中若标明演示数据，必须明确说明仅供功能演示，不代表真实历史、真实教学效果或预测准确率。"
        "历史统计按业务登记学期归属；日期越界或缺失只说明数据质量问题，不自动改归属。无记录不代表实际为零；只有一期有效数据时不能判断跨学期变化。进行中学期与结束学期的覆盖不同；同课程比较不保证考核构成一致。不得根据历史描述统计声称已完成预测。仅当提供历史演示预测回放事实时可解释其模型指标、课程级概率汇总和误报漏报；明确它是合成历史数据回放，不能推断当前学生风险、不能推荐个体处置、不能视为正式预警。0.25是训练确定的演示关注阈值，不是学校标准。未提供历史统计时不得推断历史变化。"
        "第18/19周的登记场次是统计结果，不是正式考试周安排或异常判定。"
        "规则零命中不代表所有教学风险排除；未配置正式学业阈值时不得判定正式学业预警。"
        "不能编造数据、课程归属、预警等级或提升比例；不得输出个人隐私、承诺操作数据库或声称完成正式审核。"
        "不能触发跳转或修改。以下是本次聚合事实：\n" + json.dumps(facts, ensure_ascii=False, default=str)
    )
    messages = [{"role": "system", "content": system_message}]
    for item in history[-6:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = str(item.get("content", ""))[:1200]
        if role in {"user", "assistant"} and content.strip():
            # 即使上一轮因隐私检查而本地拒答，也不能在后续轮次夹带其个人标识。
            has_sensitive = re.search(r"(?<!\d)(?:1[3-9]\d{9}|\d{8,13})(?!\d)|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", content)
            if has_sensitive or any(x in content for x in ("个人成绩", "个人档案", "某学生", "某同学")):
                continue
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": question})
    payload = {"model": model, "messages": messages, "max_tokens": 800, "temperature": 0.2,
               "thinking": {"type": "disabled"}, "stream": False}
    req = URLRequest("https://api.deepseek.com/chat/completions",
                     data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                     headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                     method="POST")
    try:
        with urlopen(req, timeout=28) as response:
            obj = json.loads(response.read(2_000_000).decode("utf-8"))
        answer = (obj.get("choices") or [{}])[0].get("message", {}).get("content")
        if isinstance(answer, str) and answer.strip():
            return answer.strip()[:6000], "deepseek"
        return None, "empty_reply"
    except HTTPError as exc:
        # 无论服务商具体错误内容是什么，都不记录或输出 API Key。
        LOG.warning("DeepSeek API HTTP error: %s", exc.code)
        return None, "provider_http_error"
    except (URLError, TimeoutError, OSError, ValueError, KeyError) as exc:
        LOG.warning("DeepSeek API failed: %s", type(exc).__name__)
        return None, "provider_unavailable"


class AIDemoReplayView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refused = guard(request)
        if refused:
            return refused
        try:
            return Response(replay())
        except Exception as exc:
            LOG.warning("Demo replay unavailable: %s", type(exc).__name__)
            return Response({"detail": "演示回放不可用：请确认服务器模型目录、训练报告、依赖版本和历史演示数据一致。"}, status=503)


class AIOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        refused = guard(request)
        if refused:
            return refused
        data = collect_overview()
        data["history_trend"] = collect_history(data["semester"]["id"] if data["semester"] else None)
        data["ai"] = {"enabled": bool(os.getenv("DEEPSEEK_API_KEY", "").strip()),
                      "model": os.getenv("DEEPSEEK_MODEL", "deepseek-flash")}
        active_cases = AIWarningCase.objects.filter(semester_key=data["semester"]["name"]) if data["semester"] else AIWarningCase.objects.none()
        data["case_counts"] = {
            "pending": active_cases.filter(status="pending").count(),
            "in_progress": active_cases.filter(status="in_progress").count(),
            "resolved": active_cases.filter(status="resolved").count(),
            "dismissed": active_cases.filter(status="dismissed").count(),
            "source_active": active_cases.filter(source_active=True).count(),
            "source_cleared": active_cases.filter(source_active=False).count(),
        }
        return Response(data)


class AIChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refused = guard(request)
        if refused:
            return refused
        question = request.data.get("question")
        if not isinstance(question, str) or not 1 <= len(question.strip()) <= 500:
            return Response({"detail": "问题长度须在1至500字之间。"}, status=400)
        question = question.strip()
        # 账号级简易调用限额，减少异常频繁调用产生的外部 API 费用。
        rate_key = f"teaching_ai_chat:{request.user.pk}:{timezone.now().strftime('%Y%m%d%H%M')}"
        try:
            if cache.add(rate_key, 1, timeout=90):
                call_count = 1
            else:
                call_count = cache.incr(rate_key)
            if call_count > 12:
                return Response({"detail": "请求过于频繁，请稍后重试。"}, status=429)
        except (ValueError, TypeError, NotImplementedError):
            # 缓存不可用时不误报“调用已成功”；外部 API 的安全配置仍由后端控制。
            LOG.warning("AI per-user rate-limit cache unavailable")
        # 试运行阶段不支持把个体学号、电话号码和个人成绩问题传给外部模型。
        personal_token = bool(re.search(r"(?<!\d)(?:1[3-9]\d{9}|\d{8,13})(?!\d)|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", question))
        personal_query = any(x in question for x in ("某同学", "某学生", "这个学生", "单个学生", "个人成绩", "个人档案"))
        if personal_token or personal_query:
            return Response({"answer": "为保护学生隐私，本中心暂不通过外部模型处理包含个人身份信息的问题。请通过学生管理或成绩管理中已有权限控制的页面查询。",
                             "mode": "data_query", "actions": [{"label": "查看学生管理", "path": "/student"}, {"label": "查看成绩管理", "path": "/grade"}],
                             "semester": None, "data_sources": [], "privacy": "未向外部模型发送个人信息。"})
        history = request.data.get("history", [])
        if not isinstance(history, list):
            history = []
        data = collect_overview()
        if is_history_question(question):
            data["history_trend"] = collect_history(data["semester"]["id"] if data["semester"] else None)
        replay_question = "历史演示预测" in question or "预测回放" in question
        if replay_question and not any(x in question for x in ("打开", "前往", "跳转", "进入")):
            try:
                data["prediction_replay"] = replay()
            except Exception as exc:
                LOG.warning("Demo replay for chat unavailable: %s", type(exc).__name__)
                return Response({"answer": "历史演示预测回放暂不可用，请先确认第六分区能正常运行。未生成预测结论。", "mode": "data_query", "actions": [], "data_sources": [], "semester": None})
        actions = ui_actions(question)
        # 对导航命令不调用大模型，降低延迟并确保无不可信跳转。
        if any(x in question for x in ("打开", "前往", "跳转", "进入")):
            answer, mode = grounded_fallback(question, data), "navigation"
        else:
            answer, mode = call_deepseek(question, history, data)
            if not answer:
                if data.get("prediction_replay"):
                    r = data["prediction_replay"]
                    answer = (REPLAY_NOTE + f"\n{r['semester']}共回放{r['samples']}个学生—课程样本，"
                              f"其中{r['flagged']}个达到演示阈值。实际低分{r['actual_low']}个，"
                              f"误报{r['confusion']['fp']}个，漏报{r['confusion']['fn']}个。请查看第六分区。")
                else:
                    answer = grounded_fallback(question, data)
                mode = "data_query"
        if data.get("demo_data") and mode != "navigation":
            answer = DEMO_NOTE + "\n\n" + answer
        return Response({"answer": answer, "mode": mode, "actions": actions,
                         "semester": data["semester"],
                         "data_sources": ["Course", "TeachingClass", "Exam", "Grade（已发布）"] + (["Semester"] if "history_trend" in data else []) + (["历史合成数据模型回放"] if "prediction_replay" in data else []),
                         "privacy": "仅向模型发送学院聚合统计，不传输学生个人档案。"})


class AIWarningListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        refused = guard(request)
        if refused:
            return refused
        # 按当前学期分页展示，避免“只取前 300 条”导致已同步事项无法管理。
        semester = current_semester()
        if not semester:
            return Response({"count": 0, "results": [], "next_offset": None})
        try:
            offset = max(0, int(request.query_params.get("offset", "0")))
            limit = min(200, max(1, int(request.query_params.get("limit", "100"))))
        except (ValueError, TypeError):
            return Response({"detail": "分页参数无效。"}, status=400)
        cases = AIWarningCase.objects.filter(semester_key=semester.name)
        state = request.query_params.get("status", "").strip()
        if state:
            if state not in VALID_STATUSES:
                return Response({"detail": "筛选状态无效。"}, status=400)
            cases = cases.filter(status=state)
        count = cases.count()
        rows = list(cases[offset:offset + limit])
        next_offset = offset + len(rows) if offset + len(rows) < count else None
        return Response({"count": count, "results": [to_record(r) for r in rows],
                         "next_offset": next_offset})


class AIWarningSyncView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        refused = guard(request)
        if refused:
            return refused
        data = collect_overview(include_all_rules=True)
        if not data["semester"]:
            return Response({"detail": "当前学期未设置，未同步任何事项。"}, status=409)
        if not data["rules_complete"]:
            return Response({"detail": "规则扫描不完整，为防止漏判或误关闭，未执行同步。"}, status=409)
        now = timezone.now()
        created = updated = reappeared = 0
        detected_keys = set()
        for item in data["_full_rules"]:
            detected_keys.add(item["key"])
            row, is_new = AIWarningCase.objects.get_or_create(event_key=item["key"], defaults={
                "rule_code": item["rule_code"], "semester_key": item["semester_key"],
                "category": item["category"], "severity": item["severity"],
                "title": item["title"], "description": item["description"],
                "source": item["source"], "route_path": item["route_path"], "evidence": item["evidence"],
                "source_active": True,
            })
            if is_new:
                created += 1
                continue
            if not row.source_active:
                reappeared += 1
                row.source_reappeared_at = now
            row.source_active = True
            row.source_cleared_at = None
            # 原始依据可能已修改。只刷新来源字段，绝不覆盖人工处理人、说明、处理状态。
            for field in ("semester_key", "rule_code", "category", "severity", "title", "description", "source", "route_path", "evidence"):
                setattr(row, field, item[field])
            row.last_seen_at = now
            row.save(update_fields=[
                "semester_key", "rule_code", "category", "severity", "title", "description", "source", "route_path", "evidence",
                "source_active", "source_cleared_at", "source_reappeared_at", "last_seen_at", "updated_at",
            ])
            updated += 1
        # 仅对本学期、此前确实处于来源命中状态的记录做“源风险消失”标记。
        stale = AIWarningCase.objects.filter(semester_key=data["semester"]["name"], source_active=True)
        if detected_keys:
            stale = stale.exclude(event_key__in=detected_keys)
        cleared = stale.update(source_active=False, source_cleared_at=now, updated_at=now)
        return Response({
            "created": created, "updated": updated, "reappeared": reappeared,
            "cleared": cleared, "detected": len(detected_keys),
            "message": "同步的是全部已完成扫描的规则事件；来源变化与人工核查状态分开保存。",
        })


class AIWarningDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, case_id: int):
        refused = guard(request)
        if refused:
            return refused
        row = AIWarningCase.objects.filter(pk=case_id).first()
        if not row:
            return Response({"detail": "预警事项不存在。"}, status=404)
        new_status = request.data.get("status", row.status)
        if new_status not in VALID_STATUSES:
            return Response({"detail": "状态无效。"}, status=400)
        handler = request.data.get("handler", row.handler)
        note = request.data.get("resolution_note", row.resolution_note)
        if not isinstance(handler, str) or len(handler) > 80 or not isinstance(note, str) or len(note) > 2000:
            return Response({"detail": "处理人或处理说明长度不符合要求。"}, status=400)
        if new_status in {"resolved", "dismissed"} and not note.strip():
            return Response({"detail": "结案或排除风险前必须填写处理依据。"}, status=400)
        row.status, row.handler, row.resolution_note = new_status, handler.strip(), note.strip()
        row.save(update_fields=["status", "handler", "resolution_note", "updated_at"])
        return Response(to_record(row))
