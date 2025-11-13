# Agent Communication Protocol - Usage Guide

Complete guide for using the Agent Communication Protocol to communicate with other agents.

## Quick Start

### 1. Check for Messages

At the start of your session, check for messages:

```python
# Get pending messages for you
messages = await get_agent_messages(
    agent_id="agent-001",
    status="pending"
)

# Acknowledge important messages
for msg in messages["messages"]:
    if msg["priority"] in ["high", "urgent"]:
        await acknowledge_message(msg["message_id"], "agent-001")
```

### 2. Send a Message

When you need to communicate with another agent:

```python
# Send a request for help
await send_agent_message(
    from_agent="agent-001",
    to_agent="agent-002",
    type="request",
    priority="high",
    subject="Need help with Traefik configuration",
    content="I'm stuck on configuring Traefik labels. Can you help?",
    related_task_id="T1.5"
)
```

### 3. Respond to Messages

When you receive a request:

```python
# Get the message
message = await get_agent_messages(agent_id="agent-002", status="pending")[0]

# Acknowledge it
await acknowledge_message(message["message_id"], "agent-002")

# Send a response
await send_agent_message(
    from_agent="agent-002",
    to_agent="agent-001",
    type="response",
    priority="medium",
    subject=f"Re: {message['subject']}",
    content="Here's the solution: [your response]",
    related_message_id=message["message_id"]
)

# Mark original as resolved
await mark_message_resolved(message["message_id"], "agent-002", "Provided solution")
```

## MCP Tools Reference

### `send_agent_message()`

Send a message to another agent.

**Parameters**:
- `from_agent` (str, required): Your agent ID
- `to_agent` (str, required): Recipient agent ID (or "all" for broadcast)
- `type` (str, required): Message type - `request`, `response`, `notification`, `escalation`
- `priority` (str, required): Priority level - `low`, `medium`, `high`, `urgent`
- `subject` (str, required): Brief subject line
- `content` (str, required): Message content (markdown supported)
- `related_task_id` (str, optional): Related task ID
- `related_message_id` (str, optional): Original message ID (for responses)

**Returns**:
```json
{
  "status": "success",
  "message_id": "MSG-2025-01-13-001",
  "message": "Message sent successfully to agent-002"
}
```

**Example**:
```python
result = await send_agent_message(
    from_agent="agent-001",
    to_agent="agent-002",
    type="request",
    priority="high",
    subject="Need help with deployment",
    content="I'm stuck on task T1.5. Can you help?",
    related_task_id="T1.5"
)
```

### `get_agent_messages()`

Get messages for an agent.

**Parameters**:
- `agent_id` (str, required): Agent ID to get messages for (or "all" for all messages)
- `status` (str, optional): Filter by status - `pending`, `acknowledged`, `in_progress`, `resolved`, `escalated`
- `type` (str, optional): Filter by type - `request`, `response`, `notification`, `escalation`
- `priority` (str, optional): Filter by priority - `low`, `medium`, `high`, `urgent`
- `limit` (int, optional): Maximum number of messages (default: 20)

**Returns**:
```json
{
  "status": "success",
  "count": 2,
  "messages": [
    {
      "message_id": "MSG-2025-01-13-001",
      "from_agent": "agent-002",
      "to_agent": "agent-001",
      "type": "request",
      "priority": "high",
      "status": "pending",
      "subject": "Need help with deployment",
      "content": "I'm stuck on task T1.5...",
      "created_at": "2025-01-13T10:30:00Z",
      "related_task_id": "T1.5"
    }
  ]
}
```

**Example**:
```python
# Get all pending messages
messages = await get_agent_messages(
    agent_id="agent-001",
    status="pending"
)

# Get urgent messages
urgent = await get_agent_messages(
    agent_id="agent-001",
    priority="urgent"
)
```

### `acknowledge_message()`

Acknowledge receipt of a message.

**Parameters**:
- `message_id` (str, required): Message ID to acknowledge
- `agent_id` (str, required): Your agent ID

**Returns**:
```json
{
  "status": "success",
  "message": "Message MSG-2025-01-13-001 acknowledged"
}
```

**Example**:
```python
await acknowledge_message("MSG-2025-01-13-001", "agent-001")
```

### `mark_message_resolved()`

Mark a message as resolved.

**Parameters**:
- `message_id` (str, required): Message ID to resolve
- `agent_id` (str, required): Your agent ID
- `resolution_note` (str, optional): Note about resolution

**Returns**:
```json
{
  "status": "success",
  "message": "Message MSG-2025-01-13-001 marked as resolved"
}
```

**Example**:
```python
await mark_message_resolved(
    "MSG-2025-01-13-001",
    "agent-001",
    "Issue resolved by updating configuration"
)
```

### `query_messages()`

Query messages with multiple filters.

**Parameters**:
- `from_agent` (str, optional): Filter by sender
- `to_agent` (str, optional): Filter by recipient
- `type` (str, optional): Filter by type
- `priority` (str, optional): Filter by priority
- `status` (str, optional): Filter by status
- `related_task_id` (str, optional): Filter by task ID
- `limit` (int, optional): Maximum results (default: 50)

**Returns**: Same format as `get_agent_messages()`

**Example**:
```python
# Find all messages related to a task
task_messages = await query_messages(
    related_task_id="T1.5"
)

# Find all high-priority requests
high_priority = await query_messages(
    type="request",
    priority="high",
    status="pending"
)
```

## Common Workflows

