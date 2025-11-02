"""
Price Update Stream
===================

Background task that polls for price updates and broadcasts to subscribed WebSocket clients.
"""

import asyncio
import logging
from typing import Dict, Set, Optional
from datetime import datetime, timezone

from ...websocket import get_websocket_manager
from ...websocket.manager import MessageType
from ....data.providers.market_data import DataProviderManager, MarketData
from ....api.routes.market_data import get_data_manager
from ....config.settings import settings

logger = logging.getLogger(__name__)


class PriceUpdateStream:
    """
    Streams real-time price updates to WebSocket clients
    
    Polls data providers at configured intervals and broadcasts
    price changes to clients subscribed to specific symbols.
    """
    
    def __init__(
        self,
        data_manager: Optional[DataProviderManager] = None,
        update_interval: Optional[int] = None,
        broadcast_only_on_change: bool = True
    ):
        """
        Initialize price update stream
        
        Args:
            data_manager: DataProviderManager instance (uses global if None)
            update_interval: Update interval in seconds (uses config if None)
            broadcast_only_on_change: Only broadcast if price changed
        """
        self.data_manager = data_manager or get_data_manager()
        self.update_interval = update_interval or settings.websocket.price_update_interval
        self.broadcast_only_on_change = broadcast_only_on_change
        
        # Cache of last known prices: symbol → MarketData
        self._last_prices: Dict[str, MarketData] = {}
        
        # Track which symbols are subscribed (for efficiency)
        self._subscribed_symbols: Set[str] = set()
        
        # Background task
        self._task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info(f"PriceUpdateStream initialized (interval: {self.update_interval}s)")
    
    def _update_subscribed_symbols(self):
        """Update set of subscribed symbols from WebSocket manager"""
        manager = get_websocket_manager()
        
        # Get all price subscriptions
        subscribed_symbols = set()
        
        # Check subscriptions (format: "price:SYMBOL")
        # We need to get all subscriptions that start with "price:"
        with manager._subscriptions_lock:
            for channel in list(manager._subscriptions.keys()):
                if channel.startswith("price:"):
                    symbol = channel.split(":", 1)[1]
                    subscribed_symbols.add(symbol)
        
        self._subscribed_symbols = subscribed_symbols
        return subscribed_symbols
    
    async def _fetch_and_broadcast_prices(self):
        """Fetch prices for subscribed symbols and broadcast updates"""
        if not self._running:
            return
        
        # Update subscribed symbols list
        subscribed_symbols = self._update_subscribed_symbols()
        
        if not subscribed_symbols:
            # No subscriptions, skip fetch
            return
        
        try:
            # Fetch quotes for all subscribed symbols
            symbols_list = list(subscribed_symbols)
            quotes = await self.data_manager.get_multiple_quotes(symbols_list)
            
            # Prepare batch update (dashboard expects all symbols in one message)
            symbols_data = {}
            has_changes = False
            
            for symbol, market_data in quotes.items():
                symbol_upper = symbol.upper()
                
                # Check if price changed
                last_price = self._last_prices.get(symbol_upper)
                
                if self.broadcast_only_on_change and last_price:
                    # Only broadcast if price changed
                    if last_price.price == market_data.price:
                        continue  # Price unchanged, skip this symbol
                
                # Store latest price
                self._last_prices[symbol_upper] = market_data
                has_changes = True
                
                # Add symbol data (matching dashboard format)
                symbols_data[symbol_upper] = {
                    "price": market_data.price,
                    "change": market_data.change,
                    "change_pct": market_data.change_pct,
                    "volume": market_data.volume,
                    "high": market_data.high,
                    "low": market_data.low,
                    "open": market_data.open,
                    "close": market_data.close,
                }
            
            # Broadcast batch update if we have changes
            if has_changes and symbols_data:
                # Dashboard expects format: { type: "price_update", symbols: { SYMBOL: { price, change, ... } } }
                message = {
                    "type": MessageType.PRICE_UPDATE.value,
                    "symbols": symbols_data,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                # Broadcast to price_updates topic (MVP: all clients auto-subscribed)
                # Dashboard expects batched updates for all symbols
                manager = get_websocket_manager()
                # Manager.broadcast takes (channel, message)
                await manager.broadcast("price_updates", message)
                
                logger.debug(f"Broadcasted price updates for {len(symbols_data)} symbols")
                
                # Record successful update for health monitoring
                from .health import get_health_monitor
                get_health_monitor().record_update("price_updates")
        
        except Exception as e:
            logger.error(f"Error in price update stream: {e}", exc_info=True)
            
            # Record error for health monitoring
            try:
                from .health import get_health_monitor
                get_health_monitor().record_error("price_updates")
            except Exception:
                pass
            
            # Continue running despite errors
    
    async def start(self):
        """Start the price update stream"""
        if self._running:
            logger.warning("PriceUpdateStream already running")
            return
        
        self._running = True
        
        # Register with health monitor
        try:
            from .health import get_health_monitor
            get_health_monitor().register_stream("price_updates")
        except Exception:
            pass
        
        async def stream_loop():
            """Background task loop"""
            while self._running:
                try:
                    await self._fetch_and_broadcast_prices()
                    await asyncio.sleep(self.update_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in price stream loop: {e}", exc_info=True)
                    await asyncio.sleep(self.update_interval)
        
        self._task = asyncio.create_task(stream_loop())
        logger.info("PriceUpdateStream started")
    
    async def stop(self):
        """Stop the price update stream"""
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("PriceUpdateStream stopped")
    
    def is_running(self) -> bool:
        """Check if stream is running"""
        return self._running

