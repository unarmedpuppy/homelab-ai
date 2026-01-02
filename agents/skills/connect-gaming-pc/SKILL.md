---
name: connect-gaming-pc
description: Connect to Gaming PC via SSH (WSL) - interactive only
when_to_use: Need shell access on Gaming PC, manage local-ai models, check GPU status
script: scripts/connect-gaming-pc.sh
---

# Connect to Gaming PC

Interactive SSH connection to the Gaming PC (Windows/WSL).

## Gaming PC Details

| Item | Value |
|------|-------|
| **IP** | `192.168.86.63` |
| **SSH Host** | `gaming-pc` |
| **User** | `micro` |
| **Shell** | WSL (Ubuntu) |
| **GPU** | RTX 3090 (24GB VRAM) |

## Usage

```bash
bash scripts/connect-gaming-pc.sh
```

Opens an interactive WSL shell on the Gaming PC.

## Limitation: Interactive Only

WSL as the default SSH shell does not support passing commands non-interactively (WSL doesn't accept the `-c` flag that OpenSSH uses).

**This works:**
```bash
ssh gaming-pc              # Interactive session
```

**This does NOT work:**
```bash
ssh gaming-pc "command"    # Fails with WSL
```

## Alternatives for Non-Interactive Commands

Use the HTTP API instead:

```bash
curl http://192.168.86.63:8000/status | jq

curl -X POST http://192.168.86.63:8000/gaming-mode \
  -H "Content-Type: application/json" \
  -d '{"enable": true}'
```

See `agents/skills/gaming-pc-manager/` for full API documentation.

## Related Tools

- `gaming-pc-manager` - Control models via HTTP API (supports non-interactive use)
- `connect-server` - Connect to home server
- `test-local-ai-router` - Test local AI endpoints
