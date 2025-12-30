# Local AI Specialist Agent

## Purpose

Specialized agent for working on the Local AI Router & Dashboard system - a multi-provider LLM routing service with conversation memory, provider health monitoring, and a ChatGPT-style web interface.

## System Architecture

### Core Components

1. **Local AI Router** (`apps/local-ai-router/`)
   - FastAPI-based OpenAI-compatible API server
   - Multi-provider routing with intelligent provider selection
   - Conversation memory with SQLite + vector embeddings
   - Streaming SSE support
   - Metrics tracking with Prometheus
   - Provider health checking

2. **Local AI Dashboard** (`apps/local-ai-dashboard/`)
   - React + TypeScript web interface
   - Real-time provider monitoring
   - ChatGPT-style chat interface with streaming
   - Conversation history and search
   - Stats/metrics visualization

3. **LLM Providers**
   - Gaming PC (RTX 3090): vLLM @ `http://10.0.0.188:8080`
   - Server (RTX 3070): vLLM @ `http://10.0.0.22:8080`
   - Z.ai: Cloud API @ `https://open.bigmodel.cn/api/paas/v4/`
   - Anthropic: Claude API @ `https://api.anthropic.com/v1/`

## Key Files and Locations

### Backend (Router)
- `apps/local-ai-router/router.py` - Main FastAPI app, chat completions endpoint (lines 506-584: streaming)
- `apps/local-ai-router/memory.py` - SQLite conversation storage, RAG search
- `apps/local-ai-router/dependencies.py` - Request tracking, memory logging (lines 56-156: `log_chat_completion()`)
- `apps/local-ai-router/providers/manager.py` - Provider selection, health checking, load balancing
- `apps/local-ai-router/config/providers.yaml` - Provider configuration (health checks use `/v1/models`)
- `apps/local-ai-router/TEST_SUMMARY.md` - Comprehensive test documentation for Phases 1-6

### Frontend (Dashboard)
- `apps/local-ai-dashboard/src/components/ChatInterface.tsx` - Main chat UI with streaming
- `apps/local-ai-dashboard/src/components/ConversationSidebar.tsx` - Conversation history
- `apps/local-ai-dashboard/src/components/ProviderMonitoring.tsx` - Provider health dashboard
- `apps/local-ai-dashboard/src/api/client.ts` - API client (lines 176-316: `sendMessageStreaming()`)
- `apps/local-ai-dashboard/src/App.tsx` - Main app layout with routing
- `apps/local-ai-dashboard/src/types/api.ts` - TypeScript type definitions

### Configuration
- `apps/local-ai-router/config/providers.yaml` - Provider endpoints, health checks, priorities
- `apps/local-ai-router/docker-compose.yml` - Deployment configuration
- `apps/local-ai-dashboard/docker-compose.yml` - Dashboard deployment

## Completed Phases (1-6)

### Phase 1-3: Backend Foundation ✅
**Status**: Deployed and validated

**Key Features**:
- Provider manager with health checking (`/v1/models` endpoint for vLLM)
- Conversation metadata tracking (username, source, display_name)
- Admin endpoints: `/admin/providers`, `/providers`
- Explicit provider/model selection via `model: "provider-id/model-id"`
- Provider info in API responses

**Important Fixes**:
- Issue #1: Conversation history loading with missing metadata fields (commit `46f9a199`)
- Issue #2: Provider selection routing failures (commit `46f9a199`)
- Issue #3: vLLM health check endpoint (commit `fc086ec4` - changed from `/health` to `/v1/models`)

**Files Modified**:
- `providers/manager.py` - Provider/model selection with explicit routing
- `memory.py` - Safe optional field access with try/except
- `config/providers.yaml` - Health check endpoint configuration

### Phase 4: Provider Monitoring Dashboard ✅
**Status**: Deployed (manual testing required)

**Key Features**:
- Real-time provider health status display
- Auto-refresh every 10 seconds
- Load utilization visualization (color-coded bars)
- Model availability lists with capabilities
- Summary stats (total/healthy/offline counts)

**Files Modified**:
- `apps/local-ai-dashboard/src/types/api.ts` - Provider types
- `apps/local-ai-dashboard/src/api/client.ts` - `providersAPI.list()`, `providersAPI.listAdmin()`
- `apps/local-ai-dashboard/src/components/ProviderMonitoring.tsx` - New component
- `apps/local-ai-dashboard/src/App.tsx` - Navigation and routing

**Deployment**: Commit `5ffa92ea`

### Phase 5: Chat Experience Enhancement ✅
**Status**: Deployed (manual testing required)

**Key Features**:
- Dynamic model/provider selection from `/admin/providers` API
- Auto-refresh provider data every 30 seconds
- Model selector format: `provider-id/model-id` (e.g., `gaming-pc-3090/qwen2.5-14b-awq`)
- Health-aware UI - offline providers disabled with "(offline)" label
- Enhanced message metadata (provider, model, backend, tokens)
- Conversation browsing and search (pre-existing)

**Files Modified**:
- `apps/local-ai-dashboard/src/components/ChatInterface.tsx` - Dynamic model loading

