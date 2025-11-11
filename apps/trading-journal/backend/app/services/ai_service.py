"""
AI Agent Helper service.

Provides functionality for parsing natural language trade descriptions,
batch trade creation, and trade suggestions based on historical data.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import re

from app.models.trade import Trade
from app.schemas.trade import TradeCreate, TradeType, TradeStatus, TradeSide
from app.schemas.ai import ParseTradeResponse, TradeSuggestion
from app.services.trade_service import bulk_create_trades


async def parse_trade_from_description(
    description: str,
    raw_data: Optional[Dict[str, Any]] = None,
) -> ParseTradeResponse:
    """
    Parse a trade from natural language description.
    
    This is a simplified rule-based parser. In a production system, this would
    likely use an LLM API for more sophisticated parsing.
    
    Args:
        description: Natural language description of the trade
        raw_data: Optional structured data to supplement parsing
    
    Returns:
        ParseTradeResponse with parsed trade data and confidence score
    """
    # Start with raw_data if provided
    extracted = raw_data.copy() if raw_data else {}
    warnings = []
    missing_fields = []
    
    # Normalize description for parsing
    desc_lower = description.lower()
    
    # Extract ticker (look for uppercase letters, typically 1-5 chars)
    if "ticker" not in extracted:
        ticker_match = re.search(r'\b([A-Z]{1,5})\b', description)
        if ticker_match:
            extracted["ticker"] = ticker_match.group(1).upper()
    
    # Extract trade type
    if "trade_type" not in extracted:
        if any(word in desc_lower for word in ["option", "call", "put"]):
            extracted["trade_type"] = "OPTION"
        elif any(word in desc_lower for word in ["crypto", "bitcoin", "btc", "eth", "ethereum"]):
            extracted["trade_type"] = "CRYPTO_SPOT"
        elif any(word in desc_lower for word in ["stock", "equity", "share"]):
            extracted["trade_type"] = "STOCK"
        else:
            extracted["trade_type"] = "STOCK"  # Default
            warnings.append("Trade type not specified, defaulting to STOCK")
    
    # Extract side (LONG/SHORT)
    if "side" not in extracted:
        if any(word in desc_lower for word in ["short", "sold", "sell"]):
            extracted["side"] = "SHORT"
        elif any(word in desc_lower for word in ["long", "bought", "buy", "purchased"]):
            extracted["side"] = "LONG"
        else:
            extracted["side"] = "LONG"  # Default
            warnings.append("Side not specified, defaulting to LONG")
    
    # Extract prices (look for dollar amounts)
    price_pattern = r'\$?(\d+\.?\d*)\s*(?:per|@|at)?\s*(?:share|contract|unit)?'
    prices = re.findall(price_pattern, description, re.IGNORECASE)
    
    if "entry_price" not in extracted and prices:
        try:
            extracted["entry_price"] = Decimal(prices[0])
        except (ValueError, IndexError):
            pass
    
    if "exit_price" not in extracted and len(prices) > 1:
        try:
            extracted["exit_price"] = Decimal(prices[1])
        except (ValueError, IndexError):
            pass
    
    # Extract quantities
    qty_pattern = r'(\d+)\s*(?:shares?|contracts?|units?|qty|quantity)'
    quantities = re.findall(qty_pattern, desc_lower)
    
    if "entry_quantity" not in extracted and quantities:
        try:
            extracted["entry_quantity"] = Decimal(quantities[0])
        except (ValueError, IndexError):
            pass
    
    if "exit_quantity" not in extracted and len(quantities) > 1:
        try:
            extracted["exit_quantity"] = Decimal(quantities[1])
        except (ValueError, IndexError):
            pass
    
    # Extract dates (look for common date formats)
    date_patterns = [
        r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
        r'(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
        r'(\d{1,2}-\d{1,2}-\d{4})',  # MM-DD-YYYY
    ]
    
    dates = []
    for pattern in date_patterns:
        dates.extend(re.findall(pattern, description))
    
    if "entry_time" not in extracted and dates:
        try:
            # Try to parse first date as entry
            date_str = dates[0]
            if "-" in date_str and len(date_str) == 10:
                extracted["entry_time"] = datetime.strptime(date_str, "%Y-%m-%d")
            elif "/" in date_str:
                extracted["entry_time"] = datetime.strptime(date_str, "%m/%d/%Y")
        except (ValueError, IndexError):
            pass
    
    if "exit_time" not in extracted and len(dates) > 1:
        try:
            # Try to parse second date as exit
            date_str = dates[1]
            if "-" in date_str and len(date_str) == 10:
                extracted["exit_time"] = datetime.strptime(date_str, "%Y-%m-%d")
            elif "/" in date_str:
                extracted["exit_time"] = datetime.strptime(date_str, "%m/%d/%Y")
        except (ValueError, IndexError):
            pass
    
    # Extract status
    if "status" not in extracted:
        if any(word in desc_lower for word in ["closed", "exited", "sold", "covered"]):
            extracted["status"] = "closed"
        elif any(word in desc_lower for word in ["open", "holding", "active"]):
            extracted["status"] = "open"
        else:
            # Default based on whether exit_price is present
            if extracted.get("exit_price"):
                extracted["status"] = "closed"
            else:
                extracted["status"] = "open"
    
    # Extract playbook/strategy (look for common strategy names)
    playbook_keywords = ["breakout", "pullback", "reversal", "momentum", "swing", "scalp", "trend"]
    for keyword in playbook_keywords:
        if keyword in desc_lower:
            extracted["playbook"] = keyword.capitalize()
            break
    
    # Set defaults for required fields
    if "entry_time" not in extracted:
        extracted["entry_time"] = datetime.now()
        warnings.append("Entry time not found, using current time")
    
    # Calculate confidence based on extracted fields
    required_fields = ["ticker", "entry_price", "entry_quantity", "side", "trade_type"]
    extracted_fields = {k: v for k, v in extracted.items() if k in required_fields}
    confidence = len(extracted_fields) / len(required_fields)
    
    # Track missing required fields
    for field in required_fields:
        if field not in extracted:
            missing_fields.append(field)
    
    # Create TradeCreate object
    try:
        parsed_trade = TradeCreate(**extracted)
    except Exception as e:
        warnings.append(f"Error creating trade object: {str(e)}")
        # Create minimal trade with defaults
        parsed_trade = TradeCreate(
            ticker=extracted.get("ticker", "UNKNOWN"),
            entry_price=extracted.get("entry_price", Decimal("0")),
            entry_quantity=extracted.get("entry_quantity", Decimal("1")),
            side=extracted.get("side", "LONG"),
            trade_type=extracted.get("trade_type", "STOCK"),
            entry_time=extracted.get("entry_time", datetime.now()),
            status=extracted.get("status", "open"),
        )
        confidence = 0.3  # Low confidence if we had to use defaults
    
    return ParseTradeResponse(
        parsed_trade=parsed_trade,
        confidence=confidence,
        extracted_fields=extracted,
        missing_fields=missing_fields,
        warnings=warnings,
    )


async def batch_create_trades_from_descriptions(
    db: AsyncSession,
    trade_requests: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Batch create trades from descriptions or raw data.
    
    Args:
        db: Database session
        trade_requests: List of trade request dictionaries with 'description' and optional 'raw_data'
    
    Returns:
        Dictionary with created_trades, failed_trades, and summary statistics
    """
    created_trades = []
    failed_trades = []
    
    # Parse all trades first
    parsed_trades = []
    for i, trade_req in enumerate(trade_requests):
        try:
            parse_result = await parse_trade_from_description(
                description=trade_req.get("description", ""),
                raw_data=trade_req.get("raw_data"),
            )
            
            if parse_result.confidence < 0.5:
                failed_trades.append({
                    "index": i,
                    "description": trade_req.get("description", ""),
                    "error": "Low confidence parsing (< 0.5)",
                    "warnings": parse_result.warnings,
                    "missing_fields": parse_result.missing_fields,
                })
            else:
                parsed_trades.append(parse_result.parsed_trade)
        except Exception as e:
            failed_trades.append({
                "index": i,
                "description": trade_req.get("description", ""),
                "error": str(e),
            })
    
    # Bulk create successfully parsed trades
    if parsed_trades:
        try:
            created = await bulk_create_trades(db, parsed_trades)
            created_trades = created
        except Exception as e:
            # If bulk create fails, add all to failed
            for trade in parsed_trades:
                failed_trades.append({
                    "trade": trade.model_dump(),
                    "error": f"Bulk create failed: {str(e)}",
                })
            created_trades = []
    
    return {
        "created_trades": created_trades,
        "failed_trades": failed_trades,
        "total_requested": len(trade_requests),
        "total_created": len(created_trades),
        "total_failed": len(failed_trades),
    }


