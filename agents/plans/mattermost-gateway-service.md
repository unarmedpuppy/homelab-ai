# Mattermost Gateway Service

**Status**: Planning
**Created**: 2025-12-28
**Parent Plan**: [mattermost-hub-strategy.md](mattermost-hub-strategy.md)

## Overview

A lightweight HTTP gateway that allows any service to interact with Mattermost through registered bot identities. Acts as a centralized integration point for all bot communications.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Internal Services                            │
├──────────┬──────────┬──────────┬──────────┬────────────────────┤
│ Trading  │ Server   │ Claude   │ Cron     │ Other              │
│ Bot      │ Monitor  │ Agent    │ Jobs     │ Services           │
└────┬─────┴────┬─────┴────┬─────┴────┬─────┴──────┬─────────────┘
     │          │          │          │            │
     └──────────┴──────────┴──────────┴────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  Mattermost Gateway    │
              │  (FastAPI service)     │
              │                        │
              │  Endpoints:            │
              │  POST /post            │
              │  POST /react           │
              │  GET  /messages        │
              │  POST /webhook/:bot    │
              │  GET  /health          │
              │                        │
              │  Bot Registry:         │
              │  - tayne (assistant)   │
              │  - server-monitor      │
              │  - trading-bot         │
              │  - claude-agent        │
              └───────────┬────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │     Mattermost         │
              │  (existing service)    │
              └────────────────────────┘
```

## Bot Registry

### Tayne (First Bot)
- **Purpose**: General personal assistant - entry point for humans
- **Capabilities**:
  - Answer questions about server status
  - Look up calendar events
  - Search documentation
  - Take actions on the server (via integrations)
  - Route requests to specialized bots
- **Avatar**: TBD (maybe the Tayne character from Tim & Eric?)
- **Token**: Stored in `.env` (MATTERMOST_BOT_TAYNE_TOKEN)

### Future Bots (Planned)
| Bot Name | Purpose | Token Env Var |
|----------|---------|---------------|
| server-monitor | System alerts, health checks | MATTERMOST_BOT_MONITOR_TOKEN |
| trading-bot | Trading notifications, status | MATTERMOST_BOT_TRADING_TOKEN |
| claude-agent | AI agent activity, logs | MATTERMOST_BOT_CLAUDE_TOKEN |

## API Design

### POST /post
Post a message as a specific bot.

```bash
curl -X POST http://mattermost-gateway:8000/post \
  -H "Content-Type: application/json" \
  -d '{
    "bot": "tayne",
    "channel": "general",
    "message": "Hello! How can I help you today?",
    "props": {}
  }'
```

**Parameters:**
- `bot` (required): Bot identity to use (must be registered)
- `channel` (required): Channel name or ID
- `message` (required): Message content (supports markdown)
- `props` (optional): Mattermost post props (attachments, etc.)
- `thread_id` (optional): Reply to a specific thread

### POST /react
Add a reaction to a message.

```bash
curl -X POST http://mattermost-gateway:8000/react \
  -H "Content-Type: application/json" \
  -d '{
    "bot": "tayne",
    "post_id": "abc123",
    "emoji": "thumbsup"
  }'
```

### GET /messages
Read messages from a channel.

```bash
curl "http://mattermost-gateway:8000/messages?channel=alerts&limit=10"
```

**Parameters:**
- `channel` (required): Channel name or ID
- `limit` (optional): Number of messages (default: 50)
- `since` (optional): Timestamp to fetch messages after
- `bot` (optional): Which bot's token to use (default: first registered)

### POST /webhook/:bot
Simple webhook endpoint for dumb services (just POST text).

```bash
# Simple text posting
curl -X POST http://mattermost-gateway:8000/webhook/tayne \
  -H "Content-Type: text/plain" \
  -d "Backup completed successfully"

# With channel header
curl -X POST http://mattermost-gateway:8000/webhook/server-monitor \
  -H "Content-Type: text/plain" \
  -H "X-Channel: alerts" \
  -d "Disk usage at 85%"
