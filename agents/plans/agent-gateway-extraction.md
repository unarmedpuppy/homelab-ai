# Agent Gateway Extraction Plan

**Status**: Planning
**Created**: 2026-01-02
**Related**: agent-core-architecture.md

## Overview

Extract agent-core, discord-reaction-bot, and mattermost-gateway into a new `agent-gateway` monorepo with a unified architecture that consolidates shared logic while preserving platform-specific adapters.

## Current State

```
home-server/apps/
├── agent-core/              # Platform-agnostic agent service
├── discord-reaction-bot/    # Discord adapter (simple bot, not gateway pattern)
└── mattermost-gateway/      # Mattermost adapter (full gateway pattern)
```

**Problems:**
1. Naming inconsistency (`discord-reaction-bot` vs `mattermost-gateway`)
2. Architecture asymmetry (MM has gateway pattern, Discord doesn't)
3. Duplicate logic (rate limiting, persona fallback, LLM calls)
4. URL inconsistency (`local-ai-router` vs `llm-router`)
5. Scattered across home-server instead of dedicated repo

## Target Architecture

### Key Insight: Two Layers

| Layer | Purpose | Examples |
|-------|---------|----------|
| **Agent Core** | Agent logic, personas, tools, LLM routing | Tayne persona, service_status tool, role auth |
| **Gateway Adapters** | Platform transport, SDK connections, message formatting | Discord.py client, MM webhooks, Telegram bot API |

### Architecture Decision: Unified Gateway + Separate Agent Core

```
                              ┌─────────────────────────────────────────────────┐
                              │              agent-gateway                       │
                              │                                                  │
   Discord ◄────────────────► │  ┌─────────────────────────────────────────────┐ │
                              │  │ adapters/                                   │ │
   Mattermost ◄──────────────► │  │ ├── discord/    (Discord SDK + handlers)   │ │
                              │  │ ├── mattermost/ (MM API + webhooks)        │ │
   Telegram ◄────────────────► │  │ └── telegram/  (future)                   │ │
                              │  └─────────────────────────────────────────────┘ │
                              │                       │                          │
                              │                       ▼                          │
                              │  ┌─────────────────────────────────────────────┐ │
   HTTP Clients ◄────────────►│  │ api/                                        │ │
                              │  │ ├── POST /send   (unified outbound)        │ │
                              │  │ ├── POST /webhook/{platform}/{bot}         │ │
                              │  │ └── GET  /health                           │ │
                              │  └─────────────────────────────────────────────┘ │
                              │                       │                          │
                              └───────────────────────┼──────────────────────────┘
                                                      │ HTTP
                                                      ▼
                              ┌─────────────────────────────────────────────────┐
                              │              agent-core                          │
                              │                                                  │
                              │  agents/          tools/           auth/         │
                              │  ├── tayne/       ├── read_only/   ├── users    │
                              │  ├── sentinel/    ├── control/     └── roles    │
                              │  └── analyst/     └── media/                     │
                              │                                                  │
                              │  POST /v1/agent/{id}/chat                        │
                              │  GET  /v1/agents                                 │
                              │  GET  /v1/tools                                  │
                              └─────────────────────────────────────────────────┘
                                                      │ HTTP
                                                      ▼
                              ┌─────────────────────────────────────────────────┐
                              │              homelab-ai (llm-router)             │
                              │                                                  │
                              │  POST /v1/chat/completions                       │
                              │  (with memory, metrics, provider routing)        │
                              └─────────────────────────────────────────────────┘
```

### Why Two Services (Not One)?

| Consideration | agent-core + agent-gateway | Single Unified Service |
|--------------|---------------------------|------------------------|
| Separation of concerns | ✅ Clean boundaries | ❌ Mixed transport + logic |
| Independent scaling | ✅ Scale gateway without core | ❌ All-or-nothing |
| API for other clients | ✅ curl, scripts can use core | ❌ Must go through gateway |
| Container size | ✅ Smaller individual images | ❌ Large monolith |
| Failure isolation | ✅ Discord SDK crash doesn't kill core | ❌ Everything fails together |
| Shared logic | ❌ Still need HTTP calls | ✅ Direct function calls |

**Decision**: Keep separate but in same repo for unified deployment.

---

## New Repository Structure

```
agent-gateway/                    # New repo (like homelab-ai)
├── .github/
│   └── workflows/
│       └── build-push.yml        # Build both images, push to Harbor
├── core/                         # agent-core service
│   ├── agents/
│   │   ├── tayne/
│   │   ├── sentinel/
│   │   └── analyst/
│   ├── tools/
│   │   ├── read_only/
│   │   ├── control/
│   │   └── media/
│   ├── auth/
│   ├── routes/
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── gateway/                      # Unified gateway service
│   ├── adapters/
│   │   ├── base.py               # Abstract adapter interface
│   │   ├── discord/
│   │   │   ├── __init__.py
│   │   │   ├── client.py         # Discord.py wrapper
│   │   │   ├── handlers.py       # Message/reaction handlers
│   │   │   └── config.py         # Discord-specific settings
│   │   ├── mattermost/
│   │   │   ├── __init__.py
│   │   │   ├── client.py         # MM API wrapper
│   │   │   ├── webhooks.py       # Webhook handlers
│   │   │   └── config.py         # MM-specific settings
│   │   └── telegram/             # Future
│   ├── shared/
│   │   ├── rate_limiting.py      # Unified rate limiter
│   │   ├── fallback.py           # LLM fallback logic
│   │   └── persona.py            # Fallback personas
│   ├── api/
│   │   ├── outbound.py           # POST /send - unified message sending
│   │   ├── inbound.py            # Webhook receivers
│   │   └── health.py             # Health checks
│   ├── main.py
│   ├── config.py
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml            # Local dev (both services)
├── docker-compose.prod.yml       # Production reference
└── README.md
```

---

## Unified API Design

### Outbound Messages (POST /send)

Any internal service can send messages to any platform:

```json
POST /send
{
  "platform": "discord",        // or "mattermost", "telegram"
  "bot": "tayne",               // bot identity to use
  "channel": "general",         // channel name or ID
  "message": "Hello from the server!",
  "thread_id": "optional",      // for threaded replies
  "metadata": {}                // platform-specific extras
}
```

### Inbound Webhooks

Each platform has its own webhook format, handled by adapters:

```
POST /webhook/discord/interaction    # Discord interactions
POST /webhook/mattermost/mention     # MM outgoing webhooks  
POST /webhook/telegram/update        # Telegram webhook
```

### Health & Status

```
GET /health                          # Overall gateway health
GET /health/discord                  # Discord connection status
GET /health/mattermost               # MM connection status
GET /adapters                        # List configured adapters
```

---

## Adapter Interface

```python
# gateway/adapters/base.py
from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel

class InboundMessage(BaseModel):
    """Normalized inbound message from any platform."""
    platform: str
    user_id: str
    user_display_name: str
    channel_id: str
    channel_name: Optional[str]
    message: str
    thread_id: Optional[str]
    raw: dict  # Original platform-specific data

class OutboundMessage(BaseModel):
    """Message to send to a platform."""
    platform: str
    bot: str
    channel: str
    message: str
    thread_id: Optional[str] = None
    metadata: dict = {}

class BaseAdapter(ABC):
    """Base class for platform adapters."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Initialize connection to platform."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Clean up connection."""
        pass
    
    @abstractmethod
    async def send_message(self, msg: OutboundMessage) -> bool:
        """Send a message to the platform."""
        pass
    
    @abstractmethod
    async def add_reaction(self, channel: str, message_id: str, emoji: str) -> bool:
        """Add reaction to a message."""
        pass
    
    @abstractmethod
    def is_healthy(self) -> bool:
        """Check if adapter is connected and healthy."""
        pass
```

---

## Shared Logic Consolidation

### What Moves to `gateway/shared/`

| Component | Current Location | New Location |
|-----------|-----------------|--------------|
| Rate limiting | Duplicated in both bots | `gateway/shared/rate_limiting.py` |
| Fallback personas | Duplicated `tayne_persona.py` | `gateway/shared/persona.py` |
| Character break detection | Duplicated `needs_fallback()` | `gateway/shared/guardrails.py` |
| Direct LLM fallback | Duplicated in both | `gateway/shared/fallback.py` |

### What Stays Platform-Specific

| Component | Location | Reason |
|-----------|----------|--------|
| Discord SDK handling | `adapters/discord/` | discord.py specific |
| MM webhook parsing | `adapters/mattermost/` | Form-encoded format |
| Bot token management | Each adapter's config | Different auth models |
| Random reactions | `adapters/discord/` | Discord-specific feature |

---

## Implementation Phases

### Phase 0: Quick Fixes (Do First)
**Goal**: Fix URL inconsistencies before extraction

- [ ] Update `discord-reaction-bot` docker-compose: `llm-router:8000`
- [ ] Update `mattermost-gateway` docker-compose: `llm-router:8000`
- [ ] Update `.env.example` files to reference correct URLs
- [ ] Update prometheus config: `llm-router:8000`

### Phase 1: Create New Repository
**Goal**: Set up agent-gateway repo with CI/CD

- [ ] Create `agent-gateway` GitHub repo
- [ ] Set up GitHub Actions workflow (build + push to Harbor)
- [ ] Create initial README and structure
- [ ] Configure Harbor project

### Phase 2: Migrate agent-core
**Goal**: Move agent-core to new repo

- [ ] Copy agent-core to `agent-gateway/core/`
- [ ] Update imports and paths
- [ ] Create Dockerfile
- [ ] Test locally with docker-compose
- [ ] Build and push to Harbor
- [ ] Update home-server to pull from Harbor

### Phase 3: Create Unified Gateway Structure
**Goal**: Set up gateway service with adapter pattern

- [ ] Create adapter base class and interface
- [ ] Create shared modules (rate_limiting, fallback, persona)
- [ ] Create API routes (outbound, health)
- [ ] Set up main.py and config

### Phase 4: Migrate Discord Adapter
**Goal**: Move discord-reaction-bot logic to gateway

- [ ] Create `adapters/discord/` module
- [ ] Port Discord.py client handling
- [ ] Port message handlers and reactions
- [ ] Wire up to unified API
- [ ] Test Discord functionality

### Phase 5: Migrate Mattermost Adapter
**Goal**: Move mattermost-gateway logic to gateway

- [ ] Create `adapters/mattermost/` module
- [ ] Port Mattermost client and webhooks
- [ ] Port bot registry pattern
- [ ] Wire up to unified API
- [ ] Test Mattermost functionality

### Phase 6: Deploy Unified Gateway
**Goal**: Single gateway container serving all platforms

- [ ] Final testing of all adapters
- [ ] Build and push gateway image to Harbor
- [ ] Update home-server docker-compose
- [ ] Remove old individual gateway apps
- [ ] Verify all platforms working

### Phase 7: Cleanup
**Goal**: Remove deprecated code from home-server

- [ ] Archive old `discord-reaction-bot/` (or delete)
- [ ] Archive old `mattermost-gateway/` (or delete)
- [ ] Archive old `agent-core/` (or delete)
- [ ] Update AGENTS.md documentation
- [ ] Update homepage labels

---

## Docker Deployment (home-server)

After extraction, home-server will have:

```yaml
# apps/agent-gateway/docker-compose.yml
services:
  agent-core:
    image: harbor.server.unarmedpuppy.com/library/agent-core:latest
    container_name: agent-core
    environment:
      - LOCAL_AI_URL=http://llm-router:8000
      - LOCAL_AI_API_KEY=${LOCAL_AI_API_KEY}
    # ... (volumes, networks, labels)

  agent-gateway:
    image: harbor.server.unarmedpuppy.com/library/agent-gateway:latest
    container_name: agent-gateway
    environment:
      - AGENT_CORE_URL=http://agent-core:8000
      # Discord
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      # Mattermost
      - MATTERMOST_URL=${MATTERMOST_URL}
      - MATTERMOST_BOT_TAYNE_TOKEN=${MATTERMOST_BOT_TAYNE_TOKEN}
      # ... other bot tokens
    # ... (ports, networks, labels)
```

---

## Success Criteria

- [ ] Single `agent-gateway` container handles Discord + Mattermost + future platforms
- [ ] `agent-core` remains platform-agnostic, usable by any HTTP client
- [ ] No duplicate logic between platform adapters
- [ ] All existing functionality preserved
- [ ] CI/CD builds and pushes to Harbor on merge
- [ ] home-server only needs to `git pull` and restart

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking Discord during migration | Keep old bot running until new is validated |
| Breaking Mattermost during migration | Keep old gateway running until new is validated |
| Lost functionality | Create feature checklist before starting |
| Container startup order | Gateway depends_on agent-core, health checks |
| Single point of failure | Gateway is stateless, can restart quickly |

---

## Related Documents

- [Agent Core Architecture](./agent-core-architecture.md) - Current architecture plan
- [Mattermost Gateway Service](./mattermost-gateway-service.md) - Original gateway plan
- [homelab-ai extraction](./homelab-ai/) - Reference for repo extraction pattern

---

## Changelog

- 2026-01-02: Initial plan created
