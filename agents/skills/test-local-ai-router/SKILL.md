---
name: test-local-ai-router
description: Test Local AI Router with memory and metrics tracking
when_to_use: When testing the router, debugging conversations, or verifying memory storage
---

# Test Local AI Router

> **⚠️ MIGRATION NOTICE (January 2025)**
> 
> Source code migrated to [homelab-ai](https://github.com/unarmedpuppy/homelab-ai) repo.
> Deploy via `apps/homelab-ai/docker-compose.yml`. This skill's test commands remain valid.

Test the Local AI Router's chat completions, memory storage, and metrics tracking.

## Quick Reference

See [agents/reference/local-ai-router.md](../../reference/local-ai-router.md) for complete documentation.

## Two Separate Systems

| System | Enabled | Purpose | Requires Headers |
|--------|---------|---------|------------------|
| **Metrics** | ✅ Always | Analytics, usage stats | ❌ No |
| **Memory** | ⚠️ Opt-in | Conversation history, RAG search | ✅ Yes |

## URLs

| Context | URL |
|---------|-----|
| Docker network | `http://local-ai-router:8000` |
| Server localhost | `http://localhost:8012` |
| External (HTTPS) | `https://local-ai-api.server.unarmedpuppy.com` |

## Test Commands

### 1. Simple Request (Metrics Only, No Memory)

```bash
curl -X POST http://localhost:8012/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Hello, how are you?"}]
  }'
```

**Expected Result**:
- ✅ Response from AI model
- ✅ Metrics logged (check `/metrics/dashboard`)
- ❌ NO conversation saved to memory

### 2. Request WITH Memory (Auto-Generated ID)

```bash
curl -X POST http://localhost:8012/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Enable-Memory: true" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Remember this conversation"}]
  }'
```

**Expected Result**:
- ✅ Response from AI model
- ✅ Metrics logged
- ✅ Conversation saved to memory with auto-generated ID
- ✅ Conversation appears in dashboard

### 3. Multi-Turn Conversation (Specific ID)

```bash
# First message
curl -X POST http://localhost:8012/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Conversation-ID: test-conv-$(date +%s)" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "My name is Josh"}]
  }'

# Second message (same conversation)
curl -X POST http://localhost:8012/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Conversation-ID: test-conv-$(date +%s)" \
  -d '{
    "model": "auto",
    "messages": [
      {"role": "user", "content": "My name is Josh"},
      {"role": "assistant", "content": "Hello Josh!"},
      {"role": "user", "content": "What is my name?"}
    ]
  }'
```

**Expected Result**:
- ✅ Both messages saved to same conversation
- ✅ Conversation shows 4 messages total (2 user + 2 assistant)

### 4. Request with Metadata

```bash
curl -X POST http://localhost:8012/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Enable-Memory: true" \
  -H "X-Project: testing" \
  -H "X-User-ID: josh" \
  -H "X-Session-ID: session-123" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Test with metadata"}]
  }'
```

**Expected Result**:
- ✅ Conversation saved with metadata fields populated
- ✅ Can filter by project/user/session in dashboard

### 5. Force to Specific Backend

```bash
# Force to 3090
curl -X POST http://localhost:8012/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Force-Big: true" \
  -H "X-Enable-Memory: true" \
  -d '{
    "model": "big",
    "messages": [{"role": "user", "content": "Complex coding task"}]
  }'
```

## Verification

### Check Metrics Dashboard

```bash
curl http://localhost:8012/metrics/dashboard | jq
```

**Look for**:
- `total_messages` - Should increase after each request
- `top_models` - Shows which models were used
- `activity_chart` - Recent activity

### Check Memory Conversations

```bash
# List all conversations
curl http://localhost:8012/memory/conversations?limit=10 | jq

# Get specific conversation (replace with actual ID)
curl http://localhost:8012/memory/conversations/{conversation_id} | jq

# Check memory stats
curl http://localhost:8012/memory/stats | jq
```

**Look for**:
- `total_conversations` - Should match number of requests with memory headers
- `total_messages` - Should match user + assistant messages
- Conversation `created_at` and `updated_at` timestamps

### Check Dashboard UI

Open: https://local-ai-dashboard.server.unarmedpuppy.com

1. **Dashboard tab** - Shows metrics (total messages, model usage)
2. **Conversations tab** - Shows memory (browsable conversations)
3. **RAG Search tab** - Semantic search across stored conversations

## Troubleshooting

### Conversation Not Appearing in Dashboard

**Problem**: Metrics show increasing message count, but conversation doesn't appear in Conversations tab.

**Cause**: Memory is opt-in. Request was logged to metrics but not saved to memory.

**Fix**: Add memory header:
```bash
-H "X-Enable-Memory: true"
# OR
-H "X-Conversation-ID: your-id"
```

### Invalid Date in Conversation View

**Problem**: Dashboard shows "—" or "Invalid Date" for conversation timestamps.

**Cause**: Date format mismatch or missing timestamp field.

**Fix**: Check API response - should have `timestamp` field (not `created_at`) with ISO 8601 format.

### 404 Error

**Problem**: `{"detail":"Not Found"}`

**Cause**: Wrong endpoint or router not running.

**Fix**:
1. Check router is running: `docker ps | grep local-ai-router`
2. Check logs: `docker logs local-ai-router --tail 50`
3. Verify endpoint exists: `curl http://localhost:8012/health`

### No Response / Timeout

**Problem**: Request hangs or times out.

**Cause**: Backend model not responding or gaming mode blocking 3090.

**Fix**:
1. Check backend health: `curl http://localhost:8012/health | jq`
2. Check gaming mode: `curl http://localhost:8012/gaming-mode`
3. Force to available backend: `-H "X-Force-Big: false"`

## RAG Search

Test semantic search across stored conversations:

```bash
curl -X POST http://localhost:8012/memory/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What did we discuss about Python?",
    "limit": 5,
    "similarity_threshold": 0.3
  }' | jq
```

**Expected Result**:
- Returns conversations semantically similar to query
- Shows similarity scores
- Includes sample messages from each conversation

## Memory Headers Reference

| Header | Purpose | Example |
|--------|---------|---------|
| `X-Enable-Memory: true` | Auto-generate conversation ID | Enable memory storage |
| `X-Conversation-ID: <id>` | Use specific conversation ID | Continue existing conversation |
| `X-Session-ID: <id>` | Group conversations by session | Optional metadata |
| `X-User-ID: <id>` | Associate with user | Optional metadata |
| `X-Project: <name>` | Tag with project name | Optional metadata |

## Related

- [Local AI Router Reference](../../reference/local-ai-router.md) - Quick reference
- [Local AI Router README](../../../apps/local-ai-router/README.md) - Full documentation
- [Local AI Dashboard](../../../apps/local-ai-dashboard/README.md) - Dashboard UI
