# Services & Applications

For detailed information about all applications, their ports, and active status, see [APPS_DOCUMENTATION.md](./apps/docs/APPS_DOCUMENTATION.md).

### Key Services

#### Homepage
- **Docs**: [Homepage GitHub](https://github.com/gethomepage/homepage)
- **Configuration**: See `apps/homepage/docker-compose.yml`

To add services to homepage, add labels to containers:
```yaml
labels:
  - "homepage.group=Game Servers"
  - "homepage.name=Service Name"
  - "homepage.href=http://service.server.unarmedpuppy.com"
  - "homepage.description=Service description"
```

#### AdGuard Home

**Previous DNS**: 172.16.30.1

**Configuration**:
- Admin Web Interface: Port 80 (after initial setup on port 3003)
- DNS Server: Port 53 (TCP/UDP)
- Listen Interface: All interfaces
- Static IP Required: Yes (for proper function)

**Setup**: Configure router DHCP/DNS settings to point to AdGuard Home server addresses.

#### Grafana Monitoring Stack

Provides:
- **Grafana**: Web dashboard (port 3000/3010)
- **Telegraf**: Metrics collection from Docker host
- **InfluxDB**: Time-series database (port 8086)
  - Default database: `telegraf`
  - Default username: `telegrafuser`
  - Default password: `MyStrongTelegrafPassword`
- **Promtail**: Log shipper
- **Loki**: Log aggregation (port 3100, localhost only)

**Interrogate InfluxDB**:
```bash
docker exec -it influxdb influx -username <username> -password <password>
USE telegraf
SHOW MEASUREMENTS
```

**Dashboard**: Import `Grafana_Dashboard_Template.json` in Grafana.

**Auto-Login and Fullscreen Dashboard Setup**:

Configure the server to auto-login on boot and automatically open Grafana in fullscreen:

1. **Configure GDM3 Auto-Login**:
   ```bash
   sudo nano /etc/gdm3/custom.conf
   ```
   Add or update the `[daemon]` section:
   ```ini
   [daemon]
   AutomaticLogin=unarmedpuppy
   AutomaticLoginEnable=true
   ```

2. **Autostart Entry** (already created):
   - Location: `~/.config/autostart/grafana-dashboard.desktop`
   - Launches Firefox in kiosk mode with Grafana dashboard

3. **Startup Script** (backup method):
   - Location: `~/.xprofile`
   - Automatically launches browser on login

4. **Restart GDM**:
   ```bash
   sudo systemctl restart gdm3
   ```
   Or reboot: `sudo reboot`

**Quick Setup Script**:
```bash
# Copy setup script to server
scp -P 4242 scripts/setup-auto-login-grafana.sh unarmedpuppy@192.168.86.47:~/

# Run on server (requires sudo password)
ssh -p 4242 unarmedpuppy@192.168.86.47 "sudo bash ~/setup-auto-login-grafana.sh"
```

**Manual Browser Launch** (for testing):
```bash
firefox -kiosk http://192.168.86.47:3010/
```

**Disable Auto-Login**:
Edit `/etc/gdm3/custom.conf` and comment out or remove the `AutomaticLogin` lines, then restart GDM.

For detailed setup instructions, see [AUTO_LOGIN_GRAFANA_SETUP.md](./docs/AUTO_LOGIN_GRAFANA_SETUP.md).

#### Game Servers

**Rust Server**:
- Server Banner: [1024x512](https://i.imgur.com/FIXxuRI.jpg)
- RCON Access: http://192.168.86.47:8080/#/192.168.86.47:28016/playerlist

**Minecraft Bedrock Server**:
- Copy world from PC:
  ```bash
  scp -P 4242 -r ~/Desktop/server/minecraft/gumberlund unarmedpuppy@192.168.86.47:~/server/apps/minecraft/gumberlund
  ```
- Server commands:
  ```bash
  docker exec minecraft-bedrock-1 send-command op unarmedpupy
  ```
- Player XUID: `2535454866260420`

**Bedrock Viz** (Minecraft Map Visualization):
- Generate map on PC:
  ```bash
  bedrock-viz.exe --db C:\Users\micro\Desktop\server\minecraft\gumberlund --out ./map --html-most
  ```
- Copy to server:
  ```bash
  scp -P 4242 -r ~/Desktop/server/minecraft/map unarmedpuppy@192.168.86.47:~/server/apps/bedrock-viz/data/output
  ```
- Build from source: [Bedrock Viz Build Guide](https://github.com/bedrock-viz/bedrock-viz/blob/master/docs/BUILD.md)
  ```bash
  sudo apt install cmake libpng++-dev zlib1g-dev libboost-program-options-dev build-essential
  ```
- Generate map on server:
  ```bash
  ./bedrock-viz --db ~/server/apps/minecraft/backup-gumberlund --cfg ~/server/apps/bedrock-viz/repo/data/bedrock_viz.cfg --xml ~/server/apps/bedrock-viz/repo/data/bedrock_viz.xml --html-all
  ```

**Libreddit**:
- JavaScript snippet to extract all subscribed subreddits:
  ```javascript
  var items = ''
  document.querySelectorAll('left-nav-community-item').forEach(function (el){
    items = items + el.getAttribute('prefixedname') + "+"
  });
  ```

### Additional Tools

#### Node.js Installation
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### Immich CLI
```bash
sudo npm i -g @immich/cli
```

---