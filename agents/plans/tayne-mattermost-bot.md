# Tayne Mattermost Bot Implementation Plan

**Status**: Planning  
**Created**: 2025-12-30  
**Epic**: home-server-xja (Tayne Bot - Multi-Platform Chat Bot)  
**Goal**: Enable Tayne to respond to mentions in Mattermost with the same persona as Discord

## Current State

### What Exists
- `apps/mattermost-gateway/` - HTTP gateway for posting messages as bots
- Tayne bot already registered in gateway config
- `MATTERMOST_BOT_TAYNE_TOKEN` env var placeholder
- Gateway can: post messages, add reactions, fetch messages

### What's Missing
- **Listener** - No way to detect when Tayne is @mentioned
- **Response logic** - No integration with local-ai-router for Tayne persona

## Architecture Options

### Option 1: Outgoing Webhook (Recommended)
Mattermost sends POST to our endpoint when trigger word is used.

```
User @mentions Tayne → Mattermost Outgoing Webhook → Gateway webhook endpoint
                                                            ↓
                                                    Query local-ai-router
                                                            ↓
                                                    Post response via gateway
```

**Pros**: Simple, no persistent connection, uses existing gateway infrastructure  
**Cons**: Requires manual webhook setup in Mattermost admin

### Option 2: WebSocket Listener
Persistent connection listening for all messages.

**Pros**: Real-time, can see all messages  
**Cons**: More complex, needs separate service, connection management

### Option 3: Slash Command
`/tayne <message>` invokes Tayne.

**Pros**: Very simple to implement  
**Cons**: Different UX than Discord (@mention vs slash command)

## Recommended Approach: Outgoing Webhook

### Implementation Steps

#### Phase 1: Gateway Webhook Endpoint
Add new endpoint to mattermost-gateway that:
1. Receives Outgoing Webhook POST from Mattermost
2. Extracts message content and channel
3. Queries local-ai-router with Tayne persona
4. Posts response back to channel

**New endpoint**: `POST /webhook/tayne/mention`

#### Phase 2: Shared Persona Module
Extract Tayne persona from Discord bot for reuse:
- System prompt
- Fallback quotes
- Guardrails
- Rate limiting logic

Options:
1. Copy `tayne_persona.py` to gateway
2. Create shared package
3. Inline the persona in gateway (simplest)

#### Phase 3: Mattermost Configuration
1. Create Tayne bot account (if not exists)
2. Set up Outgoing Webhook:
   - Trigger words: `@tayne`
   - Channel: All channels (or specific)
   - Callback URL: `http://mattermost-gateway:8000/webhook/tayne/mention`

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `apps/mattermost-gateway/gateway/routes/tayne.py` | CREATE | Tayne mention webhook handler |
| `apps/mattermost-gateway/gateway/tayne_persona.py` | CREATE | Tayne persona (copy from Discord) |
| `apps/mattermost-gateway/gateway/main.py` | MODIFY | Add tayne router |
| `apps/mattermost-gateway/requirements.txt` | MODIFY | Add aiohttp for local-ai-router |
| `apps/mattermost-gateway/.env.example` | MODIFY | Add LOCAL_AI_URL, LOCAL_AI_API_KEY |

## Webhook Endpoint Design

### Request (from Mattermost Outgoing Webhook)
```json
{
  "token": "webhook_token",
  "team_id": "...",
  "team_domain": "...",
  "channel_id": "...",
  "channel_name": "general",
  "timestamp": 1234567890,
  "user_id": "...",
  "user_name": "josh",
  "post_id": "...",
  "text": "@tayne can I get a hat wobble?",
  "trigger_word": "@tayne"
}
```

### Response Options

**Option A: Direct Response** (Mattermost handles posting)
```json
{
  "text": "Now Tayne I can get into. Initiating hat wobble sequence...",
  "response_type": "comment"
}
```

**Option B: Async Response** (We post separately)
Return 200 OK immediately, then post via gateway.
Better for slow LLM responses.

## Environment Variables

```bash
# Existing
MATTERMOST_BOT_TAYNE_TOKEN=...

# New
LOCAL_AI_URL=http://local-ai-router:8000
LOCAL_AI_API_KEY=lai_...
TAYNE_WEBHOOK_TOKEN=...  # Optional: validate incoming webhooks
```

## Rate Limiting

Same as Discord:
- Per-user cooldown: 5 seconds
- Rapid-fire detection: 5+ mentions in 60s

## Testing Checklist

- [ ] Webhook endpoint receives Mattermost POST
- [ ] Message parsed correctly
- [ ] Local-ai-router queried with Tayne persona
- [ ] Response posted to correct channel
- [ ] Guardrails trigger fallback quotes
- [ ] Rate limiting works per-user
- [ ] API down triggers satellite message

## Deployment

1. Update mattermost-gateway code
2. Deploy: `docker compose up -d --build`
3. Configure Outgoing Webhook in Mattermost admin
4. Test in a channel

## Tasks

1. [ ] Create tayne.py webhook route
2. [ ] Copy/adapt tayne_persona.py
3. [ ] Add local-ai-router integration
4. [ ] Update gateway main.py and requirements
5. [ ] Configure Mattermost Outgoing Webhook
6. [ ] Test end-to-end
7. [ ] Document in gateway README

## Related

- `apps/discord-reaction-bot/` - Reference implementation
- `apps/mattermost-gateway/` - Gateway service
- `agents/personas/tayne-agent.md` - Tayne persona docs
