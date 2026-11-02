"""智能预测 Agent 的离线测试。

这些用例全部 **不打真实模型 API**：用假的 stream 生成器替掉 llm 层，
所以可以在 CI / 无网络环境稳定重跑。覆盖的是最容易悄悄坏掉的地方：

  1. 脏 JSON 解析（模型输出两遍、带围栏、前置诱饵对象）；
  2. 数组字段被写成字符串时不能丢内容；
  3. tool_calls 协议：每个 tool_call_id 必须有对应的 role=tool 回复；
  4. thinking 模式下 reasoning_content 必须回传；
  5. 工具层字段名与错误路径；
  6. 代理解析：默认直连，不跟随系统代理；
  7. Agent 不可用时要回落，而不是报错。

真实模型连通性请用 `python manage.py verify_prediction_agent`（会真实调用 API）。

运行：
    cd backend
    python manage.py test apps.graduate.tests.test_prediction_agent -v 2
"""

import json
from unittest import mock

from django.test import SimpleTestCase, TestCase, override_settings

from apps.graduate import agent, agent_tools, llm


CHAT_REQUIRED = llm.PREDICTION_CHAT_ANSWER_SCHEMA["required"]

GOOD_ANSWER = {
    "directAnswer": "该生暂无延期风险。",
    "reasoning": ["学分完成率 92%"],
    "actionPlan": ["保持常规跟踪"],
    "citations": [],
}
GOOD_JSON = json.dumps(GOOD_ANSWER, ensure_ascii=False)


def fake_stream(events):
    """把事件列表包装成 stream_chat_messages 那样的生成器。"""

    def _stream(**_kwargs):
        for event in events:
            yield event

    return _stream


def scripted_rounds(rounds, *, default=None, record=None):
    """按轮次脚本化 stream_chat_messages。

    循环的调用次数 = 对话轮数 + 1（收尾轮），用固定长度的 side_effect 列表
    很容易因为少算一次而抛 StopIteration。这里脚本用完后自动返回 default
    （默认是一个合法 JSON 收尾），并可选地把每次的 kwargs 记录到 record。
    """
    remaining = list(rounds)
    fallback = default if default is not None else [done_event(GOOD_JSON)]

    def _side_effect(**kwargs):
        if record is not None:
            record.append(kwargs)
        events = remaining.pop(0) if remaining else fallback
        return fake_stream(events)()

    return _side_effect


def done_event(content, *, tool_calls=None, reasoning=None):
    message = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    if reasoning:
        message["reasoning_content"] = reasoning
    return {
        "type": "done",
        "message": message,
        "finishReason": "tool_calls" if tool_calls else "stop",
        "usage": {"total_tokens": 10},
        "model": "fake-model",
        "responseId": "resp_fake",
    }


def tool_call(name, arguments, call_id="call_1"):
    return {
        "id": call_id,
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(arguments, ensure_ascii=False)},
    }


FAKE_CONTEXT = {
    "student": {
        "studentId": "2021010001",
        "name": "张三",
        "grade": "2021级",
        "major": "政治学理论",
        "degreeType": "学术型硕士",
        "currentStatus": "正常在籍",
        "advisorName": "李老师",
    },
    "prediction": {"riskLevel": "低风险", "riskField": "实践参与", "riskCategory": "培养风险"},
    "currentSnapshot": {
        "courseAverage": 82.8,
        "attendanceRate": 87,
        "creditCompletionRate": 92,
        "graduationProgressRate": 84,
        "trainingPlanCompletionRate": 91,
        "advisorEvaluationScore": 80,
        "wellbeingScore": 75,
        "overdueTasksCount": 1,
    },
    "derived": {
        "compositeIndexCurrent": 71.8,
        "forecastTrend": [71.8, 74.0, 77.7],
        "keyFactors": [{"label": "实践参与", "weight": 24.8, "gap": 60.0}],
    },
    "peerReferences": {
        "sameGrade": {
            "sampleSize": 5,
            "averageSnapshot": {
                "compositePredictionIndex": 88.1,
                "courseAverage": 86.4,
                "attendanceRate": 89.8,
            },
        },
        "sameMajor": {
            "sampleSize": 3,
            "averageSnapshot": {"compositePredictionIndex": 75.7},
        },
        "sameGradeMajor": {
            "sampleSize": 2,
            "averageSnapshot": {"compositePredictionIndex": 85.2},
        },
    },
}


