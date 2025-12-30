# 7 Days to Die Dedicated Server

Dockerized 7 Days to Die dedicated server using [vinanrra/7dtd-server](https://github.com/vinanrra/Docker-7DaysToDie) with LinuxGSM.

## Setup

1. Start the server (first run will download ~15GB of game files):
   ```bash
   docker compose up -d
   ```

2. Wait for initial setup to complete (check logs):
   ```bash
   docker logs -f 7daystodie
   ```

3. **Configure port forwarding** on your router:
   - TCP/UDP 26900 → 192.168.86.47
   - UDP 26901-26902 → 192.168.86.47

4. Edit server settings after first run:
   ```bash
   nano ./data/serverfiles/sdtdserver.xml
   ```

## Server Configuration

After the first run, edit `./data/serverfiles/sdtdserver.xml`:

| Setting | Description |
|---------|-------------|
| `ServerName` | Name shown in server browser |
| `ServerPassword` | Password to join (empty = public) |
| `ServerMaxPlayerCount` | Max players (default 8) |
| `GameWorld` | `Navezgane` (fixed) or `RWG` (random) |
| `WorldGenSeed` | Seed for random world generation |
| `GameName` | Save game name |

### Web Admin Panel

| Setting | Description |
|---------|-------------|
| `ControlPanelEnabled` | Enable web panel (true/false) |
| `ControlPanelPort` | Web panel port (default 8080, mapped to 26980) |
| `ControlPanelPassword` | Admin password |

### Telnet

| Setting | Description |
|---------|-------------|
| `TelnetEnabled` | Enable telnet (true/false) |
| `TelnetPort` | Telnet port (default 8081, mapped to 26981) |
| `TelnetPassword` | Telnet password |

## Features

- **Auto-restart**: Server restarts automatically if it crashes (MONITOR=YES)
- **Auto-backups**: Daily at 5 AM, keeps 7 backups
- **Alloc Fixes**: Web map and server fixes installed by default

## Connecting

### Direct IP

1. In 7 Days to Die: Join Game → Connect to IP
2. Enter: `192.168.86.47:26900` (LAN) or `your-public-ip:26900` (external)

### Server Browser

1. In 7 Days to Die: Join Game → Find Server
2. Search for your server name

## Data Locations

| Path | Contents |
|------|----------|
| `./data/saves/` | World saves and player data |
| `./data/serverfiles/` | Server installation and config |
| `./data/config/` | LinuxGSM configuration |
| `./data/log/` | Server logs |
| `./data/backups/` | Automatic backups |

## Useful Commands

```bash
# View logs
docker logs -f 7daystodie

# Stop server gracefully
docker compose down

# Restart server
docker compose restart

# Update server (change START_MODE to 2, then back to 1)
# Edit docker-compose.yml: START_MODE=2
docker compose up -d
# Wait for update, then change back to START_MODE=1
docker compose up -d

# Access web panel
# http://192.168.86.47:26980

# Access Alloc Fixes map
# http://192.168.86.47:26982
```

## Uptime Kuma Monitoring

Add a new monitor in Uptime Kuma:

| Setting | Value |
|---------|-------|
| Monitor Type | Game Server (Gamedig) |
| Game | 7 Days to Die (7d2d) |
| Hostname | 192.168.86.47 |
| Port | 26900 |
| Friendly Name | 7 Days to Die |

## Resource Requirements

- **RAM**: 8-12 GB recommended
- **Storage**: ~15 GB for server files + world saves
- **CPU**: 2+ cores recommended

## Troubleshooting

**Server not showing in browser:**
- Ensure ports 26900-26902 are forwarded
- Check `ServerVisibility` is set to 2 (public) in sdtdserver.xml

**Connection timeout:**
- Verify firewall allows the ports
- Check server is fully started in logs

**World not generating:**
- First world generation can take 10-30 minutes
- Check logs for progress

## Resources

- [Docker Image Documentation](https://github.com/vinanrra/Docker-7DaysToDie)
- [LinuxGSM 7DTD](https://linuxgsm.com/servers/sdtdserver/)
- [7DTD Server Settings](https://7daystodie.fandom.com/wiki/Server)