### Workflow 1: Request Help

```python
# 1. Send request
result = await send_agent_message(
    from_agent="agent-001",
    to_agent="agent-002",
    type="request",
    priority="high",
    subject="Need help with Docker deployment",
    content="""
I'm working on task T1.5 and I'm stuck on Docker deployment.

**What I've tried:**
- Verified docker-compose.yml syntax
- Checked port availability
- Verified network configuration

**What I need:**
- Help troubleshooting the deployment error
- Best practices for service configuration

**Error:**
```
Container failed to start
Exit code: 1
```
""",
    related_task_id="T1.5"
)

# 2. Wait for response (check periodically)
# 3. When response received, mark original as resolved
```

### Workflow 2: Respond to Request

```python
# 1. Get pending requests
requests = await get_agent_messages(
    agent_id="agent-002",
    type="request",
    status="pending"
)

# 2. For each request, acknowledge
for req in requests["messages"]:
    await acknowledge_message(req["message_id"], "agent-002")
    
    # 3. Work on the request
    # ... do work ...
    
    # 4. Send response
    await send_agent_message(
        from_agent="agent-002",
        to_agent=req["from_agent"],
        type="response",
        priority="medium",
        subject=f"Re: {req['subject']}",
        content="""
Here's the solution:

1. The issue was in the docker-compose.yml file
2. The service port mapping was incorrect
3. Fixed by updating to port 8080

**Solution:**
```yaml
ports:
  - "8080:80"
```
""",
        related_message_id=req["message_id"]
    )
    
    # 5. Mark original as resolved
    await mark_message_resolved(
        req["message_id"],
        "agent-002",
        "Provided solution and fixed issue"
    )
```

### Workflow 3: Send Notification

```python
# Send notification about important finding
await send_agent_message(
    from_agent="agent-001",
    to_agent="all",  # Broadcast to all agents
    type="notification",
    priority="medium",
    subject="Port conflict resolved",
    content="""
**Issue**: Port 8086 was already in use by Grafana Stack.

**Resolution**: Updated agent-monitoring to use port 8087.

**Files Changed**:
- `apps/agent-monitoring/docker-compose.yml`
- All documentation references

**Impact**: No conflicts, all services can run simultaneously.
"""
)
```

### Workflow 4: Escalate Issue

```python
# Escalate critical issue
await send_agent_message(
    from_agent="agent-001",
    to_agent="all",
    type="escalation",
    priority="urgent",
    subject="Critical: Service deployment failed repeatedly",
    content="""
**Issue**: Service `myapp` has failed to deploy after 3 attempts.

**Error**: 
```
Container failed to start
Exit code: 1
```

**Attempted Solutions**:
1. Verified docker-compose.yml syntax
2. Checked port availability
3. Verified network configuration
4. Checked service dependencies

**Current Status**: Service still failing. Need human review.

**Request**: Please review and provide guidance on next steps.
""",
    related_task_id="T1.5"
)
```

## Integration with Other Systems

### Task Coordination

Link messages to tasks:

```python
# When task is blocked, send request
await send_agent_message(
    from_agent="agent-001",
    to_agent="agent-002",
    type="request",
    priority="high",
    subject=f"Task {task_id} blocked",
    content=f"Task {task_id} is blocked. Need help with [issue].",
    related_task_id=task_id
)
```

### Memory System

Record important communications:

```python
# After resolving a request, record in memory
await memory_record_decision(
    content=f"Resolved communication request: {message_id}",
    rationale="Provided solution for Docker deployment issue",
    importance=0.7,
    tags="communication,docker,deployment"
)
```

### Agent Monitoring

Communication is automatically logged:

- Message sending/receiving logged as activity
- Response times tracked
- Communication patterns visible in dashboard

## Best Practices

### Sending Messages

1. **Be Clear**: Use clear, concise subject lines
2. **Provide Context**: Include relevant information and what you've tried
3. **Set Priority**: Use appropriate priority level
4. **Link Tasks**: Link to related tasks when applicable
5. **Follow Up**: Check for responses within expected timeframe

### Receiving Messages

1. **Check Regularly**: Check messages at start of session
2. **Acknowledge Promptly**: Acknowledge within priority timeframe
   - Urgent: 15 minutes
   - High: 1 hour
   - Medium: 4 hours
   - Low: 24 hours
3. **Update Status**: Update status as you work (acknowledged → in_progress → resolved)
4. **Respond Thoroughly**: Provide complete responses with examples
5. **Escalate When Needed**: Don't hesitate to escalate if stuck

### Message Content

1. **Be Specific**: Include specific details and context
2. **Include Examples**: Provide code examples when helpful
3. **Reference Resources**: Link to relevant docs/files
4. **Show Attempts**: Describe what you've already tried
5. **Ask Clear Questions**: Make it easy to respond

## Response Time Expectations

Based on priority:

- **Urgent**: 15 minutes
- **High**: 1 hour
- **Medium**: 4 hours
- **Low**: 24 hours

## Message Status Flow

```
pending → acknowledged → in_progress → resolved
   ↓
escalated
```

## Examples

See `protocol.md` for detailed examples of each message type.

## Related Documentation

- **Protocol**: `agents/communication/protocol.md` - Complete protocol specification
- **Agent Prompt**: `agents/docs/AGENT_PROMPT.md` - Agent prompt with communication section
- **MCP Tools**: `server-management-mcp/README.md` - MCP tools reference

---

**Last Updated**: 2025-01-13
**Status**: Active

