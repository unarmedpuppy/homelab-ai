# Agent Task 6: Integrate WebSocket Streams into Dashboard UI

## Status: 🆕 **READY FOR ASSIGNMENT**

**Priority**: 🟡 HIGH  
**Estimated Time**: 3-4 hours  
**Dependencies**: Agents 3, 4, 5 (basic UI updates should be done first)

---

## Objective

Integrate WebSocket connections into the main dashboard (`src/ui/templates/dashboard.html`) to receive real-time updates for prices, signals, and portfolio changes, replacing the polling-based approach with live data streams.

## Task Details

### Files to Modify

**Primary File**: `src/ui/templates/dashboard.html`  
**WebSocket Endpoints**: 
- Price updates: `ws://localhost:8000/ws/price/{symbol}`
- Portfolio updates: `ws://localhost:8000/ws/portfolio`
- Signals: `ws://localhost:8000/ws/signals`

### WebSocket Streams to Integrate

1. **Price Stream** (`/ws/price/{symbol}`):
   - Real-time price updates
   - Replace polling from Agent 5's implementation
   - Update price display immediately on message

2. **Portfolio Stream** (`/ws/portfolio`):
   - Portfolio value changes
   - Position updates
   - Cash balance changes
   - Update portfolio summary widgets

3. **Signal Stream** (`/ws/signals`):
   - New trading signals generated
   - Display in live signal feed (new widget or existing)
   - Show signal details: symbol, type, confidence, timestamp

### Implementation Steps

1. **Create WebSocket Connection Manager**:
   ```javascript
   class DashboardWebSocketManager {
       constructor() {
           this.connections = {};
           this.reconnectAttempts = {};
           this.maxReconnectAttempts = 5;
       }
       
       connect(stream, symbol = null) {
           // Create WebSocket connection
           // Handle reconnection logic
           // Route messages to appropriate handlers
       }
       
       disconnect(stream) {
           // Close connection
           // Clean up
       }
       
       reconnect(stream) {
           // Exponential backoff reconnection
       }
   }
   ```

2. **Implement Price Stream Connection**:
   - Connect to `/ws/price/AAPL` (or configurable symbol)
   - On message: Update `#current-price` element
   - Handle connection errors and reconnection
   - Fall back to polling if WebSocket fails

3. **Implement Portfolio Stream Connection**:
   - Connect to `/ws/portfolio`
   - On message: Update portfolio summary widgets
   - Update: portfolio value, cash, positions, P&L
   - Merge with existing `updatePortfolioStats()` function

4. **Implement Signal Stream Connection**:
   - Connect to `/ws/signals`
   - On message: Add new signal to live feed
   - Display signal card with: symbol, side (BUY/SELL), confidence, timestamp
   - Auto-scroll to show newest signals
   - Optional: Play notification sound for high-confidence signals

5. **Add Connection Status Indicator**:
   - Show WebSocket connection status (connected/disconnected)
   - Display in header or status bar
   - Color code: green (connected), red (disconnected), yellow (connecting)

6. **Error Handling & Reconnection**:
   - Detect WebSocket disconnections
   - Implement exponential backoff reconnection
   - Fall back to polling if WebSocket unavailable
   - Show user-friendly connection status

7. **Cleanup**:
   - Close all WebSocket connections on page unload
   - Clear intervals
   - Prevent memory leaks

### UI Elements to Add/Update

1. **Price Display** (already updated by Agent 5):
   - Switch from polling to WebSocket updates
   - Keep polling as fallback

2. **Portfolio Summary** (already updated by Agent 3):
   - Add WebSocket updates to existing refresh logic
   - Update widgets in real-time

3. **Live Signal Feed** (new widget):
   ```html
   <div class="bg-white rounded-lg shadow p-6">
       <h2 class="text-xl font-bold mb-4">Live Signals</h2>
       <div id="signal-feed" class="space-y-2">
           <!-- Signal cards will be added here -->
       </div>
   </div>
   ```

### Reference Documentation

- **WebSocket Implementation**: `src/api/websocket/` directory
- **Existing Streams**: Check `src/api/websocket/streams/` for available streams
- **WebSocket Routes**: `src/api/routes/websocket.py` or `src/api/main.py`
- **Implementation Guide**: `docs/DASHBOARD_REAL_DATA_INTEGRATION.md` (WebSocket section)
- **Project TODO**: `docs/PROJECT_TODO.md` (UI Section, Task ui-7)

### WebSocket Endpoints Investigation

Before starting, verify WebSocket endpoints exist:
1. Check `src/api/websocket/` directory structure
2. Check `src/api/routes/websocket.py` for route definitions
3. Test WebSocket endpoints using browser console or WebSocket client
4. Understand message format from each stream

### Success Criteria

✅ Price WebSocket connected and updating in real-time  
✅ Portfolio WebSocket connected and updating portfolio widgets  
✅ Signal WebSocket connected and displaying live signals  
✅ Connection status indicator shows correct state  
✅ Automatic reconnection on disconnect  
✅ Fallback to polling if WebSocket unavailable  
✅ Clean connection cleanup on page unload  
✅ No memory leaks  
✅ No console errors  
✅ Code follows existing patterns

---

## Related Tasks

- **Agent 3**: Portfolio Summary UI (will be enhanced with WebSocket)
- **Agent 4**: Trade History UI (parallel, no overlap)
- **Agent 5**: Market Data UI (will switch from polling to WebSocket)
- **Agent 7**: Charts integration (parallel, no overlap)

## Notes

- **WebSocket URLs**: Use relative paths (e.g., `ws://${window.location.host}/ws/...`)
- **Reconnection**: Implement exponential backoff (1s, 2s, 4s, 8s, 16s)
- **Fallback**: Keep polling as backup if WebSocket fails
- **Message Format**: Verify message structure from each stream
- **Testing**: Test with WebSocket server running and disconnected states
- **Performance**: Limit signal feed to last 50 signals to prevent UI lag

---

**Ready to start?** First, investigate the existing WebSocket implementation in `src/api/websocket/` to understand available streams and message formats. Then implement the WebSocket manager and connect each stream to update the appropriate UI elements.

