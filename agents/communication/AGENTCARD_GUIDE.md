# AgentCard Guide

**Understanding AgentCards in the A2A Protocol**

**Date**: 2025-01-13

---

## What is an AgentCard?

An **AgentCard** is like a "business card" for AI agents in the A2A (Agent-to-Agent) protocol. It's a JSON document that describes:

- **Who the agent is** (agent ID, name, version)
- **What the agent can do** (capabilities)
- **How to reach the agent** (transport endpoints)
- **How to authenticate** (authentication methods)
- **Additional metadata** (specialization, status, etc.)

### Why AgentCards Matter

**AgentCards enable agent discovery** - they allow agents to:
1. **Find other agents** - Discover available agents in the system
2. **Understand capabilities** - Know what each agent can do
3. **Connect properly** - Know how to communicate with each agent
4. **Coordinate effectively** - Match tasks to agents with the right skills

**Think of it like this:**
- Without AgentCards: Agents don't know who else exists or what they can do
- With AgentCards: Agents can discover, query capabilities, and coordinate automatically

---

## AgentCard Structure

### Basic AgentCard Example

```json
{
  "agent_id": "agent-001",
  "name": "Server Management Agent",
  "version": "1.0.0",
  "capabilities": [
    "docker_management",
    "deployment",
    "troubleshooting",
    "system_monitoring"
  ],
  "transports": [
    {
      "type": "http",
      "endpoint": "http://localhost:3001/a2a",
      "methods": ["POST"]
    },
    {
      "type": "sse",
      "endpoint": "http://localhost:3001/a2a/stream",
      "events": ["message", "status"]
    }
  ],
  "authentication": {
    "type": "none",
    "required": false
  },
  "metadata": {
    "specialization": "server-management",
    "status": "active"
  },
  "created_at": "2025-01-13T10:00:00Z",
  "updated_at": "2025-01-13T10:00:00Z"
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent_id` | string | ✅ Yes | Unique identifier (e.g., "agent-001") |
| `name` | string | ✅ Yes | Human-readable name |
| `version` | string | ✅ Yes | Agent version (e.g., "1.0.0") |
| `capabilities` | array | ✅ Yes | List of what agent can do |
| `transports` | array | ✅ Yes | How to communicate with agent |
| `authentication` | object | ✅ Yes | Auth requirements |
| `metadata` | object | ❌ No | Additional info (specialization, status, etc.) |
| `created_at` | string | Auto | ISO 8601 timestamp |
| `updated_at` | string | Auto | ISO 8601 timestamp |

---

## AgentCard Components

### 1. Capabilities

**What it is**: List of skills/abilities the agent has

**Examples**:
- `"docker_management"` - Can manage Docker containers
- `"deployment"` - Can deploy services
- `"troubleshooting"` - Can diagnose issues
- `"database_management"` - Can manage databases
- `"media_download"` - Can manage media downloads

**How it's used**:
- Agents can query: "Which agents can do docker_management?"
- Task assignment: "Find agent with deployment capability"
- Skill matching: "Who can help with troubleshooting?"

### 2. Transports

**What it is**: How to communicate with the agent

**Types**:
- **HTTP** - REST API endpoint
- **SSE** - Server-Sent Events for streaming
- **WebSocket** - Real-time bidirectional (future)

**Example**:
```json
"transports": [
  {
    "type": "http",
    "endpoint": "http://localhost:3001/a2a",
    "methods": ["POST"]
  },
  {
    "type": "sse",
    "endpoint": "http://localhost:3001/a2a/stream",
    "events": ["message", "status"]
  }
]
```

**How it's used**:
- Agents know where to send messages
- Agents know which transport to use
- Enables multi-transport support

### 3. Authentication

**What it is**: Security requirements for communication

**Types**:
- `"none"` - No authentication required
- `"api_key"` - API key required
- `"oauth"` - OAuth authentication
- `"mtls"` - Mutual TLS

**Example**:
```json
"authentication": {
  "type": "api_key",
  "required": true,
  "header": "X-API-Key"
}
```

**How it's used**:
- Agents know if authentication is needed
- Agents know what type of auth to use
- Enables secure communication

### 4. Metadata

**What it is**: Additional information about the agent

**Common fields**:
- `specialization` - Agent's domain (e.g., "server-management")
- `status` - Current status (e.g., "active", "idle", "archived")
- `description` - Human-readable description
- `parent_agent` - Parent agent ID (if spawned)

**Example**:
```json
"metadata": {
  "specialization": "server-management",
  "status": "active",
  "description": "Manages server infrastructure and deployments"
}
```

---

## How AgentCards Work

### Discovery Flow

```
Agent A needs help
    ↓
Agent A queries: "Which agents can do docker_management?"
    ↓
System searches AgentCards
    ↓
Finds Agent B with docker_management capability
    ↓
Agent A gets Agent B's transport info
    ↓
Agent A sends message to Agent B via A2A protocol
```

### Example Scenario

**Scenario**: Agent-001 needs help with Docker deployment

