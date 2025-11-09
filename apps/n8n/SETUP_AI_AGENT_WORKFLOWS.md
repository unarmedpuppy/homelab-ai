# Setup Guide: AI Agent Workflows for n8n

This guide walks you through setting up n8n workflows that monitor server events and trigger an AI agent.

## Prerequisites

- n8n is installed and running
- Docker socket is accessible to n8n container
- Basic understanding of n8n workflows

## Step 1: Set Up AI Agent Webhook Service

### Option A: Docker (Recommended)

1. **Navigate to webhook service directory**:
   ```bash
   cd apps/n8n/ai-agent-webhook
   ```

2. **Create environment file**:
   ```bash
   cp .env.template .env
   nano .env  # Edit and set WEBHOOK_SECRET
   ```

3. **Start the service**:
   ```bash
   docker-compose up -d
   ```

4. **Verify it's running**:
   ```bash
   curl http://localhost:8080/health
   ```

### Option B: Standalone Python

1. **Install dependencies**:
   ```bash
   cd apps/n8n/ai-agent-webhook
   pip install -r requirements.txt
   ```

2. **Create environment file**:
   ```bash
   cp .env.template .env
   nano .env  # Edit configuration
   ```

3. **Run the service**:
   ```bash
   python webhook_service.py
   ```

## Step 2: Configure n8n Credentials

1. **Open n8n**: Navigate to `https://n8n.server.unarmedpuppy.com`

2. **Create Docker Socket Credential**:
   - Go to **Credentials** → **New**
   - Select **Execute Command** type
   - Name: `Docker Socket`
   - Configure to use Docker socket (already mounted in n8n container)

3. **Create AI Agent Webhook Credential**:
   - Go to **Credentials** → **New**
   - Select **HTTP Header Auth**
   - Name: `AI Agent Webhook Auth`
   - Header Name: `Authorization`
   - Header Value: `Bearer YOUR_WEBHOOK_SECRET` (from .env file)

## Step 3: Import Workflows

1. **Open n8n**: Navigate to `https://n8n.server.unarmedpuppy.com`

2. **Import workflows**:
   - Go to **Workflows** → **Import from File**
   - Import each workflow JSON file:
     - `workflows/docker-container-failure-monitor.json`
     - `workflows/docker-build-failure-monitor.json`
     - `workflows/service-health-monitor.json`

3. **Configure each workflow**:
   - Open the imported workflow
   - Update the **Call AI Agent Webhook** node:
     - Verify webhook URL is correct: `http://ai-agent-webhook:8080/webhook/ai-agent` (if using Docker) or `http://192.168.86.47:8080/webhook/ai-agent` (if standalone)
     - Verify credentials are set correctly
   - Update service list in **Service Health Monitor** workflow if needed

4. **Activate workflows**:
   - Toggle **Active** switch on each workflow
   - Verify workflows appear in **Executions** tab

## Step 4: Test Workflows

### Test Docker Container Failure Monitor

1. **Create a test container that will fail**:
   ```bash
   docker run --rm alpine sh -c "exit 1"
   ```

2. **Check n8n execution**:
   - Go to **Executions** in n8n
   - Find the execution for "Docker Container Failure Monitor"
   - Verify it detected the failure

3. **Check webhook received event**:
   ```bash
   curl http://localhost:8080/events?limit=5
   ```

### Test Service Health Monitor

1. **Stop a service temporarily**:
   ```bash
   docker stop homepage
   ```

2. **Wait 2-5 minutes** for workflow to run

3. **Check n8n execution**:
   - Verify workflow detected the failure
   - Check webhook received the event

4. **Restart the service**:
   ```bash
   docker start homepage
   ```

## Step 5: Integrate with AI Agent (Cursor)

The webhook service stores events that can be queried by the AI agent. To integrate:

1. **Query events from AI agent**:
   ```python
   import requests
   
   # Get high-severity pending events
   response = requests.get('http://localhost:8080/events?status=pending&severity=high')
   events = response.json()['events']
   
   # Analyze each event
   for event in events:
       print(f"Event: {event['event_type']} - {event['workflow_name']}")
       # Process event with AI agent
   ```

2. **Or use the analyze endpoint**:
   ```bash
   curl -X POST http://localhost:8080/events/evt_1234567890/analyze
   ```

## Step 6: Monitor and Maintain

### View Events

```bash
# List all events
curl http://localhost:8080/events

# List high-severity events
curl http://localhost:8080/events?severity=high

# List pending events
curl http://localhost:8080/events?status=pending
```

### Check Workflow Execution

1. Go to **Executions** in n8n
2. Filter by workflow name
3. Review execution logs and results

### Clean Up Old Events

The webhook service automatically cleans up events older than 7 days (configurable via `EVENT_RETENTION_DAYS`).

## Troubleshooting

### Workflow Not Triggering

1. **Check workflow is active**: Toggle should be ON
2. **Check schedule**: Verify trigger schedule is correct
3. **Check n8n logs**: `docker logs n8n`
4. **Test trigger manually**: Click "Execute Workflow" button

### Webhook Not Receiving Events

1. **Check webhook service is running**:
   ```bash
   curl http://localhost:8080/health
   ```

2. **Check webhook URL in workflow**: Verify it's correct
3. **Check authentication**: Verify Bearer token matches
4. **Check n8n execution logs**: Look for HTTP request errors

### Events Not Appearing

1. **Check event storage directory**: Verify it exists and is writable
2. **Check webhook service logs**: Look for errors
3. **Test webhook directly**:
   ```bash
   curl -X POST http://localhost:8080/webhook/ai-agent \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_SECRET" \
     -d '{"event_type":"test","severity":"low","timestamp":"2025-01-01T00:00:00","event_data":{}}'
   ```

## Next Steps

- [ ] Add more event types (disk space, network issues, etc.)
- [ ] Set up notifications (Slack, email, Discord)
- [ ] Create AI agent integration script
- [ ] Add auto-remediation for common issues
- [ ] Create dashboard for event monitoring

## Related Documentation

- [AI_AGENT_WORKFLOWS.md](./AI_AGENT_WORKFLOWS.md) - Workflow documentation
- [ai-agent-webhook/README.md](./ai-agent-webhook/README.md) - Webhook service docs
- [README.md](./README.md) - n8n setup and configuration

