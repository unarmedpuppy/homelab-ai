"""
Charts schemas for price data and visualization.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict, field_serializer
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class PriceDataPoint(BaseModel):
    """Single OHLCV data point."""
    timestamp: datetime = Field(..., description="Timestamp")
    open: Decimal = Field(..., description="Open price")
    high: Decimal = Field(..., description="High price")
    low: Decimal = Field(..., description="Low price")
    close: Decimal = Field(..., description="Close price")
    volume: Optional[int] = Field(None, ge=0, description="Volume")
    
    @field_serializer('open', 'high', 'low', 'close')
    def serialize_decimal(self, value: Decimal) -> float:
        """Serialize Decimal to float for JSON."""
        return float(value) if value is not None else None
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
        }
    )


class PriceDataResponse(BaseModel):
    """Price data response with metadata."""
    ticker: str = Field(..., description="Ticker symbol")
    timeframe: str = Field(..., description="Timeframe (1m, 5m, 15m, 1h, 1d)")
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    data: List[PriceDataPoint] = Field(..., description="Price data points")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
        }
    )


class TradeOverlayData(BaseModel):
    """Trade overlay data for chart visualization."""
    trade_id: int = Field(..., description="Trade ID")
    ticker: str = Field(..., description="Ticker symbol")
    entry_time: datetime = Field(..., description="Entry timestamp")
    entry_price: Decimal = Field(..., description="Entry price")
    exit_time: Optional[datetime] = Field(None, description="Exit timestamp")
    exit_price: Optional[Decimal] = Field(None, description="Exit price")
    side: str = Field(..., description="Trade side (LONG or SHORT)")
    net_pnl: Optional[Decimal] = Field(None, description="Net P&L")
    
    model_config = ConfigDict(
        json_encoders={
            Decimal: lambda v: float(v) if v is not None else None,
        }
    )

