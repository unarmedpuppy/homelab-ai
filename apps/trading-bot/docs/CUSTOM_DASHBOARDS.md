# Custom Dashboard Examples

**Status**: ✅ Complete  
**Last Updated**: December 19, 2024

---

## Overview

This document provides examples and templates for creating custom Grafana dashboards tailored to specific use cases.

---

## Quick Start

### Creating a Custom Dashboard

1. **Access Grafana**: `http://localhost:3000`
2. **Create Dashboard**: Click "+" → "Dashboard"
3. **Add Panel**: Click "Add panel"
4. **Configure Query**: Use PromQL queries (see examples below)
5. **Save**: Click "Save dashboard"

### Export Dashboard

1. Dashboard Settings → JSON Model
2. Copy JSON
3. Save to `grafana/dashboards/your-dashboard.json`

---

## Example Dashboards

### 1. Trading Performance Dashboard

**Purpose**: Focus on trading-specific metrics

**Key Panels**:
- Trade execution rate
- Win rate by strategy
- Average profit per trade
- Slippage analysis

**Example Queries**:

```promql
# Trades per hour by strategy
sum by (strategy) (rate(trades_executed_total[1h])) * 3600

# Win rate calculation
sum(rate(trades_executed_total{side="BUY"}[1h])) / 
  (sum(rate(trades_executed_total{side="BUY"}[1h])) + 
   sum(rate(trades_executed_total{side="SELL"}[1h])))

# Average slippage
histogram_quantile(0.50, rate(slippage_percent_bucket[5m]))
```

**Panel Configuration**:
```json
{
  "title": "Trades per Hour",
  "type": "graph",
  "targets": [{
    "expr": "sum by (strategy) (rate(trades_executed_total[1h])) * 3600",
    "legendFormat": "{{strategy}}"
  }]
}
```

---

### 2. Provider Health Dashboard

**Purpose**: Monitor data provider status and performance

**Key Panels**:
- Provider availability status
- Error rate by provider
- Cache hit rates
- Rate limit frequency

**Example Queries**:

```promql
# Provider availability
provider_available

# Error rate by provider
sum by (provider) (rate(provider_errors_total[5m]))

# Cache hit rate trend
provider_cache_hit_rate

# Rate limit frequency
rate(provider_rate_limit_hits_total[5m])
```

**Table Panel** (Provider Summary):
```promql
# Combine multiple metrics
provider_cache_hit_rate OR 
sum by (provider) (rate(provider_errors_total[5m])) OR
provider_available
```

---

### 3. Risk Monitoring Dashboard

**Purpose**: Real-time risk monitoring and alerting

**Key Panels**:
- Portfolio P/L and drawdown
- Position sizes vs limits
- Daily loss tracking
- Risk limit status

**Example Queries**:

```promql
# Portfolio drawdown percentage
(portfolio_total_value - max_over_time(portfolio_total_value[24h])) / 
  max_over_time(portfolio_total_value[24h]) * 100

# Position sizes
sum by (symbol) (open_positions) * position_pnl / open_positions

# Daily P/L vs limit
portfolio_daily_pnl / abs(risk_daily_loss_limit) * 100

# Risk status (gauge panel)
portfolio_daily_pnl < risk_daily_loss_limit
```

**Alert Thresholds**:
- Drawdown > -10%: Yellow
- Drawdown > -15%: Red
- Daily P/L < 80% of limit: Yellow
- Daily P/L < 100% of limit: Red

---

### 4. Strategy Comparison Dashboard

**Purpose**: Compare performance across strategies

**Key Panels**:
- Win rate comparison (bar chart)
- Signals generated (line chart)
- Evaluation time (heatmap)
- Trade distribution (pie chart)

**Example Queries**:

```promql
# Win rate by strategy
strategy_win_rate

# Signals by strategy and type
sum by (strategy, type) (signals_generated_total)

# Evaluation time distribution
histogram_quantile(0.50, rate(strategy_evaluation_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(strategy_evaluation_duration_seconds_bucket[5m]))
```

**Bar Chart Panel**:
```json
{
  "title": "Strategy Win Rates",
  "type": "bargauge",
  "targets": [{
    "expr": "strategy_win_rate",
    "legendFormat": "{{strategy}}"
  }],
  "options": {
    "displayMode": "gradient",
    "orientation": "horizontal"
  }
}
```

---

### 5. Real-Time Trading Dashboard

**Purpose**: Live trading activity monitoring

**Key Panels**:
- Live trade feed (table)
- Current positions (stat panels)
- Recent signals (log panel)
- Execution status (status panel)

**Example Queries**:

```promql
# Recent trades (last 5 minutes)
increase(trades_executed_total[5m])

# Current open positions
open_positions

# Broker connection status
broker_connection_status

# Recent signals
increase(signals_generated_total[5m])
```

**Refresh Rate**: Set to 5-10 seconds for real-time updates

