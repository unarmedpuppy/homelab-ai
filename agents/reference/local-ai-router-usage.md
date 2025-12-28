# Local AI Router Usage Guide

Complete reference for using the local AI router across different applications and platforms.

## Overview

The local AI router provides an **OpenAI-compatible API** that intelligently routes requests to multiple GPU backends (3070, 3090) with gaming mode awareness and autonomous agent capabilities.

**Base URL**: `https://local-ai-api.server.unarmedpuppy.com`

**Key Features**:
- OpenAI-compatible `/v1/chat/completions` endpoint
- Intelligent routing based on token count and complexity
- Gaming mode awareness (respects when you're playing games)
- Force-big override for complex tasks
- Autonomous agent endpoint for file/shell operations
- Streaming support
- Tool calling / function calling

## Quick Start

### Basic Chat Completion

```bash
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ]
  }'
```

### With Streaming

```bash
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Tell me a story"}],
    "stream": true
  }'
```

## Model Selection

### Auto Routing (Recommended)

Use `"model": "auto"` to let the router decide based on:
- Token count (< 2K → 3070, 2K-16K → 3090)
- Gaming mode status (prefers 3070 when gaming)
- Backend health
- Task complexity

### Explicit Model Selection

| Model Alias | Routes To | Use Case |
|-------------|-----------|----------|
| `auto` | Intelligent routing | Default, recommended |
| `small`, `fast` | 3070 | Quick responses, low complexity |
| `big`, `medium`, `3090`, `gaming-pc` | 3090 | Coding tasks, complex reasoning |
| Specific: `qwen2.5-14b-awq` | 3090 | Direct model selection |
| Specific: `deepseek-coder` | 3090 | Coding tasks |
| Specific: `llama3-8b` | 3090 | General purpose |

### Force-Big Override

When gaming mode is on, the 3090 is gated. Use force-big to override:

**Method 1: Header**
```bash
curl -X POST https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Force-Big: true" \
  -d '{"model": "auto", "messages": [...]}'
```

**Method 2: Model Name**
```bash
# Use "big" or "3090" as model
{"model": "big", "messages": [...]}
```

**Method 3: Prompt Tag**
```bash
# Include #force_big in your message
{"messages": [{"role": "user", "content": "Complex task #force_big"}]}
```

## Autonomous Agent Endpoint

The router includes an agent endpoint for autonomous tasks that can read/write files, execute shell commands, and perform multi-step operations.

### Run an Agent Task

```bash
curl -X POST https://local-ai-api.server.unarmedpuppy.com/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create a Python script that prints hello world",
    "working_directory": "/tmp",
    "model": "auto",
    "max_steps": 20
  }'
```

### Agent Tools

List available tools:
```bash
curl https://local-ai-api.server.unarmedpuppy.com/agent/tools
```

**Available Tools**:
- `read_file` - Read file contents (with optional line range)
- `write_file` - Create or overwrite files
- `edit_file` - Make precise edits using string replacement
- `run_shell` - Execute shell commands (with timeout & security)
- `search_files` - Find files by pattern or grep content
- `list_directory` - List directory contents
- `task_complete` - Signal task completion

### Agent Configuration

Default limits (configurable via environment variables):
- Max steps per run: 50
- Max retries for malformed responses: 3
- Allowed paths: `/tmp` (for security)
- Shell command timeout: 30 seconds

### Agent Use Cases

**File Operations**:
```json
{
  "task": "Read the configuration file at /etc/app/config.json and extract the database URL",
  "working_directory": "/etc/app"
}
```

**Code Generation**:
```json
{
  "task": "Create a FastAPI endpoint that returns the current time",
  "working_directory": "/tmp",
  "max_steps": 15
}
```

**System Administration**:
```json
{
  "task": "List all running Docker containers and save to containers.txt",
  "working_directory": "/tmp"
}
```

**Multi-step Tasks**:
```json
{
  "task": "Read server.log, count error messages, and create a summary report",
  "working_directory": "/var/log",
  "max_steps": 30
}
```

## n8n Integration

n8n has native support for OpenAI-compatible APIs. Here's how to use your local AI router:

### Option 1: OpenAI Node (Chat Completions)

**Setup Credentials**:
1. Go to n8n Credentials
2. Add new credential: `OpenAI API`
3. Configure:
   - **API Key**: `dummy-key` (any value - router doesn't require auth)
   - **Base URL**: `https://local-ai-api.server.unarmedpuppy.com/v1`

**Use in Workflow**:
```json
{
  "nodes": [
    {
      "parameters": {
        "resource": "chat",
        "model": "auto",
        "messages": {
          "values": [
            {
              "role": "user",
              "content": "={{ $json.question }}"
            }
          ]
        }
      },
      "type": "n8n-nodes-base.openAi",
      "credentials": {
        "openAiApi": {
          "name": "Local AI Router"
        }
      }
    }
  ]
}
```

### Option 2: HTTP Request Node (Agent Endpoint)

**Chat Completions**:
```json
{
  "parameters": {
    "method": "POST",
    "url": "https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions",
    "authentication": "none",
    "sendBody": true,
    "bodyParameters": {
      "parameters": [
        {
          "name": "model",
          "value": "auto"
        },
        {
          "name": "messages",
          "value": "={{ [{\"role\": \"user\", \"content\": $json.question}] }}"
        }
      ]
    },
    "options": {}
  },
  "type": "n8n-nodes-base.httpRequest"
}
```

**Agent Tasks**:
```json
{
  "parameters": {
    "method": "POST",
    "url": "https://local-ai-api.server.unarmedpuppy.com/agent/run",
    "sendBody": true,
    "bodyParameters": {
      "parameters": [
        {
          "name": "task",
          "value": "={{ $json.task }}"
        },
        {
          "name": "working_directory",
          "value": "/tmp"
        },
        {
          "name": "model",
          "value": "auto"
        },
        {
          "name": "max_steps",
          "value": 20
        }
      ]
    }
  },
  "type": "n8n-nodes-base.httpRequest"
}
```

### Example n8n Workflows

#### Workflow 1: AI-Powered Webhook Responder

```
Webhook Trigger → Extract Question → OpenAI Node (Local Router) → Format Response → Respond to Webhook
```

**Node Configuration**:
- **Webhook**: Accepts POST with `{"question": "..."}`
- **OpenAI Node**:
  - Credential: Local AI Router
  - Model: `auto`
  - Message: `{{ $json.question }}`
- **Respond to Webhook**: Return AI response

#### Workflow 2: Automated File Processing

```
Schedule Trigger → List Files → For Each File → Agent Node (Process File) → Save Results → Send Summary Email
```

**Agent Node Configuration**:
```json
{
  "task": "Read the file {{ $json.filepath }}, extract key information, and create a summary",
  "working_directory": "/data",
  "max_steps": 20
}
```

#### Workflow 3: Smart Content Moderator

```
Mattermost/Slack Message → OpenAI Node (Analyze) → If Inappropriate → Agent Node (Create Report) → Notify Admin
```

**OpenAI Node for Analysis**:
```json
{
  "model": "auto",
  "messages": [
    {
      "role": "system",
      "content": "Analyze if this message is inappropriate. Respond with YES or NO."
    },
    {
      "role": "user",
      "content": "={{ $json.message }}"
    }
  ]
}
```

#### Workflow 4: Force-Big for Complex Tasks

For computationally intensive tasks during gaming hours:

```json
{
  "parameters": {
    "method": "POST",
    "url": "https://local-ai-api.server.unarmedpuppy.com/v1/chat/completions",
    "headerParameters": {
      "parameters": [
        {
          "name": "X-Force-Big",
          "value": "true"
        }
      ]
    },
    "bodyParameters": {
      "parameters": [
        {
          "name": "model",
          "value": "big"
        },
        {
          "name": "messages",
          "value": "={{ $json.complexTask }}"
        }
      ]
    }
  }
}
```

## Python Integration

### Using OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://local-ai-api.server.unarmedpuppy.com/v1",
    api_key="dummy-key"  # Router doesn't require auth
)

# Chat completion
response = client.chat.completions.create(
    model="auto",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)
print(response.choices[0].message.content)

# Streaming
stream = client.chat.completions.create(
    model="auto",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### Agent Endpoint

```python
import requests

# Run agent task
response = requests.post(
    "https://local-ai-api.server.unarmedpuppy.com/agent/run",
    json={
        "task": "Create a Python script that prints hello world",
        "working_directory": "/tmp",
        "model": "auto",
        "max_steps": 20
    }
)

result = response.json()
print(f"Success: {result['success']}")
print(f"Final answer: {result['final_answer']}")
print(f"Total steps: {result['total_steps']}")

# List available tools
tools = requests.get("https://local-ai-api.server.unarmedpuppy.com/agent/tools")
print(tools.json())
```

## JavaScript/TypeScript Integration

```typescript
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'https://local-ai-api.server.unarmedpuppy.com/v1',
  apiKey: 'dummy-key', // Router doesn't require auth
});

// Chat completion
const response = await client.chat.completions.create({
  model: 'auto',
  messages: [
    { role: 'user', content: 'Hello!' }
  ],
});

console.log(response.choices[0].message.content);

// Agent task
const agentResponse = await fetch(
  'https://local-ai-api.server.unarmedpuppy.com/agent/run',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      task: 'Create a Python script that prints hello world',
      working_directory: '/tmp',
      model: 'auto',
      max_steps: 20
    })
  }
);

const result = await agentResponse.json();
console.log(result);
```

## Gaming Mode Endpoints

Check and control gaming mode:

```bash
# Get current status
curl https://local-ai-api.server.unarmedpuppy.com/health

# Enable gaming mode (via proxy to Windows PC)
curl -X POST https://local-ai-api.server.unarmedpuppy.com/gaming-mode?enable=true

# Disable gaming mode
curl -X POST https://local-ai-api.server.unarmedpuppy.com/gaming-mode?enable=false

# Stop all models on gaming PC
curl -X POST https://local-ai-api.server.unarmedpuppy.com/stop-all
```

## Best Practices

### Model Selection

✅ **DO**: Use `auto` for most requests - let the router decide
```json
{"model": "auto", "messages": [...]}
```

✅ **DO**: Use `big` for complex coding or reasoning tasks
```json
{"model": "big", "messages": [...]}
```

❌ **DON'T**: Hardcode specific models unless necessary
```json
{"model": "qwen2.5-14b-awq", ...}  // Only if you need this specific model
```

### Gaming Mode Respect

✅ **DO**: Trust the router's gaming mode awareness for non-critical tasks

✅ **DO**: Use force-big only when the task genuinely needs the 3090
```bash
-H "X-Force-Big: true"
```

❌ **DON'T**: Force-big for simple queries during gaming hours

### Agent Tasks

✅ **DO**: Be specific with task descriptions
```json
{"task": "Read config.json and extract the database URL, then save it to db_url.txt"}
```

✅ **DO**: Set appropriate max_steps based on task complexity
```json
{"max_steps": 10}  // Simple task
{"max_steps": 50}  // Complex multi-step task
```

❌ **DON'T**: Leave max_steps unlimited - use reasonable limits

### Error Handling

✅ **DO**: Handle backend unavailability
```python
try:
    response = client.chat.completions.create(...)
except Exception as e:
    if '503' in str(e):
        print("No backends available - check gaming mode or backend health")
```

✅ **DO**: Check agent task success
```python
result = requests.post(url, json=task).json()
if not result['success']:
    print(f"Task failed: {result['terminated_reason']}")
```

## Troubleshooting

### "No healthy backends available"

**Cause**: All backends are offline or gaming mode is on without force-big

**Solutions**:
1. Check health endpoint: `curl https://local-ai-api.server.unarmedpuppy.com/health`
2. If gaming mode is on and you need 3090, use force-big
3. Verify gaming PC (3090) is running and accessible

### Agent task not completing

**Cause**: Task exceeds max_steps or hits timeout

**Solutions**:
1. Increase `max_steps` for complex tasks
2. Break task into smaller subtasks
3. Check agent task response for `terminated_reason`

### Slow responses

**Cause**: Cold start (model not loaded) or routing to slower backend

**Solutions**:
1. First request to each model takes 2-3 minutes (model loading)
2. Subsequent requests are fast
3. Use `small` or `fast` model for quick responses
4. Check if gaming mode is forcing 3070 for large tasks

### Tool calling not working

**Cause**: Backend model doesn't support tool calling

**Solutions**:
1. Ensure using models with tool support: `qwen2.5-14b-awq`, `deepseek-coder`
2. Verify gaming PC containers have `--enable-auto-tool-choice` flag
3. Use agent endpoint for reliable tool execution

## API Reference

### Chat Completions Endpoint

**URL**: `POST /v1/chat/completions`

**Request Body**:
```json
{
  "model": "auto",          // Required: Model or alias
  "messages": [...],        // Required: Array of message objects
  "stream": false,          // Optional: Enable streaming
  "temperature": 0.7,       // Optional: Sampling temperature
  "max_tokens": null,       // Optional: Max tokens to generate
  "top_p": 1.0,            // Optional: Nucleus sampling
  "tools": [...],          // Optional: Tool definitions for function calling
  "tool_choice": "auto"    // Optional: How to use tools
}
```

**Response**:
```json
{
  "id": "...",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "qwen2.5-14b-awq",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

### Agent Run Endpoint

**URL**: `POST /agent/run`

**Request Body**:
```json
{
  "task": "Create a hello world script",
  "working_directory": "/tmp",
  "model": "auto",
  "max_steps": 50
}
```

**Response**:
```json
{
  "success": true,
  "final_answer": "Created hello_world.py successfully",
  "steps": [
    {
      "step_number": 1,
      "action": {...},
      "tool_result": "..."
    }
  ],
  "total_steps": 3,
  "terminated_reason": "completed"
}
```

### Health Endpoint

**URL**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "backends": {
    "3090": {
      "name": "Gaming PC (3090)",
      "healthy": true
    },
    "3070": {
      "name": "Home Server (3070)",
      "healthy": false,
      "reason": "not configured"
    }
  },
  "gaming_mode": false
}
```

## Related Documentation

- [Local AI Router README](../../apps/local-ai-router/README.md) - Service-specific documentation
- [Local AI Unified Architecture Plan](../plans/local-ai-unified-architecture.md) - Overall architecture
- [Gaming PC Local AI Setup](../../local-ai/README.md) - 3090 backend details

## Support

For issues or questions:
1. Check logs: `docker logs local-ai-router`
2. Verify health: `curl https://local-ai-api.server.unarmedpuppy.com/health`
3. Review gaming mode status
4. Check backend availability
