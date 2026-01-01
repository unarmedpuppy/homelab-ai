---
name: gaming-pc-manager
description: Interact with Gaming PC's local-ai manager for model control
when_to_use: When managing GPU models on Gaming PC, checking status, or toggling gaming mode
---

# Gaming PC Manager

Manage GPU models on the Gaming PC (RTX 3090) via the local-ai manager API.

## Gaming PC Details

| Item | Value |
|------|-------|
| **IP** | `192.168.86.63` (or your Gaming PC IP) |
| **Manager Port** | `8000` |
| **GPU** | RTX 3090 (24GB VRAM) |
| **Location** | `local-ai/` directory on Gaming PC |

## Manager Endpoints

### Check Status

```bash
curl http://<GAMING_PC_IP>:8000/status | jq
```

**Response includes:**
- `gaming_mode` - Whether gaming mode is enabled
- `safe_to_game` - Whether GPU is free for gaming
- `running_models` - List of currently loaded models
- `stopped_models` - List of available but unloaded models

### Health Check

```bash
curl http://<GAMING_PC_IP>:8000/healthz | jq
```

### Toggle Gaming Mode

```bash
# Enable gaming mode (stops all models)
curl -X POST http://<GAMING_PC_IP>:8000/gaming-mode \
  -H "Content-Type: application/json" \
  -d '{"enable": true}'

# Disable gaming mode (restarts keep-warm models)
curl -X POST http://<GAMING_PC_IP>:8000/gaming-mode \
  -H "Content-Type: application/json" \
  -d '{"enable": false}'
```

### Stop All Models

```bash
curl -X POST http://<GAMING_PC_IP>:8000/stop-all
```

### List Available Models

```bash
curl http://<GAMING_PC_IP>:8000/v1/models | jq
```

## Model Types

| Model | Type | Port | Keep-Warm |
|-------|------|------|-----------|
| `qwen2.5-14b-awq` | LLM | 8002 | ✅ Yes |
| `llama3-8b` | LLM | 8001 | No |
| `deepseek-coder` | LLM | 8003 | No |
| `qwen-image-edit` | Image | 8005 | No |
| `chatterbox-turbo` | TTS | 8006 | ✅ Yes |

## Keep-Warm Behavior

Models with `keep_warm: true` in `models.json`:
1. Auto-start on manager boot
2. Stay loaded (no idle timeout)
3. Stop when gaming mode is enabled
4. Restart when gaming mode is disabled

## Gaming Mode Workflow

**Before gaming:**
```bash
# Check if safe to game
curl http://<GAMING_PC_IP>:8000/status | jq '.safe_to_game'

# If not safe, enable gaming mode
curl -X POST http://<GAMING_PC_IP>:8000/gaming-mode -d '{"enable": true}'
```

**After gaming:**
```bash
# Disable gaming mode (keep-warm models restart)
curl -X POST http://<GAMING_PC_IP>:8000/gaming-mode -d '{"enable": false}'
```

## PowerShell Scripts (on Gaming PC)

```powershell
# Check status
.\control-gaming-mode.ps1 status

# Enable gaming mode
.\control-gaming-mode.ps1 enable

# Disable gaming mode
.\control-gaming-mode.ps1 disable

# Check if safe to game
.\control-gaming-mode.ps1 safe

# Stop all models
.\control-gaming-mode.ps1 stop-all
```

## Web Dashboard (Gaming PC)

Access the manager web dashboard at: `http://<GAMING_PC_IP>:8080`

Features:
- Real-time status monitoring
- One-click gaming mode toggle
- Stop all models button
- Visual indicators for safe-to-game status

## Docker Commands (on Gaming PC)

```powershell
# Start manager
docker compose up -d

# View manager logs
docker logs local-ai-manager --tail 100 -f

# Restart manager
docker compose restart local-ai-manager

# Check running containers
docker ps | Select-String "vllm|chatterbox|qwen"
```

## Troubleshooting

### Manager Not Responding

```bash
# Check if container is running
docker ps | grep local-ai-manager

# Check logs
docker logs local-ai-manager --tail 50
```

### Model Won't Start

```bash
# Check container status directly
docker ps -a | grep <container-name>

# Check container logs
docker logs <container-name> --tail 50
```

### VRAM Issues

```bash
# Check GPU memory (on Gaming PC)
nvidia-smi
```

## SSH Access

For direct shell access to the Gaming PC:

```bash
bash scripts/connect-gaming-pc.sh
bash scripts/connect-gaming-pc.sh "nvidia-smi"
bash scripts/connect-gaming-pc.sh "docker ps"
```

See `agents/skills/connect-gaming-pc/` for details.

## Related

- [Local AI README](../../../local-ai/README.md)
- [Gaming Mode Documentation](../../../local-ai/GAMING_MODE.md)
- [TTS Testing](../test-tts/SKILL.md)
- [Connect Gaming PC](../connect-gaming-pc/SKILL.md)