class ParseJsonPayloadTests(SimpleTestCase):
    """脏输出解析。这些形态都是真实抓到过的，不是假想。"""

    def test_plain_object(self):
        self.assertEqual(llm.parse_json_payload('{"a": 1}'), {"a": 1})

    def test_markdown_fenced(self):
        raw = '```json\n{"a": 1}\n```'
        self.assertEqual(llm.parse_json_payload(raw), {"a": 1})

    def test_prose_around_json(self):
        raw = 'Let me think about this.\n{"a": 1}\nThat is my answer.'
        self.assertEqual(llm.parse_json_payload(raw), {"a": 1})

    def test_duplicated_object_is_not_concatenated(self):
        """模型把同一答案输出两遍（紧凑版+缩进版），中间用空格填充。

        这是线上实际导致 invalid_json_text 的形态：按最外层花括号截取
        会把两个对象连在一起，反而解析失败。
        """
        raw = GOOD_JSON + " " * 400 + json.dumps(GOOD_ANSWER, ensure_ascii=False, indent=2)
        parsed = llm.parse_json_payload(raw, expected_keys=CHAT_REQUIRED)
        self.assertEqual(parsed["directAnswer"], GOOD_ANSWER["directAnswer"])

    def test_leading_decoy_object_is_skipped(self):
        """正式答案前先吐一个无关小对象时，不能取第一个就返回。"""
        raw = '{"type": "thinking"} ' + GOOD_JSON
        parsed = llm.parse_json_payload(raw, expected_keys=CHAT_REQUIRED)
        self.assertEqual(parsed["directAnswer"], GOOD_ANSWER["directAnswer"])

    def test_schema_echo_decoy_is_skipped(self):
        raw = '{"properties": {"directAnswer": "string"}} ' + GOOD_JSON
        parsed = llm.parse_json_payload(raw, expected_keys=CHAT_REQUIRED)
        self.assertEqual(parsed["directAnswer"], GOOD_ANSWER["directAnswer"])

    def test_whitespace_padding(self):
        raw = " " * 300 + GOOD_JSON
        parsed = llm.parse_json_payload(raw, expected_keys=CHAT_REQUIRED)
        self.assertEqual(parsed["directAnswer"], GOOD_ANSWER["directAnswer"])

    def test_unparseable_returns_none(self):
        for raw in ("", "   ", "no json at all", "[1, 2]"):
            self.assertIsNone(llm.parse_json_payload(raw), raw)


class NormalizeAnswerTests(SimpleTestCase):
    def test_string_instead_of_array_is_kept(self):
        """模型偶发把 reasoning 写成字符串，旧实现会整条丢掉。"""
        answer = {
            "directAnswer": "结论",
            "reasoning": "只有一条理由",
            "actionPlan": "只有一条建议",
            "citations": [],
        }
        normalized = llm.normalize_prediction_chat_answer(answer, GOOD_ANSWER)
        self.assertEqual(normalized["reasoning"], ["只有一条理由"])
        self.assertEqual(normalized["actionPlan"], ["只有一条建议"])

    def test_dict_items_are_unwrapped(self):
        self.assertEqual(
            llm.normalize_string_list([{"text": "x"}, {"content": "y"}]),
            ["x", "y"],
        )

    def test_blank_and_none_dropped(self):
        self.assertEqual(llm.normalize_string_list(["a", "", None, "b"]), ["a", "b"])

    def test_non_dict_answer_falls_back(self):
        self.assertEqual(
            llm.normalize_prediction_chat_answer("not a dict", GOOD_ANSWER),
            GOOD_ANSWER,
        )


