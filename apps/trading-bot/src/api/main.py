"""
FastAPI Application with Modern Architecture
===========================================

Clean, scalable API with proper error handling, validation, and documentation.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import logging
from datetime import datetime
from pathlib import Path

from ..config.settings import settings
from ..api.routes import trading, backtesting, screening, monitoring, market_data, strategies, sentiment, confluence, options_flow, trends, events
from ..api.middleware import LoggingMiddleware, RateLimitMiddleware

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Trading Bot API")
    
    # Startup tasks
    try:
        logger.info("Trading Bot API started successfully")
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    finally:
        # Shutdown tasks
        logger.info("Shutting down Trading Bot API")

# Create FastAPI app
app = FastAPI(
    title="Trading Bot API",
    description="""
    Advanced Trading Bot API with comprehensive sentiment analysis, options flow, and confluence scoring.
    
    ## Features
    
    * **Trading Operations**: Execute trades, manage positions, and monitor portfolios
    * **Strategy Management**: Create, evaluate, and backtest trading strategies
    * **Market Data**: Real-time quotes, historical data, and market information
    * **Sentiment Analysis**: Multi-source sentiment from Twitter, Reddit, News, and Options Flow
    * **Options Flow**: Pattern detection, metrics, chain analysis, and flow-based sentiment
    * **Confluence Scoring**: Unified scoring combining technical indicators, sentiment, and options flow
    * **Screening**: Find stocks matching specific criteria
    * **Monitoring**: Health checks and system monitoring
    
    ## Authentication
    
    API keys may be required for certain endpoints. Check individual endpoint documentation.
    
    ## Rate Limiting
    
    Rate limiting is applied per endpoint. Check response headers for rate limit information.
    """,
    version="2.0.0",
    docs_url="/docs" if settings.api.debug else None,
    redoc_url="/redoc" if settings.api.debug else None,
    lifespan=lifespan,
    tags_metadata=[
        {
            "name": "trading",
            "description": "Trading operations including order execution, position management, and portfolio monitoring."
        },
        {
            "name": "strategies",
            "description": "Strategy management, evaluation, and configuration. Includes confluence-based filtering."
        },
        {
            "name": "backtesting",
            "description": "Backtest trading strategies against historical data with detailed performance metrics."
        },
        {
            "name": "screening",
            "description": "Stock screening and filtering based on technical indicators, sentiment, and other criteria."
        },
        {
            "name": "monitoring",
            "description": "System health checks, metrics, and monitoring endpoints."
        },
        {
            "name": "market-data",
            "description": "Real-time and historical market data including quotes, charts, and symbol search."
        },
        {
            "name": "sentiment",
            "description": """
            Sentiment analysis from multiple sources:
            * **Twitter/X**: Real-time social media sentiment
            * **Reddit**: Community discussion sentiment
            * **News**: Financial news article sentiment
            * **Aggregated**: Unified sentiment across all sources
            """
        },
        {
            "name": "options-flow",
            "description": """
            Options flow analysis including:
            * **Pattern Detection**: Sweeps and block trades
            * **Metrics**: Put/call ratios, flow metrics
            * **Chain Analysis**: Max pain, gamma exposure, strike concentration
            * **Sentiment**: Options flow-based sentiment scoring
            """
        },
        {
            "name": "confluence",
            "description": """
            Confluence scoring combining:
            * **Technical Indicators**: RSI, SMA, Volume, Bollinger Bands
            * **Sentiment**: Aggregated multi-source sentiment
            * **Options Flow**: Flow-based sentiment and metrics
            * **Unified Score**: Weighted confluence with directional bias
            """
        },
    ]
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)  # No params - uses settings

# Include routers
app.include_router(trading.router, prefix="/api/trading", tags=["trading"])
app.include_router(strategies.router, prefix="/api", tags=["strategies"])
app.include_router(backtesting.router, prefix="/api/backtesting", tags=["backtesting"])
app.include_router(screening.router, prefix="/api/screening", tags=["screening"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])
app.include_router(market_data.router, prefix="/api/market-data", tags=["market-data"])
app.include_router(sentiment.router, prefix="/api/sentiment", tags=["sentiment"])
app.include_router(options_flow.router, prefix="/api/options-flow", tags=["options-flow"])
app.include_router(confluence.router, prefix="/api/confluence", tags=["confluence"])
app.include_router(trends.router, prefix="/api/data/trends", tags=["trends"])
app.include_router(events.router, prefix="/api/data/events", tags=["events"])

# Templates
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "ui" / "templates"))

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": {}})

@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """Serve the market data test page"""
    return templates.TemplateResponse("market_data_test.html", {"request": {}})

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    from .routes.monitoring import health_check as monitoring_health
    return await monitoring_health()

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return {
        "error": {
            "code": exc.status_code,
            "message": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return {
        "error": {
            "code": 500,
            "message": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.debug,
        log_level=settings.logging.level.lower()
    )