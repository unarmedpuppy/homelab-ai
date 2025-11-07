"""
Position Sync Routes
====================

API routes for manual position sync operations.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from ...core.sync.position_sync import get_position_sync_service
from ...api.routes.trading import get_ibkr_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/positions")
async def sync_positions(
    account_id: int = Query(default=1, description="Account ID to sync positions for"),
    calculate_realized_pnl: bool = Query(default=True, description="Calculate realized P&L for closed positions")
) -> Dict[str, Any]:
    """
    Manually trigger position sync from IBKR to database.
    
    This endpoint allows manual triggering of position synchronization,
    which is useful for:
    - Testing sync functionality
    - Forcing immediate sync after trades
    - Recovering from sync failures
    
    Returns:
        Dict with sync results including:
        - success: Whether sync was successful
        - account_id: Account ID that was synced
        - positions_created: Number of new positions created
        - positions_updated: Number of positions updated
        - positions_closed: Number of positions closed
        - total_ibkr_positions: Total positions found in IBKR
        - stats: Full sync statistics
    """
    try:
        # Check if IBKR is connected
        manager = get_ibkr_manager()
        if not manager or not manager.is_connected:
            raise HTTPException(
                status_code=503,
                detail="IBKR not connected. Please connect to IBKR first using /api/trading/ibkr/connect"
            )
        
        # Get position sync service
        sync_service = get_position_sync_service()
        
        # Trigger sync
        result = await sync_service.sync_positions(
            account_id=account_id,
            calculate_realized_pnl=calculate_realized_pnl
        )
        
        if result.get("success"):
            logger.info(
                f"Manual position sync completed: "
                f"created={result.get('positions_created', 0)}, "
                f"updated={result.get('positions_updated', 0)}, "
                f"closed={result.get('positions_closed', 0)}"
            )
        else:
            logger.warning(f"Manual position sync failed: {result.get('error')}")
        
        return {
            "status": "success" if result.get("success") else "error",
            **result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during manual position sync: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error syncing positions: {str(e)}"
        )


@router.get("/status")
async def get_sync_status() -> Dict[str, Any]:
    """
    Get position sync service status and statistics.
    
    Returns:
        Dict with sync status including:
        - enabled: Whether position sync is enabled
        - last_sync_time: ISO timestamp of last sync (if any)
        - stats: Sync statistics (total_syncs, successful_syncs, failed_syncs, etc.)
        - ibkr_connected: Whether IBKR is currently connected
    """
    try:
        # Get position sync service
        sync_service = get_position_sync_service()
        
        # Get sync statistics
        stats = sync_service.get_stats()
        
        # Check IBKR connection status
        manager = get_ibkr_manager()
        ibkr_connected = manager is not None and manager.is_connected
        
        # Get last sync time
        last_sync_time = sync_service._last_sync_time
        last_sync_iso = last_sync_time.isoformat() if last_sync_time else None
        
        return {
            "status": "success",
            "enabled": True,  # Service is always enabled if instantiated
            "ibkr_connected": ibkr_connected,
            "last_sync_time": last_sync_iso,
            "last_sync_minutes_ago": (
                (datetime.now() - last_sync_time).total_seconds() / 60
                if last_sync_time else None
            ),
            "stats": stats,
            "callbacks_registered": sync_service._callbacks_registered
        }
        
    except Exception as e:
        logger.error(f"Error getting sync status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error getting sync status: {str(e)}"
        )

