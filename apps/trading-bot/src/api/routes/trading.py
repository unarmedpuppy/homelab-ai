"""
Trading Routes
==============

API routes for trading operations and IBKR connection management.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
import logging
from pydantic import BaseModel
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from ...data.brokers.ibkr_client import IBKRClient, IBKRManager, OrderSide
from ...data.database.models import Trade, TradeSide, OrderStatus, Account, Position, PositionStatus, Strategy
from ...data.database import SessionLocal, get_db
from ...config.settings import settings
from ...utils.metrics_integration import update_portfolio_metrics_from_positions
from ...core.risk import get_risk_manager, RiskManager
from ...data.providers.market_data import DataProviderManager
from ...core.confluence import ConfluenceCalculator
from ...core.strategy.base import TradingSignal, SignalType

logger = logging.getLogger(__name__)

router = APIRouter()

# Global IBKR manager instance
_ibkr_manager: Optional[IBKRManager] = None

class ConnectionTestRequest(BaseModel):
    """Connection test request model"""
    host: Optional[str] = None
    port: Optional[int] = None
    client_id: Optional[int] = None

class ConnectionResponse(BaseModel):
    """Connection status response model"""
    connected: bool
    host: str
    port: int
    client_id: int
    message: str

def get_ibkr_manager() -> Optional[IBKRManager]:
    """Get or create IBKR manager instance"""
    global _ibkr_manager
    if _ibkr_manager is None:
        _ibkr_manager = IBKRManager(
            host=settings.ibkr.host,
            port=settings.ibkr.port,
            client_id=settings.ibkr.client_id
        )
    return _ibkr_manager

@router.get("/ibkr/status", response_model=ConnectionResponse)
async def ibkr_connection_status():
    """Get current IBKR connection status"""
    manager = get_ibkr_manager()
    
    if not manager:
        return ConnectionResponse(
            connected=False,
            host=settings.ibkr.host,
            port=settings.ibkr.port,
            client_id=settings.ibkr.client_id,
            message="IBKR manager not initialized"
        )
    
    # Ensure is_connected is a boolean, not None
    is_connected = bool(manager.is_connected) if manager.is_connected is not None else False
    
    # Update broker connection status metric
    try:
        from ...utils.metrics_trading import update_broker_connection_status
        update_broker_connection_status(is_connected)
    except Exception:
        pass
    
    return ConnectionResponse(
        connected=is_connected,
        host=settings.ibkr.host,
        port=settings.ibkr.port,
        client_id=settings.ibkr.client_id,
        message="Connected" if is_connected else "Not connected"
    )

@router.post("/ibkr/connect")
async def ibkr_connect(request: Optional[ConnectionTestRequest] = None):
    """Connect to IBKR"""
    global _ibkr_manager
    
    # Use provided values or defaults
    host = request.host if request and request.host else settings.ibkr.host
    port = request.port if request and request.port else settings.ibkr.port
    client_id = request.client_id if request and request.client_id else settings.ibkr.client_id
    
    try:
        # Create new manager with specified config
        _ibkr_manager = IBKRManager(host=host, port=port, client_id=client_id)
        await _ibkr_manager.start()
        
        if _ibkr_manager.is_connected:
            return {
                "status": "success",
                "message": "Successfully connected to IBKR",
                "host": host,
                "port": port,
                "client_id": client_id
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to connect to IBKR. Make sure TWS/Gateway is running and API is enabled."
            )
    except Exception as e:
        logger.error(f"Error connecting to IBKR: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Connection error: {str(e)}"
        )

@router.post("/ibkr/disconnect")
async def ibkr_disconnect():
    """Disconnect from IBKR"""
    global _ibkr_manager
    
    if _ibkr_manager:
        try:
            await _ibkr_manager.stop()
            _ibkr_manager = None
            return {
                "status": "success",
                "message": "Disconnected from IBKR"
            }
        except Exception as e:
            logger.error(f"Error disconnecting from IBKR: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Disconnect error: {str(e)}"
            )
    else:
        return {
            "status": "success",
            "message": "Already disconnected"
        }

@router.post("/ibkr/test")
async def ibkr_test_connection(request: Optional[ConnectionTestRequest] = None):
    """Test IBKR connection with detailed diagnostics"""
    # Use provided values or defaults
    host = request.host if request and request.host else settings.ibkr.host
    port = request.port if request and request.port else settings.ibkr.port
    client_id = request.client_id if request and request.client_id else settings.ibkr.client_id
    
    client = None
    results = {
        "connected": False,
        "host": host,
        "port": port,
        "client_id": client_id,
        "tests": {}
    }
    
    try:
        logger.info(f"Testing IBKR connection to {host}:{port} (client_id: {client_id})")
        
        client = IBKRClient(host=host, port=port, client_id=client_id)
        connected = await client.connect()
        
        results["connected"] = connected
        
        if not connected:
            results["error"] = "Failed to connect. Make sure TWS/Gateway is running and API connections are enabled."
            return results
        
        # Test account access
        try:
            account_summary = await client.get_account_summary()
            results["tests"]["account_access"] = {
                "success": True,
                "fields_retrieved": len(account_summary)
            }
        except Exception as e:
            results["tests"]["account_access"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test market data access
        try:
            contract = client.create_contract("AAPL")
            market_data = await client.get_market_data(contract)
            results["tests"]["market_data"] = {
                "success": True,
                "sample_symbol": "AAPL",
                "data_keys": list(market_data.keys())
            }
        except Exception as e:
            results["tests"]["market_data"] = {
                "success": False,
                "error": str(e)
            }
        
        # Test position access
        try:
            positions = await client.get_positions()
            results["tests"]["positions"] = {
                "success": True,
                "position_count": len(positions)
            }
        except Exception as e:
            results["tests"]["positions"] = {
                "success": False,
                "error": str(e)
            }
        
        results["message"] = "Connection test completed successfully"
        
    except Exception as e:
        logger.error(f"Error testing IBKR connection: {e}", exc_info=True)
        results["error"] = str(e)
    finally:
        if client:
            await client.disconnect()
    
    return results

@router.get("/ibkr/account")
async def ibkr_account_summary():
    """Get IBKR account summary"""
    manager = get_ibkr_manager()
    
    if not manager or not manager.is_connected:
        raise HTTPException(
            status_code=503,
            detail="IBKR not connected. Please connect first using /api/trading/ibkr/connect"
        )
    
    try:
        client = await manager.get_client()
        account_summary = await client.get_account_summary()
        return {
            "status": "success",
            "account_data": account_summary
        }
    except Exception as e:
        logger.error(f"Error getting account summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving account data: {str(e)}"
        )

@router.get("/ibkr/positions")
async def ibkr_positions():
    """Get current IBKR positions"""
    manager = get_ibkr_manager()
    
    if not manager or not manager.is_connected:
        raise HTTPException(
            status_code=503,
            detail="IBKR not connected. Please connect first using /api/trading/ibkr/connect"
        )
    
    try:
        client = await manager.get_client()
        positions = await client.get_positions()
        
        positions_list = []
        for pos in positions:
            positions_list.append({
                "symbol": pos.symbol,
                "quantity": pos.quantity,
                "average_price": pos.average_price,
                "market_price": pos.market_price,
                "unrealized_pnl": pos.unrealized_pnl,
                "unrealized_pnl_pct": pos.unrealized_pnl_pct
            })
            
            # Update position metrics
            try:
                from ...utils.metrics_trading import update_position_metrics
                update_position_metrics(
                    symbol=pos.symbol,
                    quantity=pos.quantity,
                    pnl=pos.unrealized_pnl
                )
            except Exception:
                pass
        
        # Update portfolio-level metrics
        try:
            update_portfolio_metrics_from_positions(positions_list)
        except Exception:
            pass
        
        return {
            "status": "success",
            "positions": positions_list
        }
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving positions: {str(e)}"
        )

@router.get("/performance")
async def get_performance_metrics(
    account_id: int = Query(default=1),
    strategy_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive performance metrics for trading account.
    
    Calculates win rate, trade statistics, P&L metrics, and performance breakdowns.
    
    Args:
        account_id: Account ID to get metrics for (default: 1)
        strategy_id: Optional strategy ID to filter by
        db: Database session
        
    Returns:
        Dictionary with performance metrics including:
        - win_rate: Win rate as decimal (0.0-1.0)
        - total_trades: Total number of closed positions
        - winning_trades: Number of winning trades
        - losing_trades: Number of losing trades
        - total_realized_pnl: Sum of P&L from closed positions
        - total_unrealized_pnl: Sum of P&L from open positions
        - average_win: Average win amount
        - average_loss: Average loss amount
        - largest_win: Largest winning trade
        - largest_loss: Largest losing trade
        - profit_factor: Total wins / abs(total losses)
        - win_loss_ratio: Average win / abs(average loss)
        - average_pnl_per_trade: Average P&L per closed trade
        - date_range: First and last trade dates
    """
    try:
        # Query closed positions
        closed_query = db.query(Position).filter(
            Position.account_id == account_id,
            Position.status == PositionStatus.CLOSED
        )
        
        if strategy_id:
            # Join with Trade table to filter by strategy
            closed_query = closed_query.join(Trade).filter(
                Trade.strategy_id == strategy_id
            )
        
        closed_positions = closed_query.all()
        
        # Query open positions for unrealized P&L
        open_query = db.query(Position).filter(
            Position.account_id == account_id,
            Position.status == PositionStatus.OPEN
        )
        
        if strategy_id:
            open_query = open_query.join(Trade).filter(
                Trade.strategy_id == strategy_id
            )
        
        open_positions = open_query.all()
        
        # Calculate metrics from closed positions
        total_trades = len(closed_positions)
        
        if total_trades == 0:
            # Return empty metrics structure
            return {
                "win_rate": 0.0,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "total_realized_pnl": 0.0,
                "total_unrealized_pnl": sum(p.unrealized_pnl or 0.0 for p in open_positions),
                "average_win": 0.0,
                "average_loss": 0.0,
                "largest_win": 0.0,
                "largest_loss": 0.0,
                "profit_factor": None,
                "win_loss_ratio": None,
                "average_pnl_per_trade": 0.0,
                "date_range": {
                    "first_trade": None,
                    "last_trade": None
                }
            }
        
        # Separate winning and losing trades
        winning_trades = [p for p in closed_positions if (p.unrealized_pnl or 0.0) > 0]
        losing_trades = [p for p in closed_positions if (p.unrealized_pnl or 0.0) <= 0]
        
        winning_count = len(winning_trades)
        losing_count = len(losing_trades)
        
        # Calculate win rate
        win_rate = winning_count / total_trades if total_trades > 0 else 0.0
        
        # Calculate P&L metrics
        total_realized_pnl = sum(p.unrealized_pnl or 0.0 for p in closed_positions)
        total_unrealized_pnl = sum(p.unrealized_pnl or 0.0 for p in open_positions)
        
        # Calculate averages
        average_win = sum(p.unrealized_pnl or 0.0 for p in winning_trades) / winning_count if winning_count > 0 else 0.0
        average_loss = sum(p.unrealized_pnl or 0.0 for p in losing_trades) / losing_count if losing_count > 0 else 0.0
        
        # Calculate largest win/loss
        largest_win = max((p.unrealized_pnl or 0.0 for p in winning_trades), default=0.0)
        largest_loss = min((p.unrealized_pnl or 0.0 for p in losing_trades), default=0.0)
        
        # Calculate profit factor (total wins / abs(total losses))
        total_wins = sum(p.unrealized_pnl or 0.0 for p in winning_trades)
        total_losses = abs(sum(p.unrealized_pnl or 0.0 for p in losing_trades))
        profit_factor = total_wins / total_losses if total_losses > 0 else None
        
        # Calculate win/loss ratio (average win / abs(average loss))
        win_loss_ratio = average_win / abs(average_loss) if average_loss < 0 else None
        
        # Average P&L per trade
        average_pnl_per_trade = total_realized_pnl / total_trades if total_trades > 0 else 0.0
        
        # Get date range
        first_trade = min((p.opened_at for p in closed_positions if p.opened_at), default=None)
        last_trade = max((p.closed_at for p in closed_positions if p.closed_at), default=None)
        
        return {
            "win_rate": round(win_rate, 4),
            "total_trades": total_trades,
            "winning_trades": winning_count,
            "losing_trades": losing_count,
            "total_realized_pnl": round(total_realized_pnl, 2),
            "total_unrealized_pnl": round(total_unrealized_pnl, 2),
            "average_win": round(average_win, 2),
            "average_loss": round(average_loss, 2),
            "largest_win": round(largest_win, 2),
            "largest_loss": round(largest_loss, 2),
            "profit_factor": round(profit_factor, 4) if profit_factor is not None else None,
            "win_loss_ratio": round(win_loss_ratio, 4) if win_loss_ratio is not None else None,
            "average_pnl_per_trade": round(average_pnl_per_trade, 2),
            "date_range": {
                "first_trade": first_trade.isoformat() if first_trade else None,
                "last_trade": last_trade.isoformat() if last_trade else None
            }
        }
    
    except Exception as e:
        logger.error(f"Error calculating performance metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating performance metrics: {str(e)}"
        )


