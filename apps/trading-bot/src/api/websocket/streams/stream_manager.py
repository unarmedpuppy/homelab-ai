"""
Stream Manager
==============

Manages all WebSocket data streams, starting/stopping them together,
and coordinating their lifecycle with the application.
"""

import logging
from typing import Optional

from .price_updates import PriceUpdateStream
from .portfolio_updates import PortfolioUpdateStream
from .signal_broadcast import SignalBroadcastStream
from .market_data import MarketDataStream
from .options_flow import OptionsFlowStream
from ....config.settings import settings
from ....core.evaluation.evaluator import StrategyEvaluator

logger = logging.getLogger(__name__)


class StreamManager:
    """
    Manages all WebSocket data streams
    
    Provides unified interface to start/stop all streams and manages
    their lifecycle with the application.
    """
    
    def __init__(self):
        """Initialize stream manager"""
        self.price_stream: Optional[PriceUpdateStream] = None
        self.portfolio_stream: Optional[PortfolioUpdateStream] = None
        self.signal_stream: Optional[SignalBroadcastStream] = None
        self.market_data_stream: Optional[MarketDataStream] = None
        self.options_stream: Optional[OptionsFlowStream] = None
        
        self._initialized = False
        
        logger.info("StreamManager initialized")
    
    def initialize(self, evaluator: Optional[StrategyEvaluator] = None):
        """
        Initialize all streams
        
        Args:
            evaluator: Optional StrategyEvaluator for signal broadcasting
        """
        if self._initialized:
            logger.warning("StreamManager already initialized")
            return
        
        # Create stream instances
        self.price_stream = PriceUpdateStream()
        self.portfolio_stream = PortfolioUpdateStream()
        
        if evaluator:
            self.signal_stream = SignalBroadcastStream(evaluator)
        else:
            # Try to get evaluator if not provided
            try:
                from ....api.routes.strategies import get_evaluator
                evaluator = get_evaluator()
                if evaluator:
                    self.signal_stream = SignalBroadcastStream(evaluator)
            except Exception as e:
                logger.warning(f"Could not get StrategyEvaluator for signal stream: {e}")
        
        self.market_data_stream = MarketDataStream()
        self.options_stream = OptionsFlowStream()
        
        self._initialized = True
        logger.info("StreamManager initialized all streams")
    
    async def start_all(self):
        """Start all enabled streams"""
        if not self._initialized:
            self.initialize()
        
        if not settings.websocket.enabled:
            logger.info("WebSocket streaming disabled in config")
            return
        
        streams_started = 0
        streams_failed = []
        
        # Start price stream
        if self.price_stream:
            try:
                await self.price_stream.start()
                streams_started += 1
            except Exception as e:
                logger.error(f"Failed to start price stream: {e}", exc_info=True)
                streams_failed.append("price")
        
        # Start portfolio stream
        if self.portfolio_stream:
            try:
                await self.portfolio_stream.start()
                streams_started += 1
            except Exception as e:
                logger.error(f"Failed to start portfolio stream: {e}", exc_info=True)
                streams_failed.append("portfolio")
        
        # Start signal stream
        if self.signal_stream:
            try:
                await self.signal_stream.start()
                streams_started += 1
            except Exception as e:
                logger.error(f"Failed to start signal stream: {e}", exc_info=True)
                streams_failed.append("signal")
        
        # Start market data stream
        if self.market_data_stream:
            try:
                await self.market_data_stream.start()
                streams_started += 1
            except Exception as e:
                logger.error(f"Failed to start market data stream: {e}", exc_info=True)
                streams_failed.append("market_data")
        
        # Start options stream
        if self.options_stream:
            try:
                await self.options_stream.start()
                streams_started += 1
            except Exception as e:
                logger.error(f"Failed to start options flow stream: {e}", exc_info=True)
                streams_failed.append("options_flow")
        
        if streams_failed:
            logger.warning(f"Started {streams_started} streams, {len(streams_failed)} failed: {streams_failed}")
        else:
            logger.info(f"Started {streams_started} WebSocket data streams")
    
    async def stop_all(self):
        """Stop all streams"""
        streams_stopped = 0
        
        if self.price_stream and self.price_stream.is_running():
            await self.price_stream.stop()
            streams_stopped += 1
        
        if self.portfolio_stream and self.portfolio_stream.is_running():
            await self.portfolio_stream.stop()
            streams_stopped += 1
        
        if self.signal_stream and self.signal_stream.is_running():
            await self.signal_stream.stop()
            streams_stopped += 1
        
        if self.market_data_stream and self.market_data_stream.is_running():
            await self.market_data_stream.stop()
            streams_stopped += 1
        
        if self.options_stream and self.options_stream.is_running():
            await self.options_stream.stop()
            streams_stopped += 1
        
        logger.info(f"Stopped {streams_stopped} WebSocket data streams")
    
    def is_running(self) -> bool:
        """Check if any stream is running"""
        return (
            (self.price_stream and self.price_stream.is_running()) or
            (self.portfolio_stream and self.portfolio_stream.is_running()) or
            (self.signal_stream and self.signal_stream.is_running()) or
            (self.market_data_stream and self.market_data_stream.is_running()) or
            (self.options_stream and self.options_stream.is_running())
        )


# Global stream manager instance (singleton)
_stream_manager: Optional[StreamManager] = None


def get_stream_manager() -> StreamManager:
    """
    Get global stream manager instance (singleton)
    
    Returns:
        StreamManager instance
    """
    global _stream_manager
    if _stream_manager is None:
        _stream_manager = StreamManager()
        logger.info("Global StreamManager created")
    return _stream_manager

