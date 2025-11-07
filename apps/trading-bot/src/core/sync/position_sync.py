"""
Position Sync Service
=====================

Service for syncing IBKR positions to the database.
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from ...data.database import SessionLocal
from ...data.database.models import Position, PositionStatus, Account, PositionClose
from ...data.brokers.ibkr_client import BrokerPosition, IBKRClient, IBKRManager
from ...api.routes.trading import get_ibkr_manager

logger = logging.getLogger(__name__)


class PositionSyncService:
    """
    Service for syncing IBKR positions to database
    
    Features:
    - Sync positions from IBKR to database
    - Track position lifecycle (open → close)
    - Calculate realized P&L when positions close
    - Handle partial closes and position updates
    """
    
    def __init__(self, ibkr_manager: Optional[IBKRManager] = None):
        """
        Initialize position sync service
        
        Args:
            ibkr_manager: IBKR manager instance (optional, will get from global if None)
        """
        self.ibkr_manager = ibkr_manager
        self._last_sync_time: Optional[datetime] = None
        self._callbacks_registered = False
        self._sync_stats = {
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "positions_created": 0,
            "positions_updated": 0,
            "positions_closed": 0,
            "callback_triggers": 0,
            "last_error": None
        }
    
    def _get_ibkr_manager(self) -> Optional[IBKRManager]:
        """Get IBKR manager instance"""
        if self.ibkr_manager:
            return self.ibkr_manager
        try:
            return get_ibkr_manager()
        except Exception as e:
            logger.debug(f"Could not get IBKR manager: {e}")
            return None
    
    @contextmanager
    def _get_session(self, autocommit: bool = True):
        """
        Get database session as context manager
        
        Args:
            autocommit: If True, automatically commit on success and rollback on error
        
        Yields:
            Session: Database session
        """
        session = SessionLocal()
        try:
            yield session
            if autocommit:
                session.commit()
        except Exception:
            if autocommit:
                session.rollback()
            raise
        finally:
            session.close()
    
    async def sync_positions(
        self, 
        account_id: int = 1,
        calculate_realized_pnl: bool = True
    ) -> Dict[str, Any]:
        """
        Sync positions from IBKR to database
        
        Args:
            account_id: Account ID to sync positions for
            calculate_realized_pnl: Whether to calculate realized P&L for closed positions
        
        Returns:
            Dict with sync results and statistics
        """
        self._sync_stats["total_syncs"] += 1
        sync_start = datetime.now()
        
        try:
            # Get IBKR manager and client
            ibkr_manager = self._get_ibkr_manager()
            if not ibkr_manager or not ibkr_manager.is_connected:
                error_msg = "IBKR not connected, cannot sync positions"
                logger.warning(error_msg)
                self._sync_stats["failed_syncs"] += 1
                self._sync_stats["last_error"] = error_msg
                return {
                    "success": False,
                    "error": error_msg,
                    "stats": self._sync_stats.copy()
                }
            
            client = await ibkr_manager.get_client()
            if not client:
                error_msg = "IBKR client not available"
                logger.warning(error_msg)
                self._sync_stats["failed_syncs"] += 1
                self._sync_stats["last_error"] = error_msg
                return {
                    "success": False,
                    "error": error_msg,
                    "stats": self._sync_stats.copy()
                }
            
            # Get positions from IBKR
            try:
                ibkr_positions = await client.get_positions()
                logger.debug(f"Retrieved {len(ibkr_positions)} positions from IBKR")
            except Exception as e:
                error_msg = f"Error getting positions from IBKR: {e}"
                logger.error(error_msg, exc_info=True)
                self._sync_stats["failed_syncs"] += 1
                self._sync_stats["last_error"] = error_msg
                return {
                    "success": False,
                    "error": error_msg,
                    "stats": self._sync_stats.copy()
                }
            
            # Verify account exists
            with self._get_session(autocommit=False) as session:
                account = session.query(Account).filter(Account.id == account_id).first()
                if not account:
                    error_msg = f"Account {account_id} not found"
                    logger.error(error_msg)
                    self._sync_stats["failed_syncs"] += 1
                    self._sync_stats["last_error"] = error_msg
                    return {
                        "success": False,
                        "error": error_msg,
                        "stats": self._sync_stats.copy()
                    }
            
            # Create map of IBKR positions by symbol
            ibkr_position_map: Dict[str, BrokerPosition] = {
                pos.symbol: pos for pos in ibkr_positions if pos.quantity != 0
            }
            
            # Get existing positions from database
            with self._get_session(autocommit=False) as session:
                db_positions = session.query(Position).filter(
                    Position.account_id == account_id
                ).all()
                
                db_position_map: Dict[str, Position] = {
                    pos.symbol: pos for pos in db_positions
                }
                
                # Track changes
                positions_created = 0
                positions_updated = 0
                positions_closed = 0
                
                # Process IBKR positions
                for symbol, ibkr_pos in ibkr_position_map.items():
                    db_pos = db_position_map.get(symbol)
                    
                    if not db_pos:
                        # Create new position
                        new_position = Position(
                            account_id=account_id,
                            symbol=symbol,
                            quantity=ibkr_pos.quantity,
                            average_price=ibkr_pos.average_price,
                            current_price=ibkr_pos.market_price,
                            unrealized_pnl=ibkr_pos.unrealized_pnl,
                            unrealized_pnl_pct=ibkr_pos.unrealized_pnl_pct,
                            status=PositionStatus.OPEN,
                            opened_at=datetime.now(),
                            last_synced_at=datetime.now()
                        )
                        session.add(new_position)
                        positions_created += 1
                        logger.info(f"Created new position: {symbol} ({ibkr_pos.quantity} shares)")
                    
                    else:
                        # Update existing position
                        old_quantity = db_pos.quantity
                        old_average_price = db_pos.average_price
                        old_status = db_pos.status
                        
                        # Calculate average price based on quantity change
                        # If quantity increased, calculate weighted average
                        # If quantity decreased (partial close), keep existing average (FIFO)
                        # If quantity unchanged, use IBKR's average (may have been updated)
                        if ibkr_pos.quantity > old_quantity:
                            # Position increased (additional buy) - calculate weighted average
                            # We derive the new shares' cost from IBKR's total cost basis
                            # Formula: weighted_avg = (old_cost_basis + new_cost_basis) / total_qty
                            total_cost_basis = ibkr_pos.average_price * ibkr_pos.quantity
                            old_cost_basis = old_average_price * old_quantity
                            new_shares = ibkr_pos.quantity - old_quantity
                            
                            if new_shares > 0 and old_quantity > 0:
                                # Calculate cost of new shares
                                new_shares_cost = total_cost_basis - old_cost_basis
                                new_shares_avg = new_shares_cost / new_shares
                                
                                # Calculate weighted average (should match IBKR's average_price)
                                weighted_avg = (old_average_price * old_quantity + new_shares_avg * new_shares) / ibkr_pos.quantity
                                
                                # Use calculated weighted average (should equal IBKR's, but we calculate it explicitly)
                                # This ensures we maintain our own cost basis tracking
                                db_pos.average_price = weighted_avg
                                
                                # Log if there's a discrepancy (shouldn't happen, but good to know)
                                if abs(weighted_avg - ibkr_pos.average_price) > 0.01:
                                    logger.warning(
                                        f"Position increased: {symbol} - "
                                        f"weighted avg (${weighted_avg:.2f}) differs from IBKR avg (${ibkr_pos.average_price:.2f})"
                                    )
                                else:
                                    logger.debug(
                                        f"Position increased: {symbol} - "
                                        f"calculated weighted avg: ${weighted_avg:.2f} "
                                        f"(old: ${old_average_price:.2f} x {old_quantity}, "
                                        f"new: ${new_shares_avg:.2f} x {new_shares})"
                                    )
                            else:
                                # Fallback to IBKR's average if calculation can't be done
                                db_pos.average_price = ibkr_pos.average_price
                                logger.debug(
                                    f"Position increased: {symbol} - "
                                    f"using IBKR average: ${ibkr_pos.average_price:.2f} "
                                    f"(old_qty: {old_quantity}, new_qty: {ibkr_pos.quantity})"
                                )
                        elif ibkr_pos.quantity < old_quantity:
                            # Partial close - keep existing average price (FIFO assumption)
                            # The average price of remaining shares doesn't change
                            db_pos.average_price = old_average_price
                            
                            # Calculate and track realized P&L for partial close
                            if calculate_realized_pnl:
                                closed_quantity = old_quantity - ibkr_pos.quantity
                                # Use current_price as exit price (or average_price if 0)
                                exit_price = ibkr_pos.market_price if ibkr_pos.market_price > 0 else old_average_price
                                
                                # Calculate realized P&L for closed portion
                                partial_realized_pnl = (exit_price - old_average_price) * closed_quantity
                                partial_realized_pnl_pct = ((exit_price / old_average_price) - 1) * 100 if old_average_price > 0 else 0
                                
                                # Create PositionClose record for this partial close
                                position_close = PositionClose(
                                    position_id=db_pos.id,
                                    account_id=account_id,
                                    symbol=symbol,
                                    quantity_closed=closed_quantity,
                                    entry_price=old_average_price,
                                    exit_price=exit_price,
                                    realized_pnl=partial_realized_pnl,
                                    realized_pnl_pct=partial_realized_pnl_pct,
                                    closed_at=datetime.now(),
                                    is_full_close=False
                                )
                                session.add(position_close)
                                
                                # Update position's total realized P&L (sum of all closes)
                                # Get existing closes for this position
                                existing_closes = session.query(PositionClose).filter(
                                    PositionClose.position_id == db_pos.id
                                ).all()
                                total_realized_pnl = sum(close.realized_pnl for close in existing_closes) + partial_realized_pnl
                                
                                # Store cumulative realized P&L in position (for quick access)
                                # Note: This is the sum of all partial closes, not just this one
                                db_pos.realized_pnl = total_realized_pnl
                                
                                logger.info(
                                    f"Partial close: {symbol} - "
                                    f"closed {closed_quantity} shares, "
                                    f"realized P&L: ${partial_realized_pnl:.2f} "
                                    f"(exit: ${exit_price:.2f}, entry: ${old_average_price:.2f}, "
                                    f"total realized: ${total_realized_pnl:.2f})"
                                )
                            else:
                                logger.debug(
                                    f"Partial close: {symbol} - "
                                    f"keeping average price: ${old_average_price:.2f} "
                                    f"(FIFO assumption, P&L calculation disabled)"
                                )
                        else:
                            # Quantity unchanged - use IBKR's average (may have been updated)
                            db_pos.average_price = ibkr_pos.average_price
                        
                        # Update other position fields
                        db_pos.quantity = ibkr_pos.quantity
                        db_pos.current_price = ibkr_pos.market_price
                        db_pos.unrealized_pnl = ibkr_pos.unrealized_pnl
                        db_pos.unrealized_pnl_pct = ibkr_pos.unrealized_pnl_pct
                        db_pos.last_synced_at = datetime.now()  # Update sync timestamp
                        
                        # Handle position close
                        if ibkr_pos.quantity == 0 and db_pos.status == PositionStatus.OPEN:
                            db_pos.status = PositionStatus.CLOSED
                            db_pos.closed_at = datetime.now()
                            
                            # Calculate realized P&L if enabled
                            if calculate_realized_pnl:
                                # Use current_price as exit price (or average_price if 0)
                                exit_price = ibkr_pos.market_price if ibkr_pos.market_price > 0 else db_pos.average_price
                                
                                # Calculate realized P&L for full close
                                realized_pnl = (exit_price - db_pos.average_price) * old_quantity
                                realized_pnl_pct = ((exit_price / db_pos.average_price) - 1) * 100 if db_pos.average_price > 0 else 0
                                
                                # Create PositionClose record for full close
                                position_close = PositionClose(
                                    position_id=db_pos.id,
                                    account_id=account_id,
                                    symbol=symbol,
                                    quantity_closed=old_quantity,
                                    entry_price=db_pos.average_price,
                                    exit_price=exit_price,
                                    realized_pnl=realized_pnl,
                                    realized_pnl_pct=realized_pnl_pct,
                                    closed_at=datetime.now(),
                                    is_full_close=True
                                )
                                session.add(position_close)
                                
                                # Store realized P&L in position (for quick access)
                                # This is the final realized P&L (sum of all closes including this full close)
                                # Get existing closes for this position (partial closes)
                                existing_closes = session.query(PositionClose).filter(
                                    PositionClose.position_id == db_pos.id,
                                    PositionClose.is_full_close == False
                                ).all()
                                partial_closes_pnl = sum(close.realized_pnl for close in existing_closes)
                                total_realized_pnl = partial_closes_pnl + realized_pnl
                                
                                db_pos.realized_pnl = total_realized_pnl
                                
                                logger.info(
                                    f"Position closed: {symbol}, "
                                    f"realized P&L: ${realized_pnl:.2f} "
                                    f"(exit: ${exit_price:.2f}, entry: ${db_pos.average_price:.2f}, qty: {old_quantity}, "
                                    f"total realized: ${total_realized_pnl:.2f})"
                                )
                            
                            positions_closed += 1
                            logger.info(f"Closed position: {symbol}")
                        
                        # Handle quantity changes (partial closes or additions)
                        elif ibkr_pos.quantity != old_quantity:
                            if ibkr_pos.quantity < old_quantity:
                                # Partial close
                                logger.info(
                                    f"Partial close: {symbol} "
                                    f"({old_quantity} → {ibkr_pos.quantity} shares, "
                                    f"avg price: ${db_pos.average_price:.2f})"
                                )
                            elif ibkr_pos.quantity > old_quantity:
                                # Position increased (additional buy)
                                logger.info(
                                    f"Position increased: {symbol} "
                                    f"({old_quantity} → {ibkr_pos.quantity} shares, "
                                    f"avg price: ${old_average_price:.2f} → ${db_pos.average_price:.2f})"
                                )
                            
                            # Ensure status is OPEN if quantity > 0
                            if ibkr_pos.quantity > 0:
                                db_pos.status = PositionStatus.OPEN
                                db_pos.closed_at = None
                        
                        positions_updated += 1
                
                # Handle positions in DB but not in IBKR
                for symbol, db_pos in db_position_map.items():
                    if symbol not in ibkr_position_map:
                        # Position exists in DB but not in IBKR
                        if db_pos.quantity > 0 and db_pos.status == PositionStatus.OPEN:
                            # Position was closed externally (not through our system)
                            logger.warning(
                                f"Position {symbol} exists in DB but not in IBKR. "
                                f"Marking as closed. (This may indicate external position closure)"
                            )
                            # Option: Mark as closed or leave as-is
                            # For now, we'll leave it as-is to avoid data loss
                            # User can manually close if needed
                        # If already closed, no action needed
                
                # Commit all changes
                session.commit()
                
                # Update statistics
                self._sync_stats["positions_created"] += positions_created
                self._sync_stats["positions_updated"] += positions_updated
                self._sync_stats["positions_closed"] += positions_closed
                self._sync_stats["successful_syncs"] += 1
                self._last_sync_time = datetime.now()
                
                sync_duration = (datetime.now() - sync_start).total_seconds()
                
                logger.info(
                    f"Position sync completed: "
                    f"created={positions_created}, "
                    f"updated={positions_updated}, "
                    f"closed={positions_closed}, "
                    f"duration={sync_duration:.2f}s"
                )
                
                return {
                    "success": True,
                    "account_id": account_id,
                    "positions_created": positions_created,
                    "positions_updated": positions_updated,
                    "positions_closed": positions_closed,
                    "total_ibkr_positions": len(ibkr_position_map),
                    "total_db_positions": len(db_position_map),
                    "sync_duration_seconds": sync_duration,
                    "stats": self._sync_stats.copy()
                }
        
        except Exception as e:
            error_msg = f"Error syncing positions: {e}"
            logger.error(error_msg, exc_info=True)
            self._sync_stats["failed_syncs"] += 1
            self._sync_stats["last_error"] = str(e)
            return {
                "success": False,
                "error": error_msg,
                "stats": self._sync_stats.copy()
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get sync statistics"""
        return {
            **self._sync_stats,
            "last_sync_time": self._last_sync_time.isoformat() if self._last_sync_time else None
        }
    
    def reset_stats(self):
        """Reset sync statistics"""
        self._sync_stats = {
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "positions_created": 0,
            "positions_updated": 0,
            "positions_closed": 0,
            "callback_triggers": 0,
            "last_error": None
        }
        self._last_sync_time = None
    
    def _on_position_update_callback(self, position):
        """
        Callback handler for IBKR position updates
        
        This is called when IBKR reports a position change.
        Triggers a position sync to update the database.
        
        Note: This is a synchronous callback, but it schedules an async sync task.
        
        Args:
            position: IBKR Position object from ib_insync
        """
        try:
            # Increment callback trigger counter
            self._sync_stats["callback_triggers"] += 1
            
            # Get config to check if callback sync is enabled
            from ...config.settings import settings
            if not settings.position_sync.sync_on_position_update:
                logger.debug("Position update callback sync is disabled, skipping")
                return
            
            # Get account ID from config
            account_id = settings.position_sync.default_account_id
            
            # Trigger sync (debounced - only if enough time has passed since last sync)
            # This prevents too many syncs from rapid position updates
            if self._last_sync_time:
                time_since_last_sync = (datetime.now() - self._last_sync_time).total_seconds()
                # Only sync if at least 5 seconds have passed since last sync
                if time_since_last_sync < 5:
                    logger.debug(f"Position update callback: skipping sync (only {time_since_last_sync:.1f}s since last sync)")
                    return
            
            symbol = position.contract.symbol if position.contract else "unknown"
            logger.debug(f"Position update callback triggered sync for {symbol}")
            
            # Schedule async sync task (callback is sync, but sync_positions is async)
            # Use asyncio to create a task that will run the sync
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Event loop is running, create a task
                    asyncio.create_task(self._sync_from_callback(account_id, settings.position_sync.calculate_realized_pnl))
                else:
                    # No event loop running, run sync in new event loop
                    asyncio.run(self._sync_from_callback(account_id, settings.position_sync.calculate_realized_pnl))
            except RuntimeError:
                # No event loop available, create a new one
                asyncio.run(self._sync_from_callback(account_id, settings.position_sync.calculate_realized_pnl))
        
        except Exception as e:
            logger.error(f"Error in position update callback: {e}", exc_info=True)
            # Don't increment failed_syncs here - the sync_positions method handles that
    
    async def _sync_from_callback(self, account_id: int, calculate_realized_pnl: bool):
        """
        Helper method to run sync from callback (async wrapper)
        
        Args:
            account_id: Account ID to sync
            calculate_realized_pnl: Whether to calculate realized P&L
        """
        try:
            result = await self.sync_positions(
                account_id=account_id,
                calculate_realized_pnl=calculate_realized_pnl
            )
            
            if result.get("success"):
                logger.debug("Position sync from callback completed successfully")
            else:
                logger.warning(f"Position sync from callback failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Error in callback sync task: {e}", exc_info=True)
    
    def register_ibkr_callbacks(self) -> bool:
        """
        Register position update callbacks with IBKR client
        
        Returns:
            True if callbacks were registered, False otherwise
        """
        if self._callbacks_registered:
            logger.debug("IBKR callbacks already registered")
            return True
        
        try:
            ibkr_manager = self._get_ibkr_manager()
            if not ibkr_manager or not ibkr_manager.is_connected:
                logger.debug("IBKR not connected, cannot register callbacks")
                return False
            
            # Get the client - need to check if it's available
            # The client might not be available immediately, so we'll try to get it
            # For now, we'll register when the client is available
            # This will be called from the scheduler or when IBKR connects
            
            # Check if we can access the client
            if hasattr(ibkr_manager, 'client') and ibkr_manager.client:
                client = ibkr_manager.client
                if hasattr(client, 'position_update_callbacks'):
                    # Register callback
                    client.position_update_callbacks.append(self._on_position_update_callback)
                    self._callbacks_registered = True
                    logger.info("Registered position update callbacks with IBKR client")
                    return True
                else:
                    logger.warning("IBKR client does not support position_update_callbacks")
                    return False
            else:
                logger.debug("IBKR client not available yet, callbacks will be registered when client is ready")
                return False
        
        except Exception as e:
            logger.error(f"Error registering IBKR callbacks: {e}", exc_info=True)
            return False
    
    def unregister_ibkr_callbacks(self):
        """Unregister position update callbacks from IBKR client"""
        if not self._callbacks_registered:
            return
        
        try:
            ibkr_manager = self._get_ibkr_manager()
            if not ibkr_manager:
                return
            
            if hasattr(ibkr_manager, 'client') and ibkr_manager.client:
                client = ibkr_manager.client
                if hasattr(client, 'position_update_callbacks'):
                    # Remove callback if it exists
                    if self._on_position_update_callback in client.position_update_callbacks:
                        client.position_update_callbacks.remove(self._on_position_update_callback)
                        self._callbacks_registered = False
                        logger.info("Unregistered position update callbacks from IBKR client")
        
        except Exception as e:
            logger.error(f"Error unregistering IBKR callbacks: {e}", exc_info=True)


# Global instance
_position_sync_service: Optional[PositionSyncService] = None


def get_position_sync_service() -> PositionSyncService:
    """Get global position sync service instance"""
    global _position_sync_service
    if _position_sync_service is None:
        _position_sync_service = PositionSyncService()
    return _position_sync_service

