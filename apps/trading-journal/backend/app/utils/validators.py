"""
Validation utilities for trade data.
"""

from decimal import Decimal
from datetime import datetime
from typing import Optional


def validate_trade_dates(entry_time: datetime, exit_time: Optional[datetime]) -> bool:
    """
    Validate that exit_time is after entry_time.
    
    Args:
        entry_time: Entry timestamp
        exit_time: Exit timestamp (optional)
    
    Returns:
        True if valid, False otherwise
    """
    if exit_time is None:
        return True
    return exit_time >= entry_time


def validate_prices(entry_price: Decimal, exit_price: Optional[Decimal]) -> bool:
    """
    Validate that prices are positive.
    
    Args:
        entry_price: Entry price
        exit_price: Exit price (optional)
    
    Returns:
        True if valid, False otherwise
    """
    if entry_price <= 0:
        return False
    if exit_price is not None and exit_price <= 0:
        return False
    return True


def validate_quantities(entry_quantity: Decimal, exit_quantity: Optional[Decimal]) -> bool:
    """
    Validate that quantities are positive.
    
    Args:
        entry_quantity: Entry quantity
        exit_quantity: Exit quantity (optional)
    
    Returns:
        True if valid, False otherwise
    """
    if entry_quantity <= 0:
        return False
    if exit_quantity is not None and exit_quantity <= 0:
        return False
    return True

