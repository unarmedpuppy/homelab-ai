# Utils package

from .cache import CacheManager, get_cache_manager, cached, cache_key
from .rate_limiter import RateLimiter, RateLimitStatus, get_rate_limiter
from .monitoring import UsageMonitor, SourceMetrics, get_usage_monitor
from .metrics import (
    get_metrics_registry,
    get_or_create_counter,
    get_or_create_histogram,
    get_or_create_gauge,
    generate_metrics_output,
    get_metrics_content_type,
    validate_metric_name,
    validate_label_names,
    normalize_metric_name
)
from .metrics_trading import (
    record_trade_executed,
    record_trade_rejected,
    record_execution_duration,
    record_order_fill_time,
    record_slippage,
    update_position_metrics,
    update_broker_connection_status,
    record_strategy_evaluation,
    record_signal_generated,
    update_strategy_win_rate
)
from .metrics_providers import (
    record_provider_request,
    record_provider_response_time,
    record_provider_error,
    record_rate_limit_hit,
    update_cache_hit_rate,
    update_provider_availability,
    update_data_freshness,
    update_provider_uptime
)
from .metrics_business import (
    update_portfolio_pnl,
    update_portfolio_value,
    update_risk_metrics
)
from .metrics_integration import (
    update_portfolio_metrics_from_positions,
    calculate_and_update_strategy_win_rate,
    update_risk_metrics_from_config,
    calculate_drawdown,
    update_cache_hit_rates_from_monitor
)

__all__ = [
    "CacheManager",
    "get_cache_manager",
    "cached",
    "cache_key",
    "RateLimiter",
    "RateLimitStatus",
    "get_rate_limiter",
    "UsageMonitor",
    "SourceMetrics",
    "get_usage_monitor",
    "get_metrics_registry",
    "get_or_create_counter",
    "get_or_create_histogram",
    "get_or_create_gauge",
    "generate_metrics_output",
    "get_metrics_content_type",
    "validate_metric_name",
    "validate_label_names",
    "normalize_metric_name",
    # Trading metrics
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
    # Provider metrics
    "record_provider_request",
    "record_provider_response_time",
    "record_provider_error",
    "record_rate_limit_hit",
    "update_cache_hit_rate",
    "update_provider_availability",
    "update_data_freshness",
    "update_provider_uptime",
    # Business metrics
    "update_portfolio_pnl",
    "update_portfolio_value",
    "update_risk_metrics",
    # Metrics integration
    "update_portfolio_metrics_from_positions",
    "calculate_and_update_strategy_win_rate",
    "update_risk_metrics_from_config",
    "calculate_drawdown",
    "update_cache_hit_rates_from_monitor",
]
