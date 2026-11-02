"""
管理命令：验证智能预测 Agent 的真实连通性与行为。

与 apps/graduate/tests/test_prediction_agent.py 的分工：
  - 单元测试全部打桩，不联网，用来防回归；
  - 本命令**真实调用模型 API**，用来确认线上配置（代理、API key、
    模型名、超时）确实可用，以及 Agent 是否真的会多轮检索。

用法：
    cd backend
    python manage.py verify_prediction_agent                      # 全部检查
    python manage.py verify_prediction_agent --check config       # 只看配置
    python manage.py verify_prediction_agent --check connectivity # 只测连通
    python manage.py verify_prediction_agent --check tools        # 只测工具
    python manage.py verify_prediction_agent --check agent        # 只跑 Agent
    python manage.py verify_prediction_agent --student 2021010001
    python manage.py verify_prediction_agent --question "休学最长多久？"
"""

import json
import time

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.graduate import agent, agent_tools, llm, services


DEFAULT_QUESTIONS = [
    # 制度类：应触发 search_policy，且在片段不足时换词重试
    ("policy", "研究生学业奖学金的评审条件是什么？该生是否符合？"),
    # 数据类：应读画像 / 对比同群体，不应编造制度条款
    ("data", "该生在同年级里处于什么水位？"),
    # 预警类：应调 list_warnings
    ("warning", "该生当前有哪些预警记录？"),
]

TOOL_LABELS = {
    "search_policy": "检索制度文件",
    "get_student_snapshot": "读取学生画像",
    "compare_peers": "对比同群体",
    "list_warnings": "查询预警记录",
}


