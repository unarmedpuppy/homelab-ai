---
name: post-to-mattermost
description: Post messages to Mattermost channels via the gateway API
when_to_use: Need to send notifications, alerts, or messages to Mattermost
---

# Post to Mattermost

Send messages to Mattermost channels using the gateway API.

## When to Use

- Send notifications or alerts
- Post status updates
- Communicate with users via Mattermost
- Trigger bot messages from scripts or services

## Quick Reference

### From Server (SSH)

```bash
# Post as Tayne
bash scripts/connect-server.sh 'curl -s -X POST http://localhost:8011/post \
  -H "Content-Type: application/json" \
  -d "{\"bot\":\"tayne\",\"channel\":\"town-square\",\"message\":\"Hello from Tayne!\"}"'

# Post as server-monitor
bash scripts/connect-server.sh 'curl -s -X POST http://localhost:8011/post \
  -H "Content-Type: application/json" \
  -d "{\"bot\":\"server-monitor\",\"channel\":\"alerts\",\"message\":\"System alert: Check required\"}"'
```

### From External (HTTPS)

```bash
curl -X POST https://mattermost-gateway.server.unarmedpuppy.com/post \
  -H "Content-Type: application/json" \
  -d '{"bot":"tayne","channel":"town-square","message":"Hello!"}'
```

### From Docker Services

```python
import httpx

async def post_to_mattermost(bot: str, channel: str, message: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://mattermost-gateway:8000/post",
            json={"bot": bot, "channel": channel, "message": message}
        )
        return response.json()
```

## Available Bots

| Bot | Purpose |
|-----|---------|
| `tayne` | Personal assistant, general messages |
| `server-monitor` | Server alerts and status |
| `trading-bot` | Trading notifications |

## Common Channels

| Channel | Purpose |
|---------|---------|
| `town-square` | General announcements |
| `alerts` | System alerts |
| `off-topic` | Casual chat |

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/post` | POST | Post a message |
| `/react` | POST | Add emoji reaction |
| `/messages` | GET | Retrieve messages |
| `/health` | GET | Health check |

## Response Format

```json
{"success": true, "post_id": "abc123", "error": null}
```

## URLs

| Context | URL |
|---------|-----|
| Docker network | `http://mattermost-gateway:8000` |
| Server localhost | `http://localhost:8011` |
| External HTTPS | `https://mattermost-gateway.server.unarmedpuppy.com` |

## Related

- [Mattermost Gateway Reference](../../reference/mattermost-gateway.md) - Full API documentation
- [Mattermost Gateway Service Plan](../../plans/mattermost-gateway-service.md) - Implementation details
