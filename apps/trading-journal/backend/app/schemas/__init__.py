"""
Pydantic schemas for API requests and responses.

All schemas use Pydantic v2 with proper validation rules.
"""

from app.schemas.trade import (
    TradeCreate,
    TradeUpdate,
    TradeResponse,
    TradeListResponse,
    TradeType,
    TradeSide,
    TradeStatus,
)
from app.schemas.dashboard import (
    DashboardStats,
    CumulativePnLPoint,
    DailyPnLPoint,
    DrawdownData,
    RecentTrade,
)
from app.schemas.calendar import (
    CalendarDay,
    CalendarMonth,
    CalendarSummary,
)
from app.schemas.daily import (
    DailyJournal,
    DailySummary,
    PnLProgressionPoint,
    DailyNoteCreate,
    DailyNoteUpdate,
    DailyNoteResponse,
)
from app.schemas.charts import (
    PriceDataPoint,
    PriceDataResponse,
    TradeOverlayData,
)

__all__ = [
    # Trade schemas
    "TradeCreate",
    "TradeUpdate",
    "TradeResponse",
    "TradeListResponse",
    "TradeType",
    "TradeSide",
    "TradeStatus",
    # Dashboard schemas
    "DashboardStats",
    "CumulativePnLPoint",
    "DailyPnLPoint",
    "DrawdownData",
    "RecentTrade",
    # Calendar schemas
    "CalendarDay",
    "CalendarMonth",
    "CalendarSummary",
    # Daily schemas
    "DailyJournal",
    "DailySummary",
    "PnLProgressionPoint",
    "DailyNoteCreate",
    "DailyNoteUpdate",
    "DailyNoteResponse",
    # Charts schemas
    "PriceDataPoint",
    "PriceDataResponse",
    "TradeOverlayData",
]

