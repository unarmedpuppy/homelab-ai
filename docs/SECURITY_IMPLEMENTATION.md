# Security Implementation Guide

Step-by-step guides to implement security fixes identified in `SECURITY_AUDIT.md`.

---

## Phase 1: Critical Fixes

### Fix 1: Remove Hardcoded Credentials

#### Step 1.1: Generate New Basic Auth Password

```bash
# On server or local machine
htpasswd -nb admin your_new_password
# Output: admin:$apr1$... (use this hash)
```

#### Step 1.2: Create Environment Variable

Create `apps/homepage/.env` (add to .gitignore):

```bash
# On server
cd ~/server/apps/homepage
cat > .env << EOF
HOMEPAGE_BASIC_AUTH=unarmedpuppy:\$apr1\$YOUR_NEW_HASH_HERE
EOF
chmod 600 .env
```

#### Step 1.3: Update docker-compose.yml

```yaml
# apps/homepage/docker-compose.yml
labels:
  - "traefik.http.middlewares.homepage-auth.basicauth.users=${HOMEPAGE_BASIC_AUTH}"
```

#### Step 1.4: Update .gitignore

Ensure `.env` files are ignored:

```bash
# In repository root
echo "apps/*/.env" >> .gitignore
echo "apps/*/.env.*" >> .gitignore
```

**Script**: Use `scripts/fix-hardcoded-credentials.sh` (see below)

---

### Fix 2: Run Containers as Non-Root

#### Step 2.1: Fix Homepage Container

```yaml
# apps/homepage/docker-compose.yml
services:
  homepage:
    # Remove: user: root
    # Add:
    user: "1000:1000"
    environment:
      - PUID=1000
      - PGID=1000
```

**Note**: Homepage may need root for Docker socket access. If so, use a dedicated user with minimal Docker permissions.

#### Step 2.2: Review Privileged Containers

**Jellyfin Unlock** (`apps/jellyfin/docker-compose-unlock.yml`):

This container needs `privileged: true` for ZFS operations. This is acceptable but should be:
- Documented why it's needed
- Isolated on separate network
- Monitored for security events

**Action**: Document the requirement and add monitoring.

---

### Fix 3: Implement Basic Secrets Management

#### Option A: Docker Secrets (Recommended for Swarm)

```bash
# Create secret
echo "your_password" | docker secret create homepage_auth -

# Use in docker-compose.yml
secrets:
  homepage_auth:
    external: true
```

#### Option B: Environment Files with Proper Permissions (Current Setup)

1. **Create `.env` files** (already in .gitignore)
2. **Set strict permissions**:
   ```bash
   chmod 600 apps/*/.env
   ```
3. **Document required variables** in `env.template` files
4. **Add validation script** to check for missing secrets

**Script**: Use `scripts/validate-secrets.sh` (see below)

---

## Phase 2: High Priority Fixes

### Fix 5: Install and Configure fail2ban

#### Step 5.1: Install fail2ban

```bash
sudo apt update
sudo apt install fail2ban -y
```

#### Step 5.2: Configure SSH Protection

Create `/etc/fail2ban/jail.local`:

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
destemail = your-email@example.com
sendername = Fail2Ban
action = %(action_mwl)s

[sshd]
enabled = true
port = 4242
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 86400
```

#### Step 5.3: Start and Enable

```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
sudo fail2ban-client status
```

**Script**: Use `scripts/setup-fail2ban.sh` (see below)

---

### Fix 6: Security Event Logging

#### Step 6.1: Configure Syslog Forwarding

Add to Grafana stack or use Loki to collect:
- `/var/log/auth.log` - SSH attempts
- `/var/log/syslog` - System events
- Docker logs - Container events

#### Step 6.2: Create Security Alerts

In Grafana, create alerts for:
- Multiple failed SSH attempts
- Unauthorized access attempts
- Container restarts
- Network anomalies

**Script**: Use `scripts/setup-security-logging.sh` (see below)

---

### Fix 7: Encrypt Backups

#### Step 7.1: Install Encryption Tools

```bash
sudo apt install gpg -y
```

#### Step 7.2: Generate GPG Key

```bash
gpg --full-generate-key
# Use RSA, 4096 bits, no expiration
```

#### Step 7.3: Update Backup Script

Modify `scripts/backup-server.sh` to encrypt before storing:

```bash
# Encrypt backup
tar czf - backup_dir | gpg --encrypt --recipient your-email@example.com > backup.tar.gz.gpg
```

**Script**: Use `scripts/encrypt-backup.sh` (see below)

---

### Fix 8: Container Image Scanning

#### Step 8.1: Install Trivy

```bash
sudo apt install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt update
sudo apt install trivy -y
```

#### Step 8.2: Scan Images

```bash
# Scan all images
trivy image --format table $(docker images --format "{{.Repository}}:{{.Tag}}")
```

#### Step 8.3: Integrate into CI/CD

Add to deployment script to scan before deployment.

**Script**: Use `scripts/scan-containers.sh` (see below)

---

## Phase 3: Medium Priority Fixes

### Fix 9: Remove Default Credentials

1. Review all `env.template` files
2. Remove default values
3. Add validation in deployment scripts
4. Add warnings for missing required variables

### Fix 10: Add Resource Limits

```yaml
services:
  my-service:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Fix 11: Network Segmentation

Create separate networks:

```yaml
networks:
  frontend:
    external: true
  backend:
    internal: true
  database:
    internal: true
```

### Fix 12: Rate Limiting in Traefik

```yaml
labels:
  - "traefik.http.middlewares.ratelimit.ratelimit.average=100"
  - "traefik.http.middlewares.ratelimit.ratelimit.burst=50"
```

### Fix 13: Security Headers

```yaml
labels:
  - "traefik.http.middlewares.security-headers.headers.stsSeconds=31536000"
  - "traefik.http.middlewares.security-headers.headers.stsIncludeSubdomains=true"
  - "traefik.http.middlewares.security-headers.headers.frameDeny=true"
```

---

## Quick Start: Run All Critical Fixes

```bash
# 1. Fix hardcoded credentials
bash scripts/fix-hardcoded-credentials.sh

# 2. Setup fail2ban
bash scripts/setup-fail2ban.sh

# 3. Validate secrets
bash scripts/validate-secrets.sh

# 4. Run security audit
bash scripts/security-audit.sh
```

---

## Verification

After implementing fixes, verify:

```bash
# Check fail2ban status
sudo fail2ban-client status

# Verify no hardcoded passwords
grep -r "password.*=" apps/*/docker-compose.yml | grep -v "#"

# Check container users
docker inspect <container> | grep -A 5 "User"

# Verify .env files are ignored
git check-ignore apps/*/.env
```

---

**Next**: Run the security audit script regularly to ensure compliance.


