# n8n AI Agent Workflows - Setup Complete Summary

## ✅ Completed

### 1. Workflows Imported
All three workflows have been successfully imported into your n8n instance:

- **Docker Container Failure Monitor** (ID: `VMmvZLRBlym0seeC`)
- **Docker Build Failure Monitor** (ID: `WVfgCTR6nZklASb0`)
- **Service Health Monitor** (ID: `YwkC1oh0bGCcgPAU`)

### 2. AI Agent Webhook Service
✅ **Running and healthy**
- **URL**: `http://ai-agent-webhook:8100` (from Docker network)
- **External URL**: `http://192.168.86.47:8100`
- **Health Check**: `http://localhost:8100/health` ✅
- **Webhook Endpoint**: `http://ai-agent-webhook:8100/webhook/ai-agent`
- **Webhook Secret**: `0e4c4ef968594f3bd1d77740646f88493efb015b21f9d74eb31e0308fd0b6d10`

### 3. Workflow Webhook URLs
✅ **Updated** (if script ran successfully)
- All workflows now point to: `http://ai-agent-webhook:8100/webhook/ai-agent`

## ⏳ Manual Configuration Required

### Step 1: Configure Credentials in n8n UI

Open n8n: `https://n8n.server.unarmedpuppy.com`

#### A. Docker Socket Credential

1. Go to **Credentials** → **New**
2. Select **Execute Command** type
3. Name: `Docker Socket`
4. Save (Docker socket is already mounted in n8n container)

#### B. AI Agent Webhook Auth Credential

1. Go to **Credentials** → **New**
2. Select **HTTP Header Auth** type
3. Name: `AI Agent Webhook Auth`
4. **Header Name**: `Authorization`
5. **Header Value**: `Bearer 0e4c4ef968594f3bd1d77740646f88493efb015b21f9d74eb31e0308fd0b6d10`
6. Save

### Step 2: Assign Credentials to Workflows

For each workflow:

1. **Docker Container Failure Monitor**
   - Open the workflow
   - For each **Execute Command** node:
     - "Check All Containers"
     - "Get Container Logs"
     - "Get Container Info"
     - "Get Resource Usage"
   - Assign **"Docker Socket"** credential to each
   - For **"Call AI Agent Webhook"** node:
     - Assign **"AI Agent Webhook Auth"** credential
   - Save workflow

2. **Docker Build Failure Monitor**
   - Open the workflow
   - For **Execute Command** nodes, assign **"Docker Socket"** credential
   - For **"Call AI Agent Webhook"** node, assign **"AI Agent Webhook Auth"** credential
   - Save workflow

3. **Service Health Monitor**
   - Open the workflow
   - For **"Call AI Agent Webhook"** node, assign **"AI Agent Webhook Auth"** credential
   - Save workflow

### Step 3: Verify Webhook URLs

Check that each workflow's "Call AI Agent Webhook" node has:
- **URL**: `http://ai-agent-webhook:8100/webhook/ai-agent`
- **Credential**: "AI Agent Webhook Auth" selected

### Step 4: Activate Workflows

1. Open each workflow
2. Toggle the **Active** switch (top right) to enable
3. Workflows will now run on their schedules:
   - **Docker Container Failure Monitor**: Every 5 minutes
   - **Docker Build Failure Monitor**: Every 10 minutes
   - **Service Health Monitor**: Every 2 minutes

## Testing

### Test Webhook Service
```bash
curl http://localhost:8100/health
# Should return: {"status":"healthy","timestamp":"...","event_count":0}
```

### Test Workflow
1. Manually execute a workflow in n8n
2. Check execution logs
3. Verify event was received:
   ```bash
   curl http://localhost:8100/events?limit=5
   ```

### Test Event Processing
```bash
# Send a test event
curl -X POST http://localhost:8100/webhook/ai-agent \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 0e4c4ef968594f3bd1d77740646f88493efb015b21f9d74eb31e0308fd0b6d10" \
  -d '{
    "event_type": "test",
    "severity": "low",
    "timestamp": "2025-11-09T20:00:00Z",
    "event_data": {"test": true},
    "source": "manual-test"
  }'

# Check events
curl http://localhost:8100/events
```

## Monitoring

### View Events
```bash
# List all events
curl http://localhost:8100/events

# List high-severity events
curl http://localhost:8100/events?severity=high

# List pending events
curl http://localhost:8100/events?status=pending
```

### Check Workflow Executions
1. Open n8n: `https://n8n.server.unarmedpuppy.com`
2. Go to **Executions** tab
3. Filter by workflow name
4. Review execution logs and results

## Troubleshooting

### Webhook Not Receiving Events
- Check webhook service is running: `docker ps | grep ai-agent-webhook`
- Check webhook URL in workflow is correct
- Verify credential is assigned
- Check n8n execution logs for errors

### Docker Commands Failing
- Verify Docker socket credential is assigned to Execute Command nodes
- Check n8n container has access to Docker socket: `docker inspect n8n | grep -i docker`
- Review workflow execution logs

### Workflows Not Triggering
- Verify workflows are **Active**
- Check schedule triggers are configured correctly
- Review n8n execution logs

## Next Steps

1. ✅ Complete manual credential configuration (Steps 1-2 above)
2. ✅ Activate workflows (Step 4 above)
3. Monitor workflow executions for a few hours
4. Check webhook service receives events
5. Set up AI agent integration to query events (optional)

## Files Created

- `apps/n8n/workflows/*.json` - Workflow definitions
- `apps/n8n/ai-agent-webhook/` - Webhook service
- `apps/n8n/import-workflows.sh` - Import script
- `apps/n8n/update-workflow-webhooks.sh` - Webhook URL update script
- `apps/n8n/configure-credentials.md` - Credential setup guide
- `apps/n8n/SETUP_COMPLETE.md` - This file

## Quick Reference

- **n8n URL**: `https://n8n.server.unarmedpuppy.com`
- **Webhook Service**: `http://ai-agent-webhook:8100`
- **Webhook Secret**: `0e4c4ef968594f3bd1d77740646f88493efb015b21f9d74eb31e0308fd0b6d10`
- **API Key**: Stored in `apps/n8n/.env.local` (not in git)

