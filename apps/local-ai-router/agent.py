"""Agent loop implementation following OpenCode's host-controlled design.

Design Principles (from OpenCode):
- The HOST, not the model, owns: loop control, step count, tool execution, error handling, termination
- Model is a stateless decision oracle
- Single-action constraint: model emits exactly ONE action per turn
- Host-enforced retries with structured feedback for malformed output
- Provider-agnostic: can swap Claude, GPT-4, local models without system rewrite

Tools are now organized in the tools/ package:
- tools/file_tools.py: read_file, write_file, edit_file, search_files, list_directory
- tools/shell_tools.py: run_shell, task_complete
- tools/git_tools.py: git_status, git_diff, git_log, git_add, git_commit, git_push, git_pull, git_branch, git_checkout
- tools/security.py: Path validation, command blocklists, audit logging
"""

import os
import json
import logging
import asyncio
import time
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

from tools import get_tool_definitions, execute_tool
from agent_storage import create_agent_run, add_agent_step, complete_agent_run
from models import AgentRunStatus

logger = logging.getLogger(__name__)

# Configuration
MAX_STEPS = int(os.getenv("AGENT_MAX_STEPS", "50"))
MAX_RETRIES = int(os.getenv("AGENT_MAX_RETRIES", "3"))


class ActionType(str, Enum):
    """Single-action types the model can emit."""
    TOOL_CALL = "tool_call"
    RESPONSE = "response"
    THINK = "think"
    TERMINATE = "terminate"


class ToolCall(BaseModel):
    """A tool call action."""
    name: str
    arguments: dict


class AgentAction(BaseModel):
    """Model's single-action output. Exactly ONE field must be set."""
    action_type: ActionType
    tool_call: Optional[ToolCall] = None
    response: Optional[str] = None
    thinking: Optional[str] = None
    final_answer: Optional[str] = None


class AgentRequest(BaseModel):
    """Request to run an agent task."""
    task: str = Field(..., description="The task to accomplish")
    working_directory: str = Field(default="/tmp", description="Working directory for file operations")
    model: str = Field(default="auto", description="Model to use (auto, big, etc.)")
    max_steps: int = Field(default=50, ge=1, le=100, description="Maximum steps before termination")
    source: Optional[str] = Field(default=None, description="Source of request (n8n, api, dashboard)")
    triggered_by: Optional[str] = Field(default=None, description="What triggered this run")


class AgentStep(BaseModel):
    """A single step in the agent execution."""
    step_number: int
    action: AgentAction
    tool_result: Optional[str] = None
    error: Optional[str] = None


class AgentResponse(BaseModel):
    """Response from agent execution."""
    success: bool
    run_id: Optional[str] = None
    final_answer: Optional[str] = None
    steps: list[AgentStep]
    total_steps: int
    terminated_reason: str


def get_agent_tools() -> list[dict]:
    """Get all registered tools for the agent."""
    return get_tool_definitions()


# Export for backwards compatibility
AGENT_TOOLS = get_agent_tools()


