# Claude Code Observability Plan

## Current State

**The Gap**: Claude Code CLI sessions completely bypass the LLM router's metrics infrastructure.

```
Dashboard Chat → LLM Router → Providers → ✅ Metrics (SQLite + Prometheus + Dashboard)
Claude Code CLI → Anthropic API directly → ❌ No metrics
Ralph Wiggum → Claude Code CLI → Anthropic API → ❌ No metrics
```

**Constraints**:
- Claude Code CLI has **no custom endpoint support** (OAuth-based, always hits Anthropic)
- Token usage is visible in CLI output but not captured anywhere
- Ralph Wiggum logs to files but doesn't emit structured metrics

## Options

### Option 1: Claude Code Hooks (Recommended)

Claude Code has a hooks system that fires shell commands on events. We can use this to post metrics.

**How it works**:
```json
// ~/.claude/settings.json in claude-harness container
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          "curl -X POST http://llm-router:8013/metrics/harness -d '{\"event\": \"tool_use\", \"tool\": \"$TOOL_NAME\"}'"
        ]
      }
    ],
    "Stop": [
      {
        "matcher": ".*",
        "hooks": [
          "/usr/local/bin/emit-session-metrics.sh"
        ]
      }
    ]
  }
}
```

**Pros**:
- Native to Claude Code, no wrappers needed
- Fires on actual events (tool use, stop, errors)
- Can capture granular data

**Cons**:
- Limited to what Claude Code exposes via hooks
- Need to parse environment variables for context
- Hook script needs to be robust (non-blocking, error-tolerant)

**Implementation**:
1. Create metrics emission script (`/usr/local/bin/emit-session-metrics.sh`)
2. Add script to claude-harness entrypoint
3. Configure hooks in settings.json
4. Add `/metrics/harness` endpoint to LLM router

---

### Option 2: FastAPI Middleware in claude-harness

Add middleware to the existing FastAPI wrapper (`main.py`) to capture metrics.

**How it works**:
```python
# In main.py - add middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    if request.url.path in ["/v1/chat/completions", "/v1/jobs"]:
        await post_metrics_to_router(
            endpoint=request.url.path,
            duration_ms=duration * 1000,
            model="claude-code",
            project=request.headers.get("X-Project"),
            session_id=request.headers.get("X-Session-ID"),
        )
    return response
```

**Pros**:
- Captures all requests through the harness API
- Can enforce X-Project headers for tracking
- Easy to implement (already have FastAPI)

