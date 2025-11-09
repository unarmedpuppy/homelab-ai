# AI Agent Webhook Service

This service receives events from n8n workflows and formats them for AI agent processing (Cursor/Claude).

## Overview

The webhook service acts as a bridge between n8n workflows and the AI agent:
1. Receives events from n8n workflows
2. Validates and formats the event data
3. Stores events for AI agent processing
4. Provides API endpoints for AI agent to query events

## Setup

### Option 1: Standalone Python Service

1. **Install dependencies**:
   ```bash
   cd apps/n8n/ai-agent-webhook
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.template .env
   nano .env  # Edit configuration
   ```

3. **Run the service**:
   ```bash
   python webhook_service.py
   ```

### Option 2: Docker Container

1. **Build and run**:
   ```bash
   cd apps/n8n/ai-agent-webhook
   docker-compose up -d
   ```

## Configuration

### Environment Variables

```bash
# Webhook Configuration
WEBHOOK_PORT=8080
WEBHOOK_SECRET=your-secret-token-here

# AI Agent Configuration
AI_AGENT_ENABLED=true
AI_AGENT_API_URL=https://api.cursor.sh/v1/chat  # Example
AI_AGENT_API_KEY=your-api-key-here

# Storage
EVENT_STORAGE_PATH=./events
EVENT_RETENTION_DAYS=7

# Server Information
SERVER_IP=192.168.86.47
SERVER_PATH=~/server
```

## API Endpoints

### POST /webhook/ai-agent

Receive events from n8n workflows.

**Headers**:
- `Content-Type: application/json`
- `Authorization: Bearer <webhook-secret>` (optional)

**Body**:
```json
{
  "event_type": "docker_container_failure",
  "severity": "high",
  "timestamp": "2025-01-XX 12:00:00",
  "source": "n8n-workflow",
  "workflow_name": "Docker Container Failure Monitor",
  "event_data": { ... },
  "context": { ... },
  "requested_action": "analyze_and_recommend"
}
```

**Response**:
```json
{
  "status": "received",
  "event_id": "evt_1234567890",
  "message": "Event received and queued for AI agent processing"
}
```

### GET /events

List recent events.

**Query Parameters**:
- `limit`: Number of events to return (default: 50)
- `event_type`: Filter by event type
- `severity`: Filter by severity (low, medium, high)
- `status`: Filter by status (pending, processed, resolved)

**Response**:
```json
{
  "events": [
    {
      "event_id": "evt_1234567890",
      "event_type": "docker_container_failure",
      "severity": "high",
      "timestamp": "2025-01-XX 12:00:00",
      "status": "pending"
    }
  ],
  "total": 1
}
```

### GET /events/:event_id

Get details of a specific event.

**Response**:
```json
{
  "event_id": "evt_1234567890",
  "event_type": "docker_container_failure",
  "severity": "high",
  "timestamp": "2025-01-XX 12:00:00",
  "status": "pending",
  "event_data": { ... },
  "ai_analysis": null,
  "ai_recommendations": null
}
```

### POST /events/:event_id/analyze

Trigger AI agent analysis for a specific event.

**Response**:
```json
{
  "status": "analyzing",
  "event_id": "evt_1234567890",
  "message": "AI agent analysis started"
}
```

## Integration with Cursor/Claude

The webhook service can be integrated with AI agents in several ways:

### 1. Direct API Integration

The service can call AI agent APIs directly when events are received.

### 2. Webhook to AI Agent

The service can send formatted events to AI agent webhooks.

### 3. Event Queue

The service stores events, and the AI agent queries the queue periodically.

## Usage

### Receiving Events from n8n

n8n workflows automatically send events to the webhook endpoint configured in the workflow.

### Querying Events from AI Agent

The AI agent (Cursor) can query events via the API endpoints:

```python
import requests

# Get pending events
response = requests.get('http://localhost:8080/events?status=pending&severity=high')
events = response.json()['events']

# Analyze an event
for event in events:
    response = requests.post(f'http://localhost:8080/events/{event["event_id"]}/analyze')
    analysis = response.json()
```

## Security

- **Authentication**: Use Bearer token authentication for webhook endpoint
- **Rate Limiting**: Implement rate limiting to prevent abuse
- **Validation**: Validate all incoming event payloads
- **HTTPS**: Use HTTPS in production

## Monitoring

The service logs all events and API requests. Check logs for:
- Failed webhook deliveries
- API errors
- Storage issues

## Troubleshooting

### Webhook Not Receiving Events

1. Check service is running: `curl http://localhost:8080/health`
2. Verify n8n workflow webhook URL is correct
3. Check authentication credentials
4. Review service logs

### Events Not Being Processed

1. Check event storage directory exists and is writable
2. Verify AI agent integration is configured
3. Check service logs for errors

