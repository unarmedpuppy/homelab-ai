"""
API Middleware
==============

Custom middleware for the FastAPI application.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import re

from ..config.settings import settings

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Logging middleware for request/response tracking"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else None
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} ({process_time:.3f}s)",
            extra={
                "status_code": response.status_code,
                "process_time": process_time
            }
        )
        
        return response

def parse_rate_limit(rate_limit_str: str) -> Tuple[int, int]:
    """
    Parse rate limit string like "100/minute" or "1000/hour"
    
    Returns:
        Tuple of (limit, period_seconds)
    """
    match = re.match(r'(\d+)/(\w+)', rate_limit_str.lower())
    if not match:
        return 100, 60  # Default: 100 per minute
    
    limit = int(match.group(1))
    period = match.group(2)
    
    period_map = {
        'second': 1,
        'minute': 60,
        'hour': 3600,
        'day': 86400,
    }
    
    period_seconds = period_map.get(period, 60)
    return limit, period_seconds


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enhanced rate limiting middleware with API key support"""
    
    def __init__(self, app):
        super().__init__(app)
        # Parse rate limits from settings
        self.ip_limit, self.ip_period = parse_rate_limit(settings.api.rate_limit_per_ip)
        self.key_limit, self.key_period = parse_rate_limit(settings.api.rate_limit_per_key)
        
        # Track by IP (for unauthenticated requests)
        self.ip_clients: Dict[str, List[float]] = {}
        # Track by API key (for authenticated requests)
        self.key_clients: Dict[str, List[float]] = {}
    
    def _get_rate_limit_info(self, identifier: str, is_api_key: bool) -> Tuple[int, int, int, float]:
        """
        Get rate limit info for identifier
        
        Returns:
            Tuple of (limit, period, remaining, reset_time)
        """
        if is_api_key:
            limit, period = self.key_limit, self.key_period
            clients = self.key_clients
        else:
            limit, period = self.ip_limit, self.ip_period
            clients = self.ip_clients
        
        current_time = time.time()
        
        # Clean old entries
        if identifier in clients:
            clients[identifier] = [
                ts for ts in clients[identifier]
                if ts > current_time - period
            ]
            remaining = max(0, limit - len(clients[identifier]))
        else:
            remaining = limit
        
        reset_time = current_time + period
        
        return limit, period, remaining, reset_time
    
    async def dispatch(self, request: Request, call_next):
        current_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        
        # Check for API key
        api_key = request.headers.get(settings.api.api_key_header)
        identifier = api_key if api_key else client_ip
        is_api_key = bool(api_key and settings.api.auth_enabled)
        
        # Get rate limit info
        limit, period, remaining, reset_time = self._get_rate_limit_info(identifier, is_api_key)
        
        # Get appropriate client dict
        if is_api_key:
            clients = self.key_clients
        else:
            clients = self.ip_clients
        
        # Check if limit exceeded
        if identifier in clients:
            if len(clients[identifier]) >= limit:
                logger.warning(
                    f"Rate limit exceeded for {'API key' if is_api_key else 'IP'}: "
                    f"{identifier[:8] if is_api_key else identifier}..."
                )
                response = Response(
                    content='{"detail": "Rate limit exceeded"}',
                    status_code=429,
                    media_type="application/json"
                )
                # Add rate limit headers
                if settings.api.enable_rate_limit_headers:
                    response.headers["X-RateLimit-Limit"] = str(limit)
                    response.headers["X-RateLimit-Remaining"] = "0"
                    response.headers["X-RateLimit-Reset"] = str(int(reset_time))
                return response
        
        # Process request
        response = await call_next(request)
        
        # Track request
        if identifier not in clients:
            clients[identifier] = []
        clients[identifier].append(current_time)
        
        # Clean old entries periodically (every 100 requests for this identifier)
        if len(clients[identifier]) % 100 == 0:
            clients[identifier] = [
                ts for ts in clients[identifier]
                if ts > current_time - period
            ]
        
        # Add rate limit headers to response
        if settings.api.enable_rate_limit_headers:
            # Recalculate after request (we just added one)
            _, _, remaining_after, reset_time_after = self._get_rate_limit_info(identifier, is_api_key)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining_after)
            response.headers["X-RateLimit-Reset"] = str(int(reset_time_after))
        
        return response
