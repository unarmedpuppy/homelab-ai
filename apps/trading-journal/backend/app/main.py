"""
Trading Journal FastAPI Application

Main application entry point with middleware, error handlers, and routing.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import text
import logging

from app.config import settings
from app.api.routes import health, trades, dashboard, calendar, daily, charts
from app.database import engine

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Trading Journal API")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Optional: Test database connection
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
    except Exception as e:
        logger.warning(f"Database connection test failed: {e}")
        # Don't fail startup - connection will be tested on first use
    
    yield
    
    # Shutdown
    logger.info("Shutting down Trading Journal API")


# Create FastAPI app
app = FastAPI(
    title="Trading Journal API",
    description="""
    Self-hosted trading journal application API.
    
    Track trades, visualize performance, and analyze trading activity.
    
    ## Features
    
    * **Trade Management**: Create, update, and manage trades
    * **Dashboard**: Performance metrics and KPIs
    * **Calendar View**: Daily P&L and trade summaries
    * **Daily Journal**: Detailed daily trading analysis
    * **Charts**: Price data and trade visualization
    * **Analytics**: Advanced performance analytics
    
    ## Authentication
    
    All endpoints (except `/api/health`) require API key authentication.
    Provide your API key in the `X-API-Key` header.
    """,
    version="0.1.0",
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    openapi_url="/api/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Error handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with user-friendly messages."""
    errors = exc.errors()
    
    # Format errors into user-friendly messages
    formatted_errors = []
    for error in errors:
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        error_type = error["type"]
        error_msg = error.get("msg", "Validation error")
        
        # Create user-friendly error message
        if field_path:
            friendly_msg = f"{field_path}: {error_msg}"
        else:
            friendly_msg = error_msg
        
        # Add context for common validation errors
        if error_type == "value_error":
            # Extract the actual error message from the context
            if "ctx" in error and "error" in error["ctx"]:
                friendly_msg = f"{field_path}: {error['ctx']['error']}"
        
        formatted_errors.append({
            "field": field_path,
            "message": friendly_msg,
            "type": error_type,
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": formatted_errors,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Include routers
from app.api.routes import trades, dashboard, calendar, daily, charts, options, analytics

# Authentication Note:
# - Health endpoint (/api/health) is public (no auth required)
# - All other endpoints must use RequireAuth dependency:
#   
#   Option 1: Per-endpoint dependency
#   from app.api.dependencies import RequireAuth
#   @router.get("/endpoint")
#   async def endpoint(db: DatabaseSession, auth: RequireAuth):
#       ...
#   
#   Option 2: Router-level dependency (recommended for protected routes)
#   from app.api.dependencies import verify_api_key
#   from fastapi import Depends
#   router = APIRouter(dependencies=[Depends(verify_api_key)])
#
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(trades.router, prefix="/api/trades", tags=["trades"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["calendar"])
app.include_router(daily.router, prefix="/api/daily", tags=["daily"])
app.include_router(charts.router, prefix="/api/charts", tags=["charts"])
app.include_router(options.router, prefix="/api/options", tags=["options"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Trading Journal API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/api/docs" if settings.debug else "disabled",
    }

