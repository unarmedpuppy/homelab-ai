# Local AI Architecture Audit - December 2025

**Date**: 2025-12-29
**Status**: Initial audit and planning phase
**Primary Use Case**: Agent backend (90%), Personal chat (10%)

## Executive Summary

Comprehensive architectural review of the local-first AI infrastructure, identifying gaps between current implementation and planned provider/model architecture. System currently operational with basic routing but needs significant enhancement for multi-agent support, provider abstraction, and intelligent failover.

---

## System Overview

### Architecture Goals
1. **Local-first**: Prioritize local GPU inference over cloud APIs
2. **Agent-focused**: Stable API for autonomous agents (90% of usage)
3. **OpenAI-compatible**: Drop-in replacement for OpenAI SDK
4. **Intelligent routing**: Auto-select best provider based on availability, capabilities, cost
5. **Low-maintenance**: Self-healing with cloud fallback

### Current Components

**1. Local AI Router** (`apps/local-ai-router/`)
- FastAPI-based OpenAI-compatible API
- Routes to: Gaming PC (3090), Home Server (3070), OpenCode/ZAI, Anthropic
- SQLite for metrics and conversation memory
- Agent endpoint with tool execution
- Gaming mode awareness

**2. Local AI Dashboard** (`apps/local-ai-dashboard/`)
- React + TanStack Query UI
- Conversation browsing and real-time chat
- URL-based routing for deep linking
- Memory API integration

**3. Local AI App** (`apps/local-ai-app/`) - **DEPRECATED**
- Older Windows proxy with image upload support
- **Decision**: Migrate image upload to dashboard, sunset this service

---

## Current System State

### ✅ Working Features

**Router Infrastructure**
- ✅ OpenAI-compatible endpoints (`/v1/chat/completions`, `/v1/models`)
- ✅ Basic routing logic with model aliases
- ✅ Gaming mode detection (Windows PC)
- ✅ Metrics tracking (always-on, separate from memory)
- ✅ Memory system (opt-in via headers)
- ✅ Agent execution loop with tools
- ✅ CORS configured for dashboard

**Data Storage**
- ✅ SQLite with WAL mode for concurrency
- ✅ Conversation threading with messages
- ✅ Metrics for analytics
- ✅ RAG search capability

**Dashboard**
- ✅ Conversation list and detail view
- ✅ Real-time chat interface
- ✅ URL routing (deep links to conversations)
- ✅ Model selection dropdown
- ✅ Advanced settings (temperature, top_p, etc.)

### 🔴 Critical Gaps

**1. Provider/Model Separation** ⚠️ **HIGH PRIORITY**
- **Problem**: Providers conflated with models in hardcoded config
- **Current**: `BACKENDS` dict in `router.py` lines 59-80
- **Impact**: Can't distinguish "Gaming PC (3090)" from "Qwen 2.5 32B running on 3090"
- **Solution**: Implement provider/model architecture from plan

**2. No Health Checking**
- **Problem**: Can't detect provider availability dynamically
- **Current**: Manual `available: True/False` flags
- **Impact**: No intelligent failover, can route to dead backends
- **Solution**: Periodic health checks with warm/cold status

**3. Missing Configuration System**
- **Problem**: No `config/providers.yaml` - all config in env vars
- **Impact**: Must redeploy to add/modify providers
- **Solution**: YAML-based provider/model config

**4. Incomplete Conversation Metadata**
- **Problem**: Missing `username`, `source`, `display_name` fields
- **Current DB**: Has `user_id`, `session_id`, `project`, `title`
- **Impact**: Can't track which agent/interface initiated conversations
- **Solution**: Add fields to schema (migration needed)

**5. No Concurrency Management** ⚠️ **CRITICAL FOR AGENTS**
- **Problem**: Local GPUs can only handle 1 request at a time
- **Current**: No queue, no busy detection
- **Impact**: Second agent request hangs or fails while first is processing
- **Solution**: Detect busy state, immediate failover to ZAI/Anthropic for parallel requests

### 🟡 Medium Priority Gaps

**6. Authentication & Authorization**
- **Current**: No auth (network security only)
- **Decision**: API keys + IP/network verification for agents
- **Action**: Implement simple API key system

**7. Image Upload Support**
- **Current**: Only in deprecated `local-ai-app`
- **Decision**: Migrate to dashboard for multimodal models
- **Action**: Add image upload to ChatInterface component

