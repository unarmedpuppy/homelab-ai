"""
Trade CRUD API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.api.dependencies import RequireAuth, DatabaseSession, verify_api_key
from app.schemas.trade import (
    TradeCreate,
    TradeUpdate,
    TradeResponse,
    TradeListResponse,
)
from app.services.trade_service import (
    create_trade,
    get_trade,
    get_trades,
    update_trade,
    delete_trade,
    bulk_create_trades,
    search_trades,
)

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.get("", response_model=TradeListResponse)
async def list_trades(
    db: DatabaseSession,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    date_from: Optional[str] = Query(None, description="Filter trades from this date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter trades up to this date (YYYY-MM-DD)"),
    ticker: Optional[str] = Query(None, min_length=1, max_length=20, description="Filter by ticker"),
    trade_type: Optional[str] = Query(None, description="Filter by trade type (STOCK, OPTION, CRYPTO_SPOT, CRYPTO_PERP, PREDICTION_MARKET)"),
    status: Optional[str] = Query(None, description="Filter by status (open, closed, partial)"),
    side: Optional[str] = Query(None, description="Filter by side (LONG, SHORT)"),
):
    """
    Get paginated list of trades with optional filters.
    
    Supports filtering by date range, ticker, trade type, status, and side.
    """
    from datetime import datetime
    
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
    
    trades, total = await get_trades(
        db=db,
        skip=skip,
        limit=limit,
        date_from=date_from_parsed,
        date_to=date_to_parsed,
        ticker=ticker,
        trade_type=trade_type,
        status=status,
        side=side,
    )
    
    return TradeListResponse(
        trades=[TradeResponse.model_validate(trade) for trade in trades],
        total=total,
        limit=limit,
        offset=skip,
        has_more=(skip + limit) < total,
    )


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade_by_id(
    trade_id: int,
    db: DatabaseSession,
):
    """
    Get a single trade by ID.
    """
    trade = await get_trade(db, trade_id)
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trade with ID {trade_id} not found"
        )
    
    return TradeResponse.model_validate(trade)


@router.post("", response_model=TradeResponse, status_code=status.HTTP_201_CREATED)
async def create_new_trade(
    trade_data: TradeCreate,
    db: DatabaseSession,
):
    """
    Create a new trade.
    """
    trade = await create_trade(db, trade_data)
    return TradeResponse.model_validate(trade)


@router.put("/{trade_id}", response_model=TradeResponse)
async def update_trade_by_id(
    trade_id: int,
    trade_data: TradeUpdate,
    db: DatabaseSession,
):
    """
    Update a trade (full update).
    """
    trade = await update_trade(db, trade_id, trade_data)
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trade with ID {trade_id} not found"
        )
    
    return TradeResponse.model_validate(trade)


@router.patch("/{trade_id}", response_model=TradeResponse)
async def patch_trade_by_id(
    trade_id: int,
    trade_data: TradeUpdate,
    db: DatabaseSession,
):
    """
    Partially update a trade.
    """
    trade = await update_trade(db, trade_id, trade_data)
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trade with ID {trade_id} not found"
        )
    
    return TradeResponse.model_validate(trade)


@router.delete("/{trade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trade_by_id(
    trade_id: int,
    db: DatabaseSession,
):
    """
    Delete a trade.
    """
    deleted = await delete_trade(db, trade_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trade with ID {trade_id} not found"
        )


@router.post("/bulk", response_model=List[TradeResponse], status_code=status.HTTP_201_CREATED)
async def bulk_create_trades_endpoint(
    trades_data: List[TradeCreate],
    db: DatabaseSession,
):
    """
    Create multiple trades in bulk.
    """
    if len(trades_data) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 trades allowed per bulk create"
        )
    
    trades = await bulk_create_trades(db, trades_data)
    return [TradeResponse.model_validate(trade) for trade in trades]


@router.get("/search", response_model=TradeListResponse)
async def search_trades_endpoint(
    db: DatabaseSession,
    q: str = Query(..., min_length=1, description="Search query"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Search trades by query string and optional tags.
    
    Searches in ticker, notes, and playbook fields.
    """
    tags_list = None
    if tags:
        tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    trades, total = await search_trades(
        db=db,
        q=q,
        tags=tags_list,
        skip=skip,
        limit=limit,
    )
    
    return TradeListResponse(
        trades=[TradeResponse.model_validate(trade) for trade in trades],
        total=total,
        limit=limit,
        offset=skip,
        has_more=(skip + limit) < total,
    )

