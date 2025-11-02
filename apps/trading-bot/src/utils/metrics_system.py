"""
System Health & Performance Metrics Utilities
=============================================

Metrics helpers for tracking system health, resource usage, and performance.
"""

import logging
import time
import sys
import os
from typing import Optional, Dict, Any

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

from ..config.settings import settings
from .metrics import (
    get_or_create_gauge,
    get_or_create_counter,
    get_or_create_histogram,
    get_metrics_registry
)

logger = logging.getLogger(__name__)


# Track startup time for uptime calculation
_app_start_time: Optional[float] = None

def get_app_start_time() -> float:
    """
    Get application startup time
    
    Returns:
        Unix timestamp of application startup
    """
    global _app_start_time
    if _app_start_time is None:
        _app_start_time = time.time()
    return _app_start_time


def initialize_system_metrics():
    """
    Initialize system health metrics
    
    Creates gauges for CPU, memory, disk, and uptime metrics.
    Should be called once at application startup.
    
    Note: This function is provided for backward compatibility.
    Metrics are automatically initialized on first use via get_system_metrics().
    """
    if not settings.metrics.enabled:
        logger.debug("Metrics disabled, skipping system metrics initialization")
        return
    
    try:
        # Just ensure metrics are created (they'll be created on first use anyway)
        # Initialize app start time if not already done
        get_app_start_time()
        logger.info("System metrics initialization completed")
    except Exception as e:
        logger.error(f"Error initializing system metrics: {e}", exc_info=True)


def get_system_metrics():
    """
    Get or create system health metrics
    
    Returns:
        Tuple of (uptime, memory_usage, memory_percent, cpu_usage, disk_usage, disk_percent)
    """
    if not settings.metrics.enabled:
        return None, None, None, None, None, None
    
    registry = get_metrics_registry()
    
    # System uptime gauge
    uptime = get_or_create_gauge(
        name="system_uptime_seconds",
        documentation="System uptime in seconds",
        registry=registry
    )
    
    # Memory usage gauge: type (rss, virtual, available, percent)
    memory_usage = get_or_create_gauge(
        name="system_memory_usage_bytes",
        documentation="System memory usage in bytes",
        labelnames=["type"],  # rss, virtual, available
        registry=registry
    )
    
    # Memory usage percent gauge
    memory_percent = get_or_create_gauge(
        name="system_memory_usage_percent",
        documentation="System memory usage percentage",
        registry=registry
    )
    
    # CPU usage gauge (percent)
    cpu_usage = get_or_create_gauge(
        name="system_cpu_usage_percent",
        documentation="System CPU usage percentage",
        registry=registry
    )
    
    # Disk usage gauge: device, mountpoint, type (used, free, total, percent)
    disk_usage = get_or_create_gauge(
        name="system_disk_usage_bytes",
        documentation="System disk usage in bytes",
        labelnames=["device", "mountpoint", "type"],  # used, free, total
        registry=registry
    )
    
    # Disk usage percent gauge
    disk_percent = get_or_create_gauge(
        name="system_disk_usage_percent",
        documentation="System disk usage percentage",
        labelnames=["device", "mountpoint"],
        registry=registry
    )
    
    return (uptime, memory_usage, memory_percent, cpu_usage, disk_usage, disk_percent)


def get_error_metrics():
    """
    Get or create error tracking metrics
    
    Returns:
        Tuple of (errors_total, exceptions_total, critical_errors_total)
    """
    if not settings.metrics.enabled:
        return None, None, None
    
    registry = get_metrics_registry()
    
    # Error counter: type, component
    errors_total = get_or_create_counter(
        name="errors_total",
        documentation="Total number of errors by type and component",
        labelnames=["type", "component"],
        registry=registry
    )
    
    # Exception counter: exception_type, component
    exceptions_total = get_or_create_counter(
        name="exceptions_total",
        documentation="Total number of exceptions by type and component",
        labelnames=["exception_type", "component"],
        registry=registry
    )
    
    # Critical errors counter: component
    critical_errors_total = get_or_create_counter(
        name="critical_errors_total",
        documentation="Total number of critical errors by component",
        labelnames=["component"],
        registry=registry
    )
    
    return errors_total, exceptions_total, critical_errors_total