**8. Streaming in Dashboard**
- **Current**: Router supports SSE, dashboard uses standard fetch
- **Decision**: Implement streaming (agents + UI both benefit)
- **Action**: Update dashboard to consume SSE streams

**9. No Database Migrations**
- **Problem**: Schema changes require manual SQL
- **Impact**: Risk of data loss during upgrades
- **Solution**: Add Alembic or similar migration tool

### 🟢 Lower Priority

**10. Cost Tracking**
- **Decision**: Token counts first, cost calculated from model config later
- **Current**: Token counting works
- **Action**: Add token cost to provider/model config

**11. Metrics Dashboard Enhancement**
- **Current**: Basic stats
- **Future**: Prometheus exports, richer analytics
- **Action**: Defer until provider/model architecture complete

**12. Load Balancing**
- **Current**: Priority-based fallback
- **Future**: True load balancing if multiple instances
- **Action**: Defer until needed

---

## Architecture Decisions

### User Answers (2025-12-29)

**1. Primary Use Cases**
- **Agent backend**: 90% (Claude Code agents, custom agents)
- **Personal chat**: 10%
- **OpenCode provider**: Use router as local provider for OpenCode agentic coding
- **Implication**:
  - Prioritize API stability, good error messages, retry logic, status endpoints
  - Full OpenAI API compatibility is CRITICAL (for OpenCode integration)
  - Streaming must work perfectly with OpenCode

**2. Users**
- **Primary**: Josh
- **Secondary**: Few household members
- **Agents**: Multiple (1-4 sporadically)
- **Implication**: Multi-agent concurrency is critical

**3. Agent Authentication**
- **Decision**: API keys + IP/network verification
- **Rationale**: Simple, low friction
- **Action**: Implement API key middleware

**4. Streaming**
- **Decision**: YES - implement for both agents and UI
- **Rationale**: Agents need it too for responsiveness
- **Action**: Priority feature

**5. UI Consolidation**
- **Decision**: Sunset `local-ai-app`, migrate features to dashboard
- **Action**: Add image upload to dashboard, deprecate old app

**6. Provider Expansion**
- **Decision**: Design for easy expansion
- **Rationale**: Will add more providers as available
- **Action**: YAML-based config, hot-reload support

**7. Cost Tracking**
- **Priority 1**: Token counts (already working)
- **Priority 2**: Cost calculation (from model config)
- **Action**: Add `cost_per_token` to model config

**8. Uptime Requirements**
- **Type**: Hobby project BUT low-maintenance
- **Monitoring**: Agent-monitored (automated alerts)
- **Failover**: Cloud fallback (ZAI/Anthropic) is critical
- **Action**: Design for self-healing, good observability

---

## Critical Insight: Concurrency Model

### Single-Request GPUs

**Key Constraint**: Local GPUs (3070, 3090) can only handle **ONE request at a time**

**Current Problem**:
- Agent A sends request → 3090 starts processing (30-60s)
- Agent B sends request → Router tries to use 3090 → hangs or times out

### Hybrid Concurrency Strategy (Decision: 2025-12-29)

**Algorithm**: Local failover → Queue (if local-only) → Cloud failover

```
Request arrives (with priority: agent > user)
│
├─ Step 1: Try Primary Local GPU (Gaming PC 3090)
│  ├─ If available → Route to 3090
│  └─ If busy (in-flight request exists) → Continue to Step 2
│
├─ Step 2: Try Secondary Local GPU (Server 3070)
│  ├─ If available → Route to 3070
│  └─ If busy → Continue to Step 3
│
└─ Step 3: Fallback Decision
   ├─ If "local-only mode" enabled:
   │  ├─ Queue request for up to 5 seconds
   │  ├─ If GPU becomes available → Route
   │  └─ If timeout → Return HTTP 503 "All local providers busy, try again"
   │
   └─ If normal mode (cloud fallback enabled):
      ├─ Try ZAI (cloud, can handle parallel requests)
      │  ├─ If available → Route to ZAI
      │  └─ If unhealthy → Continue
      │
      └─ Try Anthropic (final fallback)
         ├─ If available → Route to Anthropic
         └─ If unhealthy → Return HTTP 503 "No providers available"
```

### Implementation Requirements

**1. Request Tracking Per Provider**
- In-memory counter: `provider_id → active_request_count`
- Increment on request start, decrement on completion/error
- Thread-safe (use asyncio locks or atomic operations)

