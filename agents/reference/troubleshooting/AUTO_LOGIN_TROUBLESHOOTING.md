# Auto-Login Troubleshooting Guide

If auto-login still doesn't work after configuration, try these steps:

## Verify GDM3 Configuration

Check that both files are correctly configured:

```bash
# Check custom.conf
sudo cat /etc/gdm3/custom.conf

# Should show:
[daemon]
AutomaticLogin=unarmedpuppy
AutomaticLoginEnable=true

# Check daemon.conf
sudo grep -A 2 '[daemon]' /etc/gdm3/daemon.conf

# Should show:
[daemon]
WaylandEnable=false
```

## Fix GDM3 Configuration

If the configuration is wrong, fix it:

```bash
# Backup existing configs
sudo cp /etc/gdm3/custom.conf /etc/gdm3/custom.conf.bak
sudo cp /etc/gdm3/daemon.conf /etc/gdm3/daemon.conf.bak

# Set custom.conf
sudo tee /etc/gdm3/custom.conf > /dev/null << 'EOF'
[daemon]
AutomaticLogin=unarmedpuppy
AutomaticLoginEnable=true
EOF

# Ensure Wayland is disabled in daemon.conf
sudo sed -i '/^\[daemon\]/a WaylandEnable=false' /etc/gdm3/daemon.conf

# Verify
sudo cat /etc/gdm3/custom.conf
sudo grep -A 2 '[daemon]' /etc/gdm3/daemon.conf
```

## Alternative: Use LightDM Instead

If GDM3 continues to have issues, consider switching to LightDM which has more reliable auto-login:

```bash
# Install LightDM
sudo apt update
sudo apt install -y lightdm lightdm-gtk-greeter

# Configure auto-login
sudo nano /etc/lightdm/lightdm.conf

# Under [Seat:*] section, add:
autologin-user=unarmedpuppy
autologin-user-timeout=0

# Switch display manager
sudo dpkg-reconfigure lightdm

# Select LightDM when prompted
```

## Check User Account

Ensure the user account is not locked:

```bash
# Check account status
passwd -S unarmedpuppy

# Should show "P" (password set), not "L" (locked)
# If locked, unlock it:
sudo passwd -u unarmedpuppy
```

## Check Logs

Check GDM3 logs for errors:

```bash
# View GDM3 logs
sudo journalctl -u gdm3 -n 50 --no-pager

# Check for authentication errors
sudo journalctl -u gdm3 | grep -i "automatic\|login\|error" | tail -20
```

## Full Reboot Required

GDM3 auto-login typically requires a **full reboot**, not just restarting GDM:

```bash
sudo reboot
```

## Manual Test

After rebooting, if it still doesn't work:

1. Log in manually
2. Check if the configuration files are still correct
3. Try manually editing them again
4. Check if there are any permission issues:

```bash
ls -la /etc/gdm3/custom.conf
ls -la /etc/gdm3/daemon.conf
```

Both should be owned by root and readable.

## Nuclear Option: Reinstall GDM3

If nothing works, reinstall GDM3:

```bash
sudo apt remove --purge gdm3
sudo apt install gdm3
# Then reconfigure auto-login settings
```