class LlmOpenerTests(SimpleTestCase):
    """代理解析。线上事故根因就是跟随了已退出的本机代理。"""

    def setUp(self):
        llm._opener_cache.clear()
        self.addCleanup(llm._opener_cache.clear)

    def _proxies(self, opener):
        """取 opener 上生效的代理表。

        注意 build_opener 对"空代理表"的处理：ProxyHandler({}) 不会留在
        handlers 里（没有代理要装），所以取不到 handler 就等于不走代理。
        """
        from urllib import request as urllib_request

        for handler in opener.handlers:
            if isinstance(handler, urllib_request.ProxyHandler):
                return handler.proxies
        return {}

    @override_settings(PREDICTION_LLM_PROXY="", PREDICTION_LLM_TRUST_ENV_PROXY=False)
    def test_default_bypasses_system_proxy(self):
        self.assertEqual(self._proxies(llm.build_llm_opener()), {})

    @override_settings(
        PREDICTION_LLM_PROXY="http://127.0.0.1:7897",
        PREDICTION_LLM_TRUST_ENV_PROXY=False,
    )
    def test_explicit_proxy_is_used(self):
        self.assertEqual(
            self._proxies(llm.build_llm_opener()).get("https"),
            "http://127.0.0.1:7897",
        )


class AgentToolTests(TestCase):
    """工具层。字段名写错不会抛异常，只会静默返回 None，所以必须断言取值。"""

    def test_snapshot_uses_real_field_names(self):
        result = agent_tools.execute_tool("get_student_snapshot", {}, context=FAKE_CONTEXT)
        self.assertTrue(result["ok"])
        self.assertEqual(result["currentSnapshot"]["creditCompletionRate"], 92)
        self.assertEqual(result["compositeIndexCurrent"], 71.8)
        self.assertEqual(result["student"]["name"], "张三")

    def test_compare_peers_computes_signed_gap(self):
        result = agent_tools.execute_tool("compare_peers", {"scope": "all"}, context=FAKE_CONTEXT)
        self.assertTrue(result["ok"])
        # 71.8 - 88.1 = -16.3，负值表示低于群体均值
        self.assertAlmostEqual(result["comparisons"]["sameGrade"]["gap"], -16.3, places=1)

    def test_compare_peers_rejects_unknown_scope(self):
        result = agent_tools.execute_tool(
            "compare_peers", {"scope": "nonsense"}, context=FAKE_CONTEXT
        )
        self.assertFalse(result["ok"])

    def test_search_policy_rejects_blank_query(self):
        result = agent_tools.execute_tool("search_policy", {"query": "  "}, context=FAKE_CONTEXT)
        self.assertFalse(result["ok"])

    def test_search_policy_reports_miss_with_hint(self):
        """检索不到时要给出可操作提示，模型才知道该换关键词重试。"""
        with mock.patch.object(agent_tools.rag, "retrieve_prediction_knowledge", return_value=[]):
            result = agent_tools.execute_tool(
                "search_policy", {"query": "不存在的制度"}, context=FAKE_CONTEXT
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["hitCount"], 0)
        self.assertIn("hint", result)

    def test_search_policy_truncates_snippet(self):
        long_hit = [{"title": "T", "section": "S", "snippet": "长" * 2000, "sourceType": "file"}]
        with mock.patch.object(
            agent_tools.rag, "retrieve_prediction_knowledge", return_value=long_hit
        ):
            result = agent_tools.execute_tool(
                "search_policy", {"query": "学籍"}, context=FAKE_CONTEXT
            )
        self.assertLessEqual(
            len(result["results"][0]["snippet"]), agent_tools.MAX_SNIPPET_CHARS
        )

    def test_retrieval_exception_does_not_propagate(self):
        """工具内部异常必须转成结构化错误，否则整轮对话直接失败。"""
        with mock.patch.object(
            agent_tools.rag, "retrieve_prediction_knowledge", side_effect=RuntimeError("boom")
        ):
            result = agent_tools.execute_tool(
                "search_policy", {"query": "学籍"}, context=FAKE_CONTEXT
            )
        self.assertFalse(result["ok"])
        self.assertIn("boom", result["error"])

    def test_unknown_tool_lists_available(self):
        result = agent_tools.execute_tool("no_such_tool", {}, context=FAKE_CONTEXT)
        self.assertFalse(result["ok"])
        self.assertIn("search_policy", result["error"])

    def test_bad_argument_name_is_reported(self):
        result = agent_tools.execute_tool(
            "search_policy", {"wrong_kwarg": 1}, context=FAKE_CONTEXT
        )
        self.assertFalse(result["ok"])

    def test_list_warnings_without_student_id(self):
        result = agent_tools.execute_tool("list_warnings", {}, context={"student": {}})
        self.assertFalse(result["ok"])

    def test_list_warnings_empty_db(self):
        result = agent_tools.execute_tool("list_warnings", {}, context=FAKE_CONTEXT)
        self.assertTrue(result["ok"])
        self.assertEqual(result["hitCount"], 0)


