# Claude Code Harness

OpenAI-compatible API wrapper for Claude Code CLI, enabling the Local AI Router to use Claude models via your Claude Max subscription.

## Overview

This service wraps the Claude Code CLI to provide an OpenAI-compatible `/v1/chat/completions` endpoint. It runs as a systemd service on the host (not in Docker) to access Claude Code's OAuth credentials.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         HOME SERVER                              │
│                                                                  │
│  ┌──────────────┐      ┌─────────────────┐      ┌─────────────┐ │
│  │ Local AI     │      │ Claude Harness  │      │ Claude Code │ │
│  │ Router       │─────▶│ (FastAPI:8013)  │─────▶│ CLI         │ │
│  │ (Docker)     │      │ (systemd)       │      │ (headless)  │ │
│  └──────────────┘      └─────────────────┘      └─────────────┘ │
│                                │                       │         │
│                                │                ~/.claude.json   │
│                                │                (OAuth tokens)   │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Node.js 18+ installed on server
- Claude Max subscription (or Claude Pro)
- Python 3.11+ with pip

## Setup Instructions

### Step 1: Install Claude Code CLI on Server

SSH to your server and install Claude Code:

```bash
ssh -p 4242 unarmedpuppy@192.168.86.47

# Option A: Using npm (recommended if Node.js already installed)
npm install -g @anthropic-ai/claude-code

# Option B: Using official installer
curl -fsSL https://claude.ai/install.sh | bash

# Verify installation
claude --version
```

### Step 2: Authenticate Claude Code (One-Time)

This step requires browser access for OAuth. Use SSH port forwarding:

```bash
# From your local machine, SSH with port forwarding
ssh -p 4242 -L 8080:localhost:8080 unarmedpuppy@192.168.86.47

# On the server, run Claude interactively
claude

# Claude will display a URL like:
#   Please open this URL in your browser: https://claude.ai/oauth/...
#
# Open that URL in your LOCAL browser (thanks to port forwarding)
# Complete the authentication flow
# Once authenticated, Claude Code stores tokens in ~/.claude.json
```

**Alternative (if port forwarding doesn't work):**

```bash
# On server, run claude and copy the URL it shows
claude

# Open that URL directly in any browser on any machine
# Log in with your Claude Max account
# The token will be stored on the server
```

### Step 3: Verify Headless Mode Works

Test that Claude Code works in headless mode:

```bash
# Quick test
claude -p "Say hello in exactly 5 words" --no-input

# Should output a response without any interactive prompts
```

### Step 4: Install Python Dependencies

```bash
cd ~/server/apps/claude-harness
pip install --user -r requirements.txt
```

### Step 5: Test the Harness Locally

```bash
cd ~/server/apps/claude-harness

# Run the service
python main.py

# In another terminal, test the endpoint
curl -X POST http://127.0.0.1:8013/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Step 6: Install Systemd Service

```bash
# Copy service file
sudo cp ~/server/apps/claude-harness/claude-harness.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable claude-harness
sudo systemctl start claude-harness

# Check status
sudo systemctl status claude-harness

# View logs
journalctl -u claude-harness -f
```

### Step 7: Update Router Configuration

The router needs to be configured to use the harness. Edit `apps/local-ai-router/config/providers.yaml`:

```yaml
providers:
  # ... existing providers ...
  
  # Claude Code Harness (uses Claude Max subscription)
  - id: claude-harness
    name: "Claude (via Claude Code)"
    type: local  # Not cloud - runs locally
    description: "Claude models via Claude Code CLI using Max subscription"
    endpoint: "http://host.docker.internal:8013"  # Docker → host
    priority: 3
    enabled: true
    maxConcurrent: 1  # Claude Code handles one request at a time
    healthCheckInterval: 60
    healthCheckTimeout: 10
    healthCheckPath: "/health"
    authType: null  # No auth needed for localhost

models:
  # ... existing models ...
  
  # Update Claude models to use harness
  - id: claude-3-5-sonnet
    name: "Claude 3.5 Sonnet"
    providerId: claude-harness  # Changed from 'anthropic'
    # ... rest of config ...
```

Then rebuild the router:

```bash
cd ~/server/apps/local-ai-router
docker compose build && docker compose up -d
```

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check (verifies Claude CLI available) |
| `/v1/models` | GET | List available models |
| `/v1/chat/completions` | POST | OpenAI-compatible chat completions |

## Usage

Once configured, requests to Claude models through the router will automatically use the harness:

```bash
# Via router (recommended)
curl -X POST http://localhost:8012/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ROUTER_API_KEY" \
  -d '{
    "model": "claude-3-5-sonnet",
    "messages": [{"role": "user", "content": "Hello Claude!"}]
  }'

# Direct to harness (for testing)
curl -X POST http://localhost:8013/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet", 
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Troubleshooting

### Claude CLI not found
```bash
# Check if claude is in PATH
which claude

# If not, add to PATH in ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"
```

### Authentication expired
```bash
# Re-run claude interactively to refresh tokens
claude
# Follow the OAuth flow again
```

### Service won't start
```bash
# Check logs
journalctl -u claude-harness -n 50

# Common issues:
# - Wrong Python path in service file
# - Missing dependencies
# - Claude CLI not in PATH for systemd
```

### Permission denied on ~/.claude
```bash
# Service runs as unarmedpuppy, check ownership
ls -la ~/.claude.json
# Should be owned by unarmedpuppy
```

## Limitations

1. **No true streaming**: Claude CLI doesn't support streaming output, so responses are chunked after completion
2. **Single request at a time**: Claude Code processes one request at a time
3. **Rate limits apply**: Claude Max has usage limits that apply here too
4. **Token refresh**: If OAuth tokens expire, manual re-authentication is needed

## Files

```
apps/claude-harness/
├── main.py                    # FastAPI service
├── requirements.txt           # Python dependencies
├── claude-harness.service     # Systemd unit file
└── README.md                  # This file
```

## See Also

- [Claude Code Harness Plan](../../agents/plans/claude-code-harness.md)
- [Local AI Router](../local-ai-router/README.md)
- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code/overview)
