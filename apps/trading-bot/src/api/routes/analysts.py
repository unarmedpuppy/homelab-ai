"""
Analysts API Routes (T7: Analyst Agents)
=========================================

API endpoints for the analyst agents system.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

from ...core.agents import (
    get_analyst_registry,
    run_all_analysts,
    AnalystRecommendation,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Models
class AnalystConfig(BaseModel):
    """Configuration for an analyst"""
    enabled: bool = True
    weight: float = Field(default=1.0, ge=0.0, le=2.0)


class AnalyzeRequest(BaseModel):
    """Request to analyze a symbol"""
    symbol: str
    analysts: Optional[List[str]] = None  # Optional filter for specific analysts


class AnalystStatus(BaseModel):
    """Status of a single analyst"""
    name: str
    type: str
    enabled: bool
    weight: float


class RegistryStatus(BaseModel):
    """Status of the analyst registry"""
    total_analysts: int
    enabled_count: int
    analysts: Dict[str, AnalystStatus]


# Endpoints

@router.get("/status")
async def get_analysts_status() -> Dict[str, Any]:
    """
    Get status of all registered analysts

    Returns:
        Registry status including all analyst states
    """
    try:
        registry = get_analyst_registry()
        status = registry.get_status()
        return {
            "success": True,
            "data": status,
        }
    except Exception as e:
        logger.error(f"Error getting analyst status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_analysts() -> Dict[str, Any]:
    """
    List all registered analysts with their configurations

    Returns:
        List of analyst information
    """
    try:
        registry = get_analyst_registry()
        analysts = registry.get_all()

        analyst_list = []
        for name, analyst in analysts.items():
            analyst_list.append({
                "name": name,
                "type": analyst.analyst_type,
                "enabled": analyst.enabled,
                "weight": analyst.weight,
            })

        return {
            "success": True,
            "data": analyst_list,
            "count": len(analyst_list),
        }
    except Exception as e:
        logger.error(f"Error listing analysts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{analyst_name}/enable")
async def enable_analyst(analyst_name: str) -> Dict[str, Any]:
    """
    Enable an analyst

    Args:
        analyst_name: Name of the analyst to enable

    Returns:
        Updated analyst status
    """
    try:
        registry = get_analyst_registry()
        success = registry.set_enabled(analyst_name, True)

        if not success:
            raise HTTPException(status_code=404, detail=f"Analyst '{analyst_name}' not found")

        analyst = registry.get(analyst_name)
        return {
            "success": True,
            "message": f"Analyst '{analyst_name}' enabled",
            "analyst": {
                "name": analyst_name,
                "type": analyst.analyst_type,
                "enabled": analyst.enabled,
                "weight": analyst.weight,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling analyst {analyst_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{analyst_name}/disable")
async def disable_analyst(analyst_name: str) -> Dict[str, Any]:
    """
    Disable an analyst

    Args:
        analyst_name: Name of the analyst to disable

    Returns:
        Updated analyst status
    """
    try:
        registry = get_analyst_registry()
        success = registry.set_enabled(analyst_name, False)

        if not success:
            raise HTTPException(status_code=404, detail=f"Analyst '{analyst_name}' not found")

        analyst = registry.get(analyst_name)
        return {
            "success": True,
            "message": f"Analyst '{analyst_name}' disabled",
            "analyst": {
                "name": analyst_name,
                "type": analyst.analyst_type,
                "enabled": analyst.enabled,
                "weight": analyst.weight,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling analyst {analyst_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{analyst_name}/weight")
async def set_analyst_weight(
    analyst_name: str,
    weight: float = Query(..., ge=0.0, le=2.0, description="Weight for this analyst (0.0-2.0)")
) -> Dict[str, Any]:
    """
    Set analyst weight for aggregation

    Args:
        analyst_name: Name of the analyst
        weight: New weight value (0.0 to 2.0)

    Returns:
        Updated analyst status
    """
    try:
        registry = get_analyst_registry()
        success = registry.set_weight(analyst_name, weight)

        if not success:
            raise HTTPException(status_code=404, detail=f"Analyst '{analyst_name}' not found")

        analyst = registry.get(analyst_name)
        return {
            "success": True,
            "message": f"Analyst '{analyst_name}' weight set to {weight}",
            "analyst": {
                "name": analyst_name,
                "type": analyst.analyst_type,
                "enabled": analyst.enabled,
                "weight": analyst.weight,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting analyst weight for {analyst_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/{symbol}")
async def analyze_symbol(
    symbol: str,
    include_raw: bool = Query(False, description="Include raw data in response"),
) -> Dict[str, Any]:
    """
    Run analysis on a symbol using all enabled analysts

    Args:
        symbol: Trading symbol to analyze (e.g., AAPL, TSLA)
        include_raw: Whether to include raw data in response

    Returns:
        Aggregated analysis from all enabled analysts
    """
    try:
        # Normalize symbol
        symbol = symbol.upper().strip()
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")

        # Run analysis
        result = await run_all_analysts(symbol)

        # Convert to dict
        response_data = result.to_dict()

        # Optionally exclude raw_data from reports
        if not include_raw:
            for report in response_data.get("reports", []):
                report.pop("raw_data", None)

        return {
            "success": True,
            "symbol": symbol,
            "data": response_data,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/{symbol}/{analyst_type}")
async def analyze_symbol_single(
    symbol: str,
    analyst_type: str,
    include_raw: bool = Query(False, description="Include raw data in response"),
) -> Dict[str, Any]:
    """
    Run analysis on a symbol using a specific analyst

    Args:
        symbol: Trading symbol to analyze
        analyst_type: Type of analyst (technical, sentiment, news, fundamentals)
        include_raw: Whether to include raw data in response

    Returns:
        Analysis from the specified analyst
    """
    try:
        # Normalize
        symbol = symbol.upper().strip()
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")

        # Get the analyst
        registry = get_analyst_registry()

        # Find analyst by type
        analyst = None
        analyst_name = None
        for name, a in registry.get_all().items():
            if a.analyst_type == analyst_type:
                analyst = a
                analyst_name = name
                break

        if analyst is None:
            raise HTTPException(
                status_code=404,
                detail=f"Analyst type '{analyst_type}' not found. "
                       f"Available types: technical, sentiment, news, fundamentals"
            )

        # Run single analyst
        report = await analyst.analyze(symbol)

        # Convert to dict
        response_data = report.to_dict()

        # Optionally exclude raw_data
        if not include_raw:
            response_data.pop("raw_data", None)

        return {
            "success": True,
            "symbol": symbol,
            "analyst": analyst_name,
            "data": response_data,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing {symbol} with {analyst_type}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/batch")
async def analyze_batch(
    symbols: List[str] = Query(..., description="List of symbols to analyze"),
    include_raw: bool = Query(False, description="Include raw data in response"),
) -> Dict[str, Any]:
    """
    Run analysis on multiple symbols

    Args:
        symbols: List of trading symbols to analyze
        include_raw: Whether to include raw data in response

    Returns:
        Aggregated analyses for all symbols
    """
    import asyncio

    try:
        if not symbols:
            raise HTTPException(status_code=400, detail="At least one symbol is required")

        if len(symbols) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 symbols per batch")

        # Normalize symbols
        normalized = [s.upper().strip() for s in symbols if s.strip()]

        # Run analyses concurrently
        tasks = [run_all_analysts(symbol) for symbol in normalized]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        analyses = {}
        errors = []

        for symbol, result in zip(normalized, results):
            if isinstance(result, Exception):
                errors.append({"symbol": symbol, "error": str(result)})
            else:
                data = result.to_dict()
                if not include_raw:
                    for report in data.get("reports", []):
                        report.pop("raw_data", None)
                analyses[symbol] = data

        return {
            "success": True,
            "analyzed_count": len(analyses),
            "error_count": len(errors),
            "analyses": analyses,
            "errors": errors if errors else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
