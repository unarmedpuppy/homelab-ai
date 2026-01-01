# Local Agent Harness Enhancement Plan

**Created**: 2025-01-01
**Status**: Planning/Research
**Priority**: Low (future consideration)

## Context

Explored whether the Claude Agents SDK could work with our local vLLM infrastructure. Short answer: **No** - it's tightly coupled to Anthropic's proprietary CLI binary.

This document captures the analysis and options for getting Claude Code-like features with local models.

---

## Current State

Our `local-ai-router` agent harness (`apps/local-ai-router/router.py`):

| Feature | Implementation | Status |
|---------|----------------|--------|
| Host-controlled loop | Model emits ONE action per turn | Good |
| Provider-agnostic | Works with any OpenAI-compatible backend | Good |
| Tool calling | 19 tools (file ops, git, shell, skills) | Good |
| Skill discovery | Same skills as human operators | Unique advantage |
| Streaming | SSE support | Good |
| Memory | SQLite-backed, opt-in per request | Good |

**Endpoint**: `/agent/run` - runs autonomous agent tasks

---

## Gap Analysis: Claude Code Features

| Feature | Claude Code | Our Setup | Gap | Priority |
|---------|-------------|-----------|-----|----------|
| **MCP Protocol** | Native support for tool servers | Custom tools only | Medium | Low |
| **Subagents** | Parallel execution with isolated contexts | Single agent | Yes | Medium |
| **Permission hooks** | Pre/post tool execution callbacks | None | Yes | High |
| **Session persistence** | Conversation continuity across restarts | Memory system (opt-in) | Partial | Low |
| **Context compaction** | Auto-summarization for long conversations | None | Yes | Medium |
| **Computer use** | Browser, desktop control | Shell only | Yes | Low |

---

## Options

### Option 1: Enhance Current Harness (Recommended)

Add missing features incrementally to `local-ai-router`:

#### Phase 1: Permission Hooks (Easy)
```python
# Add to agent loop
class ToolPermission:
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"

async def pre_tool_hook(tool_name: str, args: dict) -> ToolPermission:
    """Called before each tool execution"""
    # Dangerous operations require confirmation
    if tool_name == "run_shell" and "rm " in args.get("command", ""):
        return ToolPermission.ASK
    return ToolPermission.ALLOW

async def post_tool_hook(tool_name: str, result: any) -> None:
    """Called after each tool execution for logging/auditing"""
    pass
```

#### Phase 2: Context Compaction (Medium)
```python
async def compact_context(messages: list, max_tokens: int = 4000) -> list:
    """Summarize older messages to fit context window"""
    if estimate_tokens(messages) < max_tokens:
        return messages
    
    # Keep system prompt + last N messages
    # Summarize middle messages
    summary = await summarize_messages(messages[1:-5])
    return [messages[0], {"role": "system", "content": f"Previous context: {summary}"}, *messages[-5:]]
```

#### Phase 3: Subagent Support (Medium-Hard)
```python
class SubAgent:
    """Isolated agent context for parallel execution"""
    def __init__(self, parent_context: dict, task: str):
        self.context = {**parent_context, "isolated": True}
        self.task = task
        self.messages = []
    
    async def run(self) -> str:
        """Run subtask in isolation"""
        # Separate message history
        # Limited tool access
        # Reports back to parent
```

**Effort**: 2-3 sessions
**Benefit**: Keep full control, works with any model, no vendor lock-in

---

### Option 2: Adopt Model-Agnostic Framework

Replace custom harness with established framework:

| Framework | vLLM Compatible | Tool Calling | Multi-Agent | Learning Curve | Notes |
|-----------|-----------------|--------------|-------------|----------------|-------|
| **OpenAI Agents SDK** | Yes | Excellent | Good | Low | Simplest path |
| **LangGraph** | Yes | Excellent | Best | High | Most powerful |
| **CrewAI** | Yes | Good | Best | Low-Medium | Role-based teams |
| **Pydantic AI** | Yes | Excellent | Good | Low | Type-safe |

**Integration pattern**:
```python
from openai import OpenAI

# Point at local vLLM
client = OpenAI(
    base_url="http://localhost:8012/v1",  # local-ai-router
    api_key="unused"
)

# Use with framework
agent = Agent(client=client, ...)
```

**Effort**: 1-2 sessions to prototype
**Tradeoff**: Lose skill-based discovery (our unique feature)

---

### Option 3: Hybrid Approach

Use Claude API for complex orchestration, local models for execution:

```
Claude API (planning, complex reasoning)
    ↓
Local AI Router (tool execution)
    ↓
vLLM 3090/3070 (fast inference for subtasks)
```

**Implementation**:
```python
# Orchestration layer uses Claude
orchestrator = ClaudeClient(api_key=ANTHROPIC_KEY)
plan = await orchestrator.plan(task)

# Execution uses local models
for step in plan.steps:
    result = await local_agent.execute(step)
```

**Benefit**: Best reasoning + local execution
**Cost**: Claude API usage (~$3/MTok input, $15/MTok output)

---

## Model Recommendations

Current models have tool-calling limitations:

| Model | Tool Calling | Parallel Calls | Reliability | Notes |
|-------|--------------|----------------|-------------|-------|
| **Qwen2.5-7B** (3070) | Works | Limited | Medium | Current - context limited |
| **Qwen2.5-14B** (3090) | Works | Limited | Good | Current - better |
| **Hermes-3-Llama-3.1-8B** | Excellent | Yes | Best | Consider for 3070 |
| **Functionary-v3** | Purpose-built | Yes | Best | Designed for function calling |
| **Mistral-7B-Instruct-v0.3** | Works | No | Good | Alternative |

**Recommendation**: Consider swapping to Hermes-3 or Functionary for better agent reliability.

---

## Research Sources

### Claude Agents SDK
- Repo: `anthropics/claude-agent-sdk-python`
- Architecture: Subprocess wrapping Claude Code CLI (proprietary binary)
- **Cannot work with non-Anthropic models**

### Model-Agnostic Frameworks
- OpenAI Agents SDK: Lightweight, Python-first, minimal abstractions
- LangGraph: DAG-based workflows, best for complex state management
- CrewAI: Role-based multi-agent collaboration
- Pydantic AI: Type-safe agent development

### vLLM Tool Calling
- Full OpenAI-compatible tool calling support
- Supports `tool_choice="auto"`, `"required"`, `"none"`
- Model-dependent parallel call support
- Requires correct chat template for each model family

---

## Decision Matrix

| Criteria | Option 1 (Enhance) | Option 2 (Framework) | Option 3 (Hybrid) |
|----------|-------------------|---------------------|-------------------|
| Effort | Medium | Low-Medium | Medium |
| Flexibility | Highest | Medium | High |
| Cost | $0 | $0 | API costs |
| Skill discovery | Keep | Lose | Keep |
| Best reasoning | Local only | Local only | Claude |
| Vendor lock-in | None | None | Partial |

---

## Next Steps (When Ready)

1. [ ] Decide on approach (Option 1 recommended)
2. [ ] If Option 1: Implement permission hooks first
3. [ ] Test Hermes-3 or Functionary models on 3070
4. [ ] Prototype context compaction
5. [ ] Consider subagent support for parallel tasks

---

## Related Files

- `apps/local-ai-router/router.py` - Current agent implementation
- `apps/local-ai-router/README.md` - Agent endpoint documentation
- `agents/skills/` - Skill definitions used by agent
- `apps/local-ai-server/docker-compose.yml` - 3070 vLLM config
