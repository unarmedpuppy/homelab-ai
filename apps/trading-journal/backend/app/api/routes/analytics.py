"""
Analytics API endpoints.

Provides endpoints for performance analytics, breakdowns by ticker, trade type, and playbook.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date, datetime

from app.api.dependencies import verify_api_key, DatabaseSession
from app.schemas.analytics import (
    PerformanceMetrics,
    TickerPerformanceResponse,
    TypePerformanceResponse,
    PlaybookPerformanceResponse,
)
from app.services.analytics_service import (
    get_performance_metrics,
    get_performance_by_ticker,
    get_performance_by_type,
    get_performance_by_playbook,
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


@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics_endpoint(
    db: DatabaseSession,
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """
    Get comprehensive performance metrics.
    
    Returns advanced performance metrics including:
    - Sharpe ratio and Sortino ratio
    - Max drawdown and average drawdown
    - Win rate and profit factor
    - Average win/loss
    - Best and worst trades
    """
    # Parse date strings
    date_from_parsed = parse_date_param(date_from, "date_from")
    date_to_parsed = parse_date_param(date_to, "date_to")
    
    metrics = await get_performance_metrics(
        db=db,
        date_from=date_from_parsed,
        date_to=date_to_parsed,
    )
    
    return metrics


@router.get("/by-ticker", response_model=TickerPerformanceResponse)
async def get_performance_by_ticker_endpoint(
    db: DatabaseSession,
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """
    Get performance breakdown by ticker.
    
    Returns performance metrics grouped by ticker symbol, sorted by net P&L (descending).
    """
    # Parse date strings
    date_from_parsed = parse_date_param(date_from, "date_from")
    date_to_parsed = parse_date_param(date_to, "date_to")
    
    performance = await get_performance_by_ticker(
        db=db,
        date_from=date_from_parsed,
        date_to=date_to_parsed,
    )
    
    return performance


@router.get("/by-type", response_model=TypePerformanceResponse)
async def get_performance_by_type_endpoint(
    db: DatabaseSession,
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """
    Get performance breakdown by trade type.
    
    Returns performance metrics grouped by trade type (STOCK, OPTION, CRYPTO_SPOT, etc.),
    sorted by net P&L (descending).
    """
    # Parse date strings
    date_from_parsed = parse_date_param(date_from, "date_from")
    date_to_parsed = parse_date_param(date_to, "date_to")
    
    performance = await get_performance_by_type(
        db=db,
        date_from=date_from_parsed,
        date_to=date_to_parsed,
    )
    
    return performance


@router.get("/by-playbook", response_model=PlaybookPerformanceResponse)
async def get_performance_by_playbook_endpoint(
    db: DatabaseSession,
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """
    Get performance breakdown by playbook/strategy.
    
    Returns performance metrics grouped by playbook/strategy name, sorted by net P&L (descending).
    Trades without a playbook are grouped under "Unspecified".
    """
    # Parse date strings
    date_from_parsed = parse_date_param(date_from, "date_from")
    date_to_parsed = parse_date_param(date_to, "date_to")
    
    performance = await get_performance_by_playbook(
        db=db,
        date_from=date_from_parsed,
        date_to=date_to_parsed,
    )
    
    return performance

