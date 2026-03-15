"""SQLite storage for eval runs and results."""
from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from typing import Optional

import aiosqlite

from models import CaseResult, RunSummary


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def init_db(db_path: str) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS eval_runs (
                run_id          TEXT PRIMARY KEY,
                suite_name      TEXT,
                model           TEXT NOT NULL,
                router_url      TEXT NOT NULL,
                started_at      TEXT NOT NULL,
                finished_at     TEXT,
                status          TEXT NOT NULL DEFAULT 'running',
                total_cases     INTEGER NOT NULL DEFAULT 0,
                passed          INTEGER NOT NULL DEFAULT 0,
                failed          INTEGER NOT NULL DEFAULT 0,
                errored         INTEGER NOT NULL DEFAULT 0,
                pass_rate       REAL,
                p50_latency_ms  REAL,
                p95_latency_ms  REAL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS eval_results (
                result_id           TEXT PRIMARY KEY,
                run_id              TEXT NOT NULL REFERENCES eval_runs(run_id),
                case_id             TEXT NOT NULL,
                category            TEXT NOT NULL,
                tags_json           TEXT,
                model               TEXT NOT NULL,
                status              TEXT NOT NULL,
                scorer_details_json TEXT NOT NULL,
                messages_json       TEXT NOT NULL,
                response_text       TEXT,
                tool_calls_json     TEXT,
                latency_ms          REAL,
                prompt_tokens       INTEGER,
                completion_tokens   INTEGER,
                error               TEXT,
                created_at          TEXT NOT NULL
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_results_run ON eval_results(run_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_results_case ON eval_results(case_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_results_status ON eval_results(status)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_runs_model ON eval_runs(model)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_runs_started ON eval_runs(started_at DESC)")
        await db.commit()


async def create_run(
    db_path: str,
    run_id: str,
    suite_name: Optional[str],
    model: str,
    router_url: str,
    total_cases: int,
) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO eval_runs (run_id, suite_name, model, router_url, started_at, status, total_cases)
            VALUES (?, ?, ?, ?, ?, 'running', ?)
            """,
            (run_id, suite_name, model, router_url, _now(), total_cases),
        )
        await db.commit()


async def insert_result(db_path: str, result: CaseResult) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO eval_results
                (result_id, run_id, case_id, category, tags_json, model, status,
                 scorer_details_json, messages_json, response_text, tool_calls_json,
                 latency_ms, prompt_tokens, completion_tokens, error, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.result_id,
                result.run_id,
                result.case_id,
                result.category,
                json.dumps(result.tags),
                result.model,
                result.status,
                json.dumps([s.model_dump() for s in result.scorer_results]),
                json.dumps(result.messages),
                result.response_text,
                json.dumps(result.tool_calls),
                result.latency_ms,
                result.prompt_tokens,
                result.completion_tokens,
                result.error,
                result.created_at,
            ),
        )
        # Increment run counters
        col = {"pass": "passed", "fail": "failed", "error": "errored"}[result.status]
        await db.execute(
            f"UPDATE eval_runs SET {col} = {col} + 1 WHERE run_id = ?",
            (result.run_id,),
        )
        await db.commit()


async def finish_run(db_path: str, run_id: str, status: str = "done") -> None:
    async with aiosqlite.connect(db_path) as db:
        # Compute latency stats from results
        cursor = await db.execute(
            "SELECT latency_ms FROM eval_results WHERE run_id = ? AND latency_ms IS NOT NULL",
            (run_id,),
        )
        rows = await cursor.fetchall()
        latencies = sorted(r[0] for r in rows)
        p50 = statistics.median(latencies) if latencies else None
        p95 = latencies[int(len(latencies) * 0.95)] if latencies else None

        # Compute pass rate
        cursor = await db.execute(
            "SELECT passed, failed, errored, total_cases FROM eval_runs WHERE run_id = ?",
            (run_id,),
        )
        row = await cursor.fetchone()
        pass_rate = None
        if row and row[3]:
            pass_rate = round(row[0] / row[3], 4)

        await db.execute(
            """
            UPDATE eval_runs
            SET status = ?, finished_at = ?, pass_rate = ?, p50_latency_ms = ?, p95_latency_ms = ?
            WHERE run_id = ?
            """,
            (status, _now(), pass_rate, p50, p95, run_id),
        )
        await db.commit()


async def get_run(db_path: str, run_id: str) -> Optional[dict]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM eval_runs WHERE run_id = ?", (run_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def list_runs(
    db_path: str,
    model: Optional[str] = None,
    suite: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    conditions, params = [], []
    if model:
        conditions.append("model = ?")
        params.append(model)
    if suite:
        conditions.append("suite_name = ?")
        params.append(suite)
    if status:
        conditions.append("status = ?")
        params.append(status)
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.extend([limit, offset])
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            f"SELECT * FROM eval_runs {where} ORDER BY started_at DESC LIMIT ? OFFSET ?",
            params,
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def query_results(
    db_path: str,
    run_id: str,
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    conditions = ["run_id = ?"]
    params: list = [run_id]
    if status:
        conditions.append("status = ?")
        params.append(status)
    if category:
        conditions.append("category = ?")
        params.append(category)
    where = "WHERE " + " AND ".join(conditions)
    params.extend([limit, offset])
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            f"SELECT * FROM eval_results {where} ORDER BY created_at LIMIT ? OFFSET ?",
            params,
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def get_result(db_path: str, result_id: str) -> Optional[dict]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM eval_results WHERE result_id = ?", (result_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_stats(db_path: str) -> dict:
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM eval_runs")
        total_runs = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM eval_runs WHERE started_at >= datetime('now', '-7 days')"
        )
        runs_7d = (await cursor.fetchone())[0]

        cursor = await db.execute(
            """
            SELECT model, COUNT(*) as runs, AVG(pass_rate) as avg_rate, AVG(p50_latency_ms) as avg_p50
            FROM eval_runs WHERE status = 'done'
            GROUP BY model ORDER BY avg_rate DESC
            """
        )
        by_model = [
            {"model": r[0], "runs": r[1], "avg_pass_rate": round(r[2] or 0, 4), "avg_p50_latency_ms": r[3]}
            for r in await cursor.fetchall()
        ]

        cursor = await db.execute(
            """
            SELECT category, COUNT(*) as total, SUM(CASE WHEN status='pass' THEN 1 ELSE 0 END) as passed
            FROM eval_results GROUP BY category
            """
        )
        by_category = [
            {"category": r[0], "total": r[1], "pass_rate": round(r[2] / r[1], 4) if r[1] else 0}
            for r in await cursor.fetchall()
        ]

        best = by_model[0] if by_model else None
        return {
            "total_runs": total_runs,
            "runs_last_7_days": runs_7d,
            "best_model": best,
            "by_model": by_model,
            "by_category": by_category,
        }
