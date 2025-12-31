# Local AI Router

Intelligent OpenAI-compatible API router for multi-backend LLM inference.

## URLs

| Context | URL |
|---------|-----|
| Docker network | `http://local-ai-router:8000` |
| Server localhost | `http://localhost:8012` |
| External (HTTPS) | `https://local-ai-api.server.unarmedpuppy.com` |

## Features

- **OpenAI-compatible API** - Drop-in replacement for OpenAI endpoints
- **Intelligent routing** - Routes based on token count, task complexity, and backend availability
- **Gaming mode aware** - Respects gaming mode on Windows PC
- **Force-big override** - Explicit routing with headers or model names
- **Health checks** - Monitors all backends
- **Streaming support** - Full SSE streaming for chat completions
- **Agent endpoint** - Host-controlled agent loop for autonomous task execution

## Backends

| Backend | Hardware | Status | Use Case |
|---------|----------|--------|----------|
| 3090 | Gaming PC | ✅ Active | Medium models, coding tasks |
| 3070 | Home Server | ⏳ Pending | Small models, fast routing |
| OpenCode | Container | ⏳ Pending | GLM-4.7, Claude via subscription |

## Routing Logic

1. **Explicit model request** → Route to requested backend
2. **Token estimate < 2K** → 3070 (fast path)
3. **Gaming mode ON** → 3070 only (unless force-big)
4. **Token 2K-16K + 3090 available** → 3090
5. **Complex/long context** → OpenCode
6. **Fallback** → 3070 → 3090 → OpenCode

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

### Force to 3090
```bash
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Force-Big: true" \
  -d '{
    "model": "big",
    "messages": [{"role": "user", "content": "Complex coding task..."}]
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

See [agent-endpoint-usage skill](../../agents/skills/agent-endpoint-usage/SKILL.md) for complete documentation.

## Model Aliases

| Alias | Routes To |
|-------|-----------|
| `auto` | Intelligent routing |
| `small`, `fast` | 3070 |
| `big`, `medium`, `3090`, `gaming-pc` | 3090 |
| `glm` | OpenCode (GLM-4.7) |
| `claude` | OpenCode (Claude) |

## Metrics and Memory System

The router maintains **two separate systems** for tracking and storing data:

### 1. Metrics System (Always On)

**Purpose**: Logs all API requests for analytics and monitoring

**Storage**: SQLite database (`data/local-ai-router.db` - metrics table)

**Behavior**:
- ✅ **Always enabled** by default
- ✅ Logs every request automatically
- ✅ No headers required
- ✅ Captures: model usage, tokens, duration, errors, backend routing

**Use Case**: Dashboard analytics, usage statistics, performance monitoring

### 2. Memory System (Opt-In)

**Purpose**: Stores conversation history for context and retrieval

**Storage**: SQLite database (`data/local-ai-router.db` - conversations/messages tables)

**Behavior**:
- ⚠️ **Opt-in via headers** - NOT enabled by default for API requests
- ⚠️ Requires explicit request headers to save conversations
- ⚠️ **X-User-ID is REQUIRED** when memory is enabled (returns HTTP 400 if missing)
- ✅ Supports conversation threading and RAG search
- ✅ Auto-generates conversation IDs if not provided

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
| **Enabled by default** | ✅ Yes | ❌ No (opt-in) |
| **Requires headers** | ❌ No | ✅ Yes (`X-Enable-Memory` + `X-User-ID`) |
| **Stores messages** | ❌ No | ✅ Yes (full conversation) |
| **Used for analytics** | ✅ Yes | ❌ No |
| **Used for RAG search** | ❌ No | ✅ Yes |
| **Conversation threading** | ❌ No | ✅ Yes |

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
- **Metrics** → Main dashboard (total messages, model usage, activity)
- **Memory** → Conversations tab (browsable conversation history)
- **RAG Search** → Semantic search across stored conversations

## Configuration

Environment variables:

```bash
# Backend endpoints
GAMING_PC_URL=http://192.168.86.63:8000
LOCAL_3070_URL=http://local-ai-server:8001
OPENCODE_URL=http://opencode-service:8002

# Routing thresholds
SMALL_TOKEN_THRESHOLD=2000
MEDIUM_TOKEN_THRESHOLD=16000

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
AGENT_SKILLS_DIR=/app/agents/skills  # Skills directory (mounted from host)
```

## Force-Big Signals

Override gaming mode restrictions:

1. **Header**: `X-Force-Big: true`
2. **Model name**: `model = "big"` or `model = "3090"`
3. **Prompt tag**: Include `#force_big` in message

## Related

- [Local AI Unified Architecture](../../agents/plans/local-ai-unified-architecture.md) - Full architecture plan
- [Gaming PC Local AI](../../local-ai/README.md) - 3090 backend
- [Local AI Dashboard](../local-ai-dashboard/README.md) - Web dashboard UI