**Cons**:
- Only captures requests through the API (not direct CLI usage)
- Ralph Wiggum uses CLI directly, not the API
- Token counts not available (Claude CLI doesn't expose them)

**Implementation**:
1. Add middleware to `main.py`
2. Create metrics posting function
3. Add new dashboard section for harness metrics

---

### Option 3: Modify ralph-wiggum.sh

Add metrics emission directly in the Ralph Wiggum script.

**How it works**:
```bash
# Before Claude call
task_start=$(date +%s)
emit_metric "ralph_task_started" "$task_id" "$label"

# Claude call
result=$(claude -p "$prompt" 2>&1)
exit_code=$?

# After Claude call
task_end=$(date +%s)
duration=$((task_end - task_start))
emit_metric "ralph_task_completed" "$task_id" "$label" "$duration" "$exit_code"

# Parse any token info from output
tokens=$(echo "$result" | grep -oP 'tokens?: \K\d+' || echo "0")
```

**Pros**:
- Captures all Ralph sessions (which is the main use case)
- Can track task-level metrics (success rate, duration per task)
- No changes to Claude Code itself

**Cons**:
- Only captures Ralph usage (not interactive CLI sessions)
- Token parsing is fragile (depends on output format)
- More complex bash script

**Implementation**:
1. Add `emit_metric()` function to ralph-wiggum.sh
2. Add metrics calls around Claude invocations
3. Create metrics collection endpoint
4. Add dashboard panel for Ralph metrics

---

### Option 4: Session Metadata from Harness

Track session metadata at start/stop without token-level detail.

**How it works**:
```python
# In main.py - track sessions
sessions_db = {}

async def track_session_start(job_id: str, model: str, project: str):
    sessions_db[job_id] = {
        "started_at": datetime.utcnow(),
        "model": model,
        "project": project,
        "status": "running"
    }

async def track_session_end(job_id: str, success: bool):
    session = sessions_db.get(job_id)
    if session:
        duration = datetime.utcnow() - session["started_at"]
        await post_to_router({
            "type": "harness_session",
            "duration_ms": duration.total_seconds() * 1000,
            "success": success,
            "project": session["project"]
        })
```

**Pros**:
- Simple to implement
- Tracks session duration and success rate
- No parsing needed

**Cons**:
- No token-level metrics
- No tool usage detail
- Coarse-grained data

---

### Option 5: Hybrid Approach (Recommended Overall)

Combine multiple approaches for comprehensive coverage.

**Components**:

1. **Claude Code Hooks** → Capture tool usage, session duration
2. **FastAPI Middleware** → Capture API requests with timing
3. **Ralph Metrics** → Task-level success/failure rates
4. **New LLM Router Endpoint** → `/metrics/harness` for all harness data

**Data Model**:
```sql
-- New table in LLM router SQLite
CREATE TABLE harness_sessions (
    id TEXT PRIMARY KEY,
    source TEXT,           -- 'api', 'ralph', 'interactive'
    project TEXT,
    label TEXT,            -- Ralph label (if applicable)
    task_id TEXT,          -- Beads task ID (if applicable)
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    success BOOLEAN,
    tool_calls_count INTEGER,
    error TEXT
);
```

**Dashboard Integration**:
- Add "Claude Code Sessions" panel
- Show sessions by project/label
- Track Ralph task completion rate
- Display daily Claude Code usage alongside LLM router usage

---

## Recommended Implementation Path

### Phase 1: Ralph Metrics (Quick Win)

1. Add metrics emission to `ralph-wiggum.sh`
2. Create `/metrics/harness` endpoint in LLM router
3. Add dashboard panel for Ralph status

**Effort**: Low
**Coverage**: Ralph sessions only
**Value**: High (Ralph is primary use case)

### Phase 2: FastAPI Middleware

1. Add middleware to `main.py`
2. Enforce X-Project headers
3. Post to `/metrics/harness`

**Effort**: Low
**Coverage**: API usage through harness
**Value**: Medium

### Phase 3: Claude Code Hooks

1. Research hook events and environment variables
2. Create metrics emission script
3. Configure hooks in settings.json
4. Handle hook failures gracefully

**Effort**: Medium
**Coverage**: All Claude Code usage (including interactive)
**Value**: High (most complete)

### Phase 4: Dashboard Integration

1. Add harness_sessions table
2. Create dashboard components
3. Unified view of all Claude usage

**Effort**: Medium
**Coverage**: N/A (visualization)
**Value**: High (user-facing)

---

## Quick Start: Phase 1 Implementation

### 1. Add to ralph-wiggum.sh

```bash
# Add near top of file
METRICS_ENDPOINT="${METRICS_ENDPOINT:-http://llm-router:8013/metrics/harness}"

emit_metric() {
    local event_type="$1"
    local task_id="$2"
    local label="$3"
    local duration="${4:-0}"
    local success="${5:-true}"

    curl -sf -X POST "$METRICS_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "{
            \"source\": \"ralph\",
            \"event\": \"$event_type\",
            \"task_id\": \"$task_id\",
            \"label\": \"$label\",
            \"duration_ms\": $duration,
            \"success\": $success,
            \"timestamp\": \"$(date -Iseconds)\"
        }" 2>/dev/null || true  # Don't fail on metrics error
}
```

### 2. Add endpoint to LLM router

```python
# In router.py
@app.post("/metrics/harness")
async def log_harness_metric(request: Request):
    data = await request.json()
    # Store in SQLite
    await store_harness_metric(data)
    return {"status": "ok"}
```

### 3. Dashboard panel

Add a "Harness Activity" section showing:
- Tasks processed today
- Success rate
- Active Ralph instances
- Recent sessions

---

## Questions to Decide

1. **Scope**: Track all Claude Code usage, or just Ralph/API?
2. **Granularity**: Session-level only, or tool-use level?
3. **Token estimation**: Attempt to parse tokens from output, or accept coarse data?
4. **Alerts**: Add alerting for Ralph failures?
5. **Retention**: How long to keep harness metrics?

---

## Files to Modify

| File | Change |
|------|--------|
| `claude-harness/ralph-wiggum.sh` | Add `emit_metric()` calls |
| `claude-harness/main.py` | Add middleware, session tracking |
| `claude-harness/entrypoint.sh` | Add hooks configuration |
| `llm-router/router.py` | Add `/metrics/harness` endpoint |
| `llm-router/database.py` | Add `harness_sessions` table |
| `llm-router/metrics.py` | Add harness metrics queries |
| `dashboard/src/components/` | Add harness dashboard panel |
| `dashboard/src/api/client.ts` | Add harness API methods |