@router.get("/portfolio/summary")
async def portfolio_summary(account_id: int = Query(default=1, description="Account ID")):
    """
    Get comprehensive portfolio summary including:
    - Portfolio value from IBKR
    - Cash balance
    - Current positions count and value
    - Daily P&L from trades
    - Total P&L
    - Win rate from closed trades
    - Active positions count
    """
    session = SessionLocal()
    
    try:
        # Initialize response structure
        summary = {
            "portfolio_value": 0.0,
            "cash_balance": 0.0,
            "positions_value": 0.0,
            "daily_pnl": 0.0,
            "daily_pnl_percent": 0.0,
            "total_pnl": 0.0,
            "win_rate": 0.0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "active_positions": 0,
            "last_updated": datetime.now().isoformat(),
            "ibkr_connected": False
        }
        
        # Get IBKR account data if connected
        manager = get_ibkr_manager()
        if manager and manager.is_connected:
            try:
                client = await manager.get_client()
                account_summary = await client.get_account_summary()
                
                # Extract portfolio value (NetLiquidation)
                if "NetLiquidation" in account_summary:
                    summary["portfolio_value"] = float(account_summary["NetLiquidation"].get("value", 0))
                
                # Extract cash balance
                if "TotalCashValue" in account_summary:
                    summary["cash_balance"] = float(account_summary["TotalCashValue"].get("value", 0))
                
                # Get positions
                positions = await client.get_positions()
                summary["active_positions"] = len([p for p in positions if p.quantity != 0])
                
                # Calculate positions value (sum of market_price * quantity)
                summary["positions_value"] = sum(
                    p.market_price * p.quantity for p in positions if p.quantity != 0
                )
                
                summary["ibkr_connected"] = True
                
            except Exception as e:
                logger.warning(f"Error getting IBKR data for portfolio summary: {e}")
                summary["ibkr_connected"] = False
        
        # Query database for trade statistics
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # Get today's filled trades for daily P&L
        today_trades = session.query(Trade).filter(
            and_(
                Trade.account_id == account_id,
                Trade.status == OrderStatus.FILLED,
                Trade.executed_at >= today_start,
                Trade.executed_at <= today_end
            )
        ).all()
        
        # Calculate daily P&L from position changes
        # For now, we'll use unrealized P&L from positions if available
        # TODO: Calculate realized P&L from closed positions/trades
        if manager and manager.is_connected:
            try:
                positions = await manager.get_client().get_positions()
                daily_unrealized_pnl = sum(p.unrealized_pnl for p in positions if p.quantity != 0)
                # This is a simplified calculation - ideally we'd track daily P&L separately
                summary["daily_pnl"] = daily_unrealized_pnl
            except Exception:
                pass
        
        # Get all filled trades for win rate calculation
        # We need to calculate realized P&L from closed positions
        # For now, we'll use a simplified approach based on position P&L
        all_filled_trades = session.query(Trade).filter(
            and_(
                Trade.account_id == account_id,
                Trade.status == OrderStatus.FILLED
            )
        ).all()
        
        summary["total_trades"] = len(all_filled_trades)
        
        # Calculate win rate from database positions that are closed
        closed_positions = session.query(Position).filter(
            and_(
                Position.account_id == account_id,
                Position.status == PositionStatus.CLOSED
            )
        ).all()
        
        if closed_positions:
            winning_positions = [p for p in closed_positions if p.unrealized_pnl > 0]
            summary["winning_trades"] = len(winning_positions)
            summary["losing_trades"] = len(closed_positions) - len(winning_positions)
            
            if len(closed_positions) > 0:
                summary["win_rate"] = len(winning_positions) / len(closed_positions)
            
            # Calculate total P&L from closed positions
            summary["total_pnl"] = sum(p.unrealized_pnl for p in closed_positions)
        
        # Calculate daily P&L percent
        if summary["portfolio_value"] > 0:
            summary["daily_pnl_percent"] = (summary["daily_pnl"] / summary["portfolio_value"]) * 100
        
        return {
            "status": "success",
            **summary
        }
    
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving portfolio summary: {str(e)}"
        )
    finally:
        session.close()

