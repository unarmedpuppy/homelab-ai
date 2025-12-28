"""Agent loop implementation following OpenCode's host-controlled design.

Design Principles (from OpenCode):
- The HOST, not the model, owns: loop control, step count, tool execution, error handling, termination
- Model is a stateless decision oracle
- Single-action constraint: model emits exactly ONE action per turn
- Host-enforced retries with structured feedback for malformed output
- Provider-agnostic: can swap Claude, GPT-4, local models without system rewrite
"""

import os
import json
import logging
import subprocess
import asyncio
from pathlib import Path
from typing import Optional, Literal, Union
from pydantic import BaseModel, Field
from enum import Enum

logger = logging.getLogger(__name__)

# Configuration
MAX_STEPS = int(os.getenv("AGENT_MAX_STEPS", "50"))
MAX_RETRIES = int(os.getenv("AGENT_MAX_RETRIES", "3"))
ALLOWED_PATHS = os.getenv("AGENT_ALLOWED_PATHS", "/tmp,/home").split(",")
SHELL_TIMEOUT = int(os.getenv("AGENT_SHELL_TIMEOUT", "30"))


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


# Tool definitions for OpenAI function calling
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file. Use this to examine files before making changes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the file to read"
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Optional starting line number (1-indexed)"
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Optional ending line number (inclusive)"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file, creating it if it doesn't exist or overwriting if it does.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the file to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Edit a file by replacing a specific string with new content. The old_string must match exactly.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the file to edit"
                    },
                    "old_string": {
                        "type": "string",
                        "description": "Exact string to find and replace"
                    },
                    "new_string": {
                        "type": "string",
                        "description": "String to replace old_string with"
                    }
                },
                "required": ["path", "old_string", "new_string"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "Execute a shell command and return its output. Use for git, npm, docker, and other CLI tools.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute"
                    },
                    "working_dir": {
                        "type": "string",
                        "description": "Directory to run command in (optional)"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for files matching a pattern or content. Uses glob for patterns, grep for content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern (e.g., '**/*.py') or text to search for"
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory to search in"
                    },
                    "content_search": {
                        "type": "boolean",
                        "description": "If true, search file contents. If false, search file names.",
                        "default": False
                    }
                },
                "required": ["pattern", "path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List contents of a directory with file types and sizes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the directory"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "task_complete",
            "description": "Signal that the task is complete and provide the final answer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "string",
                        "description": "Final answer or summary of what was accomplished"
                    }
                },
                "required": ["answer"]
            }
        }
    }
]


def validate_path(path: str, working_dir: str) -> tuple[bool, str]:
    """Validate that a path is allowed and resolve it."""
    try:
        # Resolve the path
        if not os.path.isabs(path):
            path = os.path.join(working_dir, path)
        resolved = os.path.realpath(path)

        # Check if path is under allowed directories
        allowed = False
        for allowed_path in ALLOWED_PATHS:
            if resolved.startswith(os.path.realpath(allowed_path.strip())):
                allowed = True
                break

        # Also allow working directory
        if resolved.startswith(os.path.realpath(working_dir)):
            allowed = True

        if not allowed:
            return False, f"Path {resolved} is not in allowed directories: {ALLOWED_PATHS}"

        return True, resolved
    except Exception as e:
        return False, f"Invalid path: {e}"