class Command(BaseCommand):
    help = "Verify prediction agent configuration, connectivity, tools and loop behaviour"

    def add_arguments(self, parser):
        parser.add_argument(
            "--check",
            type=str,
            default="all",
            choices=["all", "config", "connectivity", "tools", "agent"],
            help="Which check to run (default: all)",
        )
        parser.add_argument(
            "--student",
            type=str,
            default="",
            help="Student ID to test against (default: first available snapshot)",
        )
        parser.add_argument(
            "--question",
            type=str,
            default="",
            help="Ask one specific question instead of the built-in set",
        )

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def ok(self, message):
        self.stdout.write(self.style.SUCCESS(f"  [OK]   {message}"))

    def warn(self, message):
        self.stdout.write(self.style.WARNING(f"  [WARN] {message}"))

    def fail(self, message):
        self.stdout.write(self.style.ERROR(f"  [FAIL] {message}"))

    def section(self, title):
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING(f"=== {title} ==="))

    def resolve_student_id(self, requested):
        if requested:
            return requested
        from apps.graduate.models import PredictionSnapshot

        snapshot = PredictionSnapshot.objects.select_related("student").first()
        return snapshot.student.student_id if snapshot else ""

    # ------------------------------------------------------------------
    # checks
    # ------------------------------------------------------------------

    def check_config(self):
        self.section("1. 配置检查")
        failed = False

        if getattr(settings, "PREDICTION_LLM_ENABLED", False):
            self.ok("PREDICTION_LLM_ENABLED = True")
        else:
            self.fail("PREDICTION_LLM_ENABLED = False，模型调用被整体关闭")
            failed = True

        key = getattr(settings, "PREDICTION_LLM_API_KEY", "")
        if key.strip():
            self.ok(f"API key 已配置（{len(key)} 字符，尾号 ...{key[-4:]}）")
        else:
            self.fail("PREDICTION_LLM_API_KEY 为空")
            failed = True

        resolved = llm.resolve_llm_runtime_options({})
        self.stdout.write(
            f"         provider={resolved['provider']} model={resolved['model']} "
            f"api_style={resolved['api_style']}"
        )
        self.stdout.write(
            f"         timeout={resolved['timeout_seconds']}s "
            f"effort={resolved['reasoning_effort'] or '-'} "
            f"thinking={resolved['thinking_type'] or '-'}"
        )

        if not resolved["model"]:
            self.fail("模型名为空")
            failed = True

        # 代理是上次线上事故的根因，单独提示
        explicit_proxy = getattr(settings, "PREDICTION_LLM_PROXY", "")
        trust_env = getattr(settings, "PREDICTION_LLM_TRUST_ENV_PROXY", False)
        if explicit_proxy:
            self.warn(f"将强制走代理 {explicit_proxy}（该代理必须可用）")
        elif trust_env:
            from urllib.request import getproxies

            env_proxies = getproxies()
            if env_proxies:
                self.warn(
                    f"跟随系统代理 {env_proxies}；若该代理已退出会导致 "
                    "ConnectionRefused 并静默回退规则话术"
                )
            else:
                self.ok("跟随系统代理，但当前未检测到代理设置")
        else:
            self.ok("直连模型 API（忽略系统代理）")

        if getattr(settings, "PREDICTION_AGENT_ENABLED", False):
            budget = agent.resolve_agent_budget({})
            self.ok(
                f"Agent 已启用：maxSteps={budget['maxSteps']} "
                f"timeBudget={budget['timeBudgetSeconds']}s"
            )
        else:
            self.warn("PREDICTION_AGENT_ENABLED = False，将走单次 pipeline")

        if not getattr(settings, "PREDICTION_EXPOSE_DEBUG", False):
            self.warn(
                "PREDICTION_EXPOSE_DEBUG = False：trace 会被裁剪，"
                "排查期建议临时开启以便看到 llmReason"
            )
        return not failed

    def check_connectivity(self):
        self.section("2. 真实连通性（会实际调用 API）")
        started = time.monotonic()
        result = llm.invoke_prediction_chat_completion(
            {
                "messages": [
                    {"role": "system", "content": "你是研究生培养顾问。"},
                    {"role": "user", "content": "只回一句：连通性正常。"},
                ],
                "structuredInput": {},
            },
            {},
        )
        elapsed = time.monotonic() - started

        if result.get("used"):
            self.ok(f"调用成功，耗时 {elapsed:.1f}s，模型 {result.get('model')}")
            usage = result.get("usage") or {}
            if usage:
                self.stdout.write(f"         tokens={usage.get('total_tokens')}")
            return True

        reason = result.get("reason", "")
        self.fail(f"调用失败：reason={reason} 耗时 {elapsed:.1f}s")
        detail = str(result.get("error", ""))[:300]
        if detail:
            self.stdout.write(f"         {detail}")
        # 给出针对性的排查建议
        if reason == "request_failed" and "10061" in detail:
            self.stdout.write(
                "         提示：连接被拒通常是本机代理已退出。"
                "确认 PREDICTION_LLM_PROXY 留空且 TRUST_ENV_PROXY=False"
            )
        elif reason.startswith("http_401"):
            self.stdout.write("         提示：API key 无效或已过期")
        elif reason.startswith("http_404"):
            self.stdout.write("         提示：模型名或 base_url 可能不对")
        return False

    def check_tools(self, student_id):
        self.section("3. 工具层（不调模型，直接执行）")
        context = services.get_intelligent_prediction_context(student_id)
        if context is None:
            self.fail(f"学号 {student_id} 没有预测快照")
            return False

        cases = [
            ("get_student_snapshot", {}),
            ("compare_peers", {"scope": "all"}),
            ("list_warnings", {}),
            ("search_policy", {"query": "学业奖学金 评审条件"}),
            # 错误路径：这两个应当返回 ok=False 而不是抛异常
            ("search_policy", {"query": ""}),
            ("compare_peers", {"scope": "nonsense"}),
            ("no_such_tool", {}),
        ]
        expect_failure = {4, 5, 6}
        all_passed = True

        for index, (name, arguments) in enumerate(cases):
            payload = agent_tools.execute_tool(name, arguments, context=context)
            is_ok = bool(payload.get("ok"))
            should_fail = index in expect_failure
            passed = (not is_ok) if should_fail else is_ok
            all_passed = all_passed and passed

            label = f"{name}({json.dumps(arguments, ensure_ascii=False)})"
            suffix = " [预期失败]" if should_fail else ""
            if passed:
                extra = ""
                if payload.get("hitCount") is not None:
                    extra = f" hits={payload['hitCount']}"
                self.ok(f"{label}{suffix}{extra}")
            else:
                self.fail(f"{label}{suffix} -> {json.dumps(payload, ensure_ascii=False)[:160]}")

        return all_passed

    def check_agent(self, student_id, question):
        self.section("4. Agent 循环（真实调用，可能较慢）")
        context = services.get_intelligent_prediction_context(student_id)
        if context is None:
            self.fail(f"学号 {student_id} 没有预测快照")
            return False

        questions = [("custom", question)] if question else DEFAULT_QUESTIONS
        all_passed = True

        for label, text in questions:
            self.stdout.write("")
            self.stdout.write(f"  问题[{label}]：{text}")
            started = time.monotonic()
            tools_used = []
            final_event = None

            for event in agent.stream_prediction_chat_agent(
                context=context, question=text
            ):
                kind = event.get("type")
                if kind == "tool_start":
                    tool_label = TOOL_LABELS.get(event["tool"], event["tool"])
                    query = (event.get("arguments") or {}).get("query")
                    tools_used.append(event["tool"])
                    self.stdout.write(
                        f"         -> {tool_label}" + (f"：{query}" if query else "")
                    )
                elif kind == "final":
                    final_event = event

            elapsed = time.monotonic() - started
            if not final_event:
                self.fail(f"没有收到 final 事件（{elapsed:.1f}s）")
                all_passed = False
                continue

            if not final_event.get("used"):
                self.fail(
                    f"Agent 未产出答案：reason={final_event.get('reason')} "
                    f"（{elapsed:.1f}s）—— 会回落到单次 pipeline"
                )
                all_passed = False
                continue

            trace = final_event.get("trace") or {}
            answer = final_event.get("answer") or {}
            self.ok(
                f"完成：{elapsed:.1f}s stop={trace.get('stopReason')} "
                f"工具调用 {trace.get('toolCallCount')} 次"
            )
            self.stdout.write(f"         答案：{str(answer.get('directAnswer', ''))[:160]}")

            citations = answer.get("citations") or []
            if label == "policy":
                # 制度类问题必须检索过，否则就是在凭记忆编条款
                if "search_policy" in tools_used:
                    self.ok("制度类问题确实检索了制度文件")
                else:
                    self.fail("制度类问题没有调用 search_policy（可能在凭记忆回答）")
                    all_passed = False
                if citations:
                    titles = ", ".join(c.get("title", "") for c in citations[:3])
                    self.ok(f"带回引用：{titles}")
                else:
                    self.warn("没有带回引用，请确认答案里是否声明了「未检索到制度依据」")

        return all_passed

    # ------------------------------------------------------------------

    def handle(self, *args, **options):
        requested = options["check"]
        student_id = self.resolve_student_id(options["student"])
        question = options["question"].strip()

        self.stdout.write(self.style.MIGRATE_HEADING("智能预测 Agent 验证"))
        if student_id:
            self.stdout.write(f"目标学号：{student_id}")
        else:
            self.stdout.write(self.style.ERROR("库里没有预测快照，请先导入数据"))
            return

        results = {}
        if requested in ("all", "config"):
            results["配置"] = self.check_config()
        if requested in ("all", "connectivity"):
            results["连通性"] = self.check_connectivity()
        if requested in ("all", "tools"):
            results["工具层"] = self.check_tools(student_id)
        if requested in ("all", "agent"):
            # 连通性都不过就没必要烧 token 跑 Agent
            if results.get("连通性") is False:
                self.warn("连通性未通过，跳过 Agent 循环检查")
            else:
                results["Agent 循环"] = self.check_agent(student_id, question)

        self.section("结论")
        for name, passed in results.items():
            (self.ok if passed else self.fail)(name)
        if all(results.values()):
            self.stdout.write(self.style.SUCCESS("\n全部检查通过。"))
        else:
            self.stdout.write(
                self.style.ERROR("\n存在未通过项，请按上面的提示排查。")
            )
