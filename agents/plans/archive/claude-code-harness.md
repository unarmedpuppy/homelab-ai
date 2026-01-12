# Claude Code Harness - Claude Max API Integration

**Status**: ✅ Code Complete (pending server-side installation)
**Created**: 2025-01-01

## Overview

Enable the Local AI Router to use Claude models via the Claude Max subscription by wrapping Claude Code CLI in an OpenAI-compatible API harness running on the server.

## Problem

- Claude Max subscription provides unlimited Claude access via Claude Code CLI
- The Local AI Router needs API-style access to Claude
- Claude Code uses OAuth tokens, not API keys
- Router runs in Docker, Claude Code needs host access to credentials

## Solution Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                          HOME SERVER                              │
│                                                                   │
│  ┌─────────────────┐      ┌─────────────────┐      ┌───────────┐ │
│  │  Local AI       │      │  Claude Harness │      │  Claude   │ │
│  │  Router         │─────▶│  (FastAPI)      │─────▶│  Code CLI │ │
│  │  (Docker:8012)  │      │  (systemd:8013) │      │  -p mode  │ │
│  └─────────────────┘      └─────────────────┘      └───────────┘ │
│         │                         │                      │        │
│         │                         │               ~/.claude.json  │
│         │                         │               (OAuth tokens)  │
│         ▼                         ▼                               │
│  ┌─────────────────┐      ┌─────────────────┐                    │
│  │  Dashboard      │      │  OpenAI-compat  │                    │
│  │  (Docker:3001)  │      │  /v1/chat/...   │                    │
│  └─────────────────┘      └─────────────────┘                    │
└──────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Claude Code CLI (Already exists)
- Installed on server via npm or official installer
- Authenticated once via OAuth (browser flow)
- Stores tokens in `~/.claude.json` and system credential store
- Supports headless mode: `claude -p "prompt"`

### 2. Claude Harness Service (NEW)
- FastAPI application running as systemd service
- Listens on port 8013 (localhost only)
- Exposes OpenAI-compatible `/v1/chat/completions` endpoint
- Translates requests to `claude -p` CLI calls
- Supports streaming via SSE

### 3. Router Provider Configuration
- New provider in `providers.yaml` pointing to `http://localhost:8013`
- Models: `claude-3-5-sonnet`, `claude-3-5-haiku`, etc.
- Priority: Cloud fallback (after local GPUs)

## Implementation Details

### Claude Harness API

```python
# Endpoints
POST /v1/chat/completions  # OpenAI-compatible chat
GET  /v1/models            # List available models
GET  /health               # Health check
```

### Request Flow

1. Router receives request for `claude-3-5-sonnet`
2. Router forwards to harness at `http://localhost:8013/v1/chat/completions`
3. Harness converts messages to Claude Code format
4. Harness spawns `claude -p "formatted prompt" --output-format json`
5. Harness streams or returns response in OpenAI format

### Claude Code CLI Flags

```bash
# Basic headless mode
claude -p "Your prompt here"

# With JSON output (structured)
claude -p "prompt" --output-format json

# Continue conversation (if needed)
claude -p "follow up" --continue

# Specify model (if multiple available)
claude -p "prompt" --model claude-3-5-sonnet
```

## Setup Requirements

### Server Prerequisites
- Node.js 18+ installed
- Claude Code CLI installed globally
- User account with Claude Max subscription authenticated

### One-time Authentication
1. SSH to server with port forwarding for browser
2. Run `claude` interactively
3. Complete OAuth flow in browser
4. Tokens stored permanently

### Service Configuration
- Systemd service running as `unarmedpuppy` user
- Access to user's home directory for credentials
- Restart on failure

## File Locations

```
/home/unarmedpuppy/
├── .claude.json                    # OAuth tokens
├── .claude/                        # Claude Code data
└── server/
    └── apps/
        └── claude-harness/
            ├── main.py             # FastAPI service
            ├── requirements.txt    # Dependencies
            └── README.md           # Setup instructions

/etc/systemd/system/
└── claude-harness.service          # Systemd unit file
```

## Security Considerations

1. **Localhost only**: Harness binds to 127.0.0.1, not exposed externally
2. **User permissions**: Runs as `unarmedpuppy` with access to Claude tokens
3. **No credentials in code**: OAuth tokens managed by Claude Code
4. **Rate limits**: Claude Max has usage limits (respected by CLI)

## Tasks

### Code (Complete)
- [x] Create harness FastAPI service (`apps/claude-harness/main.py`)
- [x] Create systemd service file (`apps/claude-harness/claude-harness.service`)
- [x] Create management script (`apps/claude-harness/manage.sh`)
- [x] Update router providers.yaml (added `claude-harness` provider)
- [x] Disable old `anthropic` provider (requires API key)
- [x] Update Claude models to use `claude-harness` provider
- [x] Document setup process (`apps/claude-harness/README.md`)

### Server Installation (Pending - Manual Steps)
- [ ] Install Claude Code CLI: `npm install -g @anthropic-ai/claude-code`
- [ ] Authenticate Claude Code: `claude` (follow OAuth flow)
- [ ] Pull latest code: `cd ~/server && git pull`
- [ ] Install service: `cd apps/claude-harness && sudo ./manage.sh install`
- [ ] Test: `./manage.sh test`
- [ ] Restart router: `cd ../local-ai-router && docker compose restart`

### Verification
- [ ] Health check: `curl http://localhost:8013/health`
- [ ] Test via router: `curl -X POST http://localhost:8012/v1/chat/completions -d '{"model":"claude-sonnet",...}'`
- [ ] Update dashboard model list (if needed)

## Rollback

If issues occur:
1. Disable harness provider in router config
2. Stop systemd service: `sudo systemctl stop claude-harness`
3. Router falls back to Z.ai/local models

## Future Enhancements

- Conversation context management
- Token usage tracking
- Multiple model support (Opus, Haiku when available via CLI)
- Response caching for repeated queries
- Auto-refresh of OAuth tokens (currently requires manual re-auth ~30 days)

## Files Created

| File | Purpose |
|------|---------|
| `apps/claude-harness/main.py` | FastAPI service wrapping Claude CLI |
| `apps/claude-harness/requirements.txt` | Python dependencies |
| `apps/claude-harness/claude-harness.service` | Systemd unit file |
| `apps/claude-harness/manage.sh` | Management script (install/update/status/logs) |
| `apps/claude-harness/README.md` | Full documentation with quick start |
| `apps/local-ai-router/config/providers.yaml` | Updated with `claude-harness` provider |

## Related

- [Claude Harness README](../../apps/claude-harness/README.md) - Setup instructions
- [Local AI Router](../../apps/local-ai-router/README.md) - Router documentation
- [Local AI Unified Architecture](local-ai-unified-architecture.md) - Overall architecture
