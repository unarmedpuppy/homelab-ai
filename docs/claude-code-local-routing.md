# Claude Code → Local LLM: End-to-End Reference

How Claude Code agents communicate with local inference hardware through the homelab stack.
Covers the full request lifecycle, format translation, tool calling, streaming, routing, and the grove agent system.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Mac Mini / Dev Machine                      │
│                                                                 │
│  ┌──────────────┐   Anthropic format    ┌─────────────────────┐ │
│  │  Claude Code │ ─────────────────────▶│                     │ │
│  │  (CLI)       │◀─────────────────────│   llm-router        │ │
│  └──────────────┘   Anthropic format    │   /v1/messages      │ │
│                                         │   (FastAPI)         │ │
│  ┌──────────────┐                       │                     │ │
│  │  grove serve │                       │   bridge/           │ │
│  │  (oak:8014)  │──spawns──▶ Claude     │   translate.py      │ │
│  │  (ash:8019)  │            Code       │   stream.py         │ │
│  └──────────────┘                       └──────────┬──────────┘ │
│                                                     │           │
└─────────────────────────────────────────────────────┼───────────┘
                                    OpenAI format      │
                                    ┌──────────────────┘
                                    │
                    ┌───────────────▼──────────────────┐
                    │         ProviderManager            │
                    │         (routing chain)            │
                    └───────┬───────────────┬───────────┘
                            │               │
               Primary      │               │  Fallback
                            ▼               ▼
              ┌─────────────────┐   ┌──────────────────┐
              │  Gaming PC      │   │  Z.ai (cloud)    │
              │  vLLM           │   │  GLM-5           │
              │  qwen3-32b-awq  │   │                  │
              │  2× RTX 3090    │   │                  │
              └─────────────────┘   └──────────────────┘
```

Claude Code speaks only Anthropic's API format. vLLM (and every open-source inference server) speaks OpenAI format. The llm-router's `bridge/` module is the translation layer between them — it has zero dependencies on the router itself and can be used anywhere.

---

## The bridge/ Module

`llm-router/bridge/` is a self-contained translation package. No auth, no provider, no FastAPI.

```
bridge/
├── __init__.py      # Public API: translate_request, translate_response,
│                    #             translate_stream, count_message_tokens
├── translate.py     # All request/response translation (pure functions)
└── stream.py        # Async SSE streaming generator
```

Public API:

| Function | Input → Output |
|----------|----------------|
| `translate_request(body)` | Anthropic Messages body → OpenAI chat completions body |
| `translate_response(oai, model)` | OpenAI response dict → Anthropic Messages response dict |
| `translate_stream(url, headers, body, model, tokens)` | Async generator of Anthropic SSE strings |
| `count_message_tokens(body)` | Anthropic Messages body → int (token estimate) |

---

## Request Translation: Anthropic → OpenAI

### System Prompt

Anthropic puts the system prompt as a top-level field. OpenAI puts it as the first message.

```
Anthropic request:                  OpenAI request:
{                                   {
  "system": "You are Oak...",         "messages": [
  "messages": [...]                     {"role": "system",
}                                          "content": "You are Oak..."},
                                         ...
                                       ]
                                   }