@override_settings(
    PREDICTION_AGENT_ENABLED=True,
    PREDICTION_LLM_ENABLED=True,
    PREDICTION_LLM_API_KEY="test-key",
    PREDICTION_LLM_MODEL="fake-model",
    PREDICTION_AGENT_MAX_STEPS=3,
)
class AgentLoopTests(TestCase):
    """循环与协议。这里的断言对应真实踩过的两个 400。"""

    def test_single_tool_then_finalize(self):
        with mock.patch.object(
            llm,
            "stream_chat_messages",
            side_effect=scripted_rounds([
                [done_event("", tool_calls=[tool_call("list_warnings", {})])],
            ]),
        ):
            result = agent.run_prediction_chat_agent(
                context=FAKE_CONTEXT, question="有预警吗？"
            )
        self.assertTrue(result["used"])
        self.assertEqual(result["answer"]["directAnswer"], GOOD_ANSWER["directAnswer"])
        self.assertEqual(result["trace"]["steps"][0]["tool"], "list_warnings")

    def test_every_tool_call_id_gets_a_reply(self):
        """协议要求：assistant.tool_calls 里每个 id 都要有 role=tool 回复。

        并发上限裁剪若发生在写入 assistant 消息之后，就会漏掉回复，
        下一轮直接 400 insufficient tool messages。
        """
        many = [
            tool_call("get_student_snapshot", {}, call_id=f"call_{i}")
            for i in range(agent.MAX_TOOL_CALLS_PER_STEP + 3)
        ]
        captured = {}

        def capture(**kwargs):
            captured.setdefault("messages", kwargs.get("messages"))
            # 第一轮发一堆 tool_calls，第二轮收尾
            if "first_done" not in captured:
                captured["first_done"] = True
                return fake_stream([done_event("", tool_calls=many)])()
            captured["final_messages"] = list(kwargs.get("messages") or [])
            return fake_stream([done_event(GOOD_JSON)])()

        with mock.patch.object(llm, "stream_chat_messages", side_effect=capture):
            agent.run_prediction_chat_agent(context=FAKE_CONTEXT, question="画像如何？")

        messages = captured["final_messages"]
        assistant = next(m for m in messages if m.get("tool_calls"))
        declared = {c["id"] for c in assistant["tool_calls"]}
        replied = {m.get("tool_call_id") for m in messages if m.get("role") == "tool"}
        self.assertEqual(declared, replied)
        self.assertLessEqual(len(declared), agent.MAX_TOOL_CALLS_PER_STEP)

    def test_reasoning_content_is_passed_back(self):
        """thinking 模式下不回传 reasoning_content，下一轮会 400。"""
        captured = {}

        def capture(**kwargs):
            if "first" not in captured:
                captured["first"] = True
                return fake_stream([
                    done_event(
                        "",
                        tool_calls=[tool_call("list_warnings", {})],
                        reasoning="我需要先查预警",
                    )
                ])()
            captured["messages"] = list(kwargs.get("messages") or [])
            return fake_stream([done_event(GOOD_JSON)])()

        with mock.patch.object(llm, "stream_chat_messages", side_effect=capture):
            agent.run_prediction_chat_agent(context=FAKE_CONTEXT, question="有预警吗？")

        assistant = next(m for m in captured["messages"] if m.get("tool_calls"))
        self.assertEqual(assistant.get("reasoning_content"), "我需要先查预警")

    def test_identical_tool_calls_are_cached(self):
        same = [tool_call("get_student_snapshot", {}, call_id="a"),
                tool_call("get_student_snapshot", {}, call_id="b")]
        with mock.patch.object(
            llm,
            "stream_chat_messages",
            side_effect=scripted_rounds([
                [done_event("", tool_calls=same)],
            ]),
        ):
            result = agent.run_prediction_chat_agent(
                context=FAKE_CONTEXT, question="画像如何？"
            )
        cached_flags = [s["cached"] for s in result["trace"]["steps"]]
        self.assertEqual(cached_flags, [False, True])

    def test_max_steps_is_enforced(self):
        """模型一直要求调工具时，必须在 maxSteps 处停下来收尾。"""
        loop_event = fake_stream(
            [done_event("", tool_calls=[tool_call("search_policy", {"query": "学籍"})])]
        )

        call_count = {"n": 0}

        def never_satisfied(**_kwargs):
            call_count["n"] += 1
            # 最后一次是 finalize，返回 JSON
            if call_count["n"] > 3:
                return fake_stream([done_event(GOOD_JSON)])()
            return loop_event()

        with mock.patch.object(llm, "stream_chat_messages", side_effect=never_satisfied):
            result = agent.run_prediction_chat_agent(
                context=FAKE_CONTEXT, question="制度规定是什么？"
            )
        self.assertEqual(result["trace"]["stopReason"], "max_steps_reached")
        self.assertTrue(result["used"])

    def test_finalize_non_json_reports_unused(self):
        """收尾输出无法解析时要返回 used=False，让上层回落规则兜底。"""
        with mock.patch.object(
            llm,
            "stream_chat_messages",
            side_effect=scripted_rounds(
                [[done_event("", tool_calls=[tool_call("list_warnings", {})])]],
                default=[done_event("这不是 JSON")],
            ),
        ):
            result = agent.run_prediction_chat_agent(
                context=FAKE_CONTEXT, question="有预警吗？"
            )
        self.assertFalse(result["used"])
        self.assertEqual(result["reason"], "invalid_json_text")

    def test_first_round_error_gives_up_cleanly(self):
        with mock.patch.object(
            llm,
            "stream_chat_messages",
            side_effect=[fake_stream([{"type": "error", "reason": "http_401"}])()],
        ):
            result = agent.run_prediction_chat_agent(
                context=FAKE_CONTEXT, question="有预警吗？"
            )
        self.assertFalse(result["used"])
        self.assertEqual(result["reason"], "http_401")

    def test_stream_emits_tool_progress_events(self):
        with mock.patch.object(
            llm,
            "stream_chat_messages",
            side_effect=scripted_rounds(
                [[
                    {"type": "reasoning", "text": "想一下"},
                    done_event("", tool_calls=[tool_call("list_warnings", {})]),
                ]],
                default=[
                    {"type": "delta", "text": '{"direct'},
                    done_event(GOOD_JSON),
                ],
            ),
        ):
            events = list(
                agent.stream_prediction_chat_agent(
                    context=FAKE_CONTEXT, question="有预警吗？"
                )
            )
        kinds = [e["type"] for e in events]
        self.assertIn("status", kinds)
        self.assertIn("tool_start", kinds)
        self.assertIn("tool_result", kinds)
        self.assertIn("answer_delta", kinds)  # 收尾轮正文走 answer_delta
        self.assertEqual(kinds[-1], "final")
        self.assertTrue(events[-1]["used"])

    def test_finalize_lowers_reasoning_effort(self):
        """收尾只是打包 JSON，不该再用 high effort（会超时）。"""
        seen = []

        def capture(**kwargs):
            seen.append(kwargs.get("runtime_options") or {})
            if len(seen) == 1:
                return fake_stream([done_event("", tool_calls=[tool_call("list_warnings", {})])])()
            return fake_stream([done_event(GOOD_JSON)])()

        with mock.patch.object(llm, "stream_chat_messages", side_effect=capture):
            agent.run_prediction_chat_agent(context=FAKE_CONTEXT, question="有预警吗？")

        self.assertEqual(seen[-1].get("reasoningEffort"), "low")
        self.assertEqual(seen[-1].get("thinkingType"), "disabled")


