"""
Activity Logger for Agent Monitoring

Logs agent actions and status updates to SQLite database.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import os


# Database path - relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "apps" / "agent-monitoring" / "data" / "agent_activity.db"


def _ensure_db_dir():
    """Ensure database directory exists."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _init_database():
    """Initialize database schema if it doesn't exist."""
    _ensure_db_dir()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Agent Status table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL,
            current_task_id TEXT,
            progress TEXT,
            blockers TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create index on agent_id for fast lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_agent_status_agent_id 
        ON agent_status(agent_id)
    """)
    
    # Create index on status for filtering
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_agent_status_status 
        ON agent_status(status)
    """)
    
    # Agent Actions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            tool_name TEXT,
            parameters TEXT,
            result_status TEXT NOT NULL,
            duration_ms INTEGER,
            error TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes for agent_actions
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_agent_actions_agent_id 
        ON agent_actions(agent_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_agent_actions_timestamp 
        ON agent_actions(timestamp)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_agent_actions_action_type 
        ON agent_actions(action_type)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_agent_actions_tool_name 
        ON agent_actions(tool_name)
    """)
    
    # Agent Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_end TIMESTAMP,
            tasks_completed INTEGER DEFAULT 0,
            tools_called INTEGER DEFAULT 0
        )
    """)
    
    # Create index on agent_id for sessions
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_agent_sessions_agent_id 
        ON agent_sessions(agent_id)
    """)
    
    conn.commit()
    conn.close()


def log_action(
    agent_id: str,
    action_type: str,
    tool_name: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    result_status: str = "success",
    duration_ms: Optional[int] = None,
    error: Optional[str] = None
) -> int:
    """
    Log an agent action to the database.
    
    Args:
        agent_id: ID of the agent performing the action
        action_type: Type of action (mcp_tool, memory_query, memory_record, task_update)
        tool_name: Name of the tool/function called
        parameters: Parameters passed to the tool (will be JSON-encoded)
        result_status: "success" or "error"
        duration_ms: Duration in milliseconds
        error: Error message if failed
        
    Returns:
        ID of the inserted action record
    """
    _init_database()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Convert parameters to JSON string
    parameters_json = json.dumps(parameters) if parameters else None
    
    cursor.execute("""
        INSERT INTO agent_actions 
        (agent_id, action_type, tool_name, parameters, result_status, duration_ms, error)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        agent_id,
        action_type,
        tool_name,
        parameters_json,
        result_status,
        duration_ms,
        error
    ))
    
    action_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return action_id


def update_agent_status(
    agent_id: str,
    status: str,
    current_task_id: Optional[str] = None,
    progress: Optional[str] = None,
    blockers: Optional[str] = None
) -> int:
    """
    Update an agent's current status.
    
    Args:
        agent_id: ID of the agent
        status: Current status (active, idle, blocked, completed)
        current_task_id: Current task ID
        progress: Progress description
        blockers: Blockers/issues
        
    Returns:
        ID of the status record (new or updated)
    """
    _init_database()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if status exists for this agent
    cursor.execute("SELECT id FROM agent_status WHERE agent_id = ?", (agent_id,))
    existing = cursor.fetchone()
    
    if existing:
        # Update existing status
        cursor.execute("""
            UPDATE agent_status
            SET status = ?, current_task_id = ?, progress = ?, blockers = ?, 
                last_updated = CURRENT_TIMESTAMP
            WHERE agent_id = ?
        """, (status, current_task_id, progress, blockers, agent_id))
        status_id = existing[0]
    else:
        # Insert new status
        cursor.execute("""
            INSERT INTO agent_status 
            (agent_id, status, current_task_id, progress, blockers)
            VALUES (?, ?, ?, ?, ?)
        """, (agent_id, status, current_task_id, progress, blockers))
        status_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return status_id


def get_agent_status(agent_id: str) -> Optional[Dict[str, Any]]:
    """
    Get current status of an agent.
    
    Args:
        agent_id: ID of the agent
        
    Returns:
        Dict with agent status information, or None if not found
    """
    _init_database()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM agent_status WHERE agent_id = ?
    """, (agent_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def start_agent_session(agent_id: str) -> int:
    """
    Start a new agent session.
    
    Args:
        agent_id: ID of the agent
        
    Returns:
        ID of the session record
    """
    _init_database()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO agent_sessions (agent_id, session_start)
        VALUES (?, CURRENT_TIMESTAMP)
    """, (agent_id,))
    
    session_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return session_id


def end_agent_session(agent_id: str, tasks_completed: int = 0, tools_called: int = 0) -> None:
    """
    End an agent session.
    
    Args:
        agent_id: ID of the agent
        tasks_completed: Number of tasks completed in this session
        tools_called: Number of tools called in this session
    """
    _init_database()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Find the most recent active session for this agent
    cursor.execute("""
        SELECT id FROM agent_sessions 
        WHERE agent_id = ? AND session_end IS NULL
        ORDER BY session_start DESC
        LIMIT 1
    """, (agent_id,))
    
    session = cursor.fetchone()
    
    if session:
        cursor.execute("""
            UPDATE agent_sessions
            SET session_end = CURRENT_TIMESTAMP,
                tasks_completed = ?,
                tools_called = ?
            WHERE id = ?
        """, (tasks_completed, tools_called, session[0]))
    
    conn.commit()
    conn.close()


# Initialize database on import
_init_database()

