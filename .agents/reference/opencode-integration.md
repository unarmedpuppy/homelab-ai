# OpenCode Integration with Local AI Router

Guide for configuring OpenCode to use your Local AI Router as a provider.

## Overview

The Local AI Router provides an OpenAI-compatible API that can be used as a backend provider for OpenCode. This enables:
- Local inference on your RTX 3070/3090 GPUs
- Intelligent routing based on request complexity
- Cost-free local processing (no API fees)
- Gaming mode awareness (graceful degradation when gaming)
- Cloud fallback when local GPUs are unavailable

## Prerequisites

1. **Local AI Router running** on your server
   - URL: `https://local-ai-api.server.unarmedpuppy.com`
   - Or internal: `http://192.168.86.47:8012`

2. **API Key** generated for authentication
   ```bash
   cd ~/server/apps/local-ai-router
   python scripts/manage-api-keys.py create "opencode"
   # Save the generated key - it's only shown once!
   ```

3. **OpenCode installed** on your machine
   - Install: `npm install -g @anthropic-ai/opencode` or via pip

## Configuration

### Config File Locations (Priority Order)

1. **Global**: `~/.config/opencode/opencode.json`
2. **Project**: `./opencode.json` or `./.opencode/opencode.json`
3. **Custom Path**: `OPENCODE_CONFIG` environment variable
4. **Custom Directory**: `OPENCODE_CONFIG_DIR` environment variable

Later configs override earlier ones.

### Option 1: Full Config File (Recommended)

Create `~/.config/opencode/opencode.json`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  // Set default model
  "model": "local-ai-router/auto",
  "provider": {
    "local-ai-router": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Local AI Router",
      "options": {
        "baseURL": "https://local-ai-api.server.unarmedpuppy.com/v1",
        "apiKey": "{env:LOCAL_AI_API_KEY}"
      },
      "models": {
        "auto": {
          "name": "Auto (Intelligent Routing)",
          "limit": {
            "context": 32768,
            "output": 8192
          }
        },
        "qwen2.5-14b-awq": {
          "name": "Qwen 2.5 14B (3090)",
          "limit": {
            "context": 32768,
            "output": 8192
          }
        },
        "qwen2.5-7b-awq": {
          "name": "Qwen 2.5 7B (3070)",
          "limit": {
            "context": 2048,
            "output": 1024
          }
        },
        "big": {
          "name": "Force 3090",
          "limit": {
            "context": 32768,
            "output": 8192
          }
        },
        "small": {
          "name": "Force 3070 (Fast)",
          "limit": {
            "context": 2048,
            "output": 1024
          }
        }
      }
    }
  }
}
```

Then set the environment variable:
```bash
export LOCAL_AI_API_KEY="lai_your_api_key_here"
```

### Option 2: Environment Variables Only

For quick setup without a config file:

```bash
# Required
export LOCAL_AI_API_KEY="lai_your_api_key_here"

# Then use /connect command in OpenCode TUI to add provider
opencode
# Type: /connect
# Select: Other
# Provider ID: local-ai-router
# API Key: (paste your key)
```

### Option 3: Per-Project Configuration

For project-specific settings, create `./opencode.json` or `./.opencode/opencode.json`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  // Use local router as default for this project
  "model": "local-ai-router/auto",
  "provider": {
    "local-ai-router": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Local AI Router",
      "options": {
        "baseURL": "https://local-ai-api.server.unarmedpuppy.com/v1",
        "apiKey": "{env:LOCAL_AI_API_KEY}"
      },
      "models": {
        "auto": {
          "name": "Auto (Intelligent Routing)",
          "limit": { "context": 32768, "output": 8192 }
        }
      }
    }
  },
  // Project-specific permissions
  "permission": {
    "edit": "allow",
    "bash": "allow"
  }
}
```

### Option 4: Direct API Key in Config (Not Recommended)

If you don't want to use environment variables:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "local-ai-router": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Local AI Router",
      "options": {
        "baseURL": "https://local-ai-api.server.unarmedpuppy.com/v1",
        "apiKey": "lai_your_actual_key_here"  // Not recommended - use {env:VAR}
      },
      "models": {
        "auto": { "name": "Auto" }
      }
    }
  }
}
```

**Warning**: Don't commit config files with hardcoded API keys!

## Model Selection

The router supports several model aliases for intelligent routing:

| Model | Description | When to Use |
|-------|-------------|-------------|
| `auto` | Intelligent routing based on complexity | **Recommended default** |
| `small`, `fast` | Routes to RTX 3070 (7B model) | Quick tasks, always available |
| `big`, `medium`, `3090` | Routes to RTX 3090 (14B model) | Complex coding, large context |
| `qwen2.5-14b-awq` | Explicit 3090 model | When you need the specific model |
| `qwen2.5-7b-awq` | Explicit 3070 model | When you need the specific model |

### Routing Logic

When using `model: "auto"`:
1. Token estimate < 2K tokens -> 3070 (fast path)
2. Gaming mode ON -> 3070 only (unless force-big)
3. Token 2K-16K + 3090 available -> 3090
4. Complex/long context -> Cloud fallback
5. Fallback chain: 3070 -> 3090 -> Z.ai -> Anthropic

## Force-Big Override

When gaming mode is active but you need the 3090:

```jsonc
{
  "provider": {
    "type": "openai",
    "baseURL": "https://local-ai-api.server.unarmedpuppy.com/v1",
    "apiKey": "lai_xxx",
    "model": "big"  // Forces 3090 even during gaming mode
  }
}
```

Or include `#force_big` in your prompt when using `auto` model.

