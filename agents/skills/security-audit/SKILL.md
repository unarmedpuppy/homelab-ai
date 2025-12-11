---
name: security-audit
description: Comprehensive security audit of server infrastructure
when_to_use: Regular security checks, before deployments, after system changes, security reviews
script: scripts/security-audit.sh
---

# Security Audit

Comprehensive security audit of the home server infrastructure.

## When to Use

- Regular security checks (monthly recommended)
- Before major deployments
- After system changes
- Security reviews
- Compliance checks

## Usage

```bash
# From local machine
bash scripts/security-audit.sh

# On server
bash scripts/connect-server.sh "~/server/scripts/security-audit.sh"
```

## What It Checks

- **Hardcoded credentials** - Passwords in docker-compose files
- **Container security** - Root users, privileged containers
- **Secrets management** - .env files, .gitignore configuration
- **Git security** - Committed secrets, .gitignore coverage
- **Intrusion prevention** - fail2ban status
- **Resource limits** - Memory/CPU constraints
- **Network security** - Exposed ports, firewall rules
- **Default credentials** - Common weak passwords

## Output

- ✓ **Green checkmarks** - Security checks passing
- ! **Yellow warnings** - Issues to review
- ✗ **Red errors** - Critical security problems requiring immediate action

## After Running

1. **Review findings** - Check all warnings and errors
2. **Prioritize fixes** - Address critical issues first
3. **Use related tools**:
   - `validate-secrets` - Validate secrets configuration
   - `fix-hardcoded-credentials` - Fix credential issues
4. **Document fixes** - Update security documentation

## Related Documentation

- `agents/reference/security/SECURITY_AUDIT.md` - Complete audit findings
- `agents/reference/security/SECURITY_IMPLEMENTATION.md` - Implementation guides

## Related Tools

- `validate-secrets` - Validate secrets configuration
- `fix-hardcoded-credentials` - Fix hardcoded credentials

