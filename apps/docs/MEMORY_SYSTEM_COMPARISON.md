# Memory System Comparison: Memori vs mem-layer

## Overview

We need to choose a memory system for agent workflow integration. Two options:

1. **Memori** - [GibsonAI/Memori](https://github.com/GibsonAI/Memori) - Transparent LLM call interception
2. **mem-layer** - [0xSero/mem-layer](https://github.com/0xSero/mem-layer) - Graph-based manual API

## Comparison

| Feature | Memori | mem-layer |
|---------|--------|-----------|
| **Approach** | Transparent interception | Manual API calls |
| **Context Injection** | Automatic | Manual |
| **Recording** | Automatic | Manual |
| **Database Support** | SQLite, PostgreSQL, MySQL, Neon, Supabase | SQLite (primary) |
| **LLM Framework** | Any (via LiteLLM) | Any (manual integration) |
| **Multi-Agent** | ✅ Built-in | ✅ Via graph |
| **Pattern Learning** | ✅ Conscious Agent (background) | ✅ Manual pattern tracking |
| **Ease of Use** | ⭐⭐⭐⭐⭐ Very Easy | ⭐⭐⭐ Manual |
| **Control** | ⭐⭐⭐ Automatic | ⭐⭐⭐⭐⭐ Full Control |
| **Graph Structure** | Relational (SQL) | Graph (nodes/edges) |
| **Stars** | 2.7k | Unknown |
| **License** | Apache 2.0 | MIT |
| **Status** | Active (Oct 2025) | Unknown |

## Detailed Comparison

### Memori

**How It Works:**
- Intercepts LLM calls transparently
- Automatically injects context before calls
- Automatically records after calls
- Background "Conscious Agent" analyzes patterns
- No code changes needed (just enable)

**Pros:**
- ✅ Zero-code integration (just `memori.enable()`)
- ✅ Automatic context injection
- ✅ Automatic recording
- ✅ Background pattern analysis
- ✅ Multi-user support built-in
- ✅ Framework integrations (LangChain, AutoGen, CrewAI, etc.)
- ✅ Production-ready
- ✅ Active development (2.7k stars)

**Cons:**
- ⚠️ Less control over memory structure
- ⚠️ Relational model (not graph)
- ⚠️ Less explicit relationship tracking

**Best For:**
- Quick integration
- Automatic memory management
- Multi-agent systems
- Production deployments

### mem-layer

**How It Works:**
- Manual API calls (`api.create_node()`, `api.create_edge()`)
- Explicit graph structure (nodes and edges)
- Manual context loading
- Manual pattern tracking

**Pros:**
- ✅ Full control over memory structure
- ✅ Graph-based (explicit relationships)
- ✅ Explicit relationship tracking
- ✅ Fine-grained control

**Cons:**
- ⚠️ Requires code changes everywhere
- ⚠️ Manual context injection
- ⚠️ Manual recording
- ⚠️ More work to integrate
- ⚠️ Unknown maintenance status

**Best For:**
- Complex relationship tracking
- Explicit graph structures
- Fine-grained control

## Recommendation: **Memori**

### Why Memori is Better for Our Use Case

1. **Zero-Code Integration**
   - Just `memori.enable()` - no code changes needed
   - Works with existing Skills and MCP tools
   - Transparent to agents

2. **Automatic Context Management**
   - Agents don't need to manually load context
   - Context automatically injected before LLM calls
   - No workflow changes needed

3. **Background Pattern Learning**
   - "Conscious Agent" analyzes patterns automatically
   - Promotes important memories
   - No manual pattern tracking needed

4. **Production Ready**
   - 2.7k stars, active development
   - Framework integrations
   - Multi-user support
   - Well-documented

5. **Fits Our Architecture**
   - Works with any LLM framework
   - Supports PostgreSQL (we can use existing DB)
   - Multi-agent support built-in
   - Transparent to Skills and MCP tools

### When to Use mem-layer Instead

- Need explicit graph relationships (nodes/edges)
- Need fine-grained control over memory structure
- Building custom memory system
- Need graph traversal algorithms

## Integration Plan: Memori

### Phase 1: Setup (Day 1)

1. **Install Memori**
   ```bash
   pip install memori
   ```

2. **Configure Database**
   ```python
   from memori import Memori
   
   memori = Memori(
       database_connect="postgresql://user:pass@localhost/memori",
       conscious_ingest=True,  # Short-term working memory
       auto_ingest=True,       # Dynamic search per query
       openai_api_key="sk-..."  # Or use environment variable
   )
   memori.enable()
   ```

3. **Test Integration**
   - Test with simple agent workflow
   - Verify context injection
   - Verify recording

### Phase 2: Agent Workflow Integration (Day 2-3)

1. **Update Agent Workflow**
   - Add memory loading to startup
   - Document memory usage in prompts
   - Add memory helpers

2. **Update Agent Prompts**
   - Add memory section
   - Document automatic context injection
   - Add memory query examples

3. **Test with Real Workflow**
   - Use with actual agent tasks
   - Verify cross-session context
   - Verify pattern learning

### Phase 3: Advanced Features (Week 2)

1. **Multi-Agent Support**
   - Configure namespaces per agent
   - Test agent-to-agent context sharing

2. **Pattern Learning**
   - Monitor Conscious Agent
   - Review promoted memories
   - Adjust patterns

3. **Integration with Skills**
   - Skills automatically benefit from memory
   - Document decisions in skills
   - Track skill usage patterns

## Implementation: Memori Integration

### Step 1: Create Memory Helper

```python
# apps/agent_memory/memori_helper.py
from memori import Memori, ConfigManager
import os

def get_memori_instance():
    """Get configured Memori instance"""
    config = ConfigManager()
    config.auto_load()  # Loads from environment
    
    memori = Memori(
        database_connect=os.getenv("MEMORI_DATABASE_CONNECTION_STRING"),
        conscious_ingest=True,
        auto_ingest=True,
    )
    memori.enable()
    return memori

# Usage in agent workflow
memori = get_memori_instance()
# That's it! Memory is now active
```

### Step 2: Update Agent Workflow

```markdown
## Memory System (Automatic)

Memori is automatically enabled. You don't need to do anything special:

1. **Context is Automatic**: Memori automatically injects relevant context before each LLM call
2. **Recording is Automatic**: All conversations are automatically recorded
3. **Pattern Learning**: Conscious Agent analyzes patterns in the background

### What Gets Remembered

- All conversations
- Decisions made
- Patterns identified
- Context automatically retrieved

### Querying Memory (Optional)

If you need to explicitly query memory:

```python
# Memory is automatically used, but you can query if needed
from memori import Memori
memori = get_memori_instance()

# Query recent decisions
recent_decisions = memori.query("decisions from last week")
```

### Documenting Decisions

Decisions are automatically extracted, but you can explicitly document:

```python
# Explicitly document important decisions
memori.remember(
    content="Use PostgreSQL for database",
    category="decision",
    importance=0.9
)
```
```

### Step 3: Environment Configuration

```bash
# .env
MEMORI_DATABASE__CONNECTION_STRING="postgresql://user:pass@localhost/memori"
MEMORI_AGENTS__OPENAI_API_KEY="sk-..."
MEMORI_MEMORY__NAMESPACE="home-server"
```

## Migration from mem-layer Plan

If we had started with mem-layer, we'd need to:
- Replace all `api.create_node()` calls
- Replace all `api.create_edge()` calls
- Replace all `api.query()` calls
- Update all agent prompts

With Memori:
- No code changes needed
- Just enable and it works
- Transparent to existing workflow

## Next Steps

1. **Install Memori**: `pip install memori`
2. **Configure Database**: Set up PostgreSQL connection
3. **Enable Memory**: Add `memori.enable()` to agent workflow
4. **Test**: Verify automatic context injection
5. **Document**: Update agent prompts with memory info

---

**Recommendation**: Use **Memori** for automatic, transparent memory integration.

**Status**: Ready to implement
**Priority**: High
**Effort**: Low (just enable it!)

