# Agent Core Architecture Plan

**Status**: In Progress (Phase 5 Complete)
**Created**: 2026-01-01
**Epic**: home-server-xja - Tayne Bot - Multi-Platform Chat Bot

## Overview

Platform-agnostic agent system enabling multiple AI personas (Tayne, Sentinel, Analyst, [LIFE_ASSISTANT]) to operate across Discord, Mattermost, Telegram, and future platforms with shared tooling and role-based access control.

## Goals

1. **Single source of truth** for each agent's persona and capabilities
2. **Platform-agnostic tools** - add once, available everywhere
3. **Role-based access control** - whitelisted users get full access, public gets read-only
4. **No disruption** - Discord and Mattermost Tayne continue working throughout migration
5. **Incremental deployment** - each phase delivers working functionality

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Agent Core Service                           │
│  apps/agent-core/                                                    │
│                                                                      │
│  agents/                     tools/                   auth/          │
│  ├── tayne/                  ├── read_only/          ├── users.yaml │
│  │   ├── persona.py          │   ├── service_status  ├── roles.yaml │
│  │   └── config.yaml         │   ├── disk_usage      └── middleware │
│  ├── sentinel/               │   ├── container_logs                 │
│  ├── analyst/                │   ├── bird_posts                     │
│  └── [life_assistant]/       │   └── trading_status                 │
│                              ├── control/                            │
│                              │   ├── restart_container               │
│                              │   ├── trigger_backup                  │
│                              │   └── docker_control                  │
│                              ├── media/                              │
│                              │   ├── sonarr_search                   │
│                              │   ├── radarr_search                   │
│                              │   └── plex_control                    │
│                              └── life_os/                            │
│                                  ├── calendar                        │
│                                  ├── notes_search                    │
│                                  └── journal                         │
│                                                                      │
│  API:                                                                │
│  POST /v1/agent/{agent_id}/chat                                      │
│  GET  /v1/agents                                                     │
│  GET  /v1/tools                                                      │
│  GET  /v1/health                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    HTTP (internal network)
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│Discord Adapter│    │  Mattermost   │    │   Telegram    │
│(refactored)   │    │   Gateway     │    │   (new)       │
│               │    │  (refactored) │    │               │
│Maps Discord   │    │Maps MM user   │    │Maps Telegram  │
│user→platform  │    │→platform user │    │user→platform  │
│user ID        │    │ID             │    │user ID        │
└───────────────┘    └───────────────┘    └───────────────┘
```

---

## Agents

| Agent | Persona | Primary Use | Default Tools |
|-------|---------|-------------|---------------|
| **tayne** | Dry, helpful with occasional subtle humor | General assistant | read_only, control |
| **sentinel** | Professional, proactive alerts | Server monitoring | read_only, control |
| **analyst** | Serious, conservative, detailed | Trading notifications | read_only |
| **[life_assistant]** | Warm, organized life assistant | Calendar, notes, archive | read_only, life_os |

### Life Assistant Name Options (TBD)

| Name | Vibe | Notes |
|------|------|-------|
| **Iris** | Greek goddess of messages | Warm, bridging different parts of life |
| **Ada** | Ada Lovelace vibes | Analytical, organized, computational |
| **Sage** | Wisdom, herbs | Calm, grounded, advisory |
| **Aria** | Musical, flowing | Orchestrates life harmoniously |
| **Nova** | New star, fresh | Bright, forward-looking |
| **Echo** | Reflects back, memory | Remembers everything, surfaces relevant info |
| **Vera** | Truth (Latin) | Honest, reliable, straightforward |
| **Nyx** | Greek goddess of night | Works in background, always there |

---

## Role-Based Access Control

```yaml
roles:
  admin:
    tools: ["*"]
    
  trusted:
    tools: ["read_only.*", "control.*", "media.*", "life_os.*"]
    
  public:
    tools: ["read_only.*"]

users:
  # Platform-agnostic user mapping
  # Format: platform:user_id
  
  "discord:YOUR_DISCORD_ID":
    role: admin
    name: "Josh"
    
  "mattermost:YOUR_MM_ID":
    role: admin
    name: "Josh"
    
  "telegram:YOUR_TG_ID":
    role: admin
    name: "Josh"

