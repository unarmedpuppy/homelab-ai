# Local AI Router

OpenAI-compatible API router for multi-backend LLM inference. Routes requests across local GPUs, cloud providers, and job-based services.

## URLs

| Context | URL |
|---------|-----|
| Docker network | `http://local-ai-router:8000` |
| Server localhost | `http://localhost:8012` |
| External (HTTPS) | `https://local-ai-api.server.unarmedpuppy.com` |

## Features

- **OpenAI-compatible API** - Drop-in replacement for OpenAI endpoints
- **Simplified auto-routing** - 3090 default, Z.ai fallback. No complexity classification.
- **X-Provider / X-Model headers** - Explicit provider and model selection
- **X-Enable-Tracing** - Per-request tracking toggle
- **Willow proxy** - Job-based Claude Code subscription access
- **Rolling conversation compaction** - Context window management
- **Dynamic context capping** - Agent vs interactive context limits
- **/v1/routing/config** - Client discovery endpoint
- **Gaming mode aware** - Respects gaming mode on Windows PC
- **Health checks** - Monitors all backends
- **Streaming support** - Full SSE streaming for chat completions
- **Agent endpoint** - Host-controlled agent loop for autonomous task execution

## Backends

| Backend | Hardware/Service | Type | Status | Use Case |
|---------|------------------|------|--------|----------|
| `gaming-pc-3090` | RTX 3090 + 3090 Ti (48GB) | local | Active | Primary for all auto-routing |
| `server-3070` | RTX 3070 (8GB) | local | Active | Manual only (model=3070) |
| `zai` | Z.ai Coding Plan (GLM models) | cloud | Active | Fallback when 3090 unavailable |
| `willow` | Containerized Claude Code subscription | job | Active | Explicit only (X-Provider: willow) |

## Routing Logic

1. **X-Provider header** → Explicit provider selection (highest precedence)
2. **X-Model header** → Explicit model on that provider
3. **model=auto** → gaming-pc-3090 default (qwen3-32b-awq), fallback to Z.ai (glm-5) if 3090 unavailable
4. **model=\<alias\>** → Resolve alias, route to target model's provider
5. **Gaming mode ON + auto** → Z.ai only (skip local GPUs)
6. No complexity classification. No context-based escalation.

## API Endpoints

### Chat Completions

```bash
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Explicit Provider Routing

Use `X-Provider` and `X-Model` headers to bypass auto-routing and target a specific backend and model.

```bash
# Route to Z.ai with a specific model
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Provider: zai" \
  -H "X-Model: glm-5" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Complex coding task..."}]
  }'

# Route to the 3070 explicitly
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Provider: server-3070" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Quick question"}]
  }'
```

### Routing Config Discovery

Clients can query the router for available providers, models, and aliases:

```bash
curl https://local-ai-api.server.unarmedpuppy.com/v1/routing/config
```

### Willow Jobs

Willow provides job-based access to a containerized Claude Code subscription. Jobs are submitted and polled asynchronously.

```bash
# Submit a job
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/willow/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Analyze the error in server.py and suggest a fix",
    "working_directory": "/home/user/project"
  }'

# Poll job status
curl https://local-ai-api.server.unarmedpuppy.com/v1/willow/jobs/{id}

# Willow health check
curl https://local-ai-api.server.unarmedpuppy.com/v1/willow/health
```

### Tracing Toggle

Disable all logging and tracking for a request by setting `X-Enable-Tracing: false`:

```bash
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Enable-Tracing: false" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Streaming Modes

The router supports two streaming modes:

| Mode | Header | Format | Use Case |
|------|--------|--------|----------|
| **Passthrough** (default) | None | OpenAI-compatible SSE | SDK integration, external clients |
| **Enhanced** | `X-Enhanced-Streaming: true` | Status-based SSE | Dashboard, debugging |

**Passthrough Mode** (default): Forwards SSE chunks directly from the backend. Compatible with OpenAI Python/JS SDKs.

```bash
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer lai_xxx" \
  -d '{"model": "auto", "messages": [{"role": "user", "content": "Hello"}], "stream": true}'
```

