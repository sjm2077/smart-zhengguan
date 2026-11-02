import json
import logging
from urllib import error, request

from django.conf import settings


logger = logging.getLogger(__name__)

SUPPORTED_API_STYLES = {"responses", "chat_completions"}

# urllib 默认会读取系统/环境变量里的代理设置（HTTP_PROXY / HTTPS_PROXY，
# Windows 下还包括 IE 代理配置）。本机常见的 127.0.0.1:7897 这类代理一旦退出，
# 模型请求就会以 ConnectionRefused 失败，并静默回退成规则话术。
# 这里显式构造 opener：默认绕过系统代理直连，只有在配置了
# PREDICTION_LLM_PROXY 或开启 PREDICTION_LLM_TRUST_ENV_PROXY 时才走代理。
_opener_cache = {}


def build_llm_opener():
    explicit_proxy = str(getattr(settings, "PREDICTION_LLM_PROXY", "") or "").strip()
    trust_env_proxy = bool(getattr(settings, "PREDICTION_LLM_TRUST_ENV_PROXY", False))
    cache_key = (explicit_proxy, trust_env_proxy)
    if cache_key in _opener_cache:
        return _opener_cache[cache_key]

    if explicit_proxy:
        proxy_handler = request.ProxyHandler({"http": explicit_proxy, "https": explicit_proxy})
    elif trust_env_proxy:
        # 交给 urllib 读取环境变量/系统代理
        proxy_handler = request.ProxyHandler()
    else:
        # 空字典 = 不使用任何代理，直连 API
        proxy_handler = request.ProxyHandler({})

    opener = request.build_opener(proxy_handler)
    _opener_cache[cache_key] = opener
    return opener


PREDICTION_CHAT_ANSWER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["directAnswer", "reasoning", "actionPlan", "citations"],
    "properties": {
        "directAnswer": {"type": "string"},
        "reasoning": {
            "type": "array",
            "items": {"type": "string"},
        },
        "actionPlan": {
            "type": "array",
            "items": {"type": "string"},
        },
        "citations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["title", "section", "snippet"],
                "properties": {
                    "title": {"type": "string"},
                    "section": {"type": "string"},
                    "snippet": {"type": "string"},
                },
            },
        },
    },
}

PREDICTION_ANALYSIS_RESULT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary", "sections", "evidence"],
    "properties": {
        "summary": {"type": "string"},
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["title", "content"],
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                },
            },
        },
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["title", "section", "snippet"],
                "properties": {
                    "title": {"type": "string"},
                    "section": {"type": "string"},
                    "snippet": {"type": "string"},
                },
            },
        },
    },
}

CHAT_SCHEMA_GUIDE = (
    "Return only one JSON object with keys directAnswer, reasoning, actionPlan, citations. "
    "reasoning and actionPlan must be arrays of short strings. "
    "citations must be an array of objects with title, section, snippet. "
    "Do not wrap the JSON in markdown."
)

ANALYSIS_SCHEMA_GUIDE = (
    "Return only one JSON object with keys summary, sections, evidence. "
    "sections must be an array of objects with title and content. "
    "evidence must be an array of objects with title, section, snippet. "
    "Do not wrap the JSON in markdown."
)


def prediction_llm_is_enabled(runtime_options=None):
    runtime_options = runtime_options or {}
    if runtime_options.get("useLlmWhenAvailable") is False:
        return False
    return bool(
        getattr(settings, "PREDICTION_LLM_ENABLED", False)
        and getattr(settings, "PREDICTION_LLM_API_KEY", "").strip()
        and resolve_llm_runtime_options(runtime_options)["model"]
    )


