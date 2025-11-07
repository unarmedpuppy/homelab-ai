# Position Sync Service Implementation Plan

**Priority**: 🔴 HIGH - Critical for data persistence  
**Status**: 📋 Planning  
**Date**: 2024-12-19

## Overview

Implement a background service that syncs IBKR positions to the database, enabling:
- Historical position tracking
- Offline dashboard access
- Accurate P&L calculations
- Position lifecycle analysis

## Architecture Design

### Component: PositionSyncService

**Location**: `src/core/sync/position_sync.py`

**Responsibilities**:
1. Sync IBKR positions to database `Position` table
2. Track position lifecycle (open → close)
3. Calculate realized P&L when positions close
4. Handle edge cases (partial closes, position splits, etc.)

### Integration Points

1. **Scheduler Integration**: Add as a background task in `TradingScheduler`
2. **IBKR Callbacks**: Register position update callbacks for real-time sync
3. **API Integration**: Expose sync status and manual trigger endpoint
4. **Dashboard**: Use database positions when IBKR is disconnected

## Data Model Review

### Current Position Model

```python
class Position(Base):
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    quantity = Column(Integer, nullable=False)
    average_price = Column(Float, nullable=False)
    current_price = Column(Float)
    unrealized_pnl = Column(Float, default=0.0)
    unrealized_pnl_pct = Column(Float, default=0.0)
    status = Column(Enum(PositionStatus), default=PositionStatus.OPEN)
    opened_at = Column(DateTime, server_default=func.now())
    closed_at = Column(DateTime)
```

### Missing Fields (Consider Adding)

**Option 1: Extend Position Model**
- `last_synced_at`: When position was last synced from IBKR
- `realized_pnl`: Realized P&L when position closes
- `entry_trade_id`: Reference to first buy trade
- `exit_trade_id`: Reference to final sell trade

**Option 2: Create PositionHistory Model** (Better for tracking changes)
- Track position snapshots over time
- Enable historical analysis of position changes

**Recommendation**: Start with Option 1 (extend Position), add Option 2 later if needed.

## Sync Strategy

### Sync Triggers

1. **Periodic Sync** (Primary)
   - Run every 5 minutes (configurable)
   - Background task in scheduler
   - Syncs all positions for all accounts

2. **Event-Driven Sync** (Secondary)
   - IBKR position update callbacks
   - Trade execution callbacks
   - Manual trigger via API

3. **On-Demand Sync**
   - API endpoint to trigger immediate sync
   - Dashboard refresh button
   - After trade execution

### Sync Algorithm

```
1. Get positions from IBKR (for all accounts)
2. Get existing positions from database (for same accounts)
3. For each IBKR position:
   a. Find matching DB position (by account_id + symbol)
   b. If not found:
      - Create new Position record (status=OPEN)
      - Set opened_at = now
   c. If found:
      - Update quantity, average_price, current_price, unrealized_pnl
      - If quantity changed to 0:
         - Set status=CLOSED
         - Set closed_at = now
         - Calculate realized P&L
      - If quantity increased:
         - Update average_price (weighted average)
         - Keep status=OPEN
      - If quantity decreased (partial close):
         - Update average_price (if needed)
         - Keep status=OPEN
         - Calculate partial realized P&L
4. For each DB position not in IBKR:
   a. If quantity > 0:
      - Log warning (position exists in DB but not IBKR)
      - Option: Set status=CLOSED (position was closed externally)
   b. If quantity = 0:
      - Already closed, no action needed
5. Commit all changes
```

## Edge Cases & Error Handling

### Edge Cases

1. **IBKR Disconnected**
   - Skip sync, log warning
   - Return last known positions from database
   - Don't mark positions as closed

2. **Position Split/Merge**
   - Quantity changes without trades
   - Adjust average_price proportionally
   - Log the event

3. **Partial Closes**
   - Quantity decreases but position still open
   - Calculate realized P&L for closed portion
   - Update average_price for remaining position

4. **Position in DB but not IBKR**
   - Could be closed externally
   - Could be data inconsistency
   - Strategy: Mark as closed if quantity > 0, log warning

5. **Multiple Accounts**
   - Sync positions for all accounts
   - Filter by account_id in queries

6. **Race Conditions**
   - Multiple syncs running simultaneously
   - Use database transactions
   - Consider locking mechanism if needed

### Error Handling

- **IBKR API Errors**: Log error, skip this sync cycle, retry next cycle
- **Database Errors**: Rollback transaction, log error, alert
- **Data Validation Errors**: Log warning, skip invalid position, continue with others
- **Timeout**: Set timeout for IBKR calls, fail gracefully

## Realized P&L Calculation

### When Position Closes

```
realized_pnl = (exit_price - average_price) * quantity
```

**Challenges**:
- Need exit price (from IBKR or last trade)
- Need to handle partial closes
- Need to track cost basis accurately

