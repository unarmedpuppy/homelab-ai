# Anthropic Proxy — Architecture Reference

How Claude Code routes through local models via the llm-router.

## Mental Model

There are three separate layers in this system. Understanding where each one sits prevents confusion:

```
Layer 1: vLLM
  Runs model inference in a Docker container managed by llm-manager.
  Speaks OpenAI format (/v1/chat/completions).
  Produces tool_calls JSON — it does NOT execute tools.

Layer 2: llm-router
  Sits in front of vLLM. Has two modes:

  Proxy mode (/v1/chat/completions, /v1/messages):
    Takes a request, picks a backend, forwards it. Tools defined by caller.

  Agent mode (POST /agent/run):
    Owns the agentic loop. Has its own tool registry (file ops, shell, git).
    Calls vLLM, executes tools, loops. No Claude Code involved.

Layer 3: Claude Code / agent-harness
  Agentic shell that wraps a model via API.
  Has its own tools (Bash, Read, Write, Edit, Glob, Grep, etc.).
  When ANTHROPIC_BASE_URL is set, redirects Anthropic SDK calls to the router.
```

## The Anthropic Proxy Path

```
Claude Code CLI
  ↓  POST /v1/messages (Anthropic Messages API format)
llm-router  routers/anthropic.py
  → translate_anthropic_to_openai()
  ↓  POST /v1/chat/completions (OpenAI format)
ProviderManager  →  gaming-pc-3090 (qwen3-32b-awq)
                 →  zai (glm-5)          [16K-100K context escalation]
                 →  claude-harness        [last resort]
  ↑  OpenAI chat completion response
  → translate_openai_to_anthropic()
  ↑  Anthropic Messages API response
Claude Code CLI
```

## Configuring Claude Code to Use Local Models

```bash
export ANTHROPIC_BASE_URL=https://homelab-ai.server.unarmedpuppy.com
export ANTHROPIC_API_KEY=<llm-router-api-key>
claude  # or: claude -p "prompt"
```

The API key is a llm-router key (not an Anthropic key). Get one from the router's
key management endpoint or from the dashboard settings.

To revert to Anthropic:
```bash
unset ANTHROPIC_BASE_URL
```

## What Gets Translated

### Request

| Anthropic field | → | OpenAI field |
|-----------------|---|--------------|
| `system` (string or block list) | → | `messages[0]` with `role: system` |
| `messages[].content` (string) | → | `messages[].content` (passthrough) |
| `messages[].content` (assistant with tool_use) | → | `role: assistant` with `tool_calls` array |
| `messages[].content` (user with tool_result) | → | `role: tool` messages |
| `tools[].input_schema` | → | `tools[].function.parameters` |
| `tool_choice: "any"` | → | `tool_choice: "required"` |
| `tool_choice: {type: "tool", name: "x"}` | → | `tool_choice: {type: "function", function: {name: "x"}}` |
| `stop_sequences` | → | `stop` |

### Response (non-streaming)

| OpenAI field | → | Anthropic field |
|--------------|---|-----------------|
| `choices[0].message.content` | → | `content[0]` text block |
| `choices[0].message.tool_calls[]` | → | `content[]` tool_use blocks |
| `finish_reason: "tool_calls"` | → | `stop_reason: "tool_use"` |
| `finish_reason: "length"` | → | `stop_reason: "max_tokens"` |

### Response (streaming)

| OpenAI SSE | → | Anthropic SSE |
|------------|---|---------------|
| First delta with content | → | `message_start` + `ping` |
| `delta.content` text | → | `content_block_start` (text) + `content_block_delta` (text_delta) |
| `delta.tool_calls[i].id` appears | → | Close text block (if open) + `content_block_start` (tool_use) |
| `delta.tool_calls[i].function.arguments` chunks | → | `content_block_delta` (input_json_delta) |
| Stream end | → | Close all open blocks + `message_delta` + `message_stop` |

## What's NOT Translated

- **Image content blocks** (`type: image`) — dropped. Claude Code doesn't send images in coding sessions.
- **Thinking/extended thinking** — not forwarded. Qwen3's thinking mode is controlled at the vLLM level.
- **Model selection** — the `model` field in the request is ignored; routing uses `"auto"` always.
  The original model name is preserved in the response for Claude Code's display only.

## Choosing Between Proxy Mode and Agent Mode

| Use case | Right tool |
|----------|-----------|
| Interactive Claude Code session | Proxy mode — Claude Code manages the loop |
| Autonomous agentic task (no human in loop) | Agent mode (`POST /agent/run`) |
| Local model with Claude Code tools | Proxy mode |
| Local model with llm-router's skill-based tools | Agent mode |
| Need to test if a model can follow tool calls | Agent mode (more predictable) |

The proxy is best when you want the full Claude Code experience (slash commands, memory, hooks, permissions) backed by a local model for cost/latency. The agent loop is better for fire-and-forget tasks where you want controlled, audited tool execution.

## Local Model Tool Calling Quality

`qwen3-32b-awq` supports function calling reliably but has behavioral differences from Claude:

- More verbose: tends to emit reasoning text before tool calls
- Occasionally retries a tool call it already made
- Thinking mode (`/think`) can produce very long outputs before acting — disable with `/no_think` if using Claude Code's shell

For best results with Claude Code + local model:
- Keep sessions focused (single task per session)
- Prefer `claude -p "task"` (non-interactive) over interactive mode for agentic work
- If the model gets stuck in a loop, the complexity classifier will escalate to glm-5 or claude-harness

## Debugging

Check what the proxy is doing via router logs:

```bash
# On server via Gilfoyle
docker logs llm-router --tail 100 | grep "\[Anthropic\]"
```

Log format:
```
[Anthropic] 'claude-sonnet-4-6' → Gaming PC (RTX 3090) (qwen3-32b-awq), stream=True, tools=8
```

The `tools=N` count tells you if tool definitions are being forwarded.

## Files

| File | Purpose |
|------|---------|
| `llm-router/routers/anthropic.py` | The proxy implementation |
| `llm-router/router.py` | ProviderManager, routing logic |
| `llm-router/config/providers.yaml` | Backend definitions and priorities |
| `docs/adrs/2026-02-26-anthropic-compat-proxy-in-llm-router.md` | Initial proxy ADR |
| `docs/adrs/2026-02-27-anthropic-proxy-tool-use-translation.md` | Tool use translation ADR |