def build_system_prompt(task: str, working_dir: str) -> str:
    """Build the system prompt for the agent.
    
    This prompt emphasizes skill-based discovery over hardcoded capabilities.
    The agent should discover what skills are available and follow their
    instructions, just like a human operator would.
    """
    return f"""You are an AI agent that accomplishes tasks by discovering and following skills.

## Your Task
{task}

## Working Directory
{working_dir}

## How You Work: Skill-Based Execution

You have access to a library of **skills** - documented workflows for common tasks.
Skills are the same guides that human operators use.

### Your Workflow (IMPORTANT):

1. **FIRST: Discover relevant skills**
   - Call `list_skills()` to see all available capabilities
   - Call `search_skills(query)` to find skills matching your task
   - Call `read_skill(name)` to get detailed instructions

2. **THEN: Follow the skill instructions**
   - Skills contain step-by-step guides with exact commands
   - Use `run_shell` to execute the commands from the skill
   - Use file tools to read/write files as instructed

3. **FINALLY: Complete the task**
   - Call `task_complete` with your final answer

### Core Tools

**Skill Discovery:**
- `list_skills(category?)` - List all available skills
- `search_skills(query)` - Search skills by keyword  
- `read_skill(name)` - Read full skill instructions

**Execution:**
- `run_shell(command)` - Execute shell commands (from skill instructions)
- `read_file(path)` - Read file contents
- `write_file(path, content)` - Write/create files
- `edit_file(path, old, new)` - Edit files precisely
- `list_directory(path)` - List directory contents
- `search_files(pattern, path?)` - Search for files

**Git (fundamental operations):**
- `git_status`, `git_diff`, `git_log`, `git_add`, `git_commit`, etc.

**Completion:**
- `task_complete(answer)` - Signal task completion

### Rules

1. **ALWAYS start by discovering skills** - Don't guess commands, find the skill first
2. **Follow skill instructions exactly** - Skills contain tested, working commands
3. **One action at a time** - Make incremental progress
4. **Read before editing** - Always read a file before modifying it
5. **Use absolute paths** - Be precise with file paths

### Example Workflow

Task: "Restart the homepage container"

1. `search_skills("docker restart")` → finds "docker-container-management"
2. `read_skill("docker-container-management")` → get instructions
3. Follow the instructions using `run_shell` commands
4. `task_complete("Homepage container restarted successfully")`

### Important

- Skills directory: /app/agents/skills (or configured location)
- If no skill exists for your task, use your judgment with core tools
- If a command fails, read the error and try a different approach
- When in doubt, list available skills to find the right one
"""


def parse_model_response(response: dict) -> tuple[AgentAction, Optional[str]]:
    """Parse model response into an AgentAction. Returns (action, error)."""
    try:
        choices = response.get("choices", [])
        if not choices:
            return None, "No choices in response"

        message = choices[0].get("message", {})

        # Check for tool calls
        tool_calls = message.get("tool_calls", [])
        if tool_calls:
            tc = tool_calls[0]  # Single-action: only process first
            func = tc.get("function", {})
            name = func.get("name", "")

            # Parse arguments
            args_str = func.get("arguments", "{}")
            try:
                args = json.loads(args_str) if isinstance(args_str, str) else args_str
            except json.JSONDecodeError:
                return None, f"Invalid JSON in tool arguments: {args_str}"

            # Check if this is termination
            if name == "task_complete":
                return AgentAction(
                    action_type=ActionType.TERMINATE,
                    final_answer=args.get("answer", "Task completed")
                ), None

            return AgentAction(
                action_type=ActionType.TOOL_CALL,
                tool_call=ToolCall(name=name, arguments=args)
            ), None

        # Check for regular content (response or thinking)
        content = message.get("content", "")
        if content:
            # Check for termination markers in content
            if "[DONE]" in content or "task_complete" in content.lower():
                return AgentAction(
                    action_type=ActionType.TERMINATE,
                    final_answer=content
                ), None

            # Treat as thinking/response
            return AgentAction(
                action_type=ActionType.THINK,
                thinking=content
            ), None

        return None, "No tool_calls or content in response"

    except Exception as e:
        return None, f"Failed to parse response: {e}"


