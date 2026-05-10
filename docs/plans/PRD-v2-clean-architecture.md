# Homelab AI v2 — Clean Architecture Plan

**Date**: 2026-05-10  
**Status**: APPROVED  
**Author**: Oak (with Avery input)  
**Replaces**: Current `homelab-ai` monorepo (22 directories, 15 Docker images, 7K+ lines router)

---

## 0. Executive Summary

The current homelab-ai monorepo grew organically through 370+ commits into a sprawling 22-component system where 6 of 15 Docker images are dead, the "router" is a 7,100-line application server, and responsibility boundaries are nonexistent.

This plan replaces the entire stack with a focused, cleanly separated architecture built on simple primitives. The core insight: **the current router is doing 6 jobs**. We split those into discrete services, each with a clear contract.

**Result**: 4 active repos, 6 running containers (down from 15 built), ~3,500 total lines of Python (down from 18,000+), each component under 800 lines.

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SERVER (always-on)                          │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────────┐ │
│  │ ai-gateway   │  │ dashboard-api    │  │ dashboard (React) │ │
│  │ :8000             │  │ :8010            │  │ :8011             │ │
│  │                  │  │                  │  │                   │ │
│  │ • Route requests │  │ • Trace ingest   │  │ • All UI routes   │ │
│  │ • API key auth   │  │ • Session store   │  │ • Chat, Stats,    │ │
│  │ • Trace emission │  │ • Fleet health    │  │   Providers,      │ │
│  │ • Metrics log    │  │ • Job proxy       │  │   Tasks, Agents   │ │
│  │ • Anthropic xlate│  │ • Knowledge base  │  │                   │ │
│  └────────┬─────────┘  └──────────────────┘  └───────────────────┘ │
│           │                                                         │
│           │  HTTP (Tailscale / LAN)                                 │
│           ▼                                                         │
├─────────────────────────────────────────────────────────────────────┤
│                     GAMING PC (on-demand)                           │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │ llm-manager       │  │ image-server │  │ tts-server            │ │
│  │ :8000             │  │ :8005        │  │ :8006                 │ │
│  │                  │  │              │  │                       │ │
│  │ • vLLM orchestra │  │ • FLUX gen   │  │ • Chatterbox Turbo   │ │
│  │ • llama.cpp mgmt │  │              │  │                       │ │
│  │ • Gaming mode    │  │              │  │                       │ │
│  │ • Model swap     │  │              │  │                       │ │
│  └──────────────────┘  └──────────────┘  └───────────────────────┘ │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                    SERVER (3070 — lightweight)                      │
│                                                                     │
│  ┌──────────────────┐                                               │
│  │ llm-manager       │  (same image, MODE=always-on, small models) │
│  │ :8012             │                                               │
│  └──────────────────┘                                               │
└─────────────────────────────────────────────────────────────────────┘

EXTERNAL:
  ┌──────────────────┐
  │ z.ai (GLM-5.1)   │  Cloud fallback — OpenAI-compatible API
  │ api.z.ai         │
  └──────────────────┘
