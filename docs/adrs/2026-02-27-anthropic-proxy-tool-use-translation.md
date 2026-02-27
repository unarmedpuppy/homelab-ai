# ADR: Full Tool Use Translation in Anthropic Proxy

- **Date**: 2026-02-27
- **Status**: Accepted
- **Repos/Services affected**: homelab-ai (`llm-router/routers/anthropic.py`)

## Context

The Anthropic-compatible proxy (`/v1/messages`) was implemented on 2026-02-26 to allow Claude Code to route through the llm-router to local models. That initial implementation deliberately deferred tool use:

> "Only the Anthropic features Claude Code actually uses are translated (text content, system prompts, streaming) — tool use and vision pass through as plain text"

The consequence: when Claude Code sends a conversation containing tool_use or tool_result content blocks, the proxy flattened them to strings like `[Tool call: bash({"command":"ls"})]` and `[Tool result: file1.py ...]`. The local model received garbled plain text and could not:

1. Respond with a structured tool call the local model wants to make
2. Receive tool results in a format it can reason over
3. Participate properly in Claude Code's tool loop at all

In practice, Claude Code routed to local models produced degraded or nonsensical output on any agentic task because the tool context was unreadable.

## Decision

Implement full Anthropic ↔ OpenAI tool use format translation in `routers/anthropic.py`.

## Format Mapping

### Request: Tools Array

| Anthropic | OpenAI |
|-----------|--------|
| `{"name": "x", "description": "...", "input_schema": {schema}}` | `{"type": "function", "function": {"name": "x", "description": "...", "parameters": {schema}}}` |

Key: `input_schema` → `parameters`; wrapper added.

### Request: tool_choice

| Anthropic | OpenAI |
|-----------|--------|
| `"auto"` | `"auto"` |
| `"any"` | `"required"` |
| `"none"` | `"none"` |
| `{"type": "tool", "name": "bash"}` | `{"type": "function", "function": {"name": "bash"}}` |

### Request: Message History

**Assistant message with tool_use blocks:**

Anthropic:
```json
{"role": "assistant", "content": [
  {"type": "text", "text": "Checking..."},
  {"type": "tool_use", "id": "toolu_abc", "name": "bash", "input": {"command": "ls"}}
]}
```

OpenAI:
```json
{"role": "assistant", "content": "Checking...", "tool_calls": [
  {"id": "toolu_abc", "type": "function", "function": {"name": "bash", "arguments": "{\"command\":\"ls\"}"}}
]}
```

**User message with tool_result blocks:**

Anthropic:
```json
{"role": "user", "content": [
  {"type": "tool_result", "tool_use_id": "toolu_abc", "content": "file1.py\nfile2.py"}
]}
```

OpenAI (split into role:tool messages):
```json
{"role": "tool", "tool_call_id": "toolu_abc", "content": "file1.py\nfile2.py"}
```

Mixed user text + tool_results: text flushed as a separate role:user message; tool_results become role:tool messages.

### Response: Non-Streaming

OpenAI response with tool_calls:
```json
{"choices": [{"message": {"content": null, "tool_calls": [
  {"id": "call_abc", "type": "function", "function": {"name": "bash", "arguments": "{\"command\":\"ls\"}"}}
]}, "finish_reason": "tool_calls"}]}
```

Translated to Anthropic:
```json
{"content": [
  {"type": "tool_use", "id": "call_abc", "name": "bash", "input": {"command": "ls"}}
], "stop_reason": "tool_use"}
```

### Response: Streaming

OpenAI streams tool_calls via `delta.tool_calls[{index, id, function.name, function.arguments}]`.

Translated to Anthropic SSE sequence:
```
event: content_block_start   → {index: N, content_block: {type: "tool_use", id: ..., name: ..., input: {}}}
event: content_block_delta   → {index: N, delta: {type: "input_json_delta", partial_json: "..."}}
event: content_block_stop    → {index: N}
```

Tool blocks follow text blocks (if any). Each tool call in the OAI stream maps to a new Anthropic content block index. finish_reason `tool_calls` → Anthropic `stop_reason: tool_use`.

## Implementation

Single file changed: `llm-router/routers/anthropic.py`

New helpers added:
- `_translate_tools_to_openai(tools)` — Anthropic tools array → OpenAI tools array
- `_translate_tool_choice_to_openai(tc)` — Anthropic tool_choice → OpenAI tool_choice
- `_translate_messages(messages)` — message history with tool_use/tool_result blocks
- `_tool_result_content_to_str(content)` — flatten tool_result content field

Updated functions:
- `translate_anthropic_to_openai` — now calls `_translate_messages` and forwards tools/tool_choice
- `translate_openai_to_anthropic` — now handles tool_calls in response
- `translate_openai_stream_to_anthropic` — streaming state machine for tool_calls deltas

`_content_to_str` retained as a utility for token counting only.

## Consequences

### What this enables

Claude Code can now use its full tool set (Bash, Read, Write, Edit, Glob, Grep, etc.) when routing through local models. The local model participates in the tool loop: it receives tool results in proper format, can emit structured tool calls, and the conversation history stays coherent across tool turns.

### Caveats

Local models vary in tool-calling quality. `qwen3-32b-awq` has strong function calling support but may still:
- Emit more verbose reasoning before tool calls than Claude does
- Occasionally hallucinate tool arguments if not prompted well
- Handle deeply nested tool result content less reliably

The `agent.py` loop in the router remains the better option for structured, autonomous agentic tasks on local models — it has its own tool registry, retry logic, and context pruning. The Anthropic proxy is the right layer for interactive Claude Code sessions where the human is in the loop.

### Vision / images

Image content blocks (`type: image`) are still dropped. Claude Code does not send images in normal coding sessions, so this is not a regression.

## Related

- ADR 2026-02-26: Anthropic-Compatible Proxy in llm-router (initial proxy implementation)
- `.agents/reference/anthropic-proxy.md` — architecture reference and mental model
