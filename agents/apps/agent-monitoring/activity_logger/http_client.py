"""
HTTP client for activity logger to send data to backend API.

This module provides functions to log actions, update status, and manage sessions
via HTTP requests to the agent monitoring backend API.
"""

import os
import json
import requests
from typing import Optional, Dict, Any
import sys

# Default API URL - can be overridden with environment variable
# Default to localhost for local-first architecture
DEFAULT_API_URL = "http://localhost:3001"
API_URL = os.getenv('AGENT_MONITORING_API_URL', DEFAULT_API_URL)

# Request timeout in seconds
REQUEST_TIMEOUT = 5


def _make_request(method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> bool:
    """
    Make HTTP request to backend API.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint (e.g., '/api/actions')
        data: Optional request body data
        
    Returns:
        True if request succeeded, False otherwise
    """
    try:
        url = f"{API_URL}{endpoint}"
        response = requests.request(
            method,
            url,
            json=data,
            timeout=REQUEST_TIMEOUT,
            headers={'Content-Type': 'application/json'}
        )
        return response.status_code in [200, 201]
    except requests.exceptions.RequestException as e:
        # Silently fail - will fallback to SQLite
        if os.getenv('AGENT_MONITORING_DEBUG'):
            print(f"API request failed: {e}", file=sys.stderr)
        return False
    except Exception as e:
        if os.getenv('AGENT_MONITORING_DEBUG'):
            print(f"Unexpected error in API request: {e}", file=sys.stderr)
        return False


def log_action_via_api(
    agent_id: str,
    action_type: str,
    tool_name: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    result_status: str = "success",
    duration_ms: Optional[int] = None,
    error: Optional[str] = None
) -> bool:
    """
    Log an action via backend API.
    
    Args:
        agent_id: ID of the agent performing the action
        action_type: Type of action (mcp_tool, memory_query, etc.)
        tool_name: Name of the tool/function called
        parameters: Parameters passed to the tool
        result_status: "success" or "error"
        duration_ms: Duration in milliseconds
        error: Error message if failed
        
    Returns:
        True if API call succeeded, False otherwise
    """
    data = {
        "agent_id": agent_id,
        "action_type": action_type,
        "tool_name": tool_name,
        "parameters": parameters,
        "result_status": result_status,
        "duration_ms": duration_ms,
        "error": error
    }
    
    return _make_request('POST', '/api/actions', data)


def update_agent_status_via_api(
    agent_id: str,
    status: str,
    current_task_id: Optional[str] = None,
    progress: Optional[str] = None,
    blockers: Optional[str] = None
) -> bool:
    """
    Update agent status via backend API.
    
    Args:
        agent_id: ID of the agent
        status: Current status (active, idle, blocked, completed)
        current_task_id: Current task ID
        progress: Progress description
        blockers: Blockers/issues
        
    Returns:
        True if API call succeeded, False otherwise
    """
    data = {
        "agent_id": agent_id,
        "status": status,
        "current_task_id": current_task_id,
        "progress": progress,
        "blockers": blockers
    }
    
    return _make_request('POST', '/api/agents/status', data)


def start_session_via_api(agent_id: str) -> Optional[int]:
    """
    Start a session via backend API.
    
    Args:
        agent_id: ID of the agent
        
    Returns:
        Session ID if successful, None otherwise
    """
    try:
        url = f"{API_URL}/api/sessions"
        response = requests.post(
            url,
            json={"agent_id": agent_id},
            timeout=REQUEST_TIMEOUT,
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code == 201:
            data = response.json()
            return data.get('session_id')
        return None
    except Exception:
        return None


def end_session_via_api(
    agent_id: str,
    tasks_completed: int = 0,
    tools_called: int = 0
) -> bool:
    """
    End a session via backend API.
    
    Args:
        agent_id: ID of the agent
        tasks_completed: Number of tasks completed
        tools_called: Number of tools called
        
    Returns:
        True if API call succeeded, False otherwise
    """
    data = {
        "agent_id": agent_id,
        "tasks_completed": tasks_completed,
        "tools_called": tools_called
    }
    
    return _make_request('POST', '/api/sessions/end', data)


def is_api_available() -> bool:
    """
    Check if the backend API is available.
    
    Returns:
        True if API is reachable, False otherwise
    """
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        return response.status_code == 200
    except Exception:
        return False

