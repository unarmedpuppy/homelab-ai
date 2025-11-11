"""
Daily journal service.

Provides daily journal data including trades, summaries, P&L progression, and notes.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from collections import defaultdict

from app.models.trade import Trade
from app.models.daily_note import DailyNote
from app.schemas.daily import (
    DailyJournal,
    DailySummary,
    PnLProgressionPoint,
    DailyNoteResponse,
    DailyNoteCreate,
    DailyNoteUpdate,
)


async def get_daily_journal(
    db: AsyncSession,
    journal_date: date,
) -> DailyJournal:
    """
    Get complete daily journal data for a specific date.
    
    Args:
        db: Database session
        journal_date: Date to get journal data for
    
    Returns:
        DailyJournal with trades, summary, notes, and P&L progression
    """
    # Get all trades for the day
    # Include both closed trades (exited on this day) and open trades (entered on this day)
    start_datetime = datetime.combine(journal_date, datetime.min.time())
    end_datetime = datetime.combine(journal_date, datetime.max.time())
    
    # Get closed trades (exited on this day)
    closed_query = (
        select(Trade)
        .where(
            and_(
                Trade.status == "closed",
                Trade.exit_time >= start_datetime,
                Trade.exit_time <= end_datetime,
            )
        )
    )
    
    # Get open trades (entered on this day, still open)
    open_query = (
        select(Trade)
        .where(
            and_(
                Trade.status.in_(["open", "partial"]),
                Trade.entry_time >= start_datetime,
                Trade.entry_time <= end_datetime,
            )
        )
    )
    
    closed_result = await db.execute(closed_query)
    open_result = await db.execute(open_query)
    closed_trades = closed_result.scalars().all()
    open_trades = open_result.scalars().all()
    
    # Combine: closed trades first (ordered by exit_time), then open trades (ordered by entry_time)
    from sqlalchemy import case
    all_trades = list(closed_trades) + list(open_trades)
    
    # Sort: closed trades by exit_time, open trades by entry_time
    trades = sorted(
        all_trades,
        key=lambda t: t.exit_time if t.status == "closed" and t.exit_time else t.entry_time if t.entry_time else datetime.min
    )
    
    # Calculate daily summary
    summary = await _calculate_daily_summary(trades)
    
    # Calculate P&L progression
    pnl_progression = await _calculate_pnl_progression(trades)
    
    # Get daily notes
    notes_query = select(DailyNote).where(DailyNote.date == journal_date)
    notes_result = await db.execute(notes_query)
    daily_note = notes_result.scalar_one_or_none()
    
    notes_text = daily_note.notes if daily_note else None
    
    # Convert trades to TradeResponse format
    from app.schemas.trade import TradeResponse
    trades_list = []
    for trade in trades:
        # Update calculated fields
        trade.update_calculated_fields()
        # Convert to TradeResponse using from_attributes
        trade_response = TradeResponse.model_validate(trade)
        trades_list.append(trade_response)
    
    return DailyJournal(
        date=journal_date,
        net_pnl=summary.gross_pnl - summary.commissions,
        trades=trades_list,
        summary=summary,
        notes=notes_text,
        pnl_progression=pnl_progression,
    )


async def get_daily_trades(
    db: AsyncSession,
    journal_date: date,
) -> List[Trade]:
    """
    Get all trades for a specific date.
    
    Args:
        db: Database session
        journal_date: Date to get trades for
    
    Returns:
        List of trades for the day
    """
    start_datetime = datetime.combine(journal_date, datetime.min.time())
    end_datetime = datetime.combine(journal_date, datetime.max.time())
    
    query = (
        select(Trade)
        .where(
            and_(
                Trade.status == "closed",
                Trade.exit_time >= start_datetime,
                Trade.exit_time <= end_datetime,
            )
        )
        .order_by(Trade.exit_time)
    )
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_daily_summary(
    db: AsyncSession,
    journal_date: date,
) -> DailySummary:
    """
    Get daily summary for a specific date.
    
    Args:
        db: Database session
        journal_date: Date to get summary for
    
    Returns:
        DailySummary with statistics for the day
    """
    trades = await get_daily_trades(db, journal_date)
    return await _calculate_daily_summary(trades)


async def get_daily_pnl_progression(
    db: AsyncSession,
    journal_date: date,
) -> List[PnLProgressionPoint]:
    """
    Get P&L progression throughout the day.
    
    Args:
        db: Database session
        journal_date: Date to get progression for
    
    Returns:
        List of P&L progression points
    """
    trades = await get_daily_trades(db, journal_date)
    return await _calculate_pnl_progression(trades)


async def _calculate_daily_summary(trades: List[Trade]) -> DailySummary:
    """
    Calculate daily summary from trades.
    
    Args:
        trades: List of trades for the day
    
    Returns:
        DailySummary with statistics
    """
    if not trades:
        return DailySummary(
            total_trades=0,
            winners=0,
            losers=0,
            winrate=None,
            gross_pnl=Decimal("0"),
            commissions=Decimal("0"),
            volume=0,
            profit_factor=None,
        )
    
    total_trades = len(trades)
    winners = 0
    losers = 0
    gross_pnl = Decimal("0")
    commissions = Decimal("0")
    volume = 0
    winning_trades_pnl = []
    losing_trades_pnl = []
    
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
        
        gross_pnl += trade_gross_pnl
        commissions += trade.entry_commission + trade.exit_commission
        
        # Calculate volume (for stocks/options, use quantity * price)
        if trade.trade_type == "OPTION":
            volume += float(trade.entry_quantity * trade.entry_price * Decimal("100"))
        else:
            volume += float(trade.entry_quantity * trade.entry_price)
        
        if trade_pnl > 0:
            winners += 1
            winning_trades_pnl.append(trade_gross_pnl)
        elif trade_pnl < 0:
            losers += 1
            losing_trades_pnl.append(abs(trade_gross_pnl))
    
    # Calculate winrate
    winrate = None
    if total_trades > 0:
        winrate = (Decimal(winners) / Decimal(total_trades)) * Decimal("100")
    
    # Calculate profit factor
    profit_factor = None
    total_gross_profit = sum(winning_trades_pnl) if winning_trades_pnl else Decimal("0")
    total_gross_loss = sum(losing_trades_pnl) if losing_trades_pnl else Decimal("0")
    if total_gross_loss > 0:
        profit_factor = total_gross_profit / total_gross_loss
    
    return DailySummary(
        total_trades=total_trades,
        winners=winners,
        losers=losers,
        winrate=winrate,
        gross_pnl=gross_pnl,
        commissions=commissions,
        volume=int(volume),
        profit_factor=profit_factor,
    )


async def _calculate_pnl_progression(trades: List[Trade]) -> List[PnLProgressionPoint]:
    """
    Calculate P&L progression throughout the day.
    
    Args:
        trades: List of trades for the day, ordered by exit_time
    
    Returns:
        List of P&L progression points
    """
    if not trades:
        return []
    
    progression = []
    cumulative_pnl = Decimal("0")
    
    for trade in trades:
        trade_pnl = trade.calculate_net_pnl()
        if trade_pnl is None or not trade.exit_time:
            continue
        
        cumulative_pnl += trade_pnl
        
        progression.append(PnLProgressionPoint(
            time=trade.exit_time,
            cumulative_pnl=cumulative_pnl,
        ))
    
    return progression


async def get_daily_note(
    db: AsyncSession,
    note_date: date,
) -> Optional[DailyNoteResponse]:
    """
    Get daily note for a specific date.
    
    Args:
        db: Database session
        note_date: Date to get note for
    
    Returns:
        DailyNoteResponse if note exists, None otherwise
    """
    query = select(DailyNote).where(DailyNote.date == note_date)
    result = await db.execute(query)
    daily_note = result.scalar_one_or_none()
    
    if not daily_note:
        return None
    
    return DailyNoteResponse(
        id=daily_note.id,
        date=daily_note.date,
        notes=daily_note.notes,
        created_at=daily_note.created_at,
        updated_at=daily_note.updated_at,
    )


async def create_or_update_daily_note(
    db: AsyncSession,
    note_date: date,
    note_data: DailyNoteCreate | DailyNoteUpdate,
) -> DailyNoteResponse:
    """
    Create or update daily note for a specific date.
    
    Args:
        db: Database session
        note_date: Date for the note
        note_data: Note data to create or update
    
    Returns:
        DailyNoteResponse with created/updated note
    """
    # Check if note exists
    query = select(DailyNote).where(DailyNote.date == note_date)
    result = await db.execute(query)
    daily_note = result.scalar_one_or_none()
    
    if daily_note:
        # Update existing note
        if isinstance(note_data, DailyNoteUpdate):
            if note_data.notes is not None:
                daily_note.notes = note_data.notes
        else:
            daily_note.notes = note_data.notes
    else:
        # Create new note
        daily_note = DailyNote(
            date=note_date,
            notes=note_data.notes if isinstance(note_data, DailyNoteCreate) else note_data.notes or "",
        )
        db.add(daily_note)
    
    await db.commit()
    await db.refresh(daily_note)
    
    return DailyNoteResponse(
        id=daily_note.id,
        date=daily_note.date,
        notes=daily_note.notes,
        created_at=daily_note.created_at,
        updated_at=daily_note.updated_at,
    )


async def delete_daily_note(
    db: AsyncSession,
    note_date: date,
) -> bool:
    """
    Delete daily note for a specific date.
    
    Args:
        db: Database session
        note_date: Date to delete note for
    
    Returns:
        True if note was deleted, False if note didn't exist
    """
    from sqlalchemy import delete
    
    # Delete using delete statement (SQLAlchemy 2.0 async)
    stmt = delete(DailyNote).where(DailyNote.date == note_date)
    result = await db.execute(stmt)
    await db.commit()
    
    return result.rowcount > 0

