# WebSocket Implementation Plan - Review & Corrections

**Review Date**: 2024-12-19  
**Reviewer**: Auto  
**Status**: Issues Identified & Plan Updated

## 🔴 CRITICAL ISSUES FOUND

### 1. Message Format Mismatch with Dashboard
**Problem**: The plan's message protocol doesn't match what the dashboard expects.

**Dashboard Expectations** (from `dashboard.html:294-355`):
- `price_update`: Expects `data.symbols` directly (object mapping symbol → price data)
- `signal`: Expects `data.signal_type`, `data.confidence`, `data.price` directly at root level
- `trade_executed`: Expects trade data directly at root level

**Planned Format** (INCORRECT):
```json
{
  "type": "price_update",
  "symbols": {...},  // Correct
  "timestamp": "..."
}

{
  "type": "signal",
  "signal": {  // ❌ WRONG - should be at root level
    "signal_type": "BUY",
    ...
  }
}
```

**Correct Format**:
```json
{
  "type": "price_update",
  "symbols": {
    "AAPL": {
      "price": 150.25,
      "change": 0.5,
      "change_pct": 0.33
    }
  }
}

{
  "type": "signal",
  "signal_type": "BUY",  // ✅ At root level
  "confidence": 0.85,
  "price": 150.25,
  "symbol": "AAPL",
  "timestamp": "2024-12-19T12:00:00Z"
}

{
  "type": "trade_executed",
  "symbol": "AAPL",  // ✅ At root level
  "side": "BUY",
  "quantity": 10,
  "price": 150.25,
  "timestamp": "2024-12-19T12:00:00Z"
}
```

**Fix**: Update message models to match dashboard exactly.

---

### 2. Signal Callbacks Already Exist
**Finding**: `StrategyEvaluator` already has `signal_callbacks` list (line 59) but no notification method.

**Current State**:
```python
self.signal_callbacks: List[Callable[[TradingSignal], None]] = []
```

**Issue**: Callbacks are registered but never called when signals are generated.

**Fix**: Add `_notify_signal_callbacks()` call in `evaluate_strategy()` after signal generation (around line 246-276).

---

### 3. IBKR Callbacks Are Synchronous
**Finding**: IBKR callbacks (`order_filled_callbacks`, `position_update_callbacks`) are called synchronously from event handlers.

**Current Pattern**:
```python
def _on_order_filled(self, trade: Trade):
    for callback in self.order_filled_callbacks:
        callback(trade)  # Synchronous
```

**Issue**: WebSocket broadcasting needs to be async, but IBKR callbacks are sync.

**Fix**: 
- Option A: Make callbacks async-compatible (call `asyncio.create_task()` if callback is async)
- Option B: Use a queue to bridge sync → async
- Option C: Wrap WebSocket calls in `asyncio.run()` (not recommended)

**Recommendation**: Use async-compatible callback wrapper pattern.

---

### 4. Router Location vs Package Structure
**Finding**: Plan shows router in `src/api/routes/websocket.py` but also mentions `src/api/websocket/router.py`.

**Issue**: Inconsistent location.

**Recommendation**: 
- Router: `src/api/routes/websocket.py` (matches existing pattern)
- Package: `src/api/websocket/` for manager and streams (logical grouping)

---

## 🟡 HIGH PRIORITY IMPROVEMENTS

### 5. Subscription Protocol Missing from Dashboard
**Finding**: Dashboard doesn't send subscription messages - it just connects.

**Issue**: Plan includes subscription management but dashboard doesn't use it.

**Options**:
- A: Make all streams active by default (simpler, matches current dashboard)
- B: Add subscription support for future enhancements (more flexible)
- C: Hybrid - subscribe by default, allow unsubscribing

**Recommendation**: Option A for MVP (auto-subscribe to all streams), add subscription protocol in Phase 3.

---

### 6. Price Update Interval Too Aggressive
**Finding**: Plan suggests 1-second updates.

**Issue**: 
- May hit API rate limits
- May overwhelm dashboard with updates
- May consume excessive resources

**Recommendation**: 
- Start with 2-5 second intervals
- Make configurable
- Only send updates when price actually changes (plan already mentions this ✓)

---

### 7. Singleton Pattern Consistency
**Finding**: Codebase uses specific singleton pattern:
```python
_global_instance = None
_lock = threading.Lock()

def get_instance():
    global _global_instance
    if _global_instance is None:
        with _lock:
            if _global_instance is None:
                _global_instance = Class()
    return _global_instance
```

**Fix**: Use this exact pattern for `get_websocket_manager()`.

---

### 8. Background Task Management
**Finding**: Plan mentions `asyncio.create_task()` for background polling.

**Issue**: Tasks need to be tracked and cancelled on shutdown.

**Recommendation**:
- Store tasks in StreamManager
- Cancel all tasks in `stop_all()`
- Use FastAPI lifespan to ensure cleanup

---

### 9. Error Handling in Broadcasts
**Finding**: Plan mentions error handling but doesn't specify behavior when client disconnects during broadcast.

