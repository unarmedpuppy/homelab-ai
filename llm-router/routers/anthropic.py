"""Anthropic Messages API compatibility layer for llm-router.

Translates Claude Code's /v1/messages requests to OpenAI chat completions format,
routes via ProviderManager (with full fallback chain), then translates responses
back to Anthropic format.

All translation logic lives in bridge/ — this module is router glue only:
  - Auth validation
  - Provider selection and field stripping
  - FastAPI endpoints

## What's Translated (handled by bridge/)

Request:
  - system prompt → OpenAI system message
  - message history including tool_use/tool_result content blocks → OpenAI
    messages with tool_calls / role:tool
  - image blocks → OpenAI image_url content blocks
  - images in tool_result content → follow-up user message (OpenAI limitation)
  - Anthropic tools array (input_schema) → OpenAI tools array (parameters)
  - Anthropic tool_choice → OpenAI tool_choice
  - is_error in tool_result → [ERROR] prefix on content

Response (non-streaming):
  - OpenAI tool_calls → Anthropic tool_use content blocks
  - finish_reason "tool_calls" → stop_reason "tool_use"
  - cache_creation_input_tokens / cache_read_input_tokens always present in usage

Response (streaming):
  - OpenAI delta.tool_calls → Anthropic content_block_start/delta/stop (tool_use)
  - OpenAI delta.content → Anthropic content_block_delta (text_delta)
  - Correct Anthropic SSE event sequence maintained
  - cache fields present in message_start usage

Auth: Accepts x-api-key header (Anthropic SDK default) or Authorization: Bearer.
Model: Always uses "auto" routing so the full fallback chain applies:
       gaming-pc-3090 (qwen3-32b-awq) → zai (glm-5) → 503
"""
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from auth import ApiKey, validate_api_key, get_request_priority
from providers import build_chat_completions_url, build_request_headers
from bridge import translate_request, translate_response, translate_stream, count_message_tokens

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Auth ──────────────────────────────────────────────────────────────────────

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


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/messages/count_tokens")
async def count_tokens(
    request: Request,
    api_key: ApiKey = Depends(validate_anthropic_auth),
):
    """Token counting for Claude Code pre-flight checks."""
    body = await request.json()
    return JSONResponse({"input_tokens": count_message_tokens(body)})


@router.post("/messages")
async def messages(
    request: Request,
    api_key: ApiKey = Depends(validate_anthropic_auth),
):
    """Anthropic Messages API — routes to local/cloud LLMs via ProviderManager.

    Routing chain: gaming-pc-3090 (qwen3-32b-awq) → zai (glm-5)
    Full tool use + image translation: Anthropic ↔ OpenAI (via bridge/)
    """
    # Lazy imports to avoid circular dependency with router.py
    from router import route_request, provider_manager  # noqa: PLC0415

    body = await request.json()
    original_model = body.get("model", "auto")
    is_stream = body.get("stream", False)

    oai_body = translate_request(body)
    priority = get_request_priority(api_key)
    estimated_tokens = count_message_tokens(body)
    selection = await route_request(request, oai_body, priority=priority, api_key=api_key, estimated_tokens=estimated_tokens)
    oai_body["model"] = selection.model.id

    # Strip vLLM-specific fields when routing to cloud backends — Z.ai and
    # claude-harness reject unknown fields with HTTP 400.
    from providers.models import ProviderType  # noqa: PLC0415
    if selection.provider.type == ProviderType.CLOUD:
        for field in ("chat_template_kwargs", "top_k", "min_p"):
            oai_body.pop(field, None)

    logger.info(
        f"[Anthropic] '{original_model}' → {selection.provider.name} ({selection.model.id})"
        f", stream={is_stream}, tools={len(body.get('tools', []))}"
    )

    endpoint_url = build_chat_completions_url(selection.provider)
    request_headers = build_request_headers(selection.provider)

    if is_stream:
        async with provider_manager.track_request(selection.provider.id):
            def _on_stream_failure():
                provider_manager.record_inference_failure(selection.provider.id)

            async def stream_gen():
                async for chunk in translate_stream(
                    endpoint_url, request_headers, oai_body, original_model, estimated_tokens,
                    on_failure=_on_stream_failure,
                ):
                    yield chunk

            return StreamingResponse(stream_gen(), media_type="text/event-stream")
    else:
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

            return JSONResponse(content=translate_response(oai_response, original_model))
