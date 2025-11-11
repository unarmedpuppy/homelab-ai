"""
Calendar schemas for monthly view and navigation.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from typing import List, TYPE_CHECKING
from datetime import date as DateType
from decimal import Decimal

if TYPE_CHECKING:
    from datetime import date


class CalendarDay(BaseModel):
    """Single day in calendar view."""
    date: DateType = Field(..., description="Date")
    pnl: Decimal = Field(..., description="Net P&L for the day")
    trade_count: int = Field(..., ge=0, description="Number of trades on this day")
    is_profitable: bool = Field(..., description="Whether the day was profitable")
    
    model_config = ConfigDict(
        json_encoders={
            DateType: lambda v: v.isoformat() if v else None,
            Decimal: lambda v: float(v) if v is not None else None,
        }
    )


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
    
    model_config = ConfigDict(
        json_encoders={
            Decimal: lambda v: float(v) if v is not None else None,
        }
    )


# Update forward reference
CalendarMonth.model_rebuild()

