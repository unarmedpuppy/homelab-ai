"""
Daily journal schemas for daily view and notes.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

from app.schemas.trade import TradeResponse


class DailySummary(BaseModel):
    """Daily summary statistics."""
    total_trades: int = Field(..., ge=0, description="Total trades for the day")
    winners: int = Field(..., ge=0, description="Winning trades")
    losers: int = Field(..., ge=0, description="Losing trades")
    winrate: Optional[Decimal] = Field(None, description="Win rate percentage")
    gross_pnl: Decimal = Field(..., description="Gross P&L")
    commissions: Decimal = Field(..., ge=0, description="Total commissions")
    volume: int = Field(..., ge=0, description="Total volume")
    profit_factor: Optional[Decimal] = Field(None, description="Profit factor")


class PnLProgressionPoint(BaseModel):
    """Single point in P&L progression chart."""
    time: datetime = Field(..., description="Timestamp")
    cumulative_pnl: Decimal = Field(..., description="Cumulative P&L at this time")


class DailyJournal(BaseModel):
    """Complete daily journal data."""
    date: date = Field(..., description="Date")
    net_pnl: Decimal = Field(..., description="Net P&L for the day")
    trades: List[TradeResponse] = Field(..., description="Trades for the day")
    summary: DailySummary = Field(..., description="Daily summary")
    notes: Optional[str] = Field(None, description="Daily notes")
    pnl_progression: List[PnLProgressionPoint] = Field(..., description="P&L progression throughout the day")


class DailyNoteCreate(BaseModel):
    """Schema for creating daily notes."""
    notes: str = Field(..., description="Daily notes content")


class DailyNoteUpdate(BaseModel):
    """Schema for updating daily notes."""
    notes: str = Field(..., description="Daily notes content")


class DailyNoteResponse(BaseModel):
    """Schema for daily notes response."""
    id: int
    date: date
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

