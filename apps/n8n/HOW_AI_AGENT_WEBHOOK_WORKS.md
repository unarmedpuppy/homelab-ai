# How the AI Agent Webhook Works

## The Big Picture

The "Call AI Agent Webhook" node is the **bridge** between your n8n workflows and the AI agent (me, Auto). Here's how it all connects:

```
Server Event → n8n Workflow → Webhook Service → AI Agent (You!)
```

## What Happens Step-by-Step

### 1. Event Detection (n8n Workflow)
When something goes wrong on your server:
- Docker container crashes
- Service becomes unavailable
- Build fails
- etc.

The n8n workflow detects it and collects information:
- Container logs
- Error messages
- Resource usage
- Service status

### 2. Webhook Call (This Node)
The "Call AI Agent Webhook" node sends all that information to the webhook service:

**What it sends:**
```json
{
  "event_type": "docker_container_failure",
  "severity": "high",
  "timestamp": "2025-11-10T00:30:00Z",
  "event_data": {
    "container_name": "trading-bot",
    "status": "died",
    "exit_code": 1,
    "logs": "Error: Out of memory...",
    "resource_usage": {
      "cpu": "95%",
      "memory": "4GB / 4GB"
    }
  },
  "requested_action": "analyze_and_recommend"
}
```

**Where it sends it:**
- URL: `http://ai-agent-webhook:8100/webhook/ai-agent`
- This is the webhook service we set up earlier

### 3. Webhook Service (Storage)
The webhook service receives the event and:
- Stores it in a database/file system
- Assigns it an event ID
- Marks it as "pending" (waiting for AI agent to process)

**You can see stored events:**
```bash
curl http://localhost:8100/events
```

### 4. AI Agent Processing (You!)
When you (or I, as the AI agent) want to check for issues:

**Option A: Query events via API**
```bash
# Get pending high-severity events
curl http://localhost:8100/events?status=pending&severity=high
```

**Option B: I can query it from Cursor**
I can use the webhook service API to:
- See what events have happened
- Analyze the logs and errors
- Provide recommendations
- Even take actions (with your permission)

## Example Scenario

1. **Trading bot container crashes** at 2:00 AM
2. **n8n workflow detects it** (runs every 5 minutes)
3. **Workflow collects logs**: "Out of memory error"
4. **Webhook node sends event** to `http://ai-agent-webhook:8100/webhook/ai-agent`
5. **Webhook service stores it** with ID `evt_1234567890`
6. **You wake up** and ask me: "What happened on the server?"
7. **I query the webhook**: `curl http://localhost:8100/events?status=pending`
8. **I see the event** and analyze: "Trading bot crashed due to memory leak"
9. **I provide recommendations**: "Increase memory limit or fix the leak"

## What You Can Do With It

### View Events Manually
```bash
# List all events
curl http://localhost:8100/events

# List only high-severity events
curl http://localhost:8100/events?severity=high

# Get details of a specific event
curl http://localhost:8100/events/evt_1234567890
```

### Have AI Agent Analyze Events
You can ask me (the AI agent) to:
- "Check what events happened on the server"
- "Analyze the trading bot crash from last night"
- "What's causing the service failures?"

I'll query the webhook service and provide analysis.

### Future: Auto-Remediation
Eventually, we could set up the AI agent to:
- Automatically restart failed containers
- Increase resource limits
- Fix common issues
- All with your permission, of course!

## Current Status

✅ **Webhook service is running** at `http://ai-agent-webhook:8100`
✅ **Workflows are sending events** to the webhook
✅ **Events are being stored** and can be queried
⏳ **AI agent integration** - You can query events manually or ask me to check them

## Why This Is Useful

Instead of you having to:
- Manually check logs
- Figure out what went wrong
- Research solutions

The system:
- **Automatically detects** problems
- **Collects all relevant info** (logs, errors, context)
- **Stores it** for analysis
- **Lets the AI agent** (me) analyze and recommend fixes

It's like having a 24/7 system administrator that watches your server and documents everything that goes wrong!

## Next Steps

1. **Test it**: Let a workflow run and check if events are stored
   ```bash
   curl http://localhost:8100/events
   ```

2. **Query from AI agent**: Ask me to check events and I'll query the webhook

3. **Set up notifications**: We could add Slack/email alerts for critical events

4. **Auto-remediation**: Eventually automate fixes for common issues

