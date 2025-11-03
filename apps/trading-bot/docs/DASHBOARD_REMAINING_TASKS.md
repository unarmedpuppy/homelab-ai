# Dashboard UI - Remaining Tasks Checklist

**Date**: 2024-12-19  
**Status**: 🔄 In Progress

## ✅ Completed (Fixed in Review)

- [x] **Portfolio Summary Loading**: Added `loadPortfolioSummary()` function and integrated into init
- [x] **Fixed refreshPortfolioViaAPI**: Updated to use correct endpoint and redirect to new function
- [x] **Portfolio Auto-Refresh**: Added 30-second interval for portfolio summary updates

## 🔴 Critical Tasks (Must Complete)

### 1. Trade History P&L Accuracy
**Status**: ⚠️ Needs Fix  
**Priority**: 🔴 CRITICAL  
**File**: `src/api/routes/trading.py` (lines 696-711)

**Issue**: Realized P&L calculation finds any closed position for a symbol, not necessarily the one related to the specific trade.

**Solutions**:
- **Option A (Quick Fix)**: Add `position_id` field to Trade model and link trades to positions
- **Option B (Better)**: Calculate P&L by pairing BUY/SELL trades for the same symbol sequentially
- **Option C (Best)**: Store realized P&L when position closes and reference it

**Action**: 
- [ ] Review Trade and Position models for relationship
- [ ] Implement proper P&L calculation
- [ ] Test with multiple trades for same symbol

---

### 2. Enhanced Error Handling
**Status**: ⚠️ Partial  
**Priority**: 🔴 CRITICAL

**Issues**:
- Some API calls don't use `apiCall()` utility
- Error messages not consistently displayed to users
- Missing error boundaries for graceful degradation

**Tasks**:
- [ ] Replace all `fetch()` calls with `apiCall()` utility in dashboard.js
- [ ] Add `showErrorMessage()` for all API failures
- [ ] Add retry logic for transient failures
- [ ] Add fallback values when APIs fail (show cached/last known data)

**Files**:
- `src/ui/templates/dashboard.html` - All API calls

---

### 3. Loading States for Portfolio Stats
**Status**: ❌ Missing  
**Priority**: 🔴 CRITICAL

**Issue**: Portfolio value, P&L, win rate, and active trades don't show loading indicators while fetching.

**Tasks**:
- [ ] Add loading spinners to portfolio stat cards
- [ ] Show "Loading..." text while fetching
- [ ] Use `setLoadingState()` utility function
- [ ] Prevent flicker by showing loading only on initial load

**Location**: `dashboard.html` lines 66-110 (portfolio stat cards)

---

## 🟡 High Priority Tasks

### 4. WebSocket Connection Status Updates
**Status**: ⚠️ Partial  
**Priority**: 🟡 HIGH

**Issues**:
- WebSocket status indicator exists but may not update properly
- IBKR connection status not always reflected

**Tasks**:
- [ ] Ensure `updateConnectionStatus()` called on all connection events
- [ ] Show separate indicators for WebSocket and IBKR status
- [ ] Add reconnection attempts counter to UI
- [ ] Display connection quality/latency

**Location**: `dashboard.html` - Connection status indicator

---

### 5. Portfolio Chart Optimization
**Status**: ✅ Works, but needs optimization  
**Priority**: 🟡 HIGH

**Issues**:
- Loading 1000 trades for chart could be slow
- No date range filtering
- No caching

**Tasks**:
- [ ] Add date range parameter to `loadPortfolioChartData()` (default: last 30 days)
- [ ] Cache chart data for 5 minutes
- [ ] Add date range selector in UI
- [ ] Optimize equity curve calculation (reduce computations)
- [ ] Consider server-side aggregation for large datasets

**Location**: `dashboard.html` - Portfolio chart section

---

### 6. Empty State Handling
**Status**: ⚠️ Partial  
**Priority**: 🟡 HIGH

**Issues**:
- Empty states shown inconsistently
- No helpful messages when no data

**Tasks**:
- [ ] Add "No trades yet" message in trade history
- [ ] Add "No positions" message when active_positions = 0
- [ ] Add "Connect IBKR" prompt when disconnected
- [ ] Add helpful tips/guidance in empty states

---

### 7. Data Validation & Safety
**Status**: ⚠️ Needs improvement  
**Priority**: 🟡 HIGH

**Issues**:
- No validation of API response structure
- Potential errors if API returns unexpected format
- Division by zero not always handled

**Tasks**:
- [ ] Add response validation for all API calls
- [ ] Add null/undefined checks before displaying data
- [ ] Handle edge cases (negative values, zero division, etc.)
- [ ] Add TypeScript or JSDoc types for better safety

---

## 🟢 Medium Priority Tasks

### 8. Performance Monitoring
**Status**: ❌ Missing  
**Priority**: 🟢 MEDIUM

**Tasks**:
- [ ] Track API call times and display in console (dev mode)
- [ ] Add performance metrics to UI (optional advanced view)
- [ ] Monitor WebSocket message latency
- [ ] Alert if API calls take > 2 seconds

