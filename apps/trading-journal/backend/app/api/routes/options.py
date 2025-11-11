"""
Options chain API endpoints.

Provides endpoints for fetching options chain data and Greeks information.
"""

from fastapi import APIRouter, Depends, Path, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date, datetime
from decimal import Decimal

from app.api.dependencies import verify_api_key, DatabaseSession
from app.schemas.options import (
    OptionChainResponse,
    GreeksResponse,
    OptionType,
)
from app.services.options_service import (
    get_options_chain,
    get_options_chain_by_expiration,
    get_greeks,
)

router = APIRouter(dependencies=[Depends(verify_api_key)])


def parse_date_param(date_str: Optional[str], param_name: str) -> Optional[date]:
    """
    Parse date string parameter with error handling.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        param_name: Name of the parameter (for error messages)
    
    Returns:
        Parsed date object, or None if date_str is None/empty
    
    Raises:
        HTTPException: If date format is invalid
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {param_name} format. Use YYYY-MM-DD"
        )


@router.get("/chain/{ticker}", response_model=OptionChainResponse)
async def get_options_chain_endpoint(
    ticker: str = Path(..., description="Ticker symbol", min_length=1, max_length=20),
    expiration_date: Optional[str] = Query(None, description="Filter by expiration date (YYYY-MM-DD)"),
    option_type: Optional[str] = Query(None, description="Filter by option type (CALL or PUT)"),
    db: DatabaseSession = None,
):
    """
    Get options chain for a ticker.
    
    Returns all available option contracts for the specified ticker.
    Can be filtered by expiration date and/or option type.
    
    Note: Currently returns data from existing trades in the database.
    Future versions will integrate with real-time options data providers (e.g., Polygon.io).
    """
    # Parse expiration date
    expiration_parsed = parse_date_param(expiration_date, "expiration_date")
    
    # Validate option type
    option_type_enum = None
    if option_type:
        option_type_upper = option_type.upper()
        if option_type_upper not in ["CALL", "PUT"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="option_type must be 'CALL' or 'PUT'"
            )
        option_type_enum = OptionType(option_type_upper)
    
    chain = await get_options_chain(
        db=db,
        ticker=ticker,
        expiration_date=expiration_parsed,
        option_type=option_type_enum,
    )
    
    return chain


@router.get("/chain/{ticker}/{expiration}", response_model=OptionChainResponse)
async def get_options_chain_by_expiration_endpoint(
    ticker: str = Path(..., description="Ticker symbol", min_length=1, max_length=20),
    expiration: str = Path(..., description="Expiration date (YYYY-MM-DD)"),
    db: DatabaseSession = None,
):
    """
    Get options chain for a specific expiration date.
    
    Returns all available option contracts for the specified ticker and expiration date.
    """
    # Parse expiration date
    expiration_parsed = parse_date_param(expiration, "expiration")
    if not expiration_parsed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid expiration date format. Use YYYY-MM-DD"
        )
    
    chain = await get_options_chain_by_expiration(
        db=db,
        ticker=ticker,
        expiration=expiration_parsed,
    )
    
    return chain


@router.get("/greeks/{ticker}", response_model=GreeksResponse)
async def get_greeks_endpoint(
    ticker: str = Path(..., description="Ticker symbol", min_length=1, max_length=20),
    strike: Optional[str] = Query(None, description="Filter by strike price"),
    expiration: Optional[str] = Query(None, description="Filter by expiration date (YYYY-MM-DD)"),
    db: DatabaseSession = None,
):
    """
    Get Greeks data for a ticker.
    
    Returns Greeks (Delta, Gamma, Theta, Vega, Rho) for option contracts.
    Can be filtered by strike price and/or expiration date.
    
    Note: Currently returns data from existing trades in the database.
    Future versions will integrate with real-time options data providers (e.g., Polygon.io).
    """
    # Parse strike price
    strike_decimal = None
    if strike:
        try:
            strike_decimal = Decimal(strike)
            if strike_decimal <= 0:
                raise ValueError("Strike price must be positive")
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid strike price format. Must be a positive number"
            )
    
    # Parse expiration date
    expiration_parsed = parse_date_param(expiration, "expiration")
    
    greeks_data = await get_greeks(
        db=db,
        ticker=ticker,
        strike_price=strike_decimal,
        expiration_date=expiration_parsed,
    )
    
    return greeks_data

