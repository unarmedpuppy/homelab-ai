"""
Metrics Integration Utilities
=============================

Helper functions to integrate metrics collection into various components.
Provides high-level functions for common metric update patterns.
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime

from ..config.settings import settings
from .metrics_business import update_portfolio_pnl, update_portfolio_value, update_risk_metrics
from .metrics_trading import update_strategy_win_rate
from .metrics_providers import update_cache_hit_rate

logger = logging.getLogger(__name__)


def update_portfolio_metrics_from_positions(positions: List[Dict], cash: float = 0.0):
    """
    Update portfolio metrics from a list of positions
    
    Args:
        positions: List of position dicts with keys: symbol, quantity, market_price, unrealized_pnl
        cash: Available cash (optional)
    """
    if not settings.metrics.enabled:
        return
    
    try:
        # Calculate total P&L
        total_pnl = sum(pos.get('unrealized_pnl', 0) for pos in positions)
        
        # Calculate portfolio value (positions + cash)
        portfolio_value = cash + sum(
            pos.get('market_price', 0) * pos.get('quantity', 0) for pos in positions
        )
        
        # Update metrics
        update_portfolio_pnl(
            total_pnl=total_pnl,
            daily_pnl=None,  # Would need separate daily tracking
            monthly_pnl=None  # Would need separate monthly tracking
        )
        update_portfolio_value(portfolio_value)
        
    except Exception as e:
        logger.debug(f"Error updating portfolio metrics from positions: {e}")


def calculate_and_update_strategy_win_rate(strategy_name: str, trades: List[Dict]) -> float:
    """
    Calculate win rate from trades and update metrics
    
    Args:
        strategy_name: Strategy name
        trades: List of trade dicts with keys: pnl, exit_reason, etc.
        
    Returns:
        Win rate (0.0 to 1.0)
    """
    if not settings.metrics.enabled or not trades:
        return 0.0
    
    try:
        # Calculate win rate
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        win_rate = len(winning_trades) / len(trades) if trades else 0.0
        
        # Update metric
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
    """
    Update risk metrics from configuration values
    
    Args:
        max_drawdown: Maximum drawdown percentage (negative value)
        daily_loss_limit: Daily loss limit in currency
        position_size_limit: Maximum position size in currency
        risk_per_trade: Maximum risk per trade in currency
    """
    if not settings.metrics.enabled:
        return
    
    try:
        update_risk_metrics(
            max_drawdown=max_drawdown,
            daily_loss_limit=daily_loss_limit,
            position_size_limit=position_size_limit,
            risk_per_trade=risk_per_trade
        )
    except Exception as e:
        logger.debug(f"Error updating risk metrics from config: {e}")


def calculate_drawdown(equity_curve: List[float]) -> float:
    """
    Calculate maximum drawdown from equity curve
    
    Args:
        equity_curve: List of portfolio values over time
        
    Returns:
        Maximum drawdown percentage (negative value)
    """
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
    """
    Update cache hit rate metrics from UsageMonitor
    
    Args:
        monitor: UsageMonitor instance
        providers: Optional list of provider names to update (None = all)
    """
    if not settings.metrics.enabled:
        return
    
    try:
        if providers is None:
            # Get all providers from monitor
            providers = list(monitor.source_metrics.keys())
        
        for provider in providers:
            metrics = monitor.get_source_metrics(provider)
            if metrics and hasattr(metrics, 'cache_hit_rate'):
                update_cache_hit_rate(provider, metrics.cache_hit_rate)
                
    except Exception as e:
        logger.debug(f"Error updating cache hit rates from monitor: {e}")

