"""
Options Flow API Routes
=======================

API endpoints for enhanced options flow data with pattern detection,
metrics, and chain analysis.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
import asyncio

from ...data.providers.unusual_whales import UnusualWhalesClient
from ...data.providers.options.pattern_detector import PatternDetector
from ...data.providers.options.metrics_calculator import OptionsMetricsCalculator
from ...data.providers.options.chain_analyzer import OptionsChainAnalyzer
from ...data.providers.sentiment.options_flow_sentiment import OptionsFlowSentimentProvider
from ...config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Global instances
_options_client: Optional[UnusualWhalesClient] = None
_pattern_detector: Optional[PatternDetector] = None
_metrics_calculator: Optional[OptionsMetricsCalculator] = None
_chain_analyzer: Optional[OptionsChainAnalyzer] = None
_sentiment_provider: Optional[OptionsFlowSentimentProvider] = None


def get_options_client() -> UnusualWhalesClient:
    """Get or create Unusual Whales client"""
    global _options_client
    if _options_client is None and settings.unusual_whales.api_key:
        _options_client = UnusualWhalesClient(
            settings.unusual_whales.api_key,
            settings.unusual_whales.base_url
        )
    return _options_client


def get_pattern_detector() -> PatternDetector:
    """Get or create pattern detector"""
    global _pattern_detector
    if _pattern_detector is None:
        _pattern_detector = PatternDetector()
    return _pattern_detector


def get_metrics_calculator() -> OptionsMetricsCalculator:
    """Get or create metrics calculator"""
    global _metrics_calculator
    if _metrics_calculator is None:
        _metrics_calculator = OptionsMetricsCalculator()
    return _metrics_calculator


def get_chain_analyzer() -> OptionsChainAnalyzer:
    """Get or create chain analyzer"""
    global _chain_analyzer
    if _chain_analyzer is None:
        _chain_analyzer = OptionsChainAnalyzer()
    return _chain_analyzer


def get_options_sentiment_provider() -> OptionsFlowSentimentProvider:
    """Get or create options sentiment provider"""
    global _sentiment_provider
    if _sentiment_provider is None:
        _sentiment_provider = OptionsFlowSentimentProvider()
    return _sentiment_provider


# Response Models
class OptionsFlowResponse(BaseModel):
    """Options flow response model"""
    symbol: str
    strike: float
    expiry: datetime
    option_type: str
    volume: int
    premium: float
    direction: str
    unusual: bool
    is_sweep: bool
    is_block: bool
    pattern_type: Optional[str]
    sweep_strength: float
    timestamp: datetime


class SweepResponse(BaseModel):
    """Sweep pattern response"""
    symbol: str
    expiry_date: str
    option_type: str
    strike_count: int
    total_premium: float
    strength: float
    timestamp: datetime
    flows: List[OptionsFlowResponse]


class PutCallRatiosResponse(BaseModel):
    """Put/Call ratios response"""
    volume_ratio: float
    premium_ratio: float
    oi_ratio: Optional[float]
    timestamp: datetime


class FlowMetricsResponse(BaseModel):
    """Flow metrics response"""
    total_volume: int
    total_premium: float
    call_volume: int
    put_volume: int
    call_premium: float
    put_premium: float
    bullish_flow: float
    bearish_flow: float
    unusual_count: int
    sweep_count: int
    block_count: int


class ChainAnalysisResponse(BaseModel):
    """Options chain analysis response"""
    max_pain: float
    gamma_exposure: float
    call_dominance: float
    put_dominance: float
    strike_concentration: Dict[str, float]
    high_volume_strikes: List[Dict[str, Any]]


@router.get("/status")
async def get_options_flow_status():
    """Get options flow provider status"""
    provider = get_options_sentiment_provider()
    client = get_options_client()
    
    return {
        "available": provider.is_available() if provider else False,
        "client_configured": client is not None,
        "api_key_set": bool(settings.unusual_whales.api_key)
    }


@router.get("/{symbol}", response_model=List[OptionsFlowResponse])
async def get_options_flow(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to retrieve"),
    include_patterns: bool = Query(default=True, description="Include pattern detection")
):
    """
    Get options flow data for a symbol with pattern detection
    
    Args:
        symbol: Stock symbol
        hours: Hours of historical data
        include_patterns: Whether to detect sweeps and blocks
    
    Returns:
        List of options flows with pattern information
    """
    client = get_options_client()
    
    if not client:
        raise HTTPException(
            status_code=503,
            detail="Options flow provider not available. Check API credentials."
        )
    
    try:
        async with client as uw_client:
            flows = await uw_client.get_options_flow(symbol.upper(), hours=hours)
        
        if include_patterns:
            detector = get_pattern_detector()
            flows = detector.detect_patterns(flows)
        
        return [
            OptionsFlowResponse(
                symbol=f.symbol,
                strike=f.strike,
                expiry=f.expiry,
                option_type=f.option_type,
                volume=f.volume,
                premium=f.premium,
                direction=f.direction.value,
                unusual=f.unusual,
                is_sweep=f.is_sweep,
                is_block=f.is_block,
                pattern_type=f.pattern_type,
                sweep_strength=f.sweep_strength,
                timestamp=f.timestamp
            )
            for f in flows
        ]
    
    except Exception as e:
        logger.error(f"Error getting options flow for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving options flow: {str(e)}"
        )


@router.get("/{symbol}/sweeps", response_model=List[SweepResponse])
async def get_sweeps(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze")
):
    """Get detected sweep patterns for a symbol"""
    client = get_options_client()
    
    if not client:
        raise HTTPException(status_code=503, detail="Options flow provider not available")
    
    try:
        async with client as uw_client:
            flows = await uw_client.get_options_flow(symbol.upper(), hours=hours)
        
        detector = get_pattern_detector()
        sweeps = detector._detect_sweeps(sorted(flows, key=lambda f: f.timestamp))
        
        result = []
        for sweep in sweeps:
            result.append(SweepResponse(
                symbol=sweep['symbol'],
                expiry_date=str(sweep['expiry']),
                option_type=sweep['option_type'],
                strike_count=sweep['strike_count'],
                total_premium=sweep['total_premium'],
                strength=sweep['strength'],
                timestamp=sweep['timestamp'],
                flows=[
                    OptionsFlowResponse(
                        symbol=f.symbol,
                        strike=f.strike,
                        expiry=f.expiry,
                        option_type=f.option_type,
                        volume=f.volume,
                        premium=f.premium,
                        direction=f.direction.value,
                        unusual=f.unusual,
                        is_sweep=f.is_sweep,
                        is_block=f.is_block,
                        pattern_type=f.pattern_type,
                        sweep_strength=f.sweep_strength,
                        timestamp=f.timestamp
                    )
                    for f in sweep['flows']
                ]
            ))
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting sweeps for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/blocks", response_model=List[OptionsFlowResponse])
async def get_blocks(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze")
):
    """Get detected block trades for a symbol"""
    client = get_options_client()
    
    if not client:
        raise HTTPException(status_code=503, detail="Options flow provider not available")
    
    try:
        async with client as uw_client:
            flows = await uw_client.get_options_flow(symbol.upper(), hours=hours)
        
        detector = get_pattern_detector()
        blocks = detector._detect_blocks(sorted(flows, key=lambda f: f.timestamp))
        
        return [
            OptionsFlowResponse(
                symbol=f.symbol,
                strike=f.strike,
                expiry=f.expiry,
                option_type=f.option_type,
                volume=f.volume,
                premium=f.premium,
                direction=f.direction.value,
                unusual=f.unusual,
                is_sweep=f.is_sweep,
                is_block=f.is_block,
                pattern_type=f.pattern_type,
                sweep_strength=f.sweep_strength,
                timestamp=f.timestamp
            )
            for f in blocks
        ]
    
    except Exception as e:
        logger.error(f"Error getting blocks for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/pc-ratio", response_model=PutCallRatiosResponse)
async def get_put_call_ratio(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze")
):
    """Get put/call ratios for a symbol"""
    client = get_options_client()
    
    if not client:
        raise HTTPException(status_code=503, detail="Options flow provider not available")
    
    try:
        async with client as uw_client:
            flows = await uw_client.get_options_flow(symbol.upper(), hours=hours)
        
        calculator = get_metrics_calculator()
        ratios = calculator.calculate_put_call_ratio(flows)
        
        return PutCallRatiosResponse(
            volume_ratio=ratios.volume_ratio,
            premium_ratio=ratios.premium_ratio,
            oi_ratio=ratios.oi_ratio,
            timestamp=ratios.timestamp or datetime.now()
        )
    
    except Exception as e:
        logger.error(f"Error getting P/C ratio for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/metrics", response_model=FlowMetricsResponse)
async def get_flow_metrics(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze")
):
    """Get comprehensive flow metrics for a symbol"""
    client = get_options_client()
    
    if not client:
        raise HTTPException(status_code=503, detail="Options flow provider not available")
    
    try:
        async with client as uw_client:
            flows = await uw_client.get_options_flow(symbol.upper(), hours=hours)
        
        detector = get_pattern_detector()
        flows = detector.detect_patterns(flows)
        
        calculator = get_metrics_calculator()
        metrics = calculator.calculate_flow_metrics(flows)
        
        return FlowMetricsResponse(
            total_volume=metrics.total_volume,
            total_premium=metrics.total_premium,
            call_volume=metrics.call_volume,
            put_volume=metrics.put_volume,
            call_premium=metrics.call_premium,
            put_premium=metrics.put_premium,
            bullish_flow=metrics.bullish_flow,
            bearish_flow=metrics.bearish_flow,
            unusual_count=metrics.unusual_count,
            sweep_count=metrics.sweep_count,
            block_count=metrics.block_count
        )
    
    except Exception as e:
        logger.error(f"Error getting flow metrics for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/chain", response_model=ChainAnalysisResponse)
async def get_chain_analysis(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze"),
    current_price: Optional[float] = Query(default=None, description="Current stock price for GEX")
):
    """Get options chain analysis (max pain, gamma exposure, etc.)"""
    client = get_options_client()
    
    if not client:
        raise HTTPException(status_code=503, detail="Options flow provider not available")
    
    try:
        async with client as uw_client:
            flows = await uw_client.get_options_flow(symbol.upper(), hours=hours)
        
        analyzer = get_chain_analyzer()
        analysis = analyzer.analyze_chain(flows, current_price)
        
        return ChainAnalysisResponse(
            max_pain=analysis.max_pain,
            gamma_exposure=analysis.gamma_exposure,
            call_dominance=analysis.call_dominance,
            put_dominance=analysis.put_dominance,
            strike_concentration={str(k): v for k, v in analysis.strike_concentration.items()},
            high_volume_strikes=[{"strike": s, "volume": v} for s, v in analysis.high_volume_strikes]
        )
    
    except Exception as e:
        logger.error(f"Error getting chain analysis for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/sentiment")
async def get_options_sentiment(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of data to analyze")
):
    """Get sentiment score based on options flow"""
    provider = get_options_sentiment_provider()
    
    if not provider.is_available():
        raise HTTPException(
            status_code=503,
            detail="Options flow sentiment provider not available"
        )
    
    try:
        sentiment = provider.get_sentiment(symbol.upper(), hours=hours)
        
        if sentiment is None:
            raise HTTPException(
                status_code=404,
                detail=f"No options flow sentiment data available for {symbol}"
            )
        
        return {
            "symbol": sentiment.symbol,
            "timestamp": sentiment.timestamp,
            "sentiment_score": sentiment.weighted_sentiment,
            "sentiment_level": sentiment.sentiment_level.value,
            "confidence": sentiment.confidence,
            "mention_count": sentiment.mention_count,
            "engagement_score": sentiment.engagement_score
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting options sentiment for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

