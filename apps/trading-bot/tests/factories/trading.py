"""
Trading Data Factory Functions
===============================

Factory functions for creating trading signals, positions, and orders for testing.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from src.core.strategy.base import TradingSignal, SignalType, Position, ExitReason
from src.core.strategy.levels import PriceLevel, LevelType
from src.data.brokers.ibkr_client import (
    BrokerOrder,
    BrokerPosition,
    OrderSide,
    OrderType,
    OrderStatus
)
from unittest.mock import Mock


def create_trading_signal(
    signal_type: SignalType = SignalType.BUY,
    symbol: str = "SPY",
    price: float = 100.0,
    quantity: int = 10,
    confidence: float = 0.75,
    entry_level: Optional[PriceLevel] = None,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
    timestamp: Optional[datetime] = None
) -> TradingSignal:
    """
    Create a TradingSignal for testing
    
    Args:
        signal_type: Signal type (BUY, SELL, HOLD)
        symbol: Trading symbol
        price: Signal price
        quantity: Signal quantity
        confidence: Signal confidence (0-1)
        entry_level: Entry price level
        stop_loss: Stop loss price
        take_profit: Take profit price
        metadata: Additional metadata
        timestamp: Signal timestamp (defaults to now)
    
    Returns:
        TradingSignal instance
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    if metadata is None:
        metadata = {}
    
    return TradingSignal(
        signal_type=signal_type,
        symbol=symbol,
        price=price,
        quantity=quantity,
        timestamp=timestamp,
        confidence=confidence,
        metadata=metadata,
        entry_level=entry_level,
        stop_loss=stop_loss,
        take_profit=take_profit
    )


def create_position(
    symbol: str = "SPY",
    quantity: int = 10,
    entry_price: float = 100.0,
    current_price: float = 102.0,
    entry_time: Optional[datetime] = None,
    entry_level: Optional[PriceLevel] = None,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None
) -> Position:
    """
    Create a Position for testing
    
    Args:
        symbol: Trading symbol
        quantity: Position quantity
        entry_price: Entry price
        current_price: Current market price
        entry_time: Entry timestamp (defaults to now)
        entry_level: Entry price level
        stop_loss: Stop loss price
        take_profit: Take profit price
    
    Returns:
        Position instance
    """
    if entry_time is None:
        entry_time = datetime.now()
    
    # Calculate unrealized P&L
    price_diff = current_price - entry_price
    unrealized_pnl = price_diff * quantity
    unrealized_pnl_pct = price_diff / entry_price
    
    return Position(
        symbol=symbol,
        quantity=quantity,
        entry_price=entry_price,
        entry_time=entry_time,
        current_price=current_price,
        unrealized_pnl=unrealized_pnl,
        unrealized_pnl_pct=unrealized_pnl_pct,
        entry_level=entry_level,
        stop_loss=stop_loss,
        take_profit=take_profit
    )


def create_broker_order(
    order_id: int = 1,
    symbol: str = "SPY",
    side: OrderSide = OrderSide.BUY,
    quantity: int = 10,
    order_type: OrderType = OrderType.MARKET,
    price: Optional[float] = None,
    status: OrderStatus = OrderStatus.FILLED,
    filled_quantity: Optional[int] = None,
    average_fill_price: Optional[float] = None,
    timestamp: Optional[datetime] = None
) -> BrokerOrder:
    """
    Create a BrokerOrder for testing
    
    Args:
        order_id: Order ID
        symbol: Trading symbol
        side: Order side (BUY/SELL)
        quantity: Order quantity
        order_type: Order type (MARKET/LIMIT/STOP)
        price: Limit/stop price (if applicable)
        status: Order status
        filled_quantity: Filled quantity (defaults to quantity if filled)
        average_fill_price: Average fill price
        timestamp: Order timestamp (defaults to now)
    
    Returns:
        BrokerOrder instance
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    if filled_quantity is None:
        filled_quantity = quantity if status == OrderStatus.FILLED else 0
    
    if average_fill_price is None:
        average_fill_price = price if price is not None else 100.0
    
    return BrokerOrder(
        order_id=order_id,
        symbol=symbol,
        side=side,
        quantity=quantity,
        order_type=order_type,
        price=price,
        status=status,
        filled_quantity=filled_quantity,
        average_fill_price=average_fill_price,
        timestamp=timestamp
    )


def create_broker_position(
    symbol: str = "SPY",
    quantity: int = 10,
    average_price: float = 100.0,
    market_price: float = 102.0,
    contract: Optional[Any] = None
) -> BrokerPosition:
    """
    Create a BrokerPosition for testing
    
    Args:
        symbol: Trading symbol
        quantity: Position quantity
        average_price: Average entry price
        market_price: Current market price
        contract: IBKR contract object (creates mock if None)
    
    Returns:
        BrokerPosition instance
    """
    if contract is None:
        contract = Mock()
        contract.symbol = symbol
    
    # Calculate unrealized P&L
    price_diff = market_price - average_price
    unrealized_pnl = price_diff * quantity
    unrealized_pnl_pct = price_diff / average_price if average_price > 0 else 0.0
    
    return BrokerPosition(
        symbol=symbol,
        quantity=quantity,
        average_price=average_price,
        market_price=market_price,
        unrealized_pnl=unrealized_pnl,
        unrealized_pnl_pct=unrealized_pnl_pct,
        contract=contract
    )

