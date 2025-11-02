"""
Market Data Streaming
=====================

Background task that streams OHLCV (candle/bar) data to WebSocket clients.
"""

import asyncio
import logging
from typing import Dict, Optional, Set
from datetime import datetime, timedelta

from ...websocket import get_websocket_manager
from ...websocket.manager import MessageType
from ....data.providers.market_data import DataProviderManager, OHLCVData
from ....api.routes.market_data import get_data_manager
from ....config.settings import settings

logger = logging.getLogger(__name__)


class MarketDataStream:
    """
    Streams OHLCV (candle/bar) data to WebSocket clients
    
    Polls data providers at configured intervals and broadcasts
    new bars/candles to clients subscribed to specific symbols/timeframes.
    """
    
    def __init__(
        self,
        data_manager: Optional[DataProviderManager] = None,
        update_interval: Optional[int] = None
    ):
        """
        Initialize market data stream
        
        Args:
            data_manager: DataProviderManager instance (uses global if None)
            update_interval: Update interval in seconds (uses config if None)
        """
        self.data_manager = data_manager or get_data_manager()
        self.update_interval = update_interval or settings.websocket.market_data_interval
        
        # Cache of last bars: (symbol, timeframe) → OHLCVData
        self._last_bars: Dict[tuple, OHLCVData] = {}
        
        # Track subscribed symbols/timeframes
        self._subscribed_pairs: Set[tuple] = set()
        
        # Background task
        self._task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info(f"MarketDataStream initialized (interval: {self.update_interval}s)")
    
    def _update_subscribed_pairs(self):
        """Update set of subscribed symbol/timeframe pairs from WebSocket manager"""
        manager = get_websocket_manager()
        
        subscribed_pairs = set()
        
        # Check subscriptions (format: "market_data:SYMBOL:TIMEFRAME")
        manager._subscriptions_lock.acquire()
        try:
            for channel in list(manager._subscriptions.keys()):
                if channel.startswith("market_data:"):
                    parts = channel.split(":")
                    if len(parts) >= 3:
                        symbol = parts[1].upper()
                        timeframe = parts[2]
                        subscribed_pairs.add((symbol, timeframe))
        finally:
            manager._subscriptions_lock.release()
        
        self._subscribed_pairs = subscribed_pairs
        return subscribed_pairs
    
    async def _fetch_and_broadcast_bars(self):
        """Fetch latest bars for subscribed symbols/timeframes and broadcast"""
        if not self._running:
            return
        
        # Update subscribed pairs
        subscribed_pairs = self._update_subscribed_pairs()
        
        if not subscribed_pairs:
            return
        
        try:
            # Get current time
            now = datetime.now()
            # Fetch last few bars (to detect new bar)
            start_date = now - timedelta(hours=1)
            
            # Group by symbol (to fetch once per symbol)
            symbols_by_timeframe: Dict[str, Set[str]] = {}
            for symbol, timeframe in subscribed_pairs:
                if timeframe not in symbols_by_timeframe:
                    symbols_by_timeframe[timeframe] = set()
                symbols_by_timeframe[timeframe].add(symbol)
            
            # Fetch and broadcast for each timeframe
            for timeframe, symbols in symbols_by_timeframe.items():
                for symbol in symbols:
                    try:
                        # Fetch historical data (last hour)
                        bars = await self.data_manager.get_historical_data(
                            symbol, start_date, now, interval=timeframe
                        )
                        
                        if not bars:
                            continue
                        
                        # Get latest bar
                        latest_bar = bars[-1]
                        pair_key = (symbol, timeframe)
                        
                        # Check if this is a new bar (different timestamp)
                        last_bar = self._last_bars.get(pair_key)
                        
                        if last_bar and last_bar.timestamp == latest_bar.timestamp:
                            # Same bar, no update needed
                            continue
                        
                        # Store latest bar
                        self._last_bars[pair_key] = latest_bar
                        
                        # Prepare market data message
                        channel = f"market_data:{symbol}:{timeframe}"
                        message = {
                            "type": MessageType.MARKET_DATA.value,
                            "channel": "market_data",
                            "timestamp": latest_bar.timestamp.isoformat(),
                            "data": {
                                "symbol": symbol,
                                "timeframe": timeframe,
                                "open": latest_bar.open,
                                "high": latest_bar.high,
                                "low": latest_bar.low,
                                "close": latest_bar.close,
                                "volume": latest_bar.volume,
                            }
                        }
                        
                        # Broadcast to this symbol/timeframe channel
                        await get_websocket_manager().broadcast(channel, message)
                    
                    except Exception as e:
                        logger.debug(f"Error fetching market data for {symbol} {timeframe}: {e}")
                        continue
            
        except Exception as e:
            logger.error(f"Error in market data stream: {e}", exc_info=True)
    
    async def start(self):
        """Start the market data stream"""
        if self._running:
            logger.warning("MarketDataStream already running")
            return
        
        self._running = True
        
        async def stream_loop():
            """Background task loop"""
            while self._running:
                try:
                    await self._fetch_and_broadcast_bars()
                    await asyncio.sleep(self.update_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in market data stream loop: {e}", exc_info=True)
                    await asyncio.sleep(self.update_interval)
        
        self._task = asyncio.create_task(stream_loop())
        logger.info("MarketDataStream started")
    
    async def stop(self):
        """Stop the market data stream"""
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("MarketDataStream stopped")
    
    def is_running(self) -> bool:
        """Check if stream is running"""
        return self._running

