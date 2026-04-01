"""Pure Anthropic ↔ OpenAI translation functions.

No router, auth, or provider dependencies — only stdlib, tiktoken, and httpx.
Safe to copy into any project that needs this translation layer.

Public API (re-exported from bridge/__init__.py):
  translate_request(body)              Anthropic Messages request → OpenAI chat completions
  translate_response(oai, model)       OpenAI response → Anthropic Messages response
  count_message_tokens(body)           Token estimate for an Anthropic Messages request body
"""
import json
import uuid
from typing import Optional, Union

import tiktoken

__all__ = [
    "translate_request",
    "translate_response",
    "count_message_tokens",
]

# ── Tokenizer ─────────────────────────────────────────────────────────────────

_tokenizer = None


def _get_tokenizer():
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = tiktoken.get_encoding("cl100k_base")
    return _tokenizer


def count_tokens(text: str) -> int:
    return len(_get_tokenizer().encode(text))


# ── SSE helpers (used by stream.py too) ───────────────────────────────────────

def sse_event(event_type: str, data: dict) -> str:
    """Format a single Anthropic SSE event (event: X\\ndata: Y\\n\\n)."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


def make_message_id() -> str:
    return f"msg_{uuid.uuid4().hex[:24]}"


# ── Image translation ──────────────────────────────────────────────────────────

def _translate_image_to_openai(block: dict) -> Optional[dict]:
    """Translate an Anthropic image block to an OpenAI image_url content block.

    Anthropic base64: {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": "..."}}
    Anthropic url:    {"type": "image", "source": {"type": "url", "url": "https://..."}}

    OpenAI:           {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
                      {"type": "image_url", "image_url": {"url": "https://..."}}
    """
    source = block.get("source", {})
    src_type = source.get("type", "")
    if src_type == "base64":
        media_type = source.get("media_type", "image/jpeg")
        data = source.get("data", "")
        url = f"data:{media_type};base64,{data}"
    elif src_type == "url":
        url = source.get("url", "")
        if not url:
            return None
    else:
        return None
    return {"type": "image_url", "image_url": {"url": url}}


def _flatten_or_multipart(parts: list) -> Union[str, list]:
    """Return a plain string for single-text content, list otherwise.

    Keeps backward-compat with backends that prefer string content for text-only messages.
    """
    if len(parts) == 1 and parts[0]["type"] == "text":
        return parts[0]["text"]
    return parts


# ── Tool helpers ───────────────────────────────────────────────────────────────

def _translate_tools_to_openai(anthropic_tools: list) -> list:
    """Anthropic tools → OpenAI tools format.

    Anthropic: {"name": "bash", "description": "...", "input_schema": {JSON Schema}}
    OpenAI:    {"type": "function", "function": {"name": "bash", "description": "...", "parameters": {JSON Schema}}}
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


def _translate_tool_choice_to_openai(anthropic_tc) -> Union[str, dict]:
    """Anthropic tool_choice → OpenAI tool_choice.

    "auto"  → "auto"
    "any"   → "required"
    "none"  → "none"
    {"type": "tool", "name": "bash"} → {"type": "function", "function": {"name": "bash"}}
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


# ── Content utilities ──────────────────────────────────────────────────────────

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
            # image blocks: no text contribution to token count
        return " ".join(parts)
    return str(content)


def _tool_result_content_to_str(content) -> str:
    """Extract text from a tool_result content field (str or list of blocks).
    Images in the list are handled separately in _translate_messages.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return "\n".join(parts)
    return str(content) if content is not None else ""


# ── Message translation ────────────────────────────────────────────────────────

def _translate_messages(anthropic_messages: list) -> list:
    """Translate Anthropic message list to OpenAI messages list.

    Handles:
    - Plain string content → passthrough
    - assistant: text blocks + tool_use blocks → role:assistant with tool_calls
    - user: text + image blocks → role:user with multipart content (image_url)
    - user: tool_result blocks → role:tool messages
    - user: images inside tool_result content → separate role:user message after the tool message
    - Mixed content (text + tool_results) → split correctly, text flushed before tool messages
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
            # May contain text blocks, image blocks, and/or tool_result blocks.
            #
            # Strategy:
            #   - Accumulate text and image blocks as "pending_parts" (multipart content).
            #   - When we hit a tool_result, flush pending_parts as a user message first,
            #     then emit role:tool for the result text.
            #   - If the tool_result content contains images, emit them as a follow-up
            #     role:user message (OpenAI doesn't support images in tool messages).
            #   - After all blocks, flush any remaining pending_parts.
            pending_parts: list[dict] = []

            for block in content:
                if not isinstance(block, dict):
                    continue
                t = block.get("type")

                if t == "text":
                    pending_parts.append({"type": "text", "text": block.get("text", "")})

                elif t == "image":
                    img = _translate_image_to_openai(block)
                    if img:
                        pending_parts.append(img)

                elif t == "tool_result":
                    # Flush accumulated text/images as a user message first
                    if pending_parts:
                        oai_messages.append({"role": "user", "content": _flatten_or_multipart(pending_parts)})
                        pending_parts = []

                    # Tool result text → role:tool
                    result_text = _tool_result_content_to_str(block.get("content", ""))
                    if block.get("is_error"):
                        result_text = f"[ERROR] {result_text}"
                    oai_messages.append({
                        "role": "tool",
                        "tool_call_id": block.get("tool_use_id", ""),
                        "content": result_text,
                    })

                    # Images inside tool_result content → follow-up user message
                    tool_content = block.get("content", "")
                    if isinstance(tool_content, list):
                        img_parts = [
                            _translate_image_to_openai(b)
                            for b in tool_content
                            if isinstance(b, dict) and b.get("type") == "image"
                        ]
                        img_parts = [p for p in img_parts if p]
                        if img_parts:
                            oai_messages.append({"role": "user", "content": img_parts})

            # Flush remaining text/images
            if pending_parts:
                oai_messages.append({"role": "user", "content": _flatten_or_multipart(pending_parts)})

        else:
            # Unknown role — flatten to string
            oai_messages.append({"role": role, "content": _content_to_str(content)})

    return oai_messages


# ── Public API ─────────────────────────────────────────────────────────────────

def translate_request(anthropic_body: dict) -> dict:
    """Translate an Anthropic Messages API request to OpenAI chat completions format.

    Model is set to "auto" so the caller's routing layer picks the actual model.
    Injects Qwen3 optimal sampling defaults when client doesn't specify them.
    Disables thinking mode to avoid <think> tokens leaking into Claude Code output.
    """
    messages = []

    if anthropic_body.get("system"):
        sys = anthropic_body["system"]
        if isinstance(sys, list):
            sys = _content_to_str(sys)
        messages.append({"role": "system", "content": sys})

    messages.extend(_translate_messages(anthropic_body.get("messages", [])))

    oai_body: dict = {
        "model": "auto",
        "messages": messages,
        "max_tokens": anthropic_body.get("max_tokens", 4096),
        "stream": anthropic_body.get("stream", False),
        # Disable qwen3 thinking mode — Claude Code does its own reasoning and
        # doesn't know how to handle <think> tokens streamed as text content.
        "chat_template_kwargs": {"enable_thinking": False},
    }

    # Optimal sampling defaults for Qwen3 agentic coding (unsloth recommendation).
    # Cloud backends ignore unknown fields.
    oai_body["temperature"] = anthropic_body.get("temperature", 0.6)
    oai_body["top_p"] = anthropic_body.get("top_p", 0.95)
    oai_body["top_k"] = anthropic_body.get("top_k", 20)
    oai_body["min_p"] = anthropic_body.get("min_p", 0.0)

    if "stop_sequences" in anthropic_body:
        oai_body["stop"] = anthropic_body["stop_sequences"]

    if "tools" in anthropic_body:
        oai_body["tools"] = _translate_tools_to_openai(anthropic_body["tools"])

    if "tool_choice" in anthropic_body:
        oai_body["tool_choice"] = _translate_tool_choice_to_openai(anthropic_body["tool_choice"])

    return oai_body


def translate_response(oai_response: dict, original_model: str) -> dict:
    """Translate an OpenAI chat completion response to Anthropic Messages format.

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
        "id": make_message_id(),
        "type": "message",
        "role": "assistant",
        "model": original_model,
        "content": content_blocks,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
        },
    }


def count_message_tokens(anthropic_body: dict) -> int:
    """Estimate token count for an Anthropic Messages request body.

    Uses cl100k_base tokenizer (GPT-4 encoding) as a proxy — accurate enough
    for routing decisions and progress display.
    """
    enc = _get_tokenizer()
    total = 0

    if anthropic_body.get("system"):
        sys = anthropic_body["system"]
        if isinstance(sys, list):
            sys = _content_to_str(sys)
        total += len(enc.encode(str(sys)))

    for msg in anthropic_body.get("messages", []):
        total += len(enc.encode(_content_to_str(msg.get("content", ""))))

    for tool in anthropic_body.get("tools", []):
        total += len(enc.encode(json.dumps(tool)))

    return total
