"""
AI Agent Helper API endpoints.

Provides endpoints for parsing natural language trade descriptions,
batch trade creation, and trade suggestions based on historical data.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.dependencies import verify_api_key, DatabaseSession
from app.schemas.ai import (
    ParseTradeRequest,
    ParseTradeResponse,
    BatchCreateRequest,
    BatchCreateResponse,
    TradeSuggestion,
)
from app.schemas.trade import TradeResponse
from app.services.ai_service import (
    parse_trade_from_description,
    batch_create_trades_from_descriptions,
    get_trade_suggestions,
)

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.post("/parse-trade", response_model=ParseTradeResponse)
async def parse_trade_endpoint(
    request: ParseTradeRequest,
):
    """
    Parse a trade from natural language description.
    
    This endpoint helps AI agents convert natural language trade descriptions
    into structured trade data ready for creation.
    
    The parser extracts:
    - Ticker symbol
    - Trade type (STOCK, OPTION, CRYPTO_SPOT, etc.)
    - Side (LONG/SHORT)
    - Entry/exit prices and quantities
    - Entry/exit dates
    - Status (open/closed)
    - Playbook/strategy
    
    Returns a confidence score (0.0 to 1.0) indicating how well the trade
    could be parsed, along with warnings and missing fields.
    """
    try:
        result = await parse_trade_from_description(
            description=request.description,
            raw_data=request.raw_data,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error parsing trade: {str(e)}"
        )


@router.post("/batch-create", response_model=BatchCreateResponse)
async def batch_create_trades_endpoint(
    request: BatchCreateRequest,
    db: DatabaseSession,
):
    """
    Batch create trades from descriptions or raw data.
    
    This endpoint allows AI agents to create multiple trades at once from
    natural language descriptions or structured data.
    
    Each trade in the request is parsed and validated. Trades with low
    confidence (< 0.5) are not created and are returned in the failed_trades
    list with error details.
    
    Returns a summary of created and failed trades.
    """
    try:
        # Convert request to list of dictionaries
        trade_requests = [
            {
                "description": trade_req.description,
                "raw_data": trade_req.raw_data,
            }
            for trade_req in request.trades
        ]
        
        result = await batch_create_trades_from_descriptions(
            db=db,
            trade_requests=trade_requests,
        )
        
        # Convert created trades to TradeResponse
        created_trade_responses = [
            TradeResponse.model_validate(trade, from_attributes=True) for trade in result["created_trades"]
        ]
        
        return BatchCreateResponse(
            created_trades=created_trade_responses,
            failed_trades=result["failed_trades"],
            total_requested=result["total_requested"],
            total_created=result["total_created"],
            total_failed=result["total_failed"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error batch creating trades: {str(e)}"
        )


@router.get("/suggestions/{ticker}", response_model=TradeSuggestion)
async def get_trade_suggestions_endpoint(
    ticker: str,
    db: DatabaseSession,
):
    """
    Get trade suggestions based on historical trades for a ticker.
    
    Analyzes historical closed trades for the given ticker and suggests:
    - Entry price (average from recent trades)
    - Quantity (average from recent trades)
    - Trade type (most common)
    - Side (most common: LONG/SHORT)
    - Playbook/strategy (most common)
    - Win rate and average P&L
    - Additional insights and notes
    
    Useful for AI agents to suggest trade parameters based on historical patterns.
    """
    try:
        suggestion = await get_trade_suggestions(
            db=db,
            ticker=ticker,
        )
        return suggestion
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting trade suggestions: {str(e)}"
        )

