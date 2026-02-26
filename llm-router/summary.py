"""
Daily summary storage and retrieval.
Avery POSTs a new summary each morning; the dashboard GETs the latest.
"""
import os
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from database import get_db_connection

logger = logging.getLogger(__name__)

router = APIRouter()

SUMMARY_API_KEY = os.getenv("SUMMARY_API_KEY", "")


class SummaryCreate(BaseModel):
    content: str


class SummaryResponse(BaseModel):
    id: int
    date: str
    content: str
    created_at: str
    updated_at: str


def _row_to_response(row) -> SummaryResponse:
    return SummaryResponse(
        id=row["id"],
        date=row["date"],
        content=row["content"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.get("/latest", response_model=SummaryResponse)
def get_latest_summary():
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM daily_summaries ORDER BY date DESC LIMIT 1"
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="No summaries found")

    return _row_to_response(row)


@router.get("/{date}", response_model=SummaryResponse)
def get_summary_by_date(date: str):
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM daily_summaries WHERE date = ?", (date,)
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"No summary for {date}")

    return _row_to_response(row)


@router.post("", response_model=SummaryResponse, status_code=201)
def upsert_summary(
    body: SummaryCreate,
    x_summary_key: Optional[str] = Header(None),
):
    if not SUMMARY_API_KEY:
        raise HTTPException(status_code=500, detail="SUMMARY_API_KEY not configured on server")
    if x_summary_key != SUMMARY_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Summary-Key")

    now = datetime.now(timezone.utc).isoformat()
    today = datetime.now(timezone.utc).date().isoformat()

    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT INTO daily_summaries (date, content, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                content = excluded.content,
                updated_at = excluded.updated_at
            """,
            (today, body.content, now, now),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM daily_summaries WHERE date = ?", (today,)
        ).fetchone()

    logger.info(f"Summary upserted for {today}")
    return _row_to_response(row)
