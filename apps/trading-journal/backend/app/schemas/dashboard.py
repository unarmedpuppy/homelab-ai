"""
Dashboard schemas for statistics and metrics.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, TYPE_CHECKING
from datetime import date as DateType
from decimal import Decimal

if TYPE_CHECKING:
    from datetime import date


class DashboardStats(BaseModel):
    """Complete dashboard statistics."""
    net_pnl: Decimal = Field(..., description="Net P&L")
    gross_pnl: Decimal = Field(..., description="Gross P&L")
    total_trades: int = Field(..., ge=0, description="Total number of trades")
    winners: int = Field(..., ge=0, description="Number of winning trades")
    losers: int = Field(..., ge=0, description="Number of losing trades")
    win_rate: Optional[Decimal] = Field(None, description="Win rate percentage")
    day_win_rate: Optional[Decimal] = Field(None, description="Day win rate percentage")
    profit_factor: Optional[Decimal] = Field(None, description="Profit factor")
    avg_win: Optional[Decimal] = Field(None, description="Average winning trade")
    avg_loss: Optional[Decimal] = Field(None, description="Average losing trade")
    max_drawdown: Optional[Decimal] = Field(None, description="Maximum drawdown")
    zella_score: Optional[Decimal] = Field(None, description="Zella score (composite metric)")


class CumulativePnLPoint(BaseModel):
    """Single point in cumulative P&L chart."""
    date: DateType = Field(..., description="Date")
    cumulative_pnl: Decimal = Field(..., description="Cumulative P&L up to this date")


class DailyPnLPoint(BaseModel):
    """Single point in daily P&L chart."""
    date: DateType = Field(..., description="Date")
    pnl: Decimal = Field(..., description="Daily P&L")
    trade_count: int = Field(..., ge=0, description="Number of trades on this date")


class DrawdownData(BaseModel):
    """Drawdown data with peak, trough, and recovery points."""
    date: DateType = Field(..., description="Date")
    peak: Decimal = Field(..., description="Peak value")
    trough: Decimal = Field(..., description="Trough value")
    drawdown: Decimal = Field(..., description="Drawdown amount")
    drawdown_pct: Decimal = Field(..., description="Drawdown percentage")
    recovery_date: Optional[DateType] = Field(None, description="Recovery date (if recovered)")


class RecentTrade(BaseModel):
    """Recent trade summary for dashboard."""
    id: int
    ticker: str
    trade_type: str
    side: str
    entry_time: date
    exit_time: Optional[date]
    net_pnl: Optional[Decimal]
    status: str

