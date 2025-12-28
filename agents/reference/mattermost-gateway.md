# Mattermost Gateway Reference

**Service**: `mattermost-gateway`
**Location**: `apps/mattermost-gateway/`

## URLs

| Context | URL |
|---------|-----|
| Docker network | `http://mattermost-gateway:8000` |
| Server localhost | `http://localhost:8011` |
| External (HTTPS) | `https://mattermost-gateway.server.unarmedpuppy.com` |

**Note**: API key authentication is planned but not yet implemented. External endpoint is currently open.

## Purpose

REST API gateway for posting messages to Mattermost as bot users. Enables any service to send notifications, alerts, or messages without direct Mattermost API integration.

## Available Bots

| Bot | Purpose | Token Env Var |
|-----|---------|---------------|
| `tayne` | Personal assistant, general help | `MATTERMOST_BOT_TAYNE_TOKEN` |
| `server-monitor` | Server status, alerts | `MATTERMOST_BOT_MONITOR_TOKEN` |
| `trading-bot` | Trading notifications | `MATTERMOST_BOT_TRADING_TOKEN` |

## API Endpoints

### POST /post
Post a message to a channel as a bot.

```bash
curl -X POST http://mattermost-gateway:8000/post \
  -H "Content-Type: application/json" \
  -d '{
    "bot": "tayne",
    "channel": "town-square",
    "message": "Hello from Tayne!"
  }'
```

**Response:**
```json
{"success": true, "post_id": "abc123", "error": null}
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
Retrieve recent messages from a channel.

```bash
curl "http://mattermost-gateway:8000/messages?channel=town-square&limit=10"
```

### POST /webhook/:bot
Receive webhook payloads and post as specified bot.

```bash
curl -X POST http://mattermost-gateway:8000/webhook/server-monitor \
  -H "Content-Type: application/json" \
  -d '{"text": "Alert: Disk usage above 90%"}'
```

### GET /health
Health check endpoint.

```bash
curl http://mattermost-gateway:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "bots": ["tayne", "server-monitor", "trading-bot"],
  "mattermost": "connected"
}
```

## Usage Examples

### From Docker Compose Service

```yaml
services:
  my-service:
    environment:
      - MATTERMOST_GATEWAY_URL=http://mattermost-gateway:8000
    networks:
      - my-network
```

```python
import httpx

async def notify(message: str):
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://mattermost-gateway:8000/post",
            json={
                "bot": "server-monitor",
                "channel": "alerts",
                "message": message
            }
        )
```

### From Cron Job

```cron
0 * * * * curl -s -X POST http://localhost:8011/post \
  -H "Content-Type: application/json" \
  -d '{"bot":"server-monitor","channel":"alerts","message":"Hourly health check: OK"}'
```

### From Shell Script

```bash
#!/bin/bash
# Send alert to Mattermost
send_alert() {
    local message="$1"
    curl -s -X POST http://mattermost-gateway:8000/post \
        -H "Content-Type: application/json" \
        -d "{\"bot\":\"server-monitor\",\"channel\":\"alerts\",\"message\":\"$message\"}"
}

send_alert "Backup completed successfully"
```

### From External (HTTPS)

Access from anywhere with internet connectivity:

```bash
curl -X POST https://mattermost-gateway.server.unarmedpuppy.com/post \
  -H "Content-Type: application/json" \
  -d '{"bot":"tayne","channel":"town-square","message":"Hello from external!"}'
```

## Channel Names

Use channel names (not IDs). The gateway resolves names to IDs automatically with caching.

Common channels:
- `town-square` - General announcements
- `alerts` - System alerts (create if needed)
- `off-topic` - Casual chat

## Error Handling

The gateway returns errors immediately (fail-fast design):

```json
{"success": false, "post_id": null, "error": "Channel not found: invalid-channel"}
```

Callers should implement their own retry logic if needed.

## Adding New Bots

1. Create bot in Mattermost System Console → Integrations → Bot Accounts
2. Add token to `apps/mattermost-gateway/.env`:
   ```
   MATTERMOST_BOT_NEWBOT_TOKEN=your-token-here
   ```
3. Update `docker-compose.yml` environment section
4. Restart gateway: `docker compose restart mattermost-gateway`

## Related Documentation

- [Mattermost Gateway Service Plan](../plans/mattermost-gateway-service.md) - Full implementation details
- [Mattermost Hub Strategy](../plans/mattermost-hub-strategy.md) - High-level vision
- [Mattermost REST API](https://api.mattermost.com/) - Official API docs
