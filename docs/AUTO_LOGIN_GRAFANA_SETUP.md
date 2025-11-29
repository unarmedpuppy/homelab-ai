# Auto-Login and Grafana Dashboard Setup

This guide will help you configure your Debian 12 server to:
1. Auto-login on boot (no password required)
2. Automatically open Grafana dashboard in fullscreen

## Quick Setup

Run this command on your server (you'll need to enter your sudo password):

```bash
sudo bash ~/setup-auto-login-grafana.sh
```

Then restart GDM or reboot:
```bash
sudo systemctl restart gdm3
# OR
sudo reboot
```

## Manual Setup (Alternative)

If you prefer to set it up manually:

### 1. Configure GDM3 Auto-Login

Edit `/etc/gdm3/custom.conf`:

```bash
sudo nano /etc/gdm3/custom.conf
```

Add or update the `[daemon]` section:

```ini
[daemon]
AutomaticLogin=unarmedpuppy
AutomaticLoginEnable=true
```

### 2. Create Autostart Entry

Create the autostart directory and desktop entry:

```bash
mkdir -p ~/.config/autostart
nano ~/.config/autostart/grafana-dashboard.desktop
```

Add this content (adjust browser command if needed):

```ini
[Desktop Entry]
Type=Application
Name=Grafana Dashboard
Comment=Auto-launch Grafana dashboard in fullscreen
Exec=firefox -kiosk http://192.168.86.47:3010/
Icon=grafana
Terminal=false
Categories=Network;Monitoring;
X-GNOME-Autostart-enabled=true
StartupNotify=false
NoDisplay=false
```

### 3. Create .xprofile Script (Backup Method)

Create `~/.xprofile`:

```bash
nano ~/.xprofile
```

Add:

```bash
#!/bin/bash
# Auto-launch Grafana dashboard on login

# Wait for display and desktop to be ready
sleep 5

# Launch browser in kiosk mode
firefox -kiosk http://192.168.86.47:3010/ &
```

Make it executable:

```bash
chmod +x ~/.xprofile
```

### 4. Restart GDM

```bash
sudo systemctl restart gdm3
```

Or simply reboot:

```bash
sudo reboot
```

## Browser Options

The script detects and uses the first available browser in this order:
1. Chromium (`chromium --kiosk --app=URL`)
2. Chromium Browser (`chromium-browser --kiosk --app=URL`)
3. Firefox (`firefox -kiosk URL`)
4. Google Chrome (`google-chrome --kiosk --app=URL`)

## Troubleshooting

### Auto-login not working
- Check `/etc/gdm3/custom.conf` has the correct username
- Ensure `AutomaticLoginEnable=true` is set
- Restart GDM: `sudo systemctl restart gdm3`

### Browser not launching
- Check if browser is installed: `which firefox` or `which chromium`
- Check autostart entry: `cat ~/.config/autostart/grafana-dashboard.desktop`
- Check `.xprofile`: `cat ~/.xprofile`
- Check logs: `journalctl -u gdm3 -n 50`

### Browser launches but not in fullscreen
- Firefox: Use `-kiosk` flag (already included)
- Chromium: Use `--kiosk --app=URL` (already included)
- Try manually: `firefox -kiosk http://192.168.86.47:3010/`

### Disable Auto-Login

To disable auto-login, edit `/etc/gdm3/custom.conf` and comment out or remove:
```ini
# AutomaticLogin=unarmedpuppy
# AutomaticLoginEnable=true
```

Then restart GDM: `sudo systemctl restart gdm3`

## Files Created

- `/etc/gdm3/custom.conf` - GDM auto-login configuration
- `~/.config/autostart/grafana-dashboard.desktop` - GNOME autostart entry
- `~/.xprofile` - X session startup script (backup method)

## Security Note

⚠️ **Warning**: Auto-login bypasses password protection. Only use this on a trusted, physically secure server. If security is a concern, consider using a password-protected login with auto-launch of Grafana instead.