```

System can also be a list of content blocks (Anthropic supports this for cache_control). These are flattened to a single string for OpenAI.

### Message History

Plain string content passes through unchanged. List content is translated block-by-block.

#### Assistant messages

```
Anthropic:                              OpenAI:
{                                       {
  "role": "assistant",                    "role": "assistant",
  "content": [                            "content": "I'll run that.",
    {"type": "text",                      "tool_calls": [{
       "text": "I'll run that."},            "id": "toolu_abc",
    {"type": "tool_use",                    "type": "function",
       "id": "toolu_abc",                   "function": {
       "name": "bash",                        "name": "bash",
       "input": {"command": "ls"}}            "arguments": "{\"command\":\"ls\"}"
  ]                                       }}]
}                                       }
```

#### User messages with tool results

Anthropic bundles tool results inside user messages. OpenAI has a separate `role: tool` message type.

```
Anthropic:                              OpenAI (split):
{                                       {"role": "tool",
  "role": "user",                          "tool_call_id": "toolu_abc",
  "content": [                             "content": "file1.py\nfile2.py"}
    {"type": "tool_result",
       "tool_use_id": "toolu_abc",
       "content": "file1.py\nfile2.py"}
  ]
}
```

If `is_error: true` is set on the tool_result, the content is prefixed with `[ERROR]` so the model understands the tool failed.

If text blocks appear alongside tool_result blocks in the same user message, they are flushed as a separate `role: user` message before the tool messages.

#### User messages with images

Anthropic image blocks translate to OpenAI `image_url` content. Multiple content types coexist in a list.

```
Anthropic:                              OpenAI:
{                                       {
  "role": "user",                         "role": "user",
  "content": [                            "content": [
    {"type": "text",                        {"type": "text",
       "text": "what is this?"},               "text": "what is this?"},
    {"type": "image",                       {"type": "image_url",
       "source": {                             "image_url": {
         "type": "base64",                       "url": "data:image/png;base64,..."
         "media_type": "image/png",           }}
         "data": "..."}}                  ]
  ]                                     }
}
```

Images in tool result content (e.g. a screenshot tool returning an image) are extracted and emitted as a follow-up `role: user` message — OpenAI does not support images inside tool messages.

### Tools Array

```
Anthropic:                              OpenAI:
{                                       {
  "name": "bash",                         "type": "function",
  "description": "Run commands",          "function": {
  "input_schema": {                         "name": "bash",
    "type": "object",                       "description": "Run commands",
    "properties": {                         "parameters": {
      "command": {"type": "string"}           "type": "object",
    },                                        "properties": {
    "required": ["command"]                     "command": {"type": "string"}
  }                                         },
}                                           "required": ["command"]
                                          }
                                        }
                                      }
```

Key difference: `input_schema` → `parameters`, wrapped in `{"type": "function", "function": {...}}`.

### Tool Choice

| Anthropic | OpenAI |
|-----------|--------|
| `"auto"` | `"auto"` |
| `"any"` | `"required"` |
| `"none"` | `"none"` |
| `{"type": "tool", "name": "bash"}` | `{"type": "function", "function": {"name": "bash"}}` |

### Sampling Defaults

Claude Code sends no sampling parameters — it relies on the backend. Without defaults, vLLM falls back to its own settings. The bridge injects Qwen3 optimal values (per Unsloth recommendations for agentic coding):

```python
temperature = 0.6
top_p       = 0.95
top_k       = 20
min_p       = 0.0
```

Cloud backends (Z.ai, Anthropic) ignore these extra fields.

### Thinking Mode

vLLM-specific flag to disable Qwen3's extended thinking (`<think>` tokens). Claude Code does not know how to handle `<think>` blocks appearing in the streamed output — they would render as visible text. Disabled by default.

```python
"chat_template_kwargs": {"enable_thinking": False}
```

This field (along with `top_k`, `min_p`) is stripped when routing to cloud backends, which reject unknown fields with HTTP 400.

---

## Response Translation: OpenAI → Anthropic

### Non-Streaming

```
OpenAI response:                        Anthropic response:
{                                       {
  "choices": [{                           "id": "msg_...",
    "message": {                          "type": "message",
      "content": "Here's the result",     "role": "assistant",
      "tool_calls": [{                    "model": "claude-sonnet-4-6",
        "id": "call_abc",                 "content": [
        "type": "function",                 {"type": "text",
        "function": {                          "text": "Here's the result"},
          "name": "bash",                   {"type": "tool_use",
          "arguments": "{\"cmd\":\"ls\"}"      "id": "call_abc",
        }                                     "name": "bash",
      }]                                      "input": {"cmd": "ls"}}
    },                                  ],
    "finish_reason": "tool_calls"       "stop_reason": "tool_use",
  }],                                   "stop_sequence": null,
  "usage": {                            "usage": {
    "prompt_tokens": 1200,                "input_tokens": 1200,
    "completion_tokens": 45              "output_tokens": 45,
  }                                       "cache_creation_input_tokens": 0,
}                                         "cache_read_input_tokens": 0
                                        }
                                      }
```

`finish_reason` → `stop_reason` mapping:
- `"stop"` → `"end_turn"`
- `"length"` → `"max_tokens"`
- `"tool_calls"` → `"tool_use"`

Cache token fields are always present (zero) — Claude Code's token counter requires them to exist in the response.

### Streaming

OpenAI streams as newline-delimited JSON (`data: {...}\n\n`). Anthropic streams as typed SSE events with a specific event sequence. The bridge translates chunk-by-chunk while maintaining a state machine.

#### Full Anthropic SSE sequence (text + tool call)

```
event: message_start
data: {"type":"message_start","message":{"id":"msg_...","role":"assistant","content":[],
       "usage":{"input_tokens":1200,"output_tokens":0,
                "cache_creation_input_tokens":0,"cache_read_input_tokens":0}}}

