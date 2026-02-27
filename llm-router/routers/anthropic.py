"""Anthropic Messages API compatibility layer for llm-router.

Translates Claude Code's /v1/messages requests to OpenAI chat completions format,
routes via ProviderManager (with full fallback chain), then translates responses
back to Anthropic format.

## What's Translated

Request:
  - system prompt → OpenAI system message
  - message history including tool_use/tool_result content blocks → OpenAI
    messages with tool_calls / role:tool
  - Anthropic tools array (input_schema) → OpenAI tools array (parameters)
  - Anthropic tool_choice → OpenAI tool_choice

Response (non-streaming):
  - OpenAI tool_calls → Anthropic tool_use content blocks
  - finish_reason "tool_calls" → stop_reason "tool_use"

Response (streaming):
  - OpenAI delta.tool_calls → Anthropic content_block_start/delta/stop (tool_use)
  - OpenAI delta.content → Anthropic content_block_delta (text_delta)
  - Correct Anthropic SSE event sequence maintained

Auth: Accepts x-api-key header (Anthropic SDK default) or Authorization: Bearer.
Model: Always uses "auto" routing so the full fallback chain applies:
       gaming-pc-3090 (qwen3-32b-awq) → zai (glm-5) → claude-harness
"""
import json
import logging
import uuid
from typing import AsyncGenerator, Optional

import httpx
import tiktoken
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from auth import ApiKey, validate_api_key, get_request_priority
from providers import build_chat_completions_url, build_request_headers

logger = logging.getLogger(__name__)

router = APIRouter()

_tokenizer = None


def _get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = tiktoken.get_encoding("cl100k_base")
    return _tokenizer


def _count_tokens(text: str) -> int:
    return len(_get_tokenizer().encode(text))


# ── Auth ─────────────────────────────────────────────────────────────────────────