**Enhanced Mode**: Includes routing status events (routing, loading, streaming, done). Used by the dashboard.

```bash
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer lai_xxx" \
  -H "X-Enhanced-Streaming: true" \
  -d '{"model": "auto", "messages": [{"role": "user", "content": "Hello"}], "stream": true}'
```

### List Models
```bash
curl https://local-ai-api.server.unarmedpuppy.com/v1/models
```

### Health Check
```bash
curl https://local-ai-api.server.unarmedpuppy.com/health
```

### Gaming Mode Control
```bash
# Enable gaming mode
curl -X POST https://local-ai-api.server.unarmedpuppy.com/gaming-mode?enable=true

# Disable gaming mode
curl -X POST https://local-ai-api.server.unarmedpuppy.com/gaming-mode?enable=false

# Stop all models
curl -X POST https://local-ai-api.server.unarmedpuppy.com/stop-all
```

## Headers Reference

| Header | Direction | Purpose |
|--------|-----------|---------|
| `X-Provider` | Request | Route to specific provider (`gaming-pc-3090`, `zai`, `willow`, `server-3070`) |
| `X-Model` | Request | Select specific model on the provider |
| `X-Enable-Tracing` | Request | Set to `false` to disable all logging/tracking |
| `X-Provider` | Response | Which provider served the request |
| `X-Model` | Response | Which model served the request |
| `X-Conversation-ID` | Both | Conversation ID for session continuity |
| `X-Enhanced-Streaming` | Request | Enable enhanced streaming mode (dashboard) |

## Model Aliases

| Alias | Routes To |
|-------|-----------|
| `auto` | 3090 default, Z.ai fallback |
| `small`, `fast` | 3090 default |
| `big`, `large` | GLM-5 (Z.ai) |
| `gaming-pc`, `medium` | 3090 default |
| `glm` | GLM-5 |
| `3070`, `server` | qwen2.5-7b-awq (manual only) |
| `qwopus` | qwopus-27b |
| `abliterated` | qwen3.5-27b-abliterated |

## Context Capping

Dynamic context allocation based on API key priority:

- **Interactive users** (priority 1, default): Full 65K context on local GPUs
- **Agent requests** (priority 0, `agent-*` keys): Capped at 16K `max_tokens` on local GPUs

This allows concurrency on the 3090 -- 3 concurrent requests with 16K each fits in the 97K KV cache.

## Metrics and Memory System

The router maintains **two separate systems** for tracking and storing data:

### 1. Metrics System (Always On)

**Purpose**: Logs all API requests for analytics and monitoring

**Storage**: SQLite database (`data/local-ai-router.db` - metrics table)

**Behavior**:
- Always enabled by default
- Logs every request automatically
- No headers required
- Captures: model usage, tokens, duration, errors, backend routing

**Use Case**: Dashboard analytics, usage statistics, performance monitoring

### 2. Memory System (Opt-In)

**Purpose**: Stores conversation history for context and retrieval

**Storage**: SQLite database (`data/local-ai-router.db` - conversations/messages tables)

**Behavior**:
- Opt-in via headers -- NOT enabled by default for API requests
- Requires explicit request headers to save conversations
- `X-User-ID` is REQUIRED when memory is enabled (returns HTTP 400 if missing)
- Supports conversation threading and RAG search
- Auto-generates conversation IDs if not provided

**Enable Memory for a Request:**

```bash
# Enable memory with header (X-User-ID is REQUIRED)
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Enable-Memory: true" \
  -H "X-User-ID: user123" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Remember this conversation"}]
  }'

# Or use a specific conversation ID (X-User-ID still required for new conversations)
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Conversation-ID: my-conversation-123" \
  -H "X-User-ID: user123" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Continue our chat"}]
  }'
```

**Memory Headers:**

| Header | Purpose | Required |
|--------|---------|----------|
| `X-Enable-Memory: true` | Save this conversation to memory | To enable memory |
| `X-User-ID: <id>` | Associate with user | **REQUIRED** when memory enabled |
| `X-Conversation-ID: <id>` | Continue existing conversation | Optional (auto-generated) |
| `X-Session-ID: <id>` | Group conversations by session | Optional |
| `X-Project: <name>` | Tag with project name | Optional |

