"""智能预测 Agent 循环。

与原来的单次 pipeline 的本质区别：检索关键词由模型自己决定，
且允许「查得不够 -> 换个词再查」，最后才输出结构化答案。

循环结构（ReAct 风格的 tool-use loop）：
    system(含工具使用纪律) + user(问题 + 画像摘要)
      -> 模型决定：调工具 or 直接作答
      -> 执行工具、把结果以 role=tool 追加回消息历史
      -> 重复，直到模型不再调工具 或 触达轮次/时间预算
      -> 最后强制一轮 JSON 收尾，产出既有 schema

护栏（缺一个都会在生产上出问题）：
  - max_steps：最多工具调用轮数，防止模型反复检索打转；
  - 时间预算：累计耗时超限立即收尾，避免前端长时间挂住；
  - 单轮工具并发数上限：模型可能一次发多个 tool_calls；
  - 工具调用去重：同样的参数重复调用直接复用上次结果；
  - 任何异常/预算耗尽都走 finalize，再不行回落到既有规则兜底。
"""

import json
import logging
import time

from django.conf import settings

from apps.graduate import agent_tools, llm


logger = logging.getLogger(__name__)

DEFAULT_MAX_STEPS = 3
DEFAULT_TIME_BUDGET_SECONDS = 120
MAX_TOOL_CALLS_PER_STEP = 4
# 收尾轮不做深度推理，正常 2~5s 写完；给足余量但远小于整轮超时，
# 避免上游卡住时白等满 90s 再回落，总耗时冲到 140s+。
FINALIZE_TIMEOUT_SECONDS = 30

AGENT_SYSTEM_PROMPT = """你是高校研究生培养管理的智能分析助手，服务对象是研究生院管理人员与导师。

你可以调用工具获取信息。工具使用纪律：
1. 凡涉及制度规定、评审条件、办理流程、材料要求的问题，必须先调用 search_policy 获取原文，禁止凭记忆陈述条款。
2. 如果 search_policy 返回的片段不足以回答（例如只有部分条件、缺少量化标准），应更换更具体的关键词再检索一次，而不是直接下结论。
3. 需要结合该生实际情况判断时，调用 get_student_snapshot；需要判断其所处水位时，调用 compare_peers；问到预警情况时调用 list_warnings。
4. 信息已经足够时就不要再调用工具，直接给出答案。

回答纪律：
- 制度性结论必须有检索到的原文支撑，并在 citations 中列出来源；没有检索到原文就明确说明「未检索到制度依据」，不要编造条款或文件名。
- 区分「数据事实」与「推断建议」，不要把推断表述成规定。
- 面向管理人员，给出可执行的后续动作。
- 使用简体中文作答。"""

FINALIZE_INSTRUCTION = """现在请基于以上全部信息输出最终答案。

只输出一个 JSON 对象，不要包裹 markdown 代码块，不要输出任何额外文字：
{
  "directAnswer": "直接结论，2-4 句",
  "reasoning": ["推理依据，每条一句"],
  "actionPlan": ["建议动作，每条一句"],
  "citations": [{"title": "文件名", "section": "章节", "snippet": "原文片段"}]
}

citations 只填写本轮 search_policy 实际返回过的内容；没有检索到制度依据时填空数组 []。"""


def extract_partial_string_field(buffer, field):
    """从"还没写完"的 JSON 文本里增量取出某个字符串字段的当前内容。

    收尾轮流式下来的是 JSON 片段（`{"directAnswer": "该生当...`），
    直接展示会露出括号和键名，但等整段写完再展示又会让界面静止十几秒。
    所以这里只认一件事：找到 "<field>": " 之后、收尾引号之前的部分，
    并正确处理转义（\\" 不算结束，\\n 还原成换行）。

    返回 (text, closed)：closed=True 表示该字段已经写完。
    解析不出来就返回 ("", False)，调用方按"还没开始"处理。
    """
    marker = f'"{field}"'
    start = buffer.find(marker)
    if start == -1:
        return "", False

    cursor = buffer.find(":", start + len(marker))
    if cursor == -1:
        return "", False
    cursor += 1

    # 跳过冒号后的空白，定位开引号
    while cursor < len(buffer) and buffer[cursor] in " \t\r\n":
        cursor += 1
    if cursor >= len(buffer) or buffer[cursor] != '"':
        return "", False
    cursor += 1

    chars = []
    escaped = False
    while cursor < len(buffer):
        char = buffer[cursor]
        if escaped:
            chars.append({"n": "\n", "t": "\t", "r": "\r"}.get(char, char))
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == '"':
            return "".join(chars), True
        else:
            chars.append(char)
        cursor += 1

    # 走到末尾仍未闭合：说明还在写，返回目前已有的部分
    return "".join(chars), False


