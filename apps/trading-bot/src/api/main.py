"""
FastAPI Application with Modern Architecture
===========================================

Clean, scalable API with proper error handling, validation, and documentation.
"""

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import asyncio
import json
from typing import List, Dict, Any, Optional
import logging

from ..config.settings import settings
from ..utils.logging import setup_logging, get_logger
from ..api.routes import trading, backtesting, screening, monitoring, market_data
from ..api.middleware import LoggingMiddleware, RateLimitMiddleware
from ..data.database import get_db_session

# Setup logging
setup_logging(settings.logging.level)
logger = get_logger(__name__)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Trading Bot API")
    
    # Startup tasks
    try:
        # Initialize database
        from ..data.database import init_db
        await init_db()
        
        # Start background tasks
        asyncio.create_task(price_update_task())
        
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

if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
    )

app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(trading.router, prefix="/api/trading", tags=["trading"])
app.include_router(backtesting.router, prefix="/api/backtesting", tags=["backtesting"])
app.include_router(screening.router, prefix="/api/screening", tags=["screening"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])
app.include_router(market_data.router, prefix="/api/market-data", tags=["market-data"])

# Mount static files
app.mount("/static", StaticFiles(directory="src/ui/static"), name="static")

# Templates
templates = Jinja2Templates(directory="src/ui/templates")

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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await manager.send_personal_message(
                    json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}),
                    websocket
                )
            elif message.get("type") == "subscribe":
                # Handle subscription to specific data feeds
                symbol = message.get("symbol")
                await manager.send_personal_message(
                    json.dumps({"type": "subscribed", "symbol": symbol}),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

async def price_update_task():
    """Background task for price updates"""
    while True:
        try:
            # Simulate price updates (replace with real data feed)
            price_data = {
                "type": "price_update",
                "timestamp": datetime.now().isoformat(),
                "symbols": {
                    "AAPL": {"price": 150.25, "change": 0.15, "change_pct": 0.10},
                    "MSFT": {"price": 300.50, "change": -0.25, "change_pct": -0.08},
                    "NVDA": {"price": 450.75, "change": 2.50, "change_pct": 0.56}
                }
            }
            
            await manager.broadcast(json.dumps(price_data))
            await asyncio.sleep(5)  # Update every 5 seconds
            
        except Exception as e:
            logger.error(f"Error in price update task: {e}")
            await asyncio.sleep(10)

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
