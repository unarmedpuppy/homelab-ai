"""
Input Validation Utilities
==========================

Validation functions for sentiment provider inputs (symbols, time ranges, etc.)
"""

import re
import logging
from typing import Optional
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Stock symbol validation regex (uppercase letters/numbers, 1-5 chars)
SYMBOL_PATTERN = re.compile(r'^[A-Z0-9]{1,5}$')

# Common invalid symbols to reject
INVALID_SYMBOLS = {
    'TEST', 'DEMO', 'NULL', 'NONE', 'TRUE', 'FALSE',
    'AND', 'OR', 'NOT', 'SELECT', 'INSERT', 'DELETE',
    'UPDATE', 'DROP', 'CREATE', 'ALTER'
}


def validate_symbol(symbol: str, raise_on_error: bool = True) -> Optional[str]:
    """
    Validate stock symbol format
    
    Args:
        symbol: Stock symbol to validate
        raise_on_error: If True, raise HTTPException on validation error. If False, return None.
    
    Returns:
        Uppercase validated symbol or None if invalid (when raise_on_error=False)
    
    Raises:
        HTTPException: If symbol is invalid and raise_on_error=True
    """
    if not symbol:
        if raise_on_error:
            raise HTTPException(
                status_code=400,
                detail="Symbol is required and cannot be empty"
            )
        return None
    
    # Normalize to uppercase
    symbol = symbol.upper().strip()
    
    # Check for invalid/reserved symbols
    if symbol in INVALID_SYMBOLS:
        if raise_on_error:
            raise HTTPException(
                status_code=400,
                detail=f"Symbol '{symbol}' is reserved and cannot be used"
            )
        return None
    
    # Validate format (uppercase alphanumeric, 1-5 characters)
    if not SYMBOL_PATTERN.match(symbol):
        if raise_on_error:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid symbol format: '{symbol}'. Symbols must be 1-5 uppercase letters/numbers"
            )
        return None
    
    return symbol


def validate_hours(hours: int, min_hours: int = 1, max_hours: int = 168, raise_on_error: bool = True) -> Optional[int]:
    """
    Validate hours parameter for time range queries
    
    Args:
        hours: Hours value to validate
        min_hours: Minimum allowed hours (default: 1)
        max_hours: Maximum allowed hours (default: 168 = 7 days)
        raise_on_error: If True, raise HTTPException on validation error. If False, return None.
    
    Returns:
        Validated hours value or None if invalid (when raise_on_error=False)
    
    Raises:
        HTTPException: If hours is invalid and raise_on_error=True
    """
    if not isinstance(hours, int):
        if raise_on_error:
            raise HTTPException(
                status_code=400,
                detail=f"Hours must be an integer, got: {type(hours).__name__}"
            )
        return None
    
    if hours < min_hours:
        if raise_on_error:
            raise HTTPException(
                status_code=400,
                detail=f"Hours must be at least {min_hours}, got: {hours}"
            )
        return None
    
    if hours > max_hours:
        if raise_on_error:
            raise HTTPException(
                status_code=400,
                detail=f"Hours must be at most {max_hours} ({max_hours // 24} days), got: {hours}"
            )
        return None
    
    return hours


def validate_days(days: int, min_days: int = 1, max_days: int = 730, raise_on_error: bool = True) -> Optional[int]:
    """
    Validate days parameter for time range queries
    
    Args:
        days: Days value to validate
        min_days: Minimum allowed days (default: 1)
        max_days: Maximum allowed days (default: 730 = 2 years)
        raise_on_error: If True, raise HTTPException on validation error. If False, return None.
    
    Returns:
        Validated days value or None if invalid (when raise_on_error=False)
    
    Raises:
        HTTPException: If days is invalid and raise_on_error=True
    """
    if not isinstance(days, int):
        if raise_on_error:
            raise HTTPException(
                status_code=400,
                detail=f"Days must be an integer, got: {type(days).__name__}"
            )
        return None
    
    if days < min_days:
        if raise_on_error:
            raise HTTPException(
                status_code=400,
                detail=f"Days must be at least {min_days}, got: {days}"
            )
        return None
    
    if days > max_days:
        if raise_on_error:
            raise HTTPException(
                status_code=400,
                detail=f"Days must be at most {max_days} ({max_days // 365} years), got: {days}"
            )
        return None
    
    return days


def validate_limit(limit: int, min_limit: int = 1, max_limit: int = 1000, raise_on_error: bool = True) -> Optional[int]:
    """
    Validate limit parameter for pagination/result limits
    
    Args:
        limit: Limit value to validate
        min_limit: Minimum allowed limit (default: 1)
        max_limit: Maximum allowed limit (default: 1000)
        raise_on_error: If True, raise HTTPException on validation error. If False, return None.
    
    Returns:
        Validated limit value or None if invalid (when raise_on_error=False)
    
    Raises:
        HTTPException: If limit is invalid and raise_on_error=True
    """
    if not isinstance(limit, int):
        if raise_on_error:
            raise HTTPException(
                status_code=400,
                detail=f"Limit must be an integer, got: {type(limit).__name__}"
            )
        return None
    
    if limit < min_limit:
        if raise_on_error:
            raise HTTPException(
                status_code=400,
                detail=f"Limit must be at least {min_limit}, got: {limit}"
            )
        return None
    
    if limit > max_limit:
        if raise_on_error:
            raise HTTPException(
                status_code=400,
                detail=f"Limit must be at most {max_limit}, got: {limit}"
            )
        return None
    
    return limit


def validate_symbol_list(symbols: list, raise_on_error: bool = True) -> Optional[list]:
    """
    Validate list of stock symbols
    
    Args:
        symbols: List of symbols to validate
        raise_on_error: If True, raise HTTPException on validation error. If False, return None.
    
    Returns:
        List of validated (uppercase) symbols or None if invalid (when raise_on_error=False)
    
    Raises:
        HTTPException: If symbols list is invalid and raise_on_error=True
    """
    if not isinstance(symbols, list):
        if raise_on_error:
            raise HTTPException(
                status_code=400,
                detail=f"Symbols must be a list, got: {type(symbols).__name__}"
            )
        return None
    
    if len(symbols) == 0:
        if raise_on_error:
            raise HTTPException(
                status_code=400,
                detail="Symbols list cannot be empty"
            )
        return None
    
    if len(symbols) > 100:  # Reasonable limit
        if raise_on_error:
            raise HTTPException(
                status_code=400,
                detail=f"Symbols list cannot contain more than 100 symbols, got: {len(symbols)}"
            )
        return None
    
    validated_symbols = []
    for symbol in symbols:
        validated = validate_symbol(symbol, raise_on_error=raise_on_error)
        if validated is None:
            return None
        validated_symbols.append(validated)
    
    return validated_symbols

