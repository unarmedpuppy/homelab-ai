# Local AI Unified Architecture Plan

**Status**: Planning
**Created**: 2025-12-28
**Supersedes**: `local-ai-two-gpu-architecture.md` (consolidated here)

## Vision

A unified local AI infrastructure with intelligent routing, multiple backends, and seamless integration with existing services (Mattermost, agent tools).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          All LLM Requests                                    │
│                    (Mattermost, Web UI, API, Agents)                        │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LOCAL-AI-ROUTER                                      │
│                    (Home Server - Always On)                                 │
│                                                                              │
│  Uses 3070 for quick routing decision, then dispatches to:                  │
│                                                                              │
│  Routing Logic:                                                              │
│  1. Explicit model request? → Route to requested backend                    │
│  2. Token estimate < 2K? → 3070 (fast)                                      │
│  3. Gaming mode ON? → 3070 only (unless force-big)                          │
│  4. Token estimate 2K-16K + 3090 available? → 3090                          │
│  5. Complex/long context? → OpenCode (GLM-4.7 or Claude)                    │
│  6. Fallback → 3070                                                          │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
       ┌───────────────────────────┼───────────────────────────────┐
       │                           │                               │
       ▼                           ▼                               ▼
┌─────────────────┐     ┌─────────────────┐             ┌─────────────────┐
│   HOME SERVER   │     │   GAMING PC     │             │   OPENCODE      │
│   RTX 3070      │     │   RTX 3090      │             │   CONTAINER     │
│                 │     │                 │             │                 │
│ • Always on     │     │ • Gaming mode   │             │ • GLM-4.7       │
│ • Small models  │     │ • Medium models │             │ • Claude (sub)  │
│ • Fast routing  │     │ • Coding/refact │             │ • External API  │
│ • 7B-8B class   │     │ • 14B class     │             │ • Fallback      │
│                 │     │                 │             │                 │
│ Qwen3-Coder-7B  │     │ Qwen3-Coder-14B │             │ oh-my-opencode  │
│ or Llama 3.1 8B │     │                 │             │                 │
└─────────────────┘     └─────────────────┘             └─────────────────┘
        │                        │                              │
        └────────────────────────┴──────────────────────────────┘
                                 │
                                 ▼
                    OpenAI-Compatible Response
```

## Current State (What Exists)

### Gaming PC (`local-ai/`)
- **Status**: Working
- **GPU**: RTX 3090 (24GB)
- **Models**: Llama3-8B, Qwen2.5-14B-AWQ, DeepSeek-Coder, Qwen-Image-Edit
- **Features**:
  - Gaming mode (on/off) with web dashboard, GUI, CLI
  - Auto-shutdown after 10 min idle
  - Manager service handles model lifecycle
- **API**: `http://192.168.86.63:8000`
- **Gaming Mode API**:
  - `GET /status` - Current state
  - `POST /gaming-mode` - Toggle gaming mode
  - `POST /stop-all` - Stop all models

### Chat Interface (`apps/local-ai-app/`)
- **Status**: Working
- **Purpose**: Web chat UI + proxy to Windows
- **URL**: `https://local-ai.server.unarmedpuppy.com`
- **Limitation**: Simple proxy, no routing logic

### Server Hardware
- **GPU**: RTX 3070 (8GB) - Installed, not configured
- **Status**: Needs NVIDIA drivers, CUDA, Docker GPU support

## Target Components

### 1. Server Local AI Service (`apps/local-ai-server/`)

Local inference service running on home server with RTX 3070.

**Purpose**: Always-on small model inference + routing decisions

**Stack**:
- vLLM or llama.cpp
- Docker with GPU support
- FastAPI wrapper

**Models**:
| Model | Size | VRAM | Use Case |
|-------|------|------|----------|
| Qwen3-Coder-7B | 7B | ~6GB | Fast routing, tool calls |
| OR Llama 3.1 8B | 8B | ~8GB | General purpose |

**API**: OpenAI-compatible at `http://localhost:8001` (internal)

### 2. Local AI Router (`apps/local-ai-router/`)

The intelligent routing layer - **main entry point for all LLM requests**.

