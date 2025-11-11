"""
Charts API endpoints.

Provides price data and chart visualization endpoints.
"""

from fastapi import APIRouter, Depends, Path, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta

from app.api.dependencies import verify_api_key, DatabaseSession
from app.schemas.charts import PriceDataResponse, TradeOverlayData
from app.services.price_service import get_price_data
from app.services.trade_service import get_trade

router = APIRouter(dependencies=[Depends(verify_api_key)])


def parse_datetime_param(datetime_str: Optional[str], param_name: str = "datetime") -> Optional[datetime]:
    """
    Parse datetime string parameter with error handling.
    
    Args:
        datetime_str: Datetime string in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
        param_name: Name of the parameter (for error messages)
    
    Returns:
        Parsed datetime object or None
    
    Raises:
        HTTPException: If datetime format is invalid
    """
    if datetime_str is None:
        return None
    
    # Try ISO format first (YYYY-MM-DDTHH:MM:SS)
    try:
        return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
    except ValueError:
        pass
    
    # Try date format (YYYY-MM-DD) - convert to start of day
    try:
        date_obj = datetime.strptime(datetime_str, "%Y-%m-%d")
        return date_obj
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {param_name} format. Use YYYY-MM-DD or ISO datetime format."
        )


@router.get("/prices/{ticker}", response_model=PriceDataResponse)
async def get_price_chart(
    ticker: str = Path(..., description="Ticker symbol", min_length=1, max_length=20),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD or ISO datetime)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD or ISO datetime)"),
    timeframe: str = Query("1h", description="Timeframe: 1m, 5m, 15m, 1h, 1d"),
    db: DatabaseSession = None,
):
    """
    Get price data for a ticker.
    
    Returns OHLCV data points for the specified ticker, date range, and timeframe.
    Defaults to 1 year of data if no dates specified.
    """
    # Validate timeframe
    valid_timeframes = ["1m", "5m", "15m", "1h", "1d"]
    if timeframe not in valid_timeframes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
        )
    
    # Parse datetime parameters
    start_datetime = parse_datetime_param(start_date, "start_date")
    end_datetime = parse_datetime_param(end_date, "end_date")
    
    # Get price data
    price_data = await get_price_data(
        db=db,
        ticker=ticker.upper().strip(),
        start_date=start_datetime,
        end_date=end_datetime,
        timeframe=timeframe,
    )
    
    return price_data


@router.get("/prices/{ticker}/range", response_model=PriceDataResponse)
async def get_price_chart_range(
    ticker: str = Path(..., description="Ticker symbol", min_length=1, max_length=20),
    days: int = Query(365, ge=1, le=365, description="Number of days to retrieve (max 365)"),
    timeframe: str = Query("1h", description="Timeframe: 1m, 5m, 15m, 1h, 1d"),
    db: DatabaseSession = None,
):
    """
    Get price data for a ticker for a specified number of days.
    
    Returns OHLCV data points for the specified ticker, number of days, and timeframe.
    """
    # Validate timeframe
    valid_timeframes = ["1m", "5m", "15m", "1h", "1d"]
    if timeframe not in valid_timeframes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
        )
    
    # Calculate date range
    end_datetime = datetime.now()
    start_datetime = end_datetime - timedelta(days=days)
    
    # Get price data
    price_data = await get_price_data(
        db=db,
        ticker=ticker.upper().strip(),
        start_date=start_datetime,
        end_date=end_datetime,
        timeframe=timeframe,
    )
    
    return price_data


@router.get("/trade/{trade_id}", response_model=PriceDataResponse)
async def get_trade_chart(
    trade_id: int = Path(..., description="Trade ID", ge=1),
    days_before: int = Query(30, ge=1, le=365, description="Days before entry to include"),
    days_after: int = Query(30, ge=1, le=365, description="Days after exit to include (or current date if open)"),
    timeframe: str = Query("1h", description="Timeframe: 1m, 5m, 15m, 1h, 1d"),
    db: DatabaseSession = None,
):
    """
    Get price data for a specific trade with entry/exit context.
    
    Returns price data covering the trade's entry and exit times, plus optional buffer periods.
    For open trades, extends to current date.
    """
    # Validate timeframe
    valid_timeframes = ["1m", "5m", "15m", "1h", "1d"]
    if timeframe not in valid_timeframes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
        )
    
    # Get trade
    trade = await get_trade(db, trade_id)
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trade with ID {trade_id} not found"
        )
    
    if not trade.entry_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trade has no entry time"
        )
    
    # Calculate date range
    start_datetime = trade.entry_time - timedelta(days=days_before)
    
    if trade.exit_time:
        end_datetime = trade.exit_time + timedelta(days=days_after)
    else:
        # Open trade - extend to current date
        end_datetime = datetime.now()
    
    # Get price data
    price_data = await get_price_data(
        db=db,
        ticker=trade.ticker,
        start_date=start_datetime,
        end_date=end_datetime,
        timeframe=timeframe,
    )
    
    return price_data


@router.get("/trade/{trade_id}/overlay", response_model=TradeOverlayData)
async def get_trade_overlay(
    trade_id: int = Path(..., description="Trade ID", ge=1),
    db: DatabaseSession = None,
):
    """
    Get trade overlay data for chart visualization.
    
    Returns trade entry/exit information to overlay on price charts.
    """
    # Get trade
    trade = await get_trade(db, trade_id)
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trade with ID {trade_id} not found"
        )
    
    # Update calculated fields
    trade.update_calculated_fields()
    net_pnl = trade.calculate_net_pnl()
    
    return TradeOverlayData(
        trade_id=trade.id,
        ticker=trade.ticker,
        entry_time=trade.entry_time,
        entry_price=trade.entry_price,
        exit_time=trade.exit_time,
        exit_price=trade.exit_price,
        side=trade.side,
        net_pnl=net_pnl,
    )

