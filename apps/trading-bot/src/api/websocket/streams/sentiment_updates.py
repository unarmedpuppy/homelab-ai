"""
Sentiment Update Stream
=======================

Background task that polls sentiment aggregator and broadcasts updates to WebSocket clients.
"""

import asyncio
import logging
from typing import Dict, Optional, Set, Any
from datetime import datetime, timezone

from ...websocket import get_websocket_manager
from ....config.settings import settings

logger = logging.getLogger(__name__)


class SentimentUpdateStream:
    """
    Streams aggregated sentiment updates to WebSocket clients

    Polls sentiment aggregator at configured intervals and broadcasts
    sentiment changes for subscribed symbols.
    """

    def __init__(
        self,
        update_interval: Optional[int] = None,
        broadcast_only_on_change: bool = True,
        min_change_threshold: float = 0.05  # 5% change to trigger broadcast
    ):
        """
        Initialize sentiment update stream

        Args:
            update_interval: Update interval in seconds (default: 60s)
            broadcast_only_on_change: Only broadcast if sentiment changed significantly
            min_change_threshold: Minimum change to trigger broadcast (0.0-1.0)
        """
        self.update_interval = update_interval or getattr(
            settings.websocket, 'sentiment_update_interval', 60
        )
        self.broadcast_only_on_change = broadcast_only_on_change
        self.min_change_threshold = min_change_threshold

        # Cache of last sentiment values: symbol → sentiment_data
        self._last_sentiment: Dict[str, Dict[str, Any]] = {}

        # Track subscribed symbols
        self._subscribed_symbols: Set[str] = set()

        # Sentiment aggregator (lazy loaded)
        self._aggregator = None

        # Background task
        self._task: Optional[asyncio.Task] = None
        self._running = False

        logger.info(f"SentimentUpdateStream initialized (interval: {self.update_interval}s)")

    def _get_aggregator(self):
        """Get sentiment aggregator (lazy load)"""
        if self._aggregator is None:
            try:
                from ....data.providers.sentiment.aggregator import SentimentAggregator
                self._aggregator = SentimentAggregator()
                logger.info("Sentiment aggregator initialized for stream")
            except Exception as e:
                logger.warning(f"Could not initialize sentiment aggregator: {e}")
        return self._aggregator

    def _update_subscribed_symbols(self) -> Set[str]:
        """Update set of subscribed symbols from WebSocket manager"""
        manager = get_websocket_manager()

        subscribed_symbols = set()

        # Check subscriptions (format: "sentiment:SYMBOL" or "sentiment_updates")
        with manager._subscriptions_lock:
            for channel in list(manager._subscriptions.keys()):
                if channel.startswith("sentiment:"):
                    symbol = channel.split(":", 1)[1].upper()
                    subscribed_symbols.add(symbol)
                elif channel == "sentiment_updates":
                    # Global subscription - need to get symbols from config or recent activity
                    # For now, add default watchlist symbols
                    default_symbols = getattr(settings, 'default_watchlist', ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA'])
                    subscribed_symbols.update(s.upper() for s in default_symbols)

        self._subscribed_symbols = subscribed_symbols
        return subscribed_symbols

    def _has_significant_change(self, symbol: str, new_sentiment: Dict[str, Any]) -> bool:
        """Check if sentiment changed significantly from last broadcast"""
        if not self.broadcast_only_on_change:
            return True

        last = self._last_sentiment.get(symbol)
        if not last:
            return True  # No previous data, always broadcast

        # Compare overall sentiment score
        last_score = last.get('overall_score', 0)
        new_score = new_sentiment.get('overall_score', 0)

        return abs(new_score - last_score) >= self.min_change_threshold

    async def _fetch_and_broadcast_sentiment(self):
        """Fetch sentiment for subscribed symbols and broadcast updates"""
        if not self._running:
            return

        aggregator = self._get_aggregator()
        if not aggregator:
            return

        # Update subscribed symbols
        subscribed_symbols = self._update_subscribed_symbols()

        if not subscribed_symbols:
            return

        try:
            manager = get_websocket_manager()
            broadcast_count = 0

            for symbol in subscribed_symbols:
                try:
                    # Get aggregated sentiment
                    sentiment = await aggregator.get_aggregated_sentiment(symbol)

                    if not sentiment:
                        continue

                    # Build sentiment data dict
                    sentiment_data = {
                        'symbol': symbol,
                        'overall_score': sentiment.overall_score,
                        'overall_level': sentiment.overall_level.value if sentiment.overall_level else 'neutral',
                        'confidence': sentiment.confidence,
                        'provider_count': sentiment.provider_count,
                        'total_mentions': sentiment.total_mentions,
                        'providers': {},
                    }

                    # Add provider details
                    if sentiment.provider_sentiments:
                        for provider, data in sentiment.provider_sentiments.items():
                            sentiment_data['providers'][provider] = {
                                'score': data.score if hasattr(data, 'score') else data.get('score', 0),
                                'level': data.level.value if hasattr(data, 'level') and data.level else 'neutral',
                                'mentions': data.mention_count if hasattr(data, 'mention_count') else data.get('mention_count', 0),
                            }

                    # Check if significant change
                    if not self._has_significant_change(symbol, sentiment_data):
                        continue

                    # Update cache
                    self._last_sentiment[symbol] = sentiment_data

                    # Prepare message
                    message = {
                        'type': 'sentiment_update',
                        'channel': 'sentiment_updates',
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'data': sentiment_data
                    }

                    # Broadcast to symbol-specific channel
                    await manager.broadcast(f"sentiment:{symbol}", message)

                    # Also broadcast to general sentiment_updates channel
                    await manager.broadcast("sentiment_updates", message)

                    broadcast_count += 1

                except Exception as e:
                    logger.debug(f"Error fetching sentiment for {symbol}: {e}")
                    continue

            if broadcast_count > 0:
                logger.debug(f"Broadcasted sentiment updates for {broadcast_count} symbols")

                # Record successful update for health monitoring
                try:
                    from .health import get_health_monitor
                    get_health_monitor().record_update("sentiment_updates")
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Error in sentiment update stream: {e}", exc_info=True)

            # Record error for health monitoring
            try:
                from .health import get_health_monitor
                get_health_monitor().record_error("sentiment_updates")
            except Exception:
                pass

    async def start(self):
        """Start the sentiment update stream"""
        if self._running:
            logger.warning("SentimentUpdateStream already running")
            return

        self._running = True

        # Register with health monitor
        try:
            from .health import get_health_monitor
            get_health_monitor().register_stream("sentiment_updates")
        except Exception:
            pass

        async def stream_loop():
            """Background task loop"""
            while self._running:
                try:
                    await self._fetch_and_broadcast_sentiment()
                    await asyncio.sleep(self.update_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in sentiment stream loop: {e}", exc_info=True)
                    await asyncio.sleep(self.update_interval)

        self._task = asyncio.create_task(stream_loop())
        logger.info("SentimentUpdateStream started")

    async def stop(self):
        """Stop the sentiment update stream"""
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("SentimentUpdateStream stopped")

    def is_running(self) -> bool:
        """Check if stream is running"""
        return self._running
