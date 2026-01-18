"""Beads API Router - Task management endpoints for dashboard integration.

Provides REST API endpoints for beads task operations:
- List/filter tasks
- Get task details
- Create/update tasks
- Get statistics and labels

All endpoints use the beads_cli module to interact with the beads database
via the `bd` CLI tool.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from beads_cli import (
    list_tasks as beads_list_tasks,
    get_ready_tasks as beads_get_ready_tasks,
    get_task as beads_get_task,
    claim_task as beads_claim_task,
    close_task as beads_close_task,
    create_task as beads_create_task,
    update_task as beads_update_task,
    get_labels as beads_get_labels,
    get_stats as beads_get_stats,
    sync_beads,
    compute_age_days,
    BeadsError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/beads", tags=["beads"])


# =============================================================================
# Pydantic Models
# =============================================================================


class BeadsTaskCreate(BaseModel):
    """Request body for creating a new beads task."""

    title: str
    priority: int = 2  # 0=critical, 1=high, 2=medium, 3=low
    type: str = "task"  # task, bug, feature, epic, chore
    labels: list[str] = []  # Should include at least one repo:* label
    description: Optional[str] = None
    blocked_by: list[str] = []


class BeadsTaskUpdate(BaseModel):
    """Request body for updating a beads task."""

    status: Optional[str] = None  # open, in_progress, closed
    priority: Optional[int] = None
    labels_add: list[str] = []
    labels_remove: list[str] = []


class BeadsTaskResponse(BaseModel):
    """Response model for a single task."""

    id: str
    title: str
    status: str
    priority: int
    issue_type: str
    labels: list[str]
    blocked_by: list[str] = []
    created_at: str
    updated_at: Optional[str] = None
    description: Optional[str] = None
    age_days: int = 0


class BeadsListResponse(BaseModel):
    """Response model for task list endpoint."""

    tasks: list[dict]
    total: int


class BeadsStatsResponse(BaseModel):
    """Response model for stats endpoint."""

    total: int
    total_tasks: int
    backlog_count: int
    in_progress_count: int
    done_count: int
    blocked_count: int
    by_label: dict[str, int]
    by_priority: dict[int, int]
    by_type: dict[str, int]


class BeadsLabelsResponse(BaseModel):
    """Response model for labels endpoint."""

    labels: list[str]
    repo_labels: list[str]
    other_labels: list[str]


# =============================================================================
# API Endpoints
# =============================================================================


@router.get("/list", response_model=BeadsListResponse)
async def api_beads_list(
    status: Optional[str] = None,
    label: Optional[str] = None,
    priority: Optional[int] = None,
    type: Optional[str] = None,
    ready: bool = False,
    limit: Optional[int] = None,
):
    """
    List beads tasks with optional filters.

    Query Parameters:
        status: Filter by status (open, in_progress, closed)
        label: Filter by label
        priority: Filter by priority (0-3)
        type: Filter by type (task, bug, feature, epic, chore)
        ready: If true, only return unblocked open tasks
        limit: Maximum number of tasks to return

    Returns:
        List of tasks with computed age_days field
    """
    try:
        if ready:
            tasks = await beads_get_ready_tasks(label=label)
        else:
            tasks = await beads_list_tasks(
                status=status,
                label=label,
                priority=priority,
                task_type=type,
                limit=limit,
            )

        # Add computed age_days to each task
        for task in tasks:
            created_at = task.get("created_at", "")
            if created_at:
                task["age_days"] = compute_age_days(created_at)
            else:
                task["age_days"] = 0

        return BeadsListResponse(
            tasks=tasks,
            total=len(tasks),
        )

    except BeadsError as e:
        logger.error(f"Beads list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=BeadsListResponse)
async def api_beads_tasks(
    status: Optional[str] = None,
    label: Optional[str] = None,
    priority: Optional[int] = None,
    type: Optional[str] = None,
    ready: bool = False,
    limit: Optional[int] = None,
):
    """
    List beads tasks with optional filters (alias for /list).

    Query Parameters:
        status: Filter by status (open, in_progress, closed)
        label: Filter by label
        priority: Filter by priority (0-3)
        type: Filter by type (task, bug, feature, epic, chore)
        ready: If true, only return unblocked open tasks
        limit: Maximum number of tasks to return

    Returns:
        List of tasks with computed age_days field
    """
    return await api_beads_list(
        status=status,
        label=label,
        priority=priority,
        type=type,
        ready=ready,
        limit=limit,
    )


@router.get("/tasks/{task_id}")
async def api_beads_get_task(task_id: str):
    """
    Get a specific beads task by ID.

    Path Parameters:
        task_id: The task ID

    Returns:
        Task details including age_days
    """
    try:
        task = await beads_get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # Add computed age_days
        created_at = task.get("created_at", "")
        if created_at:
            task["age_days"] = compute_age_days(created_at)
        else:
            task["age_days"] = 0

        return task

    except BeadsError as e:
        logger.error(f"Beads get error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks")
async def api_beads_create_task(task: BeadsTaskCreate):
    """
    Create a new beads task.

    Request Body:
        title: Task title (required)
        priority: Priority 0-3 (default: 2)
        type: Task type (default: task)
        labels: List of labels (should include repo:* label)
        description: Optional markdown description
        blocked_by: Optional list of blocking task IDs

    Returns:
        Created task
    """
    try:
        # Validate that at least one repo label is present
        repo_labels = [lbl for lbl in task.labels if lbl.startswith("repo:")]
        if not repo_labels:
            logger.warning(f"Creating task without repo label: {task.title}")

        created = await beads_create_task(
            title=task.title,
            priority=task.priority,
            task_type=task.type,
            labels=task.labels,
            description=task.description,
            blocked_by=task.blocked_by if task.blocked_by else None,
        )

        # Sync after creation
        await sync_beads()

        return created

    except BeadsError as e:
        logger.error(f"Beads create error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/tasks/{task_id}")
async def api_beads_update_task(task_id: str, update: BeadsTaskUpdate):
    """
    Update an existing beads task.

    Path Parameters:
        task_id: The task ID

    Request Body:
        status: New status (open, in_progress, closed)
        priority: New priority (0-3)
        labels_add: Labels to add
        labels_remove: Labels to remove

    Returns:
        Updated task
    """
    try:
        updated = await beads_update_task(
            task_id=task_id,
            status=update.status,
            priority=update.priority,
            labels_add=update.labels_add if update.labels_add else None,
            labels_remove=update.labels_remove if update.labels_remove else None,
        )

        # Sync after update
        await sync_beads()

        return updated

    except BeadsError as e:
        logger.error(f"Beads update error: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=BeadsStatsResponse)
async def api_beads_stats():
    """
    Get aggregated beads task statistics.

    Returns:
        Statistics including total, by status, by label, by priority, by type
    """
    try:
        stats = await beads_get_stats()
        # Add 'total' as an alias for total_tasks for dashboard compatibility
        stats["total"] = stats.get("total_tasks", 0)
        return stats

    except BeadsError as e:
        logger.error(f"Beads stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/labels", response_model=BeadsLabelsResponse)
async def api_beads_labels():
    """
    Get all unique labels used in beads tasks.

    Returns:
        List of labels with repo labels grouped first
    """
    try:
        labels = await beads_get_labels()

        # Separate repo labels from other labels
        repo_labels = sorted([lbl for lbl in labels if lbl.startswith("repo:")])
        other_labels = sorted([lbl for lbl in labels if not lbl.startswith("repo:")])

        return BeadsLabelsResponse(
            labels=labels,
            repo_labels=repo_labels,
            other_labels=other_labels,
        )

    except BeadsError as e:
        logger.error(f"Beads labels error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def api_beads_sync():
    """
    Sync beads database (pull and push changes).

    Useful when multiple processes are modifying tasks.

    Returns:
        Sync status message
    """
    try:
        result = await sync_beads()
        return {"status": "ok", "message": result}

    except BeadsError as e:
        logger.error(f"Beads sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/claim")
async def api_beads_claim_task(task_id: str):
    """
    Claim a task (set status to in_progress).

    Path Parameters:
        task_id: The task ID

    Returns:
        Success message
    """
    try:
        result = await beads_claim_task(task_id)
        await sync_beads()
        return {"status": "ok", "message": result, "task_id": task_id}

    except BeadsError as e:
        logger.error(f"Beads claim error: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/close")
async def api_beads_close_task(task_id: str):
    """
    Close a task (set status to closed).

    Path Parameters:
        task_id: The task ID

    Returns:
        Success message
    """
    try:
        result = await beads_close_task(task_id)
        await sync_beads()
        return {"status": "ok", "message": result, "task_id": task_id}

    except BeadsError as e:
        logger.error(f"Beads close error: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        raise HTTPException(status_code=500, detail=str(e))
