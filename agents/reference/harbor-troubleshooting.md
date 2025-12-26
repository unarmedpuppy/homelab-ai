# Harbor Registry Troubleshooting Guide

Reference document for diagnosing and fixing Harbor registry issues.

## Working Configuration Summary

The final working Harbor setup requires these key configurations:

### 1. Registry Config (`config/registry/config.yml`)
```yaml
http:
  addr: :5000
  relativeurls: true  # Returns relative URLs instead of internal hostnames
  host: https://harbor.server.unarmedpuppy.com  # External URL for Location headers
auth:
  htpasswd:  # ONLY htpasswd - no token auth here
    realm: harbor-registry-basic-realm
    path: /etc/registry/passwd
```

### 2. Nginx Proxy (`config/proxy/nginx.conf`)
All locations need `proxy_set_header Authorization $http_authorization;`

### 3. Storage Permissions
Registry runs as UID 10000:
```bash
sudo chown -R 10000:10000 /jenquist-cloud/harbor/registry
```

### 4. Passwd File (`config/registry/passwd`)
Generated with: `htpasswd -Bbn harbor_registry_user <HARBOR_CORE_SECRET>`

## Architecture Overview

```
Client (docker login)
    ↓
Traefik (HTTPS termination)
    ↓
harbor-proxy (nginx) [:8080]
    ↓
harbor-core [:8080] ←→ harbor-db (postgres)
    ↓                ←→ harbor-redis
harbor-registry [:5000]
```

**Key insight**: harbor-core sits between clients and the registry. It validates client tokens and uses its own credentials to communicate with the registry.

## Issue: Docker Login 401 Unauthorized

### Symptoms
- `docker login harbor.server.unarmedpuppy.com` fails with 401
- Harbor web UI works fine
- API calls with Basic auth work (`curl -u admin:password /api/v2.0/...`)

### Diagnosis Steps

1. **Check container health**:
   ```bash
   docker ps --filter 'name=harbor' --format 'table {{.Names}}\t{{.Status}}'
   ```

2. **Test token service**:
   ```bash
   curl -s -k -u admin:Harbor12345 \
     'https://harbor.server.unarmedpuppy.com/service/token?service=harbor-registry' \
     | jq .token
   ```
   If this returns a token, the token service works.

3. **Test token against registry directly** (bypassing core):
   ```bash
   TOKEN=$(curl -s -k -u admin:Harbor12345 \
     'https://harbor.server.unarmedpuppy.com/service/token?service=harbor-registry' \
     | jq -r .token)
   docker exec harbor-proxy curl -s -H "Authorization: Bearer $TOKEN" \
     'http://harbor-registry:5000/v2/'
   ```
   - If this returns `{}` → registry accepts tokens, issue is with core
   - If this returns 401 → registry token validation broken

4. **Check harbor-core logs**:
   ```bash
   docker logs harbor-core --tail 50 2>&1 | grep -i 'error\|token\|auth'
   ```

5. **Check harbor-registry logs**:
   ```bash
   docker logs harbor-registry --tail 50 2>&1 | grep -i 'error\|auth'
   ```

### Root Causes & Fixes

#### Issue 1: Nginx not passing Authorization header

**Symptom**: Token service works, but /v2/ always returns 401 even with valid token.

**Diagnosis**:
```bash
# Check if nginx passes Authorization header
docker exec harbor-proxy grep -n 'Authorization' /etc/nginx/nginx.conf
```

**Fix**: Add `proxy_set_header Authorization $http_authorization;` to nginx locations:
- `/api/`
- `/service/`
- `/v2/`

**File**: `apps/harbor/config/proxy/nginx.conf`

```nginx
location /v2/ {
  proxy_pass http://harbor-core:8080/v2/;
  proxy_set_header Host $http_host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
  proxy_set_header Authorization $http_authorization;  # ADD THIS
  # ... rest of config
}
```

#### Issue 2: Registry auth configuration (htpasswd vs token)

**Symptom**:
- harbor-registry logs show "authorization token required" for requests from core
- Or registry fails to start with "must provide exactly one type"

**Key insight**: Docker Registry v2 only supports ONE auth type. Official Harbor uses **htpasswd only** on the registry. Token auth is handled by harbor-core for external clients.

**Root cause**: We initially tried both token + htpasswd, but registry only supports one.

**Fix**: Use htpasswd-only auth (like official Harbor).

1. Create passwd file:
   ```bash
   htpasswd -Bbn harbor_registry_user <HARBOR_CORE_SECRET> > apps/harbor/config/registry/passwd
   ```

2. Update `apps/harbor/config/registry/config.yml` with htpasswd ONLY:
   ```yaml
   auth:
     htpasswd:
       realm: harbor-registry-basic-realm
       path: /etc/registry/passwd
   ```

   **DO NOT** add token auth section - harbor-core handles client tokens.

