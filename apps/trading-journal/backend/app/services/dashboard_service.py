"""
Dashboard statistics service.

Calculates comprehensive trading statistics and metrics for the dashboard.
All calculations match formulas from STARTUP_GUIDE.md.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from typing import Optional, List
from datetime import date, datetime, timedelta
from decimal import Decimal
from collections import defaultdict
import math

from app.models.trade import Trade
from app.schemas.dashboard import (
    DashboardStats,
    CumulativePnLPoint,
    DailyPnLPoint,
    DrawdownData,
    RecentTrade,
)


async def get_dashboard_stats(
    db: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> DashboardStats:
    """
    Calculate comprehensive dashboard statistics.
    
    Args:
        db: Database session
        date_from: Start date for filtering (inclusive)
        date_to: End date for filtering (inclusive)
    
    Returns:
        DashboardStats with all calculated metrics
    """
    # Build query with filters
    query = select(Trade).where(Trade.status == "closed")
    
    if date_from:
        query = query.where(Trade.exit_time >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        # Include entire end date
        end_datetime = datetime.combine(date_to, datetime.max.time())
        query = query.where(Trade.exit_time <= end_datetime)
    
    result = await db.execute(query)
    trades = result.scalars().all()
    
    if not trades:
        # Return empty stats if no trades
        return DashboardStats(
            net_pnl=Decimal("0"),
            gross_pnl=Decimal("0"),
            total_trades=0,
            winners=0,
            losers=0,
            win_rate=None,
            day_win_rate=None,
            profit_factor=None,
            avg_win=None,
            avg_loss=None,
            max_drawdown=None,
            zella_score=None,
        )
    
    # Calculate basic metrics
    total_trades = len(trades)
    net_pnl = Decimal("0")
    gross_pnl = Decimal("0")
    winners = 0
    losers = 0
    winning_trades_pnl = []
    losing_trades_pnl = []
    daily_pnl_map = defaultdict(Decimal)  # date -> daily P&L
    
    for trade in trades:
        trade_pnl = trade.calculate_net_pnl()
        if trade_pnl is None:
            continue
        
        # Calculate gross P&L (before commissions)
        if trade.exit_price and trade.exit_quantity:
            quantity = trade.exit_quantity
            if trade.side == "LONG":
                price_diff = trade.exit_price - trade.entry_price
            else:  # SHORT
                price_diff = trade.entry_price - trade.exit_price
            
            if trade.trade_type == "OPTION":
                trade_gross_pnl = price_diff * quantity * Decimal("100")
            else:
                trade_gross_pnl = price_diff * quantity
        else:
            trade_gross_pnl = trade_pnl + trade.entry_commission + trade.exit_commission
        
        net_pnl += trade_pnl
        gross_pnl += trade_gross_pnl
        
        # Track winners/losers
        if trade_pnl > 0:
            winners += 1
            winning_trades_pnl.append(trade_pnl)
        elif trade_pnl < 0:
            losers += 1
            losing_trades_pnl.append(abs(trade_pnl))
        
        # Track daily P&L for day win rate
        if trade.exit_time:
            trade_date = trade.exit_time.date()
            daily_pnl_map[trade_date] += trade_pnl
    
    # Calculate win rate
    win_rate = None
    if total_trades > 0:
        win_rate = (Decimal(winners) / Decimal(total_trades)) * Decimal("100")
    
    # Calculate day win rate
    day_win_rate = None
    total_days = len(daily_pnl_map)
    winning_days = sum(1 for day_pnl in daily_pnl_map.values() if day_pnl > 0)
    if total_days > 0:
        day_win_rate = (Decimal(winning_days) / Decimal(total_days)) * Decimal("100")
    
    # Calculate profit factor
    profit_factor = None
    total_gross_profit = sum(winning_trades_pnl) if winning_trades_pnl else Decimal("0")
    total_gross_loss = sum(losing_trades_pnl) if losing_trades_pnl else Decimal("0")
    if total_gross_loss > 0:
        profit_factor = total_gross_profit / total_gross_loss
    
    # Calculate average win/loss
    avg_win = None
    if winning_trades_pnl:
        avg_win = sum(winning_trades_pnl) / Decimal(len(winning_trades_pnl))
    
    avg_loss = None
    if losing_trades_pnl:
        avg_loss = sum(losing_trades_pnl) / Decimal(len(losing_trades_pnl))
    
    # Calculate max drawdown
    max_drawdown = calculate_max_drawdown(trades, date_from, date_to)
    
    # Calculate Zella score
    zella_score = calculate_zella_score(
        win_rate=win_rate,
        profit_factor=profit_factor,
        avg_win=avg_win,
        avg_loss=avg_loss,
        max_drawdown=max_drawdown,
        daily_pnl_values=list(daily_pnl_map.values()),
    )
    
    return DashboardStats(
        net_pnl=net_pnl,
        gross_pnl=gross_pnl,
        total_trades=total_trades,
        winners=winners,
        losers=losers,
        win_rate=win_rate,
        day_win_rate=day_win_rate,
        profit_factor=profit_factor,
        avg_win=avg_win,
        avg_loss=avg_loss,
        max_drawdown=max_drawdown,
        zella_score=zella_score,
    )


def calculate_max_drawdown(
    trades: List[Trade],
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> Optional[Decimal]:
    """
    Calculate maximum drawdown from cumulative P&L.
    
    Algorithm:
    1. Calculate cumulative P&L over time
    2. Track peak values
    3. Calculate drawdown = (Peak - Current) / Peak × 100
    4. Max Drawdown = Maximum drawdown value
    
    Args:
        trades: List of closed trades
        date_from: Start date filter
        date_to: End date filter
    
    Returns:
        Maximum drawdown as percentage, or None if no trades
    """
    if not trades:
        return None
    
    # Sort trades by exit time
    sorted_trades = sorted(
        [t for t in trades if t.exit_time],
        key=lambda t: t.exit_time
    )
    
    if not sorted_trades:
        return None
    
    cumulative_pnl = Decimal("0")
    peak = Decimal("0")
    max_drawdown_pct = Decimal("0")
    
    for trade in sorted_trades:
        trade_pnl = trade.calculate_net_pnl()
        if trade_pnl is None:
            continue
        
        cumulative_pnl += trade_pnl
        
        # Update peak
        if cumulative_pnl > peak:
            peak = cumulative_pnl
        
        # Calculate drawdown
        if peak > 0:
            drawdown = ((peak - cumulative_pnl) / peak) * Decimal("100")
            if drawdown > max_drawdown_pct:
                max_drawdown_pct = drawdown
        elif peak == 0 and cumulative_pnl < 0:
            # Can't calculate percentage drawdown when starting negative (peak is 0)
            # Skip this case - max drawdown percentage doesn't apply when there's no positive peak
            pass
    
    return max_drawdown_pct if max_drawdown_pct > 0 else None


def calculate_zella_score(
    win_rate: Optional[Decimal],
    profit_factor: Optional[Decimal],
    avg_win: Optional[Decimal],
    avg_loss: Optional[Decimal],
    max_drawdown: Optional[Decimal],
    daily_pnl_values: List[Decimal],
) -> Optional[Decimal]:
    """
    Calculate Zella Score (composite metric).
    
    Zella Score = Weighted average of normalized metrics
    
    Components (all normalized to 0-100 scale):
    - Win Rate: 30% weight
    - Consistency: 20% weight (based on standard deviation of daily P&L)
    - Profit Factor: 25% weight
    - Avg Win/Loss Ratio: 15% weight
    - Max Drawdown (inverse): 10% weight
    
    Args:
        win_rate: Win rate percentage
        profit_factor: Profit factor
        avg_win: Average winning trade
        avg_loss: Average losing trade
        max_drawdown: Maximum drawdown percentage
        daily_pnl_values: List of daily P&L values for consistency calculation
    
    Returns:
        Zella score (0-100), or None if insufficient data
    """
    components = []
    weights = []
    
    # Win Rate (0-100, already normalized)
    if win_rate is not None:
        components.append(win_rate)
        weights.append(Decimal("0.30"))
    
    # Consistency (based on standard deviation of daily P&L)
    if len(daily_pnl_values) >= 2:
        try:
            # Convert to float for std dev calculation
            pnl_floats = [float(pnl) for pnl in daily_pnl_values]
            
            # Calculate mean
            mean_pnl = Decimal(str(sum(pnl_floats) / len(pnl_floats))) if pnl_floats else Decimal("0")
            
            # Calculate standard deviation
            if len(pnl_floats) > 1:
                variance = sum((x - float(mean_pnl)) ** 2 for x in pnl_floats) / (len(pnl_floats) - 1)
                std_dev = Decimal(str(math.sqrt(variance)))
            else:
                std_dev = Decimal("0")
            
            # Normalize consistency: lower std dev relative to mean = higher consistency
            # Use coefficient of variation (CV) and invert it
            if mean_pnl != 0:
                cv = abs(std_dev / mean_pnl)
                # Normalize CV to 0-100 scale (assume CV of 2.0 = 0, CV of 0 = 100)
                consistency = max(Decimal("0"), min(Decimal("100"), Decimal("100") - (cv * Decimal("50"))))
            else:
                consistency = Decimal("50")  # Neutral if no mean
            components.append(consistency)
            weights.append(Decimal("0.20"))
        except (ValueError, ZeroDivisionError):
            pass
    
    # Profit Factor (normalize to 0-100)
    if profit_factor is not None:
        # Normalize: PF of 0 = 0, PF of 5+ = 100
        normalized_pf = min(Decimal("100"), profit_factor * Decimal("20"))
        components.append(normalized_pf)
        weights.append(Decimal("0.25"))
    
    # Avg Win/Loss Ratio (normalize to 0-100)
    if avg_win is not None and avg_loss is not None and avg_loss > 0:
        win_loss_ratio = avg_win / avg_loss
        # Normalize: ratio of 0 = 0, ratio of 5+ = 100
        normalized_ratio = min(Decimal("100"), win_loss_ratio * Decimal("20"))
        components.append(normalized_ratio)
        weights.append(Decimal("0.15"))
    
    # Max Drawdown (inverse: lower drawdown = higher score)
    if max_drawdown is not None:
        # Invert: drawdown of 0% = 100, drawdown of 100% = 0
        inverse_drawdown = Decimal("100") - max_drawdown
        components.append(inverse_drawdown)
        weights.append(Decimal("0.10"))
    
    # Calculate weighted average
    if not components:
        return None
    
    # Normalize weights to sum to 1.0
    total_weight = sum(weights)
    if total_weight == 0:
        return None
    
    normalized_weights = [w / total_weight for w in weights]
    
    zella_score = sum(comp * weight for comp, weight in zip(components, normalized_weights))
    
    return max(Decimal("0"), min(Decimal("100"), zella_score))


async def get_cumulative_pnl(
    db: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    group_by: str = "day",
) -> List[CumulativePnLPoint]:
    """
    Get cumulative P&L data points for charting.
    
    Args:
        db: Database session
        date_from: Start date for filtering
        date_to: End date for filtering
        group_by: Grouping period (day, week, month)
    
    Returns:
        List of cumulative P&L points
    """
    query = select(Trade).where(Trade.status == "closed")
    
    if date_from:
        query = query.where(Trade.exit_time >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        end_datetime = datetime.combine(date_to, datetime.max.time())
        query = query.where(Trade.exit_time <= end_datetime)
    
    result = await db.execute(query)
    trades = result.scalars().all()
    
    if not trades:
        return []
    
    # Sort by exit time
    sorted_trades = sorted(
        [t for t in trades if t.exit_time],
        key=lambda t: t.exit_time
    )
    
    cumulative_pnl = Decimal("0")
    points = []
    current_period_date = None
    period_pnl = Decimal("0")
    
    for trade in sorted_trades:
        trade_pnl = trade.calculate_net_pnl()
        if trade_pnl is None:
            continue
        
        trade_date = trade.exit_time.date()
        
        # Group by period
        if group_by == "day":
            period_date = trade_date
        elif group_by == "week":
            # Get Monday of the week
            days_since_monday = trade_date.weekday()
            period_date = trade_date - timedelta(days=days_since_monday)
        elif group_by == "month":
            period_date = trade_date.replace(day=1)
        else:
            period_date = trade_date
        
        # If new period, save previous period and start new one
        if current_period_date is not None and period_date != current_period_date:
            points.append(CumulativePnLPoint(
                date=current_period_date,
                cumulative_pnl=cumulative_pnl,
            ))
            period_pnl = Decimal("0")
        
        # Add to cumulative and period
        cumulative_pnl += trade_pnl
        period_pnl += trade_pnl
        current_period_date = period_date
    
    # Add final point
    if current_period_date is not None:
        points.append(CumulativePnLPoint(
            date=current_period_date,
            cumulative_pnl=cumulative_pnl,
        ))
    
    return points


async def get_daily_pnl(
    db: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> List[DailyPnLPoint]:
    """
    Get daily P&L data points for charting.
    
    Args:
        db: Database session
        date_from: Start date for filtering
        date_to: End date for filtering
    
    Returns:
        List of daily P&L points
    """
    query = select(Trade).where(Trade.status == "closed")
    
    if date_from:
        query = query.where(Trade.exit_time >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        end_datetime = datetime.combine(date_to, datetime.max.time())
        query = query.where(Trade.exit_time <= end_datetime)
    
    result = await db.execute(query)
    trades = result.scalars().all()
    
    if not trades:
        return []
    
    # Group by date
    daily_data = defaultdict(lambda: {"pnl": Decimal("0"), "count": 0})
    
    for trade in trades:
        trade_pnl = trade.calculate_net_pnl()
        if trade_pnl is None or not trade.exit_time:
            continue
        
        trade_date = trade.exit_time.date()
        daily_data[trade_date]["pnl"] += trade_pnl
        daily_data[trade_date]["count"] += 1
    
    # Convert to list of points
    points = [
        DailyPnLPoint(
            date=date_key,
            pnl=data["pnl"],
            trade_count=data["count"],
        )
        for date_key, data in sorted(daily_data.items())
    ]
    
    return points


async def get_drawdown_data(
    db: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> List[DrawdownData]:
    """
    Get drawdown data for charting.
    
    Args:
        db: Database session
        date_from: Start date for filtering
        date_to: End date for filtering
    
    Returns:
        List of drawdown data points
    """
    query = select(Trade).where(Trade.status == "closed")
    
    if date_from:
        query = query.where(Trade.exit_time >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        end_datetime = datetime.combine(date_to, datetime.max.time())
        query = query.where(Trade.exit_time <= end_datetime)
    
    result = await db.execute(query)
    trades = result.scalars().all()
    
    if not trades:
        return []
    
    # Sort by exit time
    sorted_trades = sorted(
        [t for t in trades if t.exit_time],
        key=lambda t: t.exit_time
    )
    
    cumulative_pnl = Decimal("0")
    peak = Decimal("0")
    trough = Decimal("0")
    peak_date = None
    trough_date = None
    drawdown_points = []
    
    for trade in sorted_trades:
        trade_pnl = trade.calculate_net_pnl()
        if trade_pnl is None:
            continue
        
        trade_date = trade.exit_time.date()
        cumulative_pnl += trade_pnl
        
        # Update peak
        if cumulative_pnl > peak:
            peak = cumulative_pnl
            peak_date = trade_date
            trough = cumulative_pnl
            trough_date = trade_date
        
        # Update trough
        if cumulative_pnl < trough:
            trough = cumulative_pnl
            trough_date = trade_date
        
        # Calculate drawdown
        if peak > 0:
            drawdown = peak - cumulative_pnl
            drawdown_pct = ((peak - cumulative_pnl) / peak) * Decimal("100")
        else:
            drawdown = abs(cumulative_pnl)
            drawdown_pct = abs(cumulative_pnl)
        
        # Add point if drawdown exists
        if drawdown > 0:
            drawdown_points.append(DrawdownData(
                date=trade_date,
                peak=peak,
                trough=trough,
                drawdown=drawdown,
                drawdown_pct=drawdown_pct,
                recovery_date=None,  # TODO: Calculate recovery dates
            ))
    
    return drawdown_points


async def get_recent_trades(
    db: AsyncSession,
    limit: int = 10,
) -> List[RecentTrade]:
    """
    Get recent trades for dashboard display.
    
    Returns the most recent trades (closed first, then open), ordered by entry_time (newest first).
    For closed trades, orders by exit_time. For open trades, orders by entry_time.
    
    Args:
        db: Database session
        limit: Maximum number of trades to return
    
    Returns:
        List of recent trades
    """
    from sqlalchemy import or_, case
    
    # Get closed trades ordered by exit_time
    closed_query = (
        select(Trade)
        .where(Trade.status == "closed")
        .order_by(Trade.exit_time.desc())
        .limit(limit)
    )
    
    closed_result = await db.execute(closed_query)
    closed_trades = closed_result.scalars().all()
    
    # Get open trades ordered by entry_time if we haven't reached the limit
    remaining_limit = limit - len(closed_trades)
    open_trades = []
    if remaining_limit > 0:
        open_query = (
            select(Trade)
            .where(Trade.status.in_(["open", "partial"]))
            .order_by(Trade.entry_time.desc())
            .limit(remaining_limit)
        )
        open_result = await db.execute(open_query)
        open_trades = open_result.scalars().all()
    
    # Combine and sort: closed trades first (by exit_time), then open trades (by entry_time)
    all_trades = list(closed_trades) + list(open_trades)
    
    recent_trades = []
    for trade in all_trades:
        # Update calculated fields before accessing
        trade.update_calculated_fields()
        net_pnl = trade.calculate_net_pnl()
        
        recent_trades.append(RecentTrade(
            id=trade.id,
            ticker=trade.ticker,
            trade_type=trade.trade_type,
            side=trade.side,
            entry_time=trade.entry_time.date() if trade.entry_time else date.today(),
            exit_time=trade.exit_time.date() if trade.exit_time else None,
            net_pnl=net_pnl,
            status=trade.status,
        ))
    
    return recent_trades

