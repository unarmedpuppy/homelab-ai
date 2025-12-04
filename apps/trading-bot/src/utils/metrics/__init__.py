"""
Metrics Package
===============

Centralized Prometheus metrics for the trading bot.

Usage:
    from src.utils.metrics import record_trade_executed, update_position_metrics

    # Record a trade
    record_trade_executed("momentum", "AAPL", "BUY")

    # Update position
    update_position_metrics("AAPL", 100, 150.50)
"""

# Core registry functions
from .registry import (
    get_metrics_registry,
    get_or_create_counter,
    get_or_create_histogram,
    get_or_create_gauge,
    generate_metrics_output,
    get_metrics_content_type,
    validate_metric_name,
    validate_label_names,
    normalize_metric_name,
    track_duration,
    track_call_count,
    track_duration_context,
)

# Trading metrics
from .collectors import (
    record_trade_executed,
    record_trade_rejected,
    record_execution_duration,
    record_order_fill_time,
    record_slippage,
    update_position_metrics,
    update_broker_connection_status,
    record_strategy_evaluation,
    record_signal_generated,
    update_strategy_win_rate,
    get_trade_metrics,
    get_position_metrics,
    get_strategy_metrics,
)

# Provider metrics
from .collectors import (
    record_provider_request,
    record_provider_response_time,
    record_provider_error,
    record_rate_limit_hit,
    update_cache_hit_rate,
    update_provider_availability,
    update_data_freshness,
    update_provider_uptime,
    track_rate_limit_hit,
    track_cache_freshness,
    track_provider_availability,
    track_provider_call,
    get_provider_metrics,
)

# System metrics
from .collectors import (
    initialize_system_metrics,
    update_system_metrics,
    record_error,
    record_exception,
    record_database_query,
    update_connection_pool_usage,
    record_transaction,
    record_redis_operation,
    update_redis_hit_rate,
    get_app_start_time,
    get_system_metrics,
    get_error_metrics,
    get_database_metrics,
    get_redis_metrics,
)

# Business metrics
from .collectors import (
    update_portfolio_pnl,
    update_portfolio_value,
    update_risk_metrics,
    get_portfolio_metrics,
    get_risk_metrics,
)

# Integration helpers
from .collectors import (
    update_portfolio_metrics_from_positions,
    calculate_and_update_strategy_win_rate,
    update_risk_metrics_from_config,
    calculate_drawdown,
    update_cache_hit_rates_from_monitor,
)

# Portfolio Risk metrics (T17: Risk Manager Agent)
from .collectors import (
    get_portfolio_risk_metrics,
    record_portfolio_risk_check,
    record_portfolio_risk_score,
    update_circuit_breaker_status,
    update_market_regime,
    update_position_concentration,
    update_sector_exposure,
    record_portfolio_risk_decision,
    record_portfolio_risk_evaluation,
)

# Execution metrics (T10: Strategy-to-Execution Pipeline)
from .collectors import (
    get_execution_metrics,
    record_execution_outcome,
    record_execution_duration,
    record_risk_rejection,
    update_execution_success_rate,
)

__all__ = [
    # Registry
    "get_metrics_registry",
    "get_or_create_counter",
    "get_or_create_histogram",
    "get_or_create_gauge",
    "generate_metrics_output",
    "get_metrics_content_type",
    "validate_metric_name",
    "validate_label_names",
    "normalize_metric_name",
    "track_duration",
    "track_call_count",
    "track_duration_context",
    # Trading
    "record_trade_executed",
    "record_trade_rejected",
    "record_execution_duration",
    "record_order_fill_time",
    "record_slippage",
    "update_position_metrics",
    "update_broker_connection_status",
    "record_strategy_evaluation",
    "record_signal_generated",
    "update_strategy_win_rate",
    "get_trade_metrics",
    "get_position_metrics",
    "get_strategy_metrics",
    # Providers
    "record_provider_request",
    "record_provider_response_time",
    "record_provider_error",
    "record_rate_limit_hit",
    "update_cache_hit_rate",
    "update_provider_availability",
    "update_data_freshness",
    "update_provider_uptime",
    "track_rate_limit_hit",
    "track_cache_freshness",
    "track_provider_availability",
    "track_provider_call",
    "get_provider_metrics",
    # System
    "initialize_system_metrics",
    "update_system_metrics",
    "record_error",
    "record_exception",
    "record_database_query",
    "update_connection_pool_usage",
    "record_transaction",
    "record_redis_operation",
    "update_redis_hit_rate",
    "get_app_start_time",
    "get_system_metrics",
    "get_error_metrics",
    "get_database_metrics",
    "get_redis_metrics",
    # Business
    "update_portfolio_pnl",
    "update_portfolio_value",
    "update_risk_metrics",
    "get_portfolio_metrics",
    "get_risk_metrics",
    # Integration
    "update_portfolio_metrics_from_positions",
    "calculate_and_update_strategy_win_rate",
    "update_risk_metrics_from_config",
    "calculate_drawdown",
    "update_cache_hit_rates_from_monitor",
    # Portfolio Risk (T17)
    "get_portfolio_risk_metrics",
    "record_portfolio_risk_check",
    "record_portfolio_risk_score",
    "update_circuit_breaker_status",
    "update_market_regime",
    "update_position_concentration",
    "update_sector_exposure",
    "record_portfolio_risk_decision",
    "record_portfolio_risk_evaluation",
    # Execution (T10)
    "get_execution_metrics",
    "record_execution_outcome",
    "record_execution_duration",
    "record_risk_rejection",
    "update_execution_success_rate",
]
