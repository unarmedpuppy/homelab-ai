"""
Automatic logging decorator for MCP tools.

This decorator automatically logs all MCP tool calls to the activity logger.
Uses context variables to track the current agent_id from session start.
"""

import sys
import time
from contextvars import ContextVar
from functools import wraps
from pathlib import Path
from typing import Dict, Any, Optional, Callable

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Context variable to store current agent_id
# This is set when start_agent_session() is called
_current_agent_id: ContextVar[Optional[str]] = ContextVar('current_agent_id', default=None)

# Import activity logger
try:
    from apps.agent_monitoring.activity_logger.activity_logger import (
        log_action as _log_action
    )
except ImportError:
    # Fallback: try direct path
    activity_logger_path = project_root / "apps" / "agent-monitoring" / "activity_logger"
    sys.path.insert(0, str(activity_logger_path))
    try:
        from activity_logger import log_action as _log_action
    except ImportError:
        # If activity logger not available, create a no-op function
        def _log_action(*args, **kwargs):
            return None


def get_agent_id_from_context() -> Optional[str]:
    """
    Get agent_id from context variable (set by start_agent_session).
    
    Returns:
        Current agent_id from context, or None if not set
    """
    return _current_agent_id.get()


def set_agent_id_context(agent_id: str) -> None:
    """
    Set the current agent_id in context.
    
    This should be called by start_agent_session() to establish context.
    
    Args:
        agent_id: The agent ID to set in context
    """
    _current_agent_id.set(agent_id)


def clear_agent_id_context() -> None:
    """
    Clear the current agent_id from context.
    
    This should be called by end_agent_session() to clean up.
    """
    _current_agent_id.set(None)


def get_agent_id_from_kwargs(kwargs: Dict[str, Any]) -> str:
    """
    Extract agent_id using multiple strategies (in priority order):
    
    1. Context variable (set by start_agent_session)
    2. agent_id parameter in tool arguments
    3. from_agent parameter (used in communication tools)
    4. parent_agent_id parameter (used in agent management)
    5. Default to "agent-001" if none found
    
    Args:
        kwargs: Tool function keyword arguments
        
    Returns:
        Agent ID string
    """
    # Priority 1: Check context variable (set by start_agent_session)
    context_agent_id = get_agent_id_from_context()
    if context_agent_id:
        return context_agent_id
    
    # Priority 2: Check for agent_id parameter
    if "agent_id" in kwargs and kwargs["agent_id"]:
        return kwargs["agent_id"]
    
    # Priority 3: Check for from_agent (used in communication tools)
    if "from_agent" in kwargs and kwargs["from_agent"]:
        return kwargs["from_agent"]
    
    # Priority 4: Check for parent_agent_id (used in agent management)
    if "parent_agent_id" in kwargs and kwargs["parent_agent_id"]:
        return kwargs["parent_agent_id"]
    
    # Priority 5: Default agent ID
    return "agent-001"


def with_automatic_logging(tool_name: Optional[str] = None):
    """
    Decorator to automatically log MCP tool calls.
    
    Usage:
        @with_automatic_logging()
        async def my_tool(...):
            ...
    
    Or with custom tool name:
        @with_automatic_logging("custom_tool_name")
        async def my_tool(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        # Use provided tool_name or function name
        actual_tool_name = tool_name or func.__name__
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            result_status = "success"
            error_message = None
            result = None
            
            # Extract agent_id from kwargs
            agent_id = get_agent_id_from_kwargs(kwargs)
            
            # Prepare parameters for logging (exclude sensitive data)
            log_params = {}
            for key, value in kwargs.items():
                # Skip sensitive parameters
                if key.lower() in ["password", "token", "secret", "key", "api_key"]:
                    log_params[key] = "***REDACTED***"
                else:
                    # Convert to string if not serializable, limit length
                    try:
                        param_str = str(value)
                        if len(param_str) > 200:
                            param_str = param_str[:200] + "..."
                        log_params[key] = param_str
                    except Exception:
                        log_params[key] = "<non-serializable>"
            
            try:
                # Call the actual tool
                result = await func(*args, **kwargs)
                
                # Determine result status from return value
                if isinstance(result, dict):
                    if result.get("status") == "error":
                        result_status = "error"
                        error_message = result.get("message") or result.get("error")
                    elif result.get("status") == "success":
                        result_status = "success"
                elif result is None:
                    result_status = "error"
                    error_message = "Tool returned None"
                
                return result
                
            except Exception as e:
                result_status = "error"
                error_message = str(e)
                raise
                
            finally:
                # Log the action
                duration_ms = int((time.time() - start_time) * 1000)
                
                try:
                    _log_action(
                        agent_id=agent_id,
                        action_type="mcp_tool",
                        tool_name=actual_tool_name,
                        parameters=log_params if log_params else None,
                        result_status=result_status,
                        duration_ms=duration_ms,
                        error=error_message
                    )
                except Exception as log_error:
                    # Don't fail the tool if logging fails
                    print(f"Warning: Failed to log action: {log_error}", file=sys.stderr)
        
        return wrapper
    return decorator

