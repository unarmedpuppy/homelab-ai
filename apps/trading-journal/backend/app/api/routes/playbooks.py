"""
Playbooks API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import date, datetime

from app.api.dependencies import verify_api_key, DatabaseSession
from app.schemas.playbook import (
    PlaybookCreate,
    PlaybookUpdate,
    PlaybookResponse,
    PlaybookListResponse,
    PlaybookPerformance,
    PlaybookTemplateCreate,
    PlaybookTemplateResponse,
)
from app.schemas.trade import TradeResponse as TradeResponseSchema
from app.services.playbook_service import (
    get_playbooks,
    get_playbook,
    create_playbook,
    update_playbook,
    delete_playbook,
    get_playbook_trades,
    get_playbook_performance,
    get_playbook_templates,
    create_playbook_template,
)

router = APIRouter(dependencies=[Depends(verify_api_key)])


def parse_date_param(date_str: Optional[str], param_name: str) -> Optional[date]:
    """Parse date string parameter with error handling."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {param_name} format. Use YYYY-MM-DD"
        )


@router.get("", response_model=PlaybookListResponse)
async def list_playbooks(
    db: DatabaseSession,
    search: Optional[str] = Query(None, description="Search playbooks by name or description"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_shared: Optional[bool] = Query(None, description="Filter by shared status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
):
    """
    Get list of playbooks with optional filters.
    """
    playbooks, total = await get_playbooks(
        db=db,
        search=search,
        is_active=is_active,
        is_shared=is_shared,
        skip=skip,
        limit=limit,
    )
    
    # Calculate performance for each playbook
    playbook_responses = []
    for playbook in playbooks:
        performance = await get_playbook_performance(db, playbook.id)
        playbook_dict = {
            "id": playbook.id,
            "name": playbook.name,
            "description": playbook.description,
            "template_id": playbook.template_id,
            "is_active": playbook.is_active,
            "is_shared": playbook.is_shared,
            "created_at": playbook.created_at,
            "updated_at": playbook.updated_at,
            "user_id": playbook.user_id,
            "performance": performance,
        }
        playbook_responses.append(PlaybookResponse(**playbook_dict))
    
    return PlaybookListResponse(playbooks=playbook_responses, total=total)


@router.get("/{playbook_id}", response_model=PlaybookResponse)
async def get_playbook_by_id(
    playbook_id: int = Path(..., description="Playbook ID"),
    db: DatabaseSession = None,
):
    """
    Get a single playbook by ID with performance metrics.
    """
    playbook = await get_playbook(db, playbook_id)
    if not playbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playbook with ID {playbook_id} not found"
        )
    
    performance = await get_playbook_performance(db, playbook_id)
    
    playbook_dict = {
        "id": playbook.id,
        "name": playbook.name,
        "description": playbook.description,
        "template_id": playbook.template_id,
        "is_active": playbook.is_active,
        "is_shared": playbook.is_shared,
        "created_at": playbook.created_at,
        "updated_at": playbook.updated_at,
        "user_id": playbook.user_id,
        "performance": performance,
    }
    
    return PlaybookResponse(**playbook_dict)


@router.post("", response_model=PlaybookResponse, status_code=status.HTTP_201_CREATED)
async def create_playbook_endpoint(
    playbook_data: PlaybookCreate,
    db: DatabaseSession,
):
    """
    Create a new playbook.
    """
    try:
        playbook = await create_playbook(db, playbook_data)
        performance = await get_playbook_performance(db, playbook.id)
        
        playbook_dict = {
            "id": playbook.id,
            "name": playbook.name,
            "description": playbook.description,
            "template_id": playbook.template_id,
            "is_active": playbook.is_active,
            "is_shared": playbook.is_shared,
            "created_at": playbook.created_at,
            "updated_at": playbook.updated_at,
            "user_id": playbook.user_id,
            "performance": performance,
        }
        
        return PlaybookResponse(**playbook_dict)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating playbook: {str(e)}"
        )


@router.put("/{playbook_id}", response_model=PlaybookResponse)
async def update_playbook_endpoint(
    playbook_id: int = Path(..., description="Playbook ID"),
    playbook_data: PlaybookUpdate = ...,
    db: DatabaseSession = None,
):
    """
    Update a playbook.
    """
    playbook = await update_playbook(db, playbook_id, playbook_data)
    if not playbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playbook with ID {playbook_id} not found"
        )
    
    performance = await get_playbook_performance(db, playbook_id)
    
    playbook_dict = {
        "id": playbook.id,
        "name": playbook.name,
        "description": playbook.description,
        "template_id": playbook.template_id,
        "is_active": playbook.is_active,
        "is_shared": playbook.is_shared,
        "created_at": playbook.created_at,
        "updated_at": playbook.updated_at,
        "user_id": playbook.user_id,
        "performance": performance,
    }
    
    return PlaybookResponse(**playbook_dict)


@router.delete("/{playbook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_playbook_endpoint(
    playbook_id: int = Path(..., description="Playbook ID"),
    db: DatabaseSession = None,
):
    """
    Delete a playbook.
    
    All trades using this playbook will have their playbook_id set to NULL.
    """
    deleted = await delete_playbook(db, playbook_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Playbook with ID {playbook_id} not found"
        )


@router.get("/{playbook_id}/trades", response_model=List[TradeResponseSchema])
async def get_playbook_trades_endpoint(
    playbook_id: int = Path(..., description="Playbook ID"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: DatabaseSession = None,
):
    """
    Get all trades for a playbook.
    """
    date_from_parsed = parse_date_param(date_from, "date_from")
    date_to_parsed = parse_date_param(date_to, "date_to")
    
    trades = await get_playbook_trades(db, playbook_id, date_from_parsed, date_to_parsed)
    
    return [TradeResponseSchema.model_validate(trade, from_attributes=True) for trade in trades]


@router.get("/{playbook_id}/performance", response_model=PlaybookPerformance)
async def get_playbook_performance_endpoint(
    playbook_id: int = Path(..., description="Playbook ID"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: DatabaseSession = None,
):
    """
    Get performance metrics for a playbook.
    """
    date_from_parsed = parse_date_param(date_from, "date_from")
    date_to_parsed = parse_date_param(date_to, "date_to")
    
    performance = await get_playbook_performance(db, playbook_id, date_from_parsed, date_to_parsed)
    
    return performance


@router.get("/templates", response_model=List[PlaybookTemplateResponse])
async def list_playbook_templates(
    db: DatabaseSession,
):
    """
    Get all playbook templates.
    """
    templates = await get_playbook_templates(db)
    return [PlaybookTemplateResponse.model_validate(template, from_attributes=True) for template in templates]


@router.post("/templates", response_model=PlaybookTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_playbook_template_endpoint(
    template_data: PlaybookTemplateCreate,
    db: DatabaseSession,
):
    """
    Create a new playbook template.
    """
    try:
        template = await create_playbook_template(db, template_data)
        return PlaybookTemplateResponse.model_validate(template, from_attributes=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating template: {str(e)}"
        )

