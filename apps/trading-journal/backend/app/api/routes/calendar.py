"""
Calendar API endpoints.

Provides calendar data for monthly view and navigation.
"""

from fastapi import APIRouter, Depends, Path, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date, datetime

from app.api.dependencies import verify_api_key, DatabaseSession
from app.schemas.calendar import (
    CalendarDay,
    CalendarMonth,
    CalendarSummary,
)
from app.services.calendar_service import (
    get_calendar_month,
    get_calendar_day,
    get_calendar_summary,
)

router = APIRouter(dependencies=[Depends(verify_api_key)])


def parse_date_param(date_str: Optional[str], param_name: str) -> Optional[date]:
    """
    Parse date string parameter with error handling.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        param_name: Name of the parameter (for error messages)
    
    Returns:
        Parsed date object, or None if date_str is None/empty
    
    Raises:
        HTTPException: If date format is invalid
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {param_name} format. Use YYYY-MM-DD"
        )


@router.get("/{year}/{month}", response_model=CalendarMonth)
async def get_month(
    db: DatabaseSession,
    year: int = Path(..., ge=2000, le=2100, description="Year (YYYY)"),
    month: int = Path(..., ge=1, le=12, description="Month (1-12)"),
):
    """
    Get calendar data for a specific month.
    
    Returns:
        CalendarMonth with:
        - days: Array of all days in the month with P&L, trade count, and profitability
        - month_summary: Summary statistics for the month
    """
    try:
        calendar_data = await get_calendar_month(db=db, year=year, month=month)
        return calendar_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/date/{date_str}", response_model=CalendarDay)
async def get_day(
    db: DatabaseSession,
    date_str: str = Path(..., description="Date in YYYY-MM-DD format"),
):
    """
    Get calendar data for a specific day.
    
    Returns:
        CalendarDay with P&L, trade count, and profitability for the day
    """
    day_date = parse_date_param(date_str, "date")
    if day_date is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date parameter is required"
        )
    
    calendar_day = await get_calendar_day(db=db, day_date=day_date)
    return calendar_day


@router.get("/summary", response_model=CalendarSummary)
async def get_summary(
    db: DatabaseSession,
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """
    Get calendar summary for a date range.
    
    Returns:
        CalendarSummary with totals for the date range:
        - total_pnl: Total P&L across all days
        - total_trades: Total number of trades
        - profitable_days: Number of profitable days
        - losing_days: Number of losing days
    """
    date_from_parsed = parse_date_param(date_from, "date_from")
    date_to_parsed = parse_date_param(date_to, "date_to")
    
    summary = await get_calendar_summary(
        db=db,
        date_from=date_from_parsed,
        date_to=date_to_parsed,
    )
    
    return summary

