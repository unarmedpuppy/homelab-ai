# Local AI Router Reference

Quick reference for the Local AI Router's metrics and memory systems.

## Full Documentation

See [apps/local-ai-router/README.md](../../apps/local-ai-router/README.md) for complete documentation.

## Quick Facts

**Two Separate Systems:**

| System | Enabled | Purpose | Requires Headers |
|--------|---------|---------|------------------|
| **Metrics** | ✅ Always | Analytics, usage stats | ❌ No |
| **Memory** | ⚠️ Opt-in | Conversation history, RAG search | ✅ Yes |

## Key Discovery

**Problem**: Metrics showed message count increasing, but conversations weren't appearing in the dashboard.

**Root Cause**: The router has two separate databases:
1. **Metrics DB** - Logs all requests automatically (no headers needed)
2. **Memory DB** - Only saves when explicitly requested via headers

**Solution**: Add `X-Enable-Memory: true` header to save conversations to memory.

## Memory Headers

To save a conversation to memory, use these headers:

### Required Headers

```bash
# Enable memory storage
X-Enable-Memory: true

# Identify the user making the request
X-User-ID: user-123
```

**⚠️ IMPORTANT**: `X-User-ID` is currently **optional but strongly recommended**. It should be **required** in the future for proper user tracking (see task for enforcement).

### Optional Headers

```bash
# Use specific conversation ID (auto-generated if omitted)
X-Conversation-ID: my-conversation-123

# Project/application identifier (e.g., "dashboard", "tayne-discord-bot")
X-Project: my-project

# Session identifier for grouping related conversations
X-Session-ID: session-abc
```

### Header Details

| Header | Status | Purpose | Example Values | Notes |
|--------|--------|---------|----------------|-------|
| `X-Enable-Memory` | **Required** | Enable conversation storage | `true` | Without this, conversation is NOT saved |
| `X-User-ID` | **Recommended** | User identifier | `user-123`, Discord user ID, email | Should be unique per user. Currently optional but will be required. |
| `X-Project` | Optional | Application/source identifier | `dashboard`, `tayne-discord-bot`, `testing` | Used for filtering and source badges in UI |
| `X-Conversation-ID` | Optional | Specific conversation ID | `conv-abc-123`, `discord-{channel_id}` | Auto-generated if omitted |
| `X-Session-ID` | Optional | Session grouping | `session-abc` | Rarely used |

### Implementation Examples

**Discord Bot**:
```python
headers = {
    "Content-Type": "application/json",
    "X-Enable-Memory": "true",
    "X-Conversation-ID": f"discord-{channel_id}",  # One conversation per channel
    "X-Project": "tayne-discord-bot",
    "X-User-ID": str(message.author.id),  # Discord user ID
}
```

**Dashboard/Web App**:
```typescript
const headers = {
  'Content-Type': 'application/json',
  'X-Enable-Memory': 'true',
  'X-Project': 'dashboard',
  'X-User-ID': 'dashboard-user',  // Or actual logged-in user ID
  'X-Conversation-ID': conversationId || undefined,  // Omit for new conversations
};
```

**CLI/Script**:
```bash
curl -X POST http://localhost:8012/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Enable-Memory: true" \
  -H "X-User-ID: josh" \
  -H "X-Project: testing" \
  -d '{"model": "auto", "messages": [...]}'
```

### Best Practices

1. **Always provide X-User-ID** when using memory to enable proper user tracking
2. **Use stable identifiers** for X-User-ID (database IDs, Discord IDs, emails) - not display names
3. **Use descriptive X-Project values** to identify the source application (shows in dashboard badges)
4. **Let X-Conversation-ID auto-generate** for new conversations unless you need specific ID format
5. **Reuse X-Conversation-ID** for multi-turn conversations in the same context (e.g., same Discord channel)

## API Endpoints

```bash
# Chat completion (no memory)
curl -X POST http://localhost:8012/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "auto", "messages": [{"role": "user", "content": "Hello"}]}'

# Chat completion WITH memory
curl -X POST http://localhost:8012/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Enable-Memory: true" \
  -d '{"model": "auto", "messages": [{"role": "user", "content": "Hello"}]}'

# List conversations (memory)
curl http://localhost:8012/memory/conversations?limit=10

# Get conversation details
curl http://localhost:8012/memory/conversations/{id}

# Memory statistics
curl http://localhost:8012/memory/stats

# Dashboard metrics
curl http://localhost:8012/metrics/dashboard
```