```

### GET /health
Health check endpoint.

```bash
curl http://mattermost-gateway:8000/health
# {"status": "healthy", "bots": ["tayne"], "mattermost": "connected"}
```

## File Structure

```
apps/mattermost-gateway/
├── gateway/
│   ├── __init__.py
│   ├── main.py           # FastAPI app
│   ├── config.py         # Settings, bot registry
│   ├── mattermost.py     # Mattermost client wrapper
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── posts.py      # /post, /react endpoints
│   │   ├── messages.py   # /messages endpoint
│   │   └── webhooks.py   # /webhook/:bot endpoint
│   └── models.py         # Pydantic models
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Configuration

### Environment Variables (.env)

```bash
# Mattermost connection
MATTERMOST_URL=mattermost.server.unarmedpuppy.com
MATTERMOST_SCHEME=https
MATTERMOST_PORT=443

# Bot tokens (add more as needed)
MATTERMOST_BOT_TAYNE_TOKEN=<token>
MATTERMOST_BOT_MONITOR_TOKEN=<token>
MATTERMOST_BOT_TRADING_TOKEN=<token>

# Gateway settings
GATEWAY_PORT=8000
GATEWAY_LOG_LEVEL=INFO
DEFAULT_CHANNEL=town-square

# Optional: Channel name to ID mapping cache
CHANNEL_CACHE_TTL=300
```

### Bot Registry (config.py)

```python
BOTS = {
    "tayne": {
        "token_env": "MATTERMOST_BOT_TAYNE_TOKEN",
        "description": "Personal assistant bot",
        "default_channel": "general",
    },
    "server-monitor": {
        "token_env": "MATTERMOST_BOT_MONITOR_TOKEN",
        "description": "System monitoring alerts",
        "default_channel": "alerts",
    },
    # ... more bots
}
```

## Docker Compose

```yaml
services:
  mattermost-gateway:
    build: .
    container_name: mattermost-gateway
    restart: unless-stopped
    environment:
      - MATTERMOST_URL=${MATTERMOST_URL}
      - MATTERMOST_BOT_TAYNE_TOKEN=${MATTERMOST_BOT_TAYNE_TOKEN}
      # ... other env vars
    ports:
      - "8000:8000"  # Internal only, no Traefik exposure
    networks:
      - my-network
    depends_on:
      - mattermost
    labels:
      - "homepage.group=Infrastructure"
      - "homepage.name=Mattermost Gateway"
      - "homepage.icon=mdi-api"
      - "homepage.description=Bot message gateway"

networks:
  my-network:
    external: true
```

## Security Considerations

1. **Internal only** - No Traefik exposure, only accessible from Docker network
2. **Token storage** - All tokens in `.env`, gitignored
3. **No auth on gateway** - Trusts internal network (add API key if needed later)
4. **Rate limiting** - Consider adding per-bot rate limits
5. **Input validation** - Sanitize messages before posting

## Implementation Phases

### Phase 1: Core Gateway
- [ ] Create project structure
- [ ] Implement POST /post endpoint
- [ ] Implement GET /health endpoint
- [ ] Register Tayne bot
- [ ] Docker setup
- [ ] Test posting to Mattermost

### Phase 2: Extended Features
- [ ] Implement POST /react endpoint
- [ ] Implement GET /messages endpoint
- [ ] Implement POST /webhook/:bot endpoint
- [ ] Channel name → ID resolution with caching
- [ ] Add logging and error handling

### Phase 3: Tayne Intelligence
- [ ] WebSocket listener for mentions
- [ ] Route @tayne messages to handler
- [ ] Integrate with Claude/LLM for responses
- [ ] Calendar integration
- [ ] Documentation search

### Phase 4: Additional Bots
- [ ] Add server-monitor bot
- [ ] Add trading-bot identity
- [ ] Add claude-agent identity
- [ ] Per-bot configuration and defaults

## Example Usage

### From Trading Bot (Python)
```python
import requests

def notify_trade(symbol, action, price):
    requests.post("http://mattermost-gateway:8000/post", json={
        "bot": "trading-bot",
        "channel": "trading",
        "message": f"📈 {action.upper()} {symbol} @ ${price}"
    })
```

### From Bash Script
```bash
#!/bin/bash
# backup-complete.sh
curl -s -X POST http://mattermost-gateway:8000/webhook/server-monitor \
  -H "X-Channel: alerts" \
  -d "✅ Backup completed: $(du -sh /backup | cut -f1)"
```

### From Cron Job
```cron
0 * * * * curl -s -X POST http://mattermost-gateway:8000/post \
  -H "Content-Type: application/json" \
  -d '{"bot":"server-monitor","channel":"alerts","message":"Hourly health check: OK"}'
```

