# n8n AI Agent Workflows

This document describes the n8n workflows that monitor server events and trigger an AI agent for automated troubleshooting and response.

## Overview

The AI Agent workflows enable automated monitoring and response to server events such as:
- Failed Docker container builds
- Container crashes or unhealthy states
- Service failures
- High resource usage
- Disk space issues
- Network connectivity problems

## Architecture

```
Server Events → n8n Workflows → AI Agent Webhook → AI Agent (Cursor/Claude) → Actions
```

### Components

1. **Event Sources**: Docker events, system metrics, log monitoring
2. **n8n Workflows**: Process events, filter, and trigger webhooks
3. **AI Agent Webhook**: Receives events and formats them for AI processing
4. **AI Agent**: Analyzes events and provides recommendations/actions

## Workflows

### 1. Docker Container Failure Monitor

**Purpose**: Monitors Docker containers for failures, crashes, or unhealthy states.

**Trigger**: 
- Scheduled check every 5 minutes
- Real-time Docker events (via Docker socket)

**Events Monitored**:
- Container status changes (started, stopped, died, unhealthy)
- Container exit codes (non-zero = failure)
- Health check failures
- OOM (Out of Memory) kills

**Actions**:
- Collect container logs (last 100 lines)
- Get container configuration
- Check resource usage
- Trigger AI agent webhook with event details

### 2. Docker Build Failure Monitor

**Purpose**: Monitors Docker build failures.

**Trigger**:
- Docker build events
- Scheduled check of recent build history

**Events Monitored**:
- Build failures
- Image pull failures
- Build timeout errors

**Actions**:
- Collect build logs
- Identify failed build stage
- Check Dockerfile syntax
- Trigger AI agent webhook with build context

### 3. Service Health Monitor

**Purpose**: Monitors service health endpoints and metrics.

**Trigger**:
- Scheduled health checks every 2 minutes
- HTTP endpoint failures

**Events Monitored**:
- HTTP 5xx errors
- Health check endpoint failures
- Response time degradation
- Service unavailability

**Actions**:
- Check service logs
- Verify dependencies
- Check resource usage
- Trigger AI agent webhook

### 4. Resource Usage Monitor

**Purpose**: Monitors system resources and alerts on high usage.

**Trigger**:
- Scheduled check every 5 minutes

**Events Monitored**:
- CPU usage > 80%
- Memory usage > 85%
- Disk usage > 90%
- Network bandwidth spikes

**Actions**:
- Identify resource-intensive processes
- Check container resource limits
- Trigger AI agent webhook with resource data

### 5. Disk Space Monitor

**Purpose**: Monitors disk space and alerts on low space.

**Trigger**:
- Scheduled check every 15 minutes

**Events Monitored**:
- Disk usage > 85% (warning)
- Disk usage > 95% (critical)
- Inode usage > 90%

**Actions**:
- Identify large files/directories
- Check Docker volumes size
- Trigger AI agent webhook with disk analysis

## AI Agent Webhook Integration

### Webhook Endpoint

The AI agent webhook receives events from n8n and formats them for AI processing.

**Endpoint**: `https://n8n.server.unarmedpuppy.com/webhook/ai-agent`

**Payload Format**:
```json
{
  "event_type": "docker_container_failure",
  "severity": "high",
  "timestamp": "2025-01-XX 12:00:00",
  "source": "n8n-workflow",
  "workflow_name": "Docker Container Failure Monitor",
  "event_data": {
    "container_name": "trading-bot",
    "container_id": "abc123...",
    "status": "died",
    "exit_code": 1,
    "error_message": "...",
    "logs": "...",
    "resource_usage": {
      "cpu": "45%",
      "memory": "2.1GB / 4GB"
    }
  },
  "context": {
    "server_ip": "192.168.86.47",
    "server_path": "~/server"
  },
  "requested_action": "analyze_and_recommend"
}
```

### AI Agent Response

The AI agent processes the event and can:
1. **Analyze**: Review logs, identify root cause
2. **Recommend**: Suggest fixes or actions
3. **Execute** (optional): Automatically fix issues (with permission)

