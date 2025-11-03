"""
Scheduler Management Routes
===========================

API endpoints for managing the automatic trading scheduler.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from ...core.scheduler import TradingScheduler, get_scheduler
from ...config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status and statistics"""
    try:
        scheduler = get_scheduler()
        status = scheduler.get_status()
        return {
            "status": "success",
            **status
        }
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting scheduler status: {str(e)}"
        )


@router.post("/scheduler/start")
async def start_scheduler():
    """Start the trading scheduler"""
    try:
        scheduler = get_scheduler()
        
        if scheduler.state.value == "running":
            return {
                "status": "success",
                "message": "Scheduler is already running",
                "state": scheduler.state.value
            }
        
        await scheduler.start()
        
        return {
            "status": "success",
            "message": "Scheduler started successfully",
            "state": scheduler.state.value
        }
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error starting scheduler: {str(e)}"
        )


@router.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the trading scheduler"""
    try:
        scheduler = get_scheduler()
        
        if scheduler.state.value == "stopped":
            return {
                "status": "success",
                "message": "Scheduler is already stopped",
                "state": scheduler.state.value
            }
        
        await scheduler.stop()
        
        return {
            "status": "success",
            "message": "Scheduler stopped successfully",
            "state": scheduler.state.value
        }
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error stopping scheduler: {str(e)}"
        )


@router.post("/scheduler/pause")
async def pause_scheduler():
    """Pause the trading scheduler (maintains state)"""
    try:
        scheduler = get_scheduler()
        
        if scheduler.state.value != "running":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot pause scheduler in state: {scheduler.state.value}"
            )
        
        await scheduler.pause()
        
        return {
            "status": "success",
            "message": "Scheduler paused successfully",
            "state": scheduler.state.value
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing scheduler: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error pausing scheduler: {str(e)}"
        )


@router.post("/scheduler/resume")
async def resume_scheduler():
    """Resume the trading scheduler"""
    try:
        scheduler = get_scheduler()
        
        if scheduler.state.value != "paused":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot resume scheduler in state: {scheduler.state.value}"
            )
        
        await scheduler.resume()
        
        return {
            "status": "success",
            "message": "Scheduler resumed successfully",
            "state": scheduler.state.value
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming scheduler: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error resuming scheduler: {str(e)}"
        )


@router.get("/scheduler/stats")
async def get_scheduler_stats():
    """Get detailed scheduler statistics"""
    try:
        scheduler = get_scheduler()
        status = scheduler.get_status()
        
        return {
            "status": "success",
            "statistics": status.get("stats", {}),
            "configuration": status.get("config", {}),
        }
    except Exception as e:
        logger.error(f"Error getting scheduler stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting scheduler stats: {str(e)}"
        )