**Key Differences:**

| Feature | Metrics | Memory |
|---------|---------|--------|
| **Enabled by default** | Yes | No (opt-in) |
| **Requires headers** | No | Yes (`X-Enable-Memory` + `X-User-ID`) |
| **Stores messages** | No | Yes (full conversation) |
| **Used for analytics** | Yes | No |
| **Used for RAG search** | No | Yes |
| **Conversation threading** | No | Yes |

**Why Two Systems?**

- **Privacy**: Not all API calls should be permanently stored
- **Control**: Clients opt-in to memory storage
- **Performance**: Metrics are lightweight, memory is verbose
- **Use case separation**: Analytics vs. conversation history

### Memory API Endpoints

```bash
# List conversations
curl https://local-ai-api.server.unarmedpuppy.com/memory/conversations?limit=10

# Get specific conversation with messages
curl https://local-ai-api.server.unarmedpuppy.com/memory/conversations/{id}

# Search conversations (RAG)
curl -X POST https://local-ai-api.server.unarmedpuppy.com/memory/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What did we discuss about Python?",
    "limit": 5,
    "similarity_threshold": 0.3
  }'

# Memory statistics
curl https://local-ai-api.server.unarmedpuppy.com/memory/stats
```

### Dashboard Integration

The [Local AI Dashboard](../local-ai-dashboard/README.md) displays:
- **Metrics** -> Main dashboard (total messages, model usage, activity)
- **Memory** -> Conversations tab (browsable conversation history)
- **RAG Search** -> Semantic search across stored conversations

## Agent Endpoints

### Agent Endpoint (Skill-Based Autonomous Tasks)

Run autonomous agent tasks using a **skill-based architecture**. Instead of hardcoded capabilities, the agent discovers and follows skills from `agents/skills/` - the same skills used by human operators.

```bash
# Run an agent task
curl -X POST https://local-ai-api.server.unarmedpuppy.com/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Restart the homepage container",
    "working_directory": "/tmp",
    "model": "auto",
    "max_steps": 20
  }'
```

**Agent Workflow:**
1. Agent receives task
2. Calls `list_skills()` or `search_skills(query)` to discover capabilities
3. Calls `read_skill(name)` to get detailed instructions
4. Follows instructions using `run_shell` (same commands humans use)
5. Calls `task_complete()` when done

**Design Principles:**
- **Skill-based discovery** - Capabilities loaded on-demand, not upfront
- **Same knowledge base** - Uses the same skills as local AI assistants
- **Host-controlled loop** - Model emits ONE action per turn
- **Provider-agnostic** - Works with any model

**Core Tools (19 total):**

| Category | Tools |
|----------|-------|
| **Skill Discovery** | `list_skills`, `read_skill`, `search_skills` |
| **File Operations** | `read_file`, `write_file`, `edit_file`, `search_files`, `list_directory` |
| **Shell** | `run_shell`, `task_complete` |
| **Git** | `git_status`, `git_diff`, `git_log`, `git_add`, `git_commit`, `git_push`, `git_pull`, `git_branch`, `git_checkout` |

**Available Skills (discovered on-demand):**

The agent can discover any skill in `agents/skills/`. Examples:
- `standard-deployment` - Deploy code to server
- `connect-server` - SSH to server
- `docker-container-management` - Container operations
- `http-api-requests` - HTTP requests with curl
- `check-service-health` - Health monitoring
- `troubleshoot-container-failure` - Debug containers

```bash
# List available agent tools
curl https://local-ai-api.server.unarmedpuppy.com/agent/tools

# Example: agent discovers and uses skills
# Task: "Check Docker containers"
# Agent flow:
#   1. search_skills("docker") -> finds docker-container-management
#   2. read_skill("docker-container-management") -> gets instructions
#   3. run_shell("bash scripts/connect-server.sh 'docker ps'") -> executes
#   4. task_complete("Found 15 running containers...") -> done
```

See [agent-endpoint-usage skill](../../.agents/skills/agent-endpoint-usage/SKILL.md) for complete documentation.

