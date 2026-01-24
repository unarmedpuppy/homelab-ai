# Shua-Ledger Mattermost Integration Plan

**Goal**: Two-way Mattermost bot for shua-ledger operations using local Qwen 32B model via llm-router.

**Architecture**:
```
User @shua in Mattermost
       │
       ▼
Mattermost Outgoing Webhook
       │
       ▼
n8n Workflow (webhook trigger)
       │
       ▼ (internal docker network only)
llm-router /agent/run
       │
       ├── working_directory: /workspace/shua-ledger
       ├── model: routes to Qwen 32B on Gaming PC
       └── tools: read_file, write_file, edit_file, search_files, etc.
       │
       ▼
Agent executes shua-ledger operations
       │
       ▼
n8n posts response via mattermost-gateway
       │
       ▼
User sees response in Mattermost
```

**Security Model**:
- `/agent/run` blocked externally via Traefik (internal network only)
- Only n8n can call the agent endpoint
- Discord/Mattermost bots unaffected (they use `/v1/chat/completions`)
- shua-ledger data isolated from external access

---

## Phase 1: Infrastructure

### 1.1 Mount shua-ledger in llm-router

**File**: `home-server/apps/homelab-ai/docker-compose.yml`

**Change**: Add claude-workspace volume to llm-router service

```yaml
services:
  llm-router:
    volumes:
      - ./data:/data
      - ../../agents/skills:/app/agents/skills:ro
      - claude-workspace:/workspace:rw  # ADD THIS
```

Also declare the external volume at the bottom:
```yaml
volumes:
  huggingface-cache:
    external: true
  claude-workspace:        # ADD THIS
    external: true
```

**Why**: The agent's file tools need access to `/workspace/shua-ledger` to read/write journal entries, contacts, todos.

**Verification**:
```bash
# SSH to server, exec into llm-router
docker exec llm-router ls /workspace/shua-ledger
# Should see: AGENTS.md, README.md, data/, agents/
```

### 1.2 Block /agent/* Externally (Security)

**File**: `home-server/apps/homelab-ai/docker-compose.yml`

**Change**: Add Traefik middleware to block `/agent/*` paths from external access

```yaml
labels:
  # Existing labels...
  - "traefik.http.routers.llm-router.rule=Host(`homelab-ai-api.server.unarmedpuppy.com`)"

  # ADD: Block /agent/* externally - return 404
  - "traefik.http.routers.llm-router-agent-block.rule=Host(`homelab-ai-api.server.unarmedpuppy.com`) && PathPrefix(`/agent`)"
  - "traefik.http.routers.llm-router-agent-block.entrypoints=websecure"
  - "traefik.http.routers.llm-router-agent-block.priority=100"
  - "traefik.http.routers.llm-router-agent-block.tls.certresolver=myresolver"
  - "traefik.http.routers.llm-router-agent-block.middlewares=agent-block"
  - "traefik.http.middlewares.agent-block.replacepathregex.regex=.*"
  - "traefik.http.middlewares.agent-block.replacepathregex.replacement=/blocked-endpoint"
```

**Why**: Prevents external callers from accessing `/agent/run` with arbitrary `working_directory`. Only internal docker network (n8n) can reach it.

**What still works externally**:
- `/v1/chat/completions` - chat API
- `/health` - health checks
- `/docs` - API documentation
- `/metrics/*` - dashboard metrics

**What's blocked externally**:
- `/agent/run` - agent execution (the dangerous one)
- `/agent/tools` - tool listing

**Note**: `/agent/runs` (GET, read-only history) could remain accessible for dashboard viewing - it only shows metadata, not file contents. Adjust the PathPrefix rule if needed.

**Verification**:
```bash
# External - should fail/404
curl https://homelab-ai-api.server.unarmedpuppy.com/agent/tools

# Internal - should work
docker exec n8n curl http://llm-router:8000/agent/tools
```

---

## Phase 2: Mattermost Webhook Configuration

