# Agent-Gateway Analysis

> Analysis of agent-gateway to determine if it should be merged into agent-harness.

**Decision:** Keep separate - they serve fundamentally different purposes.

---

## Overview

### agent-gateway

**Purpose:** Multi-platform AI agent orchestrator for Discord/Mattermost chat integration using local models (vLLM).

**Architecture:** Two-service system
| Service | Port | Purpose |
|---------|------|---------|
| **agent-core** | 8022 | AI logic, personas (Tayne), tools, role-based access |
| **agent-gateway** | 8023 | Platform adapters (Discord, Mattermost, Telegram) |

**LLM Backend:** Local AI Router (vLLM) - quantized/local models

### agent-harness

**Purpose:** Claude Code wrapper with profile-based configuration for autonomous task execution and development assistance.

**Architecture:** Single service with profile system
| Profile | Environment | Purpose |
|---------|-------------|---------|
| Ralph | Server (Docker) | Autonomous task processor |
| Avery | Mac Mini | Family coordinator |
| Gilfoyle | Server (native) | Cautious sysadmin |
| Jobin | Laptop | Development buddy |

**LLM Backend:** Claude Code CLI (Anthropic API) - frontier models

---

## Tayne Agent Details

Located in `/workspace/agent-gateway/core/agents/tayne/persona.py`

### Personality
- Helpful first, humor second
- Dry observations, subtle absurdist asides
- 90s corporate entertainment system aesthetic
- Can "generate" things, offer "printouts", mention "hat wobbles" (sparingly)
- Deadpan delivery, understated humor

### Configuration
```python
temperature: 0.8
max_tokens: 200
```

### Guardrails
- Character break detection (filters "as an ai", "i cannot", etc.)
- Response length limit (500 chars)
- 11 fallback quotes when guardrails trigger
- Rate limiting: 15 sec cooldown, rapid-fire detection

### Fallback Quotes
- "Now Tayne I can get into"
- "Computer, load up Celery Man please"
- (9 others)

---

## Platform Adapters

### Discord Adapter
- Native `discord.py` integration
- Message history (last 5 for context)
- @mention and text mention detection
- Random emoji reactions
- Typing indicator while generating
- Per-user rate limiting

### Mattermost Adapter
- HTTP client-based (no library)
- Webhook handler for incoming messages
- Thread support
- Multiple bot support (tayne, monitor, trading)
- Reaction support

---

## Tools (12 Total)

### Read-Only (Public Access)
| Tool | Purpose |
|------|---------|
| ServiceStatusTool | Check running containers/services |
| DiskUsageTool | Get disk space info |
| ContainerLogsTool | Fetch container logs |
| GameServerStatusTool | Game server status |

### Control (Trusted/Admin Role)
| Tool | Purpose |
|------|---------|
| RestartContainerTool | Restart Docker container |
| RestartGameServerTool | Restart game servers |
| DockerComposeUpTool | Start docker-compose stack |
| DockerComposeDownTool | Stop docker-compose stack |
| TriggerBackupTool | Initiate backups |

### Media (Trusted Role)
| Tool | Purpose |
|------|---------|
| SonarrSearchTool | Search/manage TV shows |
| RadarrSearchTool | Search/manage movies |
| PlexScanLibraryTool | Trigger Plex library scan |

---

## Key Differences

| Aspect | agent-gateway | agent-harness |
|--------|---------------|---------------|
| **LLM Backend** | Local models (vLLM) | Claude (frontier) |
| **Primary Use** | Chat responses | Autonomous tasks |
| **Architecture** | Sync, stateless | Async job queue |
| **Personas** | Tayne (chat) | Ralph, Avery, Gilfoyle, Jobin |
| **Tools** | 12 built-in | MCP extensible |
| **Platforms** | Discord, Mattermost | API only |
| **Rate Limiting** | Per-user, per-adapter | Per-job queue |
| **Task Automation** | None | Ralph Wiggum loop |
| **Lines of Code** | ~3000 | ~1400 |

---

## Why Keep Separate

### Different Operational Models
- **agent-gateway:** Synchronous request-response for chat
- **agent-harness:** Async job queue for long-running tasks

### Different Scaling Strategies
- **agent-gateway:** Horizontal (multiple instances)
- **agent-harness:** Limited (Claude CLI is sequential)

### Different Dependencies
- **agent-gateway:** discord.py, httpx, complex adapter logic
- **agent-harness:** Minimal (FastAPI + Claude CLI)

### Different Upgrade Cycles
- **agent-gateway:** Tied to local model updates, Discord API changes
- **agent-harness:** Tied to Claude CLI version updates

### Complexity Risk
Merging would require:
- Unified job store (Redis for multiple instances)
- Unified adapter registry
- Testing all permutations (model + platform + tool)
- Increased deployment complexity

---

## Potential Future Integration

These could be done later without merging:

### 1. Shared Tool Registry
Let Claude agents call agent-gateway's homelab tools:
- Export tools as OpenAI functions
- Claude invokes via structured output
- agent-gateway executes and returns results

### 2. Tayne as a Profile
Add Tayne personality to agent-harness:
- Claude-powered Discord responses
- Richer reasoning than local models
- Keep agent-gateway for cost-effective local model chat

### 3. Cross-Triggering
- agent-gateway dispatches complex tasks to agent-harness
- Ralph processes, returns results
- Best of both: quick chat + deep work

### 4. Shared Library
Create `shared-agent-lib` containing:
- Persona definitions
- Guardrail functions
- Rate limiter logic
- Tool base classes

---

## Conclusion

**Keep agent-gateway and agent-harness as separate services.**

They serve different architectural purposes:
- **agent-gateway** = Chat bot for quick interactions via local models
- **agent-harness** = Autonomous agent system for complex work via Claude

They complement each other and can coexist. Future integration via APIs is possible without merger.

---

## File References

| File | Purpose |
|------|---------|
| `/workspace/agent-gateway/README.md` | Architecture overview |
| `/workspace/agent-gateway/AGENTS.md` | Development guidelines |
| `/workspace/agent-gateway/core/agents/tayne/persona.py` | Tayne configuration |
| `/workspace/agent-gateway/core/routes/chat.py` | Tool integration |
| `/workspace/agent-gateway/gateway/adapters/discord/` | Discord adapter |
| `/workspace/agent-gateway/gateway/adapters/mattermost/` | Mattermost adapter |
