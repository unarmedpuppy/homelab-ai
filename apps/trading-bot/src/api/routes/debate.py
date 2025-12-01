"""
Debate Room API Routes (T8: Bull vs Bear Debate)
=================================================

API endpoints for conducting and viewing analyst debates.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

from ...core.agents import (
    get_debate_room,
    conduct_debate,
    DebatePosition,
    VerdictType,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Response Models
class DebateStartRequest(BaseModel):
    """Request to start a debate"""
    symbol: str
    num_rounds: Optional[int] = 3


class DebateSummary(BaseModel):
    """Summary of a debate for list views"""
    id: str
    symbol: str
    status: str
    verdict: Optional[str]
    confidence: Optional[float]
    bull_team: List[str]
    bear_team: List[str]
    rounds_count: int
    started_at: str
    ended_at: Optional[str]


# Endpoints

@router.get("/status")
async def get_debate_room_status() -> Dict[str, Any]:
    """
    Get debate room status and configuration

    Returns:
        Debate room status including history count
    """
    try:
        room = get_debate_room()
        history = room.get_history(limit=100)

        # Calculate stats
        total_debates = len(history)
        completed = sum(1 for d in history if d.status == "completed")
        bull_wins = sum(1 for d in history if d.verdict and d.verdict.verdict in [VerdictType.BUY, VerdictType.STRONG_BUY])
        bear_wins = sum(1 for d in history if d.verdict and d.verdict.verdict in [VerdictType.SELL, VerdictType.STRONG_SELL])

        return {
            "success": True,
            "data": {
                "num_rounds": room.num_rounds,
                "min_analysts_per_side": room.min_analysts_per_side,
                "total_debates": total_debates,
                "completed_debates": completed,
                "bull_wins": bull_wins,
                "bear_wins": bear_wins,
                "no_consensus": total_debates - bull_wins - bear_wins,
            }
        }
    except Exception as e:
        logger.error(f"Error getting debate room status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start/{symbol}")
async def start_debate(
    symbol: str,
    num_rounds: int = Query(default=3, ge=1, le=5, description="Number of debate rounds"),
) -> Dict[str, Any]:
    """
    Start a new debate on a symbol

    Args:
        symbol: Trading symbol to debate (e.g., AAPL, TSLA)
        num_rounds: Number of debate rounds (1-5)

    Returns:
        Complete debate record with all rounds and verdict
    """
    try:
        # Normalize symbol
        symbol = symbol.upper().strip()
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")

        # Get or configure debate room
        room = get_debate_room()
        room.num_rounds = num_rounds

        # Conduct debate
        record = await room.conduct_debate(symbol)

        return {
            "success": True,
            "data": record.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting debate for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_debate_history(
    limit: int = Query(default=20, ge=1, le=100, description="Number of debates to return"),
    symbol: Optional[str] = Query(default=None, description="Filter by symbol"),
    verdict: Optional[str] = Query(default=None, description="Filter by verdict type"),
) -> Dict[str, Any]:
    """
    Get debate history

    Args:
        limit: Maximum number of debates to return
        symbol: Optional filter by symbol
        verdict: Optional filter by verdict type (strong_buy, buy, hold, sell, strong_sell, no_consensus)

    Returns:
        List of debate summaries
    """
    try:
        room = get_debate_room()
        history = room.get_history(limit=limit * 2)  # Get extra for filtering

        # Apply filters
        filtered = history
        if symbol:
            symbol = symbol.upper().strip()
            filtered = [d for d in filtered if d.symbol == symbol]

        if verdict:
            try:
                verdict_type = VerdictType(verdict.lower())
                filtered = [d for d in filtered if d.verdict and d.verdict.verdict == verdict_type]
            except ValueError:
                pass  # Invalid verdict type, skip filter

        # Limit and convert to summaries
        debates = filtered[:limit]
        summaries = []
        for d in debates:
            summaries.append({
                "id": d.id,
                "symbol": d.symbol,
                "status": d.status,
                "verdict": d.verdict.verdict.value if d.verdict else None,
                "confidence": d.verdict.confidence if d.verdict else None,
                "bull_team": d.bull_team,
                "bear_team": d.bear_team,
                "rounds_count": len(d.rounds),
                "total_arguments": d.total_arguments,
                "started_at": d.started_at.isoformat(),
                "ended_at": d.ended_at.isoformat() if d.ended_at else None,
            })

        return {
            "success": True,
            "count": len(summaries),
            "data": summaries,
        }
    except Exception as e:
        logger.error(f"Error getting debate history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{debate_id}")
async def get_debate(debate_id: str) -> Dict[str, Any]:
    """
    Get a specific debate by ID

    Args:
        debate_id: Debate ID

    Returns:
        Complete debate record
    """
    try:
        room = get_debate_room()
        record = room.get_debate(debate_id)

        if not record:
            raise HTTPException(status_code=404, detail=f"Debate '{debate_id}' not found")

        return {
            "success": True,
            "data": record.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting debate {debate_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{debate_id}/rounds")
async def get_debate_rounds(debate_id: str) -> Dict[str, Any]:
    """
    Get all rounds from a specific debate

    Args:
        debate_id: Debate ID

    Returns:
        List of debate rounds with arguments
    """
    try:
        room = get_debate_room()
        record = room.get_debate(debate_id)

        if not record:
            raise HTTPException(status_code=404, detail=f"Debate '{debate_id}' not found")

        return {
            "success": True,
            "debate_id": debate_id,
            "symbol": record.symbol,
            "rounds_count": len(record.rounds),
            "data": [r.to_dict() for r in record.rounds],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting debate rounds for {debate_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{debate_id}/verdict")
async def get_debate_verdict(debate_id: str) -> Dict[str, Any]:
    """
    Get the verdict from a specific debate

    Args:
        debate_id: Debate ID

    Returns:
        Debate verdict with reasoning
    """
    try:
        room = get_debate_room()
        record = room.get_debate(debate_id)

        if not record:
            raise HTTPException(status_code=404, detail=f"Debate '{debate_id}' not found")

        if not record.verdict:
            raise HTTPException(status_code=400, detail="Debate not yet completed")

        return {
            "success": True,
            "debate_id": debate_id,
            "symbol": record.symbol,
            "data": record.verdict.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting debate verdict for {debate_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{debate_id}/arguments")
async def get_debate_arguments(
    debate_id: str,
    position: Optional[str] = Query(default=None, description="Filter by position (bull/bear)"),
    round_num: Optional[int] = Query(default=None, description="Filter by round number"),
) -> Dict[str, Any]:
    """
    Get all arguments from a debate with optional filtering

    Args:
        debate_id: Debate ID
        position: Optional filter by position (bull/bear)
        round_num: Optional filter by round number

    Returns:
        List of arguments
    """
    try:
        room = get_debate_room()
        record = room.get_debate(debate_id)

        if not record:
            raise HTTPException(status_code=404, detail=f"Debate '{debate_id}' not found")

        # Collect all arguments
        arguments = []
        for round in record.rounds:
            if round_num is not None and round.round_number != round_num:
                continue

            for arg in round.bull_arguments:
                if position is None or position.lower() == "bull":
                    arguments.append(arg.to_dict())

            for arg in round.bear_arguments:
                if position is None or position.lower() == "bear":
                    arguments.append(arg.to_dict())

        return {
            "success": True,
            "debate_id": debate_id,
            "symbol": record.symbol,
            "arguments_count": len(arguments),
            "data": arguments,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting debate arguments for {debate_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_debate(
    symbols: List[str] = Query(..., description="List of symbols to debate"),
    num_rounds: int = Query(default=3, ge=1, le=5, description="Number of debate rounds"),
) -> Dict[str, Any]:
    """
    Conduct debates on multiple symbols

    Args:
        symbols: List of symbols to debate (max 5)
        num_rounds: Number of debate rounds per symbol

    Returns:
        Results for all debates
    """
    import asyncio

    try:
        if not symbols:
            raise HTTPException(status_code=400, detail="At least one symbol is required")

        if len(symbols) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 symbols per batch")

        # Normalize symbols
        normalized = [s.upper().strip() for s in symbols if s.strip()]

        # Get debate room
        room = get_debate_room()
        room.num_rounds = num_rounds

        # Run debates concurrently
        tasks = [room.conduct_debate(symbol) for symbol in normalized]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        debates = {}
        errors = []

        for symbol, result in zip(normalized, results):
            if isinstance(result, Exception):
                errors.append({"symbol": symbol, "error": str(result)})
            else:
                debates[symbol] = {
                    "id": result.id,
                    "verdict": result.verdict.verdict.value if result.verdict else None,
                    "confidence": result.verdict.confidence if result.verdict else None,
                    "summary": result.verdict.summary if result.verdict else None,
                    "recommended_action": result.verdict.recommended_action if result.verdict else None,
                }

        return {
            "success": True,
            "debated_count": len(debates),
            "error_count": len(errors),
            "debates": debates,
            "errors": errors if errors else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch debate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
