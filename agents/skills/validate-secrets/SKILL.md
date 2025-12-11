---
name: validate-secrets
description: Validate secrets configuration and identify security issues
when_to_use: Before committing changes, security reviews, after adding new services, validating .env files
script: scripts/validate-secrets.sh
---

# Validate Secrets

Validates secrets configuration and identifies security issues.

## When to Use

- Before committing changes
- Security reviews
- After adding new services
- Validating .env file configuration
- Pre-deployment checks

## Usage

```bash
bash scripts/validate-secrets.sh
```

## What It Checks

- **Hardcoded credentials** - Passwords in docker-compose.yml files
- **.env file permissions** - Ensure secure file permissions (600)
- **Default passwords** - Common weak passwords in templates
- **.gitignore configuration** - Ensures .env files are ignored
- **Secrets in environment variables** - Validates proper secret management

## Output

- ✓ **Green checkmarks** - Secrets properly configured
- ! **Yellow warnings** - Issues to review
- ✗ **Red errors** - Critical security problems

## Common Issues

### Hardcoded Credentials

**Problem**: Passwords or API keys in docker-compose.yml files

**Fix**: Use `fix-hardcoded-credentials` tool

### Insecure .env Permissions

**Problem**: .env files readable by others

**Fix**:
```bash
chmod 600 apps/*/.env
```

### Missing .gitignore Entry

**Problem**: .env files not in .gitignore

**Fix**: Add to `.gitignore`:
```
apps/*/.env
```

## Related Tools

- `security-audit` - Comprehensive security audit
- `fix-hardcoded-credentials` - Fix hardcoded credentials

