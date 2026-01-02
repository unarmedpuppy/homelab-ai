# Quick Start Guide - Multimodal Inference

Quick reference for getting multimodal inference up and running.

## Windows PC Setup (5 minutes)

```powershell
# 1. Navigate to local-ai directory
cd local-ai

# 2. Build image inference server
.\build-image-server.ps1

# 3. Run setup (creates all containers)
bash setup.sh

# 4. Verify setup
.\test-multimodal.ps1
```

## Server Setup (2 minutes)

```bash
cd apps/local-ai-app
# Verify WINDOWS_AI_HOST in docker-compose.yml
docker compose up -d
```

## Test It

### Via Web UI
1. Visit: `https://local-ai.server.unarmedpuppy.com`
2. Test text: `/model qwen2.5-14b-awq` then send "Hello!"
3. Test image: `/model qwen-image-edit` then send "a duck jumping over a puddle"

### Via API

**Text Generation:**
```bash
curl -X POST http://local-ai.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen2.5-14b-awq", "messages": [{"role": "user", "content": "Hello!"}]}'
```

**Image Generation:**
```bash
curl -X POST http://local-ai.server.unarmedpuppy.com/v1/images/generations \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen-image-edit", "prompt": "a duck jumping over a puddle", "response_format": "b64_json"}'
```

## Common Commands

```powershell
# Check manager status
Invoke-WebRequest -Uri "http://localhost:8000/healthz" -UseBasicParsing

# View running containers
docker ps

# Check image model logs
docker logs qwen-image-server --follow

# Restart manager
docker compose restart manager

# Rebuild image server
.\build-image-server.ps1
```

## Troubleshooting

**Image server build fails?**
- Check Docker Desktop is running
- Verify GPU: `docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi`

**Model not loading?**
- Check logs: `docker logs qwen-image-server --follow`
- Verify GPU available: `nvidia-smi`
- Check disk space: `docker system df`

**Manager can't find model?**
- Verify `models.json` has correct entry with `"type": "image"`
- Restart manager: `docker compose restart manager`

For more details, see:
- [DEPLOYMENT.md](DEPLOYMENT.md) - Full deployment guide
- [TESTING.md](TESTING.md) - Comprehensive test suite
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues

