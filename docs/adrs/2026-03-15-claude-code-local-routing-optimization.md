# ADR: Claude Code Local LLM Routing — Configuration and Optimization

- **Date:** 2026-03-15
- **Status:** Accepted
- **Repos/Services affected:** homelab-ai (`llm-router/routers/anthropic.py`, `scripts/setup-claude-code.sh`)
- **Tasks:** homelab-ai-019, homelab-ai-020, homelab-ai-021, homelab-ai-022
- **Related:**
  - [2026-02-27-anthropic-proxy-tool-use-translation.md](2026-02-27-anthropic-proxy-tool-use-translation.md)
  - [2026-02-27-vllm-awq-marlin-and-wsl2-optimization.md](2026-02-27-vllm-awq-marlin-and-wsl2-optimization.md)
- **Source:** Unsloth Claude Code documentation (https://unsloth.ai/docs/basics/claude-code)

## Context

The llm-router Anthropic proxy (`/v1/messages`) allows Claude Code to route through local vLLM models
via `ANTHROPIC_BASE_URL`. The proxy was implemented and working as of 2026-02-27, but several
configuration details were undocumented, non-standardized across machines, and suboptimal for
inference throughput.

Five issues identified:

### 1. Attribution header invalidates KV cache

Claude Code sends an attribution header (`X-Anthropic-Attribution` or equivalent) on every request.
On local backends this header invalidates the KV cache — the backend cannot reuse prior prompt
computation, and each request re-processes the full system prompt + conversation history from
scratch. Unsloth identifies this as causing **~90% slower inference** on local models.

The fix is `CLAUDE_CODE_ATTRIBUTION_HEADER: 0`, but it **must** be set in `~/.claude/settings.json`,
not as an environment variable. The settings file is read before the client initializes; env vars
arrive too late to suppress the header.

### 2. No sampling defaults for Qwen3.5

Claude Code does not send sampling parameters (temperature, top_p, etc.) in its API requests —
it leaves these to the backend. The proxy was passing them through only if the client provided
them, so vLLM fell back to its own defaults for every Claude Code session.

Unsloth's recommended parameters for Qwen3.5-series models in agentic coding contexts:

| Parameter | Value |
|-----------|-------|
| temperature | 0.6 |
| top_p | 0.95 |
| top_k | 20 |
| min_p | 0.00 |

### 3. Machine setup not standardized

The required `~/.claude/settings.json` entries were applied manually per-machine. There is no
shared script or documentation — a new machine joining the fleet would silently run with
cache-invalidating defaults.

### 4. Context window undersized for Claude Code sessions

vLLM is currently configured at `max_model_len=65536` (64K). A typical Claude Code session
includes: system prompt + SOUL/CLAUDE.md (~8–12K tokens), large file reads (10–30K), and
dozens of tool turns accumulating in history. At 64K the context fills quickly and Claude Code
begins truncating. Qwen3.5-27B supports 131,072 tokens natively.

### 5. KV cache not quantized

No KV cache dtype override is configured in vLLM. The default is `auto` (fp16/bf16 depending
on model dtype). At 131K context with two GPUs, KV cache at fp16 consumes ~8GB VRAM. Using
`fp8` reduces this to ~4GB, freeing headroom for larger batches or more context.

## Decisions

### 1. Suppress attribution header via settings.json (implemented)

All fleet machines running Claude Code must have in `~/.claude/settings.json`:

```json
{
  "CLAUDE_CODE_ATTRIBUTION_HEADER": 0,
  "CLAUDE_CODE_ENABLE_TELEMETRY": "0",
  "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
  "effortLevel": "high"
}
```

These are merged (not overwriting) by `scripts/setup-claude-code.sh`.

### 2. Inject Qwen3.5 sampling defaults in llm-router proxy (implemented)

Modify `translate_anthropic_to_openai()` in `llm-router/routers/anthropic.py` to inject
sampling defaults when the client does not provide them. Cloud backends (zai, claude-harness)
ignore unknown or extra fields.

```python
# Before (pass-through only):
for field in ("temperature", "top_p"):
    if field in anthropic_body:
        oai_body[field] = anthropic_body[field]

# After (inject defaults):
oai_body["temperature"] = anthropic_body.get("temperature", 0.6)
oai_body["top_p"] = anthropic_body.get("top_p", 0.95)
oai_body["top_k"] = anthropic_body.get("top_k", 20)
oai_body["min_p"] = anthropic_body.get("min_p", 0.0)
```

### 3. Shared setup script (implemented)

`scripts/setup-claude-code.sh` — merges required settings into `~/.claude/settings.json`
without overwriting existing config. Idempotent. Works on Linux and macOS. Includes
documentation for the `hal-code` alias.

### 4. Expand context window to 131,072 (planned — homelab-ai-020)

Update `llm-manager/models.json` `max_model_len` to `131072` for `qwen3.5-27b-abliterated`.
This is a deployment change requiring a model reload. Blocked by: abliterated model CI build.

### 5. Enable fp8 KV cache quantization (planned — homelab-ai-021)

Add `--kv-cache-dtype fp8` to vLLM launch args in `docker-compose.gaming.yml`. Deploy
together with context window expansion. The two changes must be deployed simultaneously —
131K context at fp16 KV cache risks OOM on 48GB.

## Consequences

**Immediate (attribution header + sampling defaults):**
- ~90% faster inference on local models for KV-cached multi-turn sessions
- Claude Code sessions now use Qwen3.5-optimal sampling without any client-side config
- Both changes are transparent — no Claude Code config changes needed per-session

**After next deploy (context window + KV cache):**
- Claude Code sessions can sustain 131K token context (~2–3x current limit)
- Full system prompt + large file trees + hundreds of tool turns fit without truncation
- fp8 KV cache trades marginal quality (imperceptible at coding tasks) for ~4GB VRAM savings

**Ongoing:**
- New fleet machines must run `scripts/setup-claude-code.sh` once to get the settings.json entries
- The setup script should be re-run after any Claude Code major version upgrade to verify settings

## How to Use

### New machine setup

```bash
cd /path/to/homelab-ai
./scripts/setup-claude-code.sh
```

### Route Claude Code to local llm-router

Add to `~/.bashrc` or `~/.zshrc`:

```bash
export HOMELAB_AI_API_KEY="<your-llm-router-key>"
alias hal-code='ANTHROPIC_BASE_URL="https://homelab-ai-api.server.unarmedpuppy.com" ANTHROPIC_API_KEY="$HOMELAB_AI_API_KEY" claude'
```

Then run `hal-code` instead of `claude` to route all inference through local models with
full fallback chain: gaming-pc (qwen3.5-27b) → zai (glm-5) → claude-harness (Anthropic).
