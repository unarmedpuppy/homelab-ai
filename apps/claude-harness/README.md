# Claude Code Harness

OpenAI-compatible API wrapper for Claude Code CLI, enabling the Local AI Router to use Claude models via your Claude Max subscription.

## Quick Start Checklist

**First-time installation on server:**

```bash
# 1. SSH to server
ssh -p 4242 unarmedpuppy@192.168.86.47

# 2. Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# 3. Authenticate (one-time OAuth flow)
claude
# Opens browser URL - log in with Claude Max account
# Tokens stored in ~/.claude.json

# 4. Verify CLI works headless
claude -p "Say hello"

# 5. Pull latest code
cd ~/server && git pull

# 6. Install service
cd apps/claude-harness
sudo ./manage.sh install

# 7. Test it works
./manage.sh test
```

**After code updates:**

```bash
cd ~/server && git pull
cd apps/claude-harness
sudo ./manage.sh update
```

## Management Script

All service management is done via `manage.sh`:

| Command | Description |
|---------|-------------|
| `sudo ./manage.sh install` | First-time setup (installs systemd service) |
| `sudo ./manage.sh update` | Update service after git pull |
| `./manage.sh status` | Show service status and health |
| `./manage.sh logs [n]` | Show last n log lines (default: 100) |
| `./manage.sh follow` | Follow logs in real-time |
| `sudo ./manage.sh restart` | Restart the service |
| `sudo ./manage.sh stop` | Stop the service |
| `sudo ./manage.sh uninstall` | Remove the service |
| `./manage.sh test` | Run health check and test completion |

### What `sudo ./manage.sh install` Does

Step-by-step breakdown of the install command:

| Step | Command | What it does |
|------|---------|--------------|
| 1 | `check_root` | Verifies you ran with sudo |
| 2 | `check_claude_cli` | Verifies `claude` command is installed |
| 3 | `check_python_deps` | Installs fastapi/uvicorn/pydantic if missing |
| 4 | `cp SERVICE_FILE SYSTEMD_PATH` | Copies `claude-harness.service` to `/etc/systemd/system/` |
| 5 | `systemctl daemon-reload` | Tells systemd to re-read service files |
| 6 | `systemctl enable` | Enables auto-start on boot |
| 7 | `systemctl start` | Starts the FastAPI service immediately |
| 8 | `systemctl status` | Shows if it started successfully |

**Files modified:**

| Location | Action |
|----------|--------|
| `/etc/systemd/system/claude-harness.service` | Created (systemd service definition) |
| `~/.local/lib/python*/...` | Maybe (Python packages if missing) |
| Systemd state | Modified (service enabled and started) |

**Safe to run?** Yes. The script:
- Only touches its own service file
- Doesn't modify system configs, PATH, or bashrc
- Can be fully reversed with `sudo ./manage.sh uninstall`

### Script Safety Features

The script uses `set -euo pipefail`:
- `set -e` → Exit immediately if any command fails
- `set -u` → Error on undefined variables (catches typos)
- `set -o pipefail` → Pipeline fails if any command in it fails

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
│         │                                              │         │
│   host.docker.internal:8013                    ~/.claude.json   │
│                                                (OAuth tokens)   │
└─────────────────────────────────────────────────────────────────┘
```

**Why not Docker?**
- Claude Code stores OAuth tokens in `~/.claude.json`
- Tokens are tied to the user session that ran `claude` interactively
- Running in Docker would require mounting credentials and managing token refresh
- Systemd service is simpler and works reliably

## Detailed Setup Instructions

### Prerequisites

- Node.js 18+ on server
- Python 3.11+ with pip
- Claude Max subscription (or Claude Pro)

### Step 1: Install Claude Code CLI

```bash
ssh -p 4242 unarmedpuppy@192.168.86.47

# Option A: npm (if Node.js installed)
npm install -g @anthropic-ai/claude-code

# Option B: Official installer
curl -fsSL https://claude.ai/install.sh | bash

# Verify
claude --version
```

### Step 2: Authenticate (One-Time)

```bash
# On server
claude

# Claude displays a URL like:
#   Please open this URL: https://claude.ai/oauth/...
#
# Open that URL in any browser
# Log in with your Claude Max account
# Tokens are stored in ~/.claude.json
```

### Step 3: Verify Headless Mode

```bash
claude -p "Say hello in exactly 5 words"
# Should output response without prompts
```

### Step 4: Install Service

```bash
cd ~/server/apps/claude-harness
sudo ./manage.sh install
```

### Step 5: Verify

```bash
./manage.sh status
./manage.sh test
```

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/v1/models` | GET | List available models |
| `/v1/chat/completions` | POST | Chat completions (OpenAI-compatible) |

## Usage Examples

```bash
# Direct to harness (for testing)
curl -X POST http://localhost:8013/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello!"}]}'

# Via router (production use)
curl -X POST http://localhost:8012/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet","messages":[{"role":"user","content":"Hello!"}]}'
```

## Router Configuration

Already configured in `apps/local-ai-router/config/providers.yaml`:

```yaml
- id: claude-harness
  name: "Claude Harness (Claude Max)"
  endpoint: "http://host.docker.internal:8013"
  enabled: true
```

After installing the harness, restart the router to connect:

```bash
cd ~/server/apps/local-ai-router
docker compose restart
```

## Troubleshooting

### Claude CLI not found

```bash
which claude
# If not found, add to PATH:
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Authentication expired

```bash
# Re-authenticate
claude
# Follow OAuth flow again
sudo ./manage.sh restart
```

### Service won't start

```bash
./manage.sh logs 50
# Check for:
# - Missing Python dependencies
# - Claude CLI not in PATH for systemd
# - Permission issues on ~/.claude.json
```

### Router can't reach harness

```bash
# Test from router container
docker exec -it local-ai-router curl http://host.docker.internal:8013/health

# If that fails, check:
# 1. Harness is running: ./manage.sh status
# 2. Port 8013 is open: sudo ufw allow 8013/tcp
# 3. Docker can reach host: check docker-compose.yml has extra_hosts
```

## Limitations

1. **No streaming**: Claude CLI outputs complete response, chunked after completion
2. **Sequential requests**: One request at a time (Claude CLI limitation)
3. **Rate limits**: Claude Max limits apply
4. **Token expiry**: Re-authenticate if tokens expire (~30 days)

## Files

```
apps/claude-harness/
├── main.py                    # FastAPI service
├── requirements.txt           # Python dependencies  
├── claude-harness.service     # Systemd unit file
├── manage.sh                  # Management script
└── README.md                  # This file
```

## See Also

- [Claude Code Harness Plan](../../agents/plans/claude-code-harness.md)
- [Local AI Router](../local-ai-router/README.md)
- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code/overview)
