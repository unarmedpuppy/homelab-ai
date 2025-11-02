"""
Options Flow Streaming
======================

Background task that polls for options flow updates and broadcasts to WebSocket clients.
"""

import asyncio
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta

from ...websocket import get_websocket_manager
from ...websocket.manager import MessageType
from ....data.providers.unusual_whales import UnusualWhalesClient
from ....api.routes.options_flow import get_options_client  # type: ignore
from ....config.settings import settings

logger = logging.getLogger(__name__)


class OptionsFlowStream:
    """
    Streams options flow updates to WebSocket clients
    
    Polls Unusual Whales API at configured intervals and broadcasts
    significant options flow activity (sweeps, blocks, unusual activity).
    """
    
    def __init__(
        self,
        options_client: Optional[UnusualWhalesClient] = None,
        update_interval: Optional[int] = None,
        min_flow_threshold: float = 50000.0  # Minimum premium to broadcast
    ):
        """
        Initialize options flow stream
        
        Args:
            options_client: UnusualWhalesClient instance (uses global if None)
            update_interval: Update interval in seconds (uses config if None)
            min_flow_threshold: Minimum premium threshold to broadcast flow
        """
        self.options_client = options_client or get_options_client()
        self.update_interval = update_interval or settings.websocket.options_flow_interval
        self.min_flow_threshold = min_flow_threshold
        
        # Track last seen flow IDs to avoid duplicates
        self._last_flow_ids: set = set()
        
        # Background task
        self._task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info(
            f"OptionsFlowStream initialized "
            f"(interval: {self.update_interval}s, threshold: ${min_flow_threshold:,.0f})"
        )
    
    async def _fetch_and_broadcast_flow(self):
        """Fetch options flow and broadcast significant activity"""
        if not self._running:
            return
        
        if not self.options_client:
            logger.debug("No options client available, skipping flow fetch")
            return
        
        try:
            # Get unusual activity (last hour)
            hours = max(1, self.update_interval // 3600 + 1)
            flows = await self.options_client.get_unusual_activity(None, hours=hours)
            
            if not flows:
                return
            
            # Filter significant flows and new flows
            significant_flows = []
            for flow in flows:
                # Check if significant (premium threshold)
                if flow.premium and flow.premium >= self.min_flow_threshold:
                    # Check if new (not seen before)
                    flow_id = f"{flow.symbol}_{flow.timestamp}_{flow.premium}"
                    if flow_id not in self._last_flow_ids:
                        significant_flows.append(flow)
                        self._last_flow_ids.add(flow_id)
            
            # Limit size of tracking set (keep last 1000)
            if len(self._last_flow_ids) > 1000:
                # Remove oldest entries (simple approach: clear half)
                self._last_flow_ids = set(list(self._last_flow_ids)[500:])
            
            # Broadcast significant flows
            if significant_flows:
                for flow in significant_flows:
                    message = {
                        "type": MessageType.OPTIONS_FLOW.value,
                        "channel": "options_flow",
                        "timestamp": flow.timestamp.isoformat() if hasattr(flow.timestamp, 'isoformat') else datetime.now().isoformat(),
                        "data": {
                            "symbol": flow.symbol,
                            "strike": flow.strike,
                            "expiry": flow.expiry.isoformat() if hasattr(flow.expiry, 'isoformat') else str(flow.expiry),
                            "option_type": flow.option_type,
                            "volume": flow.volume,
                            "premium": flow.premium,
                            "direction": flow.direction,
                            "unusual": flow.unusual if hasattr(flow, 'unusual') else True,
                            "is_sweep": flow.is_sweep if hasattr(flow, 'is_sweep') else False,
                            "is_block": flow.is_block if hasattr(flow, 'is_block') else False,
                        }
                    }
                    
                    await get_websocket_manager().broadcast("options_flow", message)
                
                logger.debug(f"Broadcasted {len(significant_flows)} options flow updates")
        
        except Exception as e:
            logger.error(f"Error in options flow stream: {e}", exc_info=True)
            # Continue running despite errors
    
    async def start(self):
        """Start the options flow stream"""
        if self._running:
            logger.warning("OptionsFlowStream already running")
            return
        
        self._running = True
        
        async def stream_loop():
            """Background task loop"""
            while self._running:
                try:
                    await self._fetch_and_broadcast_flow()
                    await asyncio.sleep(self.update_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in options flow stream loop: {e}", exc_info=True)
                    await asyncio.sleep(self.update_interval)
        
        self._task = asyncio.create_task(stream_loop())
        logger.info("OptionsFlowStream started")
    
    async def stop(self):
        """Stop the options flow stream"""
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("OptionsFlowStream stopped")
    
    def is_running(self) -> bool:
        """Check if stream is running"""
        return self._running

