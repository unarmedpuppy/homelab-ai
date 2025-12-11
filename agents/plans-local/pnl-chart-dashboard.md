# P&L Line Chart - Dashboard Implementation Plan

## Overview

Replace the CIRCUIT panel in the dashboard with a cumulative P&L line chart that:
- Shows running total P&L over time
- Has configurable timeframes (24h, 7d, All-time)
- Updates in real-time via SSE when trades resolve
- Matches the retro green terminal aesthetic

## Current State

The CIRCUIT panel (lines 527-543 in dashboard.py) displays:
- Circuit breaker status (NORMAL/WARNING/HALT)
- Visual bar segments showing risk level

This widget is low-value since the circuit breaker rarely activates. The P&L chart provides much more actionable information.

## Technical Approach

### 1. Data Source

Use existing SQLite `trades` table with columns:
- `created_at` - timestamp of trade
- `resolved_at` - when trade resolved
- `actual_profit` - realized P&L (null if pending)
- `status` - win/loss/pending

Query approach:
```sql
SELECT resolved_at, actual_profit
FROM trades
WHERE status IN ('win', 'loss') AND resolved_at IS NOT NULL
ORDER BY resolved_at ASC
```

Calculate cumulative P&L by summing `actual_profit` in order.

### 2. New API Endpoint

Add `/dashboard/pnl-history` endpoint that returns:
```json
{
  "points": [
    {"timestamp": "2025-12-10T14:30:00Z", "cumulative_pnl": 0.15},
    {"timestamp": "2025-12-10T15:45:00Z", "cumulative_pnl": 0.28},
    ...
  ],
  "timeframe": "24h"
}
```

Query params:
- `timeframe=24h|7d|all` - filter data range

### 3. Frontend Chart Implementation

