# Firefox Kiosk Mode Troubleshooting

If Firefox opens but shows a blank black window, try these solutions:

## Quick Fix: Test Firefox Manually

On the server console (logged in), test Firefox:

```bash
# Close any existing Firefox windows
pkill firefox

# Test Firefox kiosk mode
firefox -kiosk http://192.168.86.47:3010/
```

If this works, the issue is with the autostart timing.

## Solution 1: Use Chromium Instead (Recommended)

If Firefox continues to have issues, switch to Chromium which has better kiosk mode support:

```bash
# Install Chromium if not installed
sudo apt update && sudo apt install -y chromium

# Update autostart entry
cat > ~/.config/autostart/grafana-dashboard.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Grafana Dashboard
Comment=Auto-launch Grafana dashboard in fullscreen
Exec=sh -c 'sleep 10 && chromium --kiosk --app=http://192.168.86.47:3010/'
Icon=grafana
Terminal=false
Categories=Network;Monitoring;
X-GNOME-Autostart-enabled=true
StartupNotify=false
NoDisplay=false
X-GNOME-Autostart-Delay=10
EOF
```

## Solution 2: Fix Firefox Profile

Firefox might need a clean profile for kiosk mode:

```bash
# Create a Firefox profile for kiosk mode
firefox -CreateProfile kiosk

# Update autostart to use the profile
cat > ~/.config/autostart/grafana-dashboard.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Grafana Dashboard
Comment=Auto-launch Grafana dashboard in fullscreen
Exec=sh -c 'sleep 10 && firefox -P kiosk -kiosk http://192.168.86.47:3010/'
Icon=grafana
Terminal=false
Categories=Network;Monitoring;
X-GNOME-Autostart-enabled=true
StartupNotify=false
NoDisplay=false
X-GNOME-Autostart-Delay=10
EOF
```

## Solution 3: Use Fullscreen Instead of Kiosk

If kiosk mode doesn't work, use fullscreen mode:

```bash
cat > ~/.config/autostart/grafana-dashboard.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Grafana Dashboard
Comment=Auto-launch Grafana dashboard in fullscreen
Exec=sh -c 'sleep 10 && firefox --fullscreen http://192.168.86.47:3010/'
Icon=grafana
Terminal=false
Categories=Network;Monitoring;
X-GNOME-Autostart-enabled=true
StartupNotify=false
NoDisplay=false
X-GNOME-Autostart-Delay=10
EOF
```

## Solution 4: Check Firefox Preferences

Firefox might be blocking the page. Check Firefox preferences:

1. Open Firefox normally: `firefox http://192.168.86.47:3010/`
2. If it works normally, the issue is with kiosk mode flags
3. Try: `firefox -kiosk -private-window http://192.168.86.47:3010/`

## Debugging Steps

1. **Check if Grafana is accessible:**
   ```bash
   curl -I http://192.168.86.47:3010/
   ```

2. **Check Firefox process:**
   ```bash
   ps aux | grep firefox
   ```

3. **Check Firefox logs:**
   ```bash
   tail -f ~/.mozilla/firefox/*/console.log
   ```

4. **Test with verbose output:**
   ```bash
   firefox -kiosk http://192.168.86.47:3010/ 2>&1 | tee /tmp/firefox-debug.log
   ```

## Recommended: Switch to Chromium

Chromium has more reliable kiosk mode support. To switch:

```bash
# Install Chromium
sudo apt update && sudo apt install -y chromium

# Update both autostart and .xprofile
cat > ~/.config/autostart/grafana-dashboard.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Grafana Dashboard
Comment=Auto-launch Grafana dashboard in fullscreen
Exec=sh -c 'sleep 10 && chromium --kiosk --app=http://192.168.86.47:3010/'
Icon=grafana
Terminal=false
Categories=Network;Monitoring;
X-GNOME-Autostart-enabled=true
StartupNotify=false
NoDisplay=false
X-GNOME-Autostart-Delay=10
EOF

cat > ~/.xprofile << 'EOF'
#!/bin/bash
# Auto-launch Grafana dashboard on login

sleep 10

# Wait for Grafana to be accessible
timeout=30
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if curl -s -o /dev/null -w '%{http_code}' http://192.168.86.47:3010/ | grep -q '200\|302'; then
        break
    fi
    sleep 2
    elapsed=$((elapsed + 2))
done

export DISPLAY=:0
chromium --kiosk --app=http://192.168.86.47:3010/ &
EOF

chmod +x ~/.xprofile
```

