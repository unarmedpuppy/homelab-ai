---
name: fix-hardcoded-credentials
description: Move hardcoded credentials from docker-compose.yml to environment variables
when_to_use: When security-audit or validate-secrets finds hardcoded credentials, before committing sensitive data
script: scripts/fix-hardcoded-credentials.sh
---

# Fix Hardcoded Credentials

Moves hardcoded credentials from docker-compose.yml to environment variables.

## When to Use

- Security audit finds hardcoded credentials
- Before committing sensitive data
- Migrating to secure secret management
- Fixing security vulnerabilities

## Usage

```bash
# Navigate to app directory
cd apps/homepage

# Run fix script
bash ../../scripts/fix-hardcoded-credentials.sh
```

## What It Does

1. **Extracts current credentials** - Reads from docker-compose.yml
2. **Optionally generates new password** - Creates secure password if needed
3. **Creates .env file** - With secure permissions (600)
4. **Updates docker-compose.yml** - Replaces hardcoded values with `${VARIABLE}`
5. **Ensures .gitignore** - Adds .env to .gitignore if missing

## Example

**Before:**
```yaml
labels:
  - "traefik.http.middlewares.homepage-auth.basicauth.users=admin:$apr1$..."
```

**After:**
```yaml
labels:
  - "traefik.http.middlewares.homepage-auth.basicauth.users=${HOMEPAGE_BASIC_AUTH}"
```

And creates `apps/homepage/.env`:
```bash
HOMEPAGE_BASIC_AUTH=admin:$apr1$...
```

## Verification

After running, verify:
```bash
# Check .env was created
ls -la apps/homepage/.env

# Verify permissions (should be 600)
stat -c "%a" apps/homepage/.env

# Check docker-compose.yml uses variable
grep HOMEPAGE_BASIC_AUTH apps/homepage/docker-compose.yml

# Verify .gitignore includes .env
grep "\.env" .gitignore
```

## Related Tools

- `security-audit` - Find security issues
- `validate-secrets` - Validate secrets configuration

