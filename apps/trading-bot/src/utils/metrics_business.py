"""
Business Metrics Utilities
===========================

Business and financial metrics for Prometheus.
Tracks portfolio P/L, daily/monthly performance, and risk metrics.
"""

import logging
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


def get_portfolio_metrics():
    """
    Get or create portfolio metrics
    
    Returns:
        Tuple of (total_pnl, daily_pnl, monthly_pnl, portfolio_value)
    """
    if not settings.metrics.enabled:
        return None, None, None, None
    
    registry = get_metrics_registry()
    
    # Total portfolio P/L gauge
    total_pnl = get_or_create_gauge(
        name="portfolio_total_pnl",
        documentation="Total portfolio profit/loss",
        registry=registry
    )
    
    # Daily P/L gauge
    daily_pnl = get_or_create_gauge(
        name="portfolio_daily_pnl",
        documentation="Daily portfolio profit/loss",
        registry=registry
    )
    
    # Monthly P/L gauge
    monthly_pnl = get_or_create_gauge(
        name="portfolio_monthly_pnl",
        documentation="Monthly portfolio profit/loss",
        registry=registry
    )
    
    # Portfolio total value gauge
    portfolio_value = get_or_create_gauge(
        name="portfolio_total_value",
        documentation="Total portfolio value",
        registry=registry
    )
    
    return total_pnl, daily_pnl, monthly_pnl, portfolio_value


def get_risk_metrics():
    """
    Get or create risk management metrics
    
    Returns:
        Tuple of (max_drawdown, daily_loss_limit, position_size_limit, risk_per_trade)
    """
    if not settings.metrics.enabled:
        return None, None, None, None
    
    registry = get_metrics_registry()
    
    # Maximum drawdown gauge
    max_drawdown = get_or_create_gauge(
        name="risk_max_drawdown",
        documentation="Maximum drawdown percentage",
        registry=registry
    )
    
    # Daily loss limit gauge
    daily_loss_limit = get_or_create_gauge(
        name="risk_daily_loss_limit",
        documentation="Daily loss limit (absolute value)",
        registry=registry
    )
    
    # Position size limit gauge
    position_size_limit = get_or_create_gauge(
        name="risk_position_size_limit",
        documentation="Maximum position size",
        registry=registry
    )
    
    # Risk per trade gauge
    risk_per_trade = get_or_create_gauge(
        name="risk_per_trade",
        documentation="Maximum risk per trade",
        registry=registry
    )
    
    return max_drawdown, daily_loss_limit, position_size_limit, risk_per_trade


def update_portfolio_pnl(total_pnl: float, daily_pnl: Optional[float] = None, 
                        monthly_pnl: Optional[float] = None):
    """
    Update portfolio P/L metrics
    
    Args:
        total_pnl: Total portfolio profit/loss
        daily_pnl: Daily P/L (optional)
        monthly_pnl: Monthly P/L (optional)
    """
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
    """
    Update portfolio total value
    
    Args:
        total_value: Total portfolio value
    """
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
    """
    Update risk management metrics
    
    Args:
        max_drawdown: Maximum drawdown percentage
        daily_loss_limit: Daily loss limit
        position_size_limit: Maximum position size
        risk_per_trade: Maximum risk per trade
    """
    max_dd, daily_limit, pos_limit, risk_trade = get_risk_metrics()
    
    if max_drawdown is not None and max_dd:
        try:
            max_dd.set(max_drawdown)
        except Exception as e:
            logger.debug(f"Error updating max drawdown metric: {e}")
    
    if daily_loss_limit is not None and daily_limit:
        try:
            daily_limit.set(daily_loss_limit)
        except Exception as e:
            logger.debug(f"Error updating daily loss limit metric: {e}")
    
    if position_size_limit is not None and pos_limit:
        try:
            pos_limit.set(position_size_limit)
        except Exception as e:
            logger.debug(f"Error updating position size limit metric: {e}")
    
    if risk_per_trade is not None and risk_trade:
        try:
            risk_trade.set(risk_per_trade)
        except Exception as e:
            logger.debug(f"Error updating risk per trade metric: {e}")

