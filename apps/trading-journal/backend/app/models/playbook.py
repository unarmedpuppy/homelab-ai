"""
Playbook models for trading strategies.
"""

from sqlalchemy import String, Text, Boolean, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List

from app.database import Base


class PlaybookTemplate(Base):
    """
    Playbook template model for pre-built trading strategy templates.
    
    Templates can be system-provided or user-created.
    """
    __tablename__ = "playbook_templates"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # breakout, pullback, reversal, etc.
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    
    # Relationships
    playbooks: Mapped[List["Playbook"]] = relationship("Playbook", back_populates="template")


class Playbook(Base):
    """
    Playbook model representing a trading strategy/playbook.
    
    Playbooks can be created from templates or from scratch.
    Trades can be assigned to playbooks to track strategy performance.
    """
    __tablename__ = "playbooks"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    template_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("playbook_templates.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    is_shared: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    
    # Relationships
    template: Mapped[Optional["PlaybookTemplate"]] = relationship("PlaybookTemplate", back_populates="playbooks")
    trades: Mapped[List["Trade"]] = relationship("Trade", back_populates="playbook_rel")