@router.get("/trades")
async def get_trades(
    account_id: int = Query(default=1, description="Account ID"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of trades to return"),
    offset: int = Query(default=0, ge=0, description="Number of trades to skip"),
    symbol: Optional[str] = Query(default=None, description="Filter by symbol"),
    side: Optional[str] = Query(default=None, description="Filter by side (BUY/SELL)"),
    start_date: Optional[date] = Query(default=None, description="Filter trades from this date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(default=None, description="Filter trades up to this date (YYYY-MM-DD)"),
    sort_by: str = Query(default="executed_at", description="Field to sort by"),
    sort_order: str = Query(default="desc", description="Sort order (asc/desc)")
):
    """
    Get paginated list of trades from the database
    
    Supports filtering by:
    - account_id (required)
    - symbol (optional)
    - side (BUY/SELL, optional)
    - date range (start_date, end_date, optional)
    
    Supports pagination with limit and offset.
    Returns trades sorted by executed_at (descending by default).
    Includes realized P&L for closed positions and strategy information.
    """
    session = SessionLocal()
    
    try:
        # Validate sort_by field
        valid_sort_fields = ["executed_at", "timestamp", "symbol", "price", "quantity"]
        if sort_by not in valid_sort_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}"
            )
        
        # Validate sort_order
        if sort_order.lower() not in ["asc", "desc"]:
            raise HTTPException(
                status_code=400,
                detail="sort_order must be 'asc' or 'desc'"
            )
        
        # Validate side filter
        if side and side.upper() not in ["BUY", "SELL"]:
            raise HTTPException(
                status_code=400,
                detail="side must be 'BUY' or 'SELL'"
            )
        
        # Build base query with joins
        query = session.query(Trade).filter(Trade.account_id == account_id)
        
        # Apply filters
        if symbol:
            query = query.filter(Trade.symbol == symbol.upper())
        
        if side:
            trade_side = TradeSide.BUY if side.upper() == "BUY" else TradeSide.SELL
            query = query.filter(Trade.side == trade_side)
        
        # Date range filter
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            query = query.filter(Trade.executed_at >= start_datetime)
        
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.filter(Trade.executed_at <= end_datetime)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply sorting
        sort_field = getattr(Trade, sort_by, None)
        if sort_field is None:
            # Fallback to executed_at if field not found
            sort_field = Trade.executed_at
        
        if sort_order.lower() == "desc":
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())
        
        # Apply pagination
        trades = query.offset(offset).limit(limit).all()
        
        # Format response
        trades_list = []
        for trade in trades:
            # Get strategy name if available
            strategy_name = None
            if trade.strategy_id:
                strategy = session.query(Strategy).filter(Strategy.id == trade.strategy_id).first()
                if strategy:
                    strategy_name = strategy.name
            
            # Calculate realized P&L from closed position
            # For SELL trades, we can calculate realized P&L by matching with the related position
            realized_pnl = None
            realized_pnl_pct = None
            
            # If trade has a position relationship, use that
            if trade.position and trade.position.status == PositionStatus.CLOSED:
                # Position is closed, use its final P&L as realized P&L for the closing trade
                if trade.side == TradeSide.SELL:
                    realized_pnl = trade.position.unrealized_pnl
                    realized_pnl_pct = trade.position.unrealized_pnl_pct
            elif trade.executed_at and trade.side == TradeSide.SELL:
                # For SELL trades without direct position link, try to find the closed position
                # that was closed around the time of this trade
                # Match by symbol, account, and closed_at within a reasonable window (e.g., same day)
                trade_date = trade.executed_at.date() if trade.executed_at else None
                if trade_date:
                    closed_position = session.query(Position).filter(
                        and_(
                            Position.account_id == account_id,
                            Position.symbol == trade.symbol,
                            Position.status == PositionStatus.CLOSED,
                            func.date(Position.closed_at) == trade_date
                        )
                    ).order_by(Position.closed_at.desc()).first()
                    
                    if closed_position:
                        # For SELL trades, realized P&L is the difference between sell price and avg buy price
                        # But we'll use the position's final P&L which should be more accurate
                        realized_pnl = closed_position.unrealized_pnl
                        realized_pnl_pct = closed_position.unrealized_pnl_pct
            
            trade_dict = {
                "id": trade.id,
                "symbol": trade.symbol,
                "side": trade.side.value if trade.side else None,
                "quantity": trade.quantity,
                "price": trade.price,
                "order_type": trade.order_type,
                "status": trade.status.value if trade.status else None,
                "executed_at": trade.executed_at.isoformat() if trade.executed_at else None,
                "timestamp": trade.timestamp.isoformat() if trade.timestamp else None,
                "realized_pnl": realized_pnl,
                "realized_pnl_pct": realized_pnl_pct,
                "strategy_id": trade.strategy_id,
                "strategy_name": strategy_name,
                "confidence_score": trade.confidence_score,
                "filled_quantity": trade.filled_quantity,
                "average_fill_price": trade.average_fill_price,
                "commission": trade.commission,
                "is_day_trade": trade.is_day_trade
            }
            trades_list.append(trade_dict)
        
        # Calculate has_more
        has_more = (offset + limit) < total_count
        
        return {
            "trades": trades_list,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": has_more
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trades: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving trades: {str(e)}"
        )
    finally:
        session.close()

