# Agent Task 1: Create Trade History API Endpoint

## Status: 🆕 **READY FOR ASSIGNMENT**

**Priority**: 🔴 CRITICAL  
**Estimated Time**: 2-3 hours  
**Dependencies**: None (can start immediately)

---

## Objective

Create the `GET /api/trading/trades` API endpoint that returns a paginated list of trades from the database. This endpoint will be used by the main dashboard to display recent trades and replace the static HTML table.

## Task Details

### Endpoint Specification

**Route**: `GET /api/trading/trades`  
**File**: `src/api/routes/trading.py`  
**Status**: ❌ Not Implemented

### Required Functionality

1. **Query Trades from Database**:
   - Query the `Trade` table filtered by `account_id`
   - Support filtering by `symbol` (optional query parameter)
   - Support filtering by `side` (BUY/SELL, optional query parameter)
   - Support filtering by date range (optional query parameters)

2. **Pagination**:
   - `limit` query parameter (default: 20, max: 100)
   - `offset` query parameter (default: 0)
   - Return total count for pagination UI

3. **Data Formatting**:
   - Include trade details: symbol, side, quantity, price, order_type, status
   - Include timestamps: `timestamp`, `executed_at`
   - Include P&L information if available from related Position
   - Calculate realized P&L for closed positions
   - Include strategy_id and strategy name if available

4. **Sorting**:
   - Default: Sort by `executed_at` DESC (most recent first)
   - Support optional `sort_by` and `sort_order` parameters

### Response Structure

```json
{
  "trades": [
    {
      "id": 123,
      "symbol": "AAPL",
      "side": "BUY",
      "quantity": 100,
      "price": 150.50,
      "order_type": "market",
      "status": "FILLED",
      "executed_at": "2024-12-19T14:30:00Z",
      "realized_pnl": null,
      "realized_pnl_pct": null,
      "strategy_id": 1,
      "strategy_name": "SMA Strategy",
      "confidence_score": 0.75
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

### Implementation Steps

1. **Add Endpoint to trading.py**:
   ```python
   @router.get("/trades")
   async def get_trades(
       account_id: int = Query(default=1),
       limit: int = Query(default=20, ge=1, le=100),
       offset: int = Query(default=0, ge=0),
       symbol: Optional[str] = Query(default=None),
       side: Optional[str] = Query(default=None),
       sort_by: str = Query(default="executed_at"),
       sort_order: str = Query(default="desc")
   ):
   ```

2. **Database Query Logic**:
   - Build query with filters
   - Join with Strategy table for strategy name
   - Join with Position table for P&L if position is closed
   - Apply sorting
   - Apply pagination with `limit()` and `offset()`
   - Get total count with separate count query

3. **Error Handling**:
   - Handle invalid query parameters
   - Handle database errors gracefully
   - Return appropriate HTTP status codes

4. **Testing Considerations**:
   - Test with various filter combinations
   - Test pagination boundaries
   - Test with empty results
   - Test error cases

### Reference Documentation

- **Implementation Guide**: `docs/DASHBOARD_REAL_DATA_INTEGRATION.md` (Step 2: Create Trade History API Endpoint)
- **Database Models**: `src/data/database/models.py` (Trade, Position, Strategy models)
- **Existing Endpoint Reference**: `src/api/routes/trading.py` (see `/portfolio/summary` for pattern)
- **Project TODO**: `docs/PROJECT_TODO.md` (UI Section, Task ui-4)

### Success Criteria

✅ Endpoint returns paginated trades  
✅ Supports filtering by symbol, side, date range  
✅ Returns proper JSON structure with metadata  
✅ Handles errors gracefully  
✅ Follows existing code patterns in trading.py  
✅ No linter errors  
✅ Documented with docstrings

---

## Related Tasks

- **Agent 4**: Will use this endpoint to update dashboard.js trade history section
- **Agent 3**: Portfolio Summary endpoint already completed (reference implementation)

## Notes

- Use the same database session pattern as `/portfolio/summary`
- Realized P&L calculation: For closed positions, use `Position.unrealized_pnl` as realized P&L (since it's closed)
- For open positions, `realized_pnl` should be `null`
- Consider adding indexes to Trade table if query performance is slow (symbol, executed_at)

---

**Ready to start?** Review the existing `/portfolio/summary` endpoint in `trading.py` to understand the code patterns, then implement the new endpoint following the same structure.

