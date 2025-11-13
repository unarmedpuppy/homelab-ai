# Agent Communication Protocol

## Overview

The Agent Communication Protocol provides a standardized way for agents to communicate with each other. It enables structured messaging, coordination, handoffs, and escalation.

## Message Types

### 1. Request
**Purpose**: Ask for help, information, or action from another agent.

**Characteristics**:
- Requires a response
- Has priority level
- Can be escalated if not responded to
- Links to related task (optional)

**When to use**:
- Need help with a task
- Need information from another agent
- Need another agent to perform an action
- Need coordination on shared work

**Example**:
```yaml
type: request
priority: high
subject: Need help with Docker deployment
content: "I'm stuck on deploying service X. Can you help troubleshoot?"
```

### 2. Response
**Purpose**: Reply to a request from another agent.

**Characteristics**:
- Links to original message
- Resolves the request
- Can include solution, information, or status update

**When to use**:
- Replying to a request
- Providing requested information
- Confirming action taken

**Example**:
```yaml
type: response
related_message_id: MSG-2025-01-13-001
subject: Re: Need help with Docker deployment
content: "I've reviewed the issue. The problem is in the docker-compose.yml file..."
```

### 3. Notification
**Purpose**: Inform other agents about findings, updates, or important information.

**Characteristics**:
- One-way communication
- No response required
- Can be informational or warning
- Useful for sharing discoveries

**When to use**:
- Sharing important findings
- Notifying about completed work
- Warning about issues
- Broadcasting updates

**Example**:
```yaml
type: notification
priority: medium
subject: Port conflict discovered
content: "Found that port 8086 is already in use by Grafana Stack. Updated agent-monitoring to use 8087."
```

### 4. Escalation
**Purpose**: Escalate an issue that requires immediate attention or human intervention.

**Characteristics**:
- High or urgent priority
- Requires immediate attention
- May need human review
- Should include context and attempted solutions

**When to use**:
- Critical issue that can't be resolved
- Need human decision
- Security concern
- System-wide problem

**Example**:
```yaml
type: escalation
priority: urgent
subject: Critical: Service deployment failed
content: "Service X failed to deploy after 3 attempts. Error: [details]. Need human review."
```

## Priority Levels

### Low
- **Response Time**: Within 24 hours
- **Use Cases**: General questions, non-urgent requests
- **Example**: "Can you share your approach to X?"

### Medium
- **Response Time**: Within 4 hours
- **Use Cases**: Important requests, coordination needs
- **Example**: "Need to coordinate on shared task"

### High
- **Response Time**: Within 1 hour
- **Use Cases**: Blocking issues, urgent requests
- **Example**: "Blocked on task, need help immediately"

### Urgent
- **Response Time**: Within 15 minutes
- **Use Cases**: Critical issues, system problems
- **Example**: "Service down, need immediate help"

## Message Format

### File Structure
Messages are stored as Markdown files with YAML frontmatter:

```yaml
---
message_id: MSG-2025-01-13-001
from_agent: agent-001
to_agent: agent-002
type: request
priority: high
status: pending
subject: Brief subject line
created_at: 2025-01-13T10:30:00Z
acknowledged_at: null
resolved_at: null
related_task_id: T1.1
related_message_id: null
---

# Message Content

Full message body in markdown format.

Can include:
- Code blocks
- Lists
- Links
- Any markdown formatting
```

### Message Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message_id` | string | Yes | Unique message ID (format: MSG-YYYY-MM-DD-###) |
| `from_agent` | string | Yes | Agent ID sending the message |
| `to_agent` | string | Yes | Agent ID receiving (or "all" for broadcast) |
| `type` | enum | Yes | request, response, notification, escalation |
| `priority` | enum | Yes | low, medium, high, urgent |
| `status` | enum | Yes | pending, acknowledged, in_progress, resolved, escalated |
| `subject` | string | Yes | Brief subject line |
| `created_at` | datetime | Yes | ISO 8601 timestamp |
| `acknowledged_at` | datetime | No | When message was acknowledged |
| `resolved_at` | datetime | No | When message was resolved |
| `related_task_id` | string | No | Related task ID (if applicable) |
| `related_message_id` | string | No | Original message ID (for responses) |

## Message Status Flow

```
pending → acknowledged → in_progress → resolved
   ↓
escalated
```

### Status Definitions

- **pending**: Message created, not yet acknowledged
- **acknowledged**: Recipient has seen and acknowledged the message
- **in_progress**: Recipient is working on the request
- **resolved**: Request completed or issue resolved
- **escalated**: Issue escalated to human or higher priority

## Response Expectations

### For Requests

1. **Acknowledge** within priority timeframe:
   - Urgent: 15 minutes
   - High: 1 hour
   - Medium: 4 hours
   - Low: 24 hours

2. **Respond** with:
   - Information requested
   - Action taken
   - Status update
   - Or escalation if unable to help

3. **Update status** as you work:
   - `acknowledged` → `in_progress` → `resolved`

### For Notifications

- No response required
- Can acknowledge if relevant
- Can create follow-up request if needed

### For Escalations

- Immediate attention required
- May need human review
- Should include all context

## Message Storage

### Directory Structure
```
agents/communication/
├── protocol.md          # This file
├── README.md            # Usage guide
└── messages/            # Message files
    ├── index.json       # Message index for quick lookups
    └── MSG-*.md         # Individual message files
```

### Message Index
The `index.json` file provides quick lookups:
```json
{
  "messages": [
    {
      "message_id": "MSG-2025-01-13-001",
      "from_agent": "agent-001",
      "to_agent": "agent-002",
      "type": "request",
      "priority": "high",
      "status": "pending",
      "created_at": "2025-01-13T10:30:00Z",
      "file": "messages/MSG-2025-01-13-001.md"
    }
  ]
}
```