**Solution**:
1. When position closes (quantity → 0):
   - Get exit price from IBKR (current_price or last trade)
   - Calculate: `realized_pnl = (exit_price - average_price) * original_quantity`
   - Store in `Position.realized_pnl` (new field)

2. For partial closes:
   - Calculate realized P&L for closed portion
   - Store in separate `PositionClose` record (future enhancement)
   - Or track in `Trade` model with realized_pnl field

## Configuration

### Settings

Add to `SchedulerSettings` or create `PositionSyncSettings`:

```python
class PositionSyncSettings(BaseSettings):
    enabled: bool = Field(default=True)
    sync_interval: int = Field(default=300)  # 5 minutes
    sync_on_trade: bool = Field(default=True)  # Sync after trade execution
    sync_on_position_update: bool = Field(default=True)  # Sync on IBKR callbacks
    mark_missing_as_closed: bool = Field(default=False)  # Mark positions as closed if not in IBKR
    calculate_realized_pnl: bool = Field(default=True)
    
    class Config:
        env_prefix = "POSITION_SYNC_"
```

## Implementation Phases

### Phase 1: Core Sync Service ✅

**Tasks**:
- [ ] Create `PositionSyncService` class
- [ ] Implement `sync_positions()` method
- [ ] Handle create/update/close logic
- [ ] Add error handling
- [ ] Add logging

**Files**:
- `src/core/sync/__init__.py` (new)
- `src/core/sync/position_sync.py` (new)

### Phase 2: Scheduler Integration ✅

**Tasks**:
- [ ] Add sync task to `TradingScheduler`
- [ ] Configure sync interval
- [ ] Start/stop sync with scheduler
- [ ] Add sync statistics

**Files**:
- `src/core/scheduler/trading_scheduler.py` (modify)
- `src/config/settings.py` (add settings)

### Phase 3: IBKR Callback Integration ✅

**Tasks**:
- [ ] Register position update callbacks
- [ ] Trigger sync on position changes
- [ ] Handle callback errors

**Files**:
- `src/data/brokers/ibkr_client.py` (modify)
- `src/core/sync/position_sync.py` (modify)

### Phase 4: Database Model Updates ✅

**Tasks**:
- [ ] Add `last_synced_at` field to Position
- [ ] Add `realized_pnl` field to Position
- [ ] Create database migration
- [ ] Update Position queries

**Files**:
- `src/data/database/models.py` (modify)
- `alembic/versions/XXXX_add_position_fields.py` (new)

### Phase 5: API Integration ✅

**Tasks**:
- [ ] Add `/api/sync/positions` endpoint (manual trigger)
- [ ] Add `/api/sync/status` endpoint
- [ ] Add sync statistics to scheduler status

**Files**:
- `src/api/routes/sync.py` (new)
- `src/api/routes/scheduler.py` (modify)

### Phase 6: Dashboard Integration ✅

**Tasks**:
- [ ] Update portfolio summary to use DB positions when IBKR disconnected
- [ ] Add "Last Synced" indicator
- [ ] Add manual sync button

**Files**:
- `src/api/routes/trading.py` (modify)
- `src/ui/templates/dashboard.html` (modify)

### Phase 7: Testing ✅

**Tasks**:
- [ ] Unit tests for sync logic
- [ ] Integration tests with mock IBKR
- [ ] Test edge cases
- [ ] Test error scenarios

**Files**:
- `tests/unit/test_position_sync.py` (new)
- `tests/integration/test_position_sync_integration.py` (new)

## Testing Strategy

### Unit Tests

1. **Sync Logic Tests**:
   - Create new position
   - Update existing position
   - Close position
   - Handle partial closes
   - Handle missing positions

2. **P&L Calculation Tests**:
   - Realized P&L calculation
   - Partial close P&L
   - Average price updates

3. **Edge Case Tests**:
   - IBKR disconnected
   - Invalid data
   - Race conditions

### Integration Tests

1. **End-to-End Sync**:
   - Mock IBKR positions
   - Run sync
   - Verify database state

2. **Scheduler Integration**:
   - Start scheduler
   - Verify sync runs periodically
   - Verify sync on trade execution

### Manual Testing

1. **Real IBKR Connection**:
   - Connect to IBKR
   - Execute trades
   - Verify positions sync
   - Disconnect IBKR
   - Verify dashboard shows last synced positions

## Performance Considerations

### Optimization

1. **Batch Updates**: Update all positions in single transaction
2. **Selective Sync**: Only sync changed positions (if callbacks available)
3. **Indexing**: Ensure indexes on `account_id`, `symbol`, `status`
4. **Connection Pooling**: Reuse database connections

### Monitoring

1. **Sync Duration**: Track how long sync takes
2. **Sync Frequency**: Track sync success/failure rate
3. **Position Count**: Monitor number of positions synced
4. **Errors**: Alert on sync errors

## Migration Strategy

