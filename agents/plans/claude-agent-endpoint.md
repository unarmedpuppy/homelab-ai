# Claude Agent Endpoint Plan

**Created**: 2026-01-01
**Status**: Ready to Implement
**Priority**: High

## Summary

Add a passthrough endpoint (`/agent/run/claude`) that forwards tasks directly to Claude Code CLI via Claude Harness. Claude CLI is already a full agent with its own loop, tools, and execution - we just need to pass the task and return the result.

## Key Insight

**Claude Code CLI IS an agent harness.** It has:
- Its own tool calling system
- Its own execution loop
- Its own context management
- Its own error handling

Our `/agent/run/claude` endpoint is a **simple passthrough** - not a wrapper around our agent loop.

## Architecture Comparison

### Local Agent (`/agent/run`)
```
Request → Our Agent Loop → Tool Definitions → vLLM (3090) → Tool Execution → Response
              ↑                                                    │
              └────────────── Multiple Iterations ─────────────────┘
```
**We control**: Loop, tools, steps, context, error handling

### Claude Agent (`/agent/run/claude`)
```
Request → Claude Harness → Claude CLI (claude -p) → Response
```
**Claude controls**: Everything. We just pass the task.

## Implementation

### Simple Passthrough Endpoint

**File**: `apps/local-ai-router/router.py`

```python
class ClaudeAgentRequest(BaseModel):
    """Request for Claude agent - just the task."""
    task: str = Field(..., description="The task for Claude to accomplish")
    working_directory: str = Field(default="/tmp", description="Working directory hint")


class ClaudeAgentResponse(BaseModel):
    """Response from Claude agent."""
    success: bool
    response: str
    error: Optional[str] = None


@app.post("/agent/run/claude", response_model=ClaudeAgentResponse)
async def run_claude_agent(request: ClaudeAgentRequest):
    """
    Run a task using Claude Code CLI.
    
    This is a passthrough to Claude Harness - Claude CLI handles all
    agent logic internally (tools, loop, context, etc.).
    
    Example:
        curl -X POST http://localhost:8012/agent/run/claude \\
            -H "Content-Type: application/json" \\
            -d '{"task": "Analyze the codebase and suggest improvements"}'
    """
    logger.info(f"Claude agent task: {request.task[:100]}...")
    
    # Build prompt with working directory context
    prompt = request.task
    if request.working_directory != "/tmp":
        prompt = f"Working directory: {request.working_directory}\n\n{request.task}"
    
    try:
        # Simple passthrough to Claude Harness
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                "http://host.docker.internal:8013/v1/chat/completions",
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "model": "claude-sonnet",
                }
            )
            
            if response.status_code != 200:
                return ClaudeAgentResponse(
                    success=False,
                    response="",
                    error=f"Claude Harness error: {response.text}"
                )
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            return ClaudeAgentResponse(
                success=True,
                response=content
            )
            
    except Exception as e:
        logger.error(f"Claude agent error: {e}")
        return ClaudeAgentResponse(
            success=False,
            response="",
            error=str(e)
        )
```

## Endpoint Comparison

| Aspect | `/agent/run` (Local) | `/agent/run/claude` |
|--------|---------------------|---------------------|
| **Backend** | 3090 vLLM | Claude Harness → Claude CLI |
| **Agent Loop** | Our implementation | Claude's implementation |
| **Tools** | Our 19 tools | Claude's built-in tools |
| **Step Tracking** | Yes (in our DB) | No (Claude handles internally) |
| **Streaming** | Yes | No (batch response) |
| **Cost** | $0 (electricity) | Claude Max subscription |
| **Complexity** | High (we manage everything) | Low (passthrough) |

## API Examples

### Local Agent (Complex, Tracked)
```bash
curl -X POST http://localhost:8012/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "List files in /tmp",
    "working_directory": "/tmp",
    "max_steps": 10
  }'

# Response includes: run_id, steps[], total_steps, model_used, backend
```

### Claude Agent (Simple Passthrough)
```bash
curl -X POST http://localhost:8012/agent/run/claude \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Analyze this error and suggest a fix: [error details]"
  }'

# Response: { "success": true, "response": "..." }
```

## When to Use Which

| Use Local (`/agent/run`) | Use Claude (`/agent/run/claude`) |
|--------------------------|----------------------------------|
| Need step-by-step tracking | Just need the answer |
| Using our skills system | General coding questions |
| Want to see tool calls | Complex reasoning tasks |
| Cost-sensitive | Quality-critical |
| Integration with dashboard | Quick one-off tasks |

## Success Criteria

- [ ] `/agent/run/claude` endpoint exists
- [ ] Simple request/response (no step tracking needed)
- [ ] Proper error handling for Claude Harness unavailable
- [ ] Timeout handling (Claude can take a while)
- [ ] Documented in README

## Files to Modify

| File | Changes |
|------|---------|
| `apps/local-ai-router/router.py` | Add simple passthrough endpoint |
| `apps/local-ai-router/README.md` | Document new endpoint |
| `agents/reference/local-ai-router.md` | Update agent section |

## Related

- [Claude Harness README](../../apps/claude-harness/README.md)
- [Local AI Router README](../../apps/local-ai-router/README.md)
- [Local Agent Harness Enhancement](./local-agent-harness-enhancement.md)