**Issue**: Need to handle `WebSocketDisconnect` exceptions when broadcasting.

**Recommendation**: 
- Wrap each `send_json()` in try/except
- Remove disconnected clients from registry
- Log but don't fail entire broadcast

---

## 🟢 MEDIUM PRIORITY IMPROVEMENTS

### 10. Client ID Generation
**Finding**: Plan mentions generating client IDs but doesn't specify method.

**Recommendation**: Use UUID4 for uniqueness:
```python
import uuid
client_id = str(uuid.uuid4())
```

---

### 11. Configuration Settings Structure
**Finding**: Settings pattern uses Pydantic `BaseSettings` with `env_prefix`.

**Fix**: Follow exact pattern:
```python
class WebSocketSettings(BaseSettings):
    enabled: bool = Field(default=True, ...)
    ping_interval: int = Field(default=30, ...)
    
    class Config:
        env_prefix = "WEBSOCKET_"
```

---

### 12. Testing Library
**Finding**: Plan mentions `websockets` library for testing.

**Issue**: Need to check if already in requirements.

**Recommendation**: Use FastAPI's test client with WebSocket support instead (no new dependency):
```python
from fastapi.testclient import TestClient
client = TestClient(app)
with client.websocket_connect("/ws") as websocket:
    ...
```

---

### 13. Route Registration
**Finding**: All routes use `prefix="/api/..."` except root routes.

**Issue**: Plan shows `/ws` but should consider `/api/ws` for consistency.

**Recommendation**: Use `/ws` (dashboard expects it) but document both options.

---

## 📝 UPDATED IMPLEMENTATION APPROACH

### Phase 1 Corrections

1. **Message Models** - Match dashboard exactly:
   ```python
   class PriceUpdateMessage(BaseModel):
       type: Literal["price_update"] = "price_update"
       symbols: Dict[str, PriceData]
   
   class SignalMessage(BaseModel):
       type: Literal["signal"] = "signal"
       signal_type: str  # "BUY", "SELL", "HOLD"
       symbol: str
       price: float
       confidence: float
       timestamp: datetime
   
   class TradeMessage(BaseModel):
       type: Literal["trade_executed"] = "trade_executed"
       symbol: str
       side: str
       quantity: int
       price: float
       timestamp: datetime
   ```

2. **Subscription Model** - Auto-subscribe for MVP:
   - All connected clients receive all streams by default
   - Phase 3 can add selective subscriptions

3. **Signal Callback Integration**:
   - Add `_notify_signal_callbacks()` method to `StrategyEvaluator`
   - Call after signal generation (line ~276)
   - WebSocket handler registers callback

4. **IBKR Callback Integration**:
   - Create async wrapper for sync callbacks
   - Use `asyncio.create_task()` to run async operations

### Phase 2 Corrections

1. **Stream Startup** - Integrate with FastAPI lifespan:
   - Start streams in `lifespan()` startup
   - Stop streams in `lifespan()` shutdown
   - Track all background tasks

2. **Error Handling**:
   - Try/except around all `websocket.send_json()` calls
   - Remove disconnected clients immediately
   - Don't fail entire broadcast on single client error

### Phase 3 Corrections

1. **Subscription Protocol** - Defer to Phase 3:
   - MVP: All streams active for all clients
   - Enhancement: Add subscription messages later

---

## ✅ VERIFIED CORRECT ELEMENTS

1. ✅ Package structure (`src/api/websocket/`)
2. ✅ Router location (`src/api/routes/websocket.py`)
3. ✅ FastAPI lifespan integration
4. ✅ Connection manager pattern
5. ✅ Configuration via settings
6. ✅ Background task pattern (asyncio.create_task)
7. ✅ Testing approach

---

## 🎯 REVISED PRIORITIES

### Phase 1 (MVP - Dashboard Working):
1. WebSocket manager with connection tracking
2. WebSocket route at `/ws`
3. Price update stream (auto-subscribe, 2-5s interval)
4. Signal broadcast (hook into evaluator callbacks)
5. Trade broadcast (hook into IBKR callbacks)
6. Message formats matching dashboard exactly

### Phase 2 (Enhancements):
1. Portfolio updates
2. Subscription management
3. Advanced error handling
4. Connection limits and rate limiting

### Phase 3 (Future):
1. Market data streaming (OHLCV)
2. Options flow streaming
3. Authentication/authorization
4. Advanced subscription filtering

---

## 📋 ACTION ITEMS

1. ✅ Update message models to match dashboard format
2. ✅ Add signal callback notification to `StrategyEvaluator`
3. ✅ Create async callback wrapper for IBKR events
4. ✅ Update subscription model (auto-subscribe for MVP)
5. ✅ Adjust price update interval (2-5 seconds)
6. ✅ Implement singleton pattern correctly
7. ✅ Add task tracking and cleanup
8. ✅ Update test approach (use FastAPI TestClient)

---

**Status**: Plan reviewed, issues identified, corrections noted. Ready to proceed with corrected approach.