def resolve_llm_runtime_options(runtime_options=None):
    runtime_options = runtime_options or {}
    configured_temperature = getattr(settings, "PREDICTION_LLM_TEMPERATURE", None)
    temperature = runtime_options.get("temperature", configured_temperature)
    configured_api_style = getattr(settings, "PREDICTION_LLM_API_STYLE", "responses")
    requested_api_style = str(runtime_options.get("apiStyle") or configured_api_style).strip().lower()
    api_style = requested_api_style if requested_api_style in SUPPORTED_API_STYLES else "responses"
    return {
        "provider": getattr(settings, "PREDICTION_LLM_PROVIDER", "openai"),
        "api_style": api_style,
        "base_url": getattr(settings, "PREDICTION_LLM_BASE_URL", "https://api.openai.com/v1"),
        "api_key": getattr(settings, "PREDICTION_LLM_API_KEY", ""),
        "model": str(runtime_options.get("preferredModel") or getattr(settings, "PREDICTION_LLM_MODEL", "")).strip(),
        "thinking_type": str(
            runtime_options.get("thinkingType") or getattr(settings, "PREDICTION_LLM_THINKING_TYPE", "")
        ).strip(),
        "reasoning_effort": str(
            runtime_options.get("reasoningEffort") or getattr(settings, "PREDICTION_LLM_REASONING_EFFORT", "")
        ).strip(),
        "temperature": float(temperature) if temperature not in ("", None) else None,
        # 允许按调用场景覆盖超时：收尾轮只是打包 JSON，用整轮的 90s
        # 会在上游卡住时白等很久，调用方可以传更短的值。
        "timeout_seconds": int(
            runtime_options.get("timeoutSeconds")
            or getattr(settings, "PREDICTION_LLM_TIMEOUT_SECONDS", 45)
        ),
    }


def invoke_prediction_chat_completion(prompt_package, runtime_options=None):
    return invoke_prediction_structured_completion(
        prompt_package=prompt_package,
        runtime_options=runtime_options,
        schema_name="prediction_chat_answer",
        schema=PREDICTION_CHAT_ANSWER_SCHEMA,
        schema_guide=CHAT_SCHEMA_GUIDE,
    )


def invoke_prediction_analysis_completion(prompt_package, runtime_options=None):
    return invoke_prediction_structured_completion(
        prompt_package=prompt_package,
        runtime_options=runtime_options,
        schema_name="prediction_analysis_result",
        schema=PREDICTION_ANALYSIS_RESULT_SCHEMA,
        schema_guide=ANALYSIS_SCHEMA_GUIDE,
    )


def invoke_prediction_structured_completion(*, prompt_package, runtime_options, schema_name, schema, schema_guide):
    resolved = resolve_llm_runtime_options(runtime_options)
    base_result = {
        "used": False,
        "answer": None,
        "responseId": "",
        "provider": resolved["provider"],
        "apiStyle": resolved["api_style"],
        "model": resolved["model"],
        "usage": None,
    }
    if not prediction_llm_is_enabled(runtime_options):
        return {
            **base_result,
            "reason": "llm_disabled",
        }

    messages = prompt_package.get("messages") or []
    system_prompt = messages[0]["content"] if len(messages) > 0 else ""
    user_prompt = messages[1]["content"] if len(messages) > 1 else ""
    structured_input = prompt_package.get("structuredInput") or {}
    if not user_prompt:
        return {
            **base_result,
            "reason": "prompt_missing",
        }

    request_input = build_request_input(user_prompt, structured_input)
    if resolved["api_style"] == "chat_completions":
        response_payload, request_error = invoke_chat_completions_api(
            resolved=resolved,
            system_prompt=system_prompt,
            user_prompt=request_input,
            schema_guide=schema_guide,
        )
        raw_text = extract_chat_completion_text(response_payload) if response_payload else ""
    else:
        response_payload, request_error = invoke_responses_api(
            resolved=resolved,
            system_prompt=system_prompt,
            user_prompt=request_input,
            schema_name=schema_name,
            schema=schema,
        )
        raw_text = extract_response_text(response_payload) if response_payload else ""

    if request_error:
        return {
            **base_result,
            "reason": request_error["reason"],
            "error": request_error.get("error", ""),
        }

    response_payload = response_payload or {}
    response_model = response_payload.get("model", resolved["model"])
    response_id = response_payload.get("id", "")
    usage = response_payload.get("usage")
    if not raw_text:
        return {
            **base_result,
            "reason": "empty_response_text",
            "responseId": response_id,
            "model": response_model,
            "usage": usage,
        }

    answer = parse_json_payload(raw_text, expected_keys=(schema or {}).get("required"))
    if answer is None:
        logger.warning("Prediction LLM returned non-JSON text: %s", raw_text[:800])
        return {
            **base_result,
            "reason": "invalid_json_text",
            "responseId": response_id,
            "model": response_model,
            "usage": usage,
        }

    return {
        **base_result,
        "used": True,
        "answer": answer,
        "reason": "",
        "responseId": response_id,
        "model": response_model,
        "usage": usage,
    }