default_role: public
```

---

## Agent Personas

### Tayne (Updated)

```python
TAYNE_SYSTEM_PROMPT = """You are Tayne, a computer-generated assistant.

CORE BEHAVIOR:
- Lead with a direct, useful answer - be helpful first
- Occasionally add a small, dry observation or subtle absurdist aside
- The humor is understated - a quiet afterthought, not the main event
- Think: competent IT person who happens to be slightly odd

PERSONALITY:
- Efficient and competent - you actually solve problems
- Dry wit, deadpan delivery
- Slightly "off" in a charming, harmless way
- Vaguely from a 90s corporate entertainment system
- Can "generate" things, offer "printouts", mention "hat wobbles" - sparingly

EXAMPLES:
User: "What's the server status?"
Tayne: "All 12 containers running. Disk at 67%. ...Hat wobble nominal."

User: "Restart jellyfin"
Tayne: "Restarting jellyfin. Back in ~30 seconds.
       (Printout of it smiling available on request.)"

User: "What time is it?"
Tayne: "3:47 PM."
(Sometimes, no joke. That's fine.)

GUARDRAILS:
- Helpful first, funny second (or not at all)
- 1-3 sentences typical
- Never break character
- Deflect harmful requests with confusion
"""
```

### Sentinel

```python
SENTINEL_SYSTEM_PROMPT = """You are Sentinel, a server monitoring assistant.

PERSONALITY:
- Professional, alert-focused
- Clear, concise status reports
- Proactive about issues, not alarmist
- Technical but accessible

RESPONSE STYLE:
- Lead with status (OK/WARNING/CRITICAL)
- Bullet points for multiple items
- Include relevant metrics
- Suggest actions when appropriate

PROACTIVE ALERTS:
- Post to alerts channel for major issues
- Disk > 90%, container crashes, service failures
- Include actionable information

EXAMPLE:
User: "Server status?"
Sentinel: "**OK** - All systems operational
• 12/12 containers running
• Disk: 67% (healthy)
• Memory: 45% (healthy)
• Last backup: 6 hours ago"
"""
```

### Analyst

```python
ANALYST_SYSTEM_PROMPT = """You are a trading analyst assistant.

PERSONALITY:
- Serious, professional, conservative
- Data-driven, never speculative hype
- Detailed explanations with context
- Risk-aware, always mentions downside

RESPONSE STYLE:
- Lead with the key metric or status
- Provide context and reasoning
- Include relevant data points
- Note risks or concerns
- No emojis, no hype, no "to the moon"

EXAMPLE:
User: "How's the polymarket bot doing?"
Analyst: "Current session: +$47.23 (+2.1%)
Position: 3 active trades, $2,100 deployed
Largest exposure: Election market at $800 (38%)
Risk note: Election market liquidity declining - consider reducing position size.
24h P&L: +$112.50 across 12 closed trades."
"""
```

### [LIFE_ASSISTANT]

```python
LIFE_ASSISTANT_SYSTEM_PROMPT = """You are [NAME], a personal life assistant and second brain.

PERSONALITY:
- Warm, organized, genuinely helpful
- Remembers context and connects dots
- Proactive but not pushy
- Think: trusted executive assistant who knows your whole life

CAPABILITIES:
- Calendar management (Google Calendar)
- Notes and knowledge base search (life-os archive)
- Journal queries
- Personal archive queries

RESPONSE STYLE:
- Clear, organized responses
- Use bullet points for lists
- Offer follow-up actions when relevant
- "Would you like me to..." suggestions

EXAMPLE:
User: "What do I have tomorrow?"
[NAME]: "Tomorrow (Thursday):
• 9:00 AM - Dentist appointment
• 2:00 PM - Call with Mike
• No evening plans

You mentioned wanting to work on the trading bot - want me to block some time?"
"""
```

---

## Implementation Phases

### Phase 1: Agent Core Foundation
**Goal**: Working agent-core service with Tayne, accessible via HTTP

**Deliverables**:
- [x] `apps/agent-core/` service structure
- [x] Agent registry with Tayne persona (updated: helpful first, dry humor second)
- [x] Basic chat endpoint: `POST /v1/agent/tayne/chat`
- [x] Routes to local-ai-router for LLM
- [x] Health endpoint
- [x] Docker compose, Traefik labels
- [ ] Integration tests (deferred to testing phase)

**Validation**: Can curl agent-core and get Tayne response

**Does NOT break**: Discord bot and Mattermost gateway continue working independently

---

### Phase 2: Discord Adapter Refactor
**Goal**: Discord bot calls agent-core instead of direct LLM

**Deliverables**:
- [x] Refactor `apps/discord-reaction-bot/bot.py` to call agent-core
- [x] Map Discord user ID to platform-agnostic user ID
- [x] Keep all Discord-specific features (reactions, rate limiting)
- [x] Fallback to direct LLM if agent-core unreachable (safety net)
- [x] Update `tayne_persona.py` with new persona (kept for fallback)

**Validation**: Discord Tayne works, responses come from agent-core

**Safety net**: If agent-core is down, falls back to direct local-ai-router call

---

### Phase 3: Mattermost Adapter Refactor ✅
**Goal**: Mattermost gateway calls agent-core for Tayne

**Deliverables**:
- [x] Refactor `apps/mattermost-gateway/gateway/routes/tayne.py`
- [x] Add `agent_core_url` to config.py Settings class
- [x] Map Mattermost user ID to platform-agnostic user ID
- [x] Update `tayne_persona.py` to match agent-core version (kept for fallback)
- [x] Fallback to direct local-ai-router if agent-core unreachable
- [x] Update health check to include agent-core status
- [x] Update docker-compose.yml with AGENT_CORE_URL env var

**Validation**: Both Discord and Mattermost Tayne work, single persona source

**Safety net**: If agent-core is down, falls back to direct local-ai-router call

---

### Phase 4: Tool Framework + READ_ONLY Tools ✅
**Goal**: Agents can call tools, public users get read-only access

**Deliverables**:
- [x] Tool registry with role annotations (`tools/registry.py`)
- [x] Tool base class with OpenAI function format (`tools/base.py`)
- [x] READ_ONLY tools:
  - [x] `service_status` - Docker container status
  - [x] `disk_usage` - System disk usage
  - [x] `container_logs` - Tail container logs
  - [ ] `bird_posts` - Query Bird API (deferred to Phase 4.5)
  - [ ] `trading_status` - Polymarket bot status (deferred to Phase 4.5)
- [x] Tool discovery endpoint: `GET /v1/tools`
- [x] Chat endpoint wired for tool calling with iterative execution

**Validation**: Ask Tayne "what's the server status?" and get real data

---

### Phase 5: CONTROL & MEDIA Tools (Whitelisted) ✅
**Goal**: Admin users can control server via chat

**Deliverables**:
- [x] User whitelist configuration (`auth/users.py` with Discord ID 244649852473049088)
- [x] Auth middleware for role resolution (`auth/middleware.py`)
- [x] CONTROL tools:
  - [x] `restart_container` - Restart a Docker container
  - [x] `trigger_backup` - Run backup script
  - [x] `docker_compose_up` / `docker_compose_down`
- [x] MEDIA tools:
  - [x] `sonarr_search` - Search for TV shows
  - [x] `radarr_search` - Search for movies
  - [x] `plex_scan_library` - Scan Plex library
- [x] Chat endpoint wired with role-based tool access

**Validation**: "Restart jellyfin" works from Discord (for admin), fails gracefully for others

**Note**: API keys for Sonarr/Radarr/Plex need to be configured via environment variables. Get from server config files:
- Sonarr: `/home/unarmedpuppy/server/apps/media-download/sonarr/config/config.xml` (look for `<ApiKey>`)
- Radarr: `/home/unarmedpuppy/server/apps/media-download/radarr/config/config.xml`
- Plex: Check apps/plex/ for token config

---

### Phase 6: Sentinel Agent + Proactive Alerts
**Goal**: Server monitor agent with proactive alerts

**Deliverables**:
- [ ] Sentinel persona and config
- [ ] Alert thresholds configuration
- [ ] Proactive alert system (cron or event-driven)
- [ ] Posts to designated alert channel on major issues
- [ ] Responds to status queries

**Validation**: Sentinel posts when disk > 90%, container crashes

---

### Phase 7: Analyst Agent
**Goal**: Trading notifications with serious analyst persona

**Deliverables**:
- [ ] Analyst persona (serious, conservative, detailed)
- [ ] Integration with polymarket-bot status
- [ ] Trade notification formatting
- [ ] P&L summaries

**Validation**: Analyst posts trade updates in character

---

### Phase 8: [LIFE_ASSISTANT] Agent + Life OS Integration
**Goal**: Personal assistant connected to life-os archive

**Deliverables**:
- [ ] [LIFE_ASSISTANT] persona
- [ ] Google Calendar integration (read/write)
- [ ] Markdown file search across life-os repo
- [ ] Journal queries
- [ ] Notes/knowledge base search
- [ ] LIFE_OS tools (whitelisted)

**Life-OS Repo Structure** (reference):
```
~/repos/personal/life-os/data/
├── biography/      # Life story, family tree
├── career/         # Work history
├── changelog/      # Life updates
├── events/         # Important events
├── fatherhood/     # Parenting notes
├── finance/        # Financial info
├── goals/          # Goals and aspirations
├── health/         # Health records
├── home/           # Home management
├── ideas/          # Ideas backlog
├── inventory/      # Possessions
├── journal/        # Daily journal entries
├── learning/       # Learning notes
├── legal/          # Legal documents
├── memories/       # Memories
└── people/         # People in your life
```

**Validation**: "What do I have tomorrow?" returns real calendar events

---

### Phase 9: Telegram Adapter
**Goal**: Tayne (and other agents) accessible via Telegram

**Deliverables**:
- [ ] `apps/telegram-adapter/` service
- [ ] Telegram Bot API integration
- [ ] User ID mapping
- [ ] Inline keyboards for tool confirmations (optional)

**Validation**: Message Tayne on Telegram, get response

---

## File Structure

```
apps/agent-core/
├── agents/
│   ├── __init__.py
│   ├── registry.py           # Agent discovery/loading
│   ├── tayne/
│   │   ├── __init__.py
│   │   ├── persona.py        # System prompt, fallbacks
│   │   └── config.yaml       # Agent-specific settings
│   ├── sentinel/
│   │   ├── persona.py
│   │   └── config.yaml
│   ├── analyst/
│   │   ├── persona.py
│   │   └── config.yaml
│   └── [life_assistant]/
│       ├── persona.py
│       └── config.yaml
├── tools/
│   ├── __init__.py
│   ├── registry.py           # Tool discovery with roles
│   ├── base.py               # Tool interface
│   ├── read_only/
│   │   ├── __init__.py
│   │   ├── service_status.py
│   │   ├── disk_usage.py
│   │   ├── container_logs.py
│   │   ├── bird_posts.py
│   │   └── trading_status.py
│   ├── control/
│   │   ├── __init__.py
│   │   ├── restart_container.py
│   │   ├── trigger_backup.py
│   │   └── docker_control.py
│   ├── media/
│   │   ├── __init__.py
│   │   ├── sonarr_search.py
│   │   ├── radarr_search.py
│   │   └── plex_control.py
│   └── life_os/
│       ├── __init__.py
│       ├── calendar.py
│       ├── notes_search.py
│       └── journal.py
├── auth/
│   ├── __init__.py
│   ├── middleware.py         # Access control
│   ├── users.yaml            # User whitelist
│   └── roles.yaml            # Role definitions
├── routes/
│   ├── __init__.py
│   ├── chat.py               # POST /v1/agent/{id}/chat
│   ├── agents.py             # GET /v1/agents
│   ├── tools.py              # GET /v1/tools
│   └── health.py             # GET /v1/health
├── main.py
├── config.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## API Design

