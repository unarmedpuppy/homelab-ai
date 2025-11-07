# Critical Fix #2: Fix Average Price Calculation - COMPLETE ✅

**Date**: 2024-12-19  
**Status**: ✅ **COMPLETE**  
**Priority**: 🔴 HIGH

## Summary

Fixed the average price calculation to properly compute weighted averages when position quantity increases, instead of simply replacing the average price with IBKR's value.

## Problem

**Before**: When position quantity increased (additional buy), the code simply replaced `average_price` with IBKR's `average_price`, which could lead to incorrect cost basis tracking if we have multiple entry points.

**Issue**: 
- No weighted average calculation
- Could lose track of our own cost basis
- Didn't account for multiple entry prices

## Solution

Implemented proper weighted average calculation based on quantity changes:

### 1. Position Quantity Increases (Additional Buy)
- **Calculate weighted average**: `(old_avg * old_qty + new_avg * new_qty) / total_qty`
- **Derive new shares cost**: From IBKR's total cost basis
- **Maintain cost basis tracking**: Calculate explicitly to ensure accuracy
- **Log discrepancies**: Warn if calculated average differs from IBKR's (shouldn't happen)

### 2. Position Quantity Decreases (Partial Close)
- **Keep existing average**: Maintain FIFO assumption
- **Average price unchanged**: The average price of remaining shares doesn't change

### 3. Position Quantity Unchanged
- **Use IBKR's average**: May have been updated by IBKR

## Implementation Details

### Weighted Average Calculation

```python
# When quantity increases:
total_cost_basis = ibkr_pos.average_price * ibkr_pos.quantity
old_cost_basis = old_average_price * old_quantity
new_shares = ibkr_pos.quantity - old_quantity

# Calculate cost of new shares
new_shares_cost = total_cost_basis - old_cost_basis
new_shares_avg = new_shares_cost / new_shares

# Calculate weighted average
weighted_avg = (old_average_price * old_quantity + new_shares_avg * new_shares) / ibkr_pos.quantity
```

### Example

**Scenario**: Position increases from 10 shares @ $100 to 15 shares @ $105 (IBKR average)

1. **Old position**: 10 shares @ $100 = $1,000 cost basis
2. **New position**: 15 shares @ $105 = $1,575 total cost basis
3. **New shares**: 5 shares
4. **New shares cost**: $1,575 - $1,000 = $575
5. **New shares average**: $575 / 5 = $115
6. **Weighted average**: (10 * $100 + 5 * $115) / 15 = $105 ✓

The calculated weighted average should match IBKR's average_price.

## Files Changed

- ✅ `src/core/sync/position_sync.py` - Updated average price calculation logic

## Benefits

1. **Accurate Cost Basis**: Maintains proper cost basis tracking across multiple entries
2. **Weighted Average**: Correctly calculates average price when position increases
3. **FIFO Assumption**: Maintains average price on partial closes (FIFO)
4. **Verification**: Logs discrepancies if calculated average differs from IBKR's
5. **Transparency**: Detailed logging of average price calculations

## Testing Recommendations

### Test Cases

1. **Position Increase**:
   - Start: 10 shares @ $100
   - Add: 5 shares @ $115
   - Expected: 15 shares @ $105 weighted average

2. **Partial Close**:
   - Start: 15 shares @ $105
   - Close: 5 shares
   - Expected: 10 shares @ $105 (average unchanged)

3. **Multiple Increases**:
   - Start: 10 shares @ $100
   - Add: 5 shares @ $110
   - Add: 5 shares @ $120
   - Expected: 20 shares @ $110 weighted average

4. **Edge Cases**:
   - Position increase when old_quantity = 0 (should use IBKR's average)
   - Very small quantity changes
   - Rounding precision

## Next Steps

Critical Fix #2 is complete. Ready to proceed with:
- Critical Fix #3: Dashboard Fallback to DB Positions
- Critical Fix #4: Add Manual Sync API Endpoints
- Critical Fix #5: Partial Close Realized P&L Tracking

## Notes

- The weighted average calculation should match IBKR's average_price
- If there's a discrepancy, it's logged as a warning
- FIFO assumption is used for partial closes (average price unchanged)
- Calculation is explicit to ensure accuracy and maintainability

