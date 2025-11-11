"""
AI Agent Helper schemas for API requests and responses.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal

from app.schemas.trade import TradeCreate, TradeResponse


class ParseTradeRequest(BaseModel):
    """Request schema for parsing a trade from natural language."""
    description: str = Field(..., description="Natural language description of the trade")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Optional raw structured data to supplement parsing")
    
    model_config = ConfigDict(from_attributes=True)


class ParseTradeResponse(BaseModel):
    """Response schema for parsed trade data."""
    parsed_trade: TradeCreate = Field(..., description="Parsed trade data ready for creation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0)")
    extracted_fields: Dict[str, Any] = Field(default_factory=dict, description="Fields that were successfully extracted")
    missing_fields: List[str] = Field(default_factory=list, description="Required fields that could not be extracted")
    warnings: List[str] = Field(default_factory=list, description="Warnings about the parsed data")
    
    model_config = ConfigDict(from_attributes=True)


class BatchCreateRequest(BaseModel):
    """Request schema for batch trade creation."""
    trades: List[ParseTradeRequest] = Field(..., description="List of trade descriptions or raw data to create")
    
    model_config = ConfigDict(from_attributes=True)


class BatchCreateResponse(BaseModel):
    """Response schema for batch trade creation."""
    created_trades: List[TradeResponse] = Field(default_factory=list, description="Successfully created trades")
    failed_trades: List[Dict[str, Any]] = Field(default_factory=list, description="Trades that failed to create with error details")
    total_requested: int = Field(0, description="Total number of trades requested")
    total_created: int = Field(0, description="Total number of trades successfully created")
    total_failed: int = Field(0, description="Total number of trades that failed")
    
    model_config = ConfigDict(from_attributes=True)


class TradeSuggestion(BaseModel):
    """Suggested trade parameters based on historical data."""
    ticker: str = Field(..., description="Ticker symbol")
    suggested_entry_price: Optional[Decimal] = Field(None, description="Suggested entry price based on recent trades")
    suggested_quantity: Optional[Decimal] = Field(None, description="Suggested quantity based on historical patterns")
    suggested_trade_type: Optional[str] = Field(None, description="Most common trade type for this ticker")
    suggested_side: Optional[str] = Field(None, description="Most common side (LONG/SHORT) for this ticker")
    suggested_playbook: Optional[str] = Field(None, description="Most common playbook/strategy for this ticker")
    avg_win_rate: Optional[Decimal] = Field(None, description="Average win rate for this ticker")
    avg_net_pnl: Optional[Decimal] = Field(None, description="Average net P&L for this ticker")
    total_trades: int = Field(0, description="Total number of historical trades for this ticker")
    last_trade_date: Optional[date] = Field(None, description="Date of the most recent trade for this ticker")
    notes: List[str] = Field(default_factory=list, description="Additional notes and insights")
    
    model_config = ConfigDict(from_attributes=True)