def extract_partial_array_strings(buffer, field):
    """从未写完的 JSON 里取出某个字符串数组里已经写完的元素。

    与 extract_partial_string_field 配套，用于收尾轮被中断时抢救
    reasoning / actionPlan：只收集已经闭合的元素，半截的那条丢掉。
    """
    marker = f'"{field}"'
    start = buffer.find(marker)
    if start == -1:
        return []

    cursor = buffer.find("[", start + len(marker))
    if cursor == -1:
        return []
    cursor += 1

    items = []
    chars = []
    in_string = False
    escaped = False
    while cursor < len(buffer):
        char = buffer[cursor]
        if in_string:
            if escaped:
                chars.append({"n": "\n", "t": "\t", "r": "\r"}.get(char, char))
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                items.append("".join(chars))
                chars = []
                in_string = False
            else:
                chars.append(char)
        elif char == '"':
            in_string = True
        elif char == "]":
            break
        cursor += 1
    return items


def build_stream_answer_preview(buffer):
    """只展示可确认的答案字段，已完成的依据和建议无需等待整个 JSON 收尾。"""
    direct, closed = extract_partial_string_field(buffer, "directAnswer")
    if not closed:
        return ''
    blocks = [direct]
    for field, label in (("reasoning", "判断依据"), ("actionPlan", "建议动作")):
        items = extract_partial_array_strings(buffer, field)
        if items:
            blocks.append(f"{label}：" + '；'.join(items))
    return '\n\n'.join(blocks)


def agent_enabled(runtime_options=None):
    runtime_options = runtime_options or {}
    if runtime_options.get("useAgent") is False:
        return False
    if not getattr(settings, "PREDICTION_AGENT_ENABLED", False):
        return False
    return llm.prediction_llm_is_enabled(runtime_options)


def resolve_agent_budget(runtime_options=None):
    runtime_options = runtime_options or {}
    max_steps = runtime_options.get("maxSteps") or getattr(
        settings, "PREDICTION_AGENT_MAX_STEPS", DEFAULT_MAX_STEPS
    )
    time_budget = runtime_options.get("timeBudgetSeconds") or getattr(
        settings, "PREDICTION_AGENT_TIME_BUDGET_SECONDS", DEFAULT_TIME_BUDGET_SECONDS
    )
    try:
        max_steps = max(1, min(int(max_steps), 6))
    except (TypeError, ValueError):
        max_steps = DEFAULT_MAX_STEPS
    try:
        time_budget = max(15, min(int(time_budget), 300))
    except (TypeError, ValueError):
        time_budget = DEFAULT_TIME_BUDGET_SECONDS
    return {"maxSteps": max_steps, "timeBudgetSeconds": time_budget}


def build_agent_user_prompt(*, context, question, chat_history):
    student = context.get("student") or {}
    prediction = context.get("prediction") or {}
    history_lines = [
        f"{item.get('role', '')}: {item.get('content', '')}"
        for item in (chat_history or [])[-4:]
    ]
    history_text = "\n".join(history_lines) or "无"
    return (
        f"当前学生：{student.get('name', '')}（{student.get('grade', '')} "
        f"{student.get('major', '')} {student.get('degreeType', '')}）\n"
        f"系统初判风险等级：{prediction.get('riskLevel', '未知')}\n"
        f"系统初判风险领域：{prediction.get('riskField', '无')}\n\n"
        f"最近对话：\n{history_text}\n\n"
        f"管理人员的问题：{question}"
    )