class AgentBudgetTests(SimpleTestCase):
    @override_settings(PREDICTION_AGENT_MAX_STEPS=3, PREDICTION_AGENT_TIME_BUDGET_SECONDS=120)
    def test_defaults_from_settings(self):
        budget = agent.resolve_agent_budget({})
        self.assertEqual(budget["maxSteps"], 3)
        self.assertEqual(budget["timeBudgetSeconds"], 120)

    def test_values_are_clamped(self):
        self.assertEqual(agent.resolve_agent_budget({"maxSteps": 999})["maxSteps"], 6)
        self.assertEqual(agent.resolve_agent_budget({"maxSteps": 0})["maxSteps"], 3)
        self.assertEqual(
            agent.resolve_agent_budget({"timeBudgetSeconds": 9999})["timeBudgetSeconds"], 300
        )
        self.assertEqual(
            agent.resolve_agent_budget({"timeBudgetSeconds": 1})["timeBudgetSeconds"], 15
        )

    def test_garbage_budget_falls_back_to_default(self):
        self.assertEqual(agent.resolve_agent_budget({"maxSteps": "abc"})["maxSteps"], 3)

    @override_settings(PREDICTION_AGENT_ENABLED=False)
    def test_disabled_by_setting(self):
        self.assertFalse(agent.agent_enabled({}))

    @override_settings(
        PREDICTION_AGENT_ENABLED=True,
        PREDICTION_LLM_ENABLED=True,
        PREDICTION_LLM_API_KEY="k",
        PREDICTION_LLM_MODEL="m",
    )
    def test_use_agent_false_disables(self):
        self.assertTrue(agent.agent_enabled({}))
        self.assertFalse(agent.agent_enabled({"useAgent": False}))


