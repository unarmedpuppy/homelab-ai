"""
Trading Metrics Utilities
=========================

Trading-specific metrics helpers for Prometheus.
Tracks trade execution, strategy performance, and signal generation.
"""

import logging
import time
from typing import Optional
from datetime import datetime

from ..config.settings import settings
from .metrics import (
    get_or_create_counter,
    get_or_create_histogram,
    get_or_create_gauge,
    get_metrics_registry
)

logger = logging.getLogger(__name__)


def get_trade_metrics():
    """
    Get or create trading execution metrics
    
    Returns:
        Tuple of (trades_executed, trades_rejected, execution_duration, order_fill_time, slippage)
    """
    if not settings.metrics.enabled:
        return None, None, None, None, None
    
    registry = get_metrics_registry()
    
    # Trades executed counter: strategy, symbol, side
    trades_executed = get_or_create_counter(
        name="trades_executed_total",
        documentation="Total number of trades executed",
        labelnames=["strategy", "symbol", "side"],
        registry=registry
    )
    
    # Trades rejected counter: reason
    trades_rejected = get_or_create_counter(
        name="trades_rejected_total",
        documentation="Total number of trades rejected",
        labelnames=["reason"],
        registry=registry
    )
    
    # Trade execution duration histogram
    execution_duration = get_or_create_histogram(
        name="trade_execution_duration_seconds",
        documentation="Time to execute a trade (signal to order execution)",
        labelnames=["strategy", "symbol"],
        buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
        registry=registry
    )
    
    # Order fill time histogram
    order_fill_time = get_or_create_histogram(
        name="order_fill_time_seconds",
        documentation="Time from order placement to fill",
        labelnames=["symbol", "order_type"],
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
        registry=registry
    )
    
    # Slippage histogram (percentage)
    slippage = get_or_create_histogram(
        name="slippage_percent",
        documentation="Slippage percentage (actual vs expected price)",
        labelnames=["symbol", "side"],
        buckets=(-1.0, -0.5, -0.25, -0.1, 0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
        registry=registry
    )
    
    return trades_executed, trades_rejected, execution_duration, order_fill_time, slippage


def get_position_metrics():
    """
    Get or create position tracking metrics
    
    Returns:
        Tuple of (open_positions, position_pnl, broker_connection_status)
    """
    if not settings.metrics.enabled:
        return None, None, None
    
    registry = get_metrics_registry()
    
    # Open positions gauge: symbol
    open_positions = get_or_create_gauge(
        name="open_positions",
        documentation="Number of open positions",
        labelnames=["symbol"],
        registry=registry
    )
    
    # Position P/L gauge: symbol
    position_pnl = get_or_create_gauge(
        name="position_pnl",
        documentation="Current unrealized P/L per position",
        labelnames=["symbol"],
        registry=registry
    )
    
    # Broker connection status gauge
    broker_connection_status = get_or_create_gauge(
        name="broker_connection_status",
        documentation="Broker connection status (1=connected, 0=disconnected)",
        registry=registry
    )
    
    return open_positions, position_pnl, broker_connection_status


def get_strategy_metrics():
    """
    Get or create strategy evaluation metrics
    
    Returns:
        Tuple of (evaluation_duration, signals_generated, signal_confidence, strategy_win_rate)
    """
    if not settings.metrics.enabled:
        return None, None, None, None
    
    registry = get_metrics_registry()
    
    # Strategy evaluation duration histogram
    evaluation_duration = get_or_create_histogram(
        name="strategy_evaluation_duration_seconds",
        documentation="Time to evaluate a strategy",
        labelnames=["strategy"],
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
        registry=registry
    )
    
    # Signals generated counter: strategy, type, symbol
    signals_generated = get_or_create_counter(
        name="signals_generated_total",
        documentation="Total number of trading signals generated",
        labelnames=["strategy", "type", "symbol"],
        registry=registry
    )
    
    # Signal confidence histogram
    signal_confidence = get_or_create_histogram(
        name="signal_confidence",
        documentation="Signal confidence scores",
        labelnames=["strategy", "type"],
        buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
        registry=registry
    )
    
    # Strategy win rate gauge
    strategy_win_rate = get_or_create_gauge(
        name="strategy_win_rate",
        documentation="Win rate for each strategy",
        labelnames=["strategy"],
        registry=registry
    )
    
    return evaluation_duration, signals_generated, signal_confidence, strategy_win_rate


def record_trade_executed(strategy: str, symbol: str, side: str):
    """
    Record a trade execution
    
    Args:
        strategy: Strategy name
        symbol: Stock symbol
        side: Trade side (BUY/SELL)
    """
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
    """
    Record a rejected trade
    
    Args:
        reason: Reason for rejection (e.g., "risk_limit", "insufficient_funds", "invalid_signal")
    """
    _, trades_rejected, _, _, _ = get_trade_metrics()
    if trades_rejected:
        try:
            trades_rejected.labels(reason=reason).inc()
        except Exception as e:
            logger.warning(f"Error recording trade rejection metric: {e}")


def record_execution_duration(strategy: str, symbol: str, duration: float):
    """
    Record trade execution duration
    
    Args:
        strategy: Strategy name
        symbol: Stock symbol
        duration: Duration in seconds
    """
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
    """
    Record order fill time
    
    Args:
        symbol: Stock symbol
        order_type: Order type (MARKET, LIMIT, etc.)
        fill_time: Fill time in seconds
    """
    _, _, _, order_fill_time, _ = get_trade_metrics()
    if order_fill_time:
        try:
            order_fill_time.labels(
                symbol=symbol,
                order_type=order_type
            ).observe(fill_time)
        except Exception as e:
            logger.warning(f"Error recording order fill time metric: {e}")


def record_slippage(symbol: str, side: str, slippage_pct: float):
    """
    Record slippage
    
    Args:
        symbol: Stock symbol
        side: Trade side (BUY/SELL)
        slippage_pct: Slippage as percentage (positive or negative)
    """
    _, _, _, _, slippage = get_trade_metrics()
    if slippage:
        try:
            slippage.labels(
                symbol=symbol,
                side=side
            ).observe(slippage_pct)
        except Exception as e:
            logger.warning(f"Error recording slippage metric: {e}")


def update_position_metrics(symbol: str, quantity: int, pnl: float):
    """
    Update position metrics
    
    Args:
        symbol: Stock symbol
        quantity: Position quantity (0 to clear position)
        pnl: Current unrealized P/L
    """
    open_positions, position_pnl, _ = get_position_metrics()
    if open_positions and position_pnl:
        try:
            open_positions.labels(symbol=symbol).set(abs(quantity))
            if quantity != 0:
                position_pnl.labels(symbol=symbol).set(pnl)
            else:
                # Clear position when quantity is 0
                position_pnl.labels(symbol=symbol).set(0)
        except Exception as e:
            logger.warning(f"Error updating position metrics: {e}")


def update_broker_connection_status(connected: bool):
    """
    Update broker connection status
    
    Args:
        connected: Whether broker is connected
    """
    _, _, broker_connection_status = get_position_metrics()
    if broker_connection_status:
        try:
            broker_connection_status.set(1 if connected else 0)
        except Exception as e:
            logger.warning(f"Error updating broker connection status metric: {e}")


def record_strategy_evaluation(strategy: str, duration: float):
    """
    Record strategy evaluation duration
    
    Args:
        strategy: Strategy name
        duration: Evaluation duration in seconds
    """
    evaluation_duration, _, _, _ = get_strategy_metrics()
    if evaluation_duration:
        try:
            evaluation_duration.labels(strategy=strategy).observe(duration)
        except Exception as e:
            logger.warning(f"Error recording strategy evaluation metric: {e}")


def record_signal_generated(strategy: str, signal_type: str, symbol: str, confidence: float):
    """
    Record a generated signal
    
    Args:
        strategy: Strategy name
        signal_type: Signal type (BUY, SELL, HOLD)
        symbol: Stock symbol
        confidence: Signal confidence (0.0 to 1.0)
    """
    _, signals_generated, signal_confidence, _ = get_strategy_metrics()
    if signals_generated and signal_confidence:
        try:
            signals_generated.labels(
                strategy=strategy,
                type=signal_type,
                symbol=symbol
            ).inc()
            
            signal_confidence.labels(
                strategy=strategy,
                type=signal_type
            ).observe(confidence)
        except Exception as e:
            logger.warning(f"Error recording signal metric: {e}")


def update_strategy_win_rate(strategy: str, win_rate: float):
    """
    Update strategy win rate
    
    Args:
        strategy: Strategy name
        win_rate: Win rate (0.0 to 1.0)
    """
    _, _, _, strategy_win_rate = get_strategy_metrics()
    if strategy_win_rate:
        try:
            strategy_win_rate.labels(strategy=strategy).set(win_rate)
        except Exception as e:
            logger.warning(f"Error updating strategy win rate metric: {e}")