def get_database_metrics():
    """
    Get or create database performance metrics
    
    Returns:
        Tuple of (query_duration, query_count, connection_pool_usage, transaction_count)
    """
    if not settings.metrics.enabled:
        return None, None, None, None
    
    registry = get_metrics_registry()
    
    # Query duration histogram: query_type
    query_duration = get_or_create_histogram(
        name="database_query_duration_seconds",
        documentation="Database query duration by query type",
        labelnames=["query_type"],
        buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
        registry=registry
    )
    
    # Query count counter: query_type
    query_count = get_or_create_counter(
        name="database_queries_total",
        documentation="Total number of database queries by type",
        labelnames=["query_type"],
        registry=registry
    )
    
    # Connection pool usage gauge
    connection_pool_usage = get_or_create_gauge(
        name="database_connection_pool_usage",
        documentation="Database connection pool usage (connections in use / pool size)",
        labelnames=["pool"],  # default, etc.
        registry=registry
    )
    
    # Transaction count counter: status
    transaction_count = get_or_create_counter(
        name="database_transactions_total",
        documentation="Total number of database transactions by status",
        labelnames=["status"],  # committed, rolled_back, failed
        registry=registry
    )
    
    return query_duration, query_count, connection_pool_usage, transaction_count


def update_system_metrics():
    """
    Update system health metrics (uptime, memory, CPU, disk)
    
    This should be called periodically (e.g., every 10-30 seconds)
    """
    if not settings.metrics.enabled:
        return
    
    try:
        uptime, memory_usage, memory_percent, cpu_usage, disk_usage, disk_percent = get_system_metrics()
        
        # Update uptime
        if uptime:
            start_time = get_app_start_time()
            uptime_seconds = time.time() - start_time
            uptime.set(uptime_seconds)
        
        if not PSUTIL_AVAILABLE:
            logger.debug("psutil not available, skipping resource metrics")
            return
        
        # Memory metrics
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        
        # System-wide memory
        sys_mem = psutil.virtual_memory()
        
        if memory_usage:
            # Process memory
            memory_usage.labels(type="rss").set(mem_info.rss)
            memory_usage.labels(type="vms").set(mem_info.vms)
            # System memory
            memory_usage.labels(type="available").set(sys_mem.available)
            memory_usage.labels(type="total").set(sys_mem.total)
            memory_usage.labels(type="used").set(sys_mem.used)
            memory_usage.labels(type="free").set(sys_mem.free)
        
        if memory_percent:
            memory_percent.set(sys_mem.percent)
        
        # CPU metrics
        if cpu_usage:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_usage.set(cpu_percent)
        
        # Disk metrics
        if disk_usage or disk_percent:
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    device = partition.device
                    mountpoint = partition.mountpoint
                    
                    if disk_usage:
                        disk_usage.labels(device=device, mountpoint=mountpoint, type="used").set(usage.used)
                        disk_usage.labels(device=device, mountpoint=mountpoint, type="free").set(usage.free)
                        disk_usage.labels(device=device, mountpoint=mountpoint, type="total").set(usage.total)
                    
                    if disk_percent:
                        disk_percent.labels(device=device, mountpoint=mountpoint).set(usage.percent)
                except PermissionError:
                    # Skip partitions we can't access
                    continue
                except Exception as e:
                    logger.debug(f"Error getting disk usage for {partition.mountpoint}: {e}")
                    
    except Exception as e:
        logger.warning(f"Error updating system metrics: {e}")


def record_error(error_type: str, component: str, is_critical: bool = False):
    """
    Record an error
    
    Args:
        error_type: Type of error (e.g., "validation_error", "api_error", "timeout")
        component: Component where error occurred (e.g., "api", "strategy", "provider")
        is_critical: Whether this is a critical error
    """
    errors_total, exceptions_total, critical_errors_total = get_error_metrics()
    
    if errors_total:
        try:
            errors_total.labels(type=error_type, component=component).inc()
        except Exception as e:
            logger.warning(f"Error recording error metric: {e}")
    
    if is_critical and critical_errors_total:
        try:
            critical_errors_total.labels(component=component).inc()
        except Exception as e:
            logger.warning(f"Error recording critical error metric: {e}")


