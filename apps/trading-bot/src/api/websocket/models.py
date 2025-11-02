"""
WebSocket Message Models
========================

Pydantic models for WebSocket messages matching dashboard expectations.
All message formats must match exactly what dashboard.html expects.
"""

from pydantic import BaseModel
from typing import Dict, Optional, Literal
from datetime import datetime


class PriceData(BaseModel):
    """Price data for a single symbol"""
    price: float
    change: float
    change_pct: float


class PriceUpdateMessage(BaseModel):
    """Price update message (must match dashboard format)"""
    type: Literal["price_update"] = "price_update"
    symbols: Dict[str, PriceData]


class SignalMessage(BaseModel):
    """Trading signal message (must match dashboard format)"""
    type: Literal["signal"] = "signal"
    signal_type: str  # "BUY", "SELL", "HOLD"
    symbol: str
    price: float
    confidence: float
    timestamp: datetime


class TradeMessage(BaseModel):
    """Trade execution message (must match dashboard format)"""
    type: Literal["trade_executed"] = "trade_executed"
    symbol: str
    side: str  # "BUY", "SELL"
    quantity: int
    price: float
    timestamp: datetime


class PongMessage(BaseModel):
    """Pong response for ping/pong keepalive"""
    type: Literal["pong"] = "pong"


class PingMessage(BaseModel):
    """Ping message from client"""
    type: Literal["ping"] = "ping"


class ErrorMessage(BaseModel):
    """Error message to client"""
    type: Literal["error"] = "error"
    error: str
    timestamp: datetime = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now()
        super().__init__(**data)

