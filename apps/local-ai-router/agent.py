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
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

# Import tools from the new package
from tools import get_tool_definitions, execute_tool

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


class AgentStep(BaseModel):
    """A single step in the agent execution."""
    step_number: int
    action: AgentAction
    tool_result: Optional[str] = None
    error: Optional[str] = None


class AgentResponse(BaseModel):
    """Response from agent execution."""
    success: bool
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
    """Build the system prompt for the agent."""
    # Get tool names dynamically
    tool_names = [t["function"]["name"] for t in get_agent_tools()]
    tool_list = "\n".join(f"- {name}" for name in tool_names)
    
    return f"""You are an AI agent that can read files, write files, edit code, run shell commands, search directories, and perform git operations.

## Your Task
{task}

## Working Directory
{working_dir}

## Available Tools
You have access to these tools:
{tool_list}

## Rules
1. ALWAYS read a file before editing it
2. Make ONE action at a time - do not try to do multiple things
3. Be precise with file paths - use absolute paths when possible
4. When editing, provide enough context in old_string for unique matching
5. For git operations, always check status before committing
6. Call task_complete when finished to provide your final answer

## Important
- You can ONLY emit one tool call per turn
- After each tool call, you will see the result
- Think step by step and make incremental progress
- If a command fails, read the error and try a different approach
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
    steps: list[AgentStep] = []
    messages = [
        {"role": "system", "content": build_system_prompt(request.task, request.working_directory)},
        {"role": "user", "content": f"Please complete this task: {request.task}"}
    ]

    max_steps = min(request.max_steps, MAX_STEPS)
    terminated_reason = "max_steps_reached"
    final_answer = None
    
    # Get current tool definitions
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
            # Failed after retries
            steps.append(AgentStep(
                step_number=step_num,
                action=AgentAction(action_type=ActionType.RESPONSE, response="Failed to get valid response"),
                error=error
            ))
            terminated_reason = "parse_failure"
            break

        # Handle termination
        if action.action_type == ActionType.TERMINATE:
            steps.append(AgentStep(
                step_number=step_num,
                action=action
            ))
            final_answer = action.final_answer
            terminated_reason = "completed"
            break

        # Handle thinking (just log and continue)
        if action.action_type == ActionType.THINK:
            steps.append(AgentStep(
                step_number=step_num,
                action=action
            ))
            # Add thinking to conversation and prompt for action
            messages.append({"role": "assistant", "content": action.thinking})
            messages.append({
                "role": "user",
                "content": "Good thinking. Now please take an action by calling a tool."
            })
            continue

        # Execute tool call - using the new tools package
        if action.action_type == ActionType.TOOL_CALL and action.tool_call:
            tool_result = execute_tool(
                action.tool_call.name,
                action.tool_call.arguments,
                request.working_directory
            )

            steps.append(AgentStep(
                step_number=step_num,
                action=action,
                tool_result=tool_result
            ))

            # Add tool call and result to conversation
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

    return AgentResponse(
        success=terminated_reason == "completed",
        final_answer=final_answer,
        steps=steps,
        total_steps=len(steps),
        terminated_reason=terminated_reason
    )
