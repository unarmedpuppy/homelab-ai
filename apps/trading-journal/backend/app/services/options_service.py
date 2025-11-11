"""
Options chain service.

Provides options chain data and Greeks information.
Note: Currently returns placeholder data. Future integration with Polygon.io or other options data providers.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

from app.models.trade import Trade
from app.schemas.options import (
    OptionChainResponse,
    OptionChainEntry,
    GreeksResponse,
    OptionType,
)


async def get_options_chain(
    db: AsyncSession,
    ticker: str,
    expiration_date: Optional[date] = None,
    option_type: Optional[OptionType] = None,
) -> OptionChainResponse:
    """
    Get options chain for a ticker.
    
    Note: This is a placeholder implementation. In production, this would integrate
    with an options data provider (e.g., Polygon.io) to fetch real-time options chain data.
    
    For now, this returns options data from existing trades in the database.
    
    Args:
        db: Database session
        ticker: Ticker symbol
        expiration_date: Optional expiration date filter
        option_type: Optional option type filter (CALL or PUT)
    
    Returns:
        OptionChainResponse with options chain data
    """
    # Build query for option trades
    query = select(Trade).where(
        and_(
            Trade.ticker == ticker.upper().strip(),
            Trade.trade_type == "OPTION",
        )
    )
    
    if expiration_date:
        query = query.where(Trade.expiration_date == expiration_date)
    
    if option_type:
        query = query.where(Trade.option_type == option_type.value)
    
    result = await db.execute(query)
    trades = result.scalars().all()
    
    # Convert trades to option chain entries
    chain_entries: List[OptionChainEntry] = []
    seen_contracts = set()  # Track (strike, expiration, type) to avoid duplicates
    
    for trade in trades:
        if not trade.strike_price or not trade.expiration_date or not trade.option_type:
            continue
        
        # Create unique key for contract
        contract_key = (
            trade.strike_price,
            trade.expiration_date,
            trade.option_type,
        )
        
        if contract_key in seen_contracts:
            continue
        
        seen_contracts.add(contract_key)
        
        # Calculate mid price if bid/ask available
        mid_price = None
        if trade.bid_price is not None and trade.ask_price is not None:
            mid_price = (trade.bid_price + trade.ask_price) / Decimal("2")
        elif trade.bid_price is not None:
            mid_price = trade.bid_price
        elif trade.ask_price is not None:
            mid_price = trade.ask_price
        
        # Calculate intrinsic value (for calls: max(0, spot - strike), for puts: max(0, strike - spot))
        # Note: We don't have current spot price, so we'll use entry_price as approximation
        intrinsic_value = None
        if trade.entry_price and trade.strike_price:
            if trade.option_type == "CALL":
                intrinsic_value = max(Decimal("0"), trade.entry_price - trade.strike_price)
            else:  # PUT
                intrinsic_value = max(Decimal("0"), trade.strike_price - trade.entry_price)
        
        # Calculate time value (premium - intrinsic value)
        time_value = None
        if mid_price is not None and intrinsic_value is not None:
            time_value = mid_price - intrinsic_value
        
        chain_entry = OptionChainEntry(
            strike_price=trade.strike_price,
            expiration_date=trade.expiration_date,
            option_type=OptionType(trade.option_type),
            delta=trade.delta,
            gamma=trade.gamma,
            theta=trade.theta,
            vega=trade.vega,
            rho=trade.rho,
            implied_volatility=trade.implied_volatility,
            volume=trade.volume,
            open_interest=trade.open_interest,
            bid_price=trade.bid_price,
            ask_price=trade.ask_price,
            bid_ask_spread=trade.bid_ask_spread,
            last_price=trade.entry_price,  # Use entry_price as last_price approximation
            mid_price=mid_price,
            intrinsic_value=intrinsic_value,
            time_value=time_value,
        )
        
        chain_entries.append(chain_entry)
    
    # Sort by strike price, then expiration, then type
    chain_entries.sort(key=lambda x: (x.strike_price, x.expiration_date, x.option_type.value))
    
    return OptionChainResponse(
        ticker=ticker.upper().strip(),
        expiration_date=expiration_date,
        option_type=option_type,
        chain=chain_entries,
        as_of=datetime.now(),
    )


async def get_options_chain_by_expiration(
    db: AsyncSession,
    ticker: str,
    expiration: date,
) -> OptionChainResponse:
    """
    Get options chain for a specific expiration date.
    
    Args:
        db: Database session
        ticker: Ticker symbol
        expiration: Expiration date
    
    Returns:
        OptionChainResponse with options chain for the expiration
    """
    return await get_options_chain(
        db=db,
        ticker=ticker,
        expiration_date=expiration,
    )


async def get_greeks(
    db: AsyncSession,
    ticker: str,
    strike_price: Optional[Decimal] = None,
    expiration_date: Optional[date] = None,
) -> GreeksResponse:
    """
    Get Greeks data for a ticker.
    
    Note: This is a placeholder implementation. In production, this would integrate
    with an options data provider to fetch real-time Greeks data.
    
    For now, this returns Greeks data from existing option trades in the database.
    
    Args:
        db: Database session
        ticker: Ticker symbol
        strike_price: Optional strike price filter
        expiration_date: Optional expiration date filter
    
    Returns:
        GreeksResponse with Greeks data
    """
    # Build query for option trades
    query = select(Trade).where(
        and_(
            Trade.ticker == ticker.upper().strip(),
            Trade.trade_type == "OPTION",
        )
    )
    
    if strike_price:
        query = query.where(Trade.strike_price == strike_price)
    
    if expiration_date:
        query = query.where(Trade.expiration_date == expiration_date)
    
    result = await db.execute(query)
    trades = result.scalars().all()
    
    # Convert trades to Greeks entries
    greeks_entries: List[OptionChainEntry] = []
    
    for trade in trades:
        if not trade.strike_price or not trade.expiration_date or not trade.option_type:
            continue
        
        # Only include if has Greeks data
        if not any([trade.delta, trade.gamma, trade.theta, trade.vega, trade.rho]):
            continue
        
        greeks_entry = OptionChainEntry(
            strike_price=trade.strike_price,
            expiration_date=trade.expiration_date,
            option_type=OptionType(trade.option_type),
            delta=trade.delta,
            gamma=trade.gamma,
            theta=trade.theta,
            vega=trade.vega,
            rho=trade.rho,
            implied_volatility=trade.implied_volatility,
            volume=trade.volume,
            open_interest=trade.open_interest,
            bid_price=trade.bid_price,
            ask_price=trade.ask_price,
            bid_ask_spread=trade.bid_ask_spread,
        )
        
        greeks_entries.append(greeks_entry)
    
    # Sort by strike price, then expiration
    greeks_entries.sort(key=lambda x: (x.strike_price, x.expiration_date))
    
    return GreeksResponse(
        ticker=ticker.upper().strip(),
        strike_price=strike_price,
        expiration_date=expiration_date,
        greeks=greeks_entries,
        as_of=datetime.now(),
    )

