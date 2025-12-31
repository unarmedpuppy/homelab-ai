---
name: n8n-workflow-creation
description: Create n8n workflow JSON files that import cleanly
when_to_use: When creating or modifying n8n automation workflows
---

# n8n Workflow Creation Guide

## Workflow JSON Structure

### Required Top-Level Fields

```json
{
  "name": "Workflow Name",
  "nodes": [],
  "connections": {},
  "settings": {
    "executionOrder": "v1"
  },
  "active": false,
  "staticData": null,
  "tags": []
}
```

**Important**: 
- `tags` must be an empty array `[]` for clean import (not array of strings)
- `settings.executionOrder` should be `"v1"` for modern n8n

### Node Structure

```json
{
  "id": "unique-id-string",
  "name": "Human Readable Name",
  "type": "n8n-nodes-base.nodeType",
  "typeVersion": 1,
  "position": [x, y],
  "parameters": {}
}
```

**Notes**:
- `id` - unique identifier, can be UUID or descriptive string
- `name` - displayed in UI, used in connections
- `position` - [x, y] coordinates on canvas, ~200px spacing works well
- `typeVersion` - use latest stable version for each node type

### Connections Format

```json
{
  "connections": {
    "Source Node Name": {
      "main": [
        [
          { "node": "Target Node Name", "type": "main", "index": 0 }
        ]
      ]
    }
  }
}
```

**For nodes with multiple outputs** (like If node):
```json
{
  "If Node Name": {
    "main": [
      [{ "node": "True Branch Node", "type": "main", "index": 0 }],
      [{ "node": "False Branch Node", "type": "main", "index": 0 }]
    ]
  }
}
```

---

## Built-in Node Reference

### Schedule Trigger

```json
{
  "id": "schedule-trigger",
  "name": "Every 5 Minutes",
  "type": "n8n-nodes-base.scheduleTrigger",
  "typeVersion": 1.1,
  "position": [250, 300],
  "parameters": {
    "rule": {
      "interval": [
        {
          "field": "minutes",
          "minutesInterval": 5
        }
      ]
    }
  }
}
```

**Interval options**: `seconds`, `minutes`, `hours`, `days`

### Execute Command Node

```json
{
  "id": "run-command",
  "name": "Run Shell Command",
  "type": "n8n-nodes-base.executeCommand",
  "typeVersion": 1,
  "position": [450, 300],
  "parameters": {
    "command": "echo 'Hello World'",
    "executeOnce": true
  }
}
```

**Output**: `$json.stdout`, `$json.stderr`, `$json.exitCode`

**Dynamic variables in command**:
```json
"command": "docker logs {{ $json.container_name }}"
```

### HTTP Request Node

```json
{
  "id": "http-request",
  "name": "Call API",
  "type": "n8n-nodes-base.httpRequest",
  "typeVersion": 4.2,
  "position": [650, 300],
  "parameters": {
    "method": "POST",
    "url": "https://api.example.com/endpoint",
    "sendHeaders": true,
    "headerParameters": {
      "parameters": [
        { "name": "Content-Type", "value": "application/json" }
      ]
    },
    "sendBody": true,
    "specifyBody": "json",
    "jsonBody": "={{ JSON.stringify({ key: $json.value }) }}",
    "options": {
      "timeout": 30000
    }
  }
}
```

### Code Node (JavaScript)

```json
{
  "id": "code-node",
  "name": "Process Data",
  "type": "n8n-nodes-base.code",
  "typeVersion": 2,
  "position": [850, 300],
  "parameters": {
    "jsCode": "// Get input items\nconst items = $input.all();\n\n// Process and return\nconst results = items.map(item => ({\n  json: {\n    processed: item.json.data,\n    timestamp: new Date().toISOString()\n  }\n}));\n\nreturn results;"
  }
}
```

**Input/Output**:
- Input: `$input.all()` returns array of items, each with `.json` property
- Input: `$input.first()` returns first item
- Output: Must return array of `{ json: {...} }` objects
- Reference other nodes: `$('Node Name').first().json.field`

### Filter Node

```json
{
  "id": "filter-node",
  "name": "Filter Items",
  "type": "n8n-nodes-base.filter",
  "typeVersion": 2,
  "position": [1050, 300],
  "parameters": {
    "conditions": {
      "options": {
        "caseSensitive": true,
        "leftValue": "",
        "typeValidation": "strict"
      },
      "conditions": [
        {
          "id": "condition-1",
          "leftValue": "={{ $json.status }}",
          "rightValue": "active",
          "operator": {
            "type": "string",
            "operation": "equals"
          }
        }
      ],
      "combinator": "and"
    },
    "options": {}
  }
}
```

**Operators**:
- String: `equals`, `notEquals`, `contains`, `notContains`, `startsWith`, `endsWith`, `isEmpty`, `isNotEmpty`
- Number: `equals`, `notEquals`, `gt`, `gte`, `lt`, `lte`
- Boolean: `equals`, `notEquals`

