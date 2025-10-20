"""
Trading API Schemas
===================

Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

class TradeSide(str, Enum):
    """Trade side enumeration"""
    BUY = "BUY"
    SELL = "SELL"

class SignalType(str, Enum):
    """Signal type enumeration"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class TradeStatus(str, Enum):
    """Trade status enumeration"""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class PositionStatus(str, Enum):
    """Position status enumeration"""
    OPEN = "open"
    CLOSED = "closed"

class TradeRequest(BaseModel):
    """Trade execution request"""
    symbol: str = Field(..., min_length=1, max_length=10, description="Stock symbol")
    side: TradeSide = Field(..., description="Trade side")
    quantity: int = Field(..., gt=0, le=10000, description="Number of shares")
    price: Optional[Decimal] = Field(None, ge=0, description="Limit price (optional)")
    entry_threshold: Decimal = Field(0.005, ge=0, le=0.1, description="SMA entry threshold")
    take_profit: Decimal = Field(0.20, ge=0, le=1.0, description="Take profit percentage")
    stop_loss: Decimal = Field(0.10, ge=0, le=1.0, description="Stop loss percentage")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper().strip()
    
    @validator('take_profit', 'stop_loss')
    def validate_percentages(cls, v):
        if v <= 0 or v >= 1:
            raise ValueError('Percentages must be between 0 and 1')
        return v

class TradeResponse(BaseModel):
    """Trade execution response"""
    id: int
    symbol: str
    side: TradeSide
    quantity: int
    price: Decimal
    timestamp: datetime
    status: TradeStatus
    executed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PositionResponse(BaseModel):
    """Position information response"""
    id: int
    symbol: str
    quantity: int
    entry_price: Decimal
    current_price: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: Decimal
    entry_time: datetime
    
    class Config:
        from_attributes = True

class SignalResponse(BaseModel):
    """Trading signal response"""
    signal_type: SignalType
    symbol: str
    price: Decimal
    quantity: int
    confidence: float = Field(..., ge=0, le=1, description="Signal confidence (0-1)")
    timestamp: datetime
    metadata: Dict[str, Any]

class StrategyConfigRequest(BaseModel):
    """Strategy configuration request"""
    strategy_type: str = Field(..., description="Strategy type (e.g., 'sma')")
    symbol: str = Field(..., description="Symbol to configure")
    config_data: Dict[str, Any] = Field(..., description="Strategy configuration")

class StrategyConfigResponse(BaseModel):
    """Strategy configuration response"""
    id: int
    strategy_type: str
    symbol: str
    config_data: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class MarketDataResponse(BaseModel):
    """Market data response"""
    symbol: str
    price: Decimal
    change: Decimal
    change_pct: Decimal
    volume: int
    timestamp: datetime

class PortfolioSummary(BaseModel):
    """Portfolio summary response"""
    total_value: Decimal
    cash_balance: Decimal
    total_pnl: Decimal
    total_pnl_pct: Decimal
    open_positions: int
    total_trades: int
    win_rate: Decimal
    avg_trade_pnl: Decimal

class RiskMetrics(BaseModel):
    """Risk metrics response"""
    max_drawdown: Decimal
    sharpe_ratio: Decimal
    sortino_ratio: Decimal
    calmar_ratio: Decimal
    var_95: Decimal  # Value at Risk 95%
    expected_shortfall: Decimal
    beta: Decimal
    volatility: Decimal
