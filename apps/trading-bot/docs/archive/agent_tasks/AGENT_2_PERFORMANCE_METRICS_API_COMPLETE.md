# Agent Task 2: Create Performance Metrics API Endpoint

## Status: 🆕 **READY FOR ASSIGNMENT**

**Priority**: 🔴 CRITICAL  
**Estimated Time**: 2-3 hours  
**Dependencies**: None (can start immediately)

---

## Objective

Create the `GET /api/trading/performance` API endpoint that calculates and returns comprehensive performance metrics including win rate, total P&L, trade statistics, and performance breakdowns. This will be used by the dashboard for displaying win rate and other performance statistics.

## Task Details

### Endpoint Specification

**Route**: `GET /api/trading/performance`  
**File**: `src/api/routes/trading.py`  
**Status**: ❌ Not Implemented

### Required Functionality

1. **Calculate Win Rate**:
   - Query closed positions from Position table
   - Count winning trades (unrealized_pnl > 0) vs losing trades
   - Calculate win rate percentage
   - Include breakdown by strategy if available

2. **Trade Statistics**:
   - Total trades count
   - Total winning trades
   - Total losing trades
   - Average win amount
   - Average loss amount
   - Largest win
   - Largest loss
   - Win/loss ratio

3. **P&L Metrics**:
   - Total realized P&L (sum of closed positions' unrealized_pnl)
   - Total unrealized P&L (sum of open positions' unrealized_pnl)
   - Average P&L per trade
   - Profit factor (total wins / total losses)

4. **Time-Based Breakdowns** (Optional - can be simplified initially):
   - Daily P&L for last N days
   - Weekly P&L
   - Monthly P&L
   - Best/worst trading days

5. **Strategy Performance** (Optional - can be simplified initially):
   - Performance per strategy
   - Win rate per strategy
   - P&L per strategy

### Response Structure

```json
{
  "win_rate": 0.685,
  "total_trades": 50,
  "winning_trades": 34,
  "losing_trades": 16,
  "total_realized_pnl": 5420.50,
  "total_unrealized_pnl": 1250.00,
  "average_win": 250.75,
  "average_loss": -180.25,
  "largest_win": 850.00,
  "largest_loss": -420.50,
  "profit_factor": 1.39,
  "win_loss_ratio": 2.14,
  "average_pnl_per_trade": 108.41,
  "date_range": {
    "first_trade": "2024-11-01T09:30:00Z",
    "last_trade": "2024-12-19T15:45:00Z"
  }
}
```

### Implementation Steps

1. **Add Endpoint to trading.py**:
   ```python
   @router.get("/performance")
   async def get_performance_metrics(
       account_id: int = Query(default=1),
       strategy_id: Optional[int] = Query(default=None)
   ):
   ```

2. **Query Closed Positions**:
   - Filter by account_id
   - Filter by PositionStatus.CLOSED
   - Join with Trade table to get strategy information if needed

3. **Query Open Positions** (for unrealized P&L):
   - Filter by account_id
   - Filter by PositionStatus.OPEN
   - Sum unrealized_pnl

4. **Calculate Metrics**:
   - Separate winning vs losing positions
   - Calculate averages, totals, min/max
   - Calculate profit factor and win/loss ratio
   - Handle edge cases (no trades, all wins, all losses)

5. **Error Handling**:
   - Handle empty result sets
   - Handle division by zero
   - Return appropriate defaults

### Reference Documentation

- **Implementation Guide**: `docs/DASHBOARD_REAL_DATA_INTEGRATION.md` (Step 3: Create Performance Metrics API Endpoint)
- **Database Models**: `src/data/database/models.py` (Position, Trade models)
- **Existing Endpoint Reference**: `src/api/routes/trading.py` (see `/portfolio/summary` for pattern)
- **Project TODO**: `docs/PROJECT_TODO.md` (UI Section, Task ui-5)

### Success Criteria

✅ Endpoint returns comprehensive performance metrics  
✅ Win rate calculated correctly from closed positions  
✅ All statistical calculations are accurate  
✅ Handles edge cases (no trades, empty data)  
✅ Follows existing code patterns in trading.py  
✅ No linter errors  
✅ Documented with docstrings

---

## Related Tasks

- **Agent 4**: Will use win rate data from this endpoint
- **Agent 7**: Will use this data for trade distribution chart
- **Agent 3**: Portfolio Summary endpoint uses similar data sources

## Notes

- **Win Rate Calculation**: Use closed positions where `unrealized_pnl > 0` = win, `unrealized_pnl <= 0` = loss
- **Realized vs Unrealized**: For closed positions, `unrealized_pnl` becomes realized P&L
- **Profit Factor**: Total wins / abs(total losses). If no losses, return `null` or a high number.
- **Division by Zero**: Always check before dividing (e.g., win rate when no trades)
- **Performance**: Consider adding database indexes if queries are slow

---

**Ready to start?** Review the existing `/portfolio/summary` endpoint in `trading.py` to understand the code patterns and how it queries closed positions, then implement the new endpoint with expanded calculations.