def execute_tool(name: str, arguments: dict, working_dir: str) -> str:
    """Execute a tool and return the result. Host-controlled execution."""
    try:
        if name == "read_file":
            valid, path = validate_path(arguments["path"], working_dir)
            if not valid:
                return f"Error: {path}"

            if not os.path.exists(path):
                return f"Error: File not found: {path}"

            with open(path, "r") as f:
                lines = f.readlines()

            start = arguments.get("start_line", 1) - 1
            end = arguments.get("end_line", len(lines))

            # Add line numbers
            result_lines = []
            for i, line in enumerate(lines[start:end], start=start+1):
                result_lines.append(f"{i:4d}| {line.rstrip()}")

            return "\n".join(result_lines) if result_lines else "(empty file)"

        elif name == "write_file":
            valid, path = validate_path(arguments["path"], working_dir)
            if not valid:
                return f"Error: {path}"

            # Create parent directories if needed
            os.makedirs(os.path.dirname(path), exist_ok=True)

            with open(path, "w") as f:
                f.write(arguments["content"])

            return f"Successfully wrote {len(arguments['content'])} bytes to {path}"

        elif name == "edit_file":
            valid, path = validate_path(arguments["path"], working_dir)
            if not valid:
                return f"Error: {path}"

            if not os.path.exists(path):
                return f"Error: File not found: {path}"

            with open(path, "r") as f:
                content = f.read()

            old_string = arguments["old_string"]
            new_string = arguments["new_string"]

            if old_string not in content:
                return f"Error: old_string not found in file. Make sure it matches exactly."

            if content.count(old_string) > 1:
                return f"Error: old_string found {content.count(old_string)} times. Provide more context for a unique match."

            new_content = content.replace(old_string, new_string, 1)

            with open(path, "w") as f:
                f.write(new_content)

            return f"Successfully edited {path}"

        elif name == "run_shell":
            cmd_dir = arguments.get("working_dir", working_dir)
            valid, resolved_dir = validate_path(cmd_dir, working_dir)
            if not valid:
                return f"Error: {resolved_dir}"

            command = arguments["command"]

            # Block dangerous commands
            dangerous = ["rm -rf /", "mkfs", "> /dev/sd", "dd if=", ":(){ :|:& };:"]
            for d in dangerous:
                if d in command:
                    return f"Error: Blocked dangerous command pattern: {d}"

            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=resolved_dir,
                    capture_output=True,
                    text=True,
                    timeout=SHELL_TIMEOUT
                )

                output = result.stdout
                if result.stderr:
                    output += f"\n[stderr]: {result.stderr}"
                if result.returncode != 0:
                    output += f"\n[exit code: {result.returncode}]"

                # Truncate very long output
                if len(output) > 10000:
                    output = output[:10000] + "\n... (truncated)"

                return output if output.strip() else "(no output)"

            except subprocess.TimeoutExpired:
                return f"Error: Command timed out after {SHELL_TIMEOUT} seconds"
            except Exception as e:
                return f"Error executing command: {e}"

        elif name == "search_files":
            valid, path = validate_path(arguments["path"], working_dir)
            if not valid:
                return f"Error: {path}"

            pattern = arguments["pattern"]
            content_search = arguments.get("content_search", False)

            if content_search:
                # Grep for content
                try:
                    result = subprocess.run(
                        ["grep", "-rn", "--include=*", pattern, path],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    output = result.stdout
                    if len(output) > 5000:
                        output = output[:5000] + "\n... (truncated)"
                    return output if output.strip() else "No matches found"
                except Exception as e:
                    return f"Error: {e}"
            else:
                # Glob for file patterns
                from glob import glob
                matches = glob(os.path.join(path, pattern), recursive=True)
                if not matches:
                    return "No files found matching pattern"
                return "\n".join(matches[:100])

        elif name == "list_directory":
            valid, path = validate_path(arguments["path"], working_dir)
            if not valid:
                return f"Error: {path}"

            if not os.path.isdir(path):
                return f"Error: Not a directory: {path}"

            entries = []
            for entry in sorted(os.listdir(path)):
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    entries.append(f"[DIR]  {entry}/")
                else:
                    size = os.path.getsize(full_path)
                    entries.append(f"[FILE] {entry} ({size} bytes)")

            return "\n".join(entries) if entries else "(empty directory)"

        elif name == "task_complete":
            # This is a termination signal, not a real tool
            return arguments.get("answer", "Task completed")

        else:
            return f"Error: Unknown tool: {name}"

    except Exception as e:
        return f"Error executing {name}: {e}"


def build_system_prompt(task: str, working_dir: str) -> str:
    """Build the system prompt for the agent."""
    return f"""You are an AI agent that can read files, write files, edit code, run shell commands, and search directories.

## Your Task
{task}

## Working Directory
{working_dir}

## Available Tools
You have access to these tools:
- read_file: Read file contents (always read before editing)
- write_file: Create or overwrite files
- edit_file: Make precise edits using string replacement
- run_shell: Execute shell commands
- search_files: Find files by pattern or content
- list_directory: List directory contents
- task_complete: Signal you're done and provide final answer

## Rules
1. ALWAYS read a file before editing it
2. Make ONE action at a time - do not try to do multiple things
3. Be precise with file paths - use absolute paths
4. When editing, provide enough context in old_string for unique matching
5. Call task_complete when finished to provide your final answer

## Important
- You can ONLY emit one tool call per turn
- After each tool call, you will see the result
- Think step by step and make incremental progress
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
                    tools=AGENT_TOOLS,
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

        # Execute tool call
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
