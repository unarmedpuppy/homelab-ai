"""
Metrics Collectors
==================

All metric definitions and recording functions organized by domain:
- Trading: trades, positions, strategies, signals
- Providers: API calls, cache, rate limits, availability
- System: health, errors, database, Redis
- Business: portfolio P&L, risk metrics
"""

import logging
import time
import os
from typing import Optional, Dict, List, Any
from datetime import datetime

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

from .registry import (
    get_or_create_counter,
    get_or_create_histogram,
    get_or_create_gauge,
    get_metrics_registry
)

logger = logging.getLogger(__name__)

# Lazy import settings to avoid circular imports
_settings = None


def _get_settings():
    global _settings
    if _settings is None:
        from ...config.settings import settings
        _settings = settings
    return _settings


def _metrics_enabled() -> bool:
    try:
        return _get_settings().metrics.enabled
    except Exception:
        return False


# =============================================================================
# Trading Metrics
# =============================================================================


def get_trade_metrics():
    """Get or create trading execution metrics."""
    if not _metrics_enabled():
        return None, None, None, None, None

    registry = get_metrics_registry()

    trades_executed = get_or_create_counter(
        name="trades_executed_total",
        documentation="Total number of trades executed",
        labelnames=["strategy", "symbol", "side"],
        registry=registry
    )

    trades_rejected = get_or_create_counter(
        name="trades_rejected_total",
        documentation="Total number of trades rejected",
        labelnames=["reason"],
        registry=registry
    )

    execution_duration = get_or_create_histogram(
        name="trade_execution_duration_seconds",
        documentation="Time to execute a trade (signal to order execution)",
        labelnames=["strategy", "symbol"],
        buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
        registry=registry
    )

    order_fill_time = get_or_create_histogram(
        name="order_fill_time_seconds",
        documentation="Time from order placement to fill",
        labelnames=["symbol", "order_type"],
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
        registry=registry
    )

    slippage = get_or_create_histogram(
        name="slippage_percent",
        documentation="Slippage percentage (actual vs expected price)",
        labelnames=["symbol", "side"],
        buckets=(-1.0, -0.5, -0.25, -0.1, 0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
        registry=registry
    )

    return trades_executed, trades_rejected, execution_duration, order_fill_time, slippage


def get_position_metrics():
    """Get or create position tracking metrics."""
    if not _metrics_enabled():
        return None, None, None

    registry = get_metrics_registry()

    open_positions = get_or_create_gauge(
        name="open_positions",
        documentation="Number of open positions",
        labelnames=["symbol"],
        registry=registry
    )

    position_pnl = get_or_create_gauge(
        name="position_pnl",
        documentation="Current unrealized P/L per position",
        labelnames=["symbol"],
        registry=registry
    )

    broker_connection_status = get_or_create_gauge(
        name="broker_connection_status",
        documentation="Broker connection status (1=connected, 0=disconnected)",
        registry=registry
    )

    return open_positions, position_pnl, broker_connection_status


def get_strategy_metrics():
    """Get or create strategy evaluation metrics."""
    if not _metrics_enabled():
        return None, None, None, None

    registry = get_metrics_registry()

    evaluation_duration = get_or_create_histogram(
        name="strategy_evaluation_duration_seconds",
        documentation="Time to evaluate a strategy",
        labelnames=["strategy"],
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        registry=registry
    )

    signals_generated = get_or_create_counter(
        name="signals_generated_total",
        documentation="Total number of trading signals generated",
        labelnames=["strategy", "type", "symbol"],
        registry=registry
    )

    signal_confidence = get_or_create_histogram(
        name="signal_confidence",
        documentation="Signal confidence scores",
        labelnames=["strategy", "type"],
        buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
        registry=registry
    )

    strategy_win_rate = get_or_create_gauge(
        name="strategy_win_rate",
        documentation="Win rate for each strategy",
        labelnames=["strategy"],
        registry=registry
    )

    return evaluation_duration, signals_generated, signal_confidence, strategy_win_rate


def record_trade_executed(strategy: str, symbol: str, side: str):
    """Record a trade execution."""
    trades_executed, _, _, _, _ = get_trade_metrics()
    if trades_executed:
        try:
            trades_executed.labels(
                strategy=strategy or "unknown",
                symbol=symbol,
                side=side
            ).inc()
        except Exception as e:
            logger.warning(f"Error recording trade execution metric: {e}")


def record_trade_rejected(reason: str):
    """Record a rejected trade."""
    _, trades_rejected, _, _, _ = get_trade_metrics()
    if trades_rejected:
        try:
            trades_rejected.labels(reason=reason).inc()
        except Exception as e:
            logger.warning(f"Error recording trade rejection metric: {e}")


def record_execution_duration(strategy: str, symbol: str, duration: float):
    """Record trade execution duration."""
    _, _, execution_duration, _, _ = get_trade_metrics()
    if execution_duration:
        try:
            execution_duration.labels(
                strategy=strategy or "unknown",
                symbol=symbol
            ).observe(duration)
        except Exception as e:
            logger.warning(f"Error recording execution duration metric: {e}")


def record_order_fill_time(symbol: str, order_type: str, fill_time: float):
    """Record order fill time."""
    _, _, _, order_fill_time, _ = get_trade_metrics()
    if order_fill_time:
        try:
            order_fill_time.labels(symbol=symbol, order_type=order_type).observe(fill_time)
        except Exception as e:
            logger.warning(f"Error recording order fill time metric: {e}")


def record_slippage(symbol: str, side: str, slippage_pct: float):
    """Record slippage."""
    _, _, _, _, slippage = get_trade_metrics()
    if slippage:
        try:
            slippage.labels(symbol=symbol, side=side).observe(slippage_pct)
        except Exception as e:
            logger.warning(f"Error recording slippage metric: {e}")


def update_position_metrics(symbol: str, quantity: int, pnl: float):
    """Update position metrics."""
    open_positions, position_pnl, _ = get_position_metrics()
    if open_positions and position_pnl:
        try:
            open_positions.labels(symbol=symbol).set(abs(quantity))
            position_pnl.labels(symbol=symbol).set(pnl if quantity != 0 else 0)
        except Exception as e:
            logger.warning(f"Error updating position metrics: {e}")


def update_broker_connection_status(connected: bool):
    """Update broker connection status."""
    _, _, broker_connection_status = get_position_metrics()
    if broker_connection_status:
        try:
            broker_connection_status.set(1 if connected else 0)
        except Exception as e:
            logger.warning(f"Error updating broker connection status metric: {e}")


def record_strategy_evaluation(strategy: str, duration: float):
    """Record strategy evaluation duration."""
    evaluation_duration, _, _, _ = get_strategy_metrics()
    if evaluation_duration:
        try:
            evaluation_duration.labels(strategy=strategy).observe(duration)
        except Exception as e:
            logger.warning(f"Error recording strategy evaluation metric: {e}")


def record_signal_generated(strategy: str, signal_type: str, symbol: str, confidence: float):
    """Record a generated signal."""
    _, signals_generated, signal_confidence, _ = get_strategy_metrics()
    if signals_generated and signal_confidence:
        try:
            signals_generated.labels(strategy=strategy, type=signal_type, symbol=symbol).inc()
            signal_confidence.labels(strategy=strategy, type=signal_type).observe(confidence)
        except Exception as e:
            logger.warning(f"Error recording signal metric: {e}")


def update_strategy_win_rate(strategy: str, win_rate: float):
    """Update strategy win rate."""
    _, _, _, strategy_win_rate = get_strategy_metrics()
    if strategy_win_rate:
        try:
            strategy_win_rate.labels(strategy=strategy).set(win_rate)
        except Exception as e:
            logger.warning(f"Error updating strategy win rate metric: {e}")


# =============================================================================
# Provider Metrics
# =============================================================================


def get_provider_metrics():
    """Get or create data provider metrics."""
    if not _metrics_enabled():
        return None, None, None, None, None, None, None

    registry = get_metrics_registry()

    requests_total = get_or_create_counter(
        name="provider_requests_total",
        documentation="Total number of provider API requests",
        labelnames=["provider", "status"],
        registry=registry
    )

    response_time = get_or_create_histogram(
        name="provider_response_time_seconds",
        documentation="Provider API response time in seconds",
        labelnames=["provider"],
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
        registry=registry
    )

    errors_total = get_or_create_counter(
        name="provider_errors_total",
        documentation="Total number of provider errors",
        labelnames=["provider", "error_type"],
        registry=registry
    )

    rate_limit_hits = get_or_create_counter(
        name="provider_rate_limit_hits_total",
        documentation="Total number of rate limit hits",
        labelnames=["provider"],
        registry=registry
    )

    cache_hit_rate = get_or_create_gauge(
        name="provider_cache_hit_rate",
        documentation="Cache hit rate per provider (0.0 to 1.0)",
        labelnames=["provider"],
        registry=registry
    )

    provider_available = get_or_create_gauge(
        name="provider_available",
        documentation="Provider availability status (1=available, 0=unavailable)",
        labelnames=["provider"],
        registry=registry
    )

    data_freshness = get_or_create_gauge(
        name="provider_data_freshness_seconds",
        documentation="Age of cached data in seconds",
        labelnames=["provider", "endpoint"],
        registry=registry
    )

    return requests_total, response_time, errors_total, rate_limit_hits, cache_hit_rate, provider_available, data_freshness


def record_provider_request(provider: str, success: bool = True, cached: bool = False):
    """Record a provider API request."""
    requests_total, _, _, _, _, _, _ = get_provider_metrics()
    if requests_total:
        try:
            status = "cached" if cached else ("success" if success else "failure")
            requests_total.labels(provider=provider, status=status).inc()
        except Exception as e:
            logger.debug(f"Error recording provider request metric: {e}")


def record_provider_response_time(provider: str, response_time: float):
    """Record provider response time."""
    _, response_time_metric, _, _, _, _, _ = get_provider_metrics()
    if response_time_metric:
        try:
            response_time_metric.labels(provider=provider).observe(response_time)
        except Exception as e:
            logger.debug(f"Error recording provider response time metric: {e}")


def record_provider_error(provider: str, error_type: str):
    """Record a provider error."""
    _, _, errors_total, _, _, _, _ = get_provider_metrics()
    if errors_total:
        try:
            errors_total.labels(provider=provider, error_type=error_type).inc()
        except Exception as e:
            logger.debug(f"Error recording provider error metric: {e}")


def record_rate_limit_hit(provider: str):
    """Record a rate limit hit."""
    _, _, _, rate_limit_hits, _, _, _ = get_provider_metrics()
    if rate_limit_hits:
        try:
            rate_limit_hits.labels(provider=provider).inc()
        except Exception as e:
            logger.warning(f"Error recording rate limit hit metric: {e}")


def update_cache_hit_rate(provider: str, hit_rate: float):
    """Update cache hit rate for a provider."""
    _, _, _, _, cache_hit_rate, _, _ = get_provider_metrics()
    if cache_hit_rate:
        try:
            cache_hit_rate.labels(provider=provider).set(hit_rate)
        except Exception as e:
            logger.debug(f"Error updating cache hit rate metric: {e}")


def update_provider_availability(provider: str, available: bool):
    """Update provider availability status."""
    _, _, _, _, _, provider_available, _ = get_provider_metrics()
    if provider_available:
        try:
            provider_available.labels(provider=provider).set(1 if available else 0)
        except Exception as e:
            logger.warning(f"Error updating provider availability metric: {e}")


def update_data_freshness(provider: str, endpoint: str, age_seconds: float):
    """Update data freshness metric."""
    _, _, _, _, _, _, data_freshness = get_provider_metrics()
    if data_freshness:
        try:
            data_freshness.labels(provider=provider, endpoint=endpoint).set(age_seconds)
        except Exception as e:
            logger.warning(f"Error updating data freshness metric: {e}")


def update_provider_uptime(provider: str, seconds_since_last_success: float):
    """Update provider uptime metric (time since last successful call)."""
    # Uses availability gauge - reset to 0 on success
    update_provider_availability(provider, seconds_since_last_success == 0)


# Provider helpers for backward compatibility
def track_rate_limit_hit(provider: str):
    """Track rate limit hit for a provider (alias)."""
    record_rate_limit_hit(provider)


def track_cache_freshness(provider: str, endpoint: str, cached_data: Any):
    """Track data freshness when cache hit occurs."""
    try:
        if hasattr(cached_data, 'timestamp') and cached_data.timestamp:
            cache_age = (datetime.now() - cached_data.timestamp).total_seconds()
            update_data_freshness(provider, endpoint, cache_age)
    except Exception as e:
        logger.debug(f"Error recording cache freshness for {provider}: {e}")


def track_provider_availability(provider: str, is_available: bool):
    """Track provider availability status (alias)."""
    update_provider_availability(provider, is_available)


class track_provider_call:
    """Context manager for tracking provider API calls with automatic timing."""

    def __init__(self, provider: str, endpoint: str = "default"):
        self.provider = provider
        self.endpoint = endpoint
        self.start_time = None
        self.cache_hit = False

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time

        record_provider_response_time(self.provider, duration)
        record_provider_request(self.provider, success=(exc_type is None), cached=self.cache_hit)

        if exc_type is not None:
            error_type = "unknown_error"
            if "timeout" in str(exc_val).lower():
                error_type = "timeout"
            elif "rate limit" in str(exc_val).lower() or "429" in str(exc_val):
                error_type = "rate_limit"
                record_rate_limit_hit(self.provider)
            elif "connection" in str(exc_val).lower():
                error_type = "connection_error"
            record_provider_error(self.provider, error_type)
            update_provider_availability(self.provider, False)
        else:
            update_provider_availability(self.provider, True)

        return False

    def set_cache_hit(self, hit: bool):
        """Mark whether this call resulted in a cache hit."""
        self.cache_hit = hit


# =============================================================================
# System Metrics
# =============================================================================


_app_start_time: Optional[float] = None


def get_app_start_time() -> float:
    """Get application startup time."""
    global _app_start_time
    if _app_start_time is None:
        _app_start_time = time.time()
    return _app_start_time


def get_system_metrics():
    """Get or create system health metrics."""
    if not _metrics_enabled():
        return None, None, None, None, None, None

    registry = get_metrics_registry()

    uptime = get_or_create_gauge(
        name="system_uptime_seconds",
        documentation="System uptime in seconds",
        registry=registry
    )

    memory_usage = get_or_create_gauge(
        name="system_memory_usage_bytes",
        documentation="System memory usage in bytes",
        labelnames=["type"],
        registry=registry
    )

    memory_percent = get_or_create_gauge(
        name="system_memory_usage_percent",
        documentation="System memory usage percentage",
        registry=registry
    )

    cpu_usage = get_or_create_gauge(
        name="system_cpu_usage_percent",
        documentation="System CPU usage percentage",
        registry=registry
    )

    disk_usage = get_or_create_gauge(
        name="system_disk_usage_bytes",
        documentation="System disk usage in bytes",
        labelnames=["device", "mountpoint", "type"],
        registry=registry
    )

    disk_percent = get_or_create_gauge(
        name="system_disk_usage_percent",
        documentation="System disk usage percentage",
        labelnames=["device", "mountpoint"],
        registry=registry
    )

    return uptime, memory_usage, memory_percent, cpu_usage, disk_usage, disk_percent


def get_error_metrics():
    """Get or create error tracking metrics."""
    if not _metrics_enabled():
        return None, None, None

    registry = get_metrics_registry()

    errors_total = get_or_create_counter(
        name="errors_total",
        documentation="Total number of errors by type and component",
        labelnames=["type", "component"],
        registry=registry
    )

    exceptions_total = get_or_create_counter(
        name="exceptions_total",
        documentation="Total number of exceptions by type and component",
        labelnames=["exception_type", "component"],
        registry=registry
    )

    critical_errors_total = get_or_create_counter(
        name="critical_errors_total",
        documentation="Total number of critical errors by component",
        labelnames=["component"],
        registry=registry
    )

    return errors_total, exceptions_total, critical_errors_total


def get_database_metrics():
    """Get or create database performance metrics."""
    if not _metrics_enabled():
        return None, None, None, None

    registry = get_metrics_registry()

    query_duration = get_or_create_histogram(
        name="database_query_duration_seconds",
        documentation="Database query duration by query type",
        labelnames=["query_type"],
        buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
        registry=registry
    )

    query_count = get_or_create_counter(
        name="database_queries_total",
        documentation="Total number of database queries by type",
        labelnames=["query_type"],
        registry=registry
    )

    connection_pool_usage = get_or_create_gauge(
        name="database_connection_pool_usage",
        documentation="Database connection pool usage percentage",
        labelnames=["pool"],
        registry=registry
    )

    transaction_count = get_or_create_counter(
        name="database_transactions_total",
        documentation="Total number of database transactions by status",
        labelnames=["status"],
        registry=registry
    )

    return query_duration, query_count, connection_pool_usage, transaction_count


def get_redis_metrics():
    """Get or create Redis performance metrics."""
    if not _metrics_enabled():
        return None, None, None

    registry = get_metrics_registry()

    latency = get_or_create_histogram(
        name="redis_latency_seconds",
        documentation="Redis operation latency by operation type",
        labelnames=["operation"],
        buckets=(0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
        registry=registry
    )

    hit_rate = get_or_create_gauge(
        name="redis_hit_rate",
        documentation="Redis cache hit rate (0.0 to 1.0)",
        registry=registry
    )

    operations = get_or_create_counter(
        name="redis_operations_total",
        documentation="Total number of Redis operations by type and status",
        labelnames=["operation", "status"],
        registry=registry
    )

    return latency, hit_rate, operations


def initialize_system_metrics():
    """Initialize system health metrics (backward compat)."""
    if not _metrics_enabled():
        return
    get_app_start_time()
    logger.info("System metrics initialization completed")


def update_system_metrics():
    """Update system health metrics (uptime, memory, CPU, disk)."""
    if not _metrics_enabled():
        return

    try:
        uptime, memory_usage, memory_percent, cpu_usage, disk_usage, disk_percent = get_system_metrics()

        if uptime:
            uptime.set(time.time() - get_app_start_time())

        if not PSUTIL_AVAILABLE:
            return

        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        sys_mem = psutil.virtual_memory()

        if memory_usage:
            memory_usage.labels(type="rss").set(mem_info.rss)
            memory_usage.labels(type="vms").set(mem_info.vms)
            memory_usage.labels(type="available").set(sys_mem.available)
            memory_usage.labels(type="total").set(sys_mem.total)
            memory_usage.labels(type="used").set(sys_mem.used)

        if memory_percent:
            memory_percent.set(sys_mem.percent)

        if cpu_usage:
            cpu_usage.set(psutil.cpu_percent(interval=0.1))

        if disk_usage or disk_percent:
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    if disk_usage:
                        disk_usage.labels(device=partition.device, mountpoint=partition.mountpoint, type="used").set(usage.used)
                        disk_usage.labels(device=partition.device, mountpoint=partition.mountpoint, type="free").set(usage.free)
                    if disk_percent:
                        disk_percent.labels(device=partition.device, mountpoint=partition.mountpoint).set(usage.percent)
                except PermissionError:
                    continue

    except Exception as e:
        logger.warning(f"Error updating system metrics: {e}")


def record_error(error_type: str, component: str, is_critical: bool = False):
    """Record an error."""
    errors_total, _, critical_errors_total = get_error_metrics()

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
    """Record an exception."""
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
    """Record a database query."""
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
    """Update database connection pool usage."""
    _, _, connection_pool_usage, _ = get_database_metrics()

    if connection_pool_usage and pool_size > 0:
        try:
            connection_pool_usage.labels(pool=pool_name).set((in_use / pool_size) * 100)
        except Exception as e:
            logger.warning(f"Error updating connection pool usage metric: {e}")


def record_transaction(status: str):
    """Record a database transaction."""
    _, _, _, transaction_count = get_database_metrics()

    if transaction_count:
        try:
            transaction_count.labels(status=status).inc()
        except Exception as e:
            logger.warning(f"Error recording transaction metric: {e}")


def record_redis_operation(operation: str, duration: float, success: bool = True):
    """Record a Redis operation."""
    latency, _, operations = get_redis_metrics()

    if latency:
        try:
            latency.labels(operation=operation).observe(duration)
        except Exception as e:
            logger.debug(f"Error recording Redis latency metric: {e}")

    if operations:
        try:
            operations.labels(operation=operation, status="success" if success else "error").inc()
        except Exception as e:
            logger.debug(f"Error recording Redis operation metric: {e}")


def update_redis_hit_rate(hit_rate: float):
    """Update Redis cache hit rate."""
    _, hit_rate_gauge, _ = get_redis_metrics()

    if hit_rate_gauge:
        try:
            hit_rate_gauge.set(hit_rate)
        except Exception as e:
            logger.debug(f"Error updating Redis hit rate metric: {e}")


# =============================================================================
# Business Metrics
# =============================================================================


def get_portfolio_metrics():
    """Get or create portfolio metrics."""
    if not _metrics_enabled():
        return None, None, None, None

    registry = get_metrics_registry()

    total_pnl = get_or_create_gauge(
        name="portfolio_total_pnl",
        documentation="Total portfolio profit/loss",
        registry=registry
    )

    daily_pnl = get_or_create_gauge(
        name="portfolio_daily_pnl",
        documentation="Daily portfolio profit/loss",
        registry=registry
    )

    monthly_pnl = get_or_create_gauge(
        name="portfolio_monthly_pnl",
        documentation="Monthly portfolio profit/loss",
        registry=registry
    )

    portfolio_value = get_or_create_gauge(
        name="portfolio_total_value",
        documentation="Total portfolio value",
        registry=registry
    )

    return total_pnl, daily_pnl, monthly_pnl, portfolio_value


def get_risk_metrics():
    """Get or create risk management metrics."""
    if not _metrics_enabled():
        return None, None, None, None

    registry = get_metrics_registry()

    max_drawdown = get_or_create_gauge(
        name="risk_max_drawdown",
        documentation="Maximum drawdown percentage",
        registry=registry
    )

    daily_loss_limit = get_or_create_gauge(
        name="risk_daily_loss_limit",
        documentation="Daily loss limit (absolute value)",
        registry=registry
    )

    position_size_limit = get_or_create_gauge(
        name="risk_position_size_limit",
        documentation="Maximum position size",
        registry=registry
    )

    risk_per_trade = get_or_create_gauge(
        name="risk_per_trade",
        documentation="Maximum risk per trade",
        registry=registry
    )

    return max_drawdown, daily_loss_limit, position_size_limit, risk_per_trade


def update_portfolio_pnl(total_pnl: float, daily_pnl: Optional[float] = None,
                         monthly_pnl: Optional[float] = None):
    """Update portfolio P/L metrics."""
    total_pnl_gauge, daily_pnl_gauge, monthly_pnl_gauge, _ = get_portfolio_metrics()

    if total_pnl_gauge:
        try:
            total_pnl_gauge.set(total_pnl)
            if daily_pnl is not None and daily_pnl_gauge:
                daily_pnl_gauge.set(daily_pnl)
            if monthly_pnl is not None and monthly_pnl_gauge:
                monthly_pnl_gauge.set(monthly_pnl)
        except Exception as e:
            logger.warning(f"Error updating portfolio P/L metrics: {e}")


def update_portfolio_value(total_value: float):
    """Update portfolio total value."""
    _, _, _, portfolio_value = get_portfolio_metrics()

    if portfolio_value:
        try:
            portfolio_value.set(total_value)
        except Exception as e:
            logger.warning(f"Error updating portfolio value metric: {e}")


def update_risk_metrics(max_drawdown: Optional[float] = None,
                        daily_loss_limit: Optional[float] = None,
                        position_size_limit: Optional[float] = None,
                        risk_per_trade: Optional[float] = None):
    """Update risk management metrics."""
    max_dd, daily_limit, pos_limit, risk_trade = get_risk_metrics()

    try:
        if max_drawdown is not None and max_dd:
            max_dd.set(max_drawdown)
        if daily_loss_limit is not None and daily_limit:
            daily_limit.set(daily_loss_limit)
        if position_size_limit is not None and pos_limit:
            pos_limit.set(position_size_limit)
        if risk_per_trade is not None and risk_trade:
            risk_trade.set(risk_per_trade)
    except Exception as e:
        logger.debug(f"Error updating risk metrics: {e}")


# =============================================================================
# Integration Helpers
# =============================================================================


def update_portfolio_metrics_from_positions(positions: List[Dict], cash: float = 0.0):
    """Update portfolio metrics from a list of positions."""
    if not _metrics_enabled():
        return

    try:
        total_pnl = sum(pos.get('unrealized_pnl', 0) for pos in positions)
        portfolio_value = cash + sum(
            pos.get('market_price', 0) * pos.get('quantity', 0) for pos in positions
        )
        update_portfolio_pnl(total_pnl=total_pnl)
        update_portfolio_value(portfolio_value)
    except Exception as e:
        logger.debug(f"Error updating portfolio metrics from positions: {e}")


def calculate_and_update_strategy_win_rate(strategy_name: str, trades: List[Dict]) -> float:
    """Calculate win rate from trades and update metrics."""
    if not _metrics_enabled() or not trades:
        return 0.0

    try:
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        win_rate = len(winning_trades) / len(trades)
        update_strategy_win_rate(strategy_name, win_rate)
        return win_rate
    except Exception as e:
        logger.debug(f"Error calculating strategy win rate: {e}")
        return 0.0


def update_risk_metrics_from_config(
    max_drawdown: Optional[float] = None,
    daily_loss_limit: Optional[float] = None,
    position_size_limit: Optional[float] = None,
    risk_per_trade: Optional[float] = None
):
    """Update risk metrics from configuration values."""
    if not _metrics_enabled():
        return
    update_risk_metrics(max_drawdown, daily_loss_limit, position_size_limit, risk_per_trade)


def calculate_drawdown(equity_curve: List[float]) -> float:
    """Calculate maximum drawdown from equity curve."""
    if not equity_curve or len(equity_curve) < 2:
        return 0.0

    try:
        peak = equity_curve[0]
        max_drawdown = 0.0

        for value in equity_curve:
            if value > peak:
                peak = value
            drawdown = ((value - peak) / peak) * 100 if peak > 0 else 0.0
            if drawdown < max_drawdown:
                max_drawdown = drawdown

        return max_drawdown
    except Exception as e:
        logger.debug(f"Error calculating drawdown: {e}")
        return 0.0


def update_cache_hit_rates_from_monitor(monitor, providers: Optional[List[str]] = None):
    """Update cache hit rate metrics from UsageMonitor."""
    if not _metrics_enabled():
        return

    try:
        if providers is None:
            providers = list(monitor.source_metrics.keys())

        for provider in providers:
            metrics = monitor.get_source_metrics(provider)
            if metrics and hasattr(metrics, 'cache_hit_rate'):
                update_cache_hit_rate(provider, metrics.cache_hit_rate)
    except Exception as e:
        logger.debug(f"Error updating cache hit rates from monitor: {e}")
