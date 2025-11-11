"""
Analytics schemas for API requests and responses.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


class PerformanceMetrics(BaseModel):
    """Performance metrics response."""
    sharpe_ratio: Optional[Decimal] = Field(None, description="Sharpe ratio")
    sortino_ratio: Optional[Decimal] = Field(None, description="Sortino ratio")
    max_drawdown: Optional[Decimal] = Field(None, description="Maximum drawdown percentage")
    avg_drawdown: Optional[Decimal] = Field(None, description="Average drawdown percentage")
    win_rate: Optional[Decimal] = Field(None, description="Win rate percentage")
    profit_factor: Optional[Decimal] = Field(None, description="Profit factor")
    avg_win: Optional[Decimal] = Field(None, description="Average winning trade")
    avg_loss: Optional[Decimal] = Field(None, description="Average losing trade")
    best_trade: Optional[Decimal] = Field(None, description="Best trade P&L")
    worst_trade: Optional[Decimal] = Field(None, description="Worst trade P&L")
    total_trades: int = Field(0, description="Total number of trades")
    as_of: datetime = Field(default_factory=datetime.now, description="Timestamp of calculation")
    
    model_config = ConfigDict(from_attributes=True)


class TickerPerformance(BaseModel):
    """Performance breakdown by ticker."""
    ticker: str = Field(..., description="Ticker symbol")
    total_trades: int = Field(0, description="Total number of trades")
    net_pnl: Decimal = Field(Decimal("0"), description="Net P&L")
    gross_pnl: Decimal = Field(Decimal("0"), description="Gross P&L")
    win_rate: Optional[Decimal] = Field(None, description="Win rate percentage")
    profit_factor: Optional[Decimal] = Field(None, description="Profit factor")
    avg_win: Optional[Decimal] = Field(None, description="Average winning trade")
    avg_loss: Optional[Decimal] = Field(None, description="Average losing trade")
    winners: int = Field(0, description="Number of winning trades")
    losers: int = Field(0, description="Number of losing trades")
    
    model_config = ConfigDict(from_attributes=True)


class TickerPerformanceResponse(BaseModel):
    """Response for ticker performance breakdown."""
    date_from: Optional[date] = Field(None, description="Start date filter")
    date_to: Optional[date] = Field(None, description="End date filter")
    tickers: List[TickerPerformance] = Field(default_factory=list, description="Performance by ticker")
    as_of: datetime = Field(default_factory=datetime.now, description="Timestamp of calculation")
    
    model_config = ConfigDict(from_attributes=True)


class TypePerformance(BaseModel):
    """Performance breakdown by trade type."""
    trade_type: str = Field(..., description="Trade type (STOCK, OPTION, etc.)")
    total_trades: int = Field(0, description="Total number of trades")
    net_pnl: Decimal = Field(Decimal("0"), description="Net P&L")
    gross_pnl: Decimal = Field(Decimal("0"), description="Gross P&L")
    win_rate: Optional[Decimal] = Field(None, description="Win rate percentage")
    profit_factor: Optional[Decimal] = Field(None, description="Profit factor")
    avg_win: Optional[Decimal] = Field(None, description="Average winning trade")
    avg_loss: Optional[Decimal] = Field(None, description="Average losing trade")
    winners: int = Field(0, description="Number of winning trades")
    losers: int = Field(0, description="Number of losing trades")
    
    model_config = ConfigDict(from_attributes=True)


class TypePerformanceResponse(BaseModel):
    """Response for trade type performance breakdown."""
    date_from: Optional[date] = Field(None, description="Start date filter")
    date_to: Optional[date] = Field(None, description="End date filter")
    types: List[TypePerformance] = Field(default_factory=list, description="Performance by trade type")
    as_of: datetime = Field(default_factory=datetime.now, description="Timestamp of calculation")
    
    model_config = ConfigDict(from_attributes=True)


class PlaybookPerformance(BaseModel):
    """Performance breakdown by playbook/strategy."""
    playbook: str = Field(..., description="Playbook/strategy name")
    total_trades: int = Field(0, description="Total number of trades")
    net_pnl: Decimal = Field(Decimal("0"), description="Net P&L")
    gross_pnl: Decimal = Field(Decimal("0"), description="Gross P&L")
    win_rate: Optional[Decimal] = Field(None, description="Win rate percentage")
    profit_factor: Optional[Decimal] = Field(None, description="Profit factor")
    avg_win: Optional[Decimal] = Field(None, description="Average winning trade")
    avg_loss: Optional[Decimal] = Field(None, description="Average losing trade")
    winners: int = Field(0, description="Number of winning trades")
    losers: int = Field(0, description="Number of losing trades")
    
    model_config = ConfigDict(from_attributes=True)


class PlaybookPerformanceResponse(BaseModel):
    """Response for playbook performance breakdown."""
    date_from: Optional[date] = Field(None, description="Start date filter")
    date_to: Optional[date] = Field(None, description="End date filter")
    playbooks: List[PlaybookPerformance] = Field(default_factory=list, description="Performance by playbook")
    as_of: datetime = Field(default_factory=datetime.now, description="Timestamp of calculation")
    
    model_config = ConfigDict(from_attributes=True)

