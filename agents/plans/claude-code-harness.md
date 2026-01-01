# Claude Code Harness - Claude Max API Integration

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

1. [ ] Install Claude Code on server
2. [ ] Authenticate Claude Code (one-time OAuth)
3. [ ] Create harness FastAPI service
4. [ ] Create systemd service file
5. [ ] Update router providers.yaml
6. [ ] Test end-to-end flow
7. [ ] Update dashboard model list

## Rollback

If issues occur:
1. Disable harness provider in router config
2. Stop systemd service: `sudo systemctl stop claude-harness`
3. Router falls back to Z.ai/local models

## Future Enhancements

- Conversation context management
- Token usage tracking
- Multiple model support
- Response caching for repeated queries
