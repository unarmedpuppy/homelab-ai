# Local AI Router

Intelligent OpenAI-compatible API router for multi-backend LLM inference.

## URLs

| Context | URL |
|---------|-----|
| Docker network | `http://local-ai-router:8000` |
| Server localhost | `http://localhost:8012` |
| External (HTTPS) | `https://local-ai-api.server.unarmedpuppy.com` |

## Features

- **OpenAI-compatible API** - Drop-in replacement for OpenAI endpoints
- **Intelligent routing** - Routes based on token count, task complexity, and backend availability
- **Gaming mode aware** - Respects gaming mode on Windows PC
- **Force-big override** - Explicit routing with headers or model names
- **Health checks** - Monitors all backends
- **Streaming support** - Full SSE streaming for chat completions

## Backends

| Backend | Hardware | Status | Use Case |
|---------|----------|--------|----------|
| 3090 | Gaming PC | ✅ Active | Medium models, coding tasks |
| 3070 | Home Server | ⏳ Pending | Small models, fast routing |
| OpenCode | Container | ⏳ Pending | GLM-4.7, Claude via subscription |

## Routing Logic

1. **Explicit model request** → Route to requested backend
2. **Token estimate < 2K** → 3070 (fast path)
3. **Gaming mode ON** → 3070 only (unless force-big)
4. **Token 2K-16K + 3090 available** → 3090
5. **Complex/long context** → OpenCode
6. **Fallback** → 3070 → 3090 → OpenCode

## API Endpoints

### Chat Completions
```bash
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Force to 3090
```bash
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Force-Big: true" \
  -d '{
    "model": "big",
    "messages": [{"role": "user", "content": "Complex coding task..."}]
  }'
```

### List Models
```bash
curl https://local-ai-api.server.unarmedpuppy.com/v1/models
```

### Health Check
```bash
curl https://local-ai-api.server.unarmedpuppy.com/health
```

### Gaming Mode Control
```bash
# Enable gaming mode
curl -X POST https://local-ai-api.server.unarmedpuppy.com/gaming-mode?enable=true

# Disable gaming mode
curl -X POST https://local-ai-api.server.unarmedpuppy.com/gaming-mode?enable=false

# Stop all models
curl -X POST https://local-ai-api.server.unarmedpuppy.com/stop-all
```

## Model Aliases

| Alias | Routes To |
|-------|-----------|
| `auto` | Intelligent routing |
| `small`, `fast` | 3070 |
| `big`, `medium`, `3090`, `gaming-pc` | 3090 |
| `glm` | OpenCode (GLM-4.7) |
| `claude` | OpenCode (Claude) |

## Configuration

Environment variables:

```bash
# Backend endpoints
GAMING_PC_URL=http://192.168.86.63:8000
LOCAL_3070_URL=http://local-ai-server:8001
OPENCODE_URL=http://opencode-service:8002

# Routing thresholds
SMALL_TOKEN_THRESHOLD=2000
MEDIUM_TOKEN_THRESHOLD=16000

# Logging
LOG_LEVEL=INFO
```

## Force-Big Signals

Override gaming mode restrictions:

1. **Header**: `X-Force-Big: true`
2. **Model name**: `model = "big"` or `model = "3090"`
3. **Prompt tag**: Include `#force_big` in message

## Related

- [Local AI Unified Architecture](../../agents/plans/local-ai-unified-architecture.md) - Full architecture plan
- [Gaming PC Local AI](../../local-ai/README.md) - 3090 backend
- [Local AI App](../local-ai-app/README.md) - Web chat UI