**2. Provider Configuration**
```yaml
providers:
  - id: gaming-pc-3090
    max_concurrent: 1      # Single request at a time
    priority: 1            # Try first

  - id: server-3070
    max_concurrent: 1      # Single request at a time
    priority: 2            # Try second

  - id: zai
    max_concurrent: 100    # Parallel requests OK
    priority: 3            # Cloud fallback

  - id: anthropic
    max_concurrent: 100    # Parallel requests OK
    priority: 4            # Final fallback
```

**3. Priority Queue**
- Agent requests have higher priority than user requests
- Within same priority level: FIFO
- Queue implementation: Python `asyncio.PriorityQueue`

**4. Local-Only Mode**
- Config flag: `ENABLE_CLOUD_FALLBACK=true/false`
- If disabled: queue briefly, then fail gracefully
- Use case: Cost control, testing local-only setup

**5. Graceful Degradation**
- If all providers busy/unhealthy: Return OpenAI-compatible error
- HTTP 503 with retry-after header
- Error format:
  ```json
  {
    "error": {
      "message": "All providers are currently busy. Please retry in a few seconds.",
      "type": "service_unavailable",
      "code": "provider_capacity_exceeded"
    }
  }
  ```

### Monitoring Metrics

**Key Metrics to Track**:
- `requests_queued_total` - How often we queue (local-only mode)
- `requests_failed_capacity` - Requests failed due to capacity
- `provider_fallback_total{from, to}` - Fallback frequency between providers
- `provider_active_requests{provider}` - Current load per provider
- `request_wait_time_seconds` - Time spent waiting in queue

**Alert Conditions**:
- `provider_active_requests` stuck at max for >5 minutes (provider hung?)
- `requests_failed_capacity` spike (need more capacity)
- Frequent fallback to cloud (local GPUs under-provisioned?)

---

## Identified Risks

### High Risk
1. **No concurrency control** → Agents hang waiting for GPU
2. **No health checks** → Route to dead backends
3. **Hardcoded config** → Can't adapt to infrastructure changes

### Medium Risk
4. **No auth** → Open to abuse if exposed
5. **No streaming** → Poor UX for long responses
6. **No migrations** → Data loss risk on schema changes

### Low Risk
7. **No cost tracking** → Can't budget cloud fallback usage
8. **Single database file** → Scaling limit (but SQLite is fine for this use case)

---

## Recommendations

### Phase 1: Critical Foundation (Week 1-2)

**1.1 Provider/Model Architecture**
- [ ] Create `config/providers.yaml` schema
- [ ] Implement ProviderManager class
- [ ] Add concurrency tracking (`in_flight_requests` counter)
- [ ] Build provider selection algorithm with concurrency awareness

**1.2 Health Checking**
- [ ] Periodic health checks (every 30s)
- [ ] Per-provider status (online/offline/degraded)
- [ ] Warm/cold model status for local providers
- [ ] Health endpoint: `GET /providers/{id}/health`

**1.3 Database Updates**
- [ ] Add migration system (Alembic)
- [ ] Add conversation metadata fields (username, source, display_name)
- [ ] Migration: existing conversations

### Phase 2: Agent Support (Week 3-4)

**2.1 Authentication**
- [ ] API key middleware
- [ ] Key management (create, revoke, rotate)
- [ ] IP allowlist verification
- [ ] Per-key usage tracking

**2.2 Streaming**
- [ ] Validate SSE streaming in router
- [ ] Update dashboard to consume streams
- [ ] Test with agents using OpenAI SDK

**2.3 Concurrency Management**
- [ ] Request queue per provider (optional)
- [ ] Busy detection and immediate failover
- [ ] Metrics: request queueing, fallback frequency

### Phase 3: Dashboard Enhancement (Week 5-6)

**3.1 Image Upload**
- [ ] File upload component
- [ ] Base64 encoding for API
- [ ] Vision model detection
- [ ] UI: show uploaded images in chat

**3.2 Provider Visibility**
- [ ] Two-step model selector (provider → model)
- [ ] Provider status indicators
- [ ] Show provider/model used per message
- [ ] Health status dashboard

**3.3 Sunset local-ai-app** ✅ COMPLETED (2025-12-30)
- [x] Verify all features migrated
- [x] Update documentation
- [x] Remove from docker-compose
- [x] Archive codebase (moved to `inactive/local-ai-app/`)

### Phase 4: Operational Excellence (Week 7-8)

