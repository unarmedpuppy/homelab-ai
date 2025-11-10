"""
Dashboard API endpoints.

Provides statistics, charts, and metrics for the dashboard view.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date, datetime

from app.api.dependencies import verify_api_key, DatabaseSession
from app.schemas.dashboard import (
    DashboardStats,
    CumulativePnLPoint,
    DailyPnLPoint,
    DrawdownData,
    RecentTrade,
)
from app.services.dashboard_service import (
    get_dashboard_stats,
    get_cumulative_pnl,
    get_daily_pnl,
    get_drawdown_data,
    get_recent_trades,
)

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    db: DatabaseSession,
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """
    Get comprehensive dashboard statistics.
    
    Returns all KPIs including:
    - Net P&L, Gross P&L
    - Total trades, winners, losers
    - Win rate, day win rate
    - Profit factor
    - Average win/loss
    - Max drawdown
    - Zella score
    """
    # Parse date strings
    date_from_parsed = None
    date_to_parsed = None
    
    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_from format. Use YYYY-MM-DD"
            )
    
    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_to format. Use YYYY-MM-DD"
            )
    
    stats = await get_dashboard_stats(
        db=db,
        date_from=date_from_parsed,
        date_to=date_to_parsed,
    )
    
    return stats


@router.get("/cumulative-pnl", response_model=list[CumulativePnLPoint])
async def get_cumulative_pnl_chart(
    db: DatabaseSession,
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    group_by: str = Query("day", description="Grouping period: day, week, or month"),
):
    """
    Get cumulative P&L data points for charting.
    
    Returns array of {date, cumulative_pnl} points.
    Supports grouping by day, week, or month.
    """
    # Validate group_by
    if group_by not in ["day", "week", "month"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="group_by must be 'day', 'week', or 'month'"
        )
    
    # Parse date strings
    date_from_parsed = None
    date_to_parsed = None
    
    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_from format. Use YYYY-MM-DD"
            )
    
    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_to format. Use YYYY-MM-DD"
            )
    
    points = await get_cumulative_pnl(
        db=db,
        date_from=date_from_parsed,
        date_to=date_to_parsed,
        group_by=group_by,
    )
    
    return points


@router.get("/daily-pnl", response_model=list[DailyPnLPoint])
async def get_daily_pnl_chart(
    db: DatabaseSession,
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """
    Get daily P&L data points for charting.
    
    Returns array of {date, pnl, trade_count} points.
    """
    # Parse date strings
    date_from_parsed = None
    date_to_parsed = None
    
    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_from format. Use YYYY-MM-DD"
            )
    
    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_to format. Use YYYY-MM-DD"
            )
    
    points = await get_daily_pnl(
        db=db,
        date_from=date_from_parsed,
        date_to=date_to_parsed,
    )
    
    return points


@router.get("/drawdown", response_model=list[DrawdownData])
async def get_drawdown_chart(
    db: DatabaseSession,
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """
    Get drawdown data for charting.
    
    Returns array of drawdown data points with peak, trough, and recovery information.
    """
    # Parse date strings
    date_from_parsed = None
    date_to_parsed = None
    
    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_from format. Use YYYY-MM-DD"
            )
    
    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_to format. Use YYYY-MM-DD"
            )
    
    drawdown_data = await get_drawdown_data(
        db=db,
        date_from=date_from_parsed,
        date_to=date_to_parsed,
    )
    
    return drawdown_data


@router.get("/recent-trades", response_model=list[RecentTrade])
async def get_recent_trades_list(
    db: DatabaseSession,
    limit: int = Query(10, ge=1, le=100, description="Maximum number of trades to return"),
):
    """
    Get recent closed trades for dashboard display.
    
    Returns the most recent closed trades, ordered by exit time (newest first).
    """
    trades = await get_recent_trades(db=db, limit=limit)
    return trades

