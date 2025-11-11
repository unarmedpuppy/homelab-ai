"""
Validation utilities for trade data.
"""

from decimal import Decimal
from datetime import datetime, date
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
    Validate that quantities are positive and exit_quantity <= entry_quantity.
    
    Args:
        entry_quantity: Entry quantity
        exit_quantity: Exit quantity (optional)
    
    Returns:
        True if valid, False otherwise
    """
    if entry_quantity <= 0:
        return False
    if exit_quantity is not None:
        if exit_quantity <= 0:
            return False
        if exit_quantity > entry_quantity:
            return False
    return True


def validate_options_greeks(
    delta: Optional[Decimal] = None,
    gamma: Optional[Decimal] = None,
    theta: Optional[Decimal] = None,
    vega: Optional[Decimal] = None,
    rho: Optional[Decimal] = None,
) -> tuple[bool, Optional[str]]:
    """
    Validate options Greeks are within reasonable ranges.
    
    Args:
        delta: Delta value (should be between -1 and 1)
        gamma: Gamma value (should be between 0 and 1)
        theta: Theta value (typically negative for long options)
        vega: Vega value (should be non-negative)
        rho: Rho value (typically small)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if delta is not None and abs(delta) > 1:
        return False, f"Delta must be between -1 and 1, got {delta}"
    
    if gamma is not None and (gamma < 0 or gamma > 1):
        return False, f"Gamma must be between 0 and 1, got {gamma}"
    
    if vega is not None and vega < 0:
        return False, f"Vega must be non-negative, got {vega}"
    
    # Theta is typically negative for long options, but we allow positive for short positions
    # Just check it's not unreasonably large
    if theta is not None and abs(theta) > 1000:
        return False, f"Theta value seems unreasonable: {theta}"
    
    if rho is not None and abs(rho) > 100:
        return False, f"Rho value seems unreasonable: {rho}"
    
    return True, None


def validate_implied_volatility(iv: Optional[Decimal]) -> tuple[bool, Optional[str]]:
    """
    Validate implied volatility is within reasonable range (0-10 = 0-1000%).
    
    Args:
        iv: Implied volatility value
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if iv is None:
        return True, None
    
    if iv < 0:
        return False, f"Implied volatility cannot be negative, got {iv}"
    
    if iv > 10:  # 1000% is extremely high but possible
        return False, f"Implied volatility seems unreasonably high: {iv} (1000%+). Please verify."
    
    return True, None


def validate_expiration_date(expiration_date: Optional[date], entry_time: Optional[datetime]) -> tuple[bool, Optional[str]]:
    """
    Validate expiration date is reasonable.
    
    Args:
        expiration_date: Option expiration date
        entry_time: Trade entry time
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if expiration_date is None:
        return True, None
    
    if entry_time is None:
        return True, None
    
    # Expiration should be on or after entry date
    if expiration_date < entry_time.date():
        return False, f"Expiration date ({expiration_date}) must be on or after entry date ({entry_time.date()})"
    
    # Expiration should not be too far in the future (e.g., more than 10 years)
    from datetime import timedelta
    max_future_date = date.today() + timedelta(days=3650)  # 10 years
    if expiration_date > max_future_date:
        return False, f"Expiration date ({expiration_date}) seems unreasonably far in the future. Please verify."
    
    return True, None


def validate_bid_ask_prices(
    bid_price: Optional[Decimal],
    ask_price: Optional[Decimal],
    bid_ask_spread: Optional[Decimal] = None,
) -> tuple[bool, Optional[str]]:
    """
    Validate bid/ask prices are consistent.
    
    Args:
        bid_price: Bid price
        ask_price: Ask price
        bid_ask_spread: Optional bid-ask spread
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if bid_price is None or ask_price is None:
        return True, None
    
    if bid_price < 0 or ask_price < 0:
        return False, "Bid and ask prices must be non-negative"
    
    if bid_price > ask_price:
        return False, f"Bid price ({bid_price}) cannot exceed ask price ({ask_price})"
    
    if bid_ask_spread is not None:
        calculated_spread = ask_price - bid_price
        # Allow small floating point differences
        if abs(bid_ask_spread - calculated_spread) > Decimal("0.01"):
            return False, f"Bid-ask spread ({bid_ask_spread}) does not match calculated spread ({calculated_spread})"
    
    return True, None