## Best Practices

### Sending Messages

1. **Be Clear**: Use clear, concise subject lines
2. **Provide Context**: Include relevant information
3. **Set Priority**: Use appropriate priority level
4. **Link Tasks**: Link to related tasks when applicable
5. **Follow Up**: Check for responses within expected timeframe

### Receiving Messages

1. **Check Regularly**: Check messages at start of session
2. **Acknowledge Promptly**: Acknowledge within priority timeframe
3. **Update Status**: Update status as you work
4. **Respond Thoroughly**: Provide complete responses
5. **Escalate When Needed**: Don't hesitate to escalate if stuck

### Message Content

1. **Be Specific**: Include specific details and context
2. **Include Examples**: Provide examples when helpful
3. **Reference Resources**: Link to relevant docs/files
4. **Show Attempts**: Describe what you've already tried
5. **Ask Clear Questions**: Make it easy to respond

## Integration with Other Systems

### Task Coordination
- Link messages to tasks using `related_task_id`
- Messages can be created when tasks are blocked
- Task updates can trigger notifications

### Memory System
- Important communications can be recorded in memory
- Patterns from communications can be stored
- Decisions made via communication should be recorded

### Agent Monitoring
- Message sending/receiving is logged as activity
- Message response times tracked
- Communication patterns visible in dashboard

## Examples

### Example 1: Request for Help

```yaml
---
message_id: MSG-2025-01-13-001
from_agent: agent-001
to_agent: agent-002
type: request
priority: high
status: pending
subject: Need help with Traefik configuration
created_at: 2025-01-13T10:30:00Z
related_task_id: T1.5
---

# Need Help with Traefik Configuration

I'm working on task T1.5 (Add subdomain for new service) and I'm stuck on the Traefik label configuration.

**What I've tried:**
- Reviewed existing Traefik configurations in `apps/plex/docker-compose.yml`
- Read the Traefik documentation
- Checked the `add-subdomain` skill

**What I need:**
- Confirmation on the correct Traefik label format
- Example of HTTPS redirect configuration
- Best practices for service port mapping

**Context:**
- Service: `myapp`
- Subdomain: `myapp.server.unarmedpuppy.com`
- Internal port: 80
- External port: 8080

Can you help?
```

### Example 2: Response with Solution

```yaml
---
message_id: MSG-2025-01-13-002
from_agent: agent-002
to_agent: agent-001
type: response
priority: medium
status: resolved
subject: Re: Need help with Traefik configuration
created_at: 2025-01-13T10:45:00Z
related_message_id: MSG-2025-01-13-001
---

# Re: Need help with Traefik configuration

Here's the correct Traefik configuration for your service:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myapp-redirect.rule=Host(`myapp.server.unarmedpuppy.com`)"
  - "traefik.http.routers.myapp-redirect.entrypoints=web"
  - "traefik.http.middlewares.myapp-redirect.redirectscheme.scheme=https"
  - "traefik.http.routers.myapp-redirect.middlewares=myapp-redirect"
  - "traefik.http.routers.myapp.rule=Host(`myapp.server.unarmedpuppy.com`)"
  - "traefik.http.routers.myapp.entrypoints=websecure"
  - "traefik.http.routers.myapp.tls.certresolver=myresolver"
  - "traefik.http.routers.myapp.service=myapp"
  - "traefik.http.services.myapp.loadbalancer.server.port=80"
  - "traefik.docker.network=my-network"
```

**Key points:**
- Use internal port (80) in loadbalancer.server.port
- Service name should match docker-compose service name
- Always include HTTPS redirect middleware

See `agents/apps/agent-monitoring/docker-compose.yml` for a complete example.
```

### Example 3: Notification

```yaml
---
message_id: MSG-2025-01-13-003
from_agent: agent-001
to_agent: all
type: notification
priority: medium
status: resolved
subject: Port conflict resolved
created_at: 2025-01-13T11:00:00Z
---

# Port Conflict Resolved

**Issue**: Port 8086 was already in use by existing Grafana Stack InfluxDB.

**Resolution**: Updated agent-monitoring to use port 8087 instead.

**Files Changed**:
- `agents/apps/agent-monitoring/docker-compose.yml`
- All documentation references

**Impact**: No conflicts, all services can run simultaneously.

This is a notification - no response needed.
```

### Example 4: Escalation

```yaml
---
message_id: MSG-2025-01-13-004
from_agent: agent-001
to_agent: all
type: escalation
priority: urgent
status: escalated
subject: Critical: Service deployment failed repeatedly
created_at: 2025-01-13T12:00:00Z
related_task_id: T1.5
---

# Critical: Service Deployment Failed

**Issue**: Service `myapp` has failed to deploy after 3 attempts.

**Error**: 
```
Error: Container failed to start
Exit code: 1
Logs: [error details]
```

**Attempted Solutions**:
1. Verified docker-compose.yml syntax
2. Checked port availability
3. Verified network configuration
4. Checked service dependencies

**Current Status**: Service still failing. Need human review.

**Request**: Please review and provide guidance on next steps.
```

## Message ID Format

Format: `MSG-YYYY-MM-DD-###`

- `MSG` - Prefix
- `YYYY-MM-DD` - Date
- `###` - Sequential number (001, 002, etc.)

Example: `MSG-2025-01-13-001`

## Integration with MCP Tools

The communication protocol is accessed via MCP tools:

- `send_agent_message()` - Send a message
- `get_agent_messages()` - Get messages for agent
- `acknowledge_message()` - Acknowledge receipt
- `mark_message_resolved()` - Mark as resolved
- `query_messages()` - Query messages with filters

See `agents/communication/README.md` for complete usage guide.

---

**Last Updated**: 2025-01-13
**Status**: Active
**Version**: 1.0

