"""
Price Cache model for storing historical price data.
"""

from sqlalchemy import String, Numeric, DateTime, BigInteger, UniqueConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.database import Base


class PriceCache(Base):
    """
    Price cache model for storing historical OHLCV data.
    
    Caches price data from external APIs to reduce API calls.
    Supports multiple timeframes: 1m, 5m, 15m, 1h, 1d
    """
    __tablename__ = "price_cache"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Cache key fields
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)  # 1m, 5m, 15m, 1h, 1d
    
    # OHLCV data
    open_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    high_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    low_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    close_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    
    # Cache metadata
    cached_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    
    # Unique constraint and indexes (defined in migration, but documented here)
    __table_args__ = (
        UniqueConstraint("ticker", "timestamp", "timeframe", name="uq_price_cache_ticker_timestamp_timeframe"),
        Index("idx_price_cache_ticker_timestamp", "ticker", "timestamp"),
        Index("idx_price_cache_timeframe", "timeframe"),
    )
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<PriceCache(id={self.id}, ticker={self.ticker}, timeframe={self.timeframe}, timestamp={self.timestamp})>"