1. **Agent-001 queries AgentCards**:
   ```python
   cards = await list_agentcards_tool()
   # Find agents with "deployment" capability
   deployment_agents = [c for c in cards if "deployment" in c["capabilities"]]
   ```

2. **Agent-001 finds Agent-002**:
   - Agent-002 has `"deployment"` in capabilities
   - Agent-002's transport: `http://localhost:3001/a2a`

3. **Agent-001 sends message**:
   ```python
   await send_a2a_message(
       from_agent="agent-001",
       to_agent="agent-002",
       type="request",
       priority="high",
       subject="Need help with Docker deployment",
       content="I'm stuck on deploying service X..."
   )
   ```

4. **Agent-002 receives and responds**:
   - Uses its own MCP tools to help
   - Responds via A2A protocol

---

## Creating AgentCards

### Using MCP Tool

```python
# Create AgentCard for agent-001
result = await create_agentcard_tool(
    agent_id="agent-001",
    name="Server Management Agent",
    capabilities="docker_management,deployment,troubleshooting,system_monitoring"
)
```

### Using Python Directly

```python
from agents.communication.a2a import create_agentcard

card = create_agentcard(
    agent_id="agent-001",
    name="Server Management Agent",
    capabilities=[
        "docker_management",
        "deployment",
        "troubleshooting",
        "system_monitoring"
    ],
    metadata={
        "specialization": "server-management",
        "status": "active"
    }
)
```

### Custom Transports

```python
card = create_agentcard(
    agent_id="agent-001",
    name="Server Management Agent",
    capabilities=["docker_management", "deployment"],
    transports=[
        {
            "type": "http",
            "endpoint": "http://localhost:3001/a2a",
            "methods": ["POST"]
        },
        {
            "type": "sse",
            "endpoint": "http://localhost:3001/a2a/stream",
            "events": ["message", "status"]
        }
    ]
)
```

---

## Querying AgentCards

### List All AgentCards

```python
# Get all AgentCards
result = await list_agentcards_tool()
# Returns: {"status": "success", "count": 2, "agentcards": [...]}
```

### Get Specific AgentCard

```python
# Get AgentCard for agent-001
result = await get_agentcard_tool(agent_id="agent-001")
# Returns: {"status": "success", "agentcard": {...}}
```

### Via HTTP Endpoint

```bash
# List all AgentCards
curl http://localhost:3001/a2a/agentcards

# Get specific AgentCard
curl http://localhost:3001/a2a/agentcard/agent-001
```

### Via A2A Protocol

```bash
curl -X POST http://localhost:3001/a2a \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "query-1",
    "method": "a2a.listAgentCards",
    "params": {}
  }'
```

---

## AgentCard Use Cases

### Use Case 1: Agent Discovery

**Problem**: Agent-001 needs to find an agent that can help with database issues

**Solution**:
```python
# List all AgentCards
cards = await list_agentcards_tool()

# Find agents with database capability
db_agents = [
    c for c in cards["agentcards"]
    if "database_management" in c["capabilities"]
]

# Contact the first available agent
if db_agents:
    target_agent = db_agents[0]["agent_id"]
    await send_a2a_message(
        from_agent="agent-001",
        to_agent=target_agent,
        type="request",
        priority="high",
        subject="Need database help",
        content="..."
    )
```

### Use Case 2: Capability Matching

**Problem**: Need to assign task to agent with right skills

**Solution**:
```python
# Get all AgentCards
cards = await list_agentcards_tool()

# Find agent with matching capabilities
for card in cards["agentcards"]:
    if "deployment" in card["capabilities"]:
        # Found agent with deployment skill
        assign_task_to_agent(
            agent_id=card["agent_id"],
            task_description="Deploy new service"
        )
```

### Use Case 3: Transport Discovery

**Problem**: Need to know how to communicate with another agent

**Solution**:
```python
# Get AgentCard
card = await get_agentcard_tool(agent_id="agent-002")

# Use transport information
transports = card["agentcard"]["transports"]
http_transport = [t for t in transports if t["type"] == "http"][0]
endpoint = http_transport["endpoint"]

# Send message to endpoint
# (A2A protocol handles this automatically)
```

---

## AgentCard Storage

### File Location

AgentCards are stored as JSON files:
```
agents/communication/agentcards/
├── agent-001.json
├── agent-002.json
└── agent-003.json
```

### File Format

Each AgentCard is a JSON file:
```json
{
  "agent_id": "agent-001",
  "name": "Server Management Agent",
  "version": "1.0.0",
  "capabilities": [...],
  "transports": [...],
  "authentication": {...},
  "metadata": {...},
  "created_at": "2025-01-13T10:00:00Z",
  "updated_at": "2025-01-13T10:00:00Z"
}
```

---

## AgentCard vs Agent Registry

### Agent Registry (`agents/registry/agent-registry.md`)

**Purpose**: Human-readable registry of all agents
- Agent definitions
- Status tracking
- Lifecycle management
- Auto-generated from monitoring DB