```

---

## 2. Repository Structure

### 2.1 Split into 4 Repos

| Repo | Purpose | Deployed Where |
|------|---------|---------------|
| `ai-gateway` | API gateway, routing, auth, traces, Anthropic bridge | Server |
| `llm-manager` | GPU orchestration, vLLM/llama.cpp containers, gaming mode | Gaming PC + Server 3070 |
| `homelab-dashboard` | React UI + FastAPI backend | Server |
| `model-toolkit` | Quantization, abliteration, fine-tuning pipelines | Gaming PC (on-demand) |

**Why 4 repos instead of 1**: Each has a different deployment cadence, different CI targets, and different dependencies. The router changes when routing logic changes. The manager changes when GPU infrastructure changes. The dashboard changes when UI changes. The toolkit changes when you're experimenting. Mixing them guarantees conflicts.

**Why not more**: `image-server` and `tts-server` are thin FastAPI wrappers (20KB each) — they can live inside `llm-manager` repo as subdirectories since they share the same deployment target (gaming PC) and same CI pipeline. No reason for separate repos for 1-file services.

### 2.2 What Gets Killed

| Current Component | Fate |
|-------------------|------|
| `claude-harness/` | **Delete** — superseded by agent-harness repo |
| `abliteration/` | **Move** to `model-toolkit` |
| `autoawq/` | **Move** to `model-toolkit` |
| `video-server/` | **Delete** (never worked) — future video-gen is a `model-toolkit` pipeline |
| `aoe-canvas/` | **Delete** — merge concept into dashboard as a route if wanted later |
| `eval-runner/` | **Delete** — reimplement as `model-toolkit` eval pipeline when needed |
| `deploy-webhook/` | **Delete** — Gitea Actions deploy SSH handles this |
| `deploy/` | **Delete** — broken script |
| `vllm/` (custom image) | **Move** to `llm-manager` as `images/vllm-custom/` |
| `llm-tui/` | **Move** to `ai-gateway` as a sub-command |
| `.agents/` | **Delete** — stale plans/references |
| `scripts/` (31 files) | **Delete 28** — keep `harbor-push.sh`, `setup-claude-code.sh` |
| 22 ADRs | **Archive** 15+ stale ones, keep only the 5-7 that are still relevant |
| `index.html` (root) | **Delete** — build artifact |

---

## 3. Repo 1: `ai-gateway`

### 3.1 Responsibilities (and ONLY these)

1. **Route inference requests** to backends (llm-manager instances, z.ai)
2. **Authenticate** all requests via API keys (`sk-ant-...` format)
3. **Emit traces** for every request (to dashboard-api)
4. **Log metrics** for every request (tokens, latency, cost, model)
5. **Translate** Anthropic Messages API ↔ OpenAI Chat Completions
6. **Proxy** TTS and image requests to gaming PC

### 3.2 What Gets REMOVED from the Current Router

| Current Feature | Why Remove |
|----------------|------------|
| Memory system (`memory.py`, `compaction.py`, `summary.py`) | Never used in production. RAG/memory is a separate concern. |
| RAG pipeline (`rag.py`) | Never used. Embeddings + vector search ≠ routing. |
| Agent tools (`tools/` — 7 modules) | Agent tool execution is not a routing concern. Agents have their own runtimes. |
| Agent loop (`agent.py`, `agent_storage.py`) | Agent orchestration lives in agent-harness, not the router. |
| Service feeds (`service_feeds.py`) | Frigate/Immich integration has nothing to do with LLM routing. |
| Alembic migrations | Overkill for SQLite. Schema init on startup is sufficient for single-user homelab. |
| Model garden CRUD | Model discovery belongs in llm-manager. Router just needs provider endpoints. |
| Image upload (`/v1/images/upload`) | Stateful file storage doesn't belong in a stateless router. |
| Daily summaries table | Dashboard concern. |
| Harness metrics | Agent-harness concern. |

### 3.3 Target Structure

```
ai-gateway/
├── Dockerfile
├── requirements.txt
├── config/
│   └── providers.yaml          # Provider definitions (inherit current)
├── router.py                   # FastAPI app (~400 lines)
├── routing/
│   ├── __init__.py
│   ├── provider_manager.py     # Provider selection, health, concurrency (~300 lines)
│   ├── models.py               # Provider/Model Pydantic models (~100 lines)
│   └── complexity.py           # [STUB] Future: complexity-based routing
├── auth/
│   ├── __init__.py
│   └── api_keys.py             # Key generation, validation, hashing (~200 lines)
├── bridge/
│   ├── __init__.py
│   ├── translate.py            # Anthropic ↔ OpenAI translation (~300 lines) [KEEP AS-IS]
│   └── stream.py               # Anthropic SSE streaming translation (~250 lines) [KEEP AS-IS]
├── traces/
│   ├── __init__.py
│   └── emitter.py              # Fire-and-forget trace emission to dashboard-api (~80 lines)
├── db.py                       # SQLite init + connection helper (~80 lines)
├── models.py                   # Shared Pydantic models (~60 lines)
├── stream.py                   # SSE passthrough + enhanced streaming (~150 lines)
└── tests/
    └── ...
```

**Total estimate: ~1,800 lines** (down from 7,130 + 2,500 in tests)

### 3.4 API Surface

#### OpenAI-Compatible Endpoints
```
POST /v1/chat/completions        # Main inference endpoint
POST /v1/embeddings              # Embedding proxy to server 3070
POST /v1/audio/speech            # TTS proxy to gaming PC
GET  /v1/models                  # List available models (aggregated from providers)
```

#### Anthropic-Compatible Endpoints
```
POST /v1/messages                # Anthropic Messages API → translated to OpenAI → routed
POST /v1/messages/count_tokens   # Token counting (pre-flight)
```

#### Routing & Health
```
GET  /health                     # Router health
GET  /v1/routing/config          # Provider/model registry
GET  /v1/providers/status        # Live provider health + concurrency
POST /v1/providers/{id}/check    # Force health check
```

#### API Key Management
```
GET    /v1/keys                  # List keys (prefix only, never full key)
POST   /v1/keys                  # Create key → returns full key once
DELETE /v1/keys/{id}             # Revoke key
PATCH  /v1/keys/{id}             # Update key metadata/scopes
```

#### Metrics
```
GET  /metrics/recent             # Recent request metrics
GET  /metrics/daily              # Aggregated daily stats
GET  /metrics/models             # Model usage distribution
GET  /metrics/dashboard          # Summary stats for dashboard
```

#### Gaming PC Proxy
```
GET  /gaming-pc/status           # Gaming PC status (model, gaming mode, GPU)
POST /gaming-mode                # Toggle gaming mode (enable/disable)
POST /stop-all                   # Stop all models on gaming PC
```

### 3.5 Routing Logic

**Auto-routing (model="auto")**:
```
1. Check gaming PC status (cached, 30s TTL)
   ├─ If gaming mode ON → skip gaming PC
   └─ If gaming PC unreachable → skip gaming PC
2. Route to gaming-pc-3090 default model (priority 1)
3. On failure (connect error, 500+, timeout):
   ├─ Mark provider as degraded (circuit breaker, 2 failures = unhealthy)
   └─ Fall back to z.ai GLM-5.1 (priority 2)
