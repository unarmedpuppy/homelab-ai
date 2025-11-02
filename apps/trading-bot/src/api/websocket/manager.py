"""
WebSocket Connection Manager
=============================

Manages WebSocket connections, subscriptions, and broadcasting.
Thread-safe singleton pattern following project conventions.
"""

import asyncio
import logging
import threading
import uuid
from typing import Dict, Set, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types"""
    # Client → Server
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PING = "ping"
    
    # Server → Client
    PRICE_UPDATE = "price_update"
    MARKET_DATA = "market_data"
    OPTIONS_FLOW = "options_flow"
    PORTFOLIO_UPDATE = "portfolio_update"
    SIGNAL = "signal"
    TRADE_EXECUTED = "trade_executed"
    PONG = "pong"
    ERROR = "error"


@dataclass
class WebSocketConnection:
    """WebSocket connection metadata"""
    connection: WebSocket
    client_id: str
    connected_at: datetime
    last_ping: Optional[datetime] = None
    subscriptions: Set[str] = field(default_factory=set)  # Set of subscribed channels/symbols


class WebSocketConnectionManager:
    """
    Thread-safe WebSocket connection manager
    
    Handles:
    - Connection lifecycle (connect, disconnect)
    - Subscription management
    - Message broadcasting
    - Heartbeat/ping-pong
    """
    
    def __init__(
        self,
        heartbeat_interval: int = 30,
        heartbeat_timeout: int = 60,
        max_connections: int = 100
    ):
        """
        Initialize WebSocket connection manager
        
        Args:
            heartbeat_interval: Seconds between ping messages
            heartbeat_timeout: Seconds to wait for pong before disconnecting
            max_connections: Maximum concurrent connections
        """
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = heartbeat_timeout
        self.max_connections = max_connections
        
        # Active connections: client_id → WebSocketConnection
        self._connections: Dict[str, WebSocketConnection] = {}
        self._connections_lock = threading.Lock()
        
        # Subscriptions: channel/symbol → Set of client_ids
        self._subscriptions: Dict[str, Set[str]] = {}
        self._subscriptions_lock = threading.Lock()
        
        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None) -> str:
        """
        Accept new WebSocket connection
        
        Args:
            websocket: FastAPI WebSocket connection
            
        Returns:
            Client ID for this connection
            
        Raises:
            RuntimeError: If max connections reached
        """
        with self._connections_lock:
            if len(self._connections) >= self.max_connections:
                raise RuntimeError(f"Maximum connections ({self.max_connections}) reached")
        
        # Accept connection
        await websocket.accept()
        
        # Generate unique client ID if not provided
        if client_id is None:
            client_id = str(uuid.uuid4())
        
        # Create connection metadata
        connection = WebSocketConnection(
            connection=websocket,
            client_id=client_id,
            connected_at=datetime.now()
        )
        
        # Store connection
        with self._connections_lock:
            self._connections[client_id] = connection
        
        logger.info(f"WebSocket client connected: {client_id}")
        
        # Start heartbeat task if not running
        if not self._running:
            await self._start_heartbeat()
        
        return client_id
    
    async def disconnect(self, client_id: str):
        """
        Disconnect a client and cleanup
        
        Args:
            client_id: Client ID to disconnect
        """
        connection = self._connections.get(client_id)
        if not connection:
            return
        
        # Remove all subscriptions for this client
        with self._subscriptions_lock:
            for channel in list(connection.subscriptions):
                self._unsubscribe_internal(client_id, channel)
        
        # Remove connection
        with self._connections_lock:
            self._connections.pop(client_id, None)
        
        # Try to close connection gracefully
        try:
            await connection.connection.close()
        except Exception as e:
            logger.debug(f"Error closing WebSocket connection {client_id}: {e}")
        
        logger.info(f"WebSocket client disconnected: {client_id}")
    
    async def subscribe(self, client_id: str, channel: str) -> bool:
        """
        Subscribe client to a channel/symbol
        
        Args:
            client_id: Client ID
            channel: Channel/symbol to subscribe to (e.g., "price:AAPL", "portfolio")
            
        Returns:
            True if subscribed, False if client not found
        """
        with self._connections_lock:
            connection = self._connections.get(client_id)
            if not connection:
                logger.warning(f"Subscribe failed: client {client_id} not found")
                return False
            
            connection.subscriptions.add(channel)
        
        with self._subscriptions_lock:
            if channel not in self._subscriptions:
                self._subscriptions[channel] = set()
            self._subscriptions[channel].add(client_id)
        
        logger.debug(f"Client {client_id} subscribed to {channel}")
        return True
    
    async def unsubscribe(self, client_id: str, channel: str) -> bool:
        """
        Unsubscribe client from a channel/symbol
        
        Args:
            client_id: Client ID
            channel: Channel/symbol to unsubscribe from
            
        Returns:
            True if unsubscribed, False if client not found
        """
        with self._connections_lock:
            connection = self._connections.get(client_id)
            if not connection:
                return False
        
        with self._subscriptions_lock:
            self._unsubscribe_internal(client_id, channel)
        
        logger.debug(f"Client {client_id} unsubscribed from {channel}")
        return True
    
    def _unsubscribe_internal(self, client_id: str, channel: str):
        """Internal unsubscribe (must be called with subscriptions lock held)"""
        if channel in self._subscriptions:
            self._subscriptions[channel].discard(client_id)
            if not self._subscriptions[channel]:
                del self._subscriptions[channel]
        
        # Remove from connection's subscription set
        connection = self._connections.get(client_id)
        if connection:
            connection.subscriptions.discard(channel)
    
    async def broadcast(self, channel: str, message: Dict[str, Any]) -> int:
        """
        Broadcast message to all subscribers of a channel
        
        Args:
            channel: Channel/symbol to broadcast to
            message: Message dict to send (will be JSON-encoded)
            
        Returns:
            Number of clients that received the message
        """
        # Get subscribers for this channel
        with self._subscriptions_lock:
            client_ids = self._subscriptions.get(channel, set()).copy()
        
        if not client_ids:
            return 0
        
        # Send to all subscribers
        sent_count = 0
        disconnected_clients = []
        
        for client_id in client_ids:
            connection = self._connections.get(client_id)
            if not connection:
                disconnected_clients.append(client_id)
                continue
            
            try:
                await connection.connection.send_json(message)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Error sending message to client {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        if disconnected_clients:
            for client_id in disconnected_clients:
                await self.disconnect(client_id)
        
        return sent_count
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]) -> bool:
        """
        Send message to a specific client
        
        Args:
            client_id: Client ID
            message: Message dict to send
            
        Returns:
            True if sent, False if client not found or error
        """
        connection = self._connections.get(client_id)
        if not connection:
            return False
        
        try:
            await connection.connection.send_json(message)
            return True
        except Exception as e:
            logger.warning(f"Error sending message to client {client_id}: {e}")
            await self.disconnect(client_id)
            return False
    
    async def handle_ping(self, client_id: str):
        """
        Handle ping message from client (update last_ping time)
        
        Args:
            client_id: Client ID that sent ping
        """
        connection = self._connections.get(client_id)
        if connection:
            connection.last_ping = datetime.now()
            # Respond with pong
            await self.send_to_client(
                client_id,
                {"type": MessageType.PONG.value, "timestamp": datetime.now().isoformat()}
            )
    
    async def _start_heartbeat(self):
        """Start heartbeat task to ping clients periodically"""
        if self._running:
            return
        
        self._running = True
        
        async def heartbeat_loop():
            """Background task to send pings and check for timeouts"""
            while self._running:
                try:
                    await asyncio.sleep(self.heartbeat_interval)
                    
                    # Get all connections (copy to avoid lock during iteration)
                    with self._connections_lock:
                        connections = list(self._connections.values())
                    
                    current_time = datetime.now()
                    disconnected_clients = []
                    
                    for conn in connections:
                        # Send ping
                        try:
                            await conn.connection.send_json({
                                "type": "ping",
                                "timestamp": current_time.isoformat()
                            })
                        except Exception as e:
                            logger.debug(f"Error sending ping to {conn.client_id}: {e}")
                            disconnected_clients.append(conn.client_id)
                            continue
                        
                        # Check for timeout (if we have a last_ping time)
                        if conn.last_ping:
                            time_since_pong = (current_time - conn.last_ping).total_seconds()
                            if time_since_pong > self.heartbeat_timeout:
                                logger.warning(
                                    f"Client {conn.client_id} timeout: no pong in {time_since_pong}s"
                                )
                                disconnected_clients.append(conn.client_id)
                    
                    # Disconnect timed-out clients
                    for client_id in disconnected_clients:
                        await self.disconnect(client_id)
                
                except Exception as e:
                    logger.error(f"Error in heartbeat loop: {e}", exc_info=True)
                    await asyncio.sleep(self.heartbeat_interval)
        
        # Start background task
        self._heartbeat_task = asyncio.create_task(heartbeat_loop())
        logger.info("WebSocket heartbeat task started")
    
    async def stop(self):
        """Stop heartbeat task and close all connections"""
        self._running = False
        
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Disconnect all clients
        with self._connections_lock:
            client_ids = list(self._connections.keys())
        
        for client_id in client_ids:
            await self.disconnect(client_id)
        
        logger.info("WebSocket manager stopped")
    
    def get_connection_count(self) -> int:
        """Get current number of active connections"""
        with self._connections_lock:
            return len(self._connections)
    
    def get_subscription_count(self, channel: str) -> int:
        """Get number of subscribers to a channel"""
        with self._subscriptions_lock:
            return len(self._subscriptions.get(channel, set()))
    
    def get_client_subscriptions(self, client_id: str) -> Set[str]:
        """Get all channels a client is subscribed to"""
        connection = self._connections.get(client_id)
        if connection:
            return connection.subscriptions.copy()
        return set()


# Global manager instance (thread-safe singleton)
_websocket_manager: Optional[WebSocketConnectionManager] = None
_websocket_manager_lock = threading.Lock()


def get_websocket_manager() -> WebSocketConnectionManager:
    """
    Get global WebSocket manager instance (thread-safe singleton)
    
    Returns:
        WebSocketConnectionManager instance
    """
    global _websocket_manager
    if _websocket_manager is None:
        with _websocket_manager_lock:
            # Double-check pattern
            if _websocket_manager is None:
                from ...config.settings import settings
                ws_config = settings.websocket
                _websocket_manager = WebSocketConnectionManager(
                    heartbeat_interval=ws_config.ping_interval,
                    heartbeat_timeout=ws_config.heartbeat_timeout,  # Use configured timeout
                    max_connections=ws_config.max_connections
                )
                logger.info("WebSocket manager initialized")
    return _websocket_manager