async def run_agent_loop(
    request: AgentRequest,
    call_llm: callable
) -> AgentResponse:
    """
    Run the host-controlled agent loop.

    The HOST owns:
    - Loop control
    - Step count
    - Tool execution
    - Error handling
    - Termination conditions

    The model is a stateless decision oracle.
    """
    run_id = create_agent_run(
        task=request.task,
        working_directory=request.working_directory,
        model_requested=request.model,
        source=request.source,
        triggered_by=request.triggered_by
    )
    
    steps: list[AgentStep] = []
    messages = [
        {"role": "system", "content": build_system_prompt(request.task, request.working_directory)},
        {"role": "user", "content": f"Please complete this task: {request.task}"}
    ]

    max_steps = min(request.max_steps, MAX_STEPS)
    terminated_reason = "max_steps_reached"
    final_answer = None
    model_used = None
    backend_used = None
    
    current_tools = get_agent_tools()

    for step_num in range(1, max_steps + 1):
        logger.info(f"Agent step {step_num}/{max_steps}")

        # Call LLM with tools
        retries = 0
        action = None
        error = None

        while retries < MAX_RETRIES:
            try:
                response = await call_llm(
                    messages=messages,
                    model=request.model,
                    tools=current_tools,
                    tool_choice="auto"
                )

                action, error = parse_model_response(response)

                if action:
                    break

                # Host-enforced retry with structured feedback
                retries += 1
                logger.warning(f"Parse error (retry {retries}): {error}")
                messages.append({
                    "role": "user",
                    "content": f"[SYSTEM ERROR] Your response could not be parsed: {error}\n"
                               f"Please respond with a valid tool call or a clear message."
                })

            except Exception as e:
                retries += 1
                error = str(e)
                logger.error(f"LLM call failed (retry {retries}): {e}")
                await asyncio.sleep(1)  # Brief backoff

        if not action:
            steps.append(AgentStep(
                step_number=step_num,
                action=AgentAction(action_type=ActionType.RESPONSE, response="Failed to get valid response"),
                error=error
            ))
            add_agent_step(run_id, step_num, "response", error=error)
            terminated_reason = "parse_failure"
            break

        if action.action_type == ActionType.TERMINATE:
            steps.append(AgentStep(
                step_number=step_num,
                action=action
            ))
            add_agent_step(run_id, step_num, "terminate")
            final_answer = action.final_answer
            terminated_reason = "completed"
            break

        if action.action_type == ActionType.THINK:
            steps.append(AgentStep(
                step_number=step_num,
                action=action
            ))
            add_agent_step(run_id, step_num, "think", thinking=action.thinking)
            messages.append({"role": "assistant", "content": action.thinking})
            messages.append({
                "role": "user",
                "content": "Good thinking. Now please take an action by calling a tool."
            })
            continue

        if action.action_type == ActionType.TOOL_CALL and action.tool_call:
            step_start = time.time()
            tool_result = execute_tool(
                action.tool_call.name,
                action.tool_call.arguments,
                request.working_directory
            )
            step_duration = int((time.time() - step_start) * 1000)

            steps.append(AgentStep(
                step_number=step_num,
                action=action,
                tool_result=tool_result
            ))
            
            add_agent_step(
                run_id, step_num, "tool_call",
                tool_name=action.tool_call.name,
                tool_args=action.tool_call.arguments,
                tool_result=tool_result[:5000] if tool_result else None,
                duration_ms=step_duration
            )

            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": f"call_{step_num}",
                    "type": "function",
                    "function": {
                        "name": action.tool_call.name,
                        "arguments": json.dumps(action.tool_call.arguments)
                    }
                }]
            })
            messages.append({
                "role": "tool",
                "tool_call_id": f"call_{step_num}",
                "content": tool_result
            })

            logger.info(f"Tool {action.tool_call.name} executed: {tool_result[:200]}...")

    status = AgentRunStatus.COMPLETED if terminated_reason == "completed" else (
        AgentRunStatus.MAX_STEPS if terminated_reason == "max_steps_reached" else AgentRunStatus.FAILED
    )
    complete_agent_run(
        run_id,
        status=status,
        final_answer=final_answer,
        model_used=model_used,
        backend=backend_used,
        error=None if terminated_reason == "completed" else terminated_reason
    )

    return AgentResponse(
        success=terminated_reason == "completed",
        run_id=run_id,
        final_answer=final_answer,
        steps=steps,
        total_steps=len(steps),
        terminated_reason=terminated_reason
    )