def rebuild_assistant_message(message, *, tool_calls=None):
    """把模型返回的 assistant 消息重新组装后回填进历史。

    thinking 模式下 deepseek 要求把 reasoning_content 一并传回，
    否则下一轮会报 "The `reasoning_content` in the thinking mode must be
    passed back to the API."。这里原样保留该字段（只在存在时附带），
    并允许裁剪后的 tool_calls 覆盖原值。
    """
    rebuilt = {
        "role": "assistant",
        "content": message.get("content") or "",
    }
    reasoning_content = message.get("reasoning_content")
    if reasoning_content:
        rebuilt["reasoning_content"] = reasoning_content
    if tool_calls:
        rebuilt["tool_calls"] = tool_calls
    return rebuilt


def stream_prediction_chat_agent(*, context, question, chat_history=None, runtime_options=None):
    """Agent 循环的流式实现，逐步 yield 过程事件。

    这是循环的唯一实现，run_prediction_chat_agent 只是把它抽干后取最后一个
    final 事件 —— 避免流式与非流式两份循环逻辑各自演化、行为逐渐不一致。

    产出事件：
      {"type":"status","stage":"thinking"|"finalizing","step":n}
      {"type":"reasoning","text":...}            思考增量（可做"正在思考"指示）
      {"type":"delta","text":...}                中间轮自然语言增量
      {"type":"tool_start","tool":...,"arguments":...}
      {"type":"tool_result","tool":...,"ok":...,"hitCount":...}
      {"type":"answer_delta","text":...}         收尾轮 JSON 原文增量
      {"type":"final","used":...,"answer":...,"trace":...}

    注意 answer_delta 是 JSON 片段而非可直接展示的文本；前端应以 final 里
    解析好的 answer 为准，answer_delta 仅适合做"正在生成"的进度提示。
    """
    budget = resolve_agent_budget(runtime_options)
    started_at = time.monotonic()
    trace_steps = []
    tool_cache = {}
    citations_pool = []

    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_agent_user_prompt(
                context=context, question=question, chat_history=chat_history
            ),
        },
    ]

    def elapsed():
        return time.monotonic() - started_at

    def budget_exhausted():
        return elapsed() >= budget["timeBudgetSeconds"]

    stop_reason = "completed"

    for step in range(1, budget["maxSteps"] + 1):
        if budget_exhausted():
            stop_reason = "time_budget_exhausted"
            break

        yield {"type": "status", "stage": "thinking", "step": step}

        result = {}
        stream_error = None
        for event in llm.stream_chat_messages(
            messages=messages,
            runtime_options=runtime_options,
            tools=agent_tools.PREDICTION_AGENT_TOOLS,
        ):
            kind = event.get("type")
            if kind == "reasoning":
                yield {"type": "reasoning", "text": event.get("text", "")}
            elif kind == "delta":
                yield {"type": "delta", "text": event.get("text", "")}
            elif kind == "done":
                result = event
            elif kind == "error":
                stream_error = event

        if stream_error or not result:
            reason = (stream_error or {}).get("reason", "llm_error")
            # 中间轮失败：若已拿到工具结果仍可收尾，否则整体放弃
            stop_reason = f"llm_error:{reason}"
            if not trace_steps:
                yield {
                    "type": "final",
                    "used": False,
                    "reason": reason,
                    "answer": None,
                    "trace": {"steps": [], "stopReason": stop_reason},
                }
                return
            break

        message = result.get("message") or {}
        tool_calls = message.get("tool_calls") or []

        if not tool_calls:
            # 模型认为信息已足够，进入收尾
            messages.append(rebuild_assistant_message(message))
            stop_reason = "model_finished"
            break

        # 并发上限必须在写入 assistant 消息之前裁剪：
        # 协议要求 assistant.tool_calls 里的每个 tool_call_id 都要有对应的
        # role=tool 回复，否则下一轮直接 400。只执行前 N 个却保留全部 id，
        # 就会出现 "insufficient tool messages following tool_calls"。
        accepted_calls = tool_calls[:MAX_TOOL_CALLS_PER_STEP]

        # 保留 assistant 的 tool_calls 消息，否则 tool 结果无法对齐
        messages.append(rebuild_assistant_message(message, tool_calls=accepted_calls))

        for call in accepted_calls:
            function = call.get("function") or {}
            name = function.get("name") or ""
            raw_args = function.get("arguments") or "{}"
            try:
                arguments = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)
            except (json.JSONDecodeError, TypeError, ValueError):
                arguments = {}

            yield {"type": "tool_start", "tool": name, "arguments": arguments}

            cache_key = (name, json.dumps(arguments, sort_keys=True, ensure_ascii=False))
            if cache_key in tool_cache:
                payload = tool_cache[cache_key]
                cached = True
            else:
                payload = agent_tools.execute_tool(name, arguments, context=context)
                tool_cache[cache_key] = payload
                cached = False

            yield {
                "type": "tool_result",
                "tool": name,
                "ok": bool(payload.get("ok")),
                "cached": cached,
                "hitCount": payload.get("hitCount"),
                "error": payload.get("error", ""),
            }

            if name == "search_policy" and payload.get("ok"):
                for item in payload.get("results") or []:
                    citations_pool.append(
                        {
                            "title": item.get("title", ""),
                            "section": item.get("section", ""),
                            "snippet": item.get("snippet", ""),
                        }
                    )

            trace_steps.append(
                {
                    "step": step,
                    "tool": name,
                    "arguments": arguments,
                    "ok": bool(payload.get("ok")),
                    "cached": cached,
                    "hitCount": payload.get("hitCount"),
                    "error": payload.get("error", ""),
                }
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("id") or "",
                    "content": json.dumps(payload, ensure_ascii=False, default=str),
                }
            )
    else:
        stop_reason = "max_steps_reached"

    # 收尾：强制一轮结构化输出
    yield {"type": "status", "stage": "finalizing", "step": len(trace_steps)}
    messages.append({"role": "user", "content": FINALIZE_INSTRUCTION})

    # 收尾轮只是把已经想明白的结论重新打包成 JSON，不需要再深度推理。
    # 沿用 high effort 会白烧几百个 reasoning token 并经常触发读超时，
    # 所以这里显式降到 low（调用方若明确指定过 reasoningEffort 则尊重其选择）。
    finalize_options = dict(runtime_options or {})
    finalize_options.setdefault("reasoningEffort", "low")
    finalize_options.setdefault("thinkingType", "disabled")
    # 收尾只是打包已有结论，正常 2~5s 就写完。沿用整轮的 90s 超时意味着
    # 上游一卡就白等 90s，再回落单次 pipeline 总耗时会到 140s+。
    finalize_options.setdefault("timeoutSeconds", FINALIZE_TIMEOUT_SECONDS)

    final = {}
    final_error = None
    answer_buffer = ""
    emitted_answer = ""
    emitted_preview = ""
    for event in llm.stream_chat_messages(
        messages=messages,
        runtime_options=finalize_options,
        response_format={"type": "json_object"},
    ):
        kind = event.get("type")
        if kind == "reasoning":
            yield {"type": "reasoning", "text": event.get("text", "")}
        elif kind == "delta":
            # 收尾轮的正文是 JSON 片段，不能直接展示。
            # 这里顺手把 directAnswer 已写出的部分抽出来，
            # 以 answer_text 事件推给前端做"逐字显示"，
            # 否则界面会在收尾这十几秒里完全静止。
            chunk = event.get("text", "")
            answer_buffer += chunk
            partial, closed = extract_partial_string_field(answer_buffer, "directAnswer")
            if partial and partial != emitted_answer:
                yield {
                    "type": "answer_text",
                    "text": partial,
                    "delta": partial[len(emitted_answer):]
                    if partial.startswith(emitted_answer)
                    else partial,
                    "closed": closed,
                }
                emitted_answer = partial
            preview = build_stream_answer_preview(answer_buffer)
            if preview and preview != emitted_preview:
                yield {"type": "answer_sections", "text": preview}
                emitted_preview = preview
            # 原始片段仍然推送，保留给需要看原文的调试场景
            yield {"type": "answer_delta", "text": chunk}
        elif kind == "done":
            final = event
        elif kind == "error":
            final_error = event

    if final_error or not final:
        reason = (final_error or {}).get("reason", "finalize_failed")
        # 收尾轮中断前往往已经写出大半个 JSON（实测 answer_text 已出 40+ 片）。
        # 直接判失败会让上层重跑一遍单次 pipeline，等于白等一次超时
        # （实测 90s + 50s ≈ 142s）。所以先抢救已到手的内容：
        # 只要 directAnswer 已经写完整，就按正常答案返回。
        salvaged_answer, salvaged_closed = extract_partial_string_field(
            answer_buffer, "directAnswer"
        )
        if salvaged_closed and salvaged_answer:
            logger.warning(
                "Prediction agent finalize interrupted (%s), salvaged directAnswer", reason
            )
            yield {
                "type": "final",
                "used": True,
                "reason": "",
                "answer": {
                    "directAnswer": salvaged_answer,
                    "reasoning": llm.normalize_string_list(
                        extract_partial_array_strings(answer_buffer, "reasoning")
                    ),
                    "actionPlan": llm.normalize_string_list(
                        extract_partial_array_strings(answer_buffer, "actionPlan")
                    ),
                    "citations": [],
                },
                "citationsPool": citations_pool,
                "trace": {
                    "steps": trace_steps,
                    "stopReason": stop_reason,
                    "finalizeReason": f"salvaged_after_{reason}",
                    "toolCallCount": len(trace_steps),
                    "elapsedSeconds": round(elapsed(), 1),
                },
            }
            return

        yield {
            "type": "final",
            "used": False,
            "reason": reason,
            "answer": None,
            "trace": {
                "steps": trace_steps,
                "stopReason": stop_reason,
                "finalizeReason": reason,
                "elapsedSeconds": round(elapsed(), 1),
            },
        }
        return

    raw_text = (final.get("message") or {}).get("content") or ""
    answer = llm.parse_json_payload(
        raw_text, expected_keys=llm.PREDICTION_CHAT_ANSWER_SCHEMA["required"]
    )
    if answer is None:
        logger.warning("Prediction agent finalize returned non-JSON: %s", raw_text[:500])
        yield {
            "type": "final",
            "used": False,
            "reason": "invalid_json_text",
            "answer": None,
            "trace": {
                "steps": trace_steps,
                "stopReason": stop_reason,
                "elapsedSeconds": round(elapsed(), 1),
            },
        }
        return

    yield {
        "type": "final",
        "used": True,
        "reason": "",
        "answer": answer,
        "citationsPool": citations_pool,
        "model": final.get("model", ""),
        "usage": final.get("usage"),
        "responseId": final.get("responseId", ""),
        "trace": {
            "steps": trace_steps,
            "stopReason": stop_reason,
            "toolCallCount": len(trace_steps),
            "elapsedSeconds": round(elapsed(), 1),
        },
    }


def run_prediction_chat_agent(*, context, question, chat_history=None, runtime_options=None):
    """非流式入口：抽干流式循环，返回最后的 final 事件。

    刻意不另写一份循环 —— 两份实现早晚会行为不一致。
    """
    final_event = None
    for event in stream_prediction_chat_agent(
        context=context,
        question=question,
        chat_history=chat_history,
        runtime_options=runtime_options,
    ):
        if event.get("type") == "final":
            final_event = event

    if final_event is None:
        return {
            "used": False,
            "reason": "agent_no_final_event",
            "answer": None,
            "trace": {"steps": [], "stopReason": "no_final_event"},
        }

    result = dict(final_event)
    result.pop("type", None)
    return result
