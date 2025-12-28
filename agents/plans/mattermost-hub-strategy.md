# Mattermost as Centralized Communication Hub

**Status**: Planning
**Created**: 2025-12-28
**Related Tasks**: home-server-a4b (self-hosted push proxy research)

## Vision

Use Mattermost as the centralized hub for:
1. Server status notifications
2. AI agents posting messages (as bot users)
3. Agent-to-agent communication (human observable)
4. Documentation and resource links
5. Human user communication, voice calls, and coordination

## Use Cases & Feasibility

| Use Case | Mattermost Support | Complexity |
|----------|-------------------|------------|
| Server status notifications | Incoming webhooks | Low |
| AI agents as bots | Bot accounts + REST API | Medium |
| Agent-to-agent observability | Channels + threads | Medium |
| Documentation hub | Pinned posts, bookmarks | Low |
| Human users + voice | Multi-user + Calls plugin | Low-Medium |

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Mattermost                           │
├─────────────────────────────────────────────────────────┤
│  #alerts          - Server notifications (webhook)     │
│  #agent-activity  - AI agents posting status/logs      │
│  #agent-collab    - Agent-to-agent (human observable)  │
│  #resources       - Pinned docs, links, guides         │
│  #general         - Human discussion                   │
│  Town Square      - General coordination               │
└─────────────────────────────────────────────────────────┘
         ▲                    ▲                  ▲
         │                    │                  │
    Webhooks            Bot API calls        Human users
    (simple POST)      (Personal Access      (web/mobile)
                        Tokens)
```

## Potential Blockers & Gaps

### 1. Bot Authentication
- Each agent needs a bot account + Personal Access Token
- Tokens don't expire by default (good), but need secure storage
- Decision needed: Where do agents get their tokens? `.env` files? Secrets manager?

### 2. Agent-to-Agent Noise
- If agents chat frequently, could drown out human messages
- Mitigations:
  - Dedicated channels for agent activity
  - Use threading to group related messages
  - Message collapsing for verbose logs
- Consider: Retention policies to auto-delete old bot messages

### 3. Calls Plugin
- Included in Team Edition, but needs explicit setup
- For remote calls: Requires TURN/STUN server for NAT traversal
- For LAN-only: Works out of box, simpler setup

### 4. Rate Limits
- Default: 10 requests/second per user
- Heavy agent activity might need tuning
- Config: `MM_RATELIMITSETTINGS_PERSEC` can adjust

### 5. Search Pollution
- Lots of automated messages = harder to find human conversations
- Mitigations:
  - Prefix bot messages with consistent format
  - Use specific channels per bot/purpose
  - Leverage threads for related messages

### 6. Storage Growth
- Agent conversations accumulate over time
- Plan for: Data retention policies or periodic cleanup
- Monitor: PostgreSQL volume size

### 7. Claude Code Integration
Options for integration:
- **Simple**: Webhook URL for one-way notifications
- **Medium**: Bot account + Personal Access Token for posting
- **Advanced**: MCP server for bidirectional communication

## Questions to Resolve

1. **Agent inventory**: Which agents will post? Claude Code, trading bot, monitoring scripts, others?
2. **Message volume**: Occasional status updates vs. continuous logging?
3. **Bidirectional**: Do agents need to *read* messages, or just post?
4. **Voice scope**: LAN only, or need remote access?
5. **User base**: Family/friends, or technical collaborators?

## Implementation Phases

### Phase 1: Foundation
- [ ] Deploy current config changes (basic auth removal, TPNS, telemetry)
- [ ] Create channel structure (#alerts, #agent-activity, #resources)
- [ ] Set up first incoming webhook for testing
- [ ] Document webhook URL storage (secrets management)

### Phase 2: Bot Integration
- [ ] Create bot account for first agent (e.g., server-monitor)
- [ ] Generate and securely store Personal Access Token
- [ ] Build simple notification script using webhook
- [ ] Test rate limits with realistic load

### Phase 3: Agent Communication
- [ ] Define agent-to-agent protocol (message format, threading)
- [ ] Create dedicated channels for agent collaboration
- [ ] Implement first agent-to-agent use case
- [ ] Add human subscription/muting options

### Phase 4: Human Experience
- [ ] Set up Calls plugin for voice/video
- [ ] Configure TURN/STUN if remote access needed
- [ ] Invite additional human users
- [ ] Create onboarding documentation

### Phase 5: Refinement
- [ ] Implement data retention policies
- [ ] Tune rate limits based on usage
- [ ] Add search filters/saved searches for humans
- [ ] Monitor and optimize storage

## Quick Wins (Start Here)

1. **Incoming webhook for #alerts** - Any script can POST notifications
2. **Create first bot account** - Test API integration
3. **Organize channels** - Set up structure before content floods in
4. **Enable Calls plugin** - If voice is priority

## Current Configuration

Mattermost is configured with:
- TPNS for mobile push notifications
- Telemetry/diagnostics disabled
- No Traefik basic auth (Mattermost handles auth)
- PostgreSQL + Redis backend

See: `apps/mattermost/docker-compose.yml`

## Related Resources

- [Mattermost Incoming Webhooks](https://developers.mattermost.com/integrate/webhooks/incoming/)
- [Mattermost Bot Accounts](https://developers.mattermost.com/integrate/reference/bot-accounts/)
- [Mattermost REST API](https://api.mattermost.com/)
- [Calls Plugin](https://docs.mattermost.com/configure/calls-deployment.html)
