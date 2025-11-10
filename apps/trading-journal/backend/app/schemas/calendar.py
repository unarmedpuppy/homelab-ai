"""
Calendar schemas for monthly view and navigation.
"""

from pydantic import BaseModel, Field
from typing import List
from datetime import date
from decimal import Decimal


class CalendarDay(BaseModel):
    """Single day in calendar view."""
    date: date = Field(..., description="Date")
    pnl: Decimal = Field(..., description="Net P&L for the day")
    trade_count: int = Field(..., ge=0, description="Number of trades on this day")
    is_profitable: bool = Field(..., description="Whether the day was profitable")


class CalendarMonth(BaseModel):
    """Calendar data for a month."""
    year: int = Field(..., ge=2000, le=2100, description="Year")
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    days: List[CalendarDay] = Field(..., description="Days in the month with trading data")
    month_summary: "CalendarSummary" = Field(..., description="Summary for the month")


class CalendarSummary(BaseModel):
    """Summary statistics for a date range."""
    total_pnl: Decimal = Field(..., description="Total P&L")
    total_trades: int = Field(..., ge=0, description="Total number of trades")
    profitable_days: int = Field(..., ge=0, description="Number of profitable days")
    losing_days: int = Field(..., ge=0, description="Number of losing days")


# Update forward reference
CalendarMonth.model_rebuild()