event: ping
data: {"type":"ping"}

event: content_block_start
data: {"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"I'll"}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":" run that."}}

event: content_block_stop
data: {"type":"content_block_stop","index":0}

event: content_block_start
data: {"type":"content_block_start","index":1,
       "content_block":{"type":"tool_use","id":"toolu_abc","name":"bash","input":{}}}

event: content_block_delta
data: {"type":"content_block_delta","index":1,
       "delta":{"type":"input_json_delta","partial_json":"{\"command\":"}}

event: content_block_delta
data: {"type":"content_block_delta","index":1,
       "delta":{"type":"input_json_delta","partial_json":"\"ls\"}"}}

event: content_block_stop
data: {"type":"content_block_stop","index":1}

event: message_delta
data: {"type":"message_delta","delta":{"stop_reason":"tool_use","stop_sequence":null},
       "usage":{"output_tokens":23}}

event: message_stop
data: {"type":"message_stop"}
```

#### OpenAI streaming chunks that produce this

```
data: {"choices":[{"delta":{"content":"I'll"},"finish_reason":null}]}
data: {"choices":[{"delta":{"content":" run that."},"finish_reason":null}]}
data: {"choices":[{"delta":{"tool_calls":[{"index":0,"id":"toolu_abc","function":{"name":"bash","arguments":""}}]},"finish_reason":null}]}
data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"{\"command\":"}}]},"finish_reason":null}]}
data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"\"ls\"}"}}]},"finish_reason":"tool_calls"}]}
data: [DONE]
```

#### Streaming state machine

The bridge maintains state across chunks:

- `sent_message_start` — emits `message_start` on first chunk with actual content
- `text_block_open` / `text_block_index` — tracks the current text block
- `tool_blocks: dict[oai_index → {anthr_index, id, name}]` — maps OpenAI tool indexes to Anthropic block indexes
- `next_anthr_index` — monotonically increasing Anthropic content block index
- `finish_reason` — accumulated from chunks, used in `message_delta` at the end

Text blocks are closed before the first tool block opens. Tool blocks are closed in Anthropic index order during finalization.

---

## The Tool Calling Loop

Claude Code's agentic behavior runs as a multi-turn conversation. Each tool call is a full round-trip through the proxy.

```
Claude Code                   llm-router                    vLLM
     │                             │                          │
     │  POST /v1/messages          │                          │
     │  (system + user msg,        │                          │
     │   tools array defined)      │                          │
     │────────────────────────────▶│  translate_request()     │
     │                             │──────────────────────────▶
     │                             │                          │ generates
     │                             │  translate_stream()      │ tool call
     │◀────────────────────────────│◀─────────────────────────│
     │  stop_reason: tool_use      │                          │
     │  content: [tool_use block]  │                          │
     │                             │                          │
     │ executes tool locally       │                          │
     │ (bash, read, write, etc.)   │                          │
     │                             │                          │
     │  POST /v1/messages          │                          │
     │  (history + tool_result     │                          │
     │   in user message)          │                          │
     │────────────────────────────▶│  translate_request()     │
     │                             │  tool_result → role:tool │
     │                             │──────────────────────────▶
     │                             │                          │ reasons
     │                             │  translate_stream()      │ over result
     │◀────────────────────────────│◀─────────────────────────│
     │  stop_reason: end_turn      │                          │
     │  (or another tool_use)      │                          │
```

Each turn is a complete POST /v1/messages with the full conversation history. The model never maintains state — the client sends everything every time.

Claude Code has 6 core tools: `bash`, `read`, `write`, `edit`, `glob`, `grep`. All execute locally on the machine running Claude Code. The model only sees the results.

---

## Routing Chain

```
POST /v1/messages
       │
       ▼
  ProviderManager.route_request()
       │
       ├── X-Provider header set? ──▶ route directly to named provider
       │
       ├── model = "auto"?
       │       │
       │       ├── gaming-pc-3090 healthy? ──▶ qwen3-32b-awq  [primary]
       │       │
       │       ├── gaming-pc-3090 down?   ──▶ zai (GLM-5)     [fallback]
       │       │
       │       └── both down?             ──▶ 503 Service Unavailable
       │
       └── model = specific name? ──▶ MODEL_ALIASES lookup → named provider