@router.post("/execute")
async def execute_trade(
    trade_request: Dict[str, Any],
    risk_manager: RiskManager = Depends(lambda: get_risk_manager())
):
    """
    Execute a trade with risk management validation
    
    Required fields:
    - account_id: Account ID
    - symbol: Stock symbol
    - side: "BUY" or "SELL"
    - quantity: Number of shares (optional if confidence_score provided)
    - price_per_share: Price per share (required)
    - confidence_score: Optional confidence score (0.0-1.0) for position sizing
    
    Optional fields:
    - strategy_id: Strategy ID that generated this trade
    - will_create_day_trade: Whether this will create a day trade
    """
    try:
        # Extract request parameters
        account_id = trade_request.get("account_id")
        symbol = trade_request.get("symbol")
        side_str = trade_request.get("side", "BUY").upper()
        quantity = trade_request.get("quantity")
        price_per_share = trade_request.get("price_per_share")
        confidence_score = trade_request.get("confidence_score")
        strategy_id = trade_request.get("strategy_id")
        will_create_day_trade = trade_request.get("will_create_day_trade", False)
        
        # Validate required fields
        if not account_id:
            raise HTTPException(status_code=400, detail="account_id is required")
        if not symbol:
            raise HTTPException(status_code=400, detail="symbol is required")
        if not price_per_share:
            raise HTTPException(status_code=400, detail="price_per_share is required")
        if side_str not in ["BUY", "SELL"]:
            raise HTTPException(status_code=400, detail="side must be 'BUY' or 'SELL'")
        
        # Convert side to enum
        trade_side = TradeSide.BUY if side_str == "BUY" else TradeSide.SELL
        
        # 1. Pre-trade validation with risk management
        logger.info(f"Validating trade: {side_str} {quantity or 'auto'} {symbol} @ ${price_per_share:.2f}")
        
        validation = await risk_manager.validate_trade(
            account_id=account_id,
            symbol=symbol,
            side=side_str,
            quantity=quantity,
            price_per_share=price_per_share,
            confidence_score=confidence_score,
            will_create_day_trade=will_create_day_trade
        )
        
        if not validation.can_proceed:
            logger.warning(
                f"Trade rejected: {side_str} {quantity or 'auto'} {symbol} - {validation.compliance_check.message}"
            )
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Trade rejected by risk management",
                    "reason": validation.compliance_check.result.value,
                    "message": validation.compliance_check.message,
                    "compliance_details": validation.compliance_check.details
                }
            )
        
        # 2. Use position size from validation if calculated
        if validation.position_size and validation.position_size.size_shares > 0:
            quantity = validation.position_size.size_shares
            logger.info(
                f"Using calculated position size: {quantity} shares "
                f"({validation.position_size.confidence_level.value} confidence)"
            )
        
        if not quantity or quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="Quantity must be specified or confidence_score provided for auto-sizing"
            )
        
        # 3. Get IBKR manager and client
        manager = get_ibkr_manager()
        if not manager or not manager.is_connected:
            raise HTTPException(
                status_code=503,
                detail="IBKR not connected. Please connect first using /api/trading/ibkr/connect"
            )
        
        client = await manager.get_client()
        
        # 4. Create contract and place order
        contract = client.create_contract(symbol)
        ibkr_side = OrderSide.BUY if trade_side == TradeSide.BUY else OrderSide.SELL
        
        # For now, use market orders (can be enhanced to support limit orders)
        broker_order = await client.place_market_order(contract, ibkr_side, quantity)
        
        logger.info(
            f"Order placed: {side_str} {quantity} {symbol} @ market "
            f"(order_id: {broker_order.order_id})"
        )
        
        # 5. Record trade in database
        session = SessionLocal()
        try:
            # Get account (verify it exists)
            account = session.query(Account).filter(Account.id == account_id).first()
            if not account:
                raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
            
            # Create trade record
            trade = Trade(
                account_id=account_id,
                strategy_id=strategy_id,
                symbol=symbol,
                side=trade_side,
                quantity=quantity,
                price=price_per_share,
                order_type="market",
                status=OrderStatus.SUBMITTED,
                filled_quantity=0,
                confidence_score=confidence_score
            )
            session.add(trade)
            session.flush()  # Get trade ID
            
            # Record settlement for this trade
            trade_amount = quantity * price_per_share
            settlement_amount = -trade_amount if trade_side == TradeSide.BUY else trade_amount
            risk_manager.compliance.record_settlement(
                account_id=account_id,
                trade_id=trade.id,
                trade_date=datetime.now(),
                amount=settlement_amount
            )
            
            # Calculate and store settlement date
            trade.settlement_date = risk_manager.compliance.calculate_settlement_date(datetime.now())
            
            # Increment trade frequency
            risk_manager.compliance.increment_trade_frequency(account_id, datetime.now())
            
            # Check for day trade (for SELL orders)
            if trade_side == TradeSide.SELL:
                day_trade = risk_manager.compliance.detect_day_trade(
                    account_id=account_id,
                    symbol=symbol,
                    side=trade_side,
                    trade_date=datetime.now(),
                    trade_id=trade.id
                )
                if day_trade:
                    buy_trade_id, sell_trade_id = day_trade
                    risk_manager.compliance.record_day_trade(
                        account_id=account_id,
                        symbol=symbol,
                        buy_trade_id=buy_trade_id,
                        sell_trade_id=sell_trade_id,
                        trade_date=datetime.now()
                    )
                    trade.is_day_trade = True
                    logger.info(f"Day trade detected and recorded for {symbol}")
            
            session.commit()
            session.refresh(trade)
            
            logger.info(f"Trade recorded in database: trade_id={trade.id}")
            
            return {
                "status": "success",
                "message": "Trade executed successfully",
                "trade_id": trade.id,
                "broker_order_id": broker_order.order_id,
                "symbol": symbol,
                "side": side_str,
                "quantity": quantity,
                "price": price_per_share,
                "order_status": "submitted",
                "validation": {
                    "passed": True,
                    "compliance_result": validation.compliance_check.result.value,
                    "position_size": {
                        "size_shares": validation.position_size.size_shares if validation.position_size else quantity,
                        "size_usd": validation.position_size.size_usd if validation.position_size else quantity * price_per_share,
                        "confidence_level": validation.position_size.confidence_level.value if validation.position_size else None
                    } if validation.position_size else None
                }
            }
        except HTTPException:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Error recording trade: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error recording trade: {str(e)}")
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing trade: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Trade execution error: {str(e)}")