## Design Decisions (Resolved)

### Authentication
**Decision**: Require API keys for all gateway endpoints.
- Even though we trust the internal network, use API keys for future compatibility
- Avoids having to reconsider networking later
- Each calling service gets its own API key

```bash
# Environment variable
GATEWAY_API_KEYS=trading-bot:key1,server-monitor:key2,claude-agent:key3

# Usage
curl -X POST http://mattermost-gateway:8000/post \
  -H "X-API-Key: key1" \
  -H "Content-Type: application/json" \
  -d '{"bot": "tayne", "channel": "general", "message": "Hello!"}'
```

### Real-Time Events
**Decision**: WebSocket listener for @mentions + on-demand responses.
- Gateway maintains persistent WebSocket connection to Mattermost
- Listens for @tayne mentions and routes to handler
- Also responds on-demand when other services call the API

### Tayne's Brain
**Decision**: Routes to local LLM via tiered routing system.

See: [local-ai-two-gpu-architecture.md](local-ai-two-gpu-architecture.md)

```
User @mentions Tayne in Mattermost
         │
         ▼
┌─────────────────────────┐
│  Mattermost Gateway     │
│  (WebSocket listener)   │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Local AI Router        │
│  (tiered routing)       │
│                         │
│  1. Small (3070) - fast │
│  2. Medium (3090) - big │
│  3. GLM-4.7 - fallback  │
│  4. Claude - optional   │
└───────────┬─────────────┘
            │
            ▼
    Response → Mattermost
```

**Integration points**:
- Gateway calls Local AI Router's OpenAI-compatible API
- Router handles model selection based on complexity
- Response posted back to Mattermost as Tayne

## Design Decisions (Continued)

### Message Queue
**Decision**: Fail fast - no buffering.
- If Mattermost is down, callers get an error immediately
- Keeps system simple and predictable
- Callers can implement their own retry logic if needed

### Rate Limiting
**Decision**: Start loose, tighten later if needed.
- Initial: High limits (100 req/min per caller?)
- Monitor usage patterns
- Adjust if issues arise

### Claude Path
**Decision**: Local AI Router makes the determination.
- Tayne doesn't explicitly choose Claude
- Router evaluates complexity and routes appropriately
- Claude is just another option in the tiered system (when available)

## Tayne's Capabilities (Decoupled)

**Key Insight**: Tayne's tools are NOT tied to Mattermost. They're a separate capability layer that Tayne (and other agents/interfaces) can use.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Interfaces                                │
├─────────────┬─────────────┬─────────────┬──────────────────────┤
│ Mattermost  │    CLI      │   API       │   Future UI          │
│ (via GW)    │             │             │                      │
└──────┬──────┴──────┬──────┴──────┬──────┴──────────┬───────────┘
       │             │             │                 │
       └─────────────┴─────────────┴─────────────────┘
                              │
                              ▼
       ┌──────────────────────────────────────────────┐
       │              Tayne Agent                      │
       │  (personality, context, conversation mgmt)   │
       └──────────────────────┬───────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       ┌────────────┐  ┌────────────┐  ┌────────────┐
       │ Local AI   │  │ Capability │  │  Memory/   │
       │ Router     │  │ Layer      │  │  Context   │
       │ (thinking) │  │ (tools)    │  │  Store     │
       └────────────┘  └────────────┘  └────────────┘
