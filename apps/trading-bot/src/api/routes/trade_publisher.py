"""
Trade Publisher
===============

Publishes trade execution events to WebSocket clients.
Integrates with IBKR client for trade notifications.
"""

import logging
from typing import Optional
from datetime import datetime

from ..websocket import get_websocket_manager
from ..websocket.manager import MessageType

logger = logging.getLogger(__name__)


class TradePublisher:
    """
    Publishes trade execution events to WebSocket clients
    
    Can be called directly when trades execute, or integrated
    with IBKR client callbacks.
    """
    
    def __init__(self):
        """Initialize trade publisher"""
        logger.info("TradePublisher initialized")
    
    async def publish_trade(
        self,
        symbol: str,
        side: str,  # "BUY" or "SELL"
        quantity: int,
        price: float,
        timestamp: Optional[datetime] = None
    ):
        """
        Publish a trade execution event
        
        Args:
            symbol: Stock symbol
            side: Trade side ("BUY" or "SELL")
            quantity: Number of shares
            price: Execution price
            timestamp: Trade timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Prepare trade message (matching dashboard format - root-level fields)
        message = {
            "type": MessageType.TRADE_EXECUTED.value,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "timestamp": timestamp.isoformat()
        }
        
        # Broadcast to trades channel
        manager = get_websocket_manager()
        # Manager.broadcast takes (channel, message)
        sent_count = await manager.broadcast("trades", message)
        
        if sent_count > 0:
            logger.info(
                f"Published trade: {side} {quantity} {symbol} @ ${price:.2f} "
                f"to {sent_count} clients"
            )


# Global trade publisher instance
_trade_publisher: Optional[TradePublisher] = None


def get_trade_publisher() -> TradePublisher:
    """Get global trade publisher instance (singleton)"""
    global _trade_publisher
    if _trade_publisher is None:
        _trade_publisher = TradePublisher()
    return _trade_publisher

