"""
Daily journal API endpoints.

Provides daily journal data including trades, summaries, P&L progression, and notes.
"""

from fastapi import APIRouter, Depends, Path, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime

from app.api.dependencies import verify_api_key, DatabaseSession
from app.schemas.daily import (
    DailyJournal,
    DailySummary,
    PnLProgressionPoint,
    DailyNoteResponse,
    DailyNoteCreate,
    DailyNoteUpdate,
)
from app.schemas.trade import TradeResponse
from app.services.daily_service import (
    get_daily_journal,
    get_daily_trades,
    get_daily_summary,
    get_daily_pnl_progression,
    get_daily_note,
    create_or_update_daily_note,
    delete_daily_note,
)

router = APIRouter(dependencies=[Depends(verify_api_key)])


def parse_date_param(date_str: str, param_name: str = "date") -> date:
    """
    Parse date string parameter with error handling.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        param_name: Name of the parameter (for error messages)
    
    Returns:
        Parsed date object
    
    Raises:
        HTTPException: If date format is invalid
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {param_name} format. Use YYYY-MM-DD"
        )


@router.get("/{date_str}", response_model=DailyJournal)
async def get_journal(
    db: DatabaseSession,
    date_str: str = Path(..., description="Date in YYYY-MM-DD format"),
):
    """
    Get complete daily journal data for a specific date.
    
    Returns:
        DailyJournal with:
        - date, net_pnl
        - trades: Array of trades for the day
        - summary: Daily summary statistics
        - notes: Daily notes if any
        - pnl_progression: P&L progression throughout the day
    """
    journal_date = parse_date_param(date_str)
    journal = await get_daily_journal(db=db, journal_date=journal_date)
    return journal


@router.get("/{date_str}/trades", response_model=list[TradeResponse])
async def get_trades(
    db: DatabaseSession,
    date_str: str = Path(..., description="Date in YYYY-MM-DD format"),
):
    """
    Get all trades for a specific date.
    
    Returns:
        Array of trades for the day, ordered by exit_time
    """
    journal_date = parse_date_param(date_str)
    trades = await get_daily_trades(db=db, journal_date=journal_date)
    
    # Convert to TradeResponse format
    from app.schemas.trade import TradeResponse
    trade_responses = []
    for trade in trades:
        trade.update_calculated_fields()
        trade_responses.append(TradeResponse.model_validate(trade))
    
    return trade_responses


@router.get("/{date_str}/summary", response_model=DailySummary)
async def get_summary(
    db: DatabaseSession,
    date_str: str = Path(..., description="Date in YYYY-MM-DD format"),
):
    """
    Get daily summary for a specific date.
    
    Returns:
        DailySummary with statistics for the day
    """
    journal_date = parse_date_param(date_str)
    summary = await get_daily_summary(db=db, journal_date=journal_date)
    return summary


@router.get("/{date_str}/pnl-progression", response_model=list[PnLProgressionPoint])
async def get_pnl_progression(
    db: DatabaseSession,
    date_str: str = Path(..., description="Date in YYYY-MM-DD format"),
):
    """
    Get P&L progression throughout the day.
    
    Returns:
        Array of P&L progression points with time and cumulative P&L
    """
    journal_date = parse_date_param(date_str)
    progression = await get_daily_pnl_progression(db=db, journal_date=journal_date)
    return progression


@router.get("/{date_str}/notes", response_model=DailyNoteResponse)
async def get_notes(
    db: DatabaseSession,
    date_str: str = Path(..., description="Date in YYYY-MM-DD format"),
):
    """
    Get daily notes for a specific date.
    
    Returns:
        DailyNoteResponse if note exists, 404 if not found
    """
    journal_date = parse_date_param(date_str)
    note = await get_daily_note(db=db, note_date=journal_date)
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No notes found for date {date_str}"
        )
    
    return note


@router.post("/{date_str}/notes", response_model=DailyNoteResponse)
async def create_notes(
    db: DatabaseSession,
    date_str: str = Path(..., description="Date in YYYY-MM-DD format"),
    note_data: DailyNoteCreate = ...,
):
    """
    Create or update daily notes for a specific date.
    
    If notes already exist, they will be updated.
    
    Returns:
        DailyNoteResponse with created/updated notes
    """
    journal_date = parse_date_param(date_str)
    note = await create_or_update_daily_note(
        db=db,
        note_date=journal_date,
        note_data=note_data,
    )
    return note


@router.put("/{date_str}/notes", response_model=DailyNoteResponse)
async def update_notes(
    db: DatabaseSession,
    date_str: str = Path(..., description="Date in YYYY-MM-DD format"),
    note_data: DailyNoteUpdate = ...,
):
    """
    Update daily notes for a specific date.
    
    Returns:
        DailyNoteResponse with updated notes
    """
    journal_date = parse_date_param(date_str)
    note = await create_or_update_daily_note(
        db=db,
        note_date=journal_date,
        note_data=note_data,
    )
    return note


@router.delete("/{date_str}/notes", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notes(
    db: DatabaseSession,
    date_str: str = Path(..., description="Date in YYYY-MM-DD format"),
):
    """
    Delete daily notes for a specific date.
    
    Returns:
        204 No Content if deleted, 404 if not found
    """
    journal_date = parse_date_param(date_str)
    deleted = await delete_daily_note(db=db, note_date=journal_date)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No notes found for date {date_str}"
        )

