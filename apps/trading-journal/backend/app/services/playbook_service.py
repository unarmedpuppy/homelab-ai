"""
Playbook service for business logic.

Handles all playbook-related database operations and business rules.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from collections import defaultdict

from app.models.playbook import Playbook, PlaybookTemplate
from app.models.trade import Trade
from app.schemas.playbook import (
    PlaybookCreate,
    PlaybookUpdate,
    PlaybookTemplateCreate,
    PlaybookPerformance,
)


async def get_playbooks(
    db: AsyncSession,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_shared: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[List[Playbook], int]:
    """
    Get list of playbooks with optional filters.
    
    Args:
        db: Database session
        search: Search query for name/description
        is_active: Filter by active status
        is_shared: Filter by shared status
        skip: Number of records to skip
        limit: Maximum number of records to return
    
    Returns:
        Tuple of (playbooks list, total count)
    """
    query = select(Playbook)
    count_query = select(func.count()).select_from(Playbook)
    
    conditions = []
    
    if search:
        search_term = f"%{search.lower()}%"
        conditions.append(
            or_(
                func.lower(Playbook.name).like(search_term),
                func.lower(Playbook.description).like(search_term) if Playbook.description else False,
            )
        )
    
    if is_active is not None:
        conditions.append(Playbook.is_active == is_active)
    
    if is_shared is not None:
        conditions.append(Playbook.is_shared == is_shared)
    
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.order_by(Playbook.name.asc()).offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    playbooks = result.scalars().all()
    
    return list(playbooks), total


async def get_playbook(db: AsyncSession, playbook_id: int) -> Optional[Playbook]:
    """
    Get a playbook by ID.
    
    Args:
        db: Database session
        playbook_id: Playbook ID
    
    Returns:
        Playbook if found, None otherwise
    """
    query = select(Playbook).where(Playbook.id == playbook_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_playbook(db: AsyncSession, playbook_data: PlaybookCreate) -> Playbook:
    """
    Create a new playbook.
    
    Args:
        db: Database session
        playbook_data: Playbook creation data
    
    Returns:
        Created playbook
    """
    playbook_dict = playbook_data.model_dump(exclude_unset=True)
    playbook = Playbook(**playbook_dict)
    
    db.add(playbook)
    await db.commit()
    await db.refresh(playbook)
    
    return playbook


async def update_playbook(
    db: AsyncSession,
    playbook_id: int,
    playbook_data: PlaybookUpdate,
) -> Optional[Playbook]:
    """
    Update a playbook.
    
    Args:
        db: Database session
        playbook_id: Playbook ID
        playbook_data: Playbook update data
    
    Returns:
        Updated playbook if found, None otherwise
    """
    playbook = await get_playbook(db, playbook_id)
    if not playbook:
        return None
    
    update_data = playbook_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(playbook, field, value)
    
    await db.commit()
    await db.refresh(playbook)
    
    return playbook


async def delete_playbook(db: AsyncSession, playbook_id: int) -> bool:
    """
    Delete a playbook.
    
    Sets playbook_id to NULL for all trades using this playbook.
    
    Args:
        db: Database session
        playbook_id: Playbook ID
    
    Returns:
        True if deleted, False if not found
    """
    playbook = await get_playbook(db, playbook_id)
    if not playbook:
        return False
    
    # Set playbook_id to NULL for all trades using this playbook
    from sqlalchemy import update
    await db.execute(
        update(Trade)
        .where(Trade.playbook_id == playbook_id)
        .values(playbook_id=None)
    )
    
    await db.delete(playbook)
    await db.commit()
    
    return True


async def get_playbook_trades(
    db: AsyncSession,
    playbook_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> List[Trade]:
    """
    Get all trades for a playbook.
    
    Args:
        db: Database session
        playbook_id: Playbook ID
        date_from: Start date for filtering
        date_to: End date for filtering
    
    Returns:
        List of trades
    """
    query = select(Trade).where(Trade.playbook_id == playbook_id)
    
    if date_from:
        query = query.where(Trade.exit_time >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        end_datetime = datetime.combine(date_to, datetime.max.time())
        query = query.where(Trade.exit_time <= end_datetime)
    
    query = query.order_by(Trade.exit_time.desc())
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_playbook_performance(
    db: AsyncSession,
    playbook_id: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> PlaybookPerformance:
    """
    Calculate performance metrics for a playbook.
    
    Args:
        db: Database session
        playbook_id: Playbook ID
        date_from: Start date for filtering
        date_to: End date for filtering
    
    Returns:
        PlaybookPerformance with calculated metrics
    """
    trades = await get_playbook_trades(db, playbook_id, date_from, date_to)
    
    # Filter to closed trades only
    closed_trades = [t for t in trades if t.status == "closed"]
    
    if not closed_trades:
        return PlaybookPerformance(
            total_trades=0,
            missed_trades=0,
        )
    
    total_trades = len(closed_trades)
    net_pnl = Decimal("0")
    gross_pnl = Decimal("0")
    winners = 0
    losers = 0
    winning_pnl = []
    losing_pnl = []
    
    for trade in closed_trades:
        trade_pnl = trade.calculate_net_pnl()
        if trade_pnl is None:
            continue
        
        net_pnl += trade_pnl
        
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
        
        gross_pnl += trade_gross_pnl
        
        if trade_pnl > 0:
            winners += 1
            winning_pnl.append(trade_pnl)
        elif trade_pnl < 0:
            losers += 1
            losing_pnl.append(abs(trade_pnl))
    
    # Calculate win rate
    win_rate = None
    if total_trades > 0:
        win_rate = (Decimal(winners) / Decimal(total_trades)) * Decimal("100")
    
    # Calculate profit factor
    profit_factor = None
    total_gross_profit = sum(winning_pnl) if winning_pnl else Decimal("0")
    total_gross_loss = sum(losing_pnl) if losing_pnl else Decimal("0")
    if total_gross_loss > 0:
        profit_factor = total_gross_profit / total_gross_loss
    
    # Calculate average win/loss
    avg_win = None
    if winning_pnl:
        avg_win = sum(winning_pnl) / Decimal(len(winning_pnl))
    
    avg_loss = None
    if losing_pnl:
        avg_loss = sum(losing_pnl) / Decimal(len(losing_pnl))
    
    return PlaybookPerformance(
        total_trades=total_trades,
        missed_trades=0,  # Future feature
        net_pnl=net_pnl,
        gross_pnl=gross_pnl,
        win_rate=win_rate,
        profit_factor=profit_factor,
        avg_win=avg_win,
        avg_loss=avg_loss,
        winners=winners,
        losers=losers,
    )


async def get_playbook_templates(db: AsyncSession) -> List[PlaybookTemplate]:
    """
    Get all playbook templates.
    
    Args:
        db: Database session
    
    Returns:
        List of playbook templates
    """
    query = select(PlaybookTemplate).order_by(PlaybookTemplate.name.asc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_playbook_template(
    db: AsyncSession,
    template_data: PlaybookTemplateCreate,
) -> PlaybookTemplate:
    """
    Create a new playbook template.
    
    Args:
        db: Database session
        template_data: Template creation data
    
    Returns:
        Created template
    """
    template_dict = template_data.model_dump(exclude_unset=True)
    template = PlaybookTemplate(**template_dict)
    
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    return template

