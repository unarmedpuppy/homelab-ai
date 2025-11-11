"""
Playbook schemas for API requests and responses.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class PlaybookTemplateBase(BaseModel):
    """Base schema for playbook template."""
    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    category: Optional[str] = Field(None, max_length=50, description="Template category")
    
    model_config = ConfigDict(from_attributes=True)


class PlaybookTemplateCreate(PlaybookTemplateBase):
    """Schema for creating a playbook template."""
    pass


class PlaybookTemplateResponse(PlaybookTemplateBase):
    """Schema for playbook template response."""
    id: int
    is_system: bool
    created_at: datetime
    user_id: int
    
    model_config = ConfigDict(from_attributes=True)


class PlaybookBase(BaseModel):
    """Base schema for playbook."""
    name: str = Field(..., min_length=1, max_length=100, description="Playbook name")
    description: Optional[str] = Field(None, description="Playbook description")
    template_id: Optional[int] = Field(None, description="Reference to template (optional)")
    is_active: bool = Field(True, description="Whether playbook is active")
    is_shared: bool = Field(False, description="Whether playbook is shared")
    
    model_config = ConfigDict(from_attributes=True)


class PlaybookCreate(PlaybookBase):
    """Schema for creating a playbook."""
    pass


class PlaybookUpdate(BaseModel):
    """Schema for updating a playbook."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_shared: Optional[bool] = None
    
    model_config = ConfigDict(from_attributes=True)


class PlaybookPerformance(BaseModel):
    """Performance metrics for a playbook."""
    total_trades: int = Field(0, description="Total number of trades")
    missed_trades: int = Field(0, description="Number of missed trades (future feature)")
    net_pnl: Decimal = Field(Decimal("0"), description="Total net P&L")
    gross_pnl: Decimal = Field(Decimal("0"), description="Total gross P&L")
    win_rate: Optional[Decimal] = Field(None, description="Win rate percentage")
    profit_factor: Optional[Decimal] = Field(None, description="Profit factor")
    avg_win: Optional[Decimal] = Field(None, description="Average winning trade")
    avg_loss: Optional[Decimal] = Field(None, description="Average losing trade")
    winners: int = Field(0, description="Number of winning trades")
    losers: int = Field(0, description="Number of losing trades")
    
    model_config = ConfigDict(from_attributes=True)


class PlaybookResponse(PlaybookBase):
    """Schema for playbook response."""
    id: int
    created_at: datetime
    updated_at: datetime
    user_id: int
    performance: Optional[PlaybookPerformance] = Field(None, description="Performance metrics")
    
    model_config = ConfigDict(from_attributes=True)


class PlaybookListResponse(BaseModel):
    """Schema for playbook list response."""
    playbooks: List[PlaybookResponse] = Field(default_factory=list)
    total: int = Field(0, description="Total number of playbooks")
    
    model_config = ConfigDict(from_attributes=True)

