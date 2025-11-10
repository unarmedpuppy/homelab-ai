"""
Daily Summary model for aggregating daily trading statistics.
"""

from sqlalchemy import String, Numeric, DateTime, Date, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from app.database import Base


class DailySummary(Base):
    """
    Daily summary model for aggregating trading statistics per day.
    
    Stores pre-calculated daily metrics for performance optimization.
    """
    __tablename__ = "daily_summaries"
    
    # Primary key
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    
    # Trade counts
    total_trades: Mapped[int] = mapped_column(nullable=False, server_default="0")
    winners: Mapped[int] = mapped_column(nullable=False, server_default="0")
    losers: Mapped[int] = mapped_column(nullable=False, server_default="0")
    
    # Financial metrics
    gross_pnl: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")
    commissions: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, server_default="0")
    volume: Mapped[int] = mapped_column(nullable=False, server_default="0")
    
    # Calculated metrics
    profit_factor: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), nullable=True)
    winrate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    
    # Timestamp
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<DailySummary(date={self.date}, total_trades={self.total_trades}, gross_pnl={self.gross_pnl})>"