class PartialAnswerExtractionTests(SimpleTestCase):
    """收尾轮逐字输出。

    症状曾是"长时间显示正在思考"：收尾轮流下来的是 JSON 片段，
    前端拿不到可展示文本，界面在这十几秒里完全静止。
    """

    def extract(self, buffer):
        return agent.extract_partial_string_field(buffer, "directAnswer")

    def test_partial_value_is_returned_before_closing_quote(self):
        text, closed = self.extract('{"directAnswer": "该生暂无')
        self.assertEqual(text, "该生暂无")
        self.assertFalse(closed)

    def test_closed_value_is_flagged(self):
        text, closed = self.extract('{"directAnswer": "完整内容"')
        self.assertEqual(text, "完整内容")
        self.assertTrue(closed)

    def test_works_without_space_after_colon(self):
        text, closed = self.extract('{"directAnswer":"无空格"')
        self.assertEqual(text, "无空格")
        self.assertTrue(closed)

    def test_field_not_in_first_position(self):
        text, closed = self.extract('{"reasoning": ["x"], "directAnswer": "后出现"')
        self.assertEqual(text, "后出现")
        self.assertTrue(closed)

    def test_escaped_quote_does_not_end_value(self):
        text, closed = self.extract('{"directAnswer": "带\\"引号\\"的"')
        self.assertEqual(text, '带"引号"的')
        self.assertTrue(closed)

    def test_escaped_newline_is_unescaped(self):
        text, _ = self.extract('{"directAnswer": "第一行\n第二行"')
        self.assertEqual(text, "第一行\n第二行")

    def test_incomplete_prefixes_yield_nothing(self):
        for buffer in ('', '{"dir', '{"directAnswer": ', '{"directAnswer": "'):
            text, closed = self.extract(buffer)
            self.assertEqual(text, "", buffer)
            self.assertFalse(closed, buffer)

    def test_growth_is_monotonic_across_chunks(self):
        """模拟逐块到达，断言抽出的文本只增不减、不回退。"""
        full = '{"directAnswer": "该生存在一定的延期毕业风险。", "reasoning": []}'
        seen = []
        for size in range(1, len(full) + 1):
            text, _ = self.extract(full[:size])
            if text:
                seen.append(text)
        for earlier, later in zip(seen, seen[1:]):
            self.assertTrue(later.startswith(earlier), f"{earlier!r} -> {later!r}")
        self.assertEqual(seen[-1], "该生存在一定的延期毕业风险。")