**Deployment**: Commit `5ffa92ea`

**Manual Testing**: See `apps/local-ai-router/PHASE_5_MANUAL_TESTING.md`

### Phase 6: Streaming Responses ✅
**Status**: Deployed (manual testing required)

**Key Features**:
- Frontend SSE streaming with fetch API + ReadableStream
- Real-time token-by-token display
- Live streaming indicators ("connecting...", "streaming... N tokens")
- Animated green pulsing cursor at end of streaming text
- Graceful error handling and cleanup
- Auto-scroll during streaming

**Backend Implementation**:
- Basic SSE pass-through (pre-existing)
- ⚠️ **CRITICAL**: Streaming memory persistence added (commits `87e21e9e`, `841d8e5b`)
  - Accumulates stream chunks during streaming
  - Parses SSE data in background task after stream completes
  - Calls `log_chat_completion()` to save to database
  - Fixed AsyncClient context manager issue (moved inside generator)

**Files Modified**:
- `apps/local-ai-router/router.py` (lines 506-584) - Streaming with memory persistence
- `apps/local-ai-dashboard/src/api/client.ts` (lines 176-316) - `sendMessageStreaming()`
- `apps/local-ai-dashboard/src/components/ChatInterface.tsx` - Streaming UI

**Deployment**: Commit `0f1a253d` (frontend), commits `87e21e9e` + `841d8e5b` (backend streaming memory)

**Manual Testing**: See `apps/local-ai-router/TEST_SUMMARY.md` lines 392-426

## Current Status & Known Issues

### ⚠️ Critical Blocker: Gaming PC vLLM Offline

**Issue**: Gaming PC vLLM service unreachable at `10.0.0.188:8080`
- Both streaming and non-streaming requests timeout
- Connection can't be established (not an httpx error, just no connection)
- SSH to Gaming PC also hanging

**Root Cause**: Gaming PC is either:
1. Powered off
2. Network unreachable
3. IP address changed
4. Firewall blocking port 8080
5. vLLM service not running

**Impact**:
- Streaming memory persistence fix cannot be validated
- New conversations not creating conversation IDs
- Dashboard chat requests hang indefinitely
- Provider monitoring shows gaming-pc-3090 as offline

**Next Steps**:
1. Verify Gaming PC is powered on and accessible at `10.0.0.188`
2. Check vLLM service status: `docker ps | grep vllm` or `ps aux | grep vllm`
3. Restart vLLM service if needed
4. Once online, validate streaming memory persistence (see task home-server-53u)

### Pending Validation (Blocked by vLLM)

**Beads Task**: `home-server-53u` - "Validate streaming memory persistence once vLLM is running"

**Test Plan**:
1. Verify vLLM service running and accessible
2. Test streaming chat completion via dashboard UI
3. Confirm streaming conversations saved to database
4. Validate commits `87e21e9e` and `841d8e5b` work correctly
5. Update TEST_SUMMARY.md with results

**Manual Testing Required**:
- Phase 5 features (dynamic model selection, metadata display)
- Phase 6 features (streaming UX, token counters, cursors)
- See `apps/local-ai-router/PHASE_5_MANUAL_TESTING.md` for detailed test cases

## Technical Details

### Streaming Memory Persistence Implementation

**Problem**: Streaming conversations were not being saved to database (original user report: "how come the last conversation i started in the ui dashboard has dispeared?")

**Solution** (commits `87e21e9e`, `841d8e5b`):

```python
# router.py lines 506-584
if stream:
    accumulated_chunks = []
    full_content = ""
    metadata = {}

    async def stream_response():
        nonlocal full_content, metadata
        # AsyncClient MUST be inside generator to prevent premature closure
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("POST", endpoint_url, json=body, ...) as response:
                async for chunk in response.aiter_bytes():
                    accumulated_chunks.append(chunk)  # Store for later
                    yield chunk  # Stream immediately

    async def process_stream_completion():
        # Parse accumulated SSE chunks
        for chunk in accumulated_chunks:
            # Extract content from delta.content
            # Extract metadata (id, model, usage)

        # Construct response_data matching non-streaming format
        response_data = {
            'id': metadata.get('id', 'unknown'),
            'choices': [{'message': {'role': 'assistant', 'content': full_content}}],
            'usage': metadata.get('usage', {}),
            'provider': selection.provider.id,
        }

        # Save to memory/database
        log_chat_completion(tracker, body, response_data, error=None)
```

**Key Points**:
- AsyncClient created INSIDE generator to prevent context manager closing early
- Chunks accumulated while streaming to client simultaneously
- Background task parses SSE data after streaming completes
- Uses same `log_chat_completion()` function as non-streaming

### Provider Configuration

All providers use `/v1/models` for health checks (not `/health`):

```yaml
# config/providers.yaml
gaming-pc-3090:
  baseUrl: "http://10.0.0.188:8080"
  healthCheckPath: "/v1/models"  # vLLM standard health check

server-3070:
  baseUrl: "http://10.0.0.22:8080"
  healthCheckPath: "/v1/models"
```

### Memory System Headers