async def validate_anthropic_auth(
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> ApiKey:
    """Accept x-api-key (Anthropic SDK default) or Authorization: Bearer."""
    key = x_api_key
    if not key and authorization:
        key = authorization.removeprefix("Bearer ").strip()
    if not key:
        raise HTTPException(
            status_code=401,
            detail="Missing x-api-key or Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    api_key = await validate_api_key(key)
    if api_key is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or disabled API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return api_key


# ── Tool format helpers ───────────────────────────────────────────────────────────

def _translate_tools_to_openai(anthropic_tools: list) -> list:
    """Translate Anthropic tools array to OpenAI tools format.

    Anthropic:  {"name": "bash", "description": "...", "input_schema": {JSON Schema}}
    OpenAI:     {"type": "function", "function": {"name": "bash", "description": "...", "parameters": {JSON Schema}}}
    """
    oai_tools = []
    for tool in anthropic_tools:
        if not isinstance(tool, dict):
            continue
        oai_tools.append({
            "type": "function",
            "function": {
                "name": tool.get("name", ""),
                "description": tool.get("description", ""),
                "parameters": tool.get("input_schema", {"type": "object", "properties": {}}),
            },
        })
    return oai_tools


def _translate_tool_choice_to_openai(anthropic_tc) -> str | dict:
    """Translate Anthropic tool_choice to OpenAI format.

    Anthropic "auto"  → OpenAI "auto"
    Anthropic "any"   → OpenAI "required"
    Anthropic "none"  → OpenAI "none"
    Anthropic {"type": "tool", "name": "bash"} → OpenAI {"type": "function", "function": {"name": "bash"}}
    """
    if anthropic_tc == "auto":
        return "auto"
    if anthropic_tc == "any":
        return "required"
    if anthropic_tc == "none":
        return "none"
    if isinstance(anthropic_tc, dict):
        tc_type = anthropic_tc.get("type")
        if tc_type == "tool":
            return {"type": "function", "function": {"name": anthropic_tc.get("name", "")}}
        if tc_type == "auto":
            return "auto"
        if tc_type == "any":
            return "required"
        if tc_type == "none":
            return "none"
    return "auto"


# ── Content utilities ─────────────────────────────────────────────────────────────

def _content_to_str(content) -> str:
    """Flatten Anthropic content (str or list of blocks) to a plain string.
    Used for token counting only — not for message translation.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            t = block.get("type")
            if t == "text":
                parts.append(block.get("text", ""))
            elif t == "tool_result":
                inner = block.get("content", "")
                if isinstance(inner, list):
                    inner = " ".join(
                        b.get("text", "") for b in inner
                        if isinstance(b, dict) and b.get("type") == "text"
                    )
                parts.append(str(inner))
            elif t == "tool_use":
                parts.append(f"{block.get('name')}({json.dumps(block.get('input', {}))})")
        return " ".join(parts)
    return str(content)


def _tool_result_content_to_str(content) -> str:
    """Extract text from a tool_result content field (str or list of blocks)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(parts)
    return str(content) if content is not None else ""


# ── Request Translation ───────────────────────────────────────────────────────────

def _translate_messages(anthropic_messages: list) -> list:
    """Translate Anthropic message list to OpenAI messages list.

    Handles:
    - Plain string content → passthrough
    - assistant messages with tool_use blocks → role:assistant with tool_calls
    - user messages with tool_result blocks → role:tool messages
    - Mixed content (text + tool_use, text + tool_result) → split correctly
    """
    oai_messages = []

    for msg in anthropic_messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        # Simple string content — passthrough
        if isinstance(content, str):
            oai_messages.append({"role": role, "content": content})
            continue

        if not isinstance(content, list):
            oai_messages.append({"role": role, "content": str(content)})
            continue

        if role == "assistant":
            # May contain text blocks and/or tool_use blocks.
            text_parts = []
            tool_calls = []

            for block in content:
                if not isinstance(block, dict):
                    continue
                t = block.get("type")
                if t == "text":
                    text_parts.append(block.get("text", ""))
                elif t == "tool_use":
                    raw_input = block.get("input", {})
                    tool_calls.append({
                        "id": block.get("id", f"toolu_{len(tool_calls):04x}"),
                        "type": "function",
                        "function": {
                            "name": block.get("name", ""),
                            "arguments": json.dumps(raw_input) if isinstance(raw_input, dict) else str(raw_input),
                        },
                    })

            oai_msg: dict = {"role": "assistant"}
            oai_msg["content"] = " ".join(text_parts) if text_parts else None
            if tool_calls:
                oai_msg["tool_calls"] = tool_calls
            oai_messages.append(oai_msg)

        elif role == "user":
            # May contain text blocks and/or tool_result blocks.
            # tool_result blocks → role:tool messages.
            # Text blocks that appear alongside tool_results → separate role:user message.
            pending_text: list[str] = []

            for block in content:
                if not isinstance(block, dict):
                    continue
                t = block.get("type")
                if t == "text":
                    pending_text.append(block.get("text", ""))
                elif t == "tool_result":
                    # Flush accumulated text as a user message first
                    if pending_text:
                        oai_messages.append({"role": "user", "content": " ".join(pending_text)})
                        pending_text = []
                    result_text = _tool_result_content_to_str(block.get("content", ""))
                    oai_messages.append({
                        "role": "tool",
                        "tool_call_id": block.get("tool_use_id", ""),
                        "content": result_text,
                    })

            # Flush any remaining text
            if pending_text:
                oai_messages.append({"role": "user", "content": " ".join(pending_text)})

        else:
            # Unknown role — flatten to string
            oai_messages.append({"role": role, "content": _content_to_str(content)})

    return oai_messages


def translate_anthropic_to_openai(anthropic_body: dict) -> dict:
    """Translate Anthropic Messages API request to OpenAI chat completions format.

    Uses "auto" as the model so ProviderManager applies the full fallback chain
    (qwen3-32b-awq → glm-5 → claude-harness) rather than hard-routing.
    """
    messages = []

    if anthropic_body.get("system"):
        sys = anthropic_body["system"]
        # system can be a string or a list of content blocks
        if isinstance(sys, list):
            sys = _content_to_str(sys)
        messages.append({"role": "system", "content": sys})

    messages.extend(_translate_messages(anthropic_body.get("messages", [])))

    oai_body: dict = {
        "model": "auto",
        "messages": messages,
        "max_tokens": anthropic_body.get("max_tokens", 4096),
        "stream": anthropic_body.get("stream", False),
    }

    for field in ("temperature", "top_p"):
        if field in anthropic_body:
            oai_body[field] = anthropic_body[field]

    if "stop_sequences" in anthropic_body:
        oai_body["stop"] = anthropic_body["stop_sequences"]

    if "tools" in anthropic_body:
        oai_body["tools"] = _translate_tools_to_openai(anthropic_body["tools"])

    if "tool_choice" in anthropic_body:
        oai_body["tool_choice"] = _translate_tool_choice_to_openai(anthropic_body["tool_choice"])

    return oai_body


# ── Response Translation ──────────────────────────────────────────────────────────

def _make_message_id() -> str:
    return f"msg_{uuid.uuid4().hex[:24]}"


def translate_openai_to_anthropic(oai_response: dict, original_model: str) -> dict:
    """Translate OpenAI chat completion response to Anthropic Messages format.

    Handles both plain text responses and tool_calls responses.
    """
    choice = oai_response.get("choices", [{}])[0]
    message = choice.get("message", {})
    content_text = message.get("content", "") or ""
    tool_calls = message.get("tool_calls") or []
    finish_reason = choice.get("finish_reason", "stop")

    stop_reason = "end_turn"
    if finish_reason == "length":
        stop_reason = "max_tokens"
    elif finish_reason == "tool_calls":
        stop_reason = "tool_use"

    content_blocks = []

    if content_text:
        content_blocks.append({"type": "text", "text": content_text})

    for tc in tool_calls:
        func = tc.get("function", {})
        args_str = func.get("arguments", "{}")
        try:
            args = json.loads(args_str) if isinstance(args_str, str) else args_str
        except json.JSONDecodeError:
            args = {}
        content_blocks.append({
            "type": "tool_use",
            "id": tc.get("id", f"toolu_{uuid.uuid4().hex[:16]}"),
            "name": func.get("name", ""),
            "input": args,
        })

    if not content_blocks:
        content_blocks = [{"type": "text", "text": ""}]

    usage = oai_response.get("usage", {})
    return {
        "id": _make_message_id(),
        "type": "message",
        "role": "assistant",
        "model": original_model,
        "content": content_blocks,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
        },
    }


# ── Streaming Translation ─────────────────────────────────────────────────────────

def _sse_event(event_type: str, data: dict) -> str:
    """Format an Anthropic SSE event (event: X\\ndata: Y\\n\\n)."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


async def translate_openai_stream_to_anthropic(
    selection,
    oai_body: dict,
    original_model: str,
    input_token_estimate: int,
) -> AsyncGenerator[str, None]:
    """Stream from OpenAI backend, translate each chunk to Anthropic SSE format.

    Anthropic event sequence for a text + tool_use response:
      message_start
      ping
      content_block_start (index=0, type=text)
      content_block_delta* (text_delta)
      content_block_stop (index=0)
      content_block_start (index=1, type=tool_use)
      content_block_delta* (input_json_delta)
      content_block_stop (index=1)
      message_delta (stop_reason)
      message_stop

    For tool-only responses the text block is omitted. For text-only responses
    the tool blocks are omitted.
    """
    endpoint_url = build_chat_completions_url(selection.provider)
    request_headers = build_request_headers(selection.provider)

    msg_id = _make_message_id()
    output_tokens = 0

    # Streaming state
    sent_message_start = False
    text_block_open = False
    text_block_index = 0
    next_anthr_index = 0
    # oai tool index → {anthr_index, id, name}
    tool_blocks: dict[int, dict] = {}
    finish_reason = "stop"

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                endpoint_url,
                json=oai_body,
                headers=request_headers,
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    yield _sse_event("error", {
                        "type": "error",
                        "error": {
                            "type": "api_error",
                            "message": f"Backend error {response.status_code}: {error_text.decode()[:200]}",
                        },
                    })
                    return

                async for raw_bytes in response.aiter_bytes():
                    chunk_str = raw_bytes.decode("utf-8")
                    for line in chunk_str.split("\n"):
                        line = line.strip()
                        if not line.startswith("data: "):
                            continue
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        choices = chunk.get("choices", [])
                        if not choices:
                            continue

                        delta = choices[0].get("delta", {})
                        fr = choices[0].get("finish_reason")
                        if fr:
                            finish_reason = fr

                        has_content = bool(delta.get("content"))
                        has_tools = bool(delta.get("tool_calls"))

                        # Send message_start once on first actual content
                        if not sent_message_start and (has_content or has_tools):
                            sent_message_start = True
                            yield _sse_event("message_start", {
                                "type": "message_start",
                                "message": {
                                    "id": msg_id,
                                    "type": "message",
                                    "role": "assistant",
                                    "content": [],
                                    "model": original_model,
                                    "stop_reason": None,
                                    "stop_sequence": None,
                                    "usage": {
                                        "input_tokens": input_token_estimate,
                                        "output_tokens": 0,
                                    },
                                },
                            })
                            yield _sse_event("ping", {"type": "ping"})

                        # ── Text content ──────────────────────────────────────
                        text_content = delta.get("content", "")
                        if text_content:
                            if not text_block_open:
                                text_block_index = next_anthr_index
                                next_anthr_index += 1
                                text_block_open = True
                                yield _sse_event("content_block_start", {
                                    "type": "content_block_start",
                                    "index": text_block_index,
                                    "content_block": {"type": "text", "text": ""},
                                })
                            output_tokens += _count_tokens(text_content)
                            yield _sse_event("content_block_delta", {
                                "type": "content_block_delta",
                                "index": text_block_index,
                                "delta": {"type": "text_delta", "text": text_content},
                            })

                        # ── Tool calls ────────────────────────────────────────
                        tool_calls_delta = delta.get("tool_calls", [])
                        for tc_delta in tool_calls_delta:
                            oai_idx = tc_delta.get("index", 0)

                            # Close any open text block before starting tool blocks
                            if text_block_open:
                                yield _sse_event("content_block_stop", {
                                    "type": "content_block_stop",
                                    "index": text_block_index,
                                })
                                text_block_open = False

                            # New tool call starts when the id field is present
                            if tc_delta.get("id"):
                                anthr_idx = next_anthr_index
                                next_anthr_index += 1
                                tool_name = tc_delta.get("function", {}).get("name", "")
                                tool_blocks[oai_idx] = {
                                    "anthr_index": anthr_idx,
                                    "id": tc_delta["id"],
                                    "name": tool_name,
                                }
                                yield _sse_event("content_block_start", {
                                    "type": "content_block_start",
                                    "index": anthr_idx,
                                    "content_block": {
                                        "type": "tool_use",
                                        "id": tc_delta["id"],
                                        "name": tool_name,
                                        "input": {},
                                    },
                                })

                            # Stream argument JSON fragments
                            args_chunk = tc_delta.get("function", {}).get("arguments", "")
                            if args_chunk and oai_idx in tool_blocks:
                                anthr_idx = tool_blocks[oai_idx]["anthr_index"]
                                yield _sse_event("content_block_delta", {
                                    "type": "content_block_delta",
                                    "index": anthr_idx,
                                    "delta": {"type": "input_json_delta", "partial_json": args_chunk},
                                })

    except Exception as e:
        logger.error(f"[Anthropic] Stream error: {e}")
        if not sent_message_start:
            yield _sse_event("error", {
                "type": "error",
                "error": {"type": "api_error", "message": str(e)},
            })
            return

    # ── Finalize ──────────────────────────────────────────────────────────────────

    # Handle completely empty response (no content came through)
    if not sent_message_start:
        yield _sse_event("message_start", {
            "type": "message_start",
            "message": {
                "id": msg_id,
                "type": "message",
                "role": "assistant",
                "content": [],
                "model": original_model,
                "stop_reason": None,
                "stop_sequence": None,
                "usage": {"input_tokens": input_token_estimate, "output_tokens": 0},
            },
        })
        yield _sse_event("content_block_start", {
            "type": "content_block_start",
            "index": 0,
            "content_block": {"type": "text", "text": ""},
        })
        yield _sse_event("content_block_stop", {"type": "content_block_stop", "index": 0})
    else:
        # Close any still-open text block
        if text_block_open:
            yield _sse_event("content_block_stop", {
                "type": "content_block_stop",
                "index": text_block_index,
            })
        # Close all tool blocks (by Anthropic index order)
        for tb in sorted(tool_blocks.values(), key=lambda x: x["anthr_index"]):
            yield _sse_event("content_block_stop", {
                "type": "content_block_stop",
                "index": tb["anthr_index"],
            })

    stop_reason = "end_turn"
    if finish_reason == "length":
        stop_reason = "max_tokens"
    elif finish_reason == "tool_calls":
        stop_reason = "tool_use"

    yield _sse_event("message_delta", {
        "type": "message_delta",
        "delta": {"stop_reason": stop_reason, "stop_sequence": None},
        "usage": {"output_tokens": output_tokens},
    })
    yield _sse_event("message_stop", {"type": "message_stop"})


# ── Endpoints ──────────────────────────────────────────────────────────────────────

@router.post("/messages/count_tokens")
async def count_tokens(
    request: Request,
    api_key: ApiKey = Depends(validate_anthropic_auth),
):
    """Token counting for Claude Code pre-flight checks."""
    body = await request.json()
    enc = _get_tokenizer()
    total = 0

    if body.get("system"):
        sys = body["system"]
        if isinstance(sys, list):
            sys = _content_to_str(sys)
        total += len(enc.encode(str(sys)))

    for msg in body.get("messages", []):
        text = _content_to_str(msg.get("content", ""))
        total += len(enc.encode(text))

    # Rough count for tool definitions
    for tool in body.get("tools", []):
        total += len(enc.encode(json.dumps(tool)))

    return JSONResponse({"input_tokens": total})


@router.post("/messages")
async def messages(
    request: Request,
    api_key: ApiKey = Depends(validate_anthropic_auth),
):
    """Anthropic Messages API — routes to local/cloud LLMs via ProviderManager.

    Routing chain: gaming-pc-3090 (qwen3-32b-awq) → zai (glm-5) → claude-harness
    Full tool use translation: Anthropic tool_use/tool_result ↔ OpenAI tool_calls/role:tool
    """
    # Lazy imports to avoid circular dependency with router.py
    from router import route_request, provider_manager  # noqa: PLC0415

    body = await request.json()
    original_model = body.get("model", "claude-sonnet-4-6")
    is_stream = body.get("stream", False)

    oai_body = translate_anthropic_to_openai(body)
    priority = get_request_priority(api_key)
    selection = await route_request(request, oai_body, priority=priority, api_key=api_key)
    oai_body["model"] = selection.model.id

    logger.info(
        f"[Anthropic] '{original_model}' → {selection.provider.name} ({selection.model.id})"
        f", stream={is_stream}, tools={len(body.get('tools', []))}"
    )

    if is_stream:
        enc = _get_tokenizer()
        input_tokens = 0
        if body.get("system"):
            sys = body["system"]
            if isinstance(sys, list):
                sys = _content_to_str(sys)
            input_tokens += len(enc.encode(str(sys)))
        for msg in body.get("messages", []):
            input_tokens += len(enc.encode(_content_to_str(msg.get("content", ""))))
        for tool in body.get("tools", []):
            input_tokens += len(enc.encode(json.dumps(tool)))

        async with provider_manager.track_request(selection.provider.id):
            async def stream_gen():
                async for chunk in translate_openai_stream_to_anthropic(
                    selection, oai_body, original_model, input_tokens
                ):
                    yield chunk

            return StreamingResponse(stream_gen(), media_type="text/event-stream")
    else:
        endpoint_url = build_chat_completions_url(selection.provider)
        request_headers = build_request_headers(selection.provider)

        async with provider_manager.track_request(selection.provider.id):
            try:
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.post(
                        endpoint_url,
                        json=oai_body,
                        headers=request_headers,
                    )
            except (httpx.ConnectError, httpx.TimeoutException, httpx.ConnectTimeout) as e:
                logger.error(f"[Anthropic] Backend unreachable {selection.provider.name}: {e}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Backend {selection.provider.name} unreachable: {type(e).__name__}",
                )

            if response.status_code != 200:
                error_detail = response.text[:500] if response.text else "Empty response"
                logger.error(
                    f"[Anthropic] Backend error: HTTP {response.status_code} - {error_detail}"
                )
                raise HTTPException(
                    status_code=502,
                    detail=f"Backend {selection.provider.name} returned HTTP {response.status_code}",
                )

            try:
                oai_response = response.json()
            except Exception:
                raise HTTPException(status_code=502, detail="Backend returned invalid JSON")

            return JSONResponse(content=translate_openai_to_anthropic(oai_response, original_model))
