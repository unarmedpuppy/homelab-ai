"""
Calendar service for monthly view and navigation.

Provides calendar data with daily summaries, P&L, and trade counts.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List
from datetime import date, datetime, timedelta
from decimal import Decimal
from collections import defaultdict
import calendar

from app.models.trade import Trade
from app.schemas.calendar import (
    CalendarDay,
    CalendarMonth,
    CalendarSummary,
)


async def get_calendar_month(
    db: AsyncSession,
    year: int,
    month: int,
) -> CalendarMonth:
    """
    Get calendar data for a specific month.
    
    Args:
        db: Database session
        year: Year (YYYY)
        month: Month (1-12)
    
    Returns:
        CalendarMonth with days and month summary
    """
    # Validate month
    if month < 1 or month > 12:
        raise ValueError("Month must be between 1 and 12")
    
    # Get first and last day of month
    first_day = date(year, month, 1)
    last_day_num = calendar.monthrange(year, month)[1]
    last_day = date(year, month, last_day_num)
    
    # Get all trades for the month (closed trades with exit_time in range)
    start_datetime = datetime.combine(first_day, datetime.min.time())
    end_datetime = datetime.combine(last_day, datetime.max.time())
    
    query = (
        select(Trade)
        .where(
            and_(
                Trade.status == "closed",
                Trade.exit_time >= start_datetime,
                Trade.exit_time <= end_datetime,
            )
        )
    )
    
    result = await db.execute(query)
    trades = result.scalars().all()
    
    # Group trades by date
    daily_data = defaultdict(lambda: {"pnl": Decimal("0"), "count": 0})
    
    for trade in trades:
        trade_pnl = trade.calculate_net_pnl()
        if trade_pnl is None or not trade.exit_time:
            continue
        
        trade_date = trade.exit_time.date()
        daily_data[trade_date]["pnl"] += trade_pnl
        daily_data[trade_date]["count"] += 1
    
    # Create calendar days for all days in the month
    calendar_days = []
    profitable_days = 0
    losing_days = 0
    total_pnl = Decimal("0")
    total_trades = 0
    
    current_date = first_day
    while current_date <= last_day:
        day_data = daily_data.get(current_date, {"pnl": Decimal("0"), "count": 0})
        day_pnl = day_data["pnl"]
        day_count = day_data["count"]
        
        is_profitable = day_pnl > 0
        
        if day_pnl > 0:
            profitable_days += 1
        elif day_pnl < 0:
            losing_days += 1
        
        total_pnl += day_pnl
        total_trades += day_count
        
        calendar_days.append(CalendarDay(
            date=current_date,
            pnl=day_pnl,
            trade_count=day_count,
            is_profitable=is_profitable,
        ))
        
        current_date += timedelta(days=1)
    
    # Create month summary
    month_summary = CalendarSummary(
        total_pnl=total_pnl,
        total_trades=total_trades,
        profitable_days=profitable_days,
        losing_days=losing_days,
    )
    
    return CalendarMonth(
        year=year,
        month=month,
        days=calendar_days,
        month_summary=month_summary,
    )


async def get_calendar_day(
    db: AsyncSession,
    day_date: date,
) -> CalendarDay:
    """
    Get calendar data for a specific day.
    
    Args:
        db: Database session
        day_date: Date to get data for
    
    Returns:
        CalendarDay with P&L, trade count, and profitability
    """
    # Get all trades for the day
    start_datetime = datetime.combine(day_date, datetime.min.time())
    end_datetime = datetime.combine(day_date, datetime.max.time())
    
    query = (
        select(Trade)
        .where(
            and_(
                Trade.status == "closed",
                Trade.exit_time >= start_datetime,
                Trade.exit_time <= end_datetime,
            )
        )
    )
    
    result = await db.execute(query)
    trades = result.scalars().all()
    
    # Calculate daily totals
    day_pnl = Decimal("0")
    trade_count = 0
    
    for trade in trades:
        trade_pnl = trade.calculate_net_pnl()
        if trade_pnl is None:
            continue
        
        day_pnl += trade_pnl
        trade_count += 1
    
    is_profitable = day_pnl > 0
    
    return CalendarDay(
        date=day_date,
        pnl=day_pnl,
        trade_count=trade_count,
        is_profitable=is_profitable,
    )


async def get_calendar_summary(
    db: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> CalendarSummary:
    """
    Get calendar summary for a date range.
    
    Args:
        db: Database session
        date_from: Start date (inclusive)
        date_to: End date (inclusive)
    
    Returns:
        CalendarSummary with totals for the date range
    """
    # Build query
    query = select(Trade).where(Trade.status == "closed")
    
    if date_from:
        start_datetime = datetime.combine(date_from, datetime.min.time())
        query = query.where(Trade.exit_time >= start_datetime)
    
    if date_to:
        end_datetime = datetime.combine(date_to, datetime.max.time())
        query = query.where(Trade.exit_time <= end_datetime)
    
    result = await db.execute(query)
    trades = result.scalars().all()
    
    # Group by date and calculate summary
    daily_data = defaultdict(lambda: {"pnl": Decimal("0"), "count": 0})
    
    for trade in trades:
        trade_pnl = trade.calculate_net_pnl()
        if trade_pnl is None or not trade.exit_time:
            continue
        
        trade_date = trade.exit_time.date()
        daily_data[trade_date]["pnl"] += trade_pnl
        daily_data[trade_date]["count"] += 1
    
    # Calculate summary
    total_pnl = Decimal("0")
    total_trades = 0
    profitable_days = 0
    losing_days = 0
    
    for day_data in daily_data.values():
        day_pnl = day_data["pnl"]
        day_count = day_data["count"]
        
        total_pnl += day_pnl
        total_trades += day_count
        
        if day_pnl > 0:
            profitable_days += 1
        elif day_pnl < 0:
            losing_days += 1
    
    return CalendarSummary(
        total_pnl=total_pnl,
        total_trades=total_trades,
        profitable_days=profitable_days,
        losing_days=losing_days,
    )

