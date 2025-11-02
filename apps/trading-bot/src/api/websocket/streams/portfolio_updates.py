"""
Portfolio Update Stream
=======================

Background task that monitors portfolio positions and broadcasts updates to WebSocket clients.
Integrates with IBKR callbacks for real-time position updates.
"""

import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime

from ...websocket import get_websocket_manager
from ...websocket.manager import MessageType
from ....data.brokers.ibkr_client import IBKRClient, BrokerPosition
from ....api.routes.trading import get_ibkr_manager
from ....config.settings import settings

logger = logging.getLogger(__name__)


class PortfolioUpdateStream:
    """
    Streams real-time portfolio updates to WebSocket clients
    
    Monitors IBKR positions and P&L, broadcasting updates when changes occur.
    Can be driven by IBKR callbacks or polling.
    """
    
    def __init__(
        self,
        update_interval: Optional[int] = None,
        broadcast_only_on_change: bool = True
    ):
        """
        Initialize portfolio update stream
        
        Args:
            update_interval: Polling interval in seconds (uses config if None, only used if no IBKR callbacks)
            broadcast_only_on_change: Only broadcast if positions/P&L changed
        """
        self.update_interval = update_interval or settings.websocket.portfolio_update_interval
        self.broadcast_only_on_change = broadcast_only_on_change
        
        # Cache of last portfolio state
        self._last_positions: Dict[str, BrokerPosition] = {}
        self._last_total_pnl: float = 0.0
        
        # Background task (for polling mode)
        self._task: Optional[asyncio.Task] = None
        self._running = False
        
        # IBKR callback registration flag
        self._callbacks_registered = False
        
        logger.info(f"PortfolioUpdateStream initialized (interval: {self.update_interval}s)")
    
    def _register_ibkr_callbacks(self):
        """Register callbacks with IBKR manager for real-time updates"""
        ibkr_manager = get_ibkr_manager()
        if not ibkr_manager or not ibkr_manager.is_connected:
            return False
        
        client = ibkr_manager.client
        if not client:
            return False
        
        # Register position update callback
        async def on_position_update(positions: Dict[str, BrokerPosition]):
            """Handle IBKR position update callback"""
            await self._broadcast_portfolio_update(positions)
        
        # Register to IBKR callbacks (if supported)
        if hasattr(client, 'position_update_callbacks'):
            client.position_update_callbacks.append(on_position_update)
            self._callbacks_registered = True
            logger.info("Registered IBKR position update callbacks")
            return True
        
        return False
    
    async def _get_current_positions(self) -> Dict[str, BrokerPosition]:
        """Get current positions from IBKR"""
        ibkr_manager = get_ibkr_manager()
        if not ibkr_manager or not ibkr_manager.is_connected:
            return {}
        
        try:
            positions = await ibkr_manager.get_positions()
            return {pos.symbol: pos for pos in positions}
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {}
    
    async def _broadcast_portfolio_update(self, positions: Optional[Dict[str, BrokerPosition]] = None):
        """
        Broadcast portfolio update to subscribed clients
        
        Args:
            positions: Current positions dict (fetches if None)
        """
        if positions is None:
            positions = await self._get_current_positions()
        
        # Calculate total P&L
        total_pnl = sum(pos.unrealized_pnl for pos in positions.values())
        
        # Update portfolio P/L metrics
        try:
            from ....utils.metrics_business import update_portfolio_pnl, update_portfolio_value
            # Calculate portfolio total value (positions value + cash)
            # For now, we'll use total P&L as a proxy - can be enhanced with actual cash tracking
            portfolio_value = sum(
                pos.market_price * pos.quantity for pos in positions.values()
            )
            
            update_portfolio_pnl(
                total_pnl=total_pnl,
                daily_pnl=None,  # Would need daily tracking logic
                monthly_pnl=None  # Would need monthly tracking logic
            )
            update_portfolio_value(portfolio_value)
        except Exception as e:
            logger.debug(f"Error updating portfolio metrics: {e}")
        
        # Check if anything changed
        if self.broadcast_only_on_change:
            positions_changed = (
                set(positions.keys()) != set(self._last_positions.keys()) or
                total_pnl != self._last_total_pnl
            )
            
            # Check individual position changes
            if not positions_changed:
                for symbol, pos in positions.items():
                    last_pos = self._last_positions.get(symbol)
                    if not last_pos or (
                        pos.unrealized_pnl != last_pos.unrealized_pnl or
                        pos.quantity != last_pos.quantity
                    ):
                        positions_changed = True
                        break
            
            if not positions_changed:
                return  # No changes, skip broadcast
        
        # Update cache
        self._last_positions = positions.copy()
        self._last_total_pnl = total_pnl
        
        # Prepare portfolio update message
        positions_data = {}
        for symbol, pos in positions.items():
            positions_data[symbol] = {
                "symbol": pos.symbol,
                "quantity": pos.quantity,
                "average_price": pos.average_price,
                "market_price": pos.market_price,
                "unrealized_pnl": pos.unrealized_pnl,
                "unrealized_pnl_pct": pos.unrealized_pnl_pct,
            }
        
        message = {
            "type": MessageType.PORTFOLIO_UPDATE.value,
            "channel": "portfolio",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "positions": positions_data,
                "total_pnl": total_pnl,
                "position_count": len(positions)
            }
        }
        
        # Broadcast to portfolio channel
        manager = get_websocket_manager()
        # Manager.broadcast takes (channel, message)
        await manager.broadcast("portfolio", message)
        logger.debug(f"Broadcasted portfolio update: {len(positions)} positions, P&L: ${total_pnl:.2f}")
    
    async def start(self):
        """Start the portfolio update stream"""
        if self._running:
            logger.warning("PortfolioUpdateStream already running")
            return
        
        self._running = True
        
        # Try to register IBKR callbacks (event-driven mode)
        if self._register_ibkr_callbacks():
            # Using callbacks, no need for polling task
            logger.info("PortfolioUpdateStream started with IBKR callbacks (event-driven)")
            return
        
        # Fall back to polling mode
        async def stream_loop():
            """Background task loop for polling"""
            while self._running:
                try:
                    await self._broadcast_portfolio_update()
                    await asyncio.sleep(self.update_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in portfolio stream loop: {e}", exc_info=True)
                    await asyncio.sleep(self.update_interval)
        
        self._task = asyncio.create_task(stream_loop())
        logger.info("PortfolioUpdateStream started in polling mode")
    
    async def stop(self):
        """Stop the portfolio update stream"""
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        # Unregister callbacks (if registered)
        if self._callbacks_registered:
            ibkr_manager = get_ibkr_manager()
            if ibkr_manager and ibkr_manager.client:
                # Note: Callback removal would need to be implemented in IBKRClient
                pass
        
        logger.info("PortfolioUpdateStream stopped")
    
    def is_running(self) -> bool:
        """Check if stream is running"""
        return self._running