**Format**: Markdown table

**Use Case**: Human review, documentation

### AgentCard

**Purpose**: Machine-readable agent discovery
- Capability advertisement
- Transport information
- A2A protocol compliance
- Dynamic discovery

**Format**: JSON files

**Use Case**: Agent-to-agent discovery, A2A protocol

**Relationship**: 
- Agent Registry = Human view
- AgentCard = Machine view
- Both describe agents, but for different purposes

---

## Best Practices

### 1. Keep Capabilities Updated

**Do**:
- Update capabilities when agent gains new skills
- Remove capabilities that are no longer available
- Be specific (e.g., "docker_management" not just "docker")

**Don't**:
- List capabilities the agent doesn't actually have
- Use vague terms
- Forget to update when capabilities change

### 2. Provide Accurate Transport Info

**Do**:
- List all available transports
- Use correct endpoints
- Include required methods/events

**Don't**:
- List transports that aren't available
- Use incorrect endpoints
- Forget to update when endpoints change

### 3. Use Meaningful Metadata

**Do**:
- Include specialization
- Update status regularly
- Add helpful descriptions

**Don't**:
- Leave metadata empty
- Use inconsistent status values
- Include outdated information

---

## Example AgentCards

### Server Management Agent

```json
{
  "agent_id": "agent-001",
  "name": "Server Management Agent",
  "version": "1.0.0",
  "capabilities": [
    "docker_management",
    "deployment",
    "troubleshooting",
    "system_monitoring",
    "git_operations",
    "networking"
  ],
  "transports": [
    {
      "type": "http",
      "endpoint": "http://localhost:3001/a2a",
      "methods": ["POST"]
    }
  ],
  "authentication": {
    "type": "none",
    "required": false
  },
  "metadata": {
    "specialization": "server-management",
    "status": "active",
    "description": "Manages server infrastructure, deployments, and troubleshooting"
  }
}
```

### Media Download Agent

```json
{
  "agent_id": "agent-002",
  "name": "Media Download Agent",
  "version": "1.0.0",
  "capabilities": [
    "sonarr_management",
    "radarr_management",
    "download_client_management",
    "media_organization"
  ],
  "transports": [
    {
      "type": "http",
      "endpoint": "http://localhost:3001/a2a",
      "methods": ["POST"]
    }
  ],
  "authentication": {
    "type": "none",
    "required": false
  },
  "metadata": {
    "specialization": "media-download",
    "status": "active",
    "description": "Manages media download services (Sonarr, Radarr, etc.)"
  }
}
```

### Database Agent

```json
{
  "agent_id": "agent-003",
  "name": "Database Management Agent",
  "version": "1.0.0",
  "capabilities": [
    "database_management",
    "migrations",
    "backup_restore",
    "query_optimization"
  ],
  "transports": [
    {
      "type": "http",
      "endpoint": "http://localhost:3001/a2a",
      "methods": ["POST"]
    }
  ],
  "authentication": {
    "type": "none",
    "required": false
  },
  "metadata": {
    "specialization": "database",
    "status": "active",
    "description": "Manages database operations, migrations, and optimization"
  }
}
```

---

## Integration with Existing Systems

### Agent Registry Integration

AgentCards complement the agent registry:
- **Agent Registry**: Human-readable, markdown-based
- **AgentCard**: Machine-readable, JSON-based, A2A-compliant

Both can coexist and serve different purposes.

### Task Coordination Integration

AgentCards help with task assignment:
```python
# Find agent with right capabilities
cards = await list_agentcards_tool()
suitable_agent = find_agent_with_capability(cards, "deployment")

# Assign task
assign_task_to_agent(
    agent_id=suitable_agent["agent_id"],
    task_description="Deploy new service"
)
```

### Memory System Integration

AgentCards can be referenced in memory:
```python
# Record decision about agent capabilities
memory_record_decision(
    content=f"Agent {agent_id} has capabilities: {capabilities}",
    rationale="AgentCard shows available skills",
    tags="agent-discovery,capabilities"
)
```

---

## Next Steps

1. **Create AgentCards for existing agents**
   - agent-001 (Server Management)
   - Any other active agents

2. **Update AgentCards when capabilities change**
   - When agent gains new skills
   - When agent status changes

3. **Use AgentCards for discovery**
   - Query before sending messages
   - Match tasks to capabilities
   - Coordinate multi-agent work

---

## Resources

- **A2A Protocol Spec**: `a2a-protocol.org`
- **AgentCard Implementation**: `agents/communication/a2a/agentcard.py`
- **MCP Tools**: `agents/apps/agent-mcp/tools/communication.py`
- **HTTP Endpoints**: `agents/apps/agent-monitoring/backend/src/routes/a2a.ts`

---

**Last Updated**: 2025-01-13  
**Status**: Active  
**See Also**: 
- `agents/docs/AGENTIC_PROTOCOLS_LANDSCAPE_ANALYSIS.md` - Protocol overview
- `agents/communication/A2A_MIGRATION_SUMMARY.md` - Migration details

