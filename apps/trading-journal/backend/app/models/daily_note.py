"""
Daily Note model for storing daily journal notes.
"""

from sqlalchemy import String, Text, DateTime, Date, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date, datetime
from typing import Optional

from app.database import Base


class DailyNote(Base):
    """
    Daily note model for storing journal notes per day.
    
    Each day can have one note entry.
    """
    __tablename__ = "daily_notes"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Date (unique)
    date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    
    # Notes content
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    # Index (defined in migration, but documented here)
    __table_args__ = (
        Index("idx_daily_notes_date", "date"),
    )
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<DailyNote(id={self.id}, date={self.date}, has_notes={bool(self.notes)})>"

