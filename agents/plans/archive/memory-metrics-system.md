# Memory & Metrics System for Local AI Router

**Status**: In Progress
**Created**: 2025-12-28
**Related**: [Local AI Unified Architecture](local-ai-unified-architecture.md)

## Vision

A unified data layer that provides both:
1. **Long-term Agent Memory** - Full conversation history for recall, RAG, and context continuity
2. **Usage Metrics & Analytics** - Dashboard-ready data for visualizing usage patterns (OpenCode Wrapped style)

## Goals

- Store complete conversation history with metadata
- Enable agent recall and RAG capabilities
- Collect metrics for dashboard visualization (activity charts, model usage, token stats, streaks)
- Maintain OpenAI API compatibility
- Support both stateless and stateful modes
- Minimal performance impact on routing

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Request                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 FastAPI Middleware                           │
│  • Capture request metadata                                 │
│  • Assign conversation/session IDs                          │
│  • Log to database                                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Router Logic                               │
│  • Check for conversation_id (stateful mode)                │
│  • RAG retrieval if enabled                                 │
│  • Route to backend                                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend (3070/3090/OpenCode)                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Response Middleware                             │
│  • Store response in database                               │
│  • Update metrics                                           │
│  • Calculate token usage                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Client Response                          │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

### SQLite Database: `/data/local-ai-router.db`

**Table: conversations**
```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,              -- UUID
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    session_id TEXT,                  -- Optional grouping (e.g., n8n workflow run)
    user_id TEXT,                     -- Optional user identifier
    project TEXT,                     -- Optional project tag
    title TEXT,                       -- Optional conversation title
    metadata JSON,                    -- Additional metadata (tags, context, etc.)
    message_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0
);
```

**Table: messages**
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    role TEXT NOT NULL,               -- user, assistant, system, tool
    content TEXT,                     -- Message content
    model_used TEXT,                  -- Actual model used (backend)
    backend TEXT,                     -- 3070, 3090, opencode-glm, opencode-claude
    tokens_prompt INTEGER,
    tokens_completion INTEGER,
    tool_calls JSON,                  -- Tool calls made (if any)
    tool_results JSON,                -- Tool results (if any)
    metadata JSON,                    -- Additional metadata
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);
```

**Table: metrics**
```sql
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    date DATE NOT NULL,               -- For daily aggregation
    conversation_id TEXT,
    session_id TEXT,
    endpoint TEXT,                    -- /v1/chat/completions, /agent/run, etc.
    model_requested TEXT,             -- Model requested by client
    model_used TEXT,                  -- Actual model used
    backend TEXT,                     -- Backend that handled request
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    duration_ms INTEGER,              -- Request duration
    success BOOLEAN,
    error TEXT,
    streaming BOOLEAN,
    tool_calls_count INTEGER,
    user_id TEXT,
    project TEXT,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

CREATE INDEX idx_metrics_date ON metrics(date);
CREATE INDEX idx_metrics_timestamp ON metrics(timestamp);
CREATE INDEX idx_metrics_backend ON metrics(backend);
CREATE INDEX idx_metrics_user_project ON metrics(user_id, project);
```

**Table: daily_stats** (Materialized aggregation)
```sql
CREATE TABLE daily_stats (
    date DATE PRIMARY KEY,
    total_requests INTEGER,
    total_messages INTEGER,
    total_tokens INTEGER,
    unique_conversations INTEGER,
    unique_sessions INTEGER,
    models_used JSON,                 -- {"3090": 42, "3070": 18, ...}
    backends_used JSON,
    avg_duration_ms REAL,
    success_rate REAL,
    updated_at DATETIME
);
```

## API Modes

### Mode 1: Stateless (Current Behavior)
```bash
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```
- Metrics logged to database
- No conversation memory (one-shot)
- Fully compatible with existing clients

### Mode 2: Stateful (Conversation Memory)
```bash
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Conversation-ID: conv-abc123" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Continue our discussion"}]
  }'
```
- Full conversation history stored
- Messages linked to conversation ID
- Client controls conversation lifecycle

### Mode 3: Auto-Recall (RAG)
```bash
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Enable-Memory: true" \
  -H "X-User-ID: user123" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "What did we discuss last week about trading?"}]
  }'
