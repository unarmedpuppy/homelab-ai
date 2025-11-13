"""
Activity Monitoring Tools for MCP Server

Provides tools for agents to update their status and log activities.
"""

import sys
import time
from pathlib import Path
from typing import Dict, Optional, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import activity logger
try:
    from apps.agent_monitoring.activity_logger.activity_logger import (
        update_agent_status as _update_agent_status,
        get_agent_status as _get_agent_status,
        log_action as _log_action,
        start_agent_session as _start_agent_session,
        end_agent_session as _end_agent_session
    )
except ImportError:
    # Fallback: try direct path
    activity_logger_path = project_root / "apps" / "agent-monitoring" / "activity_logger"
    sys.path.insert(0, str(activity_logger_path))
    from activity_logger import (
        update_agent_status as _update_agent_status,
        get_agent_status as _get_agent_status,
        log_action as _log_action,
        start_agent_session as _start_agent_session,
        end_agent_session as _end_agent_session
    )

from mcp.server import Server
from tools.logging_decorator import set_agent_id_context, clear_agent_id_context


def register_activity_monitoring_tools(server: Server):
    """Register activity monitoring tools with MCP server."""

    @server.tool()
    async def update_agent_status(
        agent_id: str,
        status: str,
        current_task_id: Optional[str] = None,
        progress: Optional[str] = None,
        blockers: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an agent's current status in the monitoring system.

        Args:
            agent_id: ID of the agent (e.g., "agent-001")
            status: Current status - one of: "active", "idle", "blocked", "completed"
            current_task_id: Optional task ID the agent is working on (e.g., "T1.3")
            progress: Optional progress description
            blockers: Optional description of blockers/issues

        Returns:
            A dictionary containing status, status_id, and message.
        """
        try:
            status_id = _update_agent_status(
                agent_id=agent_id,
                status=status,
                current_task_id=current_task_id,
                progress=progress,
                blockers=blockers
            )
            
            return {
                "status": "success",
                "status_id": status_id,
                "message": f"Agent {agent_id} status updated to {status}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to update agent status: {str(e)}"
            }

    @server.tool()
    async def get_agent_status(
        agent_id: str
    ) -> Dict[str, Any]:
        """
        Get current status of an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            A dictionary containing agent status information.
        """
        try:
            agent_status = _get_agent_status(agent_id)
            
            if agent_status:
                return {
                    "status": "success",
                    "agent_status": agent_status
                }
            else:
                return {
                    "status": "not_found",
                    "message": f"No status found for agent {agent_id}"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get agent status: {str(e)}"
            }

    @server.tool()
    async def start_agent_session(
        agent_id: str
    ) -> Dict[str, Any]:
        """
        Start a new agent session.

        Args:
            agent_id: ID of the agent

        Returns:
            A dictionary containing status and session_id.
        """
        try:
            session_id = _start_agent_session(agent_id)
            
            # Set agent_id in context for automatic logging
            set_agent_id_context(agent_id)
            
            return {
                "status": "success",
                "session_id": session_id,
                "message": f"Session started for agent {agent_id}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to start session: {str(e)}"
            }

    @server.tool()
    async def end_agent_session(
        agent_id: str,
        tasks_completed: int = 0,
        tools_called: int = 0
    ) -> Dict[str, Any]:
        """
        End an agent session and record statistics.

        Args:
            agent_id: ID of the agent
            tasks_completed: Number of tasks completed in this session
            tools_called: Number of tools called in this session

        Returns:
            A dictionary containing status and message.
        """
        try:
            _end_agent_session(
                agent_id=agent_id,
                tasks_completed=tasks_completed,
                tools_called=tools_called
            )
            
            # Clear agent_id from context
            clear_agent_id_context()
            
            return {
                "status": "success",
                "message": f"Session ended for agent {agent_id}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to end session: {str(e)}"
            }

