# Scripts Directory

Comprehensive collection of automation scripts for home server management.

## Table of Contents

- [Server Connection](#server-connection)
- [Docker Management](#docker-management)
- [Deployment & Git](#deployment--git)
- [Backup & Restore](#backup--restore)
- [System Setup](#system-setup)
- [Media Management](#media-management)
- [Utilities](#utilities)

---

## Server Connection

### connect-server.sh

SSH connection wrapper for executing commands on the server.

**Usage:**
```bash
bash scripts/connect-server.sh "command"
bash scripts/connect-server.sh "docker ps"
bash scripts/connect-server.sh "cd ~/server/apps/plex && docker compose ps"
```

**Purpose**: Simplifies SSH access by wrapping the connection details (host, port, user).

---

## Docker Management

### docker-start.sh

Automatically starts all Docker Compose applications on server boot.

**Features:**
- **Label-based control**: Uses `x-enabled` label in docker-compose.yml files
- **Backward compatible**: Apps without the label will start by default
- **Easy management**: Just set `x-enabled: false` to disable an app

**Usage:**
```bash
# On server
~/server/scripts/docker-start.sh
```

**Configuration:**

Add `x-enabled: true` or `x-enabled: false` to your docker-compose.yml:
```yaml
version: "3.8"
x-enabled: true  # or false to disable
services:
  my-app:
    # ... your config
```

### docker-stop.sh

Stops all Docker Compose applications.

**Usage:**
```bash
# On server
~/server/scripts/docker-stop.sh
```

### docker-restart.sh

Restarts all Docker containers (stops then starts).

**Usage:**
```bash
# On server
~/server/scripts/docker-restart.sh
```

**Note**: Also available as `cycle` alias on the server.

### docker-start-example.sh

Test script to see which apps would start without actually starting them.

**Usage:**
```bash
~/server/scripts/docker-start-example.sh
```

**Output:**
- ✅ Apps that are enabled (will start)
- ❌ Apps that are disabled (will be skipped)
- Apps without the label (default: enabled)

---

## Deployment & Git

### deploy-to-server.sh

**NEW** - Automates the complete deployment workflow: commit, push, pull on server, and restart services.

**Usage:**
```bash
# Deploy all changes
bash scripts/deploy-to-server.sh "Your commit message"

# Deploy and restart specific app
bash scripts/deploy-to-server.sh "Update plex config" --app plex

# Deploy without restarting services
bash scripts/deploy-to-server.sh "Documentation update" --no-restart
```

**What it does:**
1. Stages all changes (`git add .`)
2. Commits with your message
3. Pushes to remote
4. Pulls on server
5. Optionally restarts specified app or all apps

### git-server-sync.sh

Synchronizes git repository between local and server.

**Usage:**
```bash
bash scripts/git-server-sync.sh
```

**What it does:**
1. Runs `git-sync.sh` locally (pull, add, commit, push)
2. Runs `git-sync.sh` on server (pull, add, commit, push)

### git-sync.sh

Local git sync script (pull, add all, commit, push).

**Usage:**
```bash
bash scripts/git-sync.sh
```

---

## Backup & Restore

### backup-server.sh

Comprehensive backup script for the entire server.

**Backs up:**
- All Docker volumes
- All docker-compose.yml files and configurations
- System configurations (/etc)
- User home directory configurations
- Cron jobs
- Mount point information
- System package lists

**Usage:**
```bash
# On server
BACKUP_DEST=/mnt/server-cloud/backups/daily ~/server/scripts/backup-server.sh

# From local machine
bash scripts/connect-server.sh "BACKUP_DEST=/mnt/server-cloud/backups/daily ~/server/scripts/backup-server.sh"
```

**See also:** [BACKUP_QUICKSTART.md](./BACKUP_QUICKSTART.md) and [backup-strategy.md](./backup-strategy.md)

### restore-server.sh

Restores from backups created by `backup-server.sh`.

**Usage:**
```bash
# On server
RESTORE_SOURCE=/mnt/server-cloud/backups/daily/latest ~/server/scripts/restore-server.sh
```

**Warning**: This will overwrite existing data. Requires confirmation.

### backup-rust.sh

Backs up Rust game server player data.

**Usage:**
```bash
# On server
~/server/scripts/backup-rust.sh
```

### restore-rust.sh

Restores Rust game server player data from backup.

**Usage:**
```bash
# On server
~/server/scripts/restore-rust.sh
```

### check-backup-health.sh

Validates backup integrity and checks for recent backups.

**Usage:**
```bash
# On server
~/server/scripts/check-backup-health.sh
```

### cleanup-old-backups.sh

Removes old backups based on retention policy.

**Usage:**
```bash
# On server
~/server/scripts/cleanup-old-backups.sh
```

### setup-backup-cron.sh

Sets up automated backup cron jobs.

**Usage:**
```bash
# On server
~/server/scripts/setup-backup-cron.sh
```

**Sets up:**
- Daily backups at 2 AM (kept 7 days)
- Weekly backups on Sunday 1 AM (kept 4 weeks)
- Monthly backups on 1st at midnight (kept 6 months)
- Automatic cleanup of old backups
- Backup health checks

---

## System Setup

### setup-auto-login-grafana.sh

Configures automatic login and fullscreen Grafana dashboard on boot.

**Usage:**
```bash
# Copy to server first
scp -P 4242 scripts/setup-auto-login-grafana.sh unarmedpuppy@192.168.86.47:~/

# Run on server (requires sudo)
ssh -p 4242 unarmedpuppy@192.168.86.47 "sudo bash ~/setup-auto-login-grafana.sh"
```

### fix-gdm-autologin-complete.sh

Fixes GDM3 auto-login configuration issues.

**Usage:**
```bash
# On server (requires sudo)
sudo bash ~/server/scripts/fix-gdm-autologin-complete.sh
```

---

## Media Management

### mv-youtube.sh

Moves YouTube downloads to appropriate directories.

**Usage:**
```bash
# On server
~/server/scripts/mv-youtube.sh
```

### organize-kids-films.py

Organizes children's films into appropriate directories.

**Usage:**
```bash
# On server
python3 ~/server/scripts/organize-kids-films.py
```

---

## Utilities

### check-service-health.sh

Quick health check for all Docker services.

**Usage:**
```bash
# From local machine
bash scripts/check-service-health.sh

# On server
~/server/scripts/check-service-health.sh
```

**Output:**
- Container status (running/stopped/restarting)
- Port mappings
- Health check status (if configured)
- Recent restart counts

---

## Security Tools

### security-audit.sh

Comprehensive security audit of the server infrastructure.

**Usage:**
```bash
# From local machine
bash scripts/security-audit.sh

# On server
~/server/scripts/security-audit.sh
```

**Checks:**
- Hardcoded credentials
- Container security (root users, privileged)
- Secrets management
- Git security (.gitignore)
- Intrusion prevention (fail2ban)
- Resource limits
- Network security
- Default credentials

**See also:** [Security Audit Documentation](../docs/SECURITY_AUDIT.md)

### validate-secrets.sh

Validates secrets configuration and identifies security issues.

**Usage:**
```bash
bash scripts/validate-secrets.sh
```

**Checks:**
- Hardcoded credentials in docker-compose files
- .env file permissions
- Default passwords in templates
- .gitignore configuration
- Secrets that should be in environment variables

### fix-hardcoded-credentials.sh

Moves hardcoded credentials from docker-compose.yml to environment variables.

**Usage:**
```bash
bash scripts/fix-hardcoded-credentials.sh
```

**What it does:**
1. Extracts current basic auth hash
2. Optionally generates new password
3. Creates .env file with secure permissions
4. Updates docker-compose.yml to use environment variable
5. Ensures .env is in .gitignore

**Example:**
```bash
# Fix homepage credentials
cd apps/homepage
bash ../../scripts/fix-hardcoded-credentials.sh
```

### setup-fail2ban.sh

Installs and configures fail2ban for SSH intrusion prevention.

**Usage:**
```bash
# On server (requires sudo)
sudo bash scripts/setup-fail2ban.sh
```

**What it does:**
1. Installs fail2ban
2. Configures SSH protection (port 4242)
3. Sets ban time (24 hours for SSH)
4. Enables and starts service
5. Verifies configuration

**Configuration:**
- Ban time: 24 hours for SSH
- Max retries: 3 attempts
- Time window: 10 minutes

**See also:** [Security Implementation Guide](../docs/SECURITY_IMPLEMENTATION.md)

### verify-dns-setup.sh

Verifies AdGuard Home DNS configuration and accessibility.

**Usage:**
```bash
# From local machine or server
bash scripts/verify-dns-setup.sh
```

**What it checks:**
1. AdGuard Home container status
2. DNS port (53) accessibility
3. DNS resolution functionality
4. Current device DNS configuration
5. AdGuard Home web interface accessibility
6. Firewall rules (if on server)

**Output:**
- ✓ Green checkmarks for passing checks
- ! Yellow warnings for issues to review
- ✗ Red errors for critical problems

**See also:** [Google Home DNS Setup Guide](../docs/GOOGLE_HOME_DNS_SETUP.md)

### update-homepage-groups.py

Updates homepage service groups in docker-compose.yml files.

**Usage:**
```bash
# On server or local
python3 scripts/update-homepage-groups.py
```

### vpn-share.sh

Configures VPN sharing settings.

**Usage:**
```bash
# On server
~/server/scripts/vpn-share.sh
```

### rsync.bat

Windows batch file for rsync operations (legacy).

---

## See Also

- [Docker Compose Enabled Label Documentation](../docs/DOCKER_COMPOSE_ENABLED_LABEL.md)
- [Backup Quick Start Guide](./BACKUP_QUICKSTART.md)
- [Backup Strategy](./backup-strategy.md)
- [Server Context](../agents/prompts/server.md)