def record_exception(exception_type: str, component: str, is_critical: bool = False):
    """
    Record an exception
    
    Args:
        exception_type: Exception class name (e.g., "ValueError", "ConnectionError")
        component: Component where exception occurred
        is_critical: Whether this is a critical exception
    """
    _, exceptions_total, critical_errors_total = get_error_metrics()
    
    if exceptions_total:
        try:
            exceptions_total.labels(exception_type=exception_type, component=component).inc()
        except Exception as e:
            logger.warning(f"Error recording exception metric: {e}")
    
    if is_critical and critical_errors_total:
        try:
            critical_errors_total.labels(component=component).inc()
        except Exception as e:
            logger.warning(f"Error recording critical exception metric: {e}")


def record_database_query(query_type: str, duration: float):
    """
    Record a database query
    
    Args:
        query_type: Type of query (e.g., "select", "insert", "update", "delete")
        duration: Query duration in seconds
    """
    query_duration, query_count, _, _ = get_database_metrics()
    
    if query_duration:
        try:
            query_duration.labels(query_type=query_type).observe(duration)
        except Exception as e:
            logger.warning(f"Error recording query duration metric: {e}")
    
    if query_count:
        try:
            query_count.labels(query_type=query_type).inc()
        except Exception as e:
            logger.warning(f"Error recording query count metric: {e}")


def update_connection_pool_usage(pool_name: str, in_use: int, pool_size: int):
    """
    Update database connection pool usage
    
    Args:
        pool_name: Pool identifier
        in_use: Number of connections in use
        pool_size: Total pool size
    """
    _, _, connection_pool_usage, _ = get_database_metrics()
    
    if connection_pool_usage and pool_size > 0:
        try:
            usage_percent = (in_use / pool_size) * 100
            connection_pool_usage.labels(pool=pool_name).set(usage_percent)
        except Exception as e:
            logger.warning(f"Error updating connection pool usage metric: {e}")


def record_transaction(status: str):
    """
    Record a database transaction
    
    Args:
        status: Transaction status ("committed", "rolled_back", "failed")
    """
    _, _, _, transaction_count = get_database_metrics()
    
    if transaction_count:
        try:
            transaction_count.labels(status=status).inc()
        except Exception as e:
            logger.warning(f"Error recording transaction metric: {e}")


def get_redis_metrics():
    """
    Get or create Redis performance metrics
    
    Returns:
        Tuple of (latency_histogram, hit_rate_gauge, operations_counter)
    """
    if not settings.metrics.enabled:
        return None, None, None
    
    registry = get_metrics_registry()
    
    # Redis latency histogram: operation_type
    latency = get_or_create_histogram(
        name="redis_latency_seconds",
        documentation="Redis operation latency by operation type",
        labelnames=["operation"],  # get, set, delete, exists, etc.
        buckets=(0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
        registry=registry
    )
    
    # Redis hit rate gauge
    hit_rate = get_or_create_gauge(
        name="redis_hit_rate",
        documentation="Redis cache hit rate (0.0 to 1.0)",
        registry=registry
    )
    
    # Redis operations counter: operation_type, status
    operations = get_or_create_counter(
        name="redis_operations_total",
        documentation="Total number of Redis operations by type and status",
        labelnames=["operation", "status"],  # status: success, error
        registry=registry
    )
    
    return latency, hit_rate, operations


def record_redis_operation(operation: str, duration: float, success: bool = True):
    """
    Record a Redis operation
    
    Args:
        operation: Operation type (e.g., "get", "set", "delete")
        duration: Operation duration in seconds
        success: Whether operation was successful
    """
    latency, _, operations = get_redis_metrics()
    
    if latency:
        try:
            latency.labels(operation=operation).observe(duration)
        except Exception as e:
            logger.debug(f"Error recording Redis latency metric: {e}")
    
    if operations:
        try:
            status = "success" if success else "error"
            operations.labels(operation=operation, status=status).inc()
        except Exception as e:
            logger.debug(f"Error recording Redis operation metric: {e}")


def update_redis_hit_rate(hit_rate: float):
    """
    Update Redis cache hit rate
    
    Args:
        hit_rate: Cache hit rate (0.0 to 1.0)
    """
    _, hit_rate_gauge, _ = get_redis_metrics()
    
    if hit_rate_gauge:
        try:
            hit_rate_gauge.set(hit_rate)
        except Exception as e:
            logger.debug(f"Error updating Redis hit rate metric: {e}")