**4.1 Monitoring**
- [ ] Prometheus metrics endpoint
- [ ] Key metrics: requests/sec, latency, error rate, provider health
- [ ] Agent-friendly status endpoint for automated monitoring

**4.2 Cost Tracking**
- [ ] Add `cost_per_1k_tokens` to model config
- [ ] Calculate cost per request
- [ ] Daily cost rollups in metrics

**4.3 Documentation**
- [ ] API documentation (OpenAPI spec)
- [ ] Agent integration guide
- [ ] Provider configuration guide
- [ ] Troubleshooting playbook

---

## Success Metrics

### Technical Metrics
- **Uptime**: >99% (with cloud fallback)
- **Local-first**: >80% of requests served by local GPUs
- **Latency**: <500ms routing overhead
- **Failover**: <2s to detect and failback to cloud

### Operational Metrics
- **Agent satisfaction**: Zero agent hangs due to concurrency
- **Maintenance**: <30min/week manual intervention
- **Cost**: <$50/month cloud fallback usage (track after implementation)

### User Experience
- **Dashboard**: <200ms time-to-first-token for streaming
- **Conversation search**: <1s for full-text search
- **Provider switching**: Zero configuration for new providers

---

## Open Questions

### Clarification Answers (2025-12-29)

**1. ZAI Details** ✅
- **Service**: Z.ai cloud API (third-party)
- **Auth**: API key based
- **Characteristics**: No rate limits/cost concerns, but SLOW (streaming important)
- **Models**: Multiple (GLM-4.7 mentioned)
- **Integration**: Direct integration into router (not via OpenCode initially)

**2. Concurrency Strategy** ✅
- **Model**: Hybrid with local failover preference
- **Algorithm**:
  1. Try primary local GPU (e.g., Gaming PC 3090)
  2. If busy → try secondary local GPU (e.g., Server 3070)
  3. If both busy:
     - **Local-only mode**: Queue briefly (5s), then return "unavailable, try again"
     - **Normal mode**: Failover to cloud (ZAI → Anthropic)
- **Queue timeout**: 5 seconds for local-only mode

**3. Image Upload** ✅
- **Supported models**: Claude (all vision models), Qwen Image Edit
- **Max size**: 10MB per image (reasonable default)
- **Max count**: 5 images per message
- **Storage**: Persistent (save to disk, store file references in DB)
- **Display**: Show images in conversation history

**4. API Key Management** ✅
- **Strategy**: Per-agent keys (better tracking, identify requests per agent)
- **Storage**: Database (flexibility for rotation, management)
- **Scopes**: All keys same access level initially (can add scopes later)
- **Rotation**: Manual for now

**5. Request Prioritization** ✅
- **Strategy**: Agent priority
- **Rationale**: Agents are 90% of usage, personal chat can tolerate slight delay
- **Implementation**: Priority queue with agent requests ahead of user requests

**6. Streaming** ✅
- **Standard**: OpenAI SDK compatibility
- **Rationale**: Works with OpenCode, vLLM, standard agent libraries
- **Implementation**: SSE streaming per OpenAI spec

**7. Provider Hot-Reload** ✅
- **Strategy**: Require restart for config changes
- **Rationale**: Simple, acceptable for hobby project
- **Future**: Can add hot-reload if needed

**8. Gaming Mode / Provider Availability** ✅
- **Strategy**: Generic "provider availability" toggle (not gaming-specific)
- **Control**: Manual toggle via API endpoint
- **Future enhancement**: Auto-detect system usage (GPU load, game processes)
- **Implementation**: Per-provider `enabled` flag in config, overridable via API

### Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-29 | Sunset local-ai-app | Consolidate to single dashboard UI |
| 2025-12-29 | API keys + IP verification | Simple, low-friction agent auth |
| 2025-12-29 | Per-agent API keys in database | Better tracking, can identify requests per agent |
| 2025-12-29 | Streaming required | Both agents and UI benefit |
| 2025-12-29 | OpenAI SDK compatibility | Works with OpenCode, vLLM, standard agents |
| 2025-12-29 | Token tracking first, cost calculation later | Foundation before optimization |
| 2025-12-29 | Design for easy provider expansion | YAML config, hot-reload capable |
| 2025-12-29 | Cloud fallback is critical | Low-maintenance, self-healing |
| 2025-12-29 | Hybrid concurrency: local failover → queue → cloud | Maximize local usage, fast agent response |
| 2025-12-29 | Agent priority for requests | Reflects 90% agent usage pattern |
| 2025-12-29 | Persistent image storage | Enable conversation history review |
| 2025-12-29 | Config reload requires restart | Simple, acceptable for hobby project |
| 2025-12-29 | Gaming mode → generic availability toggle | Manual control, auto-detect is future enhancement |
| 2025-12-29 | Router as OpenCode provider | Enable local agentic coding via OpenCode |