---

### 9. Accessibility Improvements
**Status**: ❌ Not Started  
**Priority**: 🟢 MEDIUM

**Tasks**:
- [ ] Add ARIA labels to all interactive elements
- [ ] Add keyboard navigation support
- [ ] Ensure color contrast meets WCAG standards
- [ ] Add screen reader announcements for dynamic updates
- [ ] Test with screen readers

---

### 10. Mobile Responsiveness
**Status**: ⚠️ Needs Testing  
**Priority**: 🟢 MEDIUM

**Tasks**:
- [ ] Test dashboard on mobile devices
- [ ] Optimize chart sizes for small screens
- [ ] Make tables scrollable on mobile
- [ ] Adjust font sizes and spacing
- [ ] Test touch interactions

---

### 11. Real-time Portfolio Updates via WebSocket
**Status**: ⚠️ Partial (polling works, WebSocket needs enhancement)  
**Priority**: 🟢 MEDIUM

**Tasks**:
- [ ] Subscribe to portfolio WebSocket stream
- [ ] Update portfolio stats on WebSocket messages
- [ ] Reduce polling frequency when WebSocket connected
- [ ] Handle portfolio update messages from WebSocket

**Location**: `dashboard.html` - WebSocket message handlers

---

## 🔵 Low Priority / Future Enhancements

### 12. Chart Interactivity
**Status**: ❌ Not Started  
**Priority**: 🔵 LOW

**Tasks**:
- [ ] Add zoom functionality to portfolio chart
- [ ] Add pan/scroll for time navigation
- [ ] Add time range selector (1D, 1W, 1M, 1Y, ALL)
- [ ] Add crosshair for precise value reading
- [ ] Add click-to-see trade details

---

### 13. Export Functionality
**Status**: ❌ Not Started  
**Priority**: 🔵 LOW

**Tasks**:
- [ ] Export trade history as CSV
- [ ] Export charts as PNG/SVG
- [ ] Export portfolio summary as PDF
- [ ] Add print-friendly view

---

### 14. Settings Panel
**Status**: ❌ Not Started  
**Priority**: 🔵 LOW

**Tasks**:
- [ ] Create settings modal/page
- [ ] Allow configuration of:
  - Refresh intervals
  - Default symbols
  - Chart preferences
  - Notification settings
  - Theme preferences

---

### 15. Browser Notifications
**Status**: ❌ Not Started  
**Priority**: 🔵 LOW

**Tasks**:
- [ ] Request notification permission
- [ ] Send notifications for high-confidence signals
- [ ] Notify on trade executions
- [ ] Notify on connection status changes
- [ ] Allow user to configure notification preferences

---

### 16. Advanced Portfolio Analytics
**Status**: ❌ Not Started  
**Priority**: 🔵 LOW

**Tasks**:
- [ ] Add Sharpe ratio display
- [ ] Add maximum drawdown chart
- [ ] Add win/loss streak tracking
- [ ] Add position sizing analysis
- [ ] Add sector/correlation breakdown

---

## Testing Checklist

### Functional Testing
- [ ] Test with IBKR connected (real data)
- [ ] Test with IBKR disconnected (fallback/errors)
- [ ] Test with no trades in database
- [ ] Test with 1000+ trades
- [ ] Test WebSocket connection/disconnection
- [ ] Test all API endpoints individually
- [ ] Test error scenarios (network failures, API errors)

### Browser Testing
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile browsers (iOS Safari, Chrome Mobile)

### Performance Testing
- [ ] Load time < 2 seconds
- [ ] API calls complete in < 1 second
- [ ] Charts render smoothly
- [ ] No memory leaks (long-running dashboard)
- [ ] Efficient WebSocket usage

### User Experience Testing
- [ ] Intuitive navigation
- [ ] Clear error messages
- [ ] Helpful loading states
- [ ] Responsive layout
- [ ] Accessible (keyboard navigation, screen reader)

---

## Code Quality Improvements

### Refactoring Opportunities
- [ ] Extract chart initialization to separate function
- [ ] Create reusable API call wrapper with retry logic
- [ ] Standardize error handling patterns
- [ ] Reduce code duplication
- [ ] Add JSDoc comments to all functions

### Documentation
- [ ] Document all API endpoints used by dashboard
- [ ] Document WebSocket message formats
- [ ] Add inline code comments for complex logic
- [ ] Create user guide for dashboard features

---

## Priority Summary

**Immediate (This Week)**:
1. Trade History P&L Accuracy (#1)
2. Enhanced Error Handling (#2)
3. Loading States (#3)

**Short-term (Next 2 Weeks)**:
4. WebSocket Status Updates (#4)
5. Portfolio Chart Optimization (#5)
6. Empty State Handling (#6)
7. Data Validation (#7)

**Long-term (Future Sprints)**:
8-16. All medium and low priority items

---

**Last Updated**: 2024-12-19  
**Next Review**: After critical fixes are complete

