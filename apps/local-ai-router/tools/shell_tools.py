"""Shell execution tools for the agent.

Tools:
- run_shell: Execute shell commands with safety checks
- task_complete: Signal task completion (termination tool)
"""

import os
import subprocess

from .security import validate_path, validate_command, SHELL_TIMEOUT
from .registry import register_tool

# =============================================================================
# Run Shell Tool
# =============================================================================

def _run_shell(arguments: dict, working_dir: str) -> str:
    """Execute a shell command with safety checks."""
    cmd_dir = arguments.get("working_dir", working_dir)
    
    # Validate working directory
    valid, resolved_dir = validate_path(cmd_dir, working_dir)
    if not valid:
        return f"Error: {resolved_dir}"
    
    command = arguments["command"]
    
    # Validate command against blocklists
    allowed, error = validate_command(command)
    if not allowed:
        return f"Error: {error}"
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=resolved_dir,
            capture_output=True,
            text=True,
            timeout=arguments.get("timeout", SHELL_TIMEOUT)
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


register_tool(
    name="run_shell",
    description="Execute a shell command and return its output. Use for git, npm, docker, and other CLI tools. Dangerous commands are blocked.",
    parameters={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Shell command to execute"
            },
            "working_dir": {
                "type": "string",
                "description": "Directory to run command in (optional, defaults to task working directory)"
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (optional, default 30)"
            }
        },
        "required": ["command"]
    },
    handler=_run_shell
)

# =============================================================================
# Task Complete Tool (Special Termination Signal)
# =============================================================================

def _task_complete(arguments: dict, working_dir: str) -> str:
    """Signal task completion. This is a termination tool."""
    return arguments.get("answer", "Task completed")


register_tool(
    name="task_complete",
    description="Signal that the task is complete and provide the final answer. Call this when you have finished the task.",
    parameters={
        "type": "object",
        "properties": {
            "answer": {
                "type": "string",
                "description": "Final answer or summary of what was accomplished"
            }
        },
        "required": ["answer"]
    },
    handler=_task_complete
)