---

## Related Documentation

### Plans
- [Provider/Model Architecture Plan](../plans/local-ai-provider-model-architecture.md) - Core architectural plan
- [Unified Architecture](../plans/local-ai-unified-architecture.md) - Original unified design
- [Two GPU Architecture](../plans/local-ai-two-gpu-architecture.md) - Dual GPU setup
- [High Availability Failover](../plans/high-availability-failover.md) - Failover strategies

### Reference
- [Docker Patterns](docker.md) - Container best practices
- [Deployment Workflows](deployment.md) - Deployment automation

### Skills
- [Standard Deployment](../skills/standard-deployment/) - Deployment workflow
- [System Health Check](../skills/system-health-check/) - Monitoring procedures

---

## Appendix: Current API Endpoints

### Router Endpoints (apps/local-ai-router/)

**Core**
- `GET /` - API info
- `GET /health` - Health check
- `GET /v1/models` - List available models

**Chat**
- `POST /v1/chat/completions` - Chat completions (streaming supported)

**Agent**
- `POST /agent/run` - Run agent task loop
- `GET /agent/tools` - List available agent tools

**Memory**
- `GET /memory/conversations` - List conversations
- `GET /memory/conversations/{id}` - Get conversation with messages
- `POST /memory/conversations` - Create conversation
- `DELETE /memory/conversations/{id}` - Delete conversation
- `POST /memory/search` - Search conversations
- `GET /memory/stats` - Memory statistics

**Metrics**
- `GET /metrics/recent` - Recent requests
- `GET /metrics/daily` - Daily aggregated stats
- `GET /metrics/activity` - Activity chart data
- `GET /metrics/models` - Model usage stats
- `GET /metrics/dashboard` - Dashboard summary

**RAG**
- `POST /rag/search` - RAG search
- `POST /rag/context` - Get context for prompt

**Gaming Mode (3090 specific)**
- `POST /gaming-mode?enable=true/false` - Toggle gaming mode
- `POST /stop-all` - Stop all models on gaming PC

---

## Appendix: Database Schema

### Current Schema (SQLite)

**conversations**
```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    session_id TEXT,
    user_id TEXT,
    project TEXT,
    title TEXT,
    metadata TEXT,  -- JSON
    message_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0
);
```

**messages**
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    role TEXT NOT NULL,  -- user, assistant, system, tool
    content TEXT,
    model_used TEXT,
    backend TEXT,
    tokens_prompt INTEGER,
    tokens_completion INTEGER,
    tool_calls TEXT,  -- JSON
    tool_results TEXT,  -- JSON
    metadata TEXT,  -- JSON
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);
```

**metrics**
```sql
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    date DATE NOT NULL,
    conversation_id TEXT,
    session_id TEXT,
    endpoint TEXT,
    model_requested TEXT,
    model_used TEXT,
    backend TEXT,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    duration_ms INTEGER,
    success BOOLEAN,
    error TEXT,
    streaming BOOLEAN,
    tool_calls_count INTEGER,
    user_id TEXT,
    project TEXT
);
```

**daily_stats**
```sql
CREATE TABLE daily_stats (
    date DATE PRIMARY KEY,
    total_requests INTEGER,
    total_messages INTEGER,
    total_tokens INTEGER,
    unique_conversations INTEGER,
    unique_sessions INTEGER,
    models_used TEXT,  -- JSON
    backends_used TEXT,  -- JSON
    avg_duration_ms REAL,
    success_rate REAL,
    updated_at DATETIME
);
```

### Proposed Schema Changes

**conversations** (add fields)
```sql
ALTER TABLE conversations ADD COLUMN username TEXT;
ALTER TABLE conversations ADD COLUMN source TEXT;  -- 'ui-dashboard', 'api', 'agent-name'
ALTER TABLE conversations ADD COLUMN display_name TEXT;
```

---

**Last Updated**: 2025-12-29
**Next Review**: After Phase 1 implementation
