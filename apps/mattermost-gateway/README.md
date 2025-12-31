# Mattermost Gateway

HTTP gateway service that allows any service to interact with Mattermost through registered bot identities.

## Access

- **Internal URL**: http://mattermost-gateway:8000 (Docker network)
- **Local Port**: 8010
- **Status**: Active

## Quick Start

1. Create a bot account in Mattermost (System Console > Integrations > Bot Accounts)
2. Generate a Personal Access Token for the bot
3. Copy `.env.example` to `.env` and add the token
4. Deploy with docker-compose

## API Endpoints

### POST /post
Post a message as a specific bot.

```bash
curl -X POST http://mattermost-gateway:8000/post \
  -H "Content-Type: application/json" \
  -d '{
    "bot": "tayne",
    "channel": "general",
    "message": "Hello from the gateway!"
  }'
```

### POST /react
Add a reaction to a message.

```bash
curl -X POST http://mattermost-gateway:8000/react \
  -H "Content-Type: application/json" \
  -d '{
    "bot": "tayne",
    "post_id": "abc123",
    "emoji": "thumbsup"
  }'
```

### GET /messages
Fetch messages from a channel.

```bash
curl "http://mattermost-gateway:8000/messages?channel=general&limit=10"
```

### POST /webhook/:bot
Simple webhook endpoint for posting text (for scripts/cron jobs).

```bash
curl -X POST http://mattermost-gateway:8000/webhook/server-monitor \
  -H "X-Channel: alerts" \
  -d "Backup completed successfully"
```

### GET /health
Health check endpoint.

```bash
curl http://mattermost-gateway:8000/health
```

## Tayne Bot (AI-Powered Responses)

Tayne is an AI-powered bot that responds when @mentioned in Mattermost. It uses the local-ai-router for LLM responses with a surreal, absurdist personality.

### Setup

1. Create Tayne bot account in Mattermost (see below)
2. Add `MATTERMOST_BOT_TAYNE_TOKEN` to `.env`
3. Add `LOCAL_AI_URL` and `LOCAL_AI_API_KEY` to `.env`
4. Create an Outgoing Webhook in Mattermost:
   - Go to: Integrations > Outgoing Webhooks > Add
   - Title: `Tayne Bot`
   - Trigger Words: `@tayne`
   - Callback URL: `http://mattermost-gateway:8000/webhook/tayne/mention`
   - Channel: (leave blank for all channels, or select specific)

### Endpoints

**POST /webhook/tayne/mention** - Mattermost Outgoing Webhook handler
- Receives form-encoded data from Mattermost when @tayne is mentioned
- Queries local-ai-router with Tayne persona
- Returns JSON response that Mattermost posts to the channel

**GET /webhook/tayne/health** - Tayne health check
```bash
curl http://mattermost-gateway:8000/webhook/tayne/health
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOCAL_AI_URL` | `http://local-ai-router:8000` | Local AI Router URL |
| `LOCAL_AI_API_KEY` | (empty) | API key for local-ai-router |

## Bot Registry

| Bot | Purpose | Token Env Var |
|-----|---------|---------------|
| tayne | Personal assistant | MATTERMOST_BOT_TAYNE_TOKEN |
| server-monitor | System alerts | MATTERMOST_BOT_MONITOR_TOKEN |
| trading-bot | Trading notifications | MATTERMOST_BOT_TRADING_TOKEN |

## Creating Bot Accounts in Mattermost

1. Go to System Console > Integrations > Bot Accounts
2. Click "Add Bot Account"
3. Fill in username (e.g., `tayne`)
4. Set role to "Member" (or "System Admin" if needed)
5. Click "Create Bot Account"
6. Copy the token and add to your `.env` file

## Usage Examples

### From Python
```python
import requests

requests.post("http://mattermost-gateway:8000/post", json={
    "bot": "server-monitor",
    "channel": "alerts",
    "message": "Disk usage at 85%"
})
```

### From Bash
```bash
curl -s -X POST http://mattermost-gateway:8000/post \
  -H "Content-Type: application/json" \
  -d '{"bot":"server-monitor","channel":"alerts","message":"Backup complete"}'
```

## Architecture

```
Internal Services → Mattermost Gateway → Mattermost Server
   (HTTP POST)         (Bot tokens)        (REST API)
```

## Related

- [Mattermost Hub Strategy](../../agents/plans/mattermost-hub-strategy.md)
- [Gateway Service Plan](../../agents/plans/mattermost-gateway-service.md)
