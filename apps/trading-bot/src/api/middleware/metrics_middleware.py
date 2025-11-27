"""
Metrics Collection Middleware
=============================

Automatic HTTP request metrics collection for Prometheus.
Tracks request count, duration, sizes, and errors.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ...config.settings import settings
from ...utils.metrics import (
    get_or_create_counter,
    get_or_create_histogram,
    get_metrics_registry
)

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting HTTP request metrics
    
    Collects:
    - Request count by method, endpoint, status code
    - Request duration by endpoint
    - Request/response sizes by endpoint
    - Error counts by endpoint and error type
    """
    
    def __init__(self, app: ASGIApp):
        """
        Initialize metrics middleware
        
        Args:
            app: ASGI application
        """
        super().__init__(app)
        
        # Only initialize metrics if enabled
        if not settings.metrics.enabled:
            logger.debug("Metrics collection disabled, skipping middleware initialization")
            self.request_count = None
            self.request_duration = None
            self.request_size = None
            self.response_size = None
            self.errors_total = None
            return
        
        registry = get_metrics_registry()
        
        # Initialize metrics
        # HTTP request counter: method, endpoint, status
        self.request_count = get_or_create_counter(
            name="http_requests_total",
            documentation="Total number of HTTP requests",
            labelnames=["method", "endpoint", "status_code"],
            registry=registry
        )
        
        # Request duration histogram: endpoint
        self.request_duration = get_or_create_histogram(
            name="http_request_duration_seconds",
            documentation="HTTP request duration in seconds",
            labelnames=["method", "endpoint"],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
            registry=registry
        )
        
        # Request size histogram: endpoint
        self.request_size = get_or_create_histogram(
            name="http_request_size_bytes",
            documentation="HTTP request size in bytes",
            labelnames=["method", "endpoint"],
            buckets=(100, 500, 1000, 2500, 5000, 10000, 25000, 50000, 100000),
            registry=registry
        )
        
        # Response size histogram: endpoint
        self.response_size = get_or_create_histogram(
            name="http_response_size_bytes",
            documentation="HTTP response size in bytes",
            labelnames=["method", "endpoint"],
            buckets=(100, 500, 1000, 2500, 5000, 10000, 25000, 50000, 100000, 500000),
            registry=registry
        )
        
        # Error counter: endpoint, error_type
        self.errors_total = get_or_create_counter(
            name="http_errors_total",
            documentation="Total number of HTTP errors",
            labelnames=["method", "endpoint", "status_code", "error_type"],
            registry=registry
        )
        
        logger.info("Metrics middleware initialized")
    
    def _normalize_endpoint(self, path: str) -> str:
        """
        Normalize endpoint path for metrics
        
        Converts dynamic paths (e.g., /api/trading/{symbol}) to generic form
        to avoid high cardinality in metrics.
        
        Args:
            path: Request path
            
        Returns:
            Normalized endpoint path
        """
        # Remove query parameters
        if '?' in path:
            path = path.split('?')[0]
        
        # Normalize common dynamic segments
        # Convert UUIDs to {id}
        import re
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{id}', path, flags=re.IGNORECASE)
        
        # Convert numeric IDs to {id}
        path = re.sub(r'/\d+', '/{id}', path)
        
        # Convert common symbol patterns to {symbol}
        # Match uppercase 1-5 letter symbols (stock symbols)
        path = re.sub(r'/[A-Z]{1,5}(?=/|$)', '/{symbol}', path)
        
        # Limit path depth to avoid explosion
        parts = path.split('/')
        if len(parts) > 6:  # Keep first 6 parts, collapse rest
            path = '/'.join(parts[:6]) + '/...'
        
        return path or "/"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and collect metrics
        
        Args:
            request: HTTP request
            call_next: Next middleware/handler
            
        Returns:
            HTTP response
        """
        # Skip metrics collection if disabled
        if not settings.metrics.enabled or self.request_count is None:
            return await call_next(request)
        
        # Skip metrics endpoint itself to avoid recursion
        if request.url.path == settings.metrics.metrics_path:
            return await call_next(request)
        
        start_time = time.time()
        method = request.method
        endpoint = self._normalize_endpoint(request.url.path)
        
        # Get request size (approximate)
        request_size = 0
        if hasattr(request, '_body'):
            request_size = len(request._body) if request._body else 0
        else:
            # Try to get from headers
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    request_size = int(content_length)
                except (ValueError, TypeError):
                    request_size = 0
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
            error_type = None
            
            # Determine error type
            if status_code >= 500:
                error_type = "server_error"
            elif status_code >= 400:
                error_type = "client_error"
            else:
                error_type = "none"
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Get response size (improved tracking)
            response_size = 0
            # First try content-length header (most reliable)
            content_length = response.headers.get("content-length")
            if content_length:
                try:
                    response_size = int(content_length)
                except (ValueError, TypeError):
                    pass
            
            # Fallback: try to get from response body if available
            if response_size == 0:
                if hasattr(response, 'body'):
                    # Response body is available
                    if hasattr(response.body, '__len__'):
                        response_size = len(response.body)
                    elif hasattr(response.body, '__iter__'):
                        # For streaming responses, we can't measure without consuming
                        # Set to 0 and skip metric (won't affect Prometheus)
                        pass
            
            # Record metrics
            try:
                # Request count
                self.request_count.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=str(status_code)
                ).inc()
                
                # Request duration
                self.request_duration.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                
                # Request size
                if request_size > 0:
                    self.request_size.labels(
                        method=method,
                        endpoint=endpoint
                    ).observe(request_size)
                
                # Response size
                if response_size > 0:
                    self.response_size.labels(
                        method=method,
                        endpoint=endpoint
                    ).observe(response_size)
                
                # Errors
                if error_type != "none":
                    self.errors_total.labels(
                        method=method,
                        endpoint=endpoint,
                        status_code=str(status_code),
                        error_type=error_type
                    ).inc()
                    
            except Exception as e:
                # Don't let metrics collection errors break the request
                logger.warning(f"Error recording metrics: {e}", exc_info=True)
            
            return response
            
        except Exception as e:
            # Handle uncaught exceptions
            duration = time.time() - start_time
            status_code = 500
            error_type = type(e).__name__
            
            # Record error metrics
            try:
                self.request_count.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=str(status_code)
                ).inc()
                
                self.errors_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=str(status_code),
                    error_type=error_type
                ).inc()
                
                self.request_duration.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                
                # Also record in system error metrics
                try:
                    from ...utils.metrics import record_exception
                    is_critical = status_code >= 500  # 5xx errors are critical
                    record_exception(error_type, component="api", is_critical=is_critical)
                except (ImportError, Exception) as sys_metrics_error:
                    logger.debug(f"Could not record exception in system metrics: {sys_metrics_error}")
                
            except Exception as metrics_error:
                logger.warning(f"Error recording exception metrics: {metrics_error}", exc_info=True)
            
            # Re-raise the exception
            raise