**Purpose**: Route requests to optimal backend based on:
- Explicit model request (override)
- Token estimate
- Task complexity
- Gaming mode status
- Backend health

**API**: OpenAI-compatible at `https://local-ai.server.unarmedpuppy.com`

**Routing Logic**:
```python
def route_request(request):
    # 1. Explicit model override
    if request.model in ["3090", "big", "gaming-pc"]:
        if gaming_mode and not force_big:
            return fallback_to_3070(request)
        return route_to_3090(request)

    if request.model in ["opencode", "glm", "claude"]:
        return route_to_opencode(request)

    if request.model in ["3070", "small", "fast"]:
        return route_to_3070(request)

    # 2. Check gaming mode
    if gaming_mode and not has_force_big_signal(request):
        return route_to_3070(request)

    # 3. Token-based routing
    estimated_tokens = estimate_tokens(request)

    if estimated_tokens < 2000:
        return route_to_3070(request)  # Fast path

    if estimated_tokens < 16000 and is_3090_healthy():
        return route_to_3090(request)  # Medium path

    # 4. Complex requests → OpenCode
    if estimated_tokens > 16000 or is_complex_task(request):
        return route_to_opencode(request)

    # 5. Fallback
    return route_to_3070(request)
```

**Force-Big Signals** (override gaming mode):
- Header: `X-Force-Big: true`
- Model: `model = "big"` or `model = "3090"`
- Prompt tag: `#force_big`

**Health Checks**:
- 3070: Always assumed healthy (local)
- 3090: Query `GET /status` on Windows
- OpenCode: HTTP health check

### 3. OpenCode Container (`apps/opencode-service/`)