3. Mount passwd file in `docker-compose.yml`:
   ```yaml
   harbor-registry:
     volumes:
       - type: bind
         source: ./config/registry/passwd
         target: /etc/registry/passwd
   ```

#### Issue 3: Token signing key mismatch

**Symptom**: harbor-core logs show "token is malformed" or signature verification errors.

**Diagnosis**:
```bash
# Compare public keys
docker exec harbor-core openssl rsa -in /etc/core/private_key.pem -pubout 2>/dev/null | md5sum
docker exec harbor-registry openssl x509 -in /etc/registry/root.crt -pubkey -noout 2>/dev/null | md5sum
```
Hashes should match.

**Fix**: Regenerate matching key pair:
```bash
openssl genrsa -traditional -out config/core/private_key.pem 4096
openssl req -new -x509 -key config/core/private_key.pem \
  -out config/registry/root.crt -days 3650 \
  -subj "/CN=harbor-token-issuer"
chmod 644 config/core/private_key.pem config/registry/root.crt
```

#### Issue 4: Push fails with EOF or retries indefinitely

**Symptom**: `docker push` keeps retrying, eventually fails with EOF.

**Diagnosis**:
```bash
# Check registry logs
docker logs harbor-registry --tail 30 2>&1 | grep -E 'error|POST'
```

**Possible causes**:

1. **Storage permission denied**:
   ```
   err.detail="filesystem: mkdir /storage/docker: permission denied"
   ```
   Registry runs as UID 10000. Fix:
   ```bash
   sudo chown -R 10000:10000 /jenquist-cloud/harbor/registry
   ```

2. **Internal Location URLs**:
   Registry returns `Location: http://harbor-registry:5000/...` which clients can't reach.

   Fix in `config/registry/config.yml`:
   ```yaml
   http:
     addr: :5000
     relativeurls: true
     host: https://harbor.server.unarmedpuppy.com
   ```

## Storage Configuration

### Moving registry storage to external volume

**File**: `apps/harbor/docker-compose.yml`

Change from:
```yaml
volumes:
  - ./data/registry:/storage:z
```

To:
```yaml
volumes:
  - /jenquist-cloud/harbor/registry:/storage:z
```

**Both services need this change**:
- `harbor-registry`
- `harbor-registryctl`

**Create directory on server**:
```bash
sudo mkdir -p /jenquist-cloud/harbor/registry
sudo chown -R 1000:1000 /jenquist-cloud/harbor
```

## Quick Diagnostic Commands

```bash
# Full health check
curl -s -k https://harbor.server.unarmedpuppy.com/api/v2.0/health | jq .

# Test docker login flow manually
TOKEN=$(curl -s -k -u admin:Harbor12345 \
  'https://harbor.server.unarmedpuppy.com/service/token?account=admin&client_id=docker&offline_token=true&service=harbor-registry' \
  | jq -r .token)
curl -s -k -H "Authorization: Bearer $TOKEN" 'https://harbor.server.unarmedpuppy.com/v2/'
# Should return: {}

# Decode JWT token
echo $TOKEN | cut -d. -f2 | base64 -d 2>/dev/null | jq .

# Check what's in the proxy logs
docker logs harbor-proxy --tail 20 2>&1 | grep -E 'v2|token'

# Check core environment
docker exec harbor-core env | grep -E 'REGISTRY|SECRET|KEY'
```

## Key Files

| File | Purpose |
|------|---------|
| `config/proxy/nginx.conf` | Nginx reverse proxy config (needs Authorization header) |
| `config/registry/config.yml` | Registry auth config (needs htpasswd + token) |
| `config/registry/passwd` | htpasswd file for internal auth |
| `config/registry/root.crt` | Public key for token verification |
| `config/core/private_key.pem` | Private key for token signing |
| `config/core/key` | Core encryption key (16 bytes) |
| `.env` | Secrets (HARBOR_CORE_SECRET, HARBOR_DB_PASSWORD, etc.) |

## Restart Procedure

After config changes:
```bash
cd apps/harbor
docker compose up -d --force-recreate
```

To restart specific service:
```bash
docker compose restart harbor-proxy  # After nginx.conf changes
docker compose restart harbor-registry  # After registry config changes
docker compose restart harbor-core  # After core config changes
```

## Common Gotchas

1. **Private key format**: Harbor expects RSA format (`-----BEGIN RSA PRIVATE KEY-----`), not PKCS#8 (`-----BEGIN PRIVATE KEY-----`). Use `openssl genrsa -traditional` to generate.

2. **htpasswd order matters**: In registry config, `htpasswd` should come before `token` in the auth section.

3. **Container restart after config change**: Config files are bind-mounted, but services may cache config. Always restart after changes.

4. **Registry storage permissions**: Must be owned by UID 1000 (harbor user inside container).

5. **Traefik vs nginx-proxy**: Both can strip headers. The Authorization header needs to pass through the entire chain: Traefik → nginx-proxy → core → registry.