```

## Resolved Architecture Decisions

### Tayne Agent Location
**Decision**: Separate service, fully decoupled from interfaces.
- Tayne should work with Mattermost, Discord, Telegram, CLI, API, etc.
- No logic coupling to any specific interface
- Interface adapters (gateways) just translate to/from Tayne

### Memory & Context
**Decision**: PostgreSQL + pgvector for persistent memory with semantic search.
- Tayne remembers past conversations
- pgvector enables semantic search ("find similar conversations")
- Scales to millions of messages
- Single backup target: PostgreSQL → jenquist-cloud (pg_dump)
- Can add Redis cache layer later if performance requires

**TODO**: Research embedding models for semantic search
- Need embeddings to power "find similar" queries
- Options: Local model on 3070? API-based? Which model?
- Task to be created when implementing memory store

### Naming
**Decision**: `apps/agent-tools/` for shared capabilities.
- Tayne is just one persona that uses a subset of these tools
- Other agents/personas can use the same tools

### Calendar
**Decision**: Currently Google Calendar, researching self-hosted sync.
- Task created: `home-server-ryi` - Research self-hosted calendar with Google sync
- Options: Nextcloud Calendar, Baikal, Radicale, DAViCal
- Agent tools will abstract the calendar backend

## Full Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Interface Gateways                            │
├──────────────┬──────────────┬──────────────┬───────────────────────┤
│ Mattermost   │   Discord    │   Telegram   │   CLI / API           │
│ Gateway      │   Gateway    │   Gateway    │                       │
└──────┬───────┴──────┬───────┴──────┬───────┴───────────┬───────────┘
       │              │              │                   │
       └──────────────┴──────────────┴───────────────────┘
                               │
                               ▼
                ┌──────────────────────────┐
                │      Agent Service       │
                │  (Tayne + other personas)│
                │                          │
                │  - Personality/prompts   │
                │  - Conversation mgmt     │
                │  - Tool orchestration    │
                └────────────┬─────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
  ┌────────────┐      ┌────────────┐      ┌────────────┐
  │ Local AI   │      │ Agent      │      │  Memory    │
  │ Router     │      │ Tools      │      │  Store     │
  │            │      │            │      │            │
  │ 3070→3090  │      │ Calendar   │      │ PostgreSQL │
  │ →GLM-4.7   │      │ Server     │      │ or SQLite  │
  │ →Claude    │      │ Docs       │      │            │
  │            │      │ Deploy     │      │ Backup:    │
  │            │      │ etc.       │      │ jenquist-  │
  └────────────┘      └────────────┘      │ cloud      │
                                          └────────────┘
```

## Service Breakdown

| Service | Purpose | Location |
|---------|---------|----------|
| `mattermost-gateway` | Mattermost ↔ Agent translation | `apps/mattermost-gateway/` |
| `discord-gateway` | Discord ↔ Agent translation | `apps/discord-gateway/` (future) |
| `agent-service` | Tayne + personas, orchestration | `apps/agent-service/` |
| `agent-tools` | Shared capabilities (calendar, server, etc.) | `apps/agent-tools/` |
| `local-ai-router` | LLM routing (3070/3090/GLM/Claude) | `apps/local-ai-app/` (upgraded) |
| `memory-store` | Persistent conversation memory | TBD (maybe in agent-service) |

## apps/agent-tools/ Structure

```
apps/agent-tools/
├── tools/
│   ├── calendar.py        # Calendar (Google now, self-hosted later)
│   ├── server.py          # Server status, health checks
│   ├── documentation.py   # Search Wiki.js, local docs
│   ├── deployment.py      # Trigger deployments (with safety)
│   ├── weather.py         # Weather lookup (future)
│   └── __init__.py
├── api.py                 # FastAPI exposing tools as endpoints
├── registry.py            # Tool registry and metadata
├── docker-compose.yml
├── .env.example
└── README.md
```

**Tool Registry**:
| Tool | Description | Risk Level | Backend |
|------|-------------|------------|---------|
| `calendar.lookup` | Query calendar events | Low | Google Calendar (→ self-hosted) |
| `calendar.create` | Create calendar event | Medium | Google Calendar (→ self-hosted) |
| `server.status` | Get server/container status | Low | Docker API |
| `server.health` | Run health checks | Low | Health scripts |
| `docs.search` | Search documentation | Low | Wiki.js API |
| `deploy.status` | Check deployment status | Low | Git/Docker |
| `deploy.trigger` | Trigger deployment | High | Git pull + compose |

### Why This Architecture?

1. **Interface-agnostic** - Add Telegram, Slack, etc. without touching agent logic
2. **Persona-flexible** - Tayne, server-bot, trading-bot share tools but have different personalities
3. **Tool-composable** - Mix and match tools per persona
4. **Memory-persistent** - Full conversation history, backed up
5. **LLM-flexible** - Router decides which model, agents don't care

## Persona Definitions

**Location**: Personas live in `apps/agent-service/` as configuration.

```
apps/agent-service/
├── personas/
│   ├── tayne.yaml           # Tayne's personality, allowed tools
│   ├── server-monitor.yaml  # Server monitoring bot
│   └── trading-bot.yaml     # Trading notifications
├── agent/
│   ├── orchestrator.py      # Tool calling, conversation flow
│   └── memory.py            # PostgreSQL + pgvector integration
└── ...
```

