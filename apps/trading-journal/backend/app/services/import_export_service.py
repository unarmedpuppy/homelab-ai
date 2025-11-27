"""
Import/Export service for trades.
"""

import csv
import io
from datetime import datetime
from typing import List, Optional, BinaryIO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.trade import Trade
from app.schemas.trade import TradeCreate, TradeType, TradeSide, TradeStatus, OptionType
from app.services.trade_service import bulk_create_trades

async def export_trades_to_csv(db: AsyncSession) -> str:
    """
    Export all trades to CSV format.
    
    Returns:
        CSV string content
    """
    # Query all trades
    query = select(Trade).order_by(Trade.entry_time.desc())
    result = await db.execute(query)
    trades = result.scalars().all()
    
    # Define CSV fields
    fieldnames = [
        "ticker", "trade_type", "side", "status",
        "entry_date", "entry_time", "entry_price", "entry_quantity", "entry_commission",
        "exit_date", "exit_time", "exit_price", "exit_quantity", "exit_commission",
        "net_pnl", "net_roi", "notes", "tags", "playbook",
        # Options specific
        "strike_price", "expiration_date", "option_type",
        "delta", "gamma", "theta", "vega", "rho", "implied_volatility",
        # Crypto specific
        "crypto_exchange", "crypto_pair",
        # Prediction market specific
        "prediction_market_platform", "prediction_outcome"
    ]
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for trade in trades:
        row = {
            "ticker": trade.ticker,
            "trade_type": trade.trade_type,
            "side": trade.side,
            "status": trade.status,
            "entry_date": trade.entry_time.date().isoformat() if trade.entry_time else "",
            "entry_time": trade.entry_time.time().isoformat() if trade.entry_time else "",
            "entry_price": trade.entry_price,
            "entry_quantity": trade.entry_quantity,
            "entry_commission": trade.entry_commission,
            "exit_date": trade.exit_time.date().isoformat() if trade.exit_time else "",
            "exit_time": trade.exit_time.time().isoformat() if trade.exit_time else "",
            "exit_price": trade.exit_price,
            "exit_quantity": trade.exit_quantity,
            "exit_commission": trade.exit_commission,
            "net_pnl": trade.net_pnl,
            "net_roi": trade.net_roi,
            "notes": trade.notes,
            "tags": ",".join(trade.tags) if trade.tags else "",
            "playbook": trade.playbook_id, # TODO: Should probably export name, but ID is safer for re-import if we map it
            # Options
            "strike_price": trade.strike_price,
            "expiration_date": trade.expiration_date.isoformat() if trade.expiration_date else "",
            "option_type": trade.option_type,
            "delta": trade.delta,
            "gamma": trade.gamma,
            "theta": trade.theta,
            "vega": trade.vega,
            "rho": trade.rho,
            "implied_volatility": trade.implied_volatility,
            # Crypto
            "crypto_exchange": trade.crypto_exchange,
            "crypto_pair": trade.crypto_pair,
            # Prediction market
            "prediction_market_platform": trade.prediction_market_platform,
            "prediction_outcome": trade.prediction_outcome,
        }
        writer.writerow(row)
        
    return output.getvalue()

async def import_trades_from_csv(db: AsyncSession, file_content: bytes) -> dict:
    """
    Import trades from CSV content.
    
    Returns:
        Dictionary with success count and errors
    """
    content_str = file_content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(content_str))
    
    trades_to_create = []
    errors = []
    row_index = 0
    
    for row in reader:
        row_index += 1
        try:
            # Parse entry datetime
            entry_dt = None
            if row.get("entry_date") and row.get("entry_time"):
                entry_dt = datetime.fromisoformat(f"{row['entry_date']}T{row['entry_time']}")
            elif row.get("entry_date"):
                entry_dt = datetime.fromisoformat(row['entry_date'])
                
            # Parse exit datetime
            exit_dt = None
            if row.get("exit_date") and row.get("exit_time"):
                exit_dt = datetime.fromisoformat(f"{row['exit_date']}T{row['exit_time']}")
            elif row.get("exit_date"):
                exit_dt = datetime.fromisoformat(row['exit_date'])
            
            # Parse tags
            tags = []
            if row.get("tags"):
                tags = [t.strip() for t in row["tags"].split(",")]
                
            # Create trade data
            trade_data = {
                "ticker": row["ticker"],
                "trade_type": row["trade_type"],
                "side": row["side"],
                "status": row.get("status", "open"),
                "entry_price": row["entry_price"],
                "entry_quantity": row["entry_quantity"],
                "entry_time": entry_dt,
                "entry_commission": row.get("entry_commission") or 0,
                "notes": row.get("notes"),
                "tags": tags,
            }
            
            # Add optional fields if present
            if exit_dt:
                trade_data["exit_time"] = exit_dt
            if row.get("exit_price"):
                trade_data["exit_price"] = row["exit_price"]
            if row.get("exit_quantity"):
                trade_data["exit_quantity"] = row["exit_quantity"]
            if row.get("exit_commission"):
                trade_data["exit_commission"] = row["exit_commission"]
                
            # Options fields
            if row.get("strike_price"):
                trade_data["strike_price"] = row["strike_price"]
            if row.get("expiration_date"):
                trade_data["expiration_date"] = datetime.fromisoformat(row["expiration_date"]).date()
            if row.get("option_type"):
                trade_data["option_type"] = row["option_type"]
                
            # Validate with schema
            trade_create = TradeCreate(**trade_data)
            trades_to_create.append(trade_create)
            
        except Exception as e:
            errors.append(f"Row {row_index}: {str(e)}")
            
    if trades_to_create:
        await bulk_create_trades(db, trades_to_create)
        
    return {
        "success_count": len(trades_to_create),
        "error_count": len(errors),
        "errors": errors
    }

