# Critical Fix #5: Partial Close Realized P&L Tracking - COMPLETE ✅

**Date**: 2024-12-19  
**Status**: ✅ **COMPLETE**  
**Priority**: 🔴 HIGH

## Summary

Implemented tracking of realized P&L for partial position closes by creating a `PositionClose` model that records each partial and full close transaction with detailed P&L information.

## Problem

**Before**: When a position partially closed (quantity decreased but position remained open), the realized P&L for the closed portion was not tracked.

**Issues**:
- No record of partial closes
- Could not track realized P&L for scaled exits
- Inaccurate total P&L tracking
- No history of position close transactions

## Solution

### 1. Created PositionClose Model

**File**: `src/data/database/models.py`

**New Model**: `PositionClose`
- Tracks each partial and full close transaction
- Stores: quantity closed, entry price, exit price, realized P&L, close timestamp
- Links to Position via foreign key
- Indexed for efficient queries

**Fields**:
- `position_id` - Foreign key to Position
- `account_id` - Account ID (for filtering)
- `symbol` - Symbol (for filtering)
- `quantity_closed` - Quantity closed in this transaction
- `entry_price` - Average entry price at time of close
- `exit_price` - Exit price for this close
- `realized_pnl` - Realized P&L for this close
- `realized_pnl_pct` - Realized P&L percentage
- `closed_at` - Timestamp of close
- `is_full_close` - Boolean flag for full position close

### 2. Updated Position Sync Logic

**File**: `src/core/sync/position_sync.py`

**Changes**:
- Create `PositionClose` record for each partial close
- Calculate realized P&L: `(exit_price - entry_price) * quantity_closed`
- Update position's cumulative `realized_pnl` (sum of all closes)
- Create `PositionClose` record for full closes
- Track both partial and full closes in database

### 3. Database Migration

**File**: `migrations/versions/005_add_position_close_model.py`

**Migration**:
- Creates `position_closes` table
- Adds foreign keys to `positions` and `accounts`
- Creates indexes for efficient queries
- Includes composite index for account/symbol queries

## Implementation Details

### Partial Close Tracking

```python
# When quantity decreases (partial close)
if ibkr_pos.quantity < old_quantity:
    closed_quantity = old_quantity - ibkr_pos.quantity
    exit_price = ibkr_pos.market_price or old_average_price
    
    # Calculate realized P&L
    partial_realized_pnl = (exit_price - old_average_price) * closed_quantity
    partial_realized_pnl_pct = ((exit_price / old_average_price) - 1) * 100
    
    # Create PositionClose record
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
    
    # Update cumulative realized P&L
    total_realized_pnl = sum(all_closes.realized_pnl)
    db_pos.realized_pnl = total_realized_pnl
```

### Full Close Tracking

```python
# When position fully closes
if ibkr_pos.quantity == 0:
    realized_pnl = (exit_price - db_pos.average_price) * old_quantity
    
    # Create PositionClose record
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
    
    # Update cumulative realized P&L (includes all partial closes)
    total_realized_pnl = sum(partial_closes.realized_pnl) + realized_pnl
    db_pos.realized_pnl = total_realized_pnl
```

## Database Schema

### PositionClose Table

```sql
CREATE TABLE position_closes (
    id INTEGER PRIMARY KEY,
    position_id INTEGER NOT NULL,
    account_id INTEGER NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    quantity_closed INTEGER NOT NULL,
    entry_price FLOAT NOT NULL,
    exit_price FLOAT NOT NULL,
    realized_pnl FLOAT NOT NULL,
    realized_pnl_pct FLOAT NOT NULL,
    closed_at DATETIME NOT NULL,
    is_full_close BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (position_id) REFERENCES positions(id),
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

CREATE INDEX ix_position_closes_position_id ON position_closes(position_id);
CREATE INDEX ix_position_closes_account_id ON position_closes(account_id);
CREATE INDEX ix_position_closes_symbol ON position_closes(symbol);
CREATE INDEX ix_position_closes_closed_at ON position_closes(closed_at);
CREATE INDEX ix_position_closes_is_full_close ON position_closes(is_full_close);
CREATE INDEX idx_position_closes_account_symbol ON position_closes(account_id, symbol);
```

## Features

### 1. Partial Close Tracking
- ✅ Records each partial close transaction
- ✅ Calculates realized P&L for closed portion
- ✅ Maintains average price for remaining shares (FIFO)
- ✅ Updates cumulative realized P&L

### 2. Full Close Tracking
- ✅ Records full close transaction
- ✅ Includes all partial closes in total realized P&L
- ✅ Marks as `is_full_close = True`

### 3. Historical Tracking
- ✅ Complete history of all closes (partial and full)
- ✅ Query closes by position, account, symbol, date
- ✅ Calculate total realized P&L from all closes

## Files Changed

- ✅ `src/data/database/models.py` - Added PositionClose model
- ✅ `src/core/sync/position_sync.py` - Updated to create PositionClose records
- ✅ `migrations/versions/005_add_position_close_model.py` - Created migration

## Benefits

1. **Accurate P&L Tracking**: Track realized P&L for every close transaction
2. **Partial Close History**: Complete history of scaled exits
3. **Cumulative P&L**: Position.realized_pnl is sum of all closes
4. **Query Flexibility**: Query closes by position, account, symbol, date
5. **Audit Trail**: Complete record of all position close transactions

## Usage Examples

### Query All Closes for a Position

```python
from src.data.database.models import PositionClose

# Get all closes for a position
closes = session.query(PositionClose).filter(
    PositionClose.position_id == position_id
).order_by(PositionClose.closed_at).all()

# Calculate total realized P&L
total_pnl = sum(close.realized_pnl for close in closes)
```

### Query Partial Closes Only

```python
# Get only partial closes
partial_closes = session.query(PositionClose).filter(
    PositionClose.position_id == position_id,
    PositionClose.is_full_close == False
).all()
```

### Query Closes by Symbol

```python
# Get all closes for a symbol
symbol_closes = session.query(PositionClose).filter(
    PositionClose.account_id == account_id,
    PositionClose.symbol == "AAPL"
).order_by(PositionClose.closed_at).all()
```

## Migration Instructions

### Running the Migration

```bash
cd apps/trading-bot
alembic upgrade head
```

### Verifying Migration

```sql
-- Check that table exists
SELECT name FROM sqlite_master WHERE type='table' AND name='position_closes';

-- Check columns
PRAGMA table_info(position_closes);
```

## Next Steps

Critical Fix #5 is complete. All critical fixes are now complete:
- ✅ Critical Fix #1: Run Database Migration
- ✅ Critical Fix #2: Fix Average Price Calculation
- ✅ Critical Fix #3: Dashboard Fallback to DB Positions
- ✅ Critical Fix #4: Add Manual Sync API Endpoints
- ✅ Critical Fix #5: Partial Close Realized P&L Tracking

## Notes

- PositionClose records are created for both partial and full closes
- Position.realized_pnl is the cumulative sum of all closes
- Partial closes maintain FIFO assumption (average price unchanged)
- Exit price uses IBKR market_price or falls back to average_price
- All closes are timestamped for historical tracking

