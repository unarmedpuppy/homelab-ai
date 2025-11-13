# Agent Memory Integration - Memori

## Overview

This module provides memory integration for AI agents using [Memori](https://github.com/GibsonAI/Memori) - an open-source memory engine that automatically manages context and learning for LLMs and AI agents.

## Why Memori?

**Memori provides transparent memory management:**
- ✅ **Automatic**: No manual memory management needed
- ✅ **Transparent**: Intercepts LLM calls automatically
- ✅ **Background Learning**: Conscious Agent learns patterns automatically
- ✅ **Multi-Agent**: Built-in support for multiple agents
- ✅ **Production Ready**: 2.7k stars, active development

## Quick Start

### 1. Install Memori

```bash
pip install memori
```

### 2. Configure Environment

```bash
# .env or environment variables
export MEMORI_DATABASE__CONNECTION_STRING="postgresql://user:pass@localhost/memori"
export MEMORI_AGENTS__OPENAI_API_KEY="sk-..."
export MEMORI_MEMORY__NAMESPACE="home-server"
```

### 3. Enable Memory in Agent Workflow

```python
from apps.agent_memory import setup_memori

# Setup memory (this enables automatic interception)
memori = setup_memori()

# That's it! Memory is now active
# All LLM calls are automatically intercepted and context is injected
```

### 4. Use with LLM (Automatic)

```python
from openai import OpenAI

client = OpenAI()

# Memori automatically injects context before this call
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Help me deploy a service"}]
)

# Memori automatically records this conversation
# Context is automatically available in future calls
```

## How It Works

Memori works by **intercepting LLM calls transparently**:

1. **Before Call**: Memori retrieves relevant memories and injects context
2. **LLM Call**: Your normal LLM call happens (with injected context)
3. **After Call**: Memori extracts entities and records the conversation
4. **Background**: Conscious Agent analyzes patterns and promotes important memories

**No code changes needed** - Memori intercepts calls automatically.

## Configuration

### Database Options

Memori supports multiple databases:

| Database | Connection String |
|----------|------------------|
| SQLite | `sqlite:///./agent_memory.db` |
| PostgreSQL | `postgresql://user:pass@localhost/memori` |
| MySQL | `mysql://user:pass@localhost/memori` |

### Memory Modes

**Conscious Mode** (Short-term working memory):
```python
memori = Memori(conscious_ingest=True)
```

**Auto Mode** (Dynamic search per query):
```python
memori = Memori(auto_ingest=True)
```

**Combined Mode** (Recommended):
```python
memori = Memori(conscious_ingest=True, auto_ingest=True)
```

## Integration with Agent Workflow

### Agent Startup

Add to agent workflow startup:

```python
# apps/agent_memory/startup.py
from apps.agent_memory import setup_memori

# Enable memory at agent startup
memori = setup_memori()
# Memory is now active for all LLM calls
```

### Agent Prompts

Update agent prompts to mention automatic memory:

```markdown
## Memory System (Automatic)

Memori is automatically enabled. You don't need to do anything special:

1. **Context is Automatic**: Memori automatically injects relevant context
2. **Recording is Automatic**: All conversations are automatically recorded
3. **Pattern Learning**: Conscious Agent learns patterns in background

### What Gets Remembered

- All conversations
- Decisions made
- Patterns identified
- Context automatically retrieved
```

## Advanced Usage

### Explicit Memory Queries (Optional)

If you need to explicitly query memory:

```python
from apps.agent_memory import get_global_memori

memori = get_global_memori()

# Query recent decisions
recent_decisions = memori.query("decisions from last week")

# Query specific patterns
patterns = memori.query("type:pattern AND severity:medium")
```

### Documenting Important Decisions

Decisions are automatically extracted, but you can explicitly document:

```python
from apps.agent_memory import get_global_memori

memori = get_global_memori()

# Explicitly document important decisions
memori.remember(
    content="Use PostgreSQL for database",
    category="decision",
    importance=0.9
)
```

## Multi-Agent Support

Memori supports multiple agents with namespaces:

```python
# Agent 1
memori_1 = setup_memori(namespace="agent-001")

# Agent 2
memori_2 = setup_memori(namespace="agent-002")

# Shared memory (home-server scope)
shared_memori = setup_memori(namespace="home-server")
```

## Integration with Skills and MCP Tools

**Memori works transparently with Skills and MCP Tools:**

- Skills automatically benefit from memory
- MCP tools automatically have context
- No changes needed to Skills or MCP tools
- Memory is injected before any LLM call

## Troubleshooting

### Memory Not Working

1. **Check if enabled**: Ensure `memori.enable()` was called
2. **Check database**: Verify database connection string
3. **Check API key**: Verify OpenAI API key is set
4. **Check logs**: Memori logs to console by default

### Context Not Injected

1. **Check mode**: Ensure `auto_ingest=True` or `conscious_ingest=True`
2. **Check database**: Verify memories are being stored
3. **Check namespace**: Ensure correct namespace is used

## References

- **Memori GitHub**: https://github.com/GibsonAI/Memori
- **Memori Documentation**: https://gibsonai.github.io/memori/
- **Comparison**: See `apps/docs/MEMORY_SYSTEM_COMPARISON.md`

---

**Status**: Ready to use
**Priority**: High
**Effort**: Low (just enable it!)

