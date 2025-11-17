# A2A Protocol Migration Audit

**Current System Analysis and Migration Plan**

**Date**: 2025-01-13  
**Status**: Audit Complete - Ready for Implementation

---

## Executive Summary

Our current agent communication system uses a custom protocol with markdown-based messages and YAML frontmatter. To migrate to A2A (Agent-to-Agent) protocol, we need to:

1. **Replace file-based storage** with JSON-RPC 2.0 over HTTP/SSE
2. **Add AgentCard support** for agent discovery
3. **Implement A2A message format** (JSON-RPC 2.0)
4. **Add transport layer** (HTTP + SSE for streaming)
5. **Maintain backward compatibility** during transition

**Migration Complexity**: Medium  
**Estimated Timeline**: 2-3 weeks  
**Breaking Changes**: Minimal (backward compatibility maintained)

---

## Current System Analysis

### What We Have ✅

1. **Message Types** (4 types)
   - Request (requires response)
   - Response (replies to request)
   - Notification (one-way, no response)
   - Escalation (urgent, needs attention)

2. **Message Fields**
   - `message_id`: Unique ID (MSG-YYYY-MM-DD-###)
   - `from_agent`: Sender agent ID
   - `to_agent`: Recipient agent ID (or "all")
   - `type`: Message type
   - `priority`: Priority level (low, medium, high, urgent)
   - `status`: Status (pending, acknowledged, in_progress, resolved, escalated)
   - `subject`: Brief subject line
   - `content`: Message body (markdown)
   - `created_at`: ISO 8601 timestamp
   - `acknowledged_at`: Optional timestamp
   - `resolved_at`: Optional timestamp
   - `related_task_id`: Optional task reference
   - `related_message_id`: Optional parent message reference

3. **Storage System**
   - Markdown files with YAML frontmatter
   - `agents/communication/messages/*.md`
   - `agents/communication/messages/index.json` for quick lookup

4. **MCP Tools** (5 tools)
   - `send_agent_message()` - Send message
   - `get_agent_messages()` - Get messages with filters
   - `acknowledge_message()` - Acknowledge receipt
   - `mark_message_resolved()` - Mark as resolved
   - `query_messages()` - Query with multiple filters

5. **Status Flow**
   - `pending` → `acknowledged` → `in_progress` → `resolved`
   - Can escalate at any point

### What We're Missing ❌

1. **A2A Protocol Compliance**
   - ❌ No JSON-RPC 2.0 format
   - ❌ No HTTP transport layer
   - ❌ No SSE streaming support
   - ❌ No AgentCard for discovery

2. **Transport Layer**
   - ❌ No HTTP endpoint for A2A messages
   - ❌ No SSE streaming
   - ❌ File-based only (not network-based)

3. **Agent Discovery**
   - ❌ No AgentCard support
   - ❌ No capability advertisement
   - ❌ No dynamic discovery

4. **Security**
   - ❌ No authentication mechanism
   - ❌ No authorization checks
   - ❌ File-based (local only)

---

## A2A Protocol Requirements

### Core Requirements

1. **JSON-RPC 2.0 Format**
   - All messages must use JSON-RPC 2.0 structure
   - Method names follow A2A conventions
   - Error handling per JSON-RPC 2.0 spec

2. **Transport Protocols**
   - HTTP with JSON-RPC 2.0 for synchronous communication
   - Server-Sent Events (SSE) for streaming
   - Support for both transports

3. **AgentCard**
   - Each agent must publish an AgentCard
   - Contains capabilities, transports, authentication
   - Enables dynamic discovery

4. **Message Structure**
   - Standardized A2A message format
   - Support for task delegation
   - Support for goal negotiation

5. **Security**
   - Authentication mechanisms (API keys, OAuth, mTLS)
   - Authorization checks
   - Secure communication channels

---

## Migration Strategy

### Phase 1: Add A2A Support (Non-Breaking)

**Goal**: Add A2A protocol support alongside existing system

**Changes**:
1. Create A2A message adapter (converts between formats)
2. Add HTTP endpoint for A2A messages
3. Add AgentCard support
4. Maintain backward compatibility with existing MCP tools

**Timeline**: Week 1

### Phase 2: Dual Protocol Support

**Goal**: Support both protocols simultaneously

**Changes**:
1. Update MCP tools to support both formats
2. Add format detection and conversion
3. Migrate existing messages to A2A format (optional)
4. Test interoperability

**Timeline**: Week 2

### Phase 3: Full A2A Migration (Optional)

**Goal**: Complete migration to A2A (if desired)

**Changes**:
1. Deprecate old format (with migration path)
2. Update all documentation
3. Remove backward compatibility layer (future)

**Timeline**: Week 3 (optional)

---

## Implementation Plan

### 1. A2A Message Format

**A2A JSON-RPC 2.0 Structure**:
```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "method": "a2a.sendMessage",
  "params": {
    "from": "agent-001",
    "to": "agent-002",
    "type": "request",
    "priority": "high",
    "subject": "Need help with deployment",
    "content": "Message content...",
    "metadata": {
      "related_task_id": "T1.5",
      "related_message_id": null
    }
  }
}
```

**Response Format**:
```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "result": {
    "message_id": "MSG-2025-01-13-001",
    "status": "success"
  }
}
```

### 2. AgentCard Structure

**AgentCard JSON**:
```json
{
  "agent_id": "agent-001",
  "name": "Server Management Agent",
  "version": "1.0.0",
  "capabilities": [
    "docker_management",
    "deployment",
    "troubleshooting"
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
    "type": "api_key",
    "required": false
  },
  "metadata": {
    "specialization": "server-management",
    "status": "active"
  }
}
```

### 3. HTTP Endpoint Structure

**Endpoints**:
- `POST /a2a` - Send A2A message (JSON-RPC 2.0)
- `GET /a2a/messages` - Get messages (with filters)
- `POST /a2a/acknowledge` - Acknowledge message
- `POST /a2a/resolve` - Resolve message
- `GET /a2a/agentcard/{agent_id}` - Get AgentCard
- `GET /a2a/stream` - SSE stream for real-time updates

### 4. Backward Compatibility

**Adapter Pattern**:
- MCP tools continue to work with existing format
- A2A adapter converts between formats
- Both formats stored (or converted on-the-fly)

---

## File Structure Changes

### Current Structure
```
agents/communication/
├── protocol.md
├── README.md
└── messages/
    ├── index.json
    └── MSG-*.md
```

### New Structure (A2A + Backward Compatible)
```
agents/communication/
├── protocol.md (updated with A2A section)
├── README.md (updated)
├── a2a/
│   ├── __init__.py
│   ├── message.py (A2A message format)
│   ├── adapter.py (format conversion)
│   ├── agentcard.py (AgentCard support)
│   └── transport.py (HTTP/SSE transport)
├── messages/ (existing, maintained)
│   ├── index.json
│   └── MSG-*.md
└── agentcards/
    └── agent-*.json (AgentCard files)
```

---

## Implementation Details

### 1. A2A Message Adapter

**Purpose**: Convert between custom format and A2A format

**Functions**:
- `to_a2a_format(custom_message)` - Convert custom → A2A
- `from_a2a_format(a2a_message)` - Convert A2A → custom
- `validate_a2a_message(message)` - Validate A2A format

### 2. AgentCard Manager

**Purpose**: Manage AgentCard creation and discovery

**Functions**:
- `create_agentcard(agent_id, capabilities, transports)` - Create AgentCard
- `get_agentcard(agent_id)` - Get AgentCard
- `list_agentcards()` - List all AgentCards
- `update_agentcard(agent_id, updates)` - Update AgentCard

### 3. A2A Transport Layer

**Purpose**: Handle HTTP and SSE communication

**Components**:
- HTTP endpoint handler (JSON-RPC 2.0)
- SSE stream handler
- Message routing
- Authentication/authorization

### 4. Updated MCP Tools

**Changes**:
- Add A2A format support (optional parameter)
- Maintain backward compatibility
- Add AgentCard tools

**New Tools**:
- `get_agentcard(agent_id)` - Get AgentCard
- `list_agentcards()` - List available agents
- `send_a2a_message()` - Send A2A-formatted message

---

## Testing Strategy

### Unit Tests
- A2A message format conversion
- AgentCard creation and validation
- JSON-RPC 2.0 format validation

### Integration Tests
- HTTP endpoint functionality
- SSE streaming
- Message routing
- Backward compatibility

### Interoperability Tests
- Communication with other A2A agents
- Protocol compliance
- Error handling

---

## Migration Checklist

### Phase 1: Foundation
- [ ] Create A2A message format module
- [ ] Create AgentCard module
- [ ] Create adapter module
- [ ] Add HTTP endpoint to monitoring backend
- [ ] Add SSE streaming support
- [ ] Create AgentCard files for existing agents

### Phase 2: Integration
- [ ] Update MCP tools to support A2A format
- [ ] Add format detection and conversion
- [ ] Test backward compatibility
- [ ] Update documentation

### Phase 3: Migration (Optional)
- [ ] Migrate existing messages to A2A format
- [ ] Update all references
- [ ] Deprecate old format (with migration path)
- [ ] Full A2A compliance testing

---

## Backward Compatibility

### Strategy
- **Maintain existing MCP tools** - No breaking changes
- **Add A2A support alongside** - Both formats work
- **Automatic conversion** - Adapter handles format conversion
- **Gradual migration** - Agents can migrate at their own pace

### Migration Path
1. Existing agents continue using current format
2. New agents can use A2A format
3. Adapter converts between formats automatically
4. Eventually deprecate old format (future)

---

## Security Considerations

### Current State
- File-based (local only)
- No authentication
- No authorization

### A2A Requirements
- Authentication (API keys, OAuth, mTLS)
- Authorization checks
- Secure communication

### Implementation
- Add authentication to HTTP endpoints
- Add authorization checks
- Support multiple auth methods
- Maintain local file access (for backward compatibility)

---

## Documentation Updates

### Files to Update
1. `agents/communication/protocol.md` - Add A2A section
2. `agents/communication/README.md` - Add A2A usage
3. `agents/docs/AGENTIC_PROTOCOLS_LANDSCAPE_ANALYSIS.md` - Update status
4. `agents/prompts/base.md` - Update communication section

### New Documentation
1. `agents/communication/A2A_GUIDE.md` - A2A usage guide
2. `agents/communication/AGENTCARD_GUIDE.md` - AgentCard guide
3. `agents/docs/A2A_MIGRATION_GUIDE.md` - Migration guide

---

## Next Steps

1. ✅ **Audit Complete** - This document
2. **Implement A2A Foundation** - Message format, AgentCard, adapter
3. **Add HTTP Endpoint** - A2A transport layer
4. **Update MCP Tools** - Add A2A support
5. **Test and Validate** - Ensure compliance
6. **Update Documentation** - Complete guides

---

**Last Updated**: 2025-01-13  
**Status**: Audit Complete - Ready for Implementation  
**Next**: Begin Phase 1 Implementation