Containerized [OpenCode](https://github.com/sst/opencode) with [oh-my-opencode](https://github.com/code-yeongyu/oh-my-opencode) for subscription-based API access.

**Purpose**: Access Claude and GLM-4.7 via existing subscriptions (no API key fees)

**Features**:
- Runs in Docker container
- Uses oh-my-opencode for browser session auth
- Exposes OpenAI-compatible API
- Supports both GLM-4.7 and Claude

**Architecture**:
```
┌─────────────────────────────────────────────┐
│           OpenCode Service                   │
├─────────────────────────────────────────────┤
│  FastAPI Wrapper                            │
│    │                                        │
│    ├─→ OpenCode (GLM-4.7)                   │
│    │     └─→ oh-my-opencode (browser auth)  │
│    │                                        │
│    └─→ OpenCode (Claude)                    │
│          └─→ oh-my-opencode (browser auth)  │
└─────────────────────────────────────────────┘
```

**TODO**: Research exact setup for oh-my-opencode in container
- How to persist browser sessions?
- How to handle auth expiry?
- Rate limiting considerations?

### 4. Mattermost Gaming Mode Integration

Control gaming mode via Mattermost bot commands.

**Commands** (via Tayne or dedicated bot):
```
@tayne gaming mode on    → Enable gaming mode
@tayne gaming mode off   → Disable gaming mode
@tayne gaming status     → Check current mode
```

**Implementation**:
- Add to mattermost-gateway as special command handler
- Calls Windows gaming mode API directly
- Reports status back to Mattermost

## Implementation Phases

### Phase 0: Prerequisites
- [ ] Install NVIDIA drivers on Debian server
- [ ] Install CUDA toolkit
- [ ] Configure Docker with GPU support (`nvidia-container-toolkit`)
- [ ] Verify GPU access: `docker run --gpus all nvidia/cuda:12.0-base nvidia-smi`

### Phase 1: Server Local AI (`apps/local-ai-server/`)
- [ ] Create service structure
- [ ] Deploy vLLM with Qwen3-Coder-7B or Llama 3.1 8B
- [ ] Configure Docker Compose with GPU
- [ ] Test inference locally
- [ ] Create health endpoint

### Phase 2: Router Service (`apps/local-ai-router/`)
- [ ] Create FastAPI service
- [ ] Implement OpenAI-compatible API
- [ ] Add backend health checks
- [ ] Implement routing logic
- [ ] Add force-big signal detection
- [ ] Connect to 3070 backend
- [ ] Connect to 3090 backend (via Windows IP)
- [ ] Add logging and metrics

### Phase 3: OpenCode Container (`apps/opencode-service/`)
- [ ] Research oh-my-opencode container setup
- [ ] Create Dockerfile
- [ ] Implement session persistence
- [ ] Add FastAPI wrapper
- [ ] Test GLM-4.7 access
- [ ] Test Claude access
- [ ] Connect to router

### Phase 4: Integration
- [ ] Upgrade `apps/local-ai-app/` to use router
- [ ] Add Mattermost gaming mode commands
- [ ] Update documentation
- [ ] Create reference docs
- [ ] Create skills for agents

### Phase 5: Polish
- [ ] Add metrics/monitoring
- [ ] Add Grafana dashboards
- [ ] Add alerting for backend failures
- [ ] Performance tuning

## Service Breakdown

| Service | Location | Port | Purpose |
|---------|----------|------|---------|
| `local-ai-server` | `apps/local-ai-server/` | 8001 | 3070 inference (internal) |
| `local-ai-router` | `apps/local-ai-router/` | 8000 | Main entry point |
| `opencode-service` | `apps/opencode-service/` | 8002 | GLM/Claude access |
| `local-ai-app` | `apps/local-ai-app/` | 8067 | Web UI (uses router) |
| Gaming PC Manager | `local-ai/` | 8000* | 3090 inference |

*Note: Gaming PC uses external IP 192.168.86.63:8000

## Configuration

### Router Environment Variables

```bash
# Backend endpoints
LOCAL_3070_URL=http://local-ai-server:8001
GAMING_PC_URL=http://192.168.86.63:8000
OPENCODE_URL=http://opencode-service:8002

# Routing thresholds
SMALL_TOKEN_THRESHOLD=2000
MEDIUM_TOKEN_THRESHOLD=16000

# Gaming mode endpoint
GAMING_MODE_URL=http://192.168.86.63:8000/status

# Logging
LOG_LEVEL=INFO
```

### Model Mapping

```json
{
  "model_aliases": {
    "small": "3070",
    "fast": "3070",
    "medium": "3090",
    "big": "3090",
    "gaming-pc": "3090",
    "glm": "opencode-glm",
    "claude": "opencode-claude"
  },
  "default_model": "auto"
}
```

## Gaming Mode States

Simple on/off:

| Mode | 3070 | 3090 | OpenCode |
|------|------|------|----------|
| OFF (normal) | ✅ Available | ✅ Available | ✅ Available |
| ON (gaming) | ✅ Available | ⚠️ Force-big only | ✅ Available |

## API Examples

### Basic Chat (auto-routed)
```bash
curl -X POST https://local-ai.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Force to 3090
```bash
curl -X POST https://local-ai.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Force-Big: true" \
  -d '{
    "model": "3090",
    "messages": [{"role": "user", "content": "Complex coding task..."}]
  }'
```

### Use Claude (via OpenCode)
```bash
curl -X POST https://local-ai.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude",
    "messages": [{"role": "user", "content": "Review this code..."}]
  }'
```

### Gaming Mode Toggle (Mattermost)
```
@tayne gaming mode on
> Gaming mode enabled. 3090 will only respond to force-big requests.

@tayne gaming status
> Gaming mode: ON
> 3070: Available
> 3090: Gated (force-big only)
> OpenCode: Available
```

## Related Documents

- [Mattermost Gateway](mattermost-gateway-service.md) - For Tayne gaming mode commands
- [Gaming PC Local AI](../../local-ai/README.md) - Current 3090 setup
- [Local AI App](../../apps/local-ai-app/README.md) - Web chat interface

## Open Questions

1. **OpenCode session persistence** - How to keep browser sessions alive in container?
2. **Rate limiting** - Should we rate limit Claude/GLM calls?
3. **Metrics** - What to track? Token usage, latency, routing decisions?
4. **TTS** - Still planning Chatterbox Turbo on 3070? (from old plan)

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-28 | Unified plan created | Consolidate scattered docs |
| 2025-12-28 | OpenCode for sub-based access | Avoid API key fees |
| 2025-12-28 | Gaming mode = simple on/off | Keep it simple |
| 2025-12-28 | Router uses token estimate | Automatic complexity detection |
