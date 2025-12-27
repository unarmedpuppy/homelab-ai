# Polymarket Bot Stabilization Plan

## Current State Assessment

**Critical Issues Identified:**
1. **Data API returning stale/incorrect positions** - API shows 21 "open" positions that don't exist in Polymarket UI
2. **No trades executing** - Strategies appear to run but no actual trades occur
3. **WebSocket callback conflicts** - Multiple strategies were overwriting each other's callbacks (FIXED)
4. **Connection recovery** - Network loss didn't trigger reconnection (FIXED)
5. **Balance discrepancy** - Dashboard shows different values than actual wallet
6. **Observability gaps** - Can't trust what the dashboard/logs show

## Stabilization Approach

### Phase 1: Audit & Verify (Before Any Code Changes)

**Goal:** Understand exactly what's happening before changing anything.

1. **Create diagnostic script that checks:**
   - Actual CLOB API balance (direct call)
   - Actual positions from Polymarket data API
   - What's in our database (trades, settlement_queue, realized_pnl_ledger)
   - WebSocket connection state
   - What callbacks are registered
   - What markets are being monitored

2. **Add comprehensive logging to trace a single trade attempt:**
   - Entry condition evaluation
   - Order creation
   - Order submission
   - Order fill/reject
   - Position tracking

3. **Verify fixes already deployed:**
   - Confirm WebSocket multi-callback is working
   - Confirm health monitor is reconnecting

### Phase 2: Simplify to Single Strategy

**Goal:** Get ONE strategy working reliably before adding complexity.

1. **Disable Vol Happens completely** - Only run Gabagool
2. **Disable directional and near-resolution** - Only run arbitrage
3. **Add explicit logging at every decision point:**
   - "Evaluating market X: YES=$0.45, NO=$0.55, spread=0.00"
   - "Spread below threshold, skipping"
   - "Spread meets threshold, checking liquidity..."
   - "Submitting order: BUY X shares of YES at $Y"
   - "Order result: SUCCESS/FAIL - reason"

4. **Create a simple health endpoint** that returns:
   ```json
   {
     "websocket_connected": true,
     "websocket_last_message_ago_seconds": 5,
     "clob_connected": true,
     "markets_monitored": 3,
     "callbacks_registered": ["gabagool"],
     "last_trade_attempt": "2025-12-16T10:00:00Z",
     "last_trade_result": "no_opportunity"
   }
   ```

### Phase 3: Fix Data Integrity

**Goal:** Reconcile database with actual Polymarket state.

1. **Clear stale data:**
   - Settlement queue entries for resolved markets
   - Trades table entries that don't match reality

2. **Re-import actual state:**
   - Get real positions from Polymarket
   - Get real balance
   - Reset circuit breaker state

3. **Add reconciliation job:**
   - Periodically compare our database to Polymarket API
   - Alert on discrepancies
   - Auto-correct where safe

### Phase 4: Execution Path Audit

**Goal:** Trace why orders aren't executing.

1. **Check if orders are being created at all**
2. **Check if orders are being submitted to CLOB**
3. **Check order responses from CLOB**
4. **Check if dry_run is accidentally enabled**
5. **Check if circuit breaker is blocking trades**

### Phase 5: Rebuild Trust in Observability

**Goal:** Dashboard shows accurate, real-time data.

1. **Add "data freshness" indicators:**
   - "Balance last updated: 5s ago"
   - "WebSocket last message: 2s ago"
   - "Last CLOB health check: 30s ago"

2. **Add explicit "system health" panel:**
   - Green/Red indicators for each component
   - Clear error messages when things fail

3. **Add audit log:**
   - Every trade attempt logged with full context
   - Every order submission logged with response
   - Every error logged with stack trace

## Implementation Order

1. **Immediate (Today):**
   - Create comprehensive diagnostic script
   - Run diagnostics and save output
   - Disable Vol Happens to simplify

2. **Short-term (This Week):**
   - Add verbose logging to Gabagool
   - Add health endpoint
   - Trace a single market through the entire flow

3. **Medium-term (Next Week):**
   - Fix any execution issues found
   - Add reconciliation job
   - Improve dashboard observability

## Success Criteria

- [ ] Can see real-time prices updating in dashboard
- [ ] Can trace a trade opportunity from detection to execution in logs
- [ ] Balance in dashboard matches Polymarket UI
- [ ] At least one real trade executes successfully
- [ ] Health endpoint shows accurate system state

## Rollback Plan

If issues persist after Phase 2:
1. Stop the bot completely
2. Export all database data
3. Reset to a known-good state
4. Re-import only verified P&L data
5. Start fresh with minimal configuration
