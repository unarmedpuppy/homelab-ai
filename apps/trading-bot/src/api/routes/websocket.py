"""
WebSocket Routes
================

FastAPI WebSocket endpoints for real-time data streaming.
"""

import json
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel, ValidationError

from ..websocket import get_websocket_manager
from ..websocket.manager import MessageType
from ...config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class ClientMessage(BaseModel):
    """Client-to-server message model"""
    type: str
    channel: Optional[str] = None
    symbols: Optional[list[str]] = None
    params: Optional[Dict[str, Any]] = None


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: Optional[str] = Query(None)):
    """
    Main WebSocket endpoint for real-time data streaming
    
    Supports:
    - Subscribe/unsubscribe to channels (price, portfolio, signals, etc.)
    - Ping/pong heartbeat
    - Multiple concurrent connections
    
    Message Format (Client → Server):
    {
        "type": "subscribe|unsubscribe|ping",
        "channel": "price|portfolio|signals|market_data|options_flow",
        "symbols": ["AAPL", "SPY"],  // Optional, for price/market_data subscriptions
        "params": {...}  // Optional channel-specific parameters
    }
    
    Message Format (Server → Client):
    {
        "type": "price_update|portfolio_update|signal|trade_executed|pong|error",
        "channel": "...",
        "timestamp": "2024-12-19T12:00:00Z",
        "data": {...}
    }
    """
    manager = get_websocket_manager()
    
    # Check if WebSocket is enabled
    if not settings.websocket.enabled:
        await websocket.close(code=1008, reason="WebSocket server disabled")
        return
    
    # Connect client
    try:
        ws_client_id = await manager.connect(websocket, client_id)
        logger.info(f"WebSocket connection established: {ws_client_id}")
    except RuntimeError as e:
        logger.warning(f"WebSocket connection rejected: {e}")
        await websocket.close(code=1008, reason=str(e))
        return
    except Exception as e:
        logger.error(f"Error accepting WebSocket connection: {e}", exc_info=True)
        await websocket.close(code=1011, reason="Internal server error")
        return
    
    # Auto-subscribe to all streams for MVP (dashboard expects all updates)
    # Note: Price subscriptions are per-symbol (e.g., "price:AAPL"), so we can't auto-subscribe
    # to all prices without knowing which symbols. Clients should subscribe to specific symbols.
    # However, we can subscribe to broadcast channels that don't require symbols.
    try:
        await manager.subscribe(ws_client_id, "signals")
        await manager.subscribe(ws_client_id, "portfolio")
        await manager.subscribe(ws_client_id, "options_flow")
        logger.debug(f"Auto-subscribed client {ws_client_id} to broadcast channels (signals, portfolio, options_flow)")
    except Exception as e:
        logger.warning(f"Error auto-subscribing client {ws_client_id}: {e}")
    
    # Message loop
    try:
        while True:
            # Receive message from client
            try:
                message_text = await websocket.receive_text()
            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected: {ws_client_id}")
                break
            
            try:
                message_data = json.loads(message_text)
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON from client {ws_client_id}: {e}")
                await manager.send_to_client(ws_client_id, {
                    "type": MessageType.ERROR.value,
                    "error": "Invalid JSON format",
                    "timestamp": __import__("datetime").datetime.now().isoformat()
                })
                continue
            
            # Validate message
            try:
                message = ClientMessage(**message_data)
            except ValidationError as e:
                logger.warning(f"Invalid message from client {ws_client_id}: {e}")
                await manager.send_to_client(ws_client_id, {
                    "type": MessageType.ERROR.value,
                    "error": "Invalid message format",
                    "details": str(e),
                    "timestamp": __import__("datetime").datetime.now().isoformat()
                })
                continue
            
            # Handle message by type
            await handle_client_message(manager, ws_client_id, message)
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {ws_client_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket handler for {ws_client_id}: {e}", exc_info=True)
    finally:
        # Cleanup
        await manager.disconnect(ws_client_id)


async def handle_client_message(
    manager,
    client_id: str,
    message: ClientMessage
):
    """
    Handle incoming client message
    
    Args:
        manager: WebSocketConnectionManager instance
        client_id: Client ID
        message: Parsed client message
    """
    message_type = message.type.lower()
    
    if message_type == MessageType.PING.value:
        # Handle ping
        await manager.handle_ping(client_id)
        logger.debug(f"Ping received from {client_id}")
    
    elif message_type == MessageType.SUBSCRIBE.value:
        # Handle subscription
        if not message.channel:
            await manager.send_to_client(client_id, {
                "type": MessageType.ERROR.value,
                "error": "Channel required for subscribe",
                "timestamp": __import__("datetime").datetime.now().isoformat()
            })
            return
        
        # Handle channel-specific subscriptions
        if message.channel == "price" and message.symbols:
            # Subscribe to price updates for specific symbols
            for symbol in message.symbols:
                channel_key = f"price:{symbol.upper()}"
                await manager.subscribe(client_id, channel_key)
        elif message.channel == "market_data" and message.symbols:
            # Subscribe to market data for specific symbols
            timeframe = message.params.get("timeframe", "1m") if message.params else "1m"
            for symbol in message.symbols:
                channel_key = f"market_data:{symbol.upper()}:{timeframe}"
                await manager.subscribe(client_id, channel_key)
        else:
            # Generic channel subscription
            await manager.subscribe(client_id, message.channel)
        
        # Send confirmation
        await manager.send_to_client(client_id, {
            "type": "subscribed",
            "channel": message.channel,
            "symbols": message.symbols,
            "timestamp": __import__("datetime").datetime.now().isoformat()
        })
        logger.debug(f"Client {client_id} subscribed to {message.channel}")
    
    elif message_type == MessageType.UNSUBSCRIBE.value:
        # Handle unsubscription
        if not message.channel:
            await manager.send_to_client(client_id, {
                "type": MessageType.ERROR.value,
                "error": "Channel required for unsubscribe",
                "timestamp": __import__("datetime").datetime.now().isoformat()
            })
            return
        
        # Handle channel-specific unsubscriptions
        if message.channel == "price" and message.symbols:
            for symbol in message.symbols:
                channel_key = f"price:{symbol.upper()}"
                await manager.unsubscribe(client_id, channel_key)
        elif message.channel == "market_data" and message.symbols:
            timeframe = message.params.get("timeframe", "1m") if message.params else "1m"
            for symbol in message.symbols:
                channel_key = f"market_data:{symbol.upper()}:{timeframe}"
                await manager.unsubscribe(client_id, channel_key)
        else:
            await manager.unsubscribe(client_id, message.channel)
        
        # Send confirmation
        await manager.send_to_client(client_id, {
            "type": "unsubscribed",
            "channel": message.channel,
            "symbols": message.symbols,
            "timestamp": __import__("datetime").datetime.now().isoformat()
        })
        logger.debug(f"Client {client_id} unsubscribed from {message.channel}")
    
    else:
        # Unknown message type
        await manager.send_to_client(client_id, {
            "type": MessageType.ERROR.value,
            "error": f"Unknown message type: {message_type}",
            "timestamp": __import__("datetime").datetime.now().isoformat()
        })
        logger.warning(f"Unknown message type from {client_id}: {message_type}")


@router.get("/websocket/status")
async def websocket_status():
    """Get WebSocket server status including stream health"""
    manager = get_websocket_manager()
    
    # Get stream health status
    stream_health = {}
    try:
        from ..websocket.streams.health import get_health_monitor
        health_monitor = get_health_monitor()
        stream_health = health_monitor.get_all_status()
        
        # Convert datetime objects to ISO strings for JSON serialization
        for stream_name, status in stream_health.items():
            if "last_update" in status and status["last_update"]:
                status["last_update"] = status["last_update"].isoformat()
            if "started_at" in status and status["started_at"]:
                status["started_at"] = status["started_at"].isoformat()
    except Exception as e:
        logger.debug(f"Error getting stream health: {e}")
    
    return {
        "enabled": settings.websocket.enabled,
        "active_connections": manager.get_connection_count(),
        "max_connections": settings.websocket.max_connections,
        "ping_interval": settings.websocket.ping_interval,
        "price_update_interval": settings.websocket.price_update_interval,
        "portfolio_update_interval": settings.websocket.portfolio_update_interval,
        "stream_health": stream_health
    }