```

Provider health is tracked by ProviderManager. Failed requests increment a failure counter. After N failures, the provider is marked unhealthy and excluded from routing until a health check recovers it.

Cloud-specific field stripping happens after provider selection — if the selected provider is `ProviderType.CLOUD`, the bridge strips `chat_template_kwargs`, `top_k`, and `min_p` before forwarding.

### Provider Reference

| Provider ID | Backend | Model | Use case |
|-------------|---------|-------|----------|
| `gaming-pc-3090` | vLLM on gaming PC | qwen3-32b-awq | Primary inference, all agentic tasks |
| `zai` | Z.ai API | GLM-5 | Auto-fallback when 3090 unavailable |
| `server-3070` | vLLM on home server | qwen2.5-7b-awq | Explicit only, lightweight tasks |
| `willow` | Willow grove agent proxy | Claude (subscription) | Explicit only, job-based |

---

## Auth

The llm-router accepts two auth formats from the Anthropic SDK:

```
x-api-key: <llm-router-key>          (Anthropic SDK default)
Authorization: Bearer <llm-router-key>  (alternative)
```

These are not Anthropic API keys — they are llm-router API keys stored in the router's database. When Claude Code sees `ANTHROPIC_API_KEY=<your-llm-router-key>` it sends it as `x-api-key`, which the router validates locally without touching Anthropic's infrastructure.

---

## KV Cache and Performance

### Attribution header

Claude Code sends an `x-stainless-*` attribution header on every request. On local vLLM, this header invalidates the KV cache — the backend cannot reuse prior computation and must re-process the full system prompt + conversation history from scratch on every turn. This causes ~90% slower multi-turn inference.

Fix (must be in `~/.claude/settings.json`, not env vars — env vars arrive too late):

```json
{
  "CLAUDE_CODE_ATTRIBUTION_HEADER": 0,
  "CLAUDE_CODE_ENABLE_TELEMETRY": "0",
  "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"
}
```

### vLLM flags for tool calling

vLLM requires explicit flags to enable structured tool call output:

```
--enable-auto-tool-choice
--tool-call-parser hermes
--reasoning-parser qwen3
```

Without these, vLLM does not emit `tool_calls` in its response delta — it outputs raw text that looks like a tool call but cannot be parsed. The gaming PC has these flags active.

### Context window

qwen3-32b-awq supports 131,072 tokens. A typical Claude Code agentic session uses:
- System prompt (SOUL + CLAUDE.md): ~8–12K
- File reads (several large files): ~10–30K
- Tool call history (dozens of turns): ~20–50K

Total: 40–90K tokens for a heavy session. vLLM is configured at 65,536 tokens (64K) — fine for most sessions but truncation can occur on deep file analysis tasks.

---

## grove Agent System

The grove fleet runs Claude Code agents as long-running processes. Each agent is a grove serve instance that accepts jobs (via Mattermost, A2A calls, or scheduler) and runs them as Claude Code subprocesses.

### How an agent session works

```
Mattermost message
        │
        ▼
grove serve (e.g. oak:8014)
   - receives POST /v1/agent/chat
   - spawns Claude Code subprocess:
       ANTHROPIC_BASE_URL=https://homelab-ai-api.server.unarmedpuppy.com
       ANTHROPIC_API_KEY=<llm-router-key>
       claude --print --output-format json "<prompt>"
   - captures stdout
   - stores session, returns response
```

The Claude Code subprocess behaves identically to an interactive session — it has the same tools, the same system prompt loading, the same token budget. The only difference is it exits after completing the task instead of waiting for the next user input.

### Agent roster

| Agent | Host | Port | Model route |
|-------|------|------|-------------|
| oak | Mac Mini | 8014 | auto (llm-router) |
| ash | Mac Mini | 8019 | auto (llm-router) |
| elm | home server | 8018 | auto (llm-router) |
| birch | gaming PC | 8021 | auto (llm-router) |
| willow | home server | 8025 | Claude (subscription, bypass llm-router) |
| prism | padme (Pi, air-gapped) | 8030 | auto (llm-router via Tailscale) |

All agents default to `model=auto` via the llm-router. They send Anthropic-format requests to `homelab-ai-api.server.unarmedpuppy.com`, which translates and routes to the gaming PC's vLLM by default.

### Fleet inference flow (full path)

```
oak (Mac Mini)
    │  POST /v1/messages  (Anthropic format)
    │  ANTHROPIC_BASE_URL = https://homelab-ai-api.server.unarmedpuppy.com
    ▼
