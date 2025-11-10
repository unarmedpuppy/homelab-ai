"""
P&L calculation utilities.

All calculation functions match the formulas from STARTUP_GUIDE.md.
"""

from decimal import Decimal
from typing import Optional


def calculate_net_pnl(
    entry_price: Decimal,
    exit_price: Decimal,
    quantity: Decimal,
    entry_commission: Decimal,
    exit_commission: Decimal,
    trade_type: str,
    side: str
) -> Decimal:
    """
    Calculate net P&L for a trade.
    
    Args:
        entry_price: Entry price
        exit_price: Exit price
        quantity: Trade quantity
        entry_commission: Entry commission
        exit_commission: Exit commission
        trade_type: Trade type (STOCK, OPTION, CRYPTO_SPOT, etc.)
        side: Trade side (LONG or SHORT)
    
    Returns:
        Net P&L as Decimal
    """
    # Calculate price difference based on side
    if side == "LONG":
        price_diff = exit_price - entry_price
    else:  # SHORT
        price_diff = entry_price - exit_price
    
    # Calculate base P&L
    if trade_type == "OPTION":
        # Options: multiply by 100 (contract size)
        base_pnl = price_diff * quantity * Decimal("100")
    else:
        # Stocks, crypto, prediction markets
        base_pnl = price_diff * quantity
    
    # Subtract commissions
    net_pnl = base_pnl - entry_commission - exit_commission
    
    return net_pnl


def calculate_roi(
    entry_price: Decimal,
    quantity: Decimal,
    entry_commission: Decimal,
    net_pnl: Decimal,
    trade_type: str
) -> Decimal:
    """
    Calculate ROI (Return on Investment) as a percentage.
    
    Args:
        entry_price: Entry price
        quantity: Trade quantity
        entry_commission: Entry commission
        net_pnl: Net P&L
        trade_type: Trade type (STOCK, OPTION, CRYPTO_SPOT, etc.)
    
    Returns:
        ROI as Decimal percentage
    """
    # Calculate total cost
    if trade_type == "OPTION":
        # Options: multiply by 100 (contract size)
        total_cost = (entry_price * quantity * Decimal("100")) + entry_commission
    else:
        total_cost = (entry_price * quantity) + entry_commission
    
    if total_cost == 0:
        return Decimal("0")
    
    # ROI = (Net P&L / Total Cost) × 100
    roi = (net_pnl / total_cost) * Decimal("100")
    
    return roi


def calculate_r_multiple(
    entry_price: Decimal,
    quantity: Decimal,
    net_pnl: Decimal,
    trade_type: str,
    stop_loss: Optional[Decimal] = None
) -> Decimal:
    """
    Calculate R-multiple for a trade.
    
    Args:
        entry_price: Entry price
        quantity: Trade quantity
        net_pnl: Net P&L
        trade_type: Trade type (STOCK, OPTION, CRYPTO_SPOT, etc.)
        stop_loss: Optional stop loss price. If not provided, uses entry price as risk.
    
    Returns:
        R-multiple as Decimal
    """
    # Calculate risk per unit
    if stop_loss is not None:
        # Use stop loss as risk
        risk_per_unit = abs(entry_price - stop_loss)
    else:
        # Default: use entry price as risk
        risk_per_unit = entry_price
    
    # Calculate total risk
    if trade_type == "OPTION":
        risk_amount = risk_per_unit * quantity * Decimal("100")
    else:
        risk_amount = risk_per_unit * quantity
    
    if risk_amount == 0:
        return Decimal("0")
    
    # R-multiple = Net P&L / Risk Amount
    r_multiple = net_pnl / risk_amount
    
    return r_multiple