4. On streaming: single provider (no mid-stream fallback)
5. On non-streaming: execution-level fallback chain tried sequentially
```

**Explicit routing (X-Provider header)**:
```
X-Provider: gaming-pc-3090       # Route to specific provider
X-Provider: zai                   # Route to z.ai explicitly
X-Model: carnice-bf16mtp          # Override model within provider
```

**Future: Complexity Router (stub)**
```
routing/complexity.py — empty module with interface:
  classify_complexity(messages) → "simple" | "medium" | "complex"
  route_by_complexity(classification) → provider_id, model_id

Plug-in point: before provider selection in /v1/chat/completions.
Configured via providers.yaml complexity_routing section.
```

### 3.6 API Key Design

**Format**: `lai-{random32hex}` (default for all keys)

Claude Code and Anthropic SDK clients that require `sk-ant-` format can be accommodated by setting a custom prefix at key creation time via `metadata.prefix` — but this is **intentional and explicit**, not the default.

**Key types**:
- `service/agent-name` — for automated agents (e.g., `service/oak`, `service/avery`)
- `user/name` — for individual users (e.g., `user/shua`)

**Metadata per key**:
```json
{
  "name": "service/oak",
  "prefix": "lai",
  "scopes": ["chat", "tts", "images"],
  "metadata": {"priority": 0, "type": "agent"},
  "expires_at": null
}
```

**Creating an Anthropic-compatible key** (for Claude Code):
```bash
POST /v1/keys
{
  "name": "service/claude-code",
  "prefix": "sk-ant-api03",
  "scopes": ["chat"]
}
```
This returns `sk-ant-api03-{random32hex}` — works with any Anthropic SDK client.

**Storage**: SHA-256 hash in SQLite. Full key returned once at creation.

**Priority from key metadata**:
- Priority 0 (high): agent keys, critical services
- Priority 1 (normal): default
- Priority 2 (low): batch/background

### 3.7 Trace Emission

Every request emits a trace event to `dashboard-api:8010/traces/events` via fire-and-forget POST:

```json
{
  "type": "InferenceComplete",
  "session_id": "...",
  "model_requested": "auto",
  "model_used": "carnice-bf16mtp",
  "provider": "gaming-pc-3090",
  "prompt_tokens": 1234,
  "completion_tokens": 567,
  "duration_ms": 3200,
  "success": true,
  "api_key_name": "service/oak",
  "streaming": true
}
```

This is **fire-and-forget** — if dashboard-api is down, the trace is dropped. Metrics are also written to the router's local SQLite for the `/metrics/*` endpoints.

### 3.8 Database Schema (SQLite, auto-created on startup)

```sql
-- Only 3 tables, not 10+
metrics (
  id, timestamp, date, model_requested, model_used, provider,
  prompt_tokens, completion_tokens, total_tokens, duration_ms,
  success, error, streaming, api_key_name, cost_usd
)

client_api_keys (
  id, key_hash UNIQUE, key_prefix, name, created_at,
  last_used_at, expires_at, enabled, scopes, metadata
)

daily_stats (
  date PRIMARY KEY, total_requests, total_tokens,
  unique_api_keys, models_used, avg_duration_ms, success_rate
)
```

That's it. No conversations table, no messages table, no agent_runs, no harness_sessions. Those belong in dashboard-api.

### 3.9 Anthropic Bridge

**Keep the existing `bridge/` module verbatim** — it's well-isolated, dependency-free, and handles all the edge cases (tool calls, vision images, streaming, empty responses). This is the best code in the current stack.

The translation layer converts:
- Anthropic Messages request → OpenAI chat completions request
- OpenAI chat completions response → Anthropic Messages response  
- OpenAI SSE stream → Anthropic SSE stream (with proper event sequencing)

Tool use translation:
- Anthropic `tool_use` blocks → OpenAI `tool_calls`
- Anthropic `tool_result` blocks → OpenAI `role: tool` messages
- `tool_choice: "any"` → `"required"`, `{"type":"tool","name":"X"}` → `{"type":"function","function":{"name":"X"}}`

### 3.10 Configuration (providers.yaml)

Minimal inheritance from current config. Strip models down to what's actually deployed:

```yaml
providers:
  - id: gaming-pc-3090
    name: "Gaming PC (2x RTX 3090)"
    type: local
    endpoint: "${GAMING_PC_URL}"
    priority: 1
    max_concurrent: 3
    health_check_path: /status
    health_check_validate_running: true
    health_check_interval: 30

  - id: server-3070
    name: "Server (RTX 3070)"
    type: local
    endpoint: "${LOCAL_3070_URL}"
    priority: 99  # explicit only
    max_concurrent: 1
    health_check_path: /health

  - id: zai
    name: "Z.ai (GLM-5.1)"
    type: cloud
    endpoint: "https://api.z.ai/api/coding/paas/v4"
    priority: 2
    max_concurrent: 100
    auth_type: bearer
    auth_secret: "ZAI_API_KEY"

models:
  - id: carnice-bf16mtp
    provider_id: gaming-pc-3090
    context_window: 262144
    max_tokens: 32768
    is_default: true
    capabilities: {streaming: true, function_calling: true, vision: false}

  - id: glm-5.1
    provider_id: zai
    context_window: 205000
    max_tokens: 8192
    is_default: true
    cost_per_1k_tokens: 0.001

settings:
  enable_cloud_fallback: true
  electricity_rate_kwh: 0.166
```

Model garden data (full model cards, cache status, prefetch) lives in llm-manager's `/status` and `/v1/models/cards` — the router doesn't need to know about VRAM, quantization, or model files.

---

## 4. Repo 2: `llm-manager`

### 4.1 Purpose

Manages GPU inference containers on a single host. Deploys as two instances:
- **Gaming PC**: `MODE=always-on`, 2x RTX 3090 (48GB), gaming mode enabled
- **Server**: `MODE=always-on`, RTX 3070 (8GB), lightweight models only

### 4.2 Target Structure

```
llm-manager/
├── Dockerfile
├── requirements.txt
├── manager.py                  # Main app (~800 lines) [cleaned up from current]
├── models.json                 # Model cards (VRAM, HF refs, runtime config)
├── patches/                    # vLLM patches for custom models
├── images/
│   ├── vllm-custom/
│   │   └── Dockerfile          # Custom vLLM with BNB NF4 patches
│   └── llamacpp/
│       └── Dockerfile          # llama.cpp server CUDA image
├── inference/                  # Inference services that share the GPU host
│   ├── image-server/
│   │   ├── Dockerfile
│   │   ├── app/
│   │   └── requirements.txt    # FLUX image generation
│   └── tts-server/
│       ├── Dockerfile
│       ├── app/
│       └── requirements.txt    # Chatterbox TTS
└── docker-compose.gaming.yml   # Full gaming PC compose (manager + image + tts)
```

### 4.3 What Changes from Current

1. **vllm-custom Dockerfile moves here** — no more separate `vllm/` directory
2. **image-server and tts-server move here** — same deployment target, same CI
3. **Gaming mode gets API-driven toggle** — `POST /gaming-mode` with `?enable=true/false` for agent automation
4. **Auto-detect gaming via process monitoring** — optional: watch for game processes and auto-switch
5. **Models.json stays** — it's already well-structured

### 4.4 API Surface (unchanged from current)

```
GET  /health
GET  /status                     # Full status (running models, gaming mode, GPU info)
GET  /v1/models                  # OpenAI-compatible model list
GET  /v1/models/cards            # Full model cards with cache info
POST /start/{model_id}
POST /stop/{model_id}
POST /swap/{model_id}            # Stop all, start this one
POST /gaming-mode                # Toggle gaming mode
POST /stop-all
POST /v1/models/{id}/prefetch    # Download weights without starting
GET  /v1/models/{id}/prefetch    # Prefetch status
GET  /metrics/recent             # Local request metrics
ANY  /v1/{path}                  # Proxy to active vLLM/llamacpp container
```

### 4.5 Gaming PC: Docker Desktop vs WSL2

**Recommendation: Stay on Docker Desktop for now.**

Research findings:
- Docker Desktop on Windows uses WSL2 under the hood for GPU access
- Performance delta between Docker Desktop and native WSL2 Docker is <5% for inference workloads
- Docker Desktop gives you Docker Compose, auto-restart, and easier management
- Native WSL2 requires manual systemd service management
- vLLM officially supports Docker + WSL2 path now

**Optimization opportunity**: Use Docker's `ipc_mode: host` for multi-GPU (already doing this), and `SHM_SIZE=8g` on the compose file for large KV caches.

### 4.6 Server 3070 Instance

Same `llm-manager` image, different config:
```yaml
llm-manager-server:
  image: llm-manager:latest
  environment:
    MODE: always-on
    DEFAULT_MODEL: bge-base-en    # embeddings + tiny model
    GPU_MEMORY_UTILIZATION: 0.90
    CPU_OFFLOAD_GB: 1
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

This gives the router an embedding endpoint and a lightweight chat model for simple queries.

### 4.7 Video Generation: Future Path

Not implemented now, but the architecture supports it:
- Add `inference/video-server/` to `llm-manager` repo
- Same pattern as image-server (thin FastAPI wrapper around a model)
- Deploy on gaming PC alongside image-server (shares GPU, but only one GPU-intensive task at a time)
- Router proxies `POST /v1/video/generate` to `video-server`

---

## 5. Repo 3: `homelab-dashboard`

### 5.1 Purpose

Central visualization and control plane for the entire AI infrastructure. React frontend + FastAPI backend.

### 5.2 Target Structure

```
homelab-dashboard/
├── frontend/                   # React + TypeScript + Vite
│   ├── src/
│   │   ├── App.tsx
│   │   ├── routes/
│   │   │   ├── Chat.tsx        # Streaming chat with provider selection
│   │   │   ├── Tasks.tsx       # Kanban board (Tasks API)
│   │   │   ├── Providers.tsx   # Provider health + model garden
│   │   │   ├── Stats.tsx       # Activity heatmap, model usage
│   │   │   ├── Sessions.tsx    # Claude Code session traces
│   │   │   ├── Agents.tsx      # Agent fleet status
│   │   │   ├── Knowledge.tsx   # Knowledge wiki
│   │   │   └── Docs.tsx        # Reference docs
│   │   ├── components/ui/      # Simple dark theme components (NOT retro)
│   │   └── styles/
│   ├── Dockerfile
│   └── package.json
│
├── backend/                    # FastAPI
│   ├── gateway.py              # Main app (~300 lines, trimmed from current 700+)
│   ├── traces.py               # SQLite schema + queries (~200 lines)
│   ├── health.py               # Agent health monitor (~150 lines)
│   ├── knowledge_base.py       # KB API (~400 lines, keep as-is)
│   ├── models.py               # Pydantic models (~150 lines)
│   ├── config.yaml             # Agent registry
│   ├── Dockerfile
│   └── requirements.txt
│
├── docker-compose.yml          # Deploys frontend + backend together
└── CLAUDE.md                   # Design system doc
```

**Frontend design**: Simple dark theme. No retro/pixel art. Standard components (cards, tables, badges). Berkeley Mono for data, system sans-serif for UI. Functional-first — every route works, polish later.

### 5.3 What Changes

1. **Frontend and backend in same repo** — they share the same deployment, same CI, same version
2. **Strip agent proxying** that duplicates agent-harness functionality (job creation, context R/W, schedule management) — keep only fleet health monitoring
3. **Trace ingestion stays** — this is the central observability store
4. **Knowledge base stays** — useful feature
5. **AoE Canvas is dropped** — if a command interface is wanted later, it's a frontend route, not a separate app

### 5.4 Backend API

```
# Trace ingestion (from ai-gateway and Claude Code hooks)
POST /traces/events
GET  /traces                     # List sessions
GET  /traces/{session_id}        # Session detail + spans
GET  /traces/stats               # Fleet-wide stats
GET  /traces/{session_id}/transcript  # JSONL → conversation

# Agent fleet health (from config.yaml)
GET  /api/agents                 # List all agents with status
GET  /api/agents/{id}            # Agent detail
POST /api/agents/{id}/check      # Force health check
GET  /api/agents/stats           # Fleet stats

# Knowledge base
GET  /api/kb/search
POST /api/kb/articles
GET  /api/kb/articles/{slug}

# Health
GET  /health
```

### 5.5 TUI (`ai-gateway tui`)

The monitoring TUI ships in Phase 1 with the router. Textual-based terminal UI for real-time inspection:

```bash
ai-gateway tui              # Launch monitoring TUI
ai-gateway tui --follow     # Live tail of requests
ai-gateway tui --provider gaming-pc-3090  # Filter by provider
```

Shows: live request stream, provider health, active models, queue depth, recent errors. Vital for triaging issues without opening the browser.

---

## 6. Repo 4: `model-toolkit`

### 6.1 Purpose

A workspace for all model post-processing: quantization, abliteration, fine-tuning, and evaluation. These are **batch jobs**, not always-on services. They run on the gaming PC when no model is loaded (or when explicitly invoked).

### 6.2 Structure

```
model-toolkit/
├── README.md
├── Dockerfile                   # Base image: torch + transformers + peft
├── docker-compose.yml           # Standalone compose for on-demand jobs
│
├── pipelines/
│   ├── quantize/
│   │   ├── autoawq.py           # AWQ quantization (from current autoawq/)
│   │   └── README.md
│   │
│   ├── ablate/
│   │   ├── abliterate.py        # Diff-in-means refusal removal
│   │   └── README.md
│   │
│   ├── finetune/
│   │   ├── lora_train.py        # LoRA/QLoRA fine-tuning script
│   │   ├── configs/             # YAML training configs per model
│   │   └── README.md
│   │
│   └── evaluate/
│       ├── eval_runner.py       # Model comparison framework
│       ├── suites/              # Eval suites (coding, reasoning, etc.)
│       └── README.md
│
├── scripts/
│   ├── run-pipeline.sh          # docker run --gpus all model-toolkit quantize ...
│   └── push-to-harbor.sh
│
└── models/
    └── output/                  # Mount point for processed models
```

### 6.3 Pipeline Commands

```bash
# Quantize a model
docker run --gpus all model-toolkit quantize \
  --model Qwen/Qwen3.5-27B \
  --method awq \
  --output /models/output/qwen3.5-27b-awq

# Abliterate (remove refusals)
docker run --gpus all model-toolkit ablate \
  --model /models/output/qwen3.5-27b-awq \
  --output /models/output/qwen3.5-27b-abliterated

# Fine-tune with LoRA
docker run --gpus all model-toolkit finetune \
  --base-model Qwen/Qwen3.5-27B \
  --dataset ./data/training.jsonl \
  --config configs/qwen-lora.yaml \
  --output /models/output/qwen3.5-27b-personal

# Run evaluation suite
docker run --gpus all model-toolkit evaluate \
  --model /models/output/qwen3.5-27b-awq \
  --suite humaneval \
  --compare carnice-bf16mtp
```

### 6.4 Fine-Tuning on 2x RTX 3090 (48GB)

**What's feasible**:
| Method | Model Size | VRAM Needed | Notes |
|--------|-----------|-------------|-------|
| QLoRA (4-bit) | 27B | ~20GB | 2x 3090 can do this comfortably with TP=2 |
| LoRA (16-bit) | 14B | ~32GB | Tight but doable on 48GB |
| Full fine-tune | 7B | ~28GB | Possible on single 3090 |
| QLoRA (4-bit) | 70B | ~40GB | Tight on 48GB, possible with gradient checkpointing |

**Recommended stack**: Unsloth for 2-5x faster LoRA/QLoRA training, or Axolotl for YAML-driven training configs. Both support multi-GPU.

**Dataset format**: JSONL with `{"instruction": "...", "output": "..."}` pairs. Curated from your own code, writing, agent traces.

### 6.5 CI/CD

The toolkit builds a single Docker image on tag push. No automatic deploy — these are manually invoked batch jobs. The `push-to-harbor.sh` script pushes processed models to Harbor as OCI artifacts for llm-manager to pull.

---

## 7. Deployment & CI/CD

### 7.1 CI Pipeline (per repo)

Each repo has a `.gitea/workflows/build.yml` that:
1. Builds Docker image(s) on tag push (`v*`)
2. Pushes to Harbor (`harbor.server.unarmedpuppy.com/library/<name>:latest`)
3. SSHs to target host to pull and restart

**Images built**:

| Repo | Images Built | Deployed To |
|------|-------------|-------------|
| `ai-gateway` | `ai-gateway` | Server |
| `llm-manager` | `llm-manager`, `image-server`, `tts-server`, `vllm-custom` | Gaming PC + Server |
| `homelab-dashboard` | `dashboard`, `dashboard-api` | Server |
| `model-toolkit` | `model-toolkit` | Gaming PC (on-demand) |

**Total: 8 images** (down from 15), but only 6 run as services.

### 7.2 Docker Compose

**Server** (`docker-compose.server.yml`):
```yaml
services:
  ai-gateway:
    image: ai-gateway:latest
    ports: ["8000:8000"]
    environment:
      - GAMING_PC_URL=${GAMING_PC_URL}
      - LOCAL_3070_URL=http://llm-manager-server:8000
      - ZAI_API_KEY=${ZAI_API_KEY}
      - DASHBOARD_API_URL=http://dashboard-api:8010
      - REQUIRE_API_KEY=1
    volumes:
      - router-data:/app/data
    networks: [my-network]

  dashboard:
    image: dashboard:latest
    ports: ["8011:80"]
    networks: [my-network]

  dashboard-api:
    image: dashboard-api:latest
    ports: ["8010:8010"]
    volumes:
      - dashboard-api-data:/app/data
    networks: [my-network]

  llm-manager-server:
    image: llm-manager:latest
    ports: ["8012:8000"]
    environment:
      - MODE=always-on
      - DEFAULT_MODEL=bge-base-en
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - huggingface-cache:/root/.cache/huggingface
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks: [my-network]
```

**Gaming PC** (`docker-compose.gaming.yml`):
```yaml
services:
  llm-manager:
    image: llm-manager:latest
    ports: ["8000:8000"]
    environment:
      - MODE=always-on
      - DEFAULT_MODEL=carnice-bf16mtp
      - GAMING_MODE_ENABLED=true
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - huggingface-cache:/root/.cache/huggingface
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  image-server:
    image: image-server:latest
    ports: ["8005:8000"]
    environment:
      - MODEL_ID=black-forest-labs/FLUX.2-dev
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  tts-server:
    image: tts-server:latest
    ports: ["8006:8000"]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

---

## 8. Data Flow

### 8.1 Inference Request Flow

```
Client (Claude Code, agent, dashboard chat)
  │
  │ POST /v1/chat/completions (or /v1/messages)
  │ Headers: Authorization: Bearer sk-ant-api03-xxx
  │
  ▼
ai-gateway (:8000)
  │
  ├─ 1. Validate API key → ApiKey{name="service/oak", priority=0}
  ├─ 2. If /v1/messages: bridge/translate.py → OpenAI format
  ├─ 3. Route: auto → gaming-pc-3090 (priority 1)
  ├─    If gaming mode ON or PC down → zai GLM-5.1 (priority 2)
  ├─ 4. Forward to llm-manager:gaming-pc:8000/v1/chat/completions
  │
  │  (on failure: circuit breaker marks gaming-pc unhealthy, retry with zai)
  │
  ├─ 5. Stream response back (or translate to Anthropic SSE if /v1/messages)
  ├─ 6. Background: emit trace to dashboard-api:8010/traces/events
  └─ 7. Background: log metrics to local SQLite
```

### 8.2 Dashboard Data Flow

```
ai-gateway ──POST traces──▶ dashboard-api ──▶ SQLite (traces.db)
                                                  ├─ sessions table
                                                  ├─ spans table
                                                  └─ stats views
                                                        │
dashboard (React) ◀──GET /traces─── dashboard-api ◀─────┘
```

### 8.3 Model Swap Flow

```
User/Agent ──POST /swap/carnice-bf16mtp──▶ ai-gateway
                                                  │
                                            POST /gaming-pc:8000/swap/carnice-bf16mtp
                                                  │
                                            llm-manager (gaming PC)
                                              ├─ Stop current vLLM container
                                              ├─ Start new vLLM container for carnice
                                              ├─ Wait for /v1/models healthy
                                              └─ Return {status: "running"}
```

---

## 9. Migration Plan

### Phase 1: Create `ai-gateway` repo (Week 1)

1. Create new Gitea repo `homelab/ai-gateway`
2. Copy `llm-router/bridge/` (translate.py + stream.py) — **unchanged**
3. Create `routing/provider_manager.py` — extract from current `providers/manager.py`, strip model garden CRUD
4. Create `auth/api_keys.py` — extract from current `auth.py`, keep `sk-ant-api03` format
5. Create `router.py` — rewrite from scratch with only the endpoints in §3.4
6. Create `db.py` — 3 tables only (metrics, api_keys, daily_stats)
7. Create `traces/emitter.py` — simple fire-and-forget POST
8. Copy `config/providers.yaml` — trim to §3.10 spec
9. Write Dockerfile, requirements.txt
10. Test locally against current llm-manager instances

**Validation**: `curl -X POST localhost:8000/v1/chat/completions -H "Authorization: Bearer test" -d '{"model":"auto","messages":[{"role":"user","content":"hello"}]}'`

### Phase 2: Create `llm-manager` repo (Week 1)

1. Create new Gitea repo `homelab/llm-manager`
2. Copy current `llm-manager/manager.py` — **mostly unchanged**, clean up dead code
3. Move `vllm/Dockerfile` → `images/vllm-custom/Dockerfile`
4. Move `image-server/` → `inference/image-server/`
5. Move `tts-server/` → `inference/tts-server/`
6. Create `docker-compose.gaming.yml` and `docker-compose.server.yml`
7. Write CI workflow (builds 4 images)
8. Test on gaming PC

**Validation**: `docker compose -f docker-compose.gaming.yml up -d` → verify model loads, gaming mode works, image/TTS accessible.

### Phase 3: Create `homelab-dashboard` repo (Week 2)

1. Create new Gitea repo `homelab/homelab-dashboard`
2. Move current `dashboard/` → `frontend/`
3. Move current `dashboard-api/` → `backend/`
4. Strip agent proxying from backend (keep fleet health + traces)
5. Create combined `docker-compose.yml`
6. Wire trace ingestion from ai-gateway
7. Test all routes

**Validation**: Open `https://ai-hub.server.unarmedpuppy.com` → verify all routes work, traces flowing.

### Phase 4: Create `model-toolkit` repo (Week 2)

1. Create new Gitea repo `homelab/model-toolkit`
2. Create pipeline scripts from current `abliteration/` and `autoawq/`
3. Add `finetune/` pipeline (new — based on Unsloth)
4. Add `evaluate/` pipeline (new — simplified from eval-runner)
5. Dockerfile + CI workflow
6. Test a quantization run

**Validation**: `docker run --gpus all model-toolkit quantize --model Qwen/Qwen3-32B --method awq`

### Phase 5: Cutover (Week 3)

1. Archive current `homelab-ai` repo (tag `v1-final`, don't delete)
2. Deploy new repos to server and gaming PC
3. Migrate API keys from old SQLite to new
4. Migrate trace data if needed (or start fresh)
5. Update all agent configs to point to new router + new domains
6. Update Traefik labels to new domains:
   - `router.server.unarmedpuppy.com` → ai-gateway
   - `ai-hub.server.unarmedpuppy.com` → dashboard
   - `ai-hub-api.server.unarmedpuppy.com` → dashboard-api
7. Monitor for 48 hours

### Phase 6: Cleanup (Week 3)

1. Delete stale ADRs, archive relevant ones
2. Update all AGENTS.md files across repos
3. Remove old Harbor images
4. Delete Windows PS1/BAT scripts from history

---

## 10. Line Count Comparison

| Component | Current Lines | Target Lines | Reduction |
|-----------|--------------|--------------|-----------|
| ai-gateway | 7,130 (router) + 2,500 (tests) | ~1,800 | 75% |
| llm-manager | 1,160 | ~900 (cleanup) | 22% |
| dashboard-api | 1,100 | ~700 | 36% |
| dashboard (React) | ~5,400 | ~3,000 | 44% (functional redesign) |
| model-toolkit | ~300 (scattered) | ~800 (new pipelines) | net new |
| **Total Python** | ~18,000 | ~4,200 | **77%** |
| Docker images built | 15 | 8 | 47% |
| Running containers | 8 server + 6 gaming | 4 server + 3 gaming | 39% |

---

## 11. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Bridge translation regression | Medium | High | Copy bridge/ verbatim, test with Claude Code |
| Gaming PC Docker issues | Low | Medium | Stay on Docker Desktop, test before cutover |
| Data loss (traces, metrics) | Low | Low | Export SQLite before cutover, start fresh acceptable |
| Agent config breakage | Medium | Medium | New domains require config update; API surface stays compatible |
| CI pipeline breakage | Low | Medium | Each repo has its own workflow, test independently |

---

## 12. Resolved Decisions

| # | Question | Decision |
|---|----------|----------|
| 1 | Port numbering | **New clean scheme**: router=8000, dashboard-api=8010, dashboard=8011, llm-manager-server=8012. Gaming PC stays on 8000/8005/8006. |
| 2 | Domain names | **All new routes** for clean cutover: `router.server.unarmedpuppy.com`, `ai-hub.server.unarmedpuppy.com`, `ai-hub-api.server.unarmedpuppy.com` |
| 3 | Dashboard redesign | **Full redesign** — functional-first with simple dark theme. Design iteration deferred. Drop retro/pixel theme entirely. |
| 4 | TUI priority | **Included in Phase 1.** Vital tool for real-time triage and deep inspection. |
| 5 | Fine-tuning dataset | **Exploration-first.** Toolkit ships with pipeline scaffolding and example configs; no real datasets yet. |
| 6 | Z.ai model | **Default to `glm-5.1`** (latest). Config field for easy updates as Z.ai releases new models. |

---

## 13. Appendix A: Feature Inventory

### Features Currently Supported → Where They Go

| Feature | Current Location | New Location | Status |
|---------|-----------------|--------------|--------|
| OpenAI chat completions routing | llm-router | ai-gateway | ✅ Core |
| Anthropic Messages API | llm-router/bridge | ai-gateway/bridge | ✅ Keep verbatim |
| Auto-routing (local → cloud fallback) | llm-router/providers | ai-gateway/routing | ✅ Simplified |
| Circuit breaker | llm-router/providers | ai-gateway/routing | ✅ Keep |
| Streaming (enhanced + passthrough) | llm-router/stream | ai-gateway/stream | ✅ Keep |
| API key auth (sk-ant-...) | llm-router/auth | ai-gateway/auth | ✅ Keep |
| Request metrics logging | llm-router/metrics + database | ai-gateway/db | ✅ Keep |
| Daily stats aggregation | llm-router/metrics | ai-gateway/db | ✅ Keep |
| Cost tracking | llm-router/providers | ai-gateway/routing | ✅ Keep |
| Gaming mode toggle | llm-router → proxy | ai-gateway → proxy | ✅ Keep |
| TTS proxy | llm-router | ai-gateway | ✅ Keep |
| Image upload | llm-router | **Drop** | ❌ Unused |
| Memory system | llm-router/memory | **Drop** | ❌ Unused |
| RAG pipeline | llm-router/rag | **Drop** | ❌ Unused |
| Agent tools | llm-router/tools | **Drop** | ❌ Wrong place |
| Agent loop | llm-router/agent | **Drop** | ❌ agent-harness |
| Model garden CRUD | llm-router/router | llm-manager | ✅ Moved |
| Service feeds | llm-router/service_feeds | **Drop** | ❌ Wrong place |
| vLLM container management | llm-manager | llm-manager | ✅ Keep |
| llama.cpp container management | llm-manager | llm-manager | ✅ Keep |
| Gaming mode (local) | llm-manager | llm-manager | ✅ Keep |
| Model prefetch | llm-manager | llm-manager | ✅ Keep |
| Cache detection | llm-manager | llm-manager | ✅ Keep |
| FLUX image generation | image-server | llm-manager/inference | ✅ Moved |
| Chatterbox TTS | tts-server | llm-manager/inference | ✅ Moved |
| Trace ingestion | dashboard-api | homelab-dashboard/backend | ✅ Keep |
| Fleet health monitoring | dashboard-api + health.py | homelab-dashboard/backend | ✅ Keep |
| Knowledge base | dashboard-api | homelab-dashboard/backend | ✅ Keep |
| Job proxy (agents) | dashboard-api | **Drop** | ❌ agent-harness |
| Claude session transcripts | dashboard-api | homelab-dashboard/backend | ✅ Keep |
| Dashboard chat | dashboard (React) | homelab-dashboard/frontend | ✅ Keep |
| Kanban tasks view | dashboard (React) | homelab-dashboard/frontend | ✅ Keep |
| Provider health view | dashboard (React) | homelab-dashboard/frontend | ✅ Keep |
| Activity stats | dashboard (React) | homelab-dashboard/frontend | ✅ Keep |
| Session traces view | dashboard (React) | homelab-dashboard/frontend | ✅ Keep |
| Knowledge wiki | dashboard (React) | homelab-dashboard/frontend | ✅ Keep |
| AWQ quantization | autoawq | model-toolkit/pipelines | ✅ Moved |
| Abliteration | abliteration | model-toolkit/pipelines | ✅ Moved |
| TUI monitoring | llm-tui | ai-gateway (subcommand) | ✅ Moved |

---

## 14. Appendix B: Dependency Map

```
ai-gateway
  ├── fastapi, uvicorn, httpx
  ├── pydantic
  ├── pyyaml (providers.yaml)
  ├── tiktoken (bridge)
  └── sqlite3 (stdlib)

llm-manager
  ├── fastapi, uvicorn, httpx
  ├── docker (Python SDK)
  └── huggingface_hub (prefetch)

homelab-dashboard/backend
  ├── fastapi, uvicorn, httpx
  ├── pyyaml (config.yaml)
  └── sqlite3 (stdlib)

homelab-dashboard/frontend
  ├── react 19, typescript, vite
  ├── tailwind 4
  ├── recharts
  └── phaser 3 (only if Command page revived)

model-toolkit
  ├── torch, transformers, peft
  ├── autoawq (quantize)
  ├── unsloth or axolotl (finetune)
  └── transformers, torch (ablate)
```

No shared Python packages between repos. No internal dependencies. Each repo is independently buildable and deployable.

---

*End of plan. Implementation tasks to be generated from this document.*
