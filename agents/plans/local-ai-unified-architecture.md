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
│  Routing Logic:                                                              │
│  1. Explicit model request? → Route to requested backend                    │
│  2. Token estimate < 2K? → 3070 (fast)                                      │
│  3. Gaming mode ON? → 3070 only (unless force-big)                          │
│  4. Token estimate 2K-16K + 3090 available? → 3090                          │
│  5. Complex/long context? → Z.ai or Claude Harness                          │
│  6. Fallback → 3070                                                          │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
       ┌──────────────┬────────────┼────────────┬──────────────┐
       │              │            │            │              │
       ▼              ▼            ▼            ▼              ▼
┌───────────┐  ┌───────────┐  ┌─────────┐  ┌─────────┐  ┌───────────┐
│  SERVER   │  │ GAMING PC │  │  Z.AI   │  │ CLAUDE  │  │ ANTHROPIC │
│  3070     │  │  3090     │  │ CLOUD   │  │ HARNESS │  │   API     │
│           │  │           │  │         │  │         │  │           │
│ ⏳ Pending │  │ ✅ Active  │  │ ✅ Active│  │ ✅ Active│  │ ❌ Disabled│
│           │  │           │  │         │  │         │  │           │
│ 7B-8B     │  │ 14B class │  │ GLM-4.7 │  │ Sonnet  │  │ Requires  │
│ models    │  │ models    │  │ GLM-4.5 │  │ (Max)   │  │ API key   │
└───────────┘  └───────────┘  └─────────┘  └─────────┘  └───────────┘
                                              │
                                              ▼
                               ┌─────────────────────────┐
                               │   Claude Code CLI       │
                               │   (systemd on host)     │
                               │   ~/.claude.json OAuth  │
                               └─────────────────────────┘
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

**Agent Endpoint** (`POST /agent/run`):

Host-controlled agent loop following OpenCode's design philosophy:
- **Host owns**: loop control, step count, tool execution, error handling, termination
- **Single-action constraint**: Model emits exactly ONE action per turn (tool call OR response)
- **Host-enforced retries**: Validates output and re-prompts with structured feedback
- **Provider-agnostic**: Can swap between Claude, GPT-4, local models without system rewrite

Available tools:
- `read_file` - Read file contents (with optional line range)
- `write_file` - Create or overwrite files
- `edit_file` - Make precise edits using string replacement
- `run_shell` - Execute shell commands (with timeout and dangerous command blocking)
- `search_files` - Find files by pattern or grep content
- `list_directory` - List directory contents
- `task_complete` - Signal task completion and provide final answer

Configuration:
- `AGENT_MAX_STEPS=50` - Max steps per agent run
- `AGENT_MAX_RETRIES=3` - Retries for malformed responses
- `AGENT_ALLOWED_PATHS=/tmp` - Comma-separated allowed paths for security
- `AGENT_SHELL_TIMEOUT=30` - Shell command timeout (seconds)

### 3. Claude Harness (`apps/claude-harness/`) ✅ IMPLEMENTED

FastAPI service wrapping Claude Code CLI for Claude Max subscription access.

**Purpose**: Access Claude models via Claude Max subscription without API keys

**Status**: ✅ Implemented and deployed

**Features**:
- Runs as systemd service on host (not Docker)
- Wraps `claude -p` CLI for headless operation
- Exposes OpenAI-compatible `/v1/chat/completions` endpoint
- Uses OAuth tokens from `~/.claude.json`

**Architecture**:
```
┌─────────────────────────────────────────────┐
│           Claude Harness (systemd:8013)     │
├─────────────────────────────────────────────┤
│  FastAPI Service                            │
│    │                                        │
│    └─→ claude -p "prompt" --no-input        │
│          └─→ ~/.claude.json (OAuth tokens)  │
│                └─→ api.anthropic.com        │
└─────────────────────────────────────────────┘
```

**Management**:
```bash
cd ~/server/apps/claude-harness
sudo ./manage.sh install   # First-time setup
sudo ./manage.sh update    # After git pull
./manage.sh status         # Check health
./manage.sh test           # Verify working
```

