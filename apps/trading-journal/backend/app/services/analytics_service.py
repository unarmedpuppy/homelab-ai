"""
Analytics service for performance analysis.

Provides analytics endpoints for performance metrics, breakdowns by ticker, trade type, and playbook.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from collections import defaultdict
import math

from app.models.trade import Trade
from app.schemas.analytics import (
    PerformanceMetrics,
    TickerPerformance,
    TickerPerformanceResponse,
    TypePerformance,
    TypePerformanceResponse,
    PlaybookPerformance,
    PlaybookPerformanceResponse,
)
from app.services.dashboard_service import calculate_max_drawdown


async def get_performance_metrics(
    db: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> PerformanceMetrics:
    """
    Get comprehensive performance metrics.
    
    Calculates advanced metrics including Sharpe ratio, Sortino ratio, and best/worst trades.
    
    Args:
        db: Database session
        date_from: Start date for filtering (inclusive)
        date_to: End date for filtering (inclusive)
    
    Returns:
        PerformanceMetrics with all calculated metrics
    """
    # Build query with filters
    query = (
        select(Trade)
        .where(Trade.status == "closed")
        .order_by(Trade.exit_time.asc())
    )
    
    if date_from:
        query = query.where(Trade.exit_time >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        end_datetime = datetime.combine(date_to, datetime.max.time())
        query = query.where(Trade.exit_time <= end_datetime)
    
    result = await db.execute(query)
    trades = result.scalars().all()
    
    if not trades:
        return PerformanceMetrics(
            total_trades=0,
        )
    
    # Calculate basic metrics
    total_trades = len(trades)
    net_pnl_values = []
    winning_trades_pnl = []
    losing_trades_pnl = []
    daily_pnl_values = []
    
    best_trade = None
    worst_trade = None
    
    for trade in trades:
        trade_pnl = trade.calculate_net_pnl()
        if trade_pnl is None:
            continue
        
        net_pnl_values.append(float(trade_pnl))
        
        # Track best/worst trades
        if best_trade is None or trade_pnl > best_trade:
            best_trade = trade_pnl
        if worst_trade is None or trade_pnl < worst_trade:
            worst_trade = trade_pnl
        
        # Track winners/losers
        if trade_pnl > 0:
            winning_trades_pnl.append(float(trade_pnl))
        elif trade_pnl < 0:
            losing_trades_pnl.append(abs(float(trade_pnl)))
        
        # Track daily P&L for drawdown calculation
        if trade.exit_time:
            trade_date = trade.exit_time.date()
            if not daily_pnl_values or daily_pnl_values[-1][0] != trade_date:
                daily_pnl_values.append([trade_date, float(trade_pnl)])
            else:
                daily_pnl_values[-1][1] += float(trade_pnl)
    
    # Calculate win rate
    win_rate = None
    if total_trades > 0:
        winners = len(winning_trades_pnl)
        win_rate = (Decimal(winners) / Decimal(total_trades)) * Decimal("100")
    
    # Calculate profit factor
    profit_factor = None
    total_gross_profit = sum(winning_trades_pnl) if winning_trades_pnl else Decimal("0")
    total_gross_loss = sum(losing_trades_pnl) if losing_trades_pnl else Decimal("0")
    if total_gross_loss > 0:
        profit_factor = Decimal(str(total_gross_profit)) / Decimal(str(total_gross_loss))
    
    # Calculate average win/loss
    avg_win = None
    if winning_trades_pnl:
        avg_win = Decimal(str(sum(winning_trades_pnl) / len(winning_trades_pnl)))
    
    avg_loss = None
    if losing_trades_pnl:
        avg_loss = Decimal(str(sum(losing_trades_pnl) / len(losing_trades_pnl)))
    
    # Calculate max drawdown
    max_drawdown = calculate_max_drawdown(trades, date_from, date_to)
    
    # Calculate average drawdown
    avg_drawdown = None
    if len(daily_pnl_values) >= 2:
        # Calculate drawdowns from daily P&L
        cumulative = 0
        peak = 0
        drawdowns = []
        
        for _, daily_pnl in daily_pnl_values:
            cumulative += daily_pnl
            if cumulative > peak:
                peak = cumulative
            if peak > 0:
                drawdown = ((peak - cumulative) / peak) * Decimal("100")
                drawdowns.append(float(drawdown))
        
        if drawdowns:
            avg_drawdown = Decimal(str(sum(drawdowns) / len(drawdowns)))
    
    # Calculate Sharpe ratio (simplified: mean return / std dev)
    sharpe_ratio = None
    if len(net_pnl_values) >= 2:
        mean_return = sum(net_pnl_values) / len(net_pnl_values)
        variance = sum((x - mean_return) ** 2 for x in net_pnl_values) / (len(net_pnl_values) - 1)
        std_dev = math.sqrt(variance)
        
        if std_dev > 0:
            # Annualized Sharpe ratio (assuming daily returns, multiply by sqrt(252))
            sharpe_ratio = Decimal(str((mean_return / std_dev) * math.sqrt(252)))
    
    # Calculate Sortino ratio (mean return / downside deviation)
    sortino_ratio = None
    if len(net_pnl_values) >= 2:
        mean_return = sum(net_pnl_values) / len(net_pnl_values)
        # Only consider negative returns for downside deviation
        negative_returns = [x for x in net_pnl_values if x < 0]
        
        if negative_returns:
            downside_variance = sum((x - mean_return) ** 2 for x in negative_returns) / len(negative_returns)
            downside_dev = math.sqrt(downside_variance)
            
            if downside_dev > 0:
                # Annualized Sortino ratio
                sortino_ratio = Decimal(str((mean_return / downside_dev) * math.sqrt(252)))
    
    return PerformanceMetrics(
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        max_drawdown=max_drawdown,
        avg_drawdown=avg_drawdown,
        win_rate=win_rate,
        profit_factor=profit_factor,
        avg_win=avg_win,
        avg_loss=avg_loss,
        best_trade=best_trade,
        worst_trade=worst_trade,
        total_trades=total_trades,
    )


async def get_performance_by_ticker(
    db: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> TickerPerformanceResponse:
    """
    Get performance breakdown by ticker.
    
    Args:
        db: Database session
        date_from: Start date for filtering (inclusive)
        date_to: End date for filtering (inclusive)
    
    Returns:
        TickerPerformanceResponse with performance breakdown by ticker
    """
    # Build query with filters
    query = (
        select(Trade)
        .where(Trade.status == "closed")
        .order_by(Trade.exit_time.asc())
    )
    
    if date_from:
        query = query.where(Trade.exit_time >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        end_datetime = datetime.combine(date_to, datetime.max.time())
        query = query.where(Trade.exit_time <= end_datetime)
    
    result = await db.execute(query)
    trades = result.scalars().all()
    
    # Group by ticker
    ticker_data = defaultdict(lambda: {
        "trades": [],
        "net_pnl": Decimal("0"),
        "gross_pnl": Decimal("0"),
        "winners": 0,
        "losers": 0,
        "winning_pnl": [],
        "losing_pnl": [],
    })
    
    for trade in trades:
        trade_pnl = trade.calculate_net_pnl()
        if trade_pnl is None:
            continue
        
        ticker = trade.ticker.upper()
        ticker_data[ticker]["trades"].append(trade)
        ticker_data[ticker]["net_pnl"] += trade_pnl
        
        # Calculate gross P&L
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
        
        ticker_data[ticker]["gross_pnl"] += trade_gross_pnl
        
        # Track winners/losers
        if trade_pnl > 0:
            ticker_data[ticker]["winners"] += 1
            ticker_data[ticker]["winning_pnl"].append(trade_pnl)
        elif trade_pnl < 0:
            ticker_data[ticker]["losers"] += 1
            ticker_data[ticker]["losing_pnl"].append(abs(trade_pnl))
    
    # Convert to response format
    ticker_performances = []
    for ticker, data in ticker_data.items():
        total_trades = len(data["trades"])
        
        # Calculate win rate
        win_rate = None
        if total_trades > 0:
            win_rate = (Decimal(data["winners"]) / Decimal(total_trades)) * Decimal("100")
        
        # Calculate profit factor
        profit_factor = None
        total_gross_profit = sum(data["winning_pnl"]) if data["winning_pnl"] else Decimal("0")
        total_gross_loss = sum(data["losing_pnl"]) if data["losing_pnl"] else Decimal("0")
        if total_gross_loss > 0:
            profit_factor = total_gross_profit / total_gross_loss
        
        # Calculate average win/loss
        avg_win = None
        if data["winning_pnl"]:
            avg_win = sum(data["winning_pnl"]) / Decimal(len(data["winning_pnl"]))
        
        avg_loss = None
        if data["losing_pnl"]:
            avg_loss = sum(data["losing_pnl"]) / Decimal(len(data["losing_pnl"]))
        
        ticker_performances.append(TickerPerformance(
            ticker=ticker,
            total_trades=total_trades,
            net_pnl=data["net_pnl"],
            gross_pnl=data["gross_pnl"],
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            winners=data["winners"],
            losers=data["losers"],
        ))
    
    # Sort by net P&L (descending)
    ticker_performances.sort(key=lambda x: x.net_pnl, reverse=True)
    
    return TickerPerformanceResponse(
        date_from=date_from,
        date_to=date_to,
        tickers=ticker_performances,
    )


async def get_performance_by_type(
    db: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> TypePerformanceResponse:
    """
    Get performance breakdown by trade type.
    
    Args:
        db: Database session
        date_from: Start date for filtering (inclusive)
        date_to: End date for filtering (inclusive)
    
    Returns:
        TypePerformanceResponse with performance breakdown by trade type
    """
    # Build query with filters
    query = (
        select(Trade)
        .where(Trade.status == "closed")
        .order_by(Trade.exit_time.asc())
    )
    
    if date_from:
        query = query.where(Trade.exit_time >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        end_datetime = datetime.combine(date_to, datetime.max.time())
        query = query.where(Trade.exit_time <= end_datetime)
    
    result = await db.execute(query)
    trades = result.scalars().all()
    
    # Group by trade type
    type_data = defaultdict(lambda: {
        "trades": [],
        "net_pnl": Decimal("0"),
        "gross_pnl": Decimal("0"),
        "winners": 0,
        "losers": 0,
        "winning_pnl": [],
        "losing_pnl": [],
    })
    
    for trade in trades:
        trade_pnl = trade.calculate_net_pnl()
        if trade_pnl is None:
            continue
        
        trade_type = trade.trade_type
        type_data[trade_type]["trades"].append(trade)
        type_data[trade_type]["net_pnl"] += trade_pnl
        
        # Calculate gross P&L
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
        
        type_data[trade_type]["gross_pnl"] += trade_gross_pnl
        
        # Track winners/losers
        if trade_pnl > 0:
            type_data[trade_type]["winners"] += 1
            type_data[trade_type]["winning_pnl"].append(trade_pnl)
        elif trade_pnl < 0:
            type_data[trade_type]["losers"] += 1
            type_data[trade_type]["losing_pnl"].append(abs(trade_pnl))
    
    # Convert to response format
    type_performances = []
    for trade_type, data in type_data.items():
        total_trades = len(data["trades"])
        
        # Calculate win rate
        win_rate = None
        if total_trades > 0:
            win_rate = (Decimal(data["winners"]) / Decimal(total_trades)) * Decimal("100")
        
        # Calculate profit factor
        profit_factor = None
        total_gross_profit = sum(data["winning_pnl"]) if data["winning_pnl"] else Decimal("0")
        total_gross_loss = sum(data["losing_pnl"]) if data["losing_pnl"] else Decimal("0")
        if total_gross_loss > 0:
            profit_factor = total_gross_profit / total_gross_loss
        
        # Calculate average win/loss
        avg_win = None
        if data["winning_pnl"]:
            avg_win = sum(data["winning_pnl"]) / Decimal(len(data["winning_pnl"]))
        
        avg_loss = None
        if data["losing_pnl"]:
            avg_loss = sum(data["losing_pnl"]) / Decimal(len(data["losing_pnl"]))
        
        type_performances.append(TypePerformance(
            trade_type=trade_type,
            total_trades=total_trades,
            net_pnl=data["net_pnl"],
            gross_pnl=data["gross_pnl"],
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            winners=data["winners"],
            losers=data["losers"],
        ))
    
    # Sort by net P&L (descending)
    type_performances.sort(key=lambda x: x.net_pnl, reverse=True)
    
    return TypePerformanceResponse(
        date_from=date_from,
        date_to=date_to,
        types=type_performances,
    )


async def get_performance_by_playbook(
    db: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> PlaybookPerformanceResponse:
    """
    Get performance breakdown by playbook/strategy.
    
    Args:
        db: Database session
        date_from: Start date for filtering (inclusive)
        date_to: End date for filtering (inclusive)
    
    Returns:
        PlaybookPerformanceResponse with performance breakdown by playbook
    """
    # Build query with filters
    query = (
        select(Trade)
        .where(Trade.status == "closed")
        .order_by(Trade.exit_time.asc())
    )
    
    if date_from:
        query = query.where(Trade.exit_time >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        end_datetime = datetime.combine(date_to, datetime.max.time())
        query = query.where(Trade.exit_time <= end_datetime)
    
    result = await db.execute(query)
    trades = result.scalars().all()
    
    # Group by playbook (use "Unspecified" for trades without playbook)
    playbook_data = defaultdict(lambda: {
        "trades": [],
        "net_pnl": Decimal("0"),
        "gross_pnl": Decimal("0"),
        "winners": 0,
        "losers": 0,
        "winning_pnl": [],
        "losing_pnl": [],
    })
    
    for trade in trades:
        trade_pnl = trade.calculate_net_pnl()
        if trade_pnl is None:
            continue
        
        playbook = trade.playbook if trade.playbook else "Unspecified"
        playbook_data[playbook]["trades"].append(trade)
        playbook_data[playbook]["net_pnl"] += trade_pnl
        
        # Calculate gross P&L
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
        
        playbook_data[playbook]["gross_pnl"] += trade_gross_pnl
        
        # Track winners/losers
        if trade_pnl > 0:
            playbook_data[playbook]["winners"] += 1
            playbook_data[playbook]["winning_pnl"].append(trade_pnl)
        elif trade_pnl < 0:
            playbook_data[playbook]["losers"] += 1
            playbook_data[playbook]["losing_pnl"].append(abs(trade_pnl))
    
    # Convert to response format
    playbook_performances = []
    for playbook, data in playbook_data.items():
        total_trades = len(data["trades"])
        
        # Calculate win rate
        win_rate = None
        if total_trades > 0:
            win_rate = (Decimal(data["winners"]) / Decimal(total_trades)) * Decimal("100")
        
        # Calculate profit factor
        profit_factor = None
        total_gross_profit = sum(data["winning_pnl"]) if data["winning_pnl"] else Decimal("0")
        total_gross_loss = sum(data["losing_pnl"]) if data["losing_pnl"] else Decimal("0")
        if total_gross_loss > 0:
            profit_factor = total_gross_profit / total_gross_loss
        
        # Calculate average win/loss
        avg_win = None
        if data["winning_pnl"]:
            avg_win = sum(data["winning_pnl"]) / Decimal(len(data["winning_pnl"]))
        
        avg_loss = None
        if data["losing_pnl"]:
            avg_loss = sum(data["losing_pnl"]) / Decimal(len(data["losing_pnl"]))
        
        playbook_performances.append(PlaybookPerformance(
            playbook=playbook,
            total_trades=total_trades,
            net_pnl=data["net_pnl"],
            gross_pnl=data["gross_pnl"],
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            winners=data["winners"],
            losers=data["losers"],
        ))
    
    # Sort by net P&L (descending)
    playbook_performances.sort(key=lambda x: x.net_pnl, reverse=True)
    
    return PlaybookPerformanceResponse(
        date_from=date_from,
        date_to=date_to,
        playbooks=playbook_performances,
    )