@override_settings(
    PREDICTION_AGENT_ENABLED=True,
    PREDICTION_LLM_ENABLED=True,
    PREDICTION_LLM_API_KEY="test-key",
    PREDICTION_LLM_MODEL="fake-model",
)
class StreamAnswerTextEventTests(TestCase):
    def test_answer_text_events_are_emitted_incrementally(self):
        chunks = ['{"directAnswer": "该生', '暂无风险。", ', '"reasoning": [], "actionPlan": [], "citations": []}']
        finalize_events = [{"type": "delta", "text": c} for c in chunks]
        finalize_events.append(done_event("".join(chunks)))

        with mock.patch.object(
            llm,
            "stream_chat_messages",
            side_effect=scripted_rounds(
                [[done_event("", tool_calls=[tool_call("list_warnings", {})])]],
                default=finalize_events,
            ),
        ):
            events = list(
                agent.stream_prediction_chat_agent(
                    context=FAKE_CONTEXT, question="有风险吗？"
                )
            )

        texts = [e["text"] for e in events if e["type"] == "answer_text"]
        self.assertTrue(texts, "收尾轮必须产出 answer_text，否则前端无字可显示")
        self.assertEqual(texts[-1], "该生暂无风险。")
        # 必须是"逐步变长"，不能一次性只给完整版
        for earlier, later in zip(texts, texts[1:]):
            self.assertTrue(later.startswith(earlier))
        self.assertTrue(events[-1]["used"])


class StreamTerminationTests(SimpleTestCase):
    """上游不发 [DONE] 时必须自行收口，否则会空等到 read timeout。"""

    @override_settings(
        PREDICTION_LLM_ENABLED=True,
        PREDICTION_LLM_API_KEY="k",
        PREDICTION_LLM_MODEL="m",
        PREDICTION_LLM_TIMEOUT_SECONDS=5,
    )
    def test_usage_only_chunk_after_finish_breaks_loop(self):
        sse_lines = [
            b'data: {"id":"1","model":"m","choices":[{"index":0,"delta":{"content":"hi"}}]}\n',
            b'data: {"id":"1","model":"m","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n',
            # 收尾统计块，之后上游"忘了"发 [DONE]
            b'data: {"id":"1","model":"m","choices":[],"usage":{"total_tokens":7}}\n',
        ]

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def __iter__(self):
                # 生成完上面三行后就不再产出，若实现依赖 [DONE] 会卡在这里
                return iter(sse_lines)

        class FakeOpener:
            def open(self, *args, **kwargs):
                return FakeResponse()

        with mock.patch.object(llm, "build_llm_opener", return_value=FakeOpener()):
            events = list(
                llm.stream_chat_messages(
                    messages=[{"role": "user", "content": "hi"}]
                )
            )

        kinds = [e["type"] for e in events]
        self.assertIn("done", kinds)
        self.assertNotIn("error", kinds)
        done = events[-1]
        self.assertEqual(done["message"]["content"], "hi")
        self.assertEqual(done["finishReason"], "stop")
        self.assertEqual((done.get("usage") or {}).get("total_tokens"), 7)


class PartialArrayExtractionTests(SimpleTestCase):
    """收尾被中断时抢救 reasoning / actionPlan 的已完成项。"""

    def extract(self, buffer):
        return agent.extract_partial_array_strings(buffer, "reasoning")

    def test_complete_items(self):
        self.assertEqual(
            self.extract('{"reasoning": ["第一条", "第二条"], "x": 1'),
            ["第一条", "第二条"],
        )

    def test_half_written_item_is_dropped(self):
        self.assertEqual(self.extract('{"reasoning": ["第一条", "第二'), ["第一条"])

    def test_escaped_quote_inside_item(self):
        self.assertEqual(self.extract('{"reasoning": ["带\\"引号\\""]'), ['带"引号"'])

    def test_empty_or_missing(self):
        for buffer in ('{"reasoning": [', '{"reasoning": []', '{"other": ["a"]', ''):
            self.assertEqual(self.extract(buffer), [], buffer)