**Documentation**: [apps/claude-harness/README.md](../../apps/claude-harness/README.md)

### 4. OpenCode Container (`apps/opencode-service/`) - SUPERSEDED

~~Containerized OpenCode with oh-my-opencode for subscription-based API access.~~

**Status**: ❌ Superseded by Claude Harness

The Claude Harness approach is simpler and more reliable:
- No browser session management
- No container credential mounting
- Standard OAuth via Claude Code CLI
- Same subscription access (Claude Max)

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
- [x] Purchase 1U shelf for GPU mount
- [x] Mount RTX 3070 in rack (external vertical mount)
- [x] Connect GPU to server (PCIe riser + power)
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
- [x] Create FastAPI service
- [x] Implement OpenAI-compatible API
- [x] Add backend health checks
- [x] Implement routing logic
- [x] Add force-big signal detection
- [ ] Connect to 3070 backend (pending Phase 0/1)
- [x] Connect to 3090 backend (via Windows IP)
- [x] Add logging and metrics
- [x] Deploy to server with Traefik (https://local-ai-api.server.unarmedpuppy.com)
- [x] **Add agent endpoint** - Host-controlled agent loop following OpenCode design
  - [x] Implement single-action constraint (ONE action per turn)
  - [x] Host validates and executes tools (read_file, write_file, edit_file, run_shell, search_files, list_directory)
  - [x] Provider-agnostic design for easy model swapping
  - [x] Deployed at `/agent/run` and `/agent/tools`

### Phase 3: Claude Harness (`apps/claude-harness/`) ✅ COMPLETE
- [x] Create FastAPI harness service
- [x] Create systemd service file
- [x] Create management script (`manage.sh`)
- [x] Update router providers.yaml
- [x] Document setup process
- [ ] Install Claude Code CLI on server (manual step)
- [ ] Authenticate Claude Code on server (manual step)
- [ ] Run `sudo ./manage.sh install` on server

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
| `local-ai-router` | `apps/local-ai-router/` | 8012 | Main entry point |
| `claude-harness` | `apps/claude-harness/` | 8013 | Claude Max access (systemd) |
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

### Agent Endpoint (Autonomous Tasks)
```bash
# Run an autonomous agent task
curl -X POST https://local-ai-api.server.unarmedpuppy.com/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create a Python script that prints hello world",
    "working_directory": "/tmp",
    "model": "auto",
    "max_steps": 20
  }'

# List available agent tools
curl https://local-ai-api.server.unarmedpuppy.com/agent/tools
```

## Related Documents

- [Mattermost Gateway](mattermost-gateway-service.md) - For Tayne gaming mode commands
- [Gaming PC Local AI](../../local-ai/README.md) - Current 3090 setup
- [Local AI App](../../apps/local-ai-app/README.md) - Web chat interface

## Open Questions

1. ~~**OpenCode session persistence** - How to keep browser sessions alive in container?~~ → Solved by Claude Harness
2. **Rate limiting** - Should we rate limit Claude/GLM calls?
3. **Metrics** - What to track? Token usage, latency, routing decisions?
4. **TTS** - Still planning Chatterbox Turbo on 3070? (from old plan)
5. **Claude token refresh** - OAuth tokens may expire (~30 days), need re-authentication

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-28 | Unified plan created | Consolidate scattered docs |
| 2025-12-28 | OpenCode for sub-based access | Avoid API key fees |
| 2025-12-28 | Gaming mode = simple on/off | Keep it simple |
| 2025-12-28 | Router uses token estimate | Automatic complexity detection |
| 2025-12-28 | **Add host-controlled agent endpoint** | Enable programmatic autonomous tasks, mirroring OpenCode's proven design pattern for provider-agnostic agent execution |
| 2025-01-01 | **Claude Harness over OpenCode container** | Simpler approach - wrap Claude Code CLI directly instead of containerizing OpenCode. Uses native OAuth, no browser session management needed. |
| 2025-01-01 | **Systemd over Docker for harness** | Claude Code stores OAuth tokens in user home dir. Running as systemd service on host is simpler than mounting credentials into Docker. |
