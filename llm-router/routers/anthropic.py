"""Anthropic Messages API compatibility layer for llm-router.

Translates Claude Code's /v1/messages requests to OpenAI chat completions format,
routes via ProviderManager (with full fallback chain), then translates responses
back to Anthropic format.

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


# ── Request Translation ───────────────────────────────────────────────────────────

def _content_to_str(content) -> str:
    """Convert Anthropic content (str or list of blocks) to a plain string."""
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
                parts.append(f"[Tool result: {inner}]")
            elif t == "tool_use":
                parts.append(
                    f"[Tool call: {block.get('name')}({json.dumps(block.get('input', {}))})]"
                )
        return " ".join(parts)
    return str(content)


def translate_anthropic_to_openai(anthropic_body: dict) -> dict:
    """Translate Anthropic Messages API request to OpenAI chat completions format.

    Uses "auto" as the model so ProviderManager applies the full fallback chain
    (qwen3-32b-awq → glm-5 → claude-harness) rather than hard-routing.
    """
    messages = []

    if anthropic_body.get("system"):
        messages.append({"role": "system", "content": anthropic_body["system"]})

    for msg in anthropic_body.get("messages", []):
        messages.append({
            "role": msg.get("role", "user"),
            "content": _content_to_str(msg.get("content", "")),
        })

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

    return oai_body


# ── Response Translation ──────────────────────────────────────────────────────────

def _make_message_id() -> str:
    return f"msg_{uuid.uuid4().hex[:24]}"


def translate_openai_to_anthropic(oai_response: dict, original_model: str) -> dict:
    """Translate OpenAI chat completion response to Anthropic Messages format."""
    choice = oai_response.get("choices", [{}])[0]
    message = choice.get("message", {})
    content_text = message.get("content", "") or ""
    finish_reason = choice.get("finish_reason", "stop")

    stop_reason = "end_turn"
    if finish_reason == "length":
        stop_reason = "max_tokens"
    elif finish_reason == "tool_calls":
        stop_reason = "tool_use"

    usage = oai_response.get("usage", {})
    return {
        "id": _make_message_id(),
        "type": "message",
        "role": "assistant",
        "model": original_model,
        "content": [{"type": "text", "text": content_text}],
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

    Anthropic event sequence:
      message_start → content_block_start → ping → content_block_delta* →
      content_block_stop → message_delta → message_stop
    """
    endpoint_url = build_chat_completions_url(selection.provider)
    request_headers = build_request_headers(selection.provider)

    msg_id = _make_message_id()
    output_tokens = 0
    sent_start = False
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

                        if not sent_start:
                            sent_start = True
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
                            yield _sse_event("content_block_start", {
                                "type": "content_block_start",
                                "index": 0,
                                "content_block": {"type": "text", "text": ""},
                            })
                            yield _sse_event("ping", {"type": "ping"})

                        content = delta.get("content", "")
                        if content:
                            output_tokens += _count_tokens(content)
                            yield _sse_event("content_block_delta", {
                                "type": "content_block_delta",
                                "index": 0,
                                "delta": {"type": "text_delta", "text": content},
                            })

    except Exception as e:
        logger.error(f"[Anthropic] Stream error: {e}")
        if not sent_start:
            yield _sse_event("error", {
                "type": "error",
                "error": {"type": "api_error", "message": str(e)},
            })
            return

    # Ensure start events were sent (empty response edge case)
    if not sent_start:
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

    stop_reason = "end_turn"
    if finish_reason == "length":
        stop_reason = "max_tokens"

    yield _sse_event("content_block_stop", {"type": "content_block_stop", "index": 0})
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
        total += len(enc.encode(body["system"]))

    for msg in body.get("messages", []):
        text = _content_to_str(msg.get("content", ""))
        total += len(enc.encode(text))

    return JSONResponse({"input_tokens": total})


@router.post("/messages")
async def messages(
    request: Request,
    api_key: ApiKey = Depends(validate_anthropic_auth),
):
    """Anthropic Messages API — routes to local/cloud LLMs via ProviderManager.

    Routing chain: gaming-pc-3090 (qwen3-32b-awq) → zai (glm-5) → claude-harness
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
        f", stream={is_stream}"
    )

    if is_stream:
        enc = _get_tokenizer()
        input_tokens = 0
        if body.get("system"):
            input_tokens += len(enc.encode(body["system"]))
        for msg in body.get("messages", []):
            input_tokens += len(enc.encode(_content_to_str(msg.get("content", ""))))

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
