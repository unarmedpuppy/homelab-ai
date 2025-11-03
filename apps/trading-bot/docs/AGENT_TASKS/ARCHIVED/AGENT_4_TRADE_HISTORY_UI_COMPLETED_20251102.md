# Agent Task 4: Integrate Trade History into Dashboard UI

## Status: 🆕 **READY FOR ASSIGNMENT**

**Priority**: 🔴 CRITICAL  
**Estimated Time**: 2-3 hours  
**Dependencies**: Agent 1 (Trade History API endpoint)

---

## Objective

Update the main dashboard JavaScript (`src/ui/templates/dashboard.html`) to fetch and display real trade history data from the `/api/trading/trades` endpoint, replacing the hardcoded static HTML table.

## Task Details

### Files to Modify

**Primary File**: `src/ui/templates/dashboard.html`  
**API Endpoint**: `GET /api/trading/trades` (to be created by Agent 1)

### Static Data to Replace

**Recent Trades Table**: Currently contains hardcoded HTML rows with static trade data:
- Symbol: "AAPL", "TSLA", "MSFT"
- Side: "BUY", "SELL"
- Quantity: 100, 50, 75
- Price: $150.00, $250.00, $300.00
- Time: "2:30 PM", "1:15 PM", "12:00 PM"

### Implementation Steps

1. **Create `loadRecentTrades()` Function**:
   ```javascript
   async function loadRecentTrades(limit = 10) {
       try {
           const response = await fetch(`/api/trading/trades?limit=${limit}&offset=0`);
           if (!response.ok) {
               throw new Error(`HTTP error! status: ${response.status}`);
           }
           const data = await response.json();
           
           // Update trades table
           renderTradesTable(data.trades);
           
           return data;
       } catch (error) {
           console.error('Error loading recent trades:', error);
           showError('Failed to load recent trades', error);
           return null;
       }
   }
   ```

2. **Create `renderTradesTable(trades)` Function**:
   - Clear existing table rows (except header)
   - Loop through trades array
   - Create table rows dynamically with:
     - Symbol
     - Side (with color coding: green for BUY, red for SELL)
     - Quantity
     - Price (formatted as currency)
     - Time (formatted from `executed_at` timestamp)
     - Status (FILLED, PENDING, etc.)
   - Handle empty trades array (show "No trades" message)

3. **Format Data**:
   - Format price: `$150.50` with 2 decimals
   - Format time: Convert ISO timestamp to local time (e.g., "2:30 PM")
   - Format quantity: Add commas for large numbers
   - Color code side: Green for BUY, Red for SELL
   - Show status badges with appropriate styling

4. **Add Auto-Refresh**:
   - Call `loadRecentTrades()` on page load
   - Optionally set up interval to refresh every 60 seconds
   - Show loading indicator while fetching

5. **Error Handling**:
   - Display error message if API call fails
   - Show "No trades available" if empty
   - Handle pagination if needed (future enhancement)

### UI Elements to Update

Find the recent trades table in `dashboard.html`:

```html
<!-- Find this section -->
<div class="bg-white rounded-lg shadow p-6">
    <h2 class="text-xl font-bold mb-4">Recent Trades</h2>
    <table class="w-full">
        <thead>...</thead>
        <tbody id="recent-trades-body">
            <!-- Static rows to be replaced -->
        </tbody>
    </table>
</div>
```

Replace static rows with dynamic rendering via JavaScript.

### Reference Documentation

- **Implementation Guide**: `docs/DASHBOARD_REAL_DATA_INTEGRATION.md` (Step 4: Update Dashboard JavaScript - Trade History section)
- **Static Data Analysis**: `docs/DASHBOARD_STATIC_DATA_ANALYSIS.md` (Recent Trades section)
- **API Endpoint**: `src/api/routes/trading.py` (`/trades` endpoint - to be created by Agent 1)
- **Scheduler Dashboard Reference**: `src/ui/templates/scheduler_dashboard.html` (table rendering patterns)
- **Project TODO**: `docs/PROJECT_TODO.md` (UI Section, Task ui-6 - Trade History part)

### Success Criteria

✅ Trades table displays real data from API  
✅ All trade fields formatted correctly (symbol, side, quantity, price, time)  
✅ Side colors are correct (green BUY, red SELL)  
✅ Time is formatted in readable format  
✅ Handles empty trades gracefully  
✅ Auto-refreshes on page load  
✅ Error handling displays user-friendly messages  
✅ Loading states shown while fetching  
✅ No console errors  
✅ Code follows existing JavaScript patterns

---

## Related Tasks

- **Agent 1**: Creating the Trade History API endpoint (must complete first or coordinate)
- **Agent 3**: Working on Portfolio Summary UI (parallel, no overlap)
- **Agent 5**: Working on Market Data UI (parallel, no overlap)

## Notes

- **API Endpoint**: `/api/trading/trades?limit=10&offset=0`
- **Date Formatting**: Use `new Date(trade.executed_at).toLocaleTimeString()` or similar
- **Table Structure**: Maintain existing table structure and styling
- **Color Coding**: Use Tailwind classes: `text-green-600` for BUY, `text-red-600` for SELL
- **Testing**: Test with various trade counts (0, 1, 10+, pagination)
- **Future Enhancement**: Add pagination controls if more than limit trades

---

**Ready to start?** Wait for Agent 1 to complete the `/api/trading/trades` endpoint, or coordinate to implement in parallel (you can mock the API response structure based on the spec). Review `dashboard.html` to find the recent trades table and understand the structure.

