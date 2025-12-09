# n8n Workflows Status

## Current Status

✅ **n8n is running**: Container `n8n` is up (port 5678)  
✅ **AI Agent Webhook is running**: Container `ai-agent-webhook` is up (port 8100)

## Existing Workflows

### 1. **Docker Container Failure Monitor** ✅ (Imported, may be active)
- **Purpose**: Monitors all Docker containers for failures, crashes, or unhealthy states
- **Trigger**: Every 5 minutes
- **What it does**:
  - Checks all containers for failures (exit codes 1, 2, 130, 137, unhealthy, restarting)
  - Collects container logs, info, and resource usage
  - Sends events to AI Agent Webhook at `http://ai-agent-webhook:8100/webhook/ai-agent`
  - Optionally sends Telegram notifications
- **Status**: Imported into n8n (ID: `VMmvZLRBlym0seeC`), but **may or may not be active** - check n8n UI

### 2. **Docker Build Failure Monitor** ✅ (Imported, may be active)
- **Purpose**: Monitors Docker build failures
- **Trigger**: Every 10 minutes
- **What it does**:
  - Checks for failed Docker builds
  - Collects build logs
  - Sends events to AI Agent Webhook
- **Status**: Imported into n8n (ID: `WVfgCTR6nZklASb0`), but **may or may not be active** - check n8n UI

### 3. **Service Health Monitor** ✅ (Imported, may be active)
- **Purpose**: Monitors service health endpoints
- **Trigger**: Every 2 minutes
- **What it does**:
  - Checks HTTP endpoints for services
  - Detects 5xx errors and failures
  - Sends events to AI Agent Webhook
- **Status**: Imported into n8n (ID: `YwkC1oh0bGCcgPAU`), but **may or may not be active** - check n8n UI

### 4. **Docker Container Auto-Restart** ⚠️ (Just created, NOT imported yet)
- **Purpose**: Automatically restarts gluetun-dependent containers when they exit
- **Trigger**: Every 5 minutes
- **What it does**:
  - Checks gluetun health
  - Monitors nzbget, qbittorrent, slskd containers
  - Restarts containers that exited with code 128 (network namespace loss)
- **Status**: ✅ Workflow JSON created, but **NOT imported into n8n yet**

### 5. **Telegram AI Bot** (Multiple versions)
- `telegram-ai-bot.json` - Full version with OpenAI integration
- `telegram-ai-bot-minimal.json` - Minimal version
- `telegram-bot-step2.json` - Step 2 version
- `telegram-bot-test.json` - Test version
- `telegram-notifications.json` - Notification helper
- **Status**: Unknown - check n8n UI to see if any are imported/active

## AI Agent Webhook Service

### What It Is

The **AI Agent Webhook** (`http://ai-agent-webhook:8100`) is a bridge service between n8n workflows and AI agents (like Cursor/Claude).

### How It Works

```
n8n Workflow → Detects Event → Sends to Webhook → AI Agent Webhook → Stores Event → AI Agent Queries Events
```

1. **n8n workflows** detect issues (container failures, build failures, etc.)
2. **Workflows send events** to `http://ai-agent-webhook:8100/webhook/ai-agent`
3. **Webhook service** receives and stores events
4. **AI agent** (Cursor/Claude) can query events via API endpoints
5. **AI agent** analyzes events and provides recommendations

### Current Status

✅ **Service is running**: Container `ai-agent-webhook` on port 8100  
✅ **Health check**: `http://192.168.86.47:8100/health` should be accessible

### API Endpoints

- **POST `/webhook/ai-agent`**: Receive events from n8n workflows
- **GET `/events`**: List recent events
- **GET `/events/:event_id`**: Get specific event details
- **POST `/events/:event_id/analyze`**: Trigger AI analysis

### Webhook Secret

The webhook uses Bearer token authentication:
- **Secret**: `0e4c4ef968594f3bd1d77740646f88493efb015b21f9d74eb31e0308fd0b6d10`
- **Header**: `Authorization: Bearer <secret>`

## Checking Workflow Status

### To see if workflows are active:

1. **Open n8n**: `https://n8n.server.unarmedpuppy.com`
2. **Go to Workflows**: Click "Workflows" in the sidebar
3. **Check Active status**: Look for the toggle switch on each workflow
4. **View Executions**: Click "Executions" to see if workflows have run recently

### To check webhook service:

```bash
# Health check
curl http://192.168.86.47:8100/health

# List recent events
curl http://192.168.86.47:8100/events?limit=5
```

## What's Actually Running?

**We can't tell from here** - you need to check the n8n UI to see:
- Which workflows are **Active** (toggle switch)
- When they last ran (Executions tab)
- If they're successfully sending events to the webhook

## Recommendations

1. **Check n8n UI** to see which workflows are active
2. **Review execution history** to see if workflows are running
3. **Import the new auto-restart workflow** we just created
4. **Consider disabling** workflows you don't need (to reduce noise)
5. **Set up notifications** if you want alerts when events occur

## Next Steps

1. **Import auto-restart workflow**:
   - Open n8n UI
   - Import `docker-container-auto-restart.json`
   - Activate it

2. **Review existing workflows**:
   - Check which ones are active
   - Decide if you want to keep them all running
   - Adjust schedules if needed

3. **Test webhook service**:
   ```bash
   curl http://192.168.86.47:8100/health
   curl http://192.168.86.47:8100/events
   ```

4. **Monitor workflow executions** in n8n UI to see what's happening

