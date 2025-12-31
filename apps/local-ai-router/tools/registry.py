"""Tool registry and execution dispatcher.

Central registry of all tools available to the agent.
Handles tool definition generation and execution routing.
"""

import time
import logging
from typing import Callable, Any

from .security import audit, validate_path, validate_command

logger = logging.getLogger(__name__)

# =============================================================================
# Tool Registry
# =============================================================================

# Registry maps tool names to their handlers
# Each handler has signature: (arguments: dict, working_dir: str) -> str
TOOL_REGISTRY: dict[str, Callable[[dict, str], str]] = {}

# OpenAI function definitions for each tool
TOOL_DEFINITIONS: list[dict] = []


def register_tool(
    name: str,
    description: str,
    parameters: dict,
    handler: Callable[[dict, str], str]
):
    """
    Register a tool with the registry.
    
    Args:
        name: Tool name (used in function calls)
        description: Description for the LLM
        parameters: JSON Schema for parameters
        handler: Function to execute the tool
    """
    TOOL_REGISTRY[name] = handler
    
    TOOL_DEFINITIONS.append({
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters
        }
    })
    
    logger.debug(f"Registered tool: {name}")


def get_tool_definitions() -> list[dict]:
    """Get OpenAI-compatible tool definitions for all registered tools."""
    return TOOL_DEFINITIONS


def execute_tool(name: str, arguments: dict, working_dir: str) -> str:
    """
    Execute a tool by name.
    
    Args:
        name: Tool name
        arguments: Tool arguments
        working_dir: Working directory context
        
    Returns:
        Tool result string
    """
    start_time = time.time()
    success = False
    result = ""
    
    try:
        if name not in TOOL_REGISTRY:
            result = f"Error: Unknown tool: {name}"
            return result
        
        handler = TOOL_REGISTRY[name]
        result = handler(arguments, working_dir)
        success = not result.startswith("Error:")
        return result
        
    except Exception as e:
        result = f"Error executing {name}: {e}"
        logger.exception(f"Tool execution failed: {name}")
        return result
        
    finally:
        duration_ms = (time.time() - start_time) * 1000
        audit.log(
            tool_name=name,
            arguments=arguments,
            result=result,
            success=success,
            working_dir=working_dir,
            duration_ms=duration_ms
        )


# =============================================================================
# Import and register all tools
# =============================================================================

def _register_all_tools():
    """Import and register all tool modules.
    
    Core Architecture: Skill-Based Agent
    =====================================
    Instead of hardcoding capabilities as Python tools, the agent
    discovers and uses skills from agents/skills/ - the same skills
    used by human operators.
    
    Core tools (always loaded):
    - file_tools: read_file, write_file, edit_file, list_directory, search_files
    - shell_tools: run_shell, task_complete
    - skill_tools: list_skills, read_skill, search_skills
    
    Git tools are also included since they're fundamental to the workflow.
    
    All other capabilities (SSH, Docker, HTTP, deployment, etc.) are
    provided through skills that the agent discovers on-demand.
    """
    from . import file_tools
    from . import shell_tools
    from . import git_tools
    from . import skill_tools
    from . import server_tools


_register_all_tools()
