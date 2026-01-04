# Valheim Dedicated Server

Dockerized Valheim dedicated server using [lloesche/valheim-server](https://github.com/lloesche/valheim-server-docker).

## Setup

1. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   nano .env
   ```

2. Start the server:
   ```bash
   docker compose up -d
   ```

3. **Configure port forwarding** on your router:
   - UDP 2456-2458 → 192.168.86.47

## Configuration

| Variable | Description |
|----------|-------------|
| `SERVER_NAME` | Name shown in server browser |
| `WORLD_NAME` | World save file name |
| `SERVER_PASS` | Password to join (min 5 chars) |

## Features

- **Auto-backups**: Every 6 hours, keeps 7 days
- **Auto-updates**: Daily at 5 AM
- **Auto-restart**: Daily at 6 AM (after updates)
- **Metals through portals**: Enabled via native World Modifier (no mods required)

## Connecting

### With Crossplay Enabled (default)

When `CROSSPLAY=true` (default), you **must use the Join Code** to connect:

1. In Valheim: Start Game → Select Character → Join Game
2. Click **"Join by code"** (or look for a code entry option)
3. Enter the 6-digit Join Code shown in server logs

**To find the Join Code:**
```bash
docker logs valheim 2>&1 | grep "join code"
```

Example output: `Session "unarmedpuppy" registered with join code 757374`

> **Note**: Direct IP connection (`Add Server` → IP:port) does NOT work when crossplay is enabled. The server uses PlayFab for matchmaking instead of Steam networking.

### With Crossplay Disabled

If you disable crossplay (`CROSSPLAY=false`), you can connect via direct IP:

1. In Valheim: Join Game → Add Server
2. Enter: `192.168.86.47:2456` (LAN) or `your-public-ip:2456` (external)
3. Or find in Community Servers by name

## World Data

| Path | Contents |
|------|----------|
| `./data/config/` | World saves, backups |
| `./data/data/` | Valheim installation |

## Useful Commands

```bash
# View logs
docker logs -f valheim

# Stop server gracefully (saves world)
docker compose down

# Backup world manually
docker exec valheim backup

# Check server status
docker exec valheim status
```

## Resources

- ~2-4 GB RAM usage
- World saves in `./data/config/worlds_local/`
- Backups in `./data/config/backups/`
