"""
Signal Broadcasting Stream
==========================

Broadcasts trading signals from StrategyEvaluator to WebSocket clients in real-time.
Integrates with StrategyEvaluator signal callbacks.
"""

import logging
from typing import Optional, Callable

from ...websocket import get_websocket_manager
from ...websocket.manager import MessageType
from ....core.strategy.base import TradingSignal, SignalType
from ....core.evaluation.evaluator import StrategyEvaluator

logger = logging.getLogger(__name__)


class SignalBroadcastStream:
    """
    Broadcasts trading signals to WebSocket clients
    
    Registers as a callback with StrategyEvaluator and immediately
    broadcasts signals when they're generated.
    """
    
    def __init__(self, evaluator: Optional[StrategyEvaluator] = None):
        """
        Initialize signal broadcast stream
        
        Args:
            evaluator: StrategyEvaluator instance (will get global if None)
        """
        self.evaluator = evaluator
        self._callback_registered = False
        self._callback_func: Optional[Callable] = None
        
        logger.info("SignalBroadcastStream initialized")
    
    def _register_callback(self):
        """Register signal callback with StrategyEvaluator"""
        if not self.evaluator:
            logger.warning("No StrategyEvaluator provided, cannot register callbacks")
            return False
        
        if self._callback_registered:
            return True
        
        def on_signal(signal: TradingSignal):
            """Handle signal callback from StrategyEvaluator (sync wrapper)"""
            # StrategyEvaluator calls callbacks synchronously
            # We need to schedule the async broadcast in the event loop
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                # Loop is running, create task
                asyncio.create_task(self._broadcast_signal(signal))
            except RuntimeError:
                # No running loop - try to get/create one
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self._broadcast_signal(signal))
                    else:
                        # Schedule on loop
                        asyncio.run_coroutine_threadsafe(
                            self._broadcast_signal(signal), loop
                        )
                except RuntimeError:
                    # Last resort: log warning
                    logger.warning(
                        f"Could not broadcast signal immediately for {signal.symbol} - "
                        f"no async context available. Signal: {signal.signal_type.value}"
                    )
        
        # Register callback
        self.evaluator.signal_callbacks.append(on_signal)
        self._callback_func = on_signal
        self._callback_registered = True
        
        logger.info("Registered signal callback with StrategyEvaluator")
        return True
    
    async def _broadcast_signal(self, signal: TradingSignal):
        """
        Broadcast signal to WebSocket clients
        
        Args:
            signal: TradingSignal to broadcast
        """
        # Only broadcast non-HOLD signals
        if signal.signal_type == SignalType.HOLD:
            return
        
        # Prepare signal message (matching dashboard format - root-level fields)
        message = {
            "type": MessageType.SIGNAL.value,
            "signal_type": signal.signal_type.value,
            "symbol": signal.symbol,
            "price": signal.price,
            "quantity": signal.quantity,
            "confidence": signal.confidence,
            "timestamp": signal.timestamp.isoformat()
        }
        
        # Broadcast to signals channel
        manager = get_websocket_manager()
        # Manager.broadcast takes (channel, message)
        sent_count = await manager.broadcast("signals", message)
        
        if sent_count > 0:
            logger.info(
                f"Broadcasted signal: {signal.signal_type.value} {signal.symbol} "
                f"@ ${signal.price:.2f} (confidence: {signal.confidence:.2%}) "
                f"to {sent_count} clients"
            )
            
            # Record successful update for health monitoring
            try:
                from .health import get_health_monitor
                get_health_monitor().record_update("signals")
            except Exception:
                pass
    
    async def start(self):
        """Start the signal broadcast stream"""
        if self._callback_registered:
            logger.warning("SignalBroadcastStream already started")
            return
        
        self._register_callback()
        logger.info("SignalBroadcastStream started")
    
    async def stop(self):
        """Stop the signal broadcast stream"""
        if not self._callback_registered or not self.evaluator:
            return
        
        # Remove callback
        if self._callback_func and self._callback_func in self.evaluator.signal_callbacks:
            self.evaluator.signal_callbacks.remove(self._callback_func)
        
        self._callback_registered = False
        logger.info("SignalBroadcastStream stopped")
    
    def is_running(self) -> bool:
        """Check if stream is running"""
        return self._callback_registered

