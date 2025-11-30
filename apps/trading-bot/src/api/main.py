"""
FastAPI Application with Modern Architecture
===========================================

Clean, scalable API with proper error handling, validation, and documentation.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import logging
from datetime import datetime
from pathlib import Path

from ..config.settings import settings
from ..api.routes import trading, backtesting, screening, monitoring, market_data, strategies, sentiment, confluence, options_flow, trends, events, websocket, scheduler, sync
# Import from middleware package (which now exports from middleware.py)
from ..api.middleware import LoggingMiddleware, RateLimitMiddleware
from ..api.middleware.metrics_middleware import MetricsMiddleware
from ..utils.metrics import update_system_metrics, get_app_start_time, initialize_system_metrics

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _publish_trade_from_ibkr(trade, trade_publisher):
    """Helper function to publish trade from IBKR Trade object"""
    try:
        from ib_insync.objects import Trade as IBKRTrade
        
        symbol = trade.contract.symbol if trade.contract else "unknown"
        side = trade.order.action  # "BUY" or "SELL"
        quantity = trade.orderStatus.filled
        price = trade.orderStatus.avgFillPrice
        
        if quantity > 0 and price > 0:
            await trade_publisher.publish_trade(
                symbol=symbol,
                side=side,
                quantity=int(quantity),
                price=float(price),
                timestamp=datetime.now()
            )
    except Exception as e:
        logger.error(f"Error publishing trade from IBKR: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Trading Bot API")
    
    # Startup tasks
    try:
        # Initialize system metrics if enabled
        if settings.metrics.enabled:
            # Initialize system metrics (includes app start time)
            initialize_system_metrics()
            # Update metrics immediately
            update_system_metrics()
            logger.info("System metrics initialized")
            
            # Schedule periodic system metrics updates (every 30 seconds)
            import asyncio
            async def periodic_system_metrics():
                while True:
                    await asyncio.sleep(30)
                    try:
                        update_system_metrics()
                    except Exception as e:
                        logger.warning(f"Error updating system metrics: {e}")
            
            # Start background task
            asyncio.create_task(periodic_system_metrics())
        
        # Initialize strategies before WebSocket streams
        from ..api.routes.strategies import get_evaluator
        from ..core.strategy.startup import initialize_strategies

        evaluator = get_evaluator()
        strategy_init_result = initialize_strategies(evaluator)
        logger.info(
            f"Strategies initialized: {strategy_init_result['registered_count']} registered, "
            f"{strategy_init_result['total_active']} active"
        )

        # Start WebSocket streams if enabled
        if settings.websocket.enabled:
            from ..api.websocket.streams import get_stream_manager
            from ..api.routes.trading import get_ibkr_manager
            from ..api.routes.trade_publisher import get_trade_publisher

            stream_manager = get_stream_manager()
            stream_manager.initialize(evaluator)
            
            # Integrate TradePublisher with IBKR client for trade execution notifications
            try:
                ibkr_manager = get_ibkr_manager()
                trade_publisher = get_trade_publisher()
                
                if ibkr_manager and ibkr_manager.client:
                    # Register trade publisher callback
                    def on_trade_filled(trade):
                        """Handle trade fill and publish to WebSocket"""
                        # IBKR callback is synchronous, schedule async publish
                        import asyncio
                        try:
                            loop = asyncio.get_running_loop()
                            asyncio.create_task(
                                _publish_trade_from_ibkr(trade, trade_publisher)
                            )
                        except RuntimeError:
                            # No running loop - try to get/create one
                            try:
                                loop = asyncio.get_event_loop()
                                if loop.is_running():
                                    asyncio.create_task(
                                        _publish_trade_from_ibkr(trade, trade_publisher)
                                    )
                                else:
                                    asyncio.run_coroutine_threadsafe(
                                        _publish_trade_from_ibkr(trade, trade_publisher),
                                        loop
                                    )
                            except Exception as e:
                                logger.warning(f"Could not publish trade to WebSocket: {e}")
                    
                    ibkr_manager.client.add_order_filled_callback(on_trade_filled)
                    logger.info("TradePublisher integrated with IBKR client")
            except Exception as e:
                logger.warning(f"Could not integrate TradePublisher with IBKR: {e}")
            
            await stream_manager.start_all()
            logger.info("WebSocket streams started")
        
        # Start trading scheduler if enabled
        if settings.scheduler.enabled:
            try:
                from ..core.scheduler import get_scheduler
                scheduler = get_scheduler()

                # Start scheduler if enabled in config
                if settings.scheduler.enabled:
                    await scheduler.start()
                    logger.info("Trading scheduler started")
            except Exception as e:
                logger.warning(f"Could not start trading scheduler: {e}", exc_info=True)

        # Start Unusual Whales scraper if enabled
        try:
            from ..data.providers.unusual_whales_scraper import get_settings as get_uw_settings, start_provider as start_uw_provider
            uw_settings = get_uw_settings()
            if uw_settings.enabled:
                await start_uw_provider()
                logger.info(f"Unusual Whales scraper started (symbols: {uw_settings.ticker_flow_symbols})")
        except Exception as e:
            logger.warning(f"Could not start Unusual Whales scraper: {e}", exc_info=True)

        logger.info("Trading Bot API started successfully")
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    finally:
        # Shutdown tasks
        # Stop Unusual Whales scraper
        try:
            from ..data.providers.unusual_whales_scraper import stop_provider as stop_uw_provider
            await stop_uw_provider()
            logger.info("Unusual Whales scraper stopped")
        except Exception as e:
            logger.warning(f"Error stopping Unusual Whales scraper: {e}")

        # Stop trading scheduler
        try:
            from ..core.scheduler import get_scheduler
            scheduler = get_scheduler()
            if scheduler.state.value != "stopped":
                await scheduler.stop()
                logger.info("Trading scheduler stopped")
        except Exception as e:
            logger.warning(f"Error stopping trading scheduler: {e}")
        
        # Stop WebSocket streams
        if settings.websocket.enabled:
            try:
                from ..api.websocket.streams import get_stream_manager
                stream_manager = get_stream_manager()
                await stream_manager.stop_all()
                logger.info("WebSocket streams stopped")
            except Exception as e:
                logger.warning(f"Error stopping WebSocket streams: {e}")
        
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
            "description": """
            Trading operations and IBKR integration:
            * **Order Execution**: Place market, limit, and stop orders
            * **Position Management**: View and manage open positions
            * **Account Info**: Account balances, margin, buying power
            * **Trade History**: Complete trade execution history
            """
        },
        {
            "name": "strategies",
            "description": """
            Strategy management and evaluation:
            * **Strategy CRUD**: Create, read, update, delete strategies
            * **Signal Generation**: Evaluate strategies and generate trading signals
            * **Strategy Performance**: Track strategy performance metrics
            """
        },
        {
            "name": "backtesting",
            "description": """
            Backtesting engine for strategy validation:
            * **Historical Testing**: Test strategies on historical data
            * **Performance Metrics**: Sharpe ratio, drawdown, win rate
            * **Parameter Optimization**: Find optimal strategy parameters
            """
        },
        {
            "name": "screening",
            "description": """
            Stock screening and filtering:
            * **Custom Screens**: Define and run custom stock screens
            * **Pre-built Filters**: Common screening criteria
            * **Results Export**: Export screening results
            """
        },
        {
            "name": "monitoring",
            "description": """
            System health and monitoring:
            * **Health Checks**: API, database, and provider health
            * **System Metrics**: CPU, memory, disk usage
            * **Connection Status**: IBKR, data provider connections
            """
        },
        {
            "name": "market-data",
            "description": """
            Market data endpoints:
            * **Real-time Quotes**: Current prices and market data
            * **Historical Data**: OHLCV data for any timeframe
            * **Market Info**: Company information, symbols search
            """
        },
        {
            "name": "sentiment",
            "description": """
            Sentiment analysis endpoints:
            * **Multi-source Sentiment**: Twitter, Reddit, News, StockTwits
            * **Aggregated Sentiment**: Unified sentiment scores
            * **Sentiment History**: Historical sentiment trends
            * **Provider Status**: Individual provider health
            """
        },
        {
            "name": "options-flow",
            "description": """
            Options flow analysis:
            * **Flow Data**: Real-time unusual options activity
            * **Pattern Detection**: Sweeps, blocks, spreads
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
        {
            "name": "websocket",
            "description": """
            Real-time data streaming via WebSocket:
            * **Live Price Updates**: Real-time price streaming for subscribed symbols
            * **Trading Signals**: Broadcast trading signals as they're generated
            * **Trade Executions**: Real-time trade execution notifications
            * **Portfolio Updates**: Live portfolio position and P&L updates
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
app.add_middleware(MetricsMiddleware)  # Metrics collection (if enabled)

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
app.include_router(websocket.router, tags=["websocket"])
app.include_router(scheduler.router, prefix="/api", tags=["scheduler"])
app.include_router(sync.router, prefix="/api/sync", tags=["sync"])

# Templates and Static Files
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "ui" / "templates"))

# Mount static files directory (for JavaScript, CSS, etc.)
static_dir = BASE_DIR / "ui" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - serve dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": {}})

@app.get("/scheduler", response_class=HTMLResponse)
async def scheduler_dashboard():
    """Scheduler dashboard endpoint"""
    return templates.TemplateResponse("scheduler_dashboard.html", {"request": {}})


@app.get("/terminal", response_class=HTMLResponse)
async def terminal_dashboard():
    """Terminal-style dashboard with real-time visualizations"""
    return templates.TemplateResponse("terminal.html", {"request": {}})


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with metrics tracking"""
    from fastapi.responses import JSONResponse

    # Record error metrics
    if settings.metrics.enabled:
        try:
            from ..utils.metrics import record_error
            is_critical = exc.status_code >= 500
            record_error("http_error", component="api", is_critical=is_critical)
        except (ImportError, Exception) as e:
            logger.debug(f"Could not record HTTP exception metric: {e}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions with metrics tracking"""
    from fastapi.responses import JSONResponse

    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Record exception metrics
    if settings.metrics.enabled:
        try:
            from ..utils.metrics import record_exception
            exc_type = type(exc).__name__
            record_exception(exc_type, component="api", is_critical=True)
        except (ImportError, Exception) as e:
            logger.debug(f"Could not record exception metric: {e}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.debug,
        log_level=settings.logging.level.lower()
    )