async def get_trade_suggestions(
    db: AsyncSession,
    ticker: str,
) -> TradeSuggestion:
    """
    Get trade suggestions based on historical trades for a ticker.
    
    Args:
        db: Database session
        ticker: Ticker symbol to analyze
    
    Returns:
        TradeSuggestion with suggested parameters and historical insights
    """
    # Query historical trades for this ticker
    query = (
        select(Trade)
        .where(Trade.ticker == ticker.upper())
        .where(Trade.status == "closed")
        .order_by(desc(Trade.exit_time))
    )
    
    result = await db.execute(query)
    trades = result.scalars().all()
    
    if not trades:
        return TradeSuggestion(
            ticker=ticker.upper(),
            notes=["No historical trades found for this ticker"],
        )
    
    # Calculate statistics
    total_trades = len(trades)
    last_trade = trades[0]
    last_trade_date = last_trade.exit_time.date() if last_trade.exit_time else None
    
    # Calculate average entry price (from recent trades)
    recent_trades = trades[:10]  # Last 10 trades
    entry_prices = [t.entry_price for t in recent_trades if t.entry_price]
    suggested_entry_price = None
    if entry_prices:
        suggested_entry_price = sum(entry_prices) / Decimal(len(entry_prices))
    
    # Calculate average quantity
    quantities = [t.entry_quantity for t in recent_trades if t.entry_quantity]
    suggested_quantity = None
    if quantities:
        suggested_quantity = sum(quantities) / Decimal(len(quantities))
    
    # Find most common trade type
    trade_types = [t.trade_type for t in trades if t.trade_type]
    suggested_trade_type = None
    if trade_types:
        suggested_trade_type = max(set(trade_types), key=trade_types.count)
    
    # Find most common side
    sides = [t.side for t in trades if t.side]
    suggested_side = None
    if sides:
        suggested_side = max(set(sides), key=sides.count)
    
    # Find most common playbook
    playbooks = [t.playbook for t in trades if t.playbook]
    suggested_playbook = None
    if playbooks:
        # Filter out None values
        playbooks_filtered = [p for p in playbooks if p]
        if playbooks_filtered:
            suggested_playbook = max(set(playbooks_filtered), key=playbooks_filtered.count)
    
    # Calculate win rate
    winners = sum(1 for t in trades if t.calculate_net_pnl() and t.calculate_net_pnl() > 0)
    avg_win_rate = None
    if total_trades > 0:
        avg_win_rate = (Decimal(winners) / Decimal(total_trades)) * Decimal("100")
    
    # Calculate average net P&L
    net_pnls = [t.calculate_net_pnl() for t in trades if t.calculate_net_pnl() is not None]
    avg_net_pnl = None
    if net_pnls:
        avg_net_pnl = sum(net_pnls) / Decimal(len(net_pnls))
    
    # Generate notes
    notes = []
    if avg_win_rate:
        if avg_win_rate >= Decimal("60"):
            notes.append(f"Strong win rate: {avg_win_rate:.1f}%")
        elif avg_win_rate < Decimal("40"):
            notes.append(f"Low win rate: {avg_win_rate:.1f}% - consider reviewing strategy")
    
    if avg_net_pnl:
        if avg_net_pnl > 0:
            notes.append(f"Historically profitable: ${avg_net_pnl:.2f} average P&L")
        else:
            notes.append(f"Historically unprofitable: ${avg_net_pnl:.2f} average P&L")
    
    if suggested_playbook:
        notes.append(f"Most common strategy: {suggested_playbook}")
    
    if total_trades >= 10:
        notes.append(f"Good sample size: {total_trades} historical trades")
    elif total_trades < 5:
        notes.append(f"Limited sample size: {total_trades} trades - suggestions may be less reliable")
    
    return TradeSuggestion(
        ticker=ticker.upper(),
        suggested_entry_price=suggested_entry_price,
        suggested_quantity=suggested_quantity,
        suggested_trade_type=suggested_trade_type,
        suggested_side=suggested_side,
        suggested_playbook=suggested_playbook,
        avg_win_rate=avg_win_rate,
        avg_net_pnl=avg_net_pnl,
        total_trades=total_trades,
        last_trade_date=last_trade_date,
        notes=notes,
    )