```
- Search past conversations via embedding similarity
- Inject relevant context into prompt
- Automatic memory retrieval

## Implementation Phases

### Phase 1: Database Foundation ✅ COMPLETE
- [x] Create database schema (`database.py`)
- [x] Create Pydantic models (`models.py`)
- [x] Database initialization and migration
- [x] Add `data/` directory to `.gitignore` (already covered by `apps/*/data/*`)
- [x] Test database initialization locally
- [x] Commit to git

### Phase 2: Memory Module ✅ COMPLETE
- [x] Create `memory.py` with conversation storage/retrieval
- [x] Implement conversation CRUD operations
- [x] Message storage with metadata
- [x] Conversation search and retrieval
- [x] Conversation statistics and helper functions
- [x] Test all CRUD operations
- [x] Fix datetime deprecation warnings

### Phase 3: Metrics Module ✅ COMPLETE
- [x] Create `metrics.py` for metrics logging
- [x] Implement metrics aggregation queries
- [x] Daily stats materialization
- [x] Dashboard data functions (GitHub charts, model usage, streaks)
- [x] Provider distribution and cost calculations
- [x] Test metrics logging and dashboard generation

### Phase 4: Middleware Integration ✅ COMPLETE
- [x] Request capture with FastAPI dependency injection
- [x] Response logging via BackgroundTasks
- [x] Token usage calculation from response
- [x] Error tracking
- [x] Header-based configuration (conversation ID, session ID, user ID, project)
- [x] Auto-conversation creation with X-Enable-Memory header
- [x] Backend inference from model names
- [x] Duration tracking
- [x] Database persistence with mounted volume

**Implementation**: Replaced BaseHTTPMiddleware with dependency injection (`dependencies.py`) to avoid request body consumption issues. Logging happens in background tasks after response is sent, with no performance impact on request latency.

**Files**:
- `dependencies.py` - RequestTracker dependency and log_chat_completion function
- `router.py` - Updated to use Depends() and BackgroundTasks
- `docker-compose.yml` - Added volume mount for database persistence

**Verified Working**:
- ✅ Metrics logging to SQLite
- ✅ Conversation memory with X-Conversation-ID header
- ✅ Auto-conversation creation with X-Enable-Memory header
- ✅ Database persists across container restarts
- ✅ Dashboard stats available via `get_dashboard_stats()`

**Known Limitations**:
- Streaming responses are not logged (TODO for future enhancement)
- Client must manage conversation history (router is stateless)

### Phase 5: API Endpoints
- [ ] Memory endpoints (`/memory/*`)
  - `GET /memory/conversations` - List conversations
  - `GET /memory/conversations/{id}` - Get conversation
  - `POST /memory/conversations` - Create conversation
  - `DELETE /memory/conversations/{id}` - Delete conversation
  - `GET /memory/search` - Search conversations
- [ ] Metrics endpoints (`/metrics/*`)
  - `GET /metrics/daily` - Daily stats
  - `GET /metrics/models` - Model usage breakdown
  - `GET /metrics/activity` - GitHub-style activity chart
  - `GET /metrics/dashboard` - Dashboard summary

### Phase 6: RAG Integration
- [ ] Embedding generation for messages
- [ ] Vector storage (SQLite with sqlite-vec or external)
- [ ] Similarity search
- [ ] Context injection logic

### Phase 7: Testing & Deployment
- [ ] Unit tests for database operations
- [ ] Integration tests for middleware
- [ ] Performance benchmarks
- [ ] Update Dockerfile for data persistence
- [ ] Update docker-compose.yml with volume mount
- [ ] Deploy to server
- [ ] Create dashboard UI (separate app)

## Configuration

### Environment Variables
```bash
# Database
DATABASE_PATH=/data/local-ai-router.db
ENABLE_MEMORY=1  # 0 or 1
ENABLE_METRICS=1  # 0 or 1

# Metrics (future)
METRICS_BATCH_SIZE=100
DAILY_STATS_UPDATE_INTERVAL=3600  # 1 hour

# RAG (future)
ENABLE_RAG=false
RAG_CONTEXT_LIMIT=3  # Max conversations to inject
RAG_SIMILARITY_THRESHOLD=0.7
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Docker Volume Mount
```yaml
services:
  local-ai-router:
    volumes:
      - ./data:/data  # Persist database to host
    environment:
      - ENABLE_MEMORY=1
      - ENABLE_METRICS=1
```

## Dashboard Metrics (OpenCode Wrapped Style)

The metrics system will support these dashboard elements:

1. **Started Date** - First conversation date
2. **Days Active** - Unique dates with activity
3. **Most Active Day** - Date with most requests
4. **GitHub Contribution Chart** - Daily activity heatmap
5. **Top Models Used** - Bar chart (3090: 42%, 3070: 30%, GLM: 18%, Claude: 10%)
6. **Providers Used** - Pie chart (Local: 72%, OpenCode: 28%)
7. **Sessions** - Unique session count
8. **Messages** - Total message count
9. **Total Tokens** - Sum of all tokens (prompt + completion)
10. **Projects** - Unique project count
11. **Streak** - Longest consecutive days active
12. **Cost Savings** - OpenCode Zen cost vs API pricing

### Dashboard Query Examples

**GitHub-style activity chart:**
```sql
SELECT date, total_requests
FROM daily_stats
WHERE date >= DATE('now', '-365 days')
ORDER BY date;
```

**Top models:**
```sql
SELECT model_used, COUNT(*) as count, SUM(total_tokens) as tokens
FROM metrics
GROUP BY model_used
ORDER BY count DESC
LIMIT 5;
```

**Streak calculation:**
```sql
WITH daily_activity AS (
  SELECT DISTINCT date FROM metrics ORDER BY date
),
gaps AS (
  SELECT
    date,
    LAG(date) OVER (ORDER BY date) as prev_date,
    JULIANDAY(date) - JULIANDAY(LAG(date) OVER (ORDER BY date)) as gap
  FROM daily_activity
)
SELECT MAX(streak) as longest_streak
FROM (
  SELECT
    SUM(CASE WHEN gap = 1 THEN 1 ELSE 0 END) + 1 as streak
  FROM gaps
);
```

## Memory Retrieval Examples

### Simple Conversation Recall
```python
# Get full conversation history
GET /memory/conversations/conv-abc123
→ Returns all messages with metadata
```

### Search by Content
```python
# Find conversations about "trading"
GET /memory/search?q=trading&user_id=user123&limit=5
→ Returns top 5 relevant conversations
```

### RAG-enhanced Query
```python
# Automatic context injection
POST /v1/chat/completions
X-Enable-Memory: true
X-User-ID: user123

{
  "messages": [
    {"role": "user", "content": "What was that trading strategy we discussed?"}
  ]
}

# Router:
# 1. Searches past conversations for "trading strategy"
# 2. Finds relevant context from 3 days ago
# 3. Injects into system message:
#    "Previous conversation context:
#     On 2025-12-25, you discussed a momentum trading strategy with..."
# 4. Sends to backend with enhanced context
```

## Security & Privacy

- Database file permissions: `600` (owner read/write only)
- No PII storage by default (user controls user_id)
- Optional conversation encryption (future)
- Retention policies (auto-delete old conversations)
- Export/delete endpoints for GDPR compliance

## Performance Considerations

- SQLite with WAL mode for concurrent reads
- Connection pooling
- Async database operations
- Batch metric writes (every N requests or M seconds)
- Materialized daily stats (updated hourly)
- Index optimization for common queries

## Migration Path

1. **Week 1**: Deploy Phase 1-4 (database + metrics logging)
2. **Week 2**: Deploy Phase 5 (API endpoints for metrics dashboard)
3. **Week 3**: Build dashboard UI
4. **Week 4**: Deploy Phase 6 (RAG) if needed

## Success Metrics

- [ ] All requests logged to database
- [ ] Dashboard shows accurate metrics
- [ ] Conversation recall working
- [ ] <5ms overhead per request (p99)
- [ ] No errors in production logs
- [ ] Database size <1GB after 1 month

## Related Documents

- [Local AI Unified Architecture](local-ai-unified-architecture.md)
- [Local AI Router README](../../apps/local-ai-router/README.md)
- [Local AI Router Usage Reference](../reference/local-ai-router-usage.md)

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-28 | SQLite for initial implementation | Simple, no external dependencies, good for single-server |
| 2025-12-28 | Unified schema for memory + metrics | Single source of truth, avoid duplication |
| 2025-12-28 | Header-based mode selection | Backward compatible, explicit control |
| 2025-12-28 | Materialized daily stats | Performance - avoid complex aggregations on every dashboard load |