llm-router (home server)
    │  bridge.translate_request()  → OpenAI format
    │  ProviderManager.route()     → gaming-pc-3090
    │  strip cloud-only fields
    ▼
vLLM (gaming PC, 2× RTX 3090)
    │  qwen3-32b-awq
    │  --enable-auto-tool-choice --tool-call-parser hermes
    │  streaming SSE response (OpenAI format)
    ▼
llm-router
    │  bridge.translate_stream()  → Anthropic SSE format
    ▼
oak
    │  receives Anthropic SSE
    │  Claude Code processes tool_use blocks
    │  executes tools locally
    │  sends next turn
```

Round-trip latency (typical): first token ~1–3s, ~40–80 tok/s throughput on qwen3-32b-awq at AWQ 4-bit.

---

## Token Counting

Claude Code calls `POST /v1/messages/count_tokens` before some operations to estimate context size. The bridge handles this with `count_message_tokens()`:

- Tokenizes system prompt, all message content, tool definitions
- Uses `cl100k_base` (GPT-4 tokenizer) as a proxy — not exact for Qwen3 but close enough for routing decisions and progress display
- Returns `{"input_tokens": N}`

Token count is also used inside the streaming path to populate `input_tokens` in `message_start` (vLLM does not report prompt tokens in streaming mode, only in non-streaming usage objects).

---

## Prompt Caching

Not currently used. Prompt caching is an Anthropic API feature — you mark sections of the prompt with `cache_control: {type: "ephemeral"}` and Anthropic caches the KV state server-side, saving tokens and latency on repeated prefixes.

vLLM has internal KV cache (automatic prefix caching), but it's not exposed via the API in the same way. The `cache_control` blocks in Anthropic requests are stripped during translation. The cache token fields (`cache_creation_input_tokens`, `cache_read_input_tokens`) are always returned as zero — not because caching is broken, but because there is genuinely no cache activity to report against local vLLM.

If routing ever shifts back to Anthropic's API directly, caching would work natively — especially valuable for the large system prompts every Claude Code session sends.

---

## Known Limitations

| Limitation | Status | Impact |
|------------|--------|--------|
| Prompt caching | Not applicable (local vLLM) | Token cost $0, latency not reduced on repeated prefixes |
| Context window | 65K tokens configured (131K supported) | Long sessions can truncate |
| Tool call quality | Model-dependent | Qwen3-32b strong but occasionally verbose |
| Images in tool messages | Split into follow-up user message | Works but non-standard |
| Cache token fields | Always zero | Claude Code token counter is accurate but shows no savings |
| Birch grove migration | Pending | Gaming PC agent not yet on grove serve |

---

## Configuration Reference

### Claude Code → llm-router

```bash
export ANTHROPIC_BASE_URL="https://homelab-ai-api.server.unarmedpuppy.com"
export ANTHROPIC_API_KEY="<llm-router-api-key>"   # not an Anthropic key
```

### ~/.claude/settings.json (required on every fleet machine)

```json
{
  "CLAUDE_CODE_ATTRIBUTION_HEADER": 0,
  "CLAUDE_CODE_ENABLE_TELEMETRY": "0",
  "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
  "effortLevel": "high"
}
```

### grove agent .env

```bash
ANTHROPIC_BASE_URL=https://homelab-ai-api.server.unarmedpuppy.com
ANTHROPIC_API_KEY=<llm-router-key>
GROVE_AGENT=oak                    # or ash, elm, etc.
GROVE_HOME=/Users/aijenquist/.grove
```

### vLLM launch flags (gaming PC)

```bash
vllm serve qwen3-32b-awq \
  --tensor-parallel-size 2 \
  --enable-auto-tool-choice \
  --tool-call-parser hermes \
  --reasoning-parser qwen3 \
  --max-model-len 65536 \
  --quantization awq_marlin
```

---

## Related Documents

| Document | What it covers |
|----------|----------------|
| [ADR: Tool Use Translation (2026-02-27)](adrs/2026-02-27-anthropic-proxy-tool-use-translation.md) | Decision to implement full tool format translation |
| [ADR: Claude Code Routing Optimization (2026-03-15)](adrs/2026-03-15-claude-code-local-routing-optimization.md) | Attribution header, sampling defaults, context window |
| [ADR: Anthropic Proxy Initial (2026-02-26)](adrs/2026-02-26-anthropic-compatible-proxy.md) | Original proxy implementation decision |
| [llm-router/bridge/](../llm-router/bridge/) | The translation module — read the source for exact behavior |