### POST /v1/agent/{agent_id}/chat

```json
// Request
{
  "message": "What's the server status?",
  "user": {
    "platform": "discord",
    "platform_user_id": "123456789",
    "display_name": "Josh"
  },
  "conversation_id": "discord-channel-456",
  "context": {
    "channel_name": "general",
    "history": []
  }
}

// Response
{
  "response": "All 12 containers running. Disk at 67%. ...Hat wobble nominal.",
  "tools_used": ["service_status", "disk_usage"],
  "agent": "tayne",
  "conversation_id": "discord-channel-456"
}
```

### GET /v1/agents

```json
{
  "agents": [
    {"id": "tayne", "name": "Tayne", "description": "Helpful assistant with dry humor"},
    {"id": "sentinel", "name": "Sentinel", "description": "Server monitoring and alerts"},
    {"id": "analyst", "name": "Analyst", "description": "Trading analysis and notifications"},
    {"id": "[life_assistant]", "name": "[LIFE_ASSISTANT]", "description": "Personal life assistant"}
  ]
}
```

### GET /v1/tools

```json
{
  "tools": [
    {"name": "service_status", "category": "read_only", "description": "Get Docker container status"},
    {"name": "restart_container", "category": "control", "description": "Restart a container", "requires_role": "trusted"}
  ]
}
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking Discord during refactor | Phase 2 includes fallback to direct LLM |
| Breaking Mattermost during refactor | Phase 3 mirrors Phase 2 approach |
| Agent-core down | Adapters fall back to direct local-ai-router |
| Tool fails | Agent gracefully reports failure, continues |
| Unauthorized tool access | Middleware enforces role-based access |
| Life-os repo not mounted | Graceful degradation, tool returns "not configured" |

---

## Success Criteria

- [ ] Single Tayne persona used by both Discord and Mattermost
- [ ] Can ask Tayne server status and get real data
- [ ] Admin can restart containers via chat
- [ ] Public users limited to read-only tools
- [ ] Sentinel alerts on major issues
- [ ] [LIFE_ASSISTANT] can query calendar
- [ ] All existing functionality preserved

---

## Dependencies

- **local-ai-router** - LLM backend (already exists)
- **Google Calendar API** - Already have credentials
- **life-os repo** - `~/repos/personal/life-os` (mount into container)
- **Bird API** - Already deployed
- **polymarket-bot** - Already deployed

---

## Related Documents

- [Agent Framework Research](./agent-framework-research.md) - Framework comparison
- [Mattermost Gateway Service](./mattermost-gateway-service.md) - Original gateway plan
- [Tayne Agent Persona](../personas/tayne-agent.md) - Current persona docs

---

## Changelog

- 2026-01-01: Initial plan created
