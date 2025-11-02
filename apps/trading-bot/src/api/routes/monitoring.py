"""
Monitoring & Health Check API Routes
====================================

API endpoints for system health monitoring, metrics, and status checks.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
import psutil
import os
import time
from functools import lru_cache
from contextlib import asynccontextmanager
import asyncio

from sqlalchemy import text

from ...config.settings import settings
from ...data.database import SessionLocal, engine
from ...data.providers.sentiment import SentimentAggregator
from ...data.providers.sentiment.options_flow_sentiment import OptionsFlowSentimentProvider

logger = logging.getLogger(__name__)
router = APIRouter()


class HealthStatus(BaseModel):
    """Health check status"""
    status: str
    timestamp: datetime
    version: str
    environment: str
    uptime_seconds: float


class ComponentHealth(BaseModel):
    """Component health status"""
    name: str
    status: str
    available: bool
    message: Optional[str] = None
    response_time_ms: Optional[float] = None


class SystemMetrics(BaseModel):
    """System resource metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_percent: Optional[float] = None
    disk_used_mb: Optional[float] = None
    disk_total_mb: Optional[float] = None


class ProviderStatus(BaseModel):
    """Provider status"""
    name: str
    available: bool
    configured: bool
    last_check: datetime
    error: Optional[str] = None


class MonitoringResponse(BaseModel):
    """Complete monitoring status"""
    health: HealthStatus
    components: List[ComponentHealth]
    providers: List[ProviderStatus]
    metrics: SystemMetrics


# Track application start time
_app_start_time = datetime.now()

# Cached provider instances (lazy-loaded)
_cached_aggregator: Optional[SentimentAggregator] = None
_cached_providers: Dict[str, Any] = {}
_provider_status_cache: Dict[str, tuple] = {}  # name -> (status, timestamp)
PROVIDER_STATUS_CACHE_TTL = 30  # seconds

# Health check timeout
HEALTH_CHECK_TIMEOUT = 5.0  # seconds


def get_uptime() -> float:
    """Get application uptime in seconds"""
    return (datetime.now() - _app_start_time).total_seconds()


def get_cached_aggregator() -> SentimentAggregator:
    """Get or create cached sentiment aggregator"""
    global _cached_aggregator
    if _cached_aggregator is None:
        _cached_aggregator = SentimentAggregator()
    return _cached_aggregator


def get_cached_provider(provider_name: str):
    """Get or create cached provider instance"""
    global _cached_providers
    
    if provider_name not in _cached_providers:
        try:
            if provider_name == "options":
                _cached_providers[provider_name] = OptionsFlowSentimentProvider()
            elif provider_name == "twitter":
                from ...data.providers.sentiment import TwitterSentimentProvider
                _cached_providers[provider_name] = TwitterSentimentProvider()
            elif provider_name == "reddit":
                from ...data.providers.sentiment import RedditSentimentProvider
                _cached_providers[provider_name] = RedditSentimentProvider()
            elif provider_name == "news":
                from ...data.providers.sentiment import NewsSentimentProvider
                _cached_providers[provider_name] = NewsSentimentProvider()
        except Exception as e:
            logger.warning(f"Failed to initialize provider {provider_name}: {e}")
            return None
    
    return _cached_providers.get(provider_name)


def get_cached_provider_status(provider_name: str) -> tuple:
    """Get cached provider status or check and cache"""
    global _provider_status_cache
    
    cache_key = provider_name
    now = datetime.now()
    
    # Check cache
    if cache_key in _provider_status_cache:
        status_data, timestamp = _provider_status_cache[cache_key]
        if (now - timestamp).total_seconds() < PROVIDER_STATUS_CACHE_TTL:
            return status_data
    
    # Check provider (with timeout)
    try:
        provider = get_cached_provider(provider_name)
        if provider and hasattr(provider, 'is_available'):
            available = provider.is_available()
        else:
            available = False
        
        status_data = (available, None)  # (available, error)
        _provider_status_cache[cache_key] = (status_data, now)
        return status_data
    except Exception as e:
        error_msg = str(e) if settings.environment == "development" else "Provider check failed"
        status_data = (False, error_msg)
        _provider_status_cache[cache_key] = (status_data, now)
        return status_data