## URLs

| Context | URL |
|---------|-----|
| Docker network | `http://local-ai-router:8000` |
| Server localhost | `http://localhost:8012` |
| External (HTTPS) | `https://local-ai-api.server.unarmedpuppy.com` |

## API Key Management

Manage client API keys for authenticating requests to the Local AI Router.

**Location:** `apps/local-ai-router/scripts/manage-api-keys.py`

**Key Format:** `lai_{32_hex_chars}` (e.g., `lai_5f4d3c2b1a9e8d7c6b5a4e3d2c1b0a9f`)

### CLI Commands

```bash
cd apps/local-ai-router

# Create a new API key
python scripts/manage-api-keys.py create "agent-1"

# Create with expiration (90 days)
python scripts/manage-api-keys.py create "temp-key" --expires-in-days 90

# Create with scopes
python scripts/manage-api-keys.py create "chat-only" --scopes chat,models

# List active keys
python scripts/manage-api-keys.py list

# List all keys (including disabled)
python scripts/manage-api-keys.py list --all

# Show key details
python scripts/manage-api-keys.py show <id>

# Disable a key (soft delete)
python scripts/manage-api-keys.py disable <id>

# Re-enable a key
python scripts/manage-api-keys.py enable <id>

# Permanently delete a key
python scripts/manage-api-keys.py delete <id>
python scripts/manage-api-keys.py delete <id> --force  # Skip confirmation
```

### Security Notes

- Keys are stored as SHA-256 hashes - the full key is only shown once at creation
- Store keys securely after creation - they cannot be retrieved later
- Use `disable` instead of `delete` to preserve audit trail
- Keys can have optional expiration dates and scopes

### Database Table

Keys are stored in the `client_api_keys` table:
- `key_hash` - SHA-256 hash for validation
- `key_prefix` - First 8 chars for display (e.g., "lai_5f4d")
- `name` - Human-readable identifier
- `enabled` - Active/inactive status
- `scopes` - Optional JSON array of allowed scopes
- `expires_at` - Optional expiration timestamp

## Dashboard

Access at: [https://local-ai-dashboard.server.unarmedpuppy.com](https://local-ai-dashboard.server.unarmedpuppy.com)

**Tabs:**
- **Dashboard** - Shows metrics (total messages, model usage, activity)
- **Conversations** - Shows memory (browsable conversation history)
- **RAG Search** - Semantic search across stored conversations

## Why Two Systems?

- **Privacy** - Not all API calls should be permanently stored
- **Control** - Clients explicitly opt-in to conversation storage
- **Performance** - Metrics are lightweight, memory is verbose
- **Separation** - Analytics vs. conversation history

## Common Use Cases

### Just Analytics (No Conversation Storage)
```bash
# Default behavior - metrics logged, no memory saved
curl -X POST http://localhost:8012/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "auto", "messages": [{"role": "user", "content": "Quick question"}]}'
```

### Conversation with Memory
```bash
# Save to memory for later retrieval or RAG search
curl -X POST http://localhost:8012/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Enable-Memory: true" \
  -H "X-Project: my-app" \
  -d '{"model": "auto", "messages": [{"role": "user", "content": "Start conversation"}]}'
```

### Multi-Turn Conversation
```bash
# First message
curl -X POST http://localhost:8012/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Conversation-ID: conv-abc-123" \
  -d '{"model": "auto", "messages": [{"role": "user", "content": "My name is Josh"}]}'

# Second message (same conversation)
curl -X POST http://localhost:8012/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Conversation-ID: conv-abc-123" \
  -d '{"model": "auto", "messages": [
    {"role": "user", "content": "My name is Josh"},
    {"role": "assistant", "content": "Hello Josh!"},
    {"role": "user", "content": "What is my name?"}
  ]}'
```

## Related

- [Local AI Router README](../../apps/local-ai-router/README.md) - Full documentation
- [Local AI Dashboard](../../apps/local-ai-dashboard/README.md) - Dashboard UI
- [Skill: Test Local AI Router](../skills/test-local-ai-router/SKILL.md) - Testing tool
