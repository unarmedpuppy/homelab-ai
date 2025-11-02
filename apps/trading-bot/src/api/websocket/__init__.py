"""
WebSocket Module
================

Real-time data streaming via WebSocket connections.
"""

from .manager import WebSocketConnectionManager, get_websocket_manager

__all__ = [
    "WebSocketConnectionManager",
    "get_websocket_manager",
]
