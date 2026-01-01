import json
import logging
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from database import get_db_connection
from models import AgentRunRecord, AgentStepRecord, AgentRunWithSteps, AgentRunStatus, AgentRunsStats

logger = logging.getLogger(__name__)


def create_agent_run(
    task: str,
    working_directory: str = "/tmp",
    model_requested: str = "auto",
    source: Optional[str] = None,
    triggered_by: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    run_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO agent_runs 
            (id, task, working_directory, model_requested, status, started_at, source, triggered_by, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            task,
            working_directory,
            model_requested,
            AgentRunStatus.RUNNING.value,
            now.isoformat() + "Z",  # Add Z suffix for proper UTC parsing in JavaScript
            source,
            triggered_by,
            json.dumps(metadata) if metadata else None
        ))
        conn.commit()
    
    logger.info(f"Created agent run {run_id}: {task[:50]}...")
    return run_id


def add_agent_step(
    agent_run_id: str,
    step_number: int,
    action_type: str,
    tool_name: Optional[str] = None,
    tool_args: Optional[Dict[str, Any]] = None,
    tool_result: Optional[str] = None,
    thinking: Optional[str] = None,
    error: Optional[str] = None,
    duration_ms: Optional[int] = None
) -> int:
    now = datetime.utcnow()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO agent_steps 
            (agent_run_id, step_number, action_type, tool_name, tool_args, tool_result, thinking, error, started_at, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            agent_run_id,
            step_number,
            action_type,
            tool_name,
            json.dumps(tool_args) if tool_args else None,
            tool_result,
            thinking,
            error,
            now.isoformat() + "Z",  # Add Z suffix for proper UTC parsing in JavaScript
            duration_ms
        ))
        step_id = cursor.lastrowid or 0
        
        cursor.execute("""
            UPDATE agent_runs SET total_steps = total_steps + 1 WHERE id = ?
        """, (agent_run_id,))
        
        conn.commit()
    
    return step_id


def complete_agent_run(
    agent_run_id: str,
    status: AgentRunStatus,
    final_answer: Optional[str] = None,
    model_used: Optional[str] = None,
    backend: Optional[str] = None,
    error: Optional[str] = None
) -> None:
    now = datetime.utcnow()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT started_at FROM agent_runs WHERE id = ?", (agent_run_id,))
        row = cursor.fetchone()
        if row:
            # Handle both old format (no Z) and new format (with Z)
            started_str = row[0].rstrip("Z")
            started_at = datetime.fromisoformat(started_str)
            duration_ms = int((now - started_at).total_seconds() * 1000)
        else:
            duration_ms = None
        
        cursor.execute("""
            UPDATE agent_runs 
            SET status = ?, final_answer = ?, model_used = ?, backend = ?, 
                error = ?, completed_at = ?, duration_ms = ?
            WHERE id = ?
        """, (
            status.value,
            final_answer,
            model_used,
            backend,
            error,
            now.isoformat() + "Z",  # Add Z suffix for proper UTC parsing in JavaScript
            duration_ms,
            agent_run_id
        ))
        conn.commit()
    
    logger.info(f"Completed agent run {agent_run_id}: {status.value}")


def get_agent_run(agent_run_id: str) -> Optional[AgentRunWithSteps]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM agent_runs WHERE id = ?", (agent_run_id,))
        run_row = cursor.fetchone()
        if not run_row:
            return None
        
        run_dict = dict(run_row)
        if run_dict.get("metadata"):
            run_dict["metadata"] = json.loads(run_dict["metadata"])
        
        cursor.execute(
            "SELECT * FROM agent_steps WHERE agent_run_id = ? ORDER BY step_number",
            (agent_run_id,)
        )
        step_rows = cursor.fetchall()
        
        steps = []
        for step_row in step_rows:
            step_dict = dict(step_row)
            if step_dict.get("tool_args"):
                step_dict["tool_args"] = json.loads(step_dict["tool_args"])
            steps.append(AgentStepRecord(**step_dict))
        
        return AgentRunWithSteps(**run_dict, steps=steps)


def list_agent_runs(
    status: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[AgentRunRecord]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM agent_runs WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        if source:
            query += " AND source = ?"
            params.append(source)
        
        query += " ORDER BY started_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        runs = []
        for row in rows:
            row_dict = dict(row)
            if row_dict.get("metadata"):
                row_dict["metadata"] = json.loads(row_dict["metadata"])
            runs.append(AgentRunRecord(**row_dict))
        
        return runs


def get_agent_runs_stats() -> AgentRunsStats:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM agent_runs")
        total_runs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM agent_runs WHERE status = 'completed'")
        completed = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM agent_runs WHERE status = 'failed'")
        failed = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM agent_runs WHERE status = 'running'")
        running = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(total_steps) FROM agent_runs WHERE status != 'running'")
        avg_steps = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT AVG(duration_ms) FROM agent_runs WHERE duration_ms IS NOT NULL")
        avg_duration = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT source, COUNT(*) FROM agent_runs GROUP BY source")
        by_source = {row[0] or "unknown": row[1] for row in cursor.fetchall()}
        
        cursor.execute("SELECT status, COUNT(*) FROM agent_runs GROUP BY status")
        by_status = {row[0]: row[1] for row in cursor.fetchall()}
        
        return AgentRunsStats(
            total_runs=total_runs,
            completed=completed,
            failed=failed,
            running=running,
            avg_steps=round(avg_steps, 1),
            avg_duration_ms=round(avg_duration, 0),
            by_source=by_source,
            by_status=by_status
        )