@router.post("/live-trade")
async def live_trade(trade_request: Dict[str, Any]):
    """
    Execute a live trade (legacy endpoint, redirects to /execute)
    
    Deprecated: Use /execute instead
    """
    logger.warning("/live-trade endpoint is deprecated, use /execute instead")
    return await execute_trade(trade_request)

@router.post("/backtest")
async def backtest(backtest_request: Dict[str, Any]):
    """Run a backtest"""
    logger.info(f"Backtest request: {backtest_request}")
    
    # TODO: Implement backtesting logic
    return {
        "status": "success",
        "message": "Backtesting not yet implemented",
        "results": {}
    }

@router.get("/status")
async def trading_status():
    """Get trading bot status"""
    manager = get_ibkr_manager()
    ibkr_connected = manager.is_connected if manager else False
    
    return {
        "status": "running",
        "ibkr_connected": ibkr_connected,
        "active_strategies": 0,
        "open_positions": 0,
        "last_trade": None
    }


class SignalRequest(BaseModel):
    """Signal generation request model"""
    symbol: str
    entry_threshold: Optional[float] = 0.005  # 0.5% default
    take_profit: Optional[float] = 0.20  # 20% default
    stop_loss: Optional[float] = 0.10  # 10% default
    quantity: Optional[int] = None