async def timeout_wrapper(coro, timeout_seconds: float):
    """Wrap async function with timeout"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.warning(f"Operation timed out after {timeout_seconds}s")
        return None


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """
    Basic health check endpoint
    
    Returns:
        Health status with uptime information
    """
    return HealthStatus(
        status="healthy",
        timestamp=datetime.now(),
        version="2.0.0",
        environment=settings.environment,
        uptime_seconds=get_uptime()
    )


@router.get("/health/detailed", response_model=MonitoringResponse)
async def detailed_health_check():
    """
    Detailed health check with component status
    
    Returns:
        Complete system health status including:
        - Overall health
        - Component status (database, providers, etc.)
        - Provider availability
        - System metrics
    """
    components: List[ComponentHealth] = []
    providers: List[ProviderStatus] = []
    
    # Check database (with timeout)
    db_status = "healthy"
    db_available = False
    db_response_time = None
    try:
        start = time.time()
        with SessionLocal() as db:
            # Use text() wrapper for SQL safety
            db.execute(text("SELECT 1"))
            db_response_time = (time.time() - start) * 1000
        
        # Check for timeout
        if db_response_time > HEALTH_CHECK_TIMEOUT * 1000:
            db_status = "degraded"
            logger.warning(f"Database health check slow: {db_response_time}ms")
        
        db_available = True
    except Exception as e:
        db_status = "unhealthy"
        error_msg = str(e) if settings.environment == "development" else "Database check failed"
        logger.error(f"Database health check failed: {error_msg}")
    
    components.append(ComponentHealth(
        name="database",
        status=db_status,
        available=db_available,
        response_time_ms=db_response_time
    ))
    
    # Check sentiment aggregator (use cached instance)
    try:
        aggregator = get_cached_aggregator()
        aggregator_available = len(aggregator.providers) > 0
        error_msg = None
        if not aggregator_available:
            error_msg = "No providers available"
        components.append(ComponentHealth(
            name="sentiment_aggregator",
            status="healthy" if aggregator_available else "degraded",
            available=aggregator_available,
            message=f"{len(aggregator.providers)} providers available" if aggregator_available else error_msg
        ))
    except Exception as e:
        error_msg = str(e) if settings.environment == "development" else "Aggregator check failed"
        components.append(ComponentHealth(
            name="sentiment_aggregator",
            status="unhealthy",
            available=False,
            message=error_msg
        ))
    
    # Check providers (use cached status)
    provider_names = ["twitter", "reddit", "news", "options"]
    for provider_name in provider_names:
        try:
            # Use cached provider status check
            available, error = get_cached_provider_status(provider_name)
            
            error_msg = None
            if error and settings.environment != "development":
                error_msg = "Provider check failed"  # Sanitize in production
            
            providers.append(ProviderStatus(
                name=provider_name,
                available=available,
                configured=available,
                last_check=datetime.now(),
                error=error_msg or error
            ))
        except Exception as e:
            error_msg = str(e) if settings.environment == "development" else "Provider check failed"
            providers.append(ProviderStatus(
                name=provider_name,
                available=False,
                configured=False,
                last_check=datetime.now(),
                error=error_msg
            ))
    
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    
    disk_percent = None
    disk_used_mb = None
    disk_total_mb = None
    try:
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used_mb = disk.used / (1024 * 1024)
        disk_total_mb = disk.total / (1024 * 1024)
    except Exception:
        pass  # May not have disk access in container
    
    metrics = SystemMetrics(
        cpu_percent=cpu_percent,
        memory_percent=memory.percent,
        memory_used_mb=memory.used / (1024 * 1024),
        memory_total_mb=memory.total / (1024 * 1024),
        disk_percent=disk_percent,
        disk_used_mb=disk_used_mb,
        disk_total_mb=disk_total_mb
    )
    
    # Determine overall health
    unhealthy_components = [c for c in components if c.status == "unhealthy"]
    overall_status = "healthy" if not unhealthy_components else "degraded"
    
    return MonitoringResponse(
        health=HealthStatus(
            status=overall_status,
            timestamp=datetime.now(),
            version="2.0.0",
            environment=settings.environment,
            uptime_seconds=get_uptime()
        ),
        components=components,
        providers=providers,
        metrics=metrics
    )


@router.get("/metrics")
async def get_metrics():
    """
    Get system and application metrics
    
    Returns:
        System resource usage and application metrics
    """
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    
    disk_percent = None
    disk_used_mb = None
    disk_total_mb = None
    try:
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_used_mb = disk.used / (1024 * 1024)
        disk_total_mb = disk.total / (1024 * 1024)
    except Exception:
        pass
    
    return {
        "timestamp": datetime.now().isoformat(),
        "system": {
            "cpu_percent": cpu_percent,
            "memory": {
                "percent": memory.percent,
                "used_mb": memory.used / (1024 * 1024),
                "total_mb": memory.total / (1024 * 1024),
                "available_mb": memory.available / (1024 * 1024)
            },
            "disk": {
                "percent": disk_percent,
                "used_mb": disk_used_mb,
                "total_mb": disk_total_mb
            } if disk_percent is not None else None
        },
        "application": {
            "uptime_seconds": get_uptime(),
            "version": "2.0.0",
            "environment": settings.environment
        }
    }


@router.get("/providers/status")
async def get_providers_status():
    """
    Get status of all data providers
    
    Returns:
        Status of each provider (Twitter, Reddit, News, Options Flow)
    """
    providers: List[ProviderStatus] = []
    
    # Use cached provider status
    provider_names = ["twitter", "reddit", "news", "options"]
    for provider_name in provider_names:
        try:
            available, error = get_cached_provider_status(provider_name)
            
            error_msg = None
            if error and settings.environment != "development":
                error_msg = "Provider check failed"
            
            providers.append(ProviderStatus(
                name=provider_name,
                available=available,
                configured=available,
                last_check=datetime.now(),
                error=error_msg or error
            ))
        except Exception as e:
            error_msg = str(e) if settings.environment == "development" else "Provider check failed"
            providers.append(ProviderStatus(
                name=provider_name,
                available=False,
                configured=False,
                last_check=datetime.now(),
                error=error_msg
            ))
    
    return {
        "timestamp": datetime.now().isoformat(),
        "providers": providers,
        "total_providers": len(providers),
        "available_providers": sum(1 for p in providers if p.available)
    }


@router.get("/rate-limits")
async def get_rate_limits():
    """
    Get rate limit status for all data sources
    
    Returns:
        Rate limit information for each source
    """
    sources = ["twitter", "reddit", "news", "options", "stocktwits"]
    rate_limits = {}
    
    # Default rate limits (requests per window)
    source_limits = {
        "twitter": (300, 900),  # 300 requests per 15 minutes
        "reddit": (60, 60),  # 60 requests per minute
        "news": (100, 60),  # 100 requests per minute
        "options": (100, 60),  # 100 requests per minute
        "stocktwits": (200, 3600),  # 200 requests per hour (1000 with token)
    }
    
    for source in sources:
        limit, window = source_limits.get(source, (100, 60))
        limiter = get_rate_limiter(source)
        status = limiter.get_status(limit, window)
        
        rate_limits[source] = {
            "allowed": status.allowed,
            "used": status.used,
            "remaining": status.remaining,
            "window_seconds": window,
            "reset_at": status.reset_at.isoformat(),
            "is_limited": status.is_limited
        }
    
    return {
        "timestamp": datetime.now().isoformat(),
        "sources": rate_limits
    }


@router.get("/cache/status")
async def get_cache_status():
    """
    Get cache status and statistics
    
    Returns:
        Cache health and availability information
    """
    cache = get_cache_manager()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "redis_available": cache.is_available(),
        "using_redis": cache.redis_client is not None,
        "in_memory_fallback": cache.redis_client is None,
        "namespace": cache.namespace
    }


@router.get("/usage")
async def get_usage_metrics():
    """
    Get API usage metrics and statistics
    
    Returns:
        Usage metrics including requests, costs, cache hit rates
    """
    monitor = get_usage_monitor()
    summary = monitor.get_usage_summary()
    
    return {
        "timestamp": datetime.now().isoformat(),
        **summary
    }


@router.post("/cache/clear")
async def clear_cache(pattern: Optional[str] = None):
    """
    Clear cache entries
    
    Args:
        pattern: Optional pattern to match (e.g., "sentiment:*"). If not provided, clears all.
        
    Returns:
        Confirmation of cache clear operation
    """
    cache = get_cache_manager()
    
    if pattern:
        cache.clear_pattern(pattern)
        return {
            "status": "success",
            "message": f"Cleared cache entries matching pattern: {pattern}"
        }
    else:
        # Clear all sentiment-related caches
        cache.clear_pattern("sentiment:*")
        cache.clear_pattern("confluence:*")
        cache.clear_pattern("rate_limit:*")
        
        return {
            "status": "success",
            "message": "Cleared sentiment, confluence, and rate limit caches"
        }