## Streaming

The router supports full SSE streaming compatible with OpenAI SDKs.

**Default Mode**: Passthrough streaming (OpenAI SDK compatible)
- Standard SSE chunks forwarded directly from backend
- Works with OpenCode out of the box

**Enhanced Mode** (for debugging): Add header `X-Enhanced-Streaming: true`
- Includes status events (routing, loading, streaming, done)
- Not needed for normal OpenCode usage

## Testing Your Setup

### Quick Test (curl)

```bash
# Test chat completion
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer lai_your_api_key_here" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Say hello!"}]
  }'
```

### Test with OpenAI Python SDK

```python
#!/usr/bin/env python3
"""Test Local AI Router with OpenAI SDK"""

from openai import OpenAI

client = OpenAI(
    base_url="https://local-ai-api.server.unarmedpuppy.com/v1",
    api_key="lai_your_api_key_here"
)

# Non-streaming test
response = client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "Hello! What model are you?"}]
)
print(response.choices[0].message.content)

# Streaming test
print("\n--- Streaming ---")
stream = client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "Count from 1 to 5"}],
    stream=True
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print()
```

Save as `scripts/test-opencode-integration.py` and run:
```bash
python scripts/test-opencode-integration.py
```

## Troubleshooting

### Connection Issues

**Error**: `Connection refused` or `ECONNREFUSED`
- Verify router is running: `curl https://local-ai-api.server.unarmedpuppy.com/health`
- Check firewall allows port 8012
- Try internal URL if on same network: `http://192.168.86.47:8012`

**Error**: `401 Unauthorized`
- Verify API key is correct and not expired
- Check key is enabled: `python scripts/manage-api-keys.py list`
- Regenerate key if needed: `python scripts/manage-api-keys.py create "opencode-new"`

### Streaming Issues

**Error**: `Streaming not working`
- Ensure `stream: true` in request
- Check that backend (vLLM) supports streaming
- Verify no proxy is buffering SSE responses

**Error**: `Incomplete responses`
- Increase timeout in OpenCode config
- Check model context limits (7B model has 2K context)

### Model Not Available

**Error**: `503 Service Unavailable`
- Gaming PC may be offline or in gaming mode
- Check backend health: `curl https://local-ai-api.server.unarmedpuppy.com/health`
- Use `model: "small"` to force 3070 (always available)

**Error**: `Model loading timeout`
- First request after idle may take 60-90 seconds
- Models auto-stop after 10 minutes idle
- Wait for model to warm up

### Gaming Mode

**Symptom**: Requests failing or slower than expected
- Check gaming mode status: `curl https://local-ai-api.server.unarmedpuppy.com/health`
- Use `model: "big"` or `X-Force-Big: true` header to override
- Gaming mode gates 3090 access to preserve GPU for games

## Best Practices

### 1. Use `auto` Model for Most Cases
Let the router decide based on request complexity. It handles:
- Token estimation
- Backend availability
- Gaming mode awareness
- Automatic escalation

### 2. Reserve `big` for Specific Needs
Only explicitly request 3090 when you:
- Know you have large context (>2K tokens)
- Need the 14B model's capabilities specifically
- Are willing to wait if gaming mode is active

### 3. Handle Errors Gracefully
The router has fallback chains, but your code should handle:
- Timeouts (models need warm-up time)
- 503 errors (all backends unavailable)
- Rate limiting (if using cloud fallback)

### 4. Memory System (Optional)
Enable conversation memory for persistent chat history:

```bash
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer lai_xxx" \
  -H "X-Enable-Memory: true" \
  -H "X-User-ID: opencode-user" \
  -H "X-Project: opencode" \
  -d '{"model": "auto", "messages": [...]}'
```

## URLs Reference

| Context | URL |
|---------|-----|
| External (HTTPS) | `https://local-ai-api.server.unarmedpuppy.com` |
| Server localhost | `http://localhost:8012` |
| Internal network | `http://192.168.86.47:8012` |
| Docker network | `http://local-ai-router:8000` |

## Related Documentation

- [Local AI Router README](../../apps/local-ai-router/README.md) - Full router documentation
- [Local AI Router Reference](./local-ai-router.md) - Quick reference
- [API Key Management](./local-ai-router.md#api-key-management) - Managing API keys
- [Memory Headers](./local-ai-router.md#memory-headers) - Conversation persistence