class SignalResponse(BaseModel):
    """Signal generation response model"""
    symbol: str
    signal_type: str  # BUY, SELL, HOLD
    price: float
    confidence: float  # 0.0 to 1.0
    entry_price: float
    take_profit_price: Optional[float] = None
    stop_loss_price: Optional[float] = None
    quantity: Optional[int] = None
    confluence_score: Optional[float] = None
    directional_bias: Optional[float] = None
    recommendation: str
    reasoning: Optional[Dict[str, Any]] = None


@router.post("/signal", response_model=SignalResponse)
async def generate_signal(signal_request: SignalRequest):
    """
    Generate a trading signal for a symbol based on confluence analysis
    
    Uses confluence calculator to analyze technical indicators, sentiment,
    and options flow to generate a trading recommendation.
    
    Request body:
    {
        "symbol": "AAPL",
        "entry_threshold": 0.005,  # Optional: 0.5% price movement threshold
        "take_profit": 0.20,       # Optional: 20% take profit target
        "stop_loss": 0.10,         # Optional: 10% stop loss
        "quantity": 10             # Optional: Suggested quantity
    }
    
    Returns:
    {
        "symbol": "AAPL",
        "signal_type": "BUY",
        "price": 150.25,
        "confidence": 0.75,
        "entry_price": 150.25,
        "take_profit_price": 180.30,
        "stop_loss_price": 135.23,
        "quantity": 10,
        "confluence_score": 0.82,
        "directional_bias": 0.65,
        "recommendation": "Strong buy signal based on technical and sentiment confluence",
        "reasoning": {...}
    }
    """
    try:
        symbol = signal_request.symbol.upper()
        
        # Initialize data provider and confluence calculator
        data_provider = DataProviderManager()
        calculator = ConfluenceCalculator(
            use_sentiment=True,
            use_options_flow=True
        )
        
        # Fetch current market data (1-minute bars, last 100 bars for indicators)
        logger.info(f"Fetching market data for {symbol} to generate signal")
        market_data = await data_provider.get_historical_data(
            symbol=symbol,
            timeframe="1m",
            lookback_bars=100
        )
        
        if market_data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No market data available for {symbol}. Symbol may be invalid or market closed."
            )
        
        # Get current price (last close price)
        current_price = float(market_data['close'].iloc[-1])
        
        # Calculate confluence score
        logger.info(f"Calculating confluence score for {symbol}")
        confluence = calculator.calculate_confluence(
            symbol=symbol,
            market_data=market_data,
            sentiment_hours=24
        )
        
        if confluence is None:
            raise HTTPException(
                status_code=500,
                detail=f"Could not calculate confluence for {symbol}. Insufficient data."
            )
        
        # Determine signal based on confluence and directional bias
        signal_type = SignalType.HOLD
        confidence = confluence.confidence
        
        # Use directional bias to determine signal direction
        # Positive bias = bullish (BUY), Negative bias = bearish (SELL)
        if confluence.directional_bias > 0.2 and confluence.confluence_score > 0.6:
            signal_type = SignalType.BUY
            confidence = min(confidence * (1 + confluence.directional_bias), 1.0)
        elif confluence.directional_bias < -0.2 and confluence.confluence_score > 0.6:
            signal_type = SignalType.SELL
            confidence = min(confidence * (1 + abs(confluence.directional_bias)), 1.0)
        else:
            signal_type = SignalType.HOLD
            confidence = confluence.confidence * 0.5  # Lower confidence for HOLD
        
        # Check if confluence meets minimum threshold for entry
        if signal_type != SignalType.HOLD and not confluence.meets_minimum_threshold:
            # Signal exists but doesn't meet minimum confluence
            signal_type = SignalType.HOLD
            confidence = confluence.confidence * 0.3
        
        # Calculate entry, take profit, and stop loss prices
        entry_price = current_price
        
        # Apply entry threshold if provided (wait for price movement)
        if signal_request.entry_threshold and signal_request.entry_threshold > 0:
            if signal_type == SignalType.BUY:
                entry_price = current_price * (1 + signal_request.entry_threshold)
            elif signal_type == SignalType.SELL:
                entry_price = current_price * (1 - signal_request.entry_threshold)
        
        # Calculate take profit and stop loss prices
        take_profit_price = None
        stop_loss_price = None
        
        if signal_type == SignalType.BUY:
            if signal_request.take_profit:
                take_profit_price = entry_price * (1 + signal_request.take_profit)
            if signal_request.stop_loss:
                stop_loss_price = entry_price * (1 - signal_request.stop_loss)
        elif signal_type == SignalType.SELL:
            if signal_request.take_profit:
                take_profit_price = entry_price * (1 - signal_request.take_profit)
            if signal_request.stop_loss:
                stop_loss_price = entry_price * (1 + signal_request.stop_loss)
        
        # Build recommendation message
        if signal_type == SignalType.BUY:
            recommendation = f"Buy signal for {symbol} with {confidence:.1%} confidence. "
            recommendation += f"Strong confluence (score: {confluence.confluence_score:.2f}, bias: {confluence.directional_bias:.2f}). "
            recommendation += f"Entry: ${entry_price:.2f}"
        elif signal_type == SignalType.SELL:
            recommendation = f"Sell signal for {symbol} with {confidence:.1%} confidence. "
            recommendation += f"Strong confluence (score: {confluence.confluence_score:.2f}, bias: {confluence.directional_bias:.2f}). "
            recommendation += f"Entry: ${entry_price:.2f}"
        else:
            recommendation = f"Hold signal for {symbol}. "
            recommendation += f"Confluence score {confluence.confluence_score:.2f} below threshold or mixed signals. "
            recommendation += "Wait for better entry opportunity."
        
        # Build reasoning breakdown
        reasoning = {
            "confluence_score": confluence.confluence_score,
            "confluence_level": confluence.confluence_level.value,
            "directional_bias": confluence.directional_bias,
            "meets_minimum_threshold": confluence.meets_minimum_threshold,
            "meets_high_threshold": confluence.meets_high_threshold,
            "components_used": confluence.components_used,
            "technical_score": confluence.breakdown.technical.overall_score if confluence.breakdown.technical else None,
            "sentiment_score": confluence.breakdown.sentiment.sentiment_score if confluence.breakdown.sentiment else None,
            "options_flow_score": confluence.breakdown.options_flow.overall_score if confluence.breakdown.options_flow else None,
            "current_price": current_price,
            "entry_threshold_applied": signal_request.entry_threshold if signal_request.entry_threshold else 0.0
        }
        
        # Record signal generation metric
        try:
            from ...utils.metrics_trading import record_signal_generated
            record_signal_generated(
                symbol=symbol,
                signal_type=signal_type.value,
                confidence=confidence
            )
        except Exception:
            pass  # Non-critical, skip if metrics not available
        
        logger.info(
            f"Signal generated for {symbol}: {signal_type.value} @ ${entry_price:.2f} "
            f"(confidence: {confidence:.1%}, confluence: {confluence.confluence_score:.2f})"
        )
        
        return SignalResponse(
            symbol=symbol,
            signal_type=signal_type.value,
            price=entry_price,
            confidence=confidence,
            entry_price=entry_price,
            take_profit_price=take_profit_price,
            stop_loss_price=stop_loss_price,
            quantity=signal_request.quantity,
            confluence_score=confluence.confluence_score,
            directional_bias=confluence.directional_bias,
            recommendation=recommendation,
            reasoning=reasoning
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating signal for {signal_request.symbol}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating signal: {str(e)}"
        )