**Response Format**:
```json
{
  "analysis": {
    "root_cause": "Out of memory error due to memory leak",
    "confidence": "high",
    "recommendations": [
      "Increase container memory limit",
      "Check for memory leaks in application code",
      "Restart container with increased memory"
    ]
  },
  "actions_taken": [],
  "actions_available": [
    {
      "action": "restart_container",
      "description": "Restart the failed container",
      "requires_permission": true
    },
    {
      "action": "increase_memory_limit",
      "description": "Update docker-compose.yml with higher memory limit",
      "requires_permission": true
    }
  ]
}
```

## Setup Instructions

### 1. Import Workflows

1. Open n8n: `https://n8n.server.unarmedpuppy.com`
2. Go to **Workflows** → **Import from File**
3. Import each workflow JSON file:
   - `workflows/docker-container-failure-monitor.json`
   - `workflows/docker-build-failure-monitor.json`
   - `workflows/service-health-monitor.json`
   - `workflows/resource-usage-monitor.json`
   - `workflows/disk-space-monitor.json`

### 2. Configure Credentials

Each workflow needs credentials configured:

**Docker Socket**:
- Type: Execute Command
- Command: `docker`
- Use Docker socket mounted in n8n container

**HTTP Request**:
- Configure webhook URL: `https://n8n.server.unarmedpuppy.com/webhook/ai-agent`
- Method: POST
- Authentication: Bearer token (if configured)

### 3. Activate Workflows

1. Open each workflow
2. Review and adjust settings as needed
3. Click **Active** toggle to enable
4. Verify workflows are running in **Executions** tab

### 4. Test Workflows

Test each workflow by:
1. Manually triggering a test event
2. Checking webhook receives the event
3. Verifying AI agent processes the event

## Workflow Configuration

### Environment Variables

Add to `apps/n8n/.env`:

```bash
# AI Agent Webhook Configuration
AI_AGENT_WEBHOOK_URL=https://n8n.server.unarmedpuppy.com/webhook/ai-agent
AI_AGENT_WEBHOOK_SECRET=your-secret-token-here

# Server Information
SERVER_IP=192.168.86.47
SERVER_PATH=~/server
SERVER_SSH_USER=unarmedpuppy
SERVER_SSH_PORT=4242
```

### Webhook Security

1. **Authentication**: Use Bearer token authentication
2. **Rate Limiting**: Limit webhook calls to prevent abuse
3. **Validation**: Validate webhook payloads before processing

## Monitoring Workflow Execution

### View Executions

1. Go to **Executions** in n8n
2. Filter by workflow name
3. View execution details, logs, and results

### Alerts

Set up alerts for:
- Workflow execution failures
- High event frequency
- AI agent webhook failures

## Customization

### Adding New Event Types

1. Create new workflow in n8n
2. Add trigger node (Schedule, Webhook, or Docker Events)
3. Add processing nodes (filter, transform, enrich)
4. Add HTTP Request node to call AI agent webhook
5. Export workflow JSON and add to this repo

### Modifying Event Filters

Edit workflow nodes to:
- Filter specific containers/services
- Adjust severity thresholds
- Change check intervals
- Add custom conditions

## Troubleshooting

### Workflow Not Triggering

1. Check workflow is **Active**
2. Verify trigger configuration
3. Check n8n logs: `docker logs n8n`
4. Test trigger manually

### Webhook Not Receiving Events

1. Verify webhook URL is correct
2. Check authentication credentials
3. Test webhook endpoint directly
4. Check n8n execution logs for errors

### AI Agent Not Responding

1. Verify AI agent webhook service is running
2. Check webhook service logs
3. Test webhook endpoint with curl
4. Verify payload format matches expected structure

## Future Enhancements

- [ ] Add Slack/Discord notifications
- [ ] Add email alerts for critical events
- [ ] Implement auto-remediation for common issues
- [ ] Add event history and analytics
- [ ] Create dashboard for event monitoring
- [ ] Add machine learning for anomaly detection

## Related Documentation

- [n8n README](./README.md) - n8n setup and configuration
- [SERVER_AGENT_PROMPT.md](../docs/SERVER_AGENT_PROMPT.md) - AI agent guidelines
- [APPS_DOCUMENTATION.md](../docs/APPS_DOCUMENTATION.md) - Application details

