"""
Basic API Endpoints
==================

Simple API endpoints for quotes and historical data.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from ...data.providers.market_data import DataProviderManager, DataProviderType
from ...api.schemas.trading import MarketDataResponse
from ...config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize data provider manager
data_manager = None

def get_data_manager():
    """Get data provider manager"""
    global data_manager
    if data_manager is None:
        # Create manager with available providers
        providers = [
            (DataProviderType.YAHOO_FINANCE, None),
        ]
        
        # Add other providers if API keys are available
        if hasattr(settings, 'alpha_vantage_api_key') and settings.alpha_vantage_api_key:
            providers.append((DataProviderType.ALPHA_VANTAGE, settings.alpha_vantage_api_key))
        
        if hasattr(settings, 'polygon_api_key') and settings.polygon_api_key:
            providers.append((DataProviderType.POLYGON, settings.polygon_api_key))
        
        data_manager = DataProviderManager(providers)
    
    return data_manager

@router.get("/")
async def get_market_data_info():
    """Get information about available market data endpoints"""
    return {
        "service": "Market Data API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/market-data/health",
            "providers": "/api/market-data/providers", 
            "quote": "/api/market-data/quote/{symbol}",
            "historical": "/api/market-data/historical/{symbol}",
            "search": "/api/market-data/search?query={query}",
            "multiple_quotes": "/api/market-data/quotes?symbols={symbol1,symbol2,...}"
        },
        "examples": {
            "get_quote": "/api/market-data/quote/AAPL",
            "get_historical": "/api/market-data/historical/AAPL?days=30",
            "search_symbols": "/api/market-data/search?query=AAPL",
            "multiple_quotes": "/api/market-data/quotes?symbols=AAPL,MSFT,GOOGL"
        }
    }

@router.get("/quote/{symbol}", response_model=MarketDataResponse)
async def get_quote(symbol: str):
    """Get current quote for a symbol - uses IBKR if connected, otherwise falls back to other providers"""
    try:
        # Try IBKR first if connected
        try:
            # Import IBKRManager and get the global instance from trading routes
            from ...data.brokers.ibkr_client import IBKRManager
            from ...api.routes.trading import get_ibkr_manager
            ibkr_manager = get_ibkr_manager()
            
            if ibkr_manager and ibkr_manager.is_connected:
                try:
                    client = await ibkr_manager.get_client()
                    contract = client.create_contract(symbol.upper())
                    market_data = await client.get_market_data(contract)
                    
                    # Use last price if available, otherwise use bid/ask midpoint
                    price = market_data.get("last")
                    if price is None:
                        bid = market_data.get("bid")
                        ask = market_data.get("ask")
                        if bid is not None and ask is not None:
                            price = (bid + ask) / 2
                        elif bid is not None:
                            price = bid
                        elif ask is not None:
                            price = ask
                    
                    if price is None:
                        raise ValueError("No price data available from IBKR")
                    
                    # Calculate change (simplified - would need previous close for accurate change)
                    # For now, just return current price with 0 change
                    return MarketDataResponse(
                        symbol=symbol.upper(),
                        price=float(price),
                        change=0.0,  # Would need to track previous close for accurate change
                        change_pct=0.0,
                        volume=market_data.get("volume", 0),
                        timestamp=datetime.now()
                    )
                except Exception as ibkr_error:
                    logger.debug(f"IBKR quote failed for {symbol}, falling back to other providers: {ibkr_error}")
                    # Fall through to use other providers
        except ImportError:
            # IBKR not available, use other providers
            pass
        except Exception as e:
            logger.debug(f"Error checking IBKR connection: {e}")
            # Fall through to use other providers
        
        # Fallback to other data providers
        manager = get_data_manager()
        quote = await manager.get_quote(symbol.upper())
        
        return MarketDataResponse(
            symbol=quote.symbol,
            price=quote.price,
            change=quote.change,
            change_pct=quote.change_pct,
            volume=quote.volume,
            timestamp=quote.timestamp
        )
        
    except Exception as e:
        logger.error(f"Error getting quote for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quotes", response_model=List[MarketDataResponse])
async def get_multiple_quotes(symbols: str = Query(..., description="Comma-separated list of symbols")):
    """Get quotes for multiple symbols"""
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        
        if not symbol_list:
            raise HTTPException(status_code=400, detail="No symbols provided")
        
        if len(symbol_list) > 20:
            raise HTTPException(status_code=400, detail="Too many symbols (max 20)")
        
        manager = get_data_manager()
        quotes = await manager.get_multiple_quotes(symbol_list)
        
        return [
            MarketDataResponse(
                symbol=quote.symbol,
                price=quote.price,
                change=quote.change,
                change_pct=quote.change_pct,
                volume=quote.volume,
                timestamp=quote.timestamp
            )
            for quote in quotes.values()
        ]
        
    except Exception as e:
        logger.error(f"Error getting quotes for {symbols}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/historical/{symbol}")
async def get_historical_data(
    symbol: str,
    days: int = Query(30, ge=1, le=365, description="Number of days of historical data"),
    interval: str = Query("1d", description="Data interval (1d, 1h, 5m)")
):
    """Get historical data for a symbol"""
    try:
        manager = get_data_manager()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        historical_data = await manager.get_historical_data(
            symbol.upper(), start_date, end_date, interval
        )
        
        # Convert to dict format for JSON response
        data = []
        for bar in historical_data:
            data.append({
                "timestamp": bar.timestamp.isoformat(),
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume
            })
        
        return {
            "symbol": symbol.upper(),
            "interval": interval,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "count": len(data),
            "data": data
        }
        
    except Exception as e:
        logger.error(f"Error getting historical data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_symbols(query: str = Query(..., min_length=1, description="Search query")):
    """Search for symbols (placeholder - would need a symbol database)"""
    try:
        # This is a placeholder - in a real implementation, you'd search a database
        # of symbols or use an API that provides symbol search
        
        # For now, return some common symbols that match the query
        common_symbols = [
            "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "BRK-B",
            "UNH", "JNJ", "V", "PG", "JPM", "HD", "MA", "DIS", "PYPL", "ADBE",
            "NFLX", "CRM", "INTC", "CMCSA", "PFE", "TMO", "ABT", "COST", "DHR",
            "ACN", "VZ", "NKE", "TXN", "QCOM", "CVX", "MRK", "WMT", "UNP"
        ]
        
        matching_symbols = [
            symbol for symbol in common_symbols 
            if query.upper() in symbol.upper()
        ]
        
        return {
            "query": query,
            "results": matching_symbols[:10]  # Limit to 10 results
        }
        
    except Exception as e:
        logger.error(f"Error searching symbols for {query}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/providers")
async def get_available_providers():
    """Get list of available data providers"""
    try:
        manager = get_data_manager()
        
        providers = []
        for provider in manager.providers:
            providers.append({
                "name": provider.__class__.__name__,
                "type": provider.__class__.__name__.replace("Provider", "").lower(),
                "rate_limit": getattr(provider, 'rate_limit', 'unknown')
            })
        
        return {
            "providers": providers,
            "count": len(providers)
        }
        
    except Exception as e:
        logger.error(f"Error getting providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        manager = get_data_manager()
        
        # Test with a simple quote
        test_quote = await manager.get_quote("AAPL")
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "providers": len(manager.providers),
            "test_symbol": "AAPL",
            "test_price": test_quote.price
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