**Persona Config Example** (`tayne.yaml`):
```yaml
name: tayne
display_name: "Tayne"
description: "Personal assistant for server management and general help"
system_prompt: |
  You are Tayne, a helpful personal assistant for managing a home server.
  You have access to tools for checking server status, searching documentation,
  managing calendar events, and triggering deployments.
  Be friendly, concise, and proactive about suggesting helpful actions.

allowed_tools:
  - calendar.*        # All calendar tools
  - server.*          # All server tools
  - docs.*            # All documentation tools
  - deploy.status     # Can check deploy status
  # deploy.trigger NOT allowed - requires elevated persona

default_channel: "general"
```

**Why in agent-service?**
- Personas are tightly coupled to agent orchestration logic
- Tool permissions are enforced by agent-service
- Avoids overhead of separate personas app
- Config files (YAML) keep it simple - no code for new personas

## Tool Permissions

**Decision**: Agent-service enforces permissions. Tools declare default levels.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Permission Flow                               │
├─────────────────────────────────────────────────────────────────┤
│  1. Request comes in: "@tayne deploy the trading bot"           │
│  2. Agent-service checks tayne.yaml → allowed_tools             │
│  3. deploy.trigger NOT in allowed_tools → DENIED                │
│  4. Response: "I can check deploy status, but triggering        │
│     deployments requires elevated access."                      │
└─────────────────────────────────────────────────────────────────┘
```

**Tool Permission Levels** (declared in agent-tools):
| Level | Description | Example Tools |
|-------|-------------|---------------|
| `general` | Safe, read-only | calendar.lookup, server.status, docs.search |
| `elevated` | Write operations | calendar.create, deploy.trigger |
| `admin` | Destructive/critical | (future: delete, restart services) |

**Enforcement**:
- Tools declare their default permission level in registry
- Personas declare which tools/levels they can access
- Agent-service checks both before executing

## Agent Framework

**Decision**: Research needed - leaning toward custom or LangChain.

Key requirement: Must work with local-ai-app's OpenAI-compatible API (no vendor lock-in).

**Task**: `home-server-bxa` - Research agent orchestration frameworks

Options under consideration:
1. **Custom** - Full control, uses local-ai-app directly, no external dependencies
2. **LangChain** - Large ecosystem, but may add complexity
3. **Pydantic AI** - Simpler, type-safe, newer

## Implementation Priority

**Recommended order** (each phase builds on previous):

### Phase 1: Foundation (Mattermost Gateway)
1. `apps/mattermost-gateway/` - Basic POST /post endpoint
2. Test posting messages as Tayne bot
3. Add WebSocket listener for @mentions
4. No AI yet - just echo responses to verify plumbing

### Phase 2: Agent Tools
1. `apps/agent-tools/` - Create service structure
2. Implement `server.status` tool (Docker API)
3. Implement `docs.search` tool (Wiki.js API)
4. Test tools independently via API

### Phase 3: Agent Service (Basic)
1. `apps/agent-service/` - Create service structure
2. Define Tayne persona (YAML config)
3. Connect to local-ai-app for LLM inference
4. Basic tool calling (no memory yet)
5. Wire up: Gateway → Agent → Tools → Response

### Phase 4: Memory
1. Add PostgreSQL + pgvector to agent-service
2. Research/choose embedding model
3. Implement conversation storage
4. Implement semantic search for context retrieval

### Phase 5: Additional Interfaces
1. Upgrade `discord-reaction-bot` → `discord-gateway`
2. Add more personas (server-monitor, trading-bot)
3. Add more tools (calendar, deploy)

**Rationale**:
- Phase 1 validates Mattermost integration works
- Phase 2 builds reusable tools independently
- Phase 3 connects the pieces with basic AI
- Phase 4 adds the "memory" differentiator
- Phase 5 expands to other interfaces

## Related Resources

- [Mattermost REST API](https://api.mattermost.com/)
- [mattermostdriver Python library](https://github.com/Vaelor/python-mattermost-driver)
- [FastAPI documentation](https://fastapi.tiangolo.com/)
- Parent plan: [mattermost-hub-strategy.md](mattermost-hub-strategy.md)