### Database Migration

1. Add new fields to Position model
2. Create Alembic migration
3. Run migration on deployment
4. Backfill `last_synced_at` for existing positions

### Deployment

1. Deploy code with sync service disabled
2. Enable sync service via config
3. Monitor for issues
4. Gradually increase sync frequency if needed

## Success Criteria

1. ✅ Positions are synced to database every 5 minutes
2. ✅ Positions sync immediately after trade execution
3. ✅ Dashboard shows positions when IBKR is disconnected
4. ✅ Realized P&L is calculated when positions close
5. ✅ Position lifecycle is tracked (open → close)
6. ✅ No data loss or inconsistencies
7. ✅ Performance impact is minimal (< 1 second per sync)

## Future Enhancements

1. **Position History**: Track position changes over time
2. **Position Events**: Log position open/close events
3. **Cost Basis Tracking**: Track cost basis for tax reporting
4. **Multi-Account Support**: Enhanced multi-account position tracking
5. **Position Analytics**: Historical position analysis

## Questions to Resolve

1. **Realized P&L Storage**: Store in Position model or separate table?
   - **Decision**: Store in Position model for simplicity, can add separate table later

2. **Partial Close Tracking**: How to track partial closes?
   - **Decision**: Update Position, calculate realized P&L for closed portion, store in Trade model

3. **Sync Frequency**: How often to sync?
   - **Decision**: 5 minutes default, configurable

4. **Missing Position Handling**: What to do if position in DB but not IBKR?
   - **Decision**: Log warning, don't auto-close (user might have closed externally)

5. **Position History**: Do we need PositionHistory model now?
   - **Decision**: No, start simple, add later if needed

## Implementation Order

1. **Phase 1**: Core sync service (can test independently)
2. **Phase 4**: Database model updates (needed for Phase 1)
3. **Phase 2**: Scheduler integration (uses Phase 1)
4. **Phase 3**: IBKR callbacks (enhancement)
5. **Phase 5**: API integration (nice to have)
6. **Phase 6**: Dashboard integration (user-facing)
7. **Phase 7**: Testing (throughout, but comprehensive at end)

## Estimated Effort

- **Phase 1**: 2-3 hours
- **Phase 2**: 1 hour
- **Phase 3**: 1-2 hours
- **Phase 4**: 1 hour
- **Phase 5**: 1 hour
- **Phase 6**: 1-2 hours
- **Phase 7**: 2-3 hours

**Total**: ~10-13 hours

## Dependencies

- ✅ Database models exist
- ✅ IBKR client exists
- ✅ Scheduler exists
- ✅ Database session management exists
- ⚠️ Need to add position update callbacks to IBKR client (if not already present)

## Risks & Mitigations

1. **Risk**: Sync conflicts with manual position updates
   - **Mitigation**: Use database transactions, sync is source of truth

2. **Risk**: Performance impact of frequent syncs
   - **Mitigation**: Optimize queries, use indexes, batch updates

3. **Risk**: Data inconsistencies between IBKR and DB
   - **Mitigation**: IBKR is source of truth, DB is cache, log discrepancies

4. **Risk**: Missing position updates during IBKR disconnection
   - **Mitigation**: Sync on reconnection, periodic sync catches up

## Key Implementation Details

### Database Session Pattern

Use the existing pattern from `src/data/database/__init__.py`:

```python
from ...data.database import SessionLocal

session = SessionLocal()
try:
    # Database operations
    session.commit()
except Exception:
    session.rollback()
    raise
finally:
    session.close()
```

Or use context manager pattern from `SentimentRepository`:

```python
@contextmanager
def _get_session(self, autocommit: bool = True):
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
```

### IBKR Callback Pattern

Position update callbacks already exist in `IBKRClient`:

```python
# In IBKRClient
self.position_update_callbacks = []

def _on_position_update(self, position: Position):
    for callback in self.position_update_callbacks:
        callback(position)

# Register callback
client.position_update_callbacks.append(on_position_update)
```

### Scheduler Integration Pattern

Follow the pattern from `TradingScheduler`:

```python
# In TradingScheduler.__init__
self._sync_task: Optional[asyncio.Task] = None

# In start()
self._sync_task = asyncio.create_task(self._sync_loop())

# In stop()
if self._sync_task:
    self._sync_task.cancel()
```

## Next Steps

1. ✅ Review and approve this plan
2. Start with Phase 1 (Core Sync Service)
3. Test incrementally
4. Deploy and monitor

## Ready to Implement

All planning complete. Key decisions made:
- ✅ Use existing Position model (extend with new fields)
- ✅ Sync every 5 minutes (configurable)
- ✅ Use IBKR callbacks for real-time updates
- ✅ Follow existing database session patterns
- ✅ Integrate with scheduler as background task
- ✅ Calculate realized P&L when positions close

**Status**: ✅ **READY FOR IMPLEMENTATION**