### If Node (Conditional Branch)

Same structure as Filter but with two outputs:
- Output 0: Items matching conditions (true branch)
- Output 1: Items not matching (false branch)

```json
{
  "id": "if-node",
  "name": "Check Condition",
  "type": "n8n-nodes-base.if",
  "typeVersion": 2,
  "position": [1250, 300],
  "parameters": {
    "conditions": {
      "options": {
        "caseSensitive": true,
        "leftValue": "",
        "typeValidation": "strict"
      },
      "conditions": [
        {
          "id": "check-1",
          "leftValue": "={{ $json.success }}",
          "rightValue": true,
          "operator": {
            "type": "boolean",
            "operation": "equals"
          }
        }
      ],
      "combinator": "and"
    },
    "options": {}
  }
}
```

---

## Docker Integration

### Prerequisites

The n8n container needs:
1. Docker socket mounted: `/var/run/docker.sock:/var/run/docker.sock`
2. Docker CLI installed (custom image required)

### Custom n8n Dockerfile

```dockerfile
FROM harbor.server.unarmedpuppy.com/docker-hub/n8nio/n8n:latest

USER root
RUN apk add --no-cache curl docker-cli
USER node
```

### Docker Commands in Execute Command Node

```json
{
  "parameters": {
    "command": "docker ps -a --format '{{.Names}}|{{.Status}}|{{.State}}'"
  },
  "type": "n8n-nodes-base.executeCommand",
  "typeVersion": 1
}
```

**Common Docker commands**:
```bash
# List containers with status
docker ps -a --format '{{.Names}}|{{.Status}}|{{.State}}'

# Get container logs
docker logs --tail 50 container_name 2>&1

# Check container health
docker inspect container_name --format '{{.State.Health.Status}}'

# Restart container
docker restart container_name
```

---

## Best Practices

### Error Handling

Add to node for resilience:
```json
{
  "continueOnFail": true,
  "retryOnFail": true,
  "maxTries": 3,
  "waitBetweenTries": 1000
}
```

### Credentials

**Never hardcode credentials in workflow JSON**. Instead:
1. Create credentials in n8n UI first
2. Reference by name (user selects after import)
3. Or omit credentials block entirely for importable workflows

### Testing Workflows

1. Use "Test workflow" button in n8n UI
2. Pin test data to nodes for consistent testing
3. Check execution logs for errors

### Import Checklist

Before importing a workflow JSON:
- [ ] `tags` is empty array `[]`
- [ ] No hardcoded credential IDs
- [ ] All referenced node names match in connections
- [ ] `typeVersion` matches installed n8n version
- [ ] No community nodes unless installed

---

## Complete Example: Docker Monitor Workflow

```json
{
  "name": "Docker Container Monitor",
  "nodes": [
    {
      "id": "trigger",
      "name": "Every 5 Minutes",
      "type": "n8n-nodes-base.scheduleTrigger",
      "typeVersion": 1.1,
      "position": [250, 300],
      "parameters": {
        "rule": {
          "interval": [{ "field": "minutes", "minutesInterval": 5 }]
        }
      }
    },
    {
      "id": "check-containers",
      "name": "Check Containers",
      "type": "n8n-nodes-base.executeCommand",
      "typeVersion": 1,
      "position": [450, 300],
      "parameters": {
        "command": "docker ps -a --format '{{.Names}}|{{.Status}}|{{.State}}'"
      }
    },
    {
      "id": "parse-output",
      "name": "Parse Output",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [650, 300],
      "parameters": {
        "jsCode": "const stdout = $input.first().json.stdout || '';\nconst lines = stdout.split('\\n').filter(l => l.trim());\n\nreturn lines.map(line => {\n  const [name, status, state] = line.split('|');\n  return { json: { name, status, state } };\n});"
      }
    }
  ],
  "connections": {
    "Every 5 Minutes": {
      "main": [[{ "node": "Check Containers", "type": "main", "index": 0 }]]
    },
    "Check Containers": {
      "main": [[{ "node": "Parse Output", "type": "main", "index": 0 }]]
    }
  },
  "settings": { "executionOrder": "v1" },
  "staticData": null,
  "tags": []
}
```

---

## Troubleshooting

### "This node is not currently installed"
- Node type doesn't exist or typo in `type` field
- Community node not installed
- `typeVersion` incompatible with n8n version

### Nodes not connected after import
- Credential IDs don't match (remove credentials block)
- Node names in connections don't match actual node names
- Invalid JSON structure

### Execute Command returns empty
- Command failed silently - check `stderr`
- Tool not installed in container (curl, docker, etc.)
- Permission denied - check socket permissions

### Filter/If not working
- Check `leftValue` expression syntax: `={{ $json.field }}`
- Verify `typeValidation` setting
- Check data types match operator type