All chat requests include:
```
X-Enable-Memory: true
X-Project: dashboard
X-User-ID: dashboard-user
X-Conversation-ID: <conversation-id>  # if continuing conversation
```

### API Endpoints

**Public API** (port 8012, via Traefik):
- `POST /v1/chat/completions` - OpenAI-compatible chat (streaming/non-streaming)
- `GET /providers` - Basic provider list
- `GET /admin/providers` - Detailed provider status with health/load
- `GET /memory/conversations` - List conversations
- `GET /memory/conversations/{id}` - Get conversation
- `POST /memory/search` - RAG search
- `GET /metrics/dashboard` - Metrics/stats

**Dashboard URL**: https://local-ai-dashboard.server.unarmedpuppy.com/

## Development Workflow

### Testing Backend Changes

```bash
# Local development
cd apps/local-ai-router
python router.py  # Runs on port 8000

# Deploy to server
git add . && git commit -m "..." && git push
ssh server
cd /home/unarmedpuppy/server/apps/local-ai-router
git pull
docker compose build --no-cache  # IMPORTANT: Rebuild image
docker compose up -d
docker compose logs -f --tail 100
```

### Testing Frontend Changes

```bash
# Local development
cd apps/local-ai-dashboard
npm run dev

# Deploy to server
git add . && git commit -m "..." && git push
ssh server
cd /home/unarmedpuppy/server/apps/local-ai-dashboard
git pull
docker compose build --no-cache  # IMPORTANT: Rebuild image
docker compose up -d
```

### Checking Logs

```bash
# Router logs
ssh server
docker logs local-ai-router-api-1 --tail 100 -f

# Dashboard logs
docker logs local-ai-dashboard-dashboard-1 --tail 100 -f

# Provider health checks
curl http://localhost:8012/admin/providers | jq
```

## Common Debugging Steps

### 1. Provider Showing as Offline

```bash
# Check health endpoint directly
curl http://10.0.0.188:8080/v1/models  # Gaming PC
curl http://10.0.0.22:8080/v1/models   # Server

# Check router can reach provider
ssh server
curl http://10.0.0.188:8080/v1/models
```

### 2. Streaming Not Working

```bash
# Test streaming directly to provider
curl -X POST http://10.0.0.188:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen2.5-14b-awq", "messages": [{"role": "user", "content": "Hello"}], "stream": true}' \
  --no-buffer -N

# Test streaming through router
curl -X POST http://localhost:8012/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "auto", "messages": [{"role": "user", "content": "Hello"}], "stream": true}' \
  --no-buffer -N
```

### 3. Memory Not Persisting

```bash
# Check conversation exists
ssh server
docker exec -it local-ai-router-api-1 bash
sqlite3 /app/data/conversations.db "SELECT * FROM conversations ORDER BY created_at DESC LIMIT 5;"

# Check messages saved
sqlite3 /app/data/conversations.db "SELECT conversation_id, role, substr(content, 1, 50) FROM messages ORDER BY created_at DESC LIMIT 10;"
```

### 4. Docker Container Not Picking Up Code Changes

```bash
# MUST rebuild with --no-cache
docker compose build --no-cache
docker compose up -d

# Verify new image created
docker images | grep local-ai
```

## Important Commits

- `46f9a199` - Fix conversation history loading + provider selection routing
- `fc086ec4` - Update vLLM health check endpoint to /v1/models
- `5ffa92ea` - Phase 5: Dynamic provider/model selection
- `0f1a253d` - Phase 6: Frontend streaming support
- `87e21e9e` - Phase 6: Backend streaming memory persistence (initial)
- `841d8e5b` - Phase 6: Fix AsyncClient context manager for streaming

## Reference Documentation

- **Implementation Plans**: `agents/plans/local-ai-*.md`
- **Test Documentation**: `apps/local-ai-router/TEST_SUMMARY.md`
- **Manual Test Guide**: `apps/local-ai-router/PHASE_5_MANUAL_TESTING.md`
- **Provider Config**: `apps/local-ai-router/config/providers.yaml`
- **API Types**: `apps/local-ai-dashboard/src/types/api.ts`

## Future Enhancements (Not Implemented)

- Conversation renaming/editing
- Conversation export
- Conversation folders/tags
- Multi-user support with authentication
- Custom system prompts
- Model warmup status indicators
- Provider failover automation
- Advanced metrics dashboards
- Cost tracking per provider

## Agent Guidelines

When working on the Local AI system:

1. **Always check TEST_SUMMARY.md first** - Contains comprehensive status of all phases
2. **Reference correct file locations** - Use line numbers from Read tool output
3. **Remember the streaming memory fix** - Commits 87e21e9e and 841d8e5b are critical
4. **Check provider health** - Gaming PC vLLM is currently offline/unreachable
5. **Rebuild Docker images** - Always use `--no-cache` when deploying code changes
6. **Test streaming separately** - Frontend and backend streaming are separate systems
7. **Validate memory persistence** - Check SQLite database to confirm conversations saved
8. **Use correct health endpoints** - vLLM uses `/v1/models` not `/health`
9. **Read git history** - Important fixes in commits listed above
10. **Manual testing required** - Many features need browser testing (see test guides)
