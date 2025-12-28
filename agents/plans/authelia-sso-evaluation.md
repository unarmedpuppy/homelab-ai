# Authelia SSO/2FA Evaluation

**Status**: Planned
**Beads Epic**: `home-server-9o6`
**Goal**: Evaluate and potentially deploy Authelia for centralized authentication

## Overview

Replace per-service Traefik basic auth with Authelia for:
- Single Sign-On (SSO) across all services
- Two-Factor Authentication (2FA/MFA)
- Session management and timeout policies
- Better security than basic auth

## Current State

Services use Traefik basic auth labels:
```yaml
- "traefik.http.middlewares.n8n-auth.basicauth.users=unarmedpuppy:$$apr1$$..."
```

**Problems with basic auth:**
- Re-enter password for each service
- No 2FA option
- Passwords sent with every request (even if hashed)
- No session timeout/management

## What Authelia Provides

### Authentication Methods
- Local users (file-based or LDAP)
- 2FA via TOTP (authenticator apps), WebAuthn (hardware keys), or Duo
- Password reset flows

### Access Control
- Per-service access policies
- IP-based rules
- Time-based restrictions
- User/group-based permissions

### Session Management
- Configurable session timeouts
- Remember me functionality
- Session invalidation

## Architecture

```
User Request
     │
     ▼
┌─────────┐     ┌──────────┐     ┌─────────────┐
│ Traefik │────►│ Authelia │────►│   Service   │
└─────────┘     └──────────┘     └─────────────┘
                     │
                     ▼
               ┌──────────┐
               │  Redis   │ (session store)
               │  SQLite  │ (user DB)
               └──────────┘
```

## Traefik Integration

```yaml
# Authelia forward auth middleware
- "traefik.http.middlewares.authelia.forwardauth.address=http://authelia:9091/api/verify?rd=https://auth.server.unarmedpuppy.com"
- "traefik.http.middlewares.authelia.forwardauth.trustForwardHeader=true"
- "traefik.http.middlewares.authelia.forwardauth.authResponseHeaders=Remote-User,Remote-Groups,Remote-Name,Remote-Email"

# Apply to services
- "traefik.http.routers.n8n.middlewares=authelia"
```

## Evaluation Criteria

1. **Complexity** - How much configuration is needed?
2. **Migration path** - Can we migrate service by service?
3. **Mobile apps** - Do Vaultwarden, Home Assistant apps work with it?
4. **Recovery** - What happens if Authelia is down?
5. **Essential service?** - Should it be in failover set?

## Concerns

### App Compatibility
Some apps have their own auth (Vaultwarden, Home Assistant). Options:
- Skip Authelia for these (they have built-in 2FA)
- Use Authelia as additional layer
- Bypass Authelia for local network

### Cloudflare Tunnel
Need to ensure Authelia works with Cloudflare Tunnel's request flow.

### Vendor Lock-in Alternative
If reducing Cloudflare dependency, Wireguard + Authelia provides:
- VPN for remote access (Wireguard)
- SSO/2FA for web services (Authelia)
- No external dependencies

## Implementation Steps

1. [ ] Deploy Authelia in test mode (parallel to basic auth)
2. [ ] Configure local user database
3. [ ] Set up 2FA (TOTP initially)
4. [ ] Migrate one low-risk service (e.g., homepage)
5. [ ] Test with Cloudflare Tunnel
6. [ ] Migrate remaining services incrementally
7. [ ] Remove basic auth middleware from Traefik

## Resources

- [Authelia Docs](https://www.authelia.com/docs/)
- [Traefik Integration](https://www.authelia.com/integration/proxies/traefik/)
- [Docker Compose Examples](https://github.com/authelia/authelia/tree/master/examples/compose)
