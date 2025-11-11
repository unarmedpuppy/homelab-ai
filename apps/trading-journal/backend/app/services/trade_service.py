"""
Trade service for business logic.

Handles all trade-related database operations and business rules.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, delete
from typing import Optional, List, Tuple
from datetime import datetime, date
from decimal import Decimal

from app.models.trade import Trade
from app.schemas.trade import TradeCreate, TradeUpdate


async def create_trade(db: AsyncSession, trade_data: TradeCreate) -> Trade:
    """
    Create a new trade.
    
    Args:
        db: Database session
        trade_data: Trade creation data
    
    Returns:
        Created trade
    """
    # Convert Pydantic model to dict, excluding None values
    trade_dict = trade_data.model_dump(exclude_unset=True)
    
    # Create trade instance
    trade = Trade(**trade_dict)
    
    # Calculate fields if trade is closed
    if trade.exit_price and trade.exit_quantity:
        trade.update_calculated_fields()
    
    # Add to session
    db.add(trade)
    await db.commit()
    await db.refresh(trade)
    
    return trade


async def get_trade(db: AsyncSession, trade_id: int) -> Optional[Trade]:
    """
    Get a trade by ID.
    
    Args:
        db: Database session
        trade_id: Trade ID
    
    Returns:
        Trade if found, None otherwise
    """
    result = await db.execute(select(Trade).where(Trade.id == trade_id))
    return result.scalar_one_or_none()


async def get_trades(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    ticker: Optional[str] = None,
    trade_type: Optional[str] = None,
    status: Optional[str] = None,
    side: Optional[str] = None,
) -> Tuple[List[Trade], int]:
    """
    Get paginated list of trades with filters.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        date_from: Filter trades from this date
        date_to: Filter trades up to this date
        ticker: Filter by ticker
        trade_type: Filter by trade type
        status: Filter by status
        side: Filter by side
    
    Returns:
        Tuple of (trades list, total count)
    """
    # Build query
    query = select(Trade)
    count_query = select(func.count()).select_from(Trade)
    
    # Apply filters
    conditions = []
    
    if date_from:
        conditions.append(Trade.entry_time >= datetime.combine(date_from, datetime.min.time()))
    
    if date_to:
        conditions.append(Trade.entry_time <= datetime.combine(date_to, datetime.max.time()))
    
    if ticker:
        conditions.append(Trade.ticker == ticker.upper())
    
    if trade_type:
        conditions.append(Trade.trade_type == trade_type)
    
    if status:
        conditions.append(Trade.status == status)
    
    if side:
        conditions.append(Trade.side == side)
    
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.order_by(Trade.entry_time.desc()).offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    trades = result.scalars().all()
    
    return list(trades), total


async def update_trade(
    db: AsyncSession,
    trade_id: int,
    trade_data: TradeUpdate
) -> Optional[Trade]:
    """
    Update a trade.
    
    Args:
        db: Database session
        trade_id: Trade ID
        trade_data: Trade update data
    
    Returns:
        Updated trade if found, None otherwise
    """
    # Get existing trade
    trade = await get_trade(db, trade_id)
    if not trade:
        return None
    
    # Update fields (only provided fields)
    update_data = trade_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(trade, field, value)
    
    # Recalculate fields if exit data changed
    if "exit_price" in update_data or "exit_quantity" in update_data:
        trade.update_calculated_fields()
    
    await db.commit()
    await db.refresh(trade)
    
    return trade


async def delete_trade(db: AsyncSession, trade_id: int) -> bool:
    """
    Delete a trade.
    
    Args:
        db: Database session
        trade_id: Trade ID
    
    Returns:
        True if deleted, False if not found
    """
    # Check if trade exists
    trade = await get_trade(db, trade_id)
    if not trade:
        return False
    
    # Delete using delete statement (SQLAlchemy 2.0 async)
    stmt = delete(Trade).where(Trade.id == trade_id)
    result = await db.execute(stmt)
    await db.commit()
    
    return result.rowcount > 0


async def bulk_create_trades(
    db: AsyncSession,
    trades_data: List[TradeCreate]
) -> List[Trade]:
    """
    Create multiple trades in bulk.
    
    Optimized to use bulk insert operations for better performance.
    
    Args:
        db: Database session
        trades_data: List of trade creation data
    
    Returns:
        List of created trades
    """
    if not trades_data:
        return []
    
    trades = []
    for trade_data in trades_data:
        trade_dict = trade_data.model_dump(exclude_unset=True)
        trade = Trade(**trade_dict)
        
        # Calculate fields if trade is closed
        if trade.exit_price and trade.exit_quantity:
            trade.update_calculated_fields()
        
        trades.append(trade)
    
    # Use bulk_save_objects for better performance with many trades
    db.add_all(trades)
    await db.commit()
    
    # Refresh all trades to get IDs and default values
    for trade in trades:
        await db.refresh(trade)
    
    return trades


async def search_trades(
    db: AsyncSession,
    q: str,
    tags: Optional[List[str]] = None,
    skip: int = 0,
    limit: int = 100,
) -> Tuple[List[Trade], int]:
    """
    Search trades by query string and tags.
    
    Args:
        db: Database session
        q: Search query (searches ticker, notes, playbook)
        tags: Optional list of tags to filter by
        skip: Number of records to skip
        limit: Maximum number of records to return
    
    Returns:
        Tuple of (trades list, total count)
    """
    # Build search conditions (ilike is case-insensitive, so no need for .lower())
    search_term = f"%{q}%"
    conditions = [
        or_(
            Trade.ticker.ilike(search_term),
            Trade.notes.ilike(search_term),
            Trade.playbook.ilike(search_term),
        )
    ]
    
    # Add tag filter if provided
    if tags:
        # PostgreSQL array contains operator - check if any tag matches
        tag_conditions = []
        for tag in tags:
            tag_conditions.append(Trade.tags.contains([tag]))
        if tag_conditions:
            conditions.append(or_(*tag_conditions))
    
    # Build query
    query = select(Trade).where(and_(*conditions))
    count_query = select(func.count()).select_from(Trade).where(and_(*conditions))
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination and ordering
    query = query.order_by(Trade.entry_time.desc()).offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    trades = result.scalars().all()
    
    return list(trades), total

