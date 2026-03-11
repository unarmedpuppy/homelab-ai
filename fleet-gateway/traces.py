"""Trace storage for Claude Code session observability."""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

import aiosqlite


async def init_db(db_path: str) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS trace_sessions (
                session_id TEXT PRIMARY KEY,
                machine_id TEXT NOT NULL,
                agent_label TEXT NOT NULL DEFAULT 'interactive',
                interactive INTEGER NOT NULL DEFAULT 1,
                model TEXT,
                cwd TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                span_count INTEGER NOT NULL DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS trace_spans (
                span_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                parent_span_id TEXT,
                tool_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                input_json TEXT,
                output_summary TEXT,
                status TEXT NOT NULL DEFAULT 'in_progress',
                start_time TEXT NOT NULL,
                end_time TEXT,
                agent_id TEXT,
                agent_transcript_path TEXT,
                FOREIGN KEY (session_id) REFERENCES trace_sessions(session_id)
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_spans_session ON trace_spans(session_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_machine ON trace_sessions(machine_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_start ON trace_sessions(start_time DESC)")
        await db.commit()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def upsert_session(
    db_path: str,
    session_id: str,
    machine_id: str,
    agent_label: str,
    interactive: bool,
    model: Optional[str],
    cwd: Optional[str],
    start_time: str,
) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO trace_sessions
                (session_id, machine_id, agent_label, interactive, model, cwd, start_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO NOTHING
            """,
            (session_id, machine_id, agent_label, 1 if interactive else 0, model, cwd, start_time),
        )
        await db.commit()


async def insert_span(
    db_path: str,
    session_id: str,
    tool_name: str,
    event_type: str,
    input_json: Optional[str],
    start_time: str,
    agent_id: Optional[str] = None,
    agent_transcript_path: Optional[str] = None,
) -> str:
    span_id = str(uuid.uuid4())
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO trace_spans
                (span_id, session_id, tool_name, event_type, input_json, start_time, status, agent_id, agent_transcript_path)
            VALUES (?, ?, ?, ?, ?, ?, 'in_progress', ?, ?)
            """,
            (span_id, session_id, tool_name, event_type, input_json, start_time, agent_id, agent_transcript_path),
        )
        await db.execute(
            "UPDATE trace_sessions SET span_count = span_count + 1 WHERE session_id = ?",
            (session_id,),
        )
        await db.commit()
    return span_id


async def update_span(
    db_path: str,
    session_id: str,
    tool_name: str,
    output_summary: Optional[str],
    status: str,
    end_time: str,
) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            UPDATE trace_spans
            SET output_summary = ?, status = ?, end_time = ?
            WHERE span_id = (
                SELECT span_id FROM trace_spans
                WHERE session_id = ? AND tool_name = ? AND status = 'in_progress'
                ORDER BY start_time DESC
                LIMIT 1
            )
            """,
            (output_summary, status, end_time, session_id, tool_name),
        )
        await db.commit()


async def update_session_end(db_path: str, session_id: str, end_time: str) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "UPDATE trace_sessions SET end_time = ? WHERE session_id = ?",
            (end_time, session_id),
        )
        await db.commit()


async def query_sessions(
    db_path: str,
    machine_id: Optional[str] = None,
    agent_label: Optional[str] = None,
    interactive: Optional[bool] = None,
    from_time: Optional[str] = None,
    to_time: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    conditions = []
    params: list = []

    if machine_id:
        conditions.append("machine_id = ?")
        params.append(machine_id)
    if agent_label:
        conditions.append("agent_label = ?")
        params.append(agent_label)
    if interactive is not None:
        conditions.append("interactive = ?")
        params.append(1 if interactive else 0)
    if from_time:
        conditions.append("start_time >= ?")
        params.append(from_time)
    if to_time:
        conditions.append("start_time <= ?")
        params.append(to_time)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.extend([limit, offset])

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            f"SELECT * FROM trace_sessions {where} ORDER BY start_time DESC LIMIT ? OFFSET ?",
            params,
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_session_detail(db_path: str, session_id: str) -> Optional[dict]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM trace_sessions WHERE session_id = ?", (session_id,)
        )
        session_row = await cursor.fetchone()
        if not session_row:
            return None

        cursor = await db.execute(
            "SELECT * FROM trace_spans WHERE session_id = ? ORDER BY start_time",
            (session_id,),
        )
        span_rows = await cursor.fetchall()

        return {**dict(session_row), "spans": [dict(s) for s in span_rows]}


async def get_stats(db_path: str) -> dict:
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            """
            SELECT machine_id, DATE(start_time) AS day, COUNT(*) AS count
            FROM trace_sessions
            WHERE start_time >= datetime('now', '-7 days')
            GROUP BY machine_id, day
            ORDER BY day DESC, machine_id
            """
        )
        rows = await cursor.fetchall()

        cursor = await db.execute(
            """
            SELECT COUNT(*) FROM trace_sessions
            WHERE end_time IS NULL AND start_time >= datetime('now', '-2 hours')
            """
        )
        active_row = await cursor.fetchone()
        active_count = active_row[0] if active_row else 0

        cursor = await db.execute(
            """
            SELECT COUNT(*) FROM trace_sessions
            WHERE start_time >= datetime('now', 'start of day')
            """
        )
        today_row = await cursor.fetchone()
        today_count = today_row[0] if today_row else 0

        return {
            "by_machine_day": [
                {"machine_id": r[0], "day": r[1], "count": r[2]} for r in rows
            ],
            "active_sessions": active_count,
            "sessions_today": today_count,
        }