Use **Canvas API** (no external libraries) for retro terminal style:
- Draw with green (#00ff41) line on dark background
- Grid lines in dim green (#003b00)
- Glow effect matching existing terminal aesthetic
- Y-axis: P&L values (auto-scale with padding)
- X-axis: Time labels appropriate to timeframe

### 4. Panel Structure

Replace CIRCUIT panel HTML (lines 527-543) with:
```html
<!-- P&L Chart -->
<div class="panel">
    <div class="panel-header">
        <span class="panel-title">[ P&L CHART ]</span>
        <div class="chart-timeframe">
            <button class="timeframe-btn active" data-tf="24h">24H</button>
            <button class="timeframe-btn" data-tf="7d">7D</button>
            <button class="timeframe-btn" data-tf="all">ALL</button>
        </div>
    </div>
    <div class="panel-body" style="padding: 10px;">
        <canvas id="pnl-chart" width="300" height="120"></canvas>
    </div>
</div>
```

### 5. CSS Additions

```css
.chart-timeframe {
    display: flex;
    gap: 5px;
}

.timeframe-btn {
    background: var(--dark-green);
    border: 1px solid var(--border);
    color: var(--dim-green);
    padding: 2px 8px;
    font-family: inherit;
    font-size: 0.7rem;
    cursor: pointer;
}

.timeframe-btn.active {
    background: var(--green);
    color: var(--bg);
    border-color: var(--green);
}

.timeframe-btn:hover {
    border-color: var(--green);
}
```

### 6. JavaScript Chart Rendering

```javascript
let currentTimeframe = '24h';
let pnlData = [];

function drawPnlChart(data) {
    const canvas = document.getElementById('pnl-chart');
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    ctx.fillStyle = '#0d1117';
    ctx.fillRect(0, 0, width, height);

    if (!data.length) {
        ctx.fillStyle = '#00aa2a';
        ctx.font = '12px "Share Tech Mono"';
        ctx.textAlign = 'center';
        ctx.fillText('No data', width/2, height/2);
        return;
    }

    // Calculate bounds with padding
    const values = data.map(d => d.cumulative_pnl);
    const minVal = Math.min(0, ...values);
    const maxVal = Math.max(0, ...values);
    const range = maxVal - minVal || 1;
    const padding = range * 0.1;

    // Draw grid lines
    ctx.strokeStyle = '#003b00';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = (height / 4) * i;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
    }

    // Draw zero line if crosses zero
    if (minVal < 0 && maxVal > 0) {
        const zeroY = height - ((0 - minVal + padding) / (range + 2*padding)) * height;
        ctx.strokeStyle = '#1a3a1a';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(0, zeroY);
        ctx.lineTo(width, zeroY);
        ctx.stroke();
    }

    // Draw P&L line with glow
    ctx.strokeStyle = '#00ff41';
    ctx.lineWidth = 2;
    ctx.shadowColor = '#00ff41';
    ctx.shadowBlur = 8;
    ctx.beginPath();

    data.forEach((point, i) => {
        const x = (i / (data.length - 1)) * width;
        const y = height - ((point.cumulative_pnl - minVal + padding) / (range + 2*padding)) * height;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Draw current value label
    const lastVal = data[data.length - 1].cumulative_pnl;
    ctx.fillStyle = lastVal >= 0 ? '#00ff41' : '#ff0040';
    ctx.font = 'bold 14px "Share Tech Mono"';
    ctx.textAlign = 'right';
    ctx.fillText((lastVal >= 0 ? '+' : '') + '$' + lastVal.toFixed(2), width - 5, 15);
}

async function loadPnlData(timeframe) {
    const resp = await fetch('/dashboard/pnl-history?timeframe=' + timeframe);
    const data = await resp.json();
    pnlData = data.points;
    drawPnlChart(pnlData);
}

// Timeframe button handlers
document.querySelectorAll('.timeframe-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.timeframe-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentTimeframe = btn.dataset.tf;
        loadPnlData(currentTimeframe);
    });
});
```

### 7. Real-time Updates via SSE

When a trade resolves, broadcast includes the new P&L point:
```javascript
// In updateDashboard function, handle pnl_update
if (data.pnl_update) {
    pnlData.push(data.pnl_update);
    drawPnlChart(pnlData);
}
```

Backend broadcasts on trade resolution:
```python
await dashboard.broadcast({
    "pnl_update": {
        "timestamp": resolved_at,
        "cumulative_pnl": running_total
    }
})
```

## Implementation Steps

### Step 1: Add persistence method for P&L history
- Add `get_pnl_history(timeframe)` method to `Database` class
- Returns list of (timestamp, cumulative_pnl) tuples

### Step 2: Add API endpoint
- Add `/dashboard/pnl-history` route to `DashboardServer`
- Accept `timeframe` query param
- Return JSON with points array

### Step 3: Replace CIRCUIT panel HTML
- Remove circuit breaker HTML (lines 527-543)
- Add P&L chart panel with canvas and timeframe buttons
- Remove circuit breaker CSS (lines 352-387)
- Add chart CSS

### Step 4: Add JavaScript chart logic
- Add chart drawing function
- Add timeframe button handlers
- Load initial data on page load
- Handle real-time updates

### Step 5: Broadcast P&L updates
- Modify trade resolution to broadcast pnl_update
- Include running cumulative total

### Step 6: Test and deploy
- Test with existing trade data
- Verify real-time updates work
- Deploy to server

## Files to Modify

1. `src/persistence.py` - Add `get_pnl_history()` method
2. `src/dashboard.py` - All frontend changes:
   - New API endpoint
   - Replace CIRCUIT HTML with chart
   - Add CSS styles
   - Add JavaScript chart logic
   - Broadcast P&L updates on trade resolution

## Cleanup

Remove circuit breaker related:
- `circuit_breaker` from stats dict (keep for backend, just remove UI)
- CSS for `.circuit-status`, `.circuit-level`, `.circuit-bar`, `.circuit-segment`
- JavaScript for circuit breaker updates