### Willow Agent Endpoint

The `/agent/run/claude` endpoint proxies to Willow, the containerized Claude Code subscription service. Unlike `/agent/run` which uses a custom agent loop with local models, this submits a job to Willow and returns a job ID for polling.

```bash
# Submit a job to Willow
curl -X POST https://local-ai-api.server.unarmedpuppy.com/agent/run/claude \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Analyze the error in server.py and suggest a fix",
    "working_directory": "/home/user/project"
  }'

# Poll job status using the returned job ID
curl https://local-ai-api.server.unarmedpuppy.com/v1/willow/jobs/{job_id}
```

## Configuration

Environment variables:

```bash
# Backend endpoints (configure with your network IPs/hostnames)
GAMING_PC_URL=http://gaming-pc.local:8000  # Your Gaming PC IP/hostname
LOCAL_3070_URL=http://local-ai-server:8000
WILLOW_URL=http://willow:8013

# Context capping
AGENT_CONTEXT_CAP=16384

# Feature flags
ENABLE_METRICS=1            # Default: 1 (enabled)
ENABLE_MEMORY=1             # Default: 1 (enabled, but opt-in per request)

# Logging
LOG_LEVEL=INFO

# Agent configuration
AGENT_MAX_STEPS=50          # Max steps per agent run
AGENT_MAX_RETRIES=3         # Retries for malformed responses
AGENT_ALLOWED_PATHS=/tmp    # Comma-separated allowed paths
AGENT_SHELL_TIMEOUT=30      # Shell command timeout (seconds)
AGENT_SKILLS_DIR=/app/.agents/skills  # Skills directory (mounted from host)
```

## Claude Code Integration Notes

### Attribution Header -- KV Cache Fix

Claude Code prepends an attribution header to every request that **invalidates the KV cache on vLLM**, causing ~90% slower inference. This must be disabled in `~/.claude/settings.json` (a shell export does NOT work):

```json
{
  "env": {
    "CLAUDE_CODE_ATTRIBUTION_HEADER": "0"
  }
}
```

Reference: https://unsloth.ai/docs/basics/claude-code

### Compaction Behavior with vLLM

The `compaction.py` module manages rolling conversation compaction for context window management. When Claude Code compacts a session it calls the same model endpoint (`ANTHROPIC_BASE_URL`) with a summarization request -- there is no separate small/fast model. With the llm-router pointing at vLLM:

- **Compaction goes to vLLM** -- the same model that handles normal requests handles the summarization. No cloud fallback.
- **Trigger is context-window-percentage-based** -- Claude Code fires compaction at ~95% of the context window reported by the model. This comes from the `context_length` field in the `/v1/models` response.
- **vLLM context window reporting matters** -- If vLLM reports a large context window (e.g. 32k) but the model was loaded with a smaller `--max-model-len`, actual OOM or truncation can occur before compaction fires. Ensure `--max-model-len` matches what vLLM advertises.
- **Early compaction** -- Set `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=70` (env var on the Claude Code side) to compact earlier and reduce the risk of hitting vLLM's actual limit.
- **CLAUDE.md survives compaction** -- Re-read from disk and re-injected after every compact. Instructions given only in conversation are lost.
- **PreCompact hook** -- innie-engine installs a PreCompact hook that fires before compaction, prompting the assistant to write working state to CONTEXT.md first.

**vLLM setup checklist for Claude Code use:**

| Item | Why |
|------|-----|
| Set `--max-model-len` explicitly | Prevents mismatch between advertised and actual context |
| Disable attribution header in `~/.claude/settings.json` | Fixes KV cache invalidation (~90% inference slowdown) |
| Set `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=70` | Compact before hitting vLLM's real limit |
| Verify `/v1/models` returns correct `context_length` | Claude Code uses this to calculate compaction threshold |

## Related

- [Local AI Dashboard](../local-ai-dashboard/README.md) - Web dashboard UI
- [Willow](../willow/README.md) - Containerized Claude Code subscription service
- [Gaming PC vLLM](../../local-ai/README.md) - 3090 backend
