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
from ..api.routes import trading, backtesting, screening, monitoring, market_data
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
    description="Advanced trading bot with SMA strategy, backtesting, and screening",
    version="2.0.0",
    docs_url="/docs" if settings.api.debug else None,
    redoc_url="/redoc" if settings.api.debug else None,
    lifespan=lifespan
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
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(trading.router, prefix="/api/trading", tags=["trading"])
app.include_router(backtesting.router, prefix="/api/backtesting", tags=["backtesting"])
app.include_router(screening.router, prefix="/api/screening", tags=["screening"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])
app.include_router(market_data.router, prefix="/api/market-data", tags=["market-data"])

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
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.environment,
        "timestamp": datetime.now().isoformat()
    }

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