@override_settings(
    PREDICTION_AGENT_ENABLED=True,
    PREDICTION_LLM_ENABLED=True,
    PREDICTION_LLM_API_KEY="test-key",
    PREDICTION_LLM_MODEL="fake-model",
)
class FinalizeSalvageTests(TestCase):
    """收尾轮中断后必须抢救已写出的答案，而不是整轮判失败重跑。

    线上表现：answer_text 已出 40+ 片（答案其实写完了），却因最后一块
    超时被丢弃，上层再跑一遍单次 pipeline，总耗时 90s+50s≈142s。
    """

    def test_salvages_closed_direct_answer_on_interrupt(self):
        partial = (
            '{"directAnswer": "该生存在较高延期风险。", '
            '"reasoning": ["学分完成率偏低", "科研进度滞后", "任务逾'
        )
        finalize_events = [
            {"type": "delta", "text": partial},
            {"type": "error", "reason": "stream_interrupted", "error": "timed out"},
        ]
        with mock.patch.object(
            llm,
            "stream_chat_messages",
            side_effect=scripted_rounds(
                [[done_event("", tool_calls=[tool_call("list_warnings", {})])]],
                default=finalize_events,
            ),
        ):
            result = agent.run_prediction_chat_agent(
                context=FAKE_CONTEXT, question="有风险吗？"
            )

        self.assertTrue(result["used"], "directAnswer 已闭合时应抢救成功")
        self.assertEqual(result["answer"]["directAnswer"], "该生存在较高延期风险。")
        # 半截的第三条要丢掉，只保留写完的两条
        self.assertEqual(result["answer"]["reasoning"], ["学分完成率偏低", "科研进度滞后"])
        self.assertIn("salvaged_after", result["trace"]["finalizeReason"])

    def test_gives_up_when_direct_answer_incomplete(self):
        """directAnswer 还没写完就断了，没什么可抢救的，应如实返回失败。"""
        finalize_events = [
            {"type": "delta", "text": '{"directAnswer": "该生存在'},
            {"type": "error", "reason": "stream_interrupted", "error": "timed out"},
        ]
        with mock.patch.object(
            llm,
            "stream_chat_messages",
            side_effect=scripted_rounds(
                [[done_event("", tool_calls=[tool_call("list_warnings", {})])]],
                default=finalize_events,
            ),
        ):
            result = agent.run_prediction_chat_agent(
                context=FAKE_CONTEXT, question="有风险吗？"
            )
        self.assertFalse(result["used"])
        self.assertEqual(result["reason"], "stream_interrupted")

    def test_finalize_uses_shorter_timeout(self):
        seen = []

        def capture(**kwargs):
            seen.append(kwargs.get("runtime_options") or {})
            if len(seen) == 1:
                return fake_stream([done_event("", tool_calls=[tool_call("list_warnings", {})])])()
            return fake_stream([done_event(GOOD_JSON)])()

        with mock.patch.object(llm, "stream_chat_messages", side_effect=capture):
            agent.run_prediction_chat_agent(context=FAKE_CONTEXT, question="有风险吗？")

        self.assertEqual(
            seen[-1].get("timeoutSeconds"), agent.FINALIZE_TIMEOUT_SECONDS
        )
        self.assertLess(agent.FINALIZE_TIMEOUT_SECONDS, 90)


class TimeoutOverrideTests(SimpleTestCase):
    @override_settings(PREDICTION_LLM_TIMEOUT_SECONDS=90)
    def test_runtime_option_overrides_setting(self):
        self.assertEqual(llm.resolve_llm_runtime_options({})["timeout_seconds"], 90)
        self.assertEqual(
            llm.resolve_llm_runtime_options({"timeoutSeconds": 30})["timeout_seconds"], 30
        )


class PredictionDataSourceTests(TestCase):
    """真实快照与公式推算样本必须能区分，否则会把推算值当实测值解读。"""

    def test_virtual_snapshot_is_flagged(self):
        from types import SimpleNamespace

        virtual = SimpleNamespace(is_virtual=True)
        measured = SimpleNamespace(is_virtual=False)
        context = {
            "student": {"studentId": "x", "name": "n", "grade": "", "major": "",
                        "degreeType": "", "college": "", "advisorName": "",
                        "currentStatus": ""},
            "prediction": {},
            "derived": {},
            "peerReferences": {"sameGrade": {}},
            "currentSnapshot": {},
            "monthlyMetrics": {},
        }
        from apps.graduate import services

        v = services.prediction_compose_student_payload(virtual, context)
        m = services.prediction_compose_student_payload(measured, context)
        self.assertEqual(v["dataSource"], "virtual")
        self.assertFalse(v["hasMeasuredSnapshot"])
        self.assertEqual(m["dataSource"], "measured")
        self.assertTrue(m["hasMeasuredSnapshot"])
