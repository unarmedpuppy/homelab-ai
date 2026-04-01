"""Anthropic SSE streaming translation from an OpenAI-compatible backend.

No router, auth, or provider dependencies — only httpx and stdlib.
The caller provides backend_url and backend_headers; this module handles
the full SSE translation loop.

Public API (re-exported from bridge/__init__.py):
  translate_stream(backend_url, backend_headers, oai_body, original_model,
                   input_token_estimate, on_failure=None)
    → AsyncGenerator[str, None]  (Anthropic SSE events)
"""
import json
import logging
from typing import AsyncGenerator, Callable, Optional

import httpx

from .translate import count_tokens, make_message_id, sse_event

__all__ = ["translate_stream"]

logger = logging.getLogger(__name__)


async def translate_stream(
    backend_url: str,
    backend_headers: dict,
    oai_body: dict,
    original_model: str,
    input_token_estimate: int,
    on_failure: Optional[Callable] = None,
) -> AsyncGenerator[str, None]:
    """Stream from an OpenAI-compatible backend and translate to Anthropic SSE format.

    Anthropic event sequence for a text + tool_use response:
      message_start
      ping
      content_block_start  (index=0, type=text)
      content_block_delta* (text_delta)
      content_block_stop   (index=0)
      content_block_start  (index=1, type=tool_use)
      content_block_delta* (input_json_delta)
      content_block_stop   (index=1)
      message_delta        (stop_reason)
      message_stop

    For tool-only responses the text block is omitted.
    For text-only responses the tool blocks are omitted.
    """
    msg_id = make_message_id()
    output_tokens = 0

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
                backend_url,
                json=oai_body,
                headers=backend_headers,
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    yield sse_event("error", {
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

                        # Emit message_start on first actual content
                        if not sent_message_start and (has_content or has_tools):
                            sent_message_start = True
                            yield sse_event("message_start", {
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
                                        "cache_creation_input_tokens": 0,
                                        "cache_read_input_tokens": 0,
                                    },
                                },
                            })
                            yield sse_event("ping", {"type": "ping"})

                        # ── Text content ───────────────────────────────────────
                        text_content = delta.get("content", "")
                        if text_content:
                            if not text_block_open:
                                text_block_index = next_anthr_index
                                next_anthr_index += 1
                                text_block_open = True
                                yield sse_event("content_block_start", {
                                    "type": "content_block_start",
                                    "index": text_block_index,
                                    "content_block": {"type": "text", "text": ""},
                                })
                            output_tokens += count_tokens(text_content)
                            yield sse_event("content_block_delta", {
                                "type": "content_block_delta",
                                "index": text_block_index,
                                "delta": {"type": "text_delta", "text": text_content},
                            })

                        # ── Tool calls ─────────────────────────────────────────
                        tool_calls_delta = delta.get("tool_calls", [])
                        for tc_delta in tool_calls_delta:
                            oai_idx = tc_delta.get("index", 0)

                            # Close any open text block before starting tool blocks
                            if text_block_open:
                                yield sse_event("content_block_stop", {
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
                                yield sse_event("content_block_start", {
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
                                yield sse_event("content_block_delta", {
                                    "type": "content_block_delta",
                                    "index": anthr_idx,
                                    "delta": {"type": "input_json_delta", "partial_json": args_chunk},
                                })

    except (httpx.ConnectError, httpx.ConnectTimeout) as e:
        logger.error(f"[bridge] Stream connect error: {e}")
        if on_failure:
            on_failure()
        if not sent_message_start:
            yield sse_event("error", {
                "type": "error",
                "error": {"type": "api_error", "message": f"Backend unreachable: {type(e).__name__}"},
            })
            return
    except Exception as e:
        logger.error(f"[bridge] Stream error: {e}")
        if not sent_message_start:
            yield sse_event("error", {
                "type": "error",
                "error": {"type": "api_error", "message": str(e)},
            })
            return

    # ── Finalize ──────────────────────────────────────────────────────────────

    # Handle completely empty response (no content came through)
    if not sent_message_start:
        yield sse_event("message_start", {
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
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 0,
                },
            },
        })
        yield sse_event("content_block_start", {
            "type": "content_block_start",
            "index": 0,
            "content_block": {"type": "text", "text": ""},
        })
        yield sse_event("content_block_stop", {"type": "content_block_stop", "index": 0})
    else:
        # Close any still-open text block
        if text_block_open:
            yield sse_event("content_block_stop", {
                "type": "content_block_stop",
                "index": text_block_index,
            })
        # Close all tool blocks in Anthropic index order
        for tb in sorted(tool_blocks.values(), key=lambda x: x["anthr_index"]):
            yield sse_event("content_block_stop", {
                "type": "content_block_stop",
                "index": tb["anthr_index"],
            })

    stop_reason = "end_turn"
    if finish_reason == "length":
        stop_reason = "max_tokens"
    elif finish_reason == "tool_calls":
        stop_reason = "tool_use"

    yield sse_event("message_delta", {
        "type": "message_delta",
        "delta": {"stop_reason": stop_reason, "stop_sequence": None},
        "usage": {"output_tokens": output_tokens},
    })
    yield sse_event("message_stop", {"type": "message_stop"})
