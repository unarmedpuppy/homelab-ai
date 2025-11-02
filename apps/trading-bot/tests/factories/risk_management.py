"""
Risk Management Factory Functions
==================================

Factory functions for creating risk management data for testing.
"""

from typing import Dict, Any, Optional


def create_account_balance(
    total_value: float = 100000.0,
    available_funds: Optional[float] = None,
    buying_power: Optional[float] = None,
    cash: Optional[float] = None,
    margin_used: float = 0.0
) -> Dict[str, float]:
    """
    Create account balance data for testing
    
    Args:
        total_value: Total account value
        available_funds: Available funds (defaults to total_value * 0.5)
        buying_power: Buying power (defaults to total_value)
        cash: Cash balance (defaults to available_funds)
        margin_used: Margin used
    
    Returns:
        Account balance dictionary
    """
    if available_funds is None:
        available_funds = total_value * 0.5
    
    if buying_power is None:
        buying_power = total_value
    
    if cash is None:
        cash = available_funds
    
    return {
        "total_value": total_value,
        "available_funds": available_funds,
        "buying_power": buying_power,
        "cash": cash,
        "margin_used": margin_used
    }


def create_risk_limits(
    max_position_size_pct: float = 0.04,
    max_open_positions: int = 5,
    max_daily_loss_pct: float = 0.02,
    stop_loss_pct: float = 0.005,
    take_profit_pct: float = 0.02,
    confidence_sizing: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Create risk management limits for testing
    
    Args:
        max_position_size_pct: Maximum position size as % of account
        max_open_positions: Maximum open positions
        max_daily_loss_pct: Maximum daily loss as % of account
        stop_loss_pct: Default stop loss percentage
        take_profit_pct: Default take profit percentage
        confidence_sizing: Confidence-based sizing (defaults to 1%, 2%, 4%)
    
    Returns:
        Risk limits dictionary
    """
    if confidence_sizing is None:
        confidence_sizing = {
            "low": 0.01,      # 1% for low confidence
            "medium": 0.02,   # 2% for medium confidence
            "high": 0.04      # 4% for high confidence
        }
    
    return {
        "max_position_size_pct": max_position_size_pct,
        "max_open_positions": max_open_positions,
        "max_daily_loss_pct": max_daily_loss_pct,
        "stop_loss_pct": stop_loss_pct,
        "take_profit_pct": take_profit_pct,
        "confidence_sizing": confidence_sizing
    }