---

### 6. Cost Analysis Dashboard

**Purpose**: Track API costs and usage

**Key Panels**:
- API calls by provider
- Cache effectiveness
- Rate limit hits (cost indicator)
- Provider cost trends

**Example Queries**:

```promql
# Total API calls (estimate costs)
sum by (provider) (provider_requests_total{status!="cached"})

# Cache effectiveness
sum(provider_cache_hit_rate) / count(provider_cache_hit_rate) * 100

# Rate limit frequency (high = need more quota)
sum(rate(provider_rate_limit_hits_total[1h])) * 3600

# Cost savings from cache
sum(provider_requests_total{status="cached"}) / 
  sum(provider_requests_total) * 100
```

---

## Dashboard Templates

### Single Stat Panel Template

```json
{
  "title": "Metric Name",
  "type": "stat",
  "targets": [{
    "expr": "your_metric_query",
    "refId": "A"
  }],
  "options": {
    "graphMode": "area",
    "colorMode": "value",
    "thresholds": {
      "mode": "absolute",
      "steps": [
        {"color": "green", "value": null},
        {"color": "yellow", "value": 70},
        {"color": "red", "value": 90}
      ]
    }
  }
}
```

### Graph Panel Template

```json
{
  "title": "Metric Over Time",
  "type": "graph",
  "targets": [{
    "expr": "rate(your_metric[5m])",
    "legendFormat": "{{label}}"
  }],
  "yaxes": [
    {"format": "short", "label": "Value"},
    {"format": "short"}
  ],
  "xaxis": {"mode": "time"}
}
```

### Table Panel Template

```json
{
  "title": "Metric Table",
  "type": "table",
  "targets": [{
    "expr": "your_metric",
    "format": "table",
    "refId": "A"
  }],
  "transformations": [{
    "id": "organize",
    "options": {
      "excludeByName": {"Time": true},
      "renameByName": {
        "Value": "Display Name",
        "label": "Label Name"
      }
    }
  }]
}
```

---

## Advanced Techniques

### 1. Variable-Based Filtering

Create dashboard variables:

```json
{
  "templating": {
    "list": [{
      "name": "strategy",
      "type": "query",
      "query": "label_values(signals_generated_total, strategy)",
      "current": {"text": "All", "value": "$__all"}
    }]
  }
}
```

Use in queries:
```promql
rate(signals_generated_total{strategy=~"$strategy"}[5m])
```

### 2. Calculated Metrics

```promql
# Success rate
sum(rate(provider_requests_total{status="success"}[5m])) / 
  sum(rate(provider_requests_total[5m])) * 100

# Cost per trade (if tracking API costs)
api_costs_total / trades_executed_total
```

### 3. Annotations

Add annotations for events:

```json
{
  "annotations": {
    "list": [{
      "name": "Deployments",
      "datasource": "Prometheus",
      "expr": "deployment_event == 1",
      "titleFormat": "Deployment",
      "tags": ["deployment"]
    }]
  }
}
```

### 4. Alert Integration

Show alert status on dashboard:

```json
{
  "title": "Active Alerts",
  "type": "stat",
  "targets": [{
    "expr": "ALERTS{alertstate=\"firing\"}",
    "legendFormat": "{{alertname}}"
  }]
}
```

---

## Best Practices

1. **Group Related Metrics**: Use rows to organize panels
2. **Use Appropriate Visualizations**: 
   - Time series → Graph
   - Current value → Stat
   - Comparison → Bar chart
   - Distribution → Pie chart
3. **Set Refresh Intervals**: 
   - Real-time: 5-10s
   - Standard: 30s-1m
   - Historical: 5m+
4. **Color Code**: Use consistent colors (green=good, yellow=warning, red=critical)
5. **Add Descriptions**: Document what each panel shows
6. **Test Queries**: Verify queries work in Prometheus before adding to dashboard

---

## Dashboard JSON Export

Example minimal dashboard JSON:

```json
{
  "dashboard": {
    "title": "Custom Dashboard",
    "tags": ["custom", "trading-bot"],
    "timezone": "browser",
    "refresh": "30s",
    "panels": [
      {
        "id": 1,
        "title": "Panel Title",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "targets": [{
          "expr": "your_metric",
          "refId": "A"
        }]
      }
    ]
  }
}
```

---

## Sharing Dashboards

1. **Export JSON**: Dashboard Settings → JSON Model
2. **Save to Repository**: Place in `grafana/dashboards/`
3. **Auto-Provision**: Grafana will load automatically (if configured)
4. **Share with Team**: Commit to version control

---

## Related Documentation

- **Grafana Dashboards**: `docs/GRAFANA_DASHBOARDS.md`
- **Metrics Reference**: `docs/METRICS_REFERENCE.md`
- **Prometheus Queries**: https://prometheus.io/docs/prometheus/latest/querying/

---

**Last Updated**: December 19, 2024

