"""
Confluence Calculator API Routes
=================================

API endpoints for confluence calculation combining technical indicators,
sentiment analysis, and options flow data.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel
import logging
import pandas as pd
from datetime import datetime

from ...core.confluence import ConfluenceCalculator, ConfluenceScore, ConfluenceLevel
from ...data.providers.market_data import DataProviderManager, DataProviderType
from ...config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Global calculator instance
_calculator: Optional[ConfluenceCalculator] = None


def get_calculator() -> ConfluenceCalculator:
    """Get or create confluence calculator instance"""
    global _calculator
    if _calculator is None:
        _calculator = ConfluenceCalculator()
    return _calculator


# Response Models
class TechnicalScoreResponse(BaseModel):
    """Technical score response"""
    rsi_score: float
    sma_score: float
    volume_score: float
    bollinger_score: float
    overall_score: float
    directional_bias: float


class SentimentScoreResponse(BaseModel):
    """Sentiment score response"""
    sentiment_score: float
    confidence: float
    mention_count: int


class OptionsFlowScoreResponse(BaseModel):
    """Options flow score response"""
    flow_score: float
    confidence: float
    unusual_activity: bool


class ConfluenceBreakdownResponse(BaseModel):
    """Confluence breakdown response"""
    technical: Optional[TechnicalScoreResponse] = None
    sentiment: Optional[SentimentScoreResponse] = None
    options_flow: Optional[OptionsFlowScoreResponse] = None
    
    technical_weight: float
    sentiment_weight: float
    options_flow_weight: float
    
    technical_raw: Optional[float] = None
    sentiment_raw: Optional[float] = None
    options_flow_raw: Optional[float] = None


class ConfluenceScoreResponse(BaseModel):
    """Confluence score response"""
    symbol: str
    timestamp: datetime
    confluence_score: float  # 0.0 to 1.0
    directional_bias: float  # -1.0 to 1.0
    confluence_level: str
    confidence: float
    
    breakdown: ConfluenceBreakdownResponse
    
    components_used: list[str]
    meets_minimum_threshold: bool
    meets_high_threshold: bool
    
    volume_trend: str
    metadata: dict


@router.get("/status")
async def confluence_status():
    """Get confluence calculator status"""
    calculator = get_calculator()
    
    return {
        "available": True,
        "use_sentiment": calculator.use_sentiment,
        "use_options_flow": calculator.use_options_flow,
        "min_confluence": calculator.config.min_confluence,
        "high_confluence": calculator.config.high_confluence,
        "weights": {
            "technical": calculator.config.weight_technical,
            "sentiment": calculator.config.weight_sentiment,
            "options_flow": calculator.config.weight_options_flow
        }
    }


@router.get("/{symbol}", response_model=ConfluenceScoreResponse)
async def get_confluence(
    symbol: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of sentiment data to analyze"),
    timeframe: str = Query(default="5m", description="Market data timeframe"),
    use_sentiment: Optional[bool] = Query(default=None, description="Override sentiment usage"),
    use_options_flow: Optional[bool] = Query(default=None, description="Override options flow usage")
):
    """
    Get confluence score for a symbol
    
    Combines technical indicators, sentiment analysis, and options flow data
    into a unified confluence score.
    
    Args:
        symbol: Stock symbol (e.g., AAPL, SPY)
        hours: Hours of sentiment data to analyze
        timeframe: Market data timeframe (e.g., "5m", "1h", "1d")
        use_sentiment: Override sentiment usage (default: from settings)
        use_options_flow: Override options flow usage (default: from settings)
    
    Returns:
        Confluence score with breakdown
    """
    calculator = get_calculator()
    
    # Temporarily override settings if requested
    original_sentiment = calculator.use_sentiment
    original_options = calculator.use_options_flow
    
    try:
        if use_sentiment is not None:
            calculator.use_sentiment = use_sentiment
        if use_options_flow is not None:
            calculator.use_options_flow = use_options_flow
        
        # Fetch market data
        # TODO: Integrate with DataProviderManager for real data
        # For now, this would need market data passed in or fetched
        # This is a placeholder that shows the structure
        
        # In production, you'd fetch market data here:
        # data_provider = DataProviderManager(...)
        # market_data = await data_provider.get_historical_data(symbol, timeframe, bars=100)
        
        # For now, return an error indicating market data is needed
        raise HTTPException(
            status_code=501,
            detail="Market data fetching not yet integrated. Provide market_data or implement DataProviderManager integration."
        )
        
        # Once market data is available:
        # confluence = calculator.calculate_confluence(
        #     symbol.upper(),
        #     market_data,
        #     sentiment_hours=hours
        # )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating confluence for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating confluence: {str(e)}"
        )
    finally:
        # Restore original settings
        calculator.use_sentiment = original_sentiment
        calculator.use_options_flow = original_options


@router.post("/{symbol}", response_model=ConfluenceScoreResponse)
async def calculate_confluence_with_data(
    symbol: str,
    market_data: dict,  # Would be a proper Pydantic model in production
    hours: int = Query(default=24, ge=1, le=168, description="Hours of sentiment data"),
    use_sentiment: Optional[bool] = Query(default=None),
    use_options_flow: Optional[bool] = Query(default=None)
):
    """
    Calculate confluence score with provided market data
    
    Args:
        symbol: Stock symbol
        market_data: Market data dictionary with OHLCV data
        hours: Hours of sentiment data
        use_sentiment: Override sentiment usage
        use_options_flow: Override options flow usage
    
    Returns:
        Confluence score
    """
    calculator = get_calculator()
    
    # Convert market_data dict to DataFrame
    try:
        df = pd.DataFrame(market_data)
        
        # Validate required columns
        required = ['close']
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {missing}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid market_data format: {str(e)}"
        )
    
    # Override settings temporarily
    original_sentiment = calculator.use_sentiment
    original_options = calculator.use_options_flow
    
    try:
        if use_sentiment is not None:
            calculator.use_sentiment = use_sentiment
        if use_options_flow is not None:
            calculator.use_options_flow = use_options_flow
        
        confluence = calculator.calculate_confluence(
            symbol.upper(),
            df,
            sentiment_hours=hours
        )
        
        if confluence is None:
            raise HTTPException(
                status_code=404,
                detail=f"Could not calculate confluence for {symbol}. Insufficient data."
            )
        
        # Build response
        breakdown_response = ConfluenceBreakdownResponse(
            technical=TechnicalScoreResponse(
                rsi_score=confluence.breakdown.technical.rsi_score if confluence.breakdown.technical else 0.0,
                sma_score=confluence.breakdown.technical.sma_score if confluence.breakdown.technical else 0.0,
                volume_score=confluence.breakdown.technical.volume_score if confluence.breakdown.technical else 0.0,
                bollinger_score=confluence.breakdown.technical.bollinger_score if confluence.breakdown.technical else 0.0,
                overall_score=confluence.breakdown.technical.overall_score if confluence.breakdown.technical else 0.0,
                directional_bias=confluence.breakdown.technical.directional_bias if confluence.breakdown.technical else 0.0
            ) if confluence.breakdown.technical else None,
            sentiment=SentimentScoreResponse(
                sentiment_score=confluence.breakdown.sentiment.sentiment_score if confluence.breakdown.sentiment else 0.0,
                confidence=confluence.breakdown.sentiment.confidence if confluence.breakdown.sentiment else 0.0,
                mention_count=confluence.breakdown.sentiment.mention_count if confluence.breakdown.sentiment else 0
            ) if confluence.breakdown.sentiment else None,
            options_flow=OptionsFlowScoreResponse(
                flow_score=confluence.breakdown.options_flow.flow_score if confluence.breakdown.options_flow else 0.0,
                confidence=confluence.breakdown.options_flow.confidence if confluence.breakdown.options_flow else 0.0,
                unusual_activity=confluence.breakdown.options_flow.unusual_activity if confluence.breakdown.options_flow else False
            ) if confluence.breakdown.options_flow else None,
            technical_weight=confluence.breakdown.technical_weight,
            sentiment_weight=confluence.breakdown.sentiment_weight,
            options_flow_weight=confluence.breakdown.options_flow_weight,
            technical_raw=confluence.breakdown.technical_raw,
            sentiment_raw=confluence.breakdown.sentiment_raw,
            options_flow_raw=confluence.breakdown.options_flow_raw
        )
        
        return ConfluenceScoreResponse(
            symbol=confluence.symbol,
            timestamp=confluence.timestamp,
            confluence_score=confluence.confluence_score,
            directional_bias=confluence.directional_bias,
            confluence_level=confluence.confluence_level.value,
            confidence=confluence.confidence,
            breakdown=breakdown_response,
            components_used=confluence.components_used,
            meets_minimum_threshold=confluence.meets_minimum_threshold,
            meets_high_threshold=confluence.meets_high_threshold,
            volume_trend=confluence.volume_trend,
            metadata=confluence.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating confluence for {symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating confluence: {str(e)}"
        )
    finally:
        calculator.use_sentiment = original_sentiment
        calculator.use_options_flow = original_options