def build_request_input(user_prompt, structured_input):
    if not structured_input:
        return user_prompt
    return "\n\n".join(
        [
            user_prompt,
            "Structured input JSON:",
            json.dumps(structured_input, ensure_ascii=False, indent=2),
        ]
    )


def invoke_responses_api(*, resolved, system_prompt, user_prompt, schema_name, schema):
    body = {
        "model": resolved["model"],
        "instructions": system_prompt,
        "input": user_prompt,
        "store": False,
        "text": {
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "schema": schema,
                "strict": True,
            }
        },
    }
    reasoning_effort = resolved["reasoning_effort"]
    if reasoning_effort:
        body["reasoning"] = {"effort": reasoning_effort}

    temperature = resolved["temperature"]
    if temperature is not None:
        body["temperature"] = float(temperature)

    endpoint = f"{resolved['base_url'].rstrip('/')}/responses"
    return post_json(endpoint, body, resolved["api_key"], resolved["timeout_seconds"])


def invoke_chat_messages(*, messages, runtime_options=None, tools=None, response_format=None):
    """面向 Agent 循环的底层调用：直接传入完整 messages，返回原始 message 对象。

    与 invoke_prediction_structured_completion 的区别：
      - 不假设只有 system+user 两条消息，Agent 需要携带 tool_calls / tool 结果历史；
      - 不强制 JSON schema，中间轮次模型要么发工具调用、要么发自然语言；
      - 返回未经归一化的 message，由调用方决定下一步（继续调工具 or 收尾）。
    """
    resolved = resolve_llm_runtime_options(runtime_options)
    base_result = {
        "ok": False,
        "message": None,
        "finishReason": "",
        "provider": resolved["provider"],
        "model": resolved["model"],
        "usage": None,
        "reason": "",
    }
    if not prediction_llm_is_enabled(runtime_options):
        return {**base_result, "reason": "llm_disabled"}
    if not messages:
        return {**base_result, "reason": "prompt_missing"}

    body = {
        "model": resolved["model"],
        "messages": messages,
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    if response_format:
        body["response_format"] = response_format

    reasoning_effort = resolved["reasoning_effort"]
    if reasoning_effort:
        body["reasoning_effort"] = reasoning_effort
    thinking_type = resolved["thinking_type"]
    if thinking_type:
        body["thinking"] = {"type": thinking_type}
    temperature = resolved["temperature"]
    if temperature is not None:
        body["temperature"] = float(temperature)

    endpoint = f"{resolved['base_url'].rstrip('/')}/chat/completions"
    response_payload, request_error = post_json(
        endpoint, body, resolved["api_key"], resolved["timeout_seconds"]
    )
    # 部分网关不支持 response_format，剔除后重试一次
    if request_error and request_error["reason"] == "http_400" and response_format:
        lowered = request_error.get("error", "").lower()
        if "response_format" in lowered or "json_object" in lowered:
            body.pop("response_format", None)
            response_payload, request_error = post_json(
                endpoint, body, resolved["api_key"], resolved["timeout_seconds"]
            )

    if request_error:
        return {
            **base_result,
            "reason": request_error["reason"],
            "error": request_error.get("error", ""),
        }

    response_payload = response_payload or {}
    choices = response_payload.get("choices") or []
    if not choices:
        return {**base_result, "reason": "empty_response_text"}

    choice = choices[0] or {}
    return {
        **base_result,
        "ok": True,
        "message": choice.get("message") or {},
        "finishReason": choice.get("finish_reason", ""),
        "model": response_payload.get("model", resolved["model"]),
        "usage": response_payload.get("usage"),
        "responseId": response_payload.get("id", ""),
    }


def stream_chat_messages(*, messages, runtime_options=None, tools=None, response_format=None):
    """流式版 invoke_chat_messages，逐块 yield 增量。

    产出的事件（dict）：
      {"type": "delta",     "text": "..."}        正文增量
      {"type": "reasoning", "text": "..."}        思考过程增量（可供前端显示"正在思考"）
      {"type": "done",      "message": {...},     完整装配好的 message
                            "finishReason": ...,
                            "usage": ...}
      {"type": "error",     "reason": "...", "error": "..."}

    tool_calls 在流式下是分片到达的（function.arguments 逐字拼接），
    必须按 index 累积后再装配，不能直接取某一块。
    """
    resolved = resolve_llm_runtime_options(runtime_options)
    if not prediction_llm_is_enabled(runtime_options):
        yield {"type": "error", "reason": "llm_disabled", "error": ""}
        return
    if not messages:
        yield {"type": "error", "reason": "prompt_missing", "error": ""}
        return

    body = {
        "model": resolved["model"],
        "messages": messages,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    if response_format:
        body["response_format"] = response_format
    if resolved["reasoning_effort"]:
        body["reasoning_effort"] = resolved["reasoning_effort"]
    if resolved["thinking_type"]:
        body["thinking"] = {"type": resolved["thinking_type"]}
    if resolved["temperature"] is not None:
        body["temperature"] = float(resolved["temperature"])

    endpoint = f"{resolved['base_url'].rstrip('/')}/chat/completions"
    http_request = request.Request(
        endpoint,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {resolved['api_key']}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        method="POST",
    )

    opener = build_llm_opener()
    content_parts = []
    reasoning_parts = []
    tool_call_buffer = {}
    finish_reason = ""
    usage = None
    response_id = ""
    response_model = resolved["model"]

    try:
        response = opener.open(http_request, timeout=resolved["timeout_seconds"])
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        logger.warning("Prediction LLM stream HTTP error: %s %s", exc.code, detail[:800])
        yield {"type": "error", "reason": f"http_{exc.code}", "error": detail[:800]}
        return
    except Exception as exc:
        logger.warning("Prediction LLM stream failed: %s", exc)
        yield {"type": "error", "reason": "request_failed", "error": str(exc)}
        return

    try:
        with response:
            for raw_line in response:
                line = raw_line.decode("utf-8", errors="ignore").strip()
                if not line or not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                try:
                    chunk = json.loads(payload)
                except json.JSONDecodeError:
                    continue

                if chunk.get("usage"):
                    usage = chunk["usage"]
                response_id = chunk.get("id") or response_id
                response_model = chunk.get("model") or response_model

                choices = chunk.get("choices") or []
                if not choices:
                    # 带 usage 但不带 choices 的块是收尾统计块。
                    # 正文已经结束时就不要再等 [DONE]：上游偶发不发这一行，
                    # 继续 for 下去会一直阻塞到 read timeout（实测白等 90s）。
                    if usage and finish_reason:
                        break
                    continue
                choice = choices[0] or {}
                finish_reason = choice.get("finish_reason") or finish_reason
                delta = choice.get("delta") or {}

                text = delta.get("content")
                if text:
                    content_parts.append(text)
                    yield {"type": "delta", "text": text}

                reasoning = delta.get("reasoning_content")
                if reasoning:
                    reasoning_parts.append(reasoning)
                    yield {"type": "reasoning", "text": reasoning}

                # tool_calls 分片累积：按 index 合并 id/name/arguments
                for item in delta.get("tool_calls") or []:
                    if not isinstance(item, dict):
                        continue
                    index = item.get("index", 0)
                    slot = tool_call_buffer.setdefault(
                        index,
                        {"id": "", "type": "function", "function": {"name": "", "arguments": ""}},
                    )
                    if item.get("id"):
                        slot["id"] = item["id"]
                    function = item.get("function") or {}
                    if function.get("name"):
                        slot["function"]["name"] = function["name"]
                    if function.get("arguments"):
                        slot["function"]["arguments"] += function["arguments"]
    except Exception as exc:
        logger.warning("Prediction LLM stream interrupted: %s", exc)
        yield {"type": "error", "reason": "stream_interrupted", "error": str(exc)}
        return

    message = {"role": "assistant", "content": "".join(content_parts)}
    if reasoning_parts:
        message["reasoning_content"] = "".join(reasoning_parts)
    if tool_call_buffer:
        message["tool_calls"] = [tool_call_buffer[key] for key in sorted(tool_call_buffer)]

    yield {
        "type": "done",
        "message": message,
        "finishReason": finish_reason,
        "usage": usage,
        "model": response_model,
        "responseId": response_id,
    }


def invoke_chat_completions_api(*, resolved, system_prompt, user_prompt, schema_guide):
    body = {
        "model": resolved["model"],
        "messages": [
            {
                "role": "system",
                "content": build_json_system_prompt(system_prompt, schema_guide),
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        "response_format": {"type": "json_object"},
    }
    reasoning_effort = resolved["reasoning_effort"]
    if reasoning_effort:
        body["reasoning_effort"] = reasoning_effort

    thinking_type = resolved["thinking_type"]
    if thinking_type:
        body["thinking"] = {"type": thinking_type}

    temperature = resolved["temperature"]
    if temperature is not None:
        body["temperature"] = float(temperature)

    endpoint = f"{resolved['base_url'].rstrip('/')}/chat/completions"
    response_payload, request_error = post_json(endpoint, body, resolved["api_key"], resolved["timeout_seconds"])
    if request_error and request_error["reason"] == "http_400":
        lowered_error = request_error.get("error", "").lower()
        if "response_format" in lowered_error or "json_object" in lowered_error:
            body.pop("response_format", None)
            response_payload, request_error = post_json(
                endpoint,
                body,
                resolved["api_key"],
                resolved["timeout_seconds"],
            )
    return response_payload, request_error


def parse_json_payload(raw_text, expected_keys=None):
    """从模型回复中提取目标 JSON 对象。

    开启 thinking / reasoning_effort 时，deepseek 偶发会出现这几种脏输出：
      1. JSON 前后带解释性文字或 ```json 代码块围栏；
      2. 正文被大量空格填充；
      3. 同一个答案输出两遍（紧凑版 + 缩进版）首尾拼接；
      4. 正式答案前先吐出一个无关小对象（如 {"type":"thinking"}）。
    按"最外层花括号"截取会把第 3 种的两个对象连在一起导致解析失败；
    只取第一个对象又会在第 4 种情况下抓错。
    所以这里用 raw_decode 扫描出所有候选对象，
    优先返回命中 expected_keys 的那个，没有匹配时退回第一个非空对象。
    返回 None 表示确实无法解析。
    """
    text = (raw_text or "").strip()
    if not text:
        return None

    # 去掉 ```json ... ``` 围栏，保留内部正文
    if text.startswith("```"):
        blocks = [block.strip() for block in text.split("```")]
        for block in blocks:
            if block.lower().startswith("json"):
                block = block[4:].strip()
            if block.startswith("{"):
                text = block
                break

    decoder = json.JSONDecoder()
    candidates = []
    index = 0
    length = len(text)
    while index < length:
        brace = text.find("{", index)
        if brace == -1:
            break
        try:
            parsed, end = decoder.raw_decode(text, brace)
        except json.JSONDecodeError:
            index = brace + 1
            continue
        if isinstance(parsed, dict) and parsed:
            candidates.append(parsed)
            index = max(end, brace + 1)
        else:
            index = brace + 1

    if not candidates:
        return None

    if expected_keys:
        expected = set(expected_keys)
        # 优先选包含全部必需键的对象
        for candidate in candidates:
            if expected.issubset(candidate.keys()):
                return candidate
        # 其次选交集最多且确有交集的对象
        best = max(candidates, key=lambda item: len(expected & item.keys()))
        if expected & best.keys():
            return best

    return candidates[0]


def post_json(endpoint, body, api_key, timeout_seconds):
    """发起一次模型请求，对网络抖动/超时做有限次重试。

    开启 thinking 后单次回复会先产出几百个 reasoning token，
    偶发会超过 timeout，仅一次失败就回退成规则话术太脆弱，
    因此对超时与连接类错误重试；HTTP 4xx/5xx 属于明确应答，不重试。
    """
    payload = json.dumps(body).encode("utf-8")
    opener = build_llm_opener()
    max_attempts = max(1, int(getattr(settings, "PREDICTION_LLM_MAX_RETRIES", 2)))
    last_error = None

    for attempt in range(1, max_attempts + 1):
        http_request = request.Request(
            endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with opener.open(http_request, timeout=timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8")), None
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            logger.warning("Prediction LLM HTTP error: %s %s", exc.code, detail[:800])
            return None, {
                "reason": f"http_{exc.code}",
                "error": detail[:800],
            }
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Prediction LLM request failed (attempt %s/%s): %s",
                attempt,
                max_attempts,
                exc,
            )

    return None, {
        "reason": "request_failed",
        "error": str(last_error),
    }


def build_json_system_prompt(system_prompt, schema_guide):
    base_prompt = (system_prompt or "").strip()
    if not base_prompt:
        return schema_guide
    return f"{base_prompt}\n\n{schema_guide}"


def extract_response_text(response_payload):
    output_text = response_payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    outputs = response_payload.get("output") or []
    fragments = []
    for item in outputs:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "message":
            continue
        for content in item.get("content") or []:
            if not isinstance(content, dict):
                continue
            if content.get("type") in {"output_text", "text"}:
                text = content.get("text") or ""
                if text:
                    fragments.append(text)
    return "\n".join(fragment.strip() for fragment in fragments if fragment).strip()


def extract_chat_completion_text(response_payload):
    choices = response_payload.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ""

    fragments = []
    for item in content:
        if isinstance(item, str):
            fragments.append(item)
            continue
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            fragments.append(text.strip())
    return "\n".join(fragments).strip()


def normalize_prediction_chat_answer(answer, fallback_answer):
    if not isinstance(answer, dict):
        return fallback_answer

    return {
        "directAnswer": normalize_string(answer.get("directAnswer")) or fallback_answer["directAnswer"],
        "reasoning": normalize_string_list(answer.get("reasoning")) or fallback_answer["reasoning"],
        "actionPlan": normalize_string_list(answer.get("actionPlan")) or fallback_answer["actionPlan"],
        "citations": normalize_citations(answer.get("citations")) or fallback_answer["citations"],
    }


def normalize_prediction_analysis_result(answer, fallback_result):
    if not isinstance(answer, dict):
        return fallback_result

    return {
        "summary": normalize_string(answer.get("summary")) or fallback_result["summary"],
        "sections": normalize_analysis_sections(answer.get("sections")) or fallback_result["sections"],
        "evidence": normalize_citations(answer.get("evidence")) or fallback_result["evidence"],
    }


def normalize_string(value):
    return str(value or "").strip()


def normalize_string_list(values):
    # 模型有时会把 reasoning / actionPlan 写成单个字符串而不是数组，
    # 旧实现直接丢弃，导致回答看起来"少了内容"。这里兼容字符串形态。
    if isinstance(values, str):
        text = normalize_string(values)
        return [text] if text else []
    if not isinstance(values, list):
        return []
    normalized = []
    for item in values:
        if isinstance(item, dict):
            # 容错 [{"text": "..."}] / [{"content": "..."}] 这类结构
            item = item.get("text") or item.get("content") or item.get("step") or ""
        text = normalize_string(item)
        if text:
            normalized.append(text)
    return normalized[:5]


def normalize_analysis_sections(values):
    if not isinstance(values, list):
        return []

    normalized = []
    for item in values[:4]:
        if not isinstance(item, dict):
            continue
        title = normalize_string(item.get("title"))
        content = normalize_string(item.get("content"))
        if not (title and content):
            continue
        normalized.append(
            {
                "title": title,
                "content": content,
            }
        )
    return normalized


def normalize_citations(values):
    if not isinstance(values, list):
        return []

    normalized = []
    for item in values[:5]:
        if not isinstance(item, dict):
            continue
        title = normalize_string(item.get("title"))
        section = normalize_string(item.get("section"))
        snippet = normalize_string(item.get("snippet"))
        if not (title or snippet):
            continue
        normalized.append(
            {
                "title": title,
                "section": section,
                "snippet": snippet,
            }
        )
    return normalized
