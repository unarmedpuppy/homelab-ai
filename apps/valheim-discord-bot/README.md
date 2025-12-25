# Valheim Discord Status Bot

Discord bot that displays Valheim server status in a channel.

## Setup

### 1. Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" → Name it "Valheim Status"
3. Go to "Bot" → Click "Add Bot"
4. Copy the **Token** (keep this secret!)
5. Enable these Privileged Gateway Intents:
   - Message Content Intent

### 2. Invite Bot to Server

1. Go to "OAuth2" → "URL Generator"
2. Select scopes: `bot`, `applications.commands`
3. Select permissions: `Send Messages`, `Embed Links`, `Read Message History`
4. Copy the generated URL and open it to invite the bot

### 3. Configure the Bot

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Add your bot token:
   ```
   DISCORD_TOKEN=your_token_here
   ```

3. Edit `config/config.json`:
   - Replace `YOUR_CHANNEL_ID_HERE` with the Discord channel ID
   - (Right-click channel → Copy ID, requires Developer Mode enabled)

### 4. Start the Bot

```bash
docker compose up -d
```

## Configuration

Edit `config/config.json` to customize:

```json
{
  "servers": [
    {
      "name": "Valheim - Fenrirhaven",
      "type": "valheim",
      "host": "192.168.86.47",
      "port": 2457,
      "channel": "123456789012345678",
      "updateInterval": 60
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `name` | Display name in Discord |
| `type` | Game type (valheim, minecraft, etc.) |
| `host` | Server IP (internal or external) |
| `port` | Query port (2457 for Valheim) |
| `channel` | Discord channel ID for status embed |
| `updateInterval` | Seconds between updates |

## Alternative: Uptime Kuma Discord Integration

For simpler alerting (up/down notifications only), use Uptime Kuma's built-in Discord webhook support instead of this bot. See [Uptime Kuma README](../uptime-kuma/README.md).