### 2.1 Create Outgoing Webhook in Mattermost

**Location**: Mattermost System Console → Integrations → Outgoing Webhooks

**Settings**:
- **Title**: Shua-Ledger Bot
- **Description**: Routes messages to shua-ledger agent
- **Channel**: (specific channel, e.g., "shua-ledger" or "journal")
- **Trigger Words**: `@shua`, `@ledger`, `@journal` (pick one or more)
- **Callback URL**: `https://n8n.server.unarmedpuppy.com/webhook/shua-ledger`
- **Content Type**: `application/json`

**Output**: Note the webhook token for n8n validation

**Verification**:
- Type `@shua test` in the channel
- Check n8n execution logs for incoming webhook

### 2.2 Create Mattermost Channel (Optional)

If you want a dedicated channel:
- Create `#shua-ledger` channel in Mattermost
- Configure webhook to only trigger in this channel

---

## Phase 3: n8n Workflow - Interactive Chat

### 3.1 Create Shua-Ledger Webhook Workflow

**Workflow Name**: `Shua-Ledger Mattermost Bot`

**Nodes**:

```
[Webhook Trigger] → [Validate & Parse] → [Call Agent] → [Post Response]
```

#### Node 1: Webhook Trigger
- **Type**: Webhook
- **Path**: `shua-ledger`
- **Method**: POST
- **Response Mode**: Immediately (we'll post async)

#### Node 2: Validate & Parse (Code Node)
```javascript
const body = $input.first().json;

// Extract Mattermost webhook fields
const userId = body.user_id;
const userName = body.user_name;
const channelId = body.channel_id;
const postId = body.post_id;
const text = body.text;
const triggerWord = body.trigger_word;

// Clean message (remove trigger word)
const message = text.replace(new RegExp(triggerWord, 'gi'), '').trim();

// Validate (optional: check webhook token)
if (!message) {
  return [{ json: { skip: true } }];
}

return [{
  json: {
    userId,
    userName,
    channelId,
    postId,
    message,
    triggerWord
  }
}];
```

#### Node 3: Call Agent (HTTP Request)
- **Method**: POST
- **URL**: `http://llm-router:8000/agent/run`
- **Body**:
```json
{
  "task": "{{ $json.message }}",
  "working_directory": "/workspace/shua-ledger",
  "model": "auto",
  "max_steps": 20,
  "source": "mattermost",
  "triggered_by": "{{ $json.userName }}"
}
```
- **Headers**:
  - `Content-Type`: `application/json`
  - `X-Project`: `shua-ledger`

#### Node 4: Format Response (Code Node)
```javascript
const agentResponse = $input.first().json;
const original = $('Validate & Parse').first().json;

let responseText;
if (agentResponse.success) {
  responseText = agentResponse.final_answer || 'Done!';
} else {
  responseText = `Error: ${agentResponse.terminated_reason}`;
}

// Truncate if too long for Mattermost
if (responseText.length > 4000) {
  responseText = responseText.substring(0, 3997) + '...';
}

return [{
  json: {
    bot: 'tayne',
    channel: original.channelId,
    message: responseText,
    thread_id: original.postId
  }
}];
```

#### Node 5: Post Response (HTTP Request)
- **Method**: POST
- **URL**: `http://mattermost-gateway:8000/post`
- **Body**: `{{ JSON.stringify($json) }}`

**Verification**:
```bash
# Test the webhook directly
curl -X POST https://n8n.server.unarmedpuppy.com/webhook/shua-ledger \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","user_name":"joshua","channel_id":"xxx","post_id":"yyy","text":"@shua what did I do yesterday?","trigger_word":"@shua"}'
```

---

## Phase 4: Scheduled Workflows

### 4.1 Morning Briefing Workflow

**Workflow Name**: `Shua-Ledger Morning Briefing`

**Trigger**: Cron - `0 7 * * *` (7:00 AM daily)

**Nodes**:

```
[Cron Trigger] → [Call Agent] → [Post to Mattermost]
```

#### Agent Task:
```
Generate my morning briefing for today. Follow the morning-briefing skill in /workspace/shua-ledger/agents/skills/morning-briefing/
```

#### Post to Channel:
- Channel: `town-square` or dedicated `#daily` channel
- Bot: `tayne`

### 4.2 Weekly Summary Workflow

**Workflow Name**: `Shua-Ledger Weekly Summary`

**Trigger**: Cron - `0 18 0 * * 0` (6:00 PM Sunday)

**Nodes**: Same pattern as morning briefing

#### Agent Task:
```
Generate my weekly summary. Follow the weekly-summary skill in /workspace/shua-ledger/agents/skills/weekly-summary/
```

---

## Phase 5: Agent System Prompt (Optional Enhancement)

### 5.1 Shua-Ledger Specific System Prompt

The current agent system prompt is generic. For better shua-ledger integration, we could add a custom system prompt option.

**Option A**: Use the task field to include context
```json
{
  "task": "You are Tayne, a personal assistant for Joshua's shua-ledger knowledge base. The user says: 'what did I do yesterday?' - Find and summarize yesterday's journal entry.",
  "working_directory": "/workspace/shua-ledger"
}
```

**Option B**: Add system_prompt field to AgentRequest (requires code change)

For now, Option A should work - the agent will search for skills and follow them.

---

## Phase 6: Testing & Validation

### 6.1 Unit Tests

1. **Volume mount test**:
   ```bash
   docker exec llm-router cat /workspace/shua-ledger/AGENTS.md | head -5
   ```

2. **Agent endpoint test**:
   ```bash
   curl -X POST http://localhost:8012/agent/run \
     -H "Content-Type: application/json" \
     -d '{
       "task": "List the files in /workspace/shua-ledger/data/journal/2026/01/",
       "working_directory": "/workspace/shua-ledger",
       "max_steps": 5
     }'
   ```

3. **Mattermost webhook test**: Trigger word in channel → check n8n logs

4. **Full flow test**: `@shua log: had coffee with Sarah` → verify journal updated

### 6.2 Integration Tests

1. **Journal entry**: `@shua log: tested the new bot integration`
2. **Contact update**: `@shua talked to Mom about weekend plans`
3. **Todo add**: `@shua remind me to review weekly summary tomorrow`
4. **Query**: `@shua when did I last see John?`
5. **Morning briefing**: Manually trigger cron, verify post appears

---

## Implementation Order

| Step | Component | Effort | Dependencies |
|------|-----------|--------|--------------|
| 1a | Mount shua-ledger volume in llm-router | Low | None |
| 1b | Block `/agent/run` externally (Traefik) | Low | None |
| 2 | Deploy llm-router changes, verify security | Low | Step 1a, 1b |
| 3 | Test agent can access shua-ledger files (internal) | Low | Step 2 |
| 4 | Create Mattermost outgoing webhook | Low | None |
| 5 | Create n8n interactive workflow | Medium | Steps 3, 4 |
| 6 | Test full interactive flow | Low | Step 5 |
| 7 | Create morning briefing workflow | Low | Step 5 |
| 8 | Create weekly summary workflow | Low | Step 5 |
| 9 | End-to-end testing | Medium | Steps 6-8 |

**Estimated Total Effort**: 2-3 hours

---

## Rollback Plan

If issues arise:
1. Remove volume mount and Traefik block labels from llm-router → redeploy
2. Disable Mattermost webhook in Mattermost settings
3. Deactivate n8n workflows

No data loss risk - all changes are additive.

---

## Future Enhancements

1. **Dedicated Mattermost bot** - Create `shua` bot instead of using Tayne
2. **Typing indicators** - Show "Shua is typing..." while agent runs
3. **Slash commands** - `/journal`, `/todo`, `/briefing` in Mattermost
4. **Image support** - Attach photos from Immich to events
5. **Voice notes** - TTS for morning briefing audio
