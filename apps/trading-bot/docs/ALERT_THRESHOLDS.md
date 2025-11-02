# Alert Threshold Recommendations

**Status**: ✅ Complete  
**Last Updated**: December 19, 2024

---

## Overview

This document provides recommendations for adjusting alert thresholds based on different environments (development, staging, production) and use cases.

---

## System Health Alerts

### CPU Usage

**Current Threshold**: `> 90% for 5m`

**Recommendations**:
- **Development**: `> 95% for 10m` (more lenient)
- **Production**: `> 80% for 3m` (more sensitive)
- **High-Frequency Trading**: `> 70% for 1m` (very sensitive)

**Reasoning**: High CPU can cause latency in trading decisions. Adjust based on criticality.

### Memory Usage

**Current Threshold**: `> 85% for 5m`

**Recommendations**:
- **Development**: `> 90% for 10m`
- **Production**: `> 80% for 3m`
- **Memory-Constrained**: `> 75% for 5m`

**Reasoning**: Memory pressure can cause OOM kills. Monitor swap usage as secondary indicator.

### Disk Usage

**Current Threshold**: `> 90% for 10m`

**Recommendations**:
- **All Environments**: Keep at `> 85% for 5m` (critical)
- **High Data Volume**: `> 80% for 1h` (early warning)
- **Log-Heavy**: `> 80% for 30m` (logs can fill quickly)

**Reasoning**: Disk full = application failure. Always critical.

---

## API Health Alerts

### Error Rate

**Current Threshold**: `> 0.1 errors/sec for 5m`

**Recommendations**:
- **Development**: `> 1.0 errors/sec for 10m`
- **Production**: `> 0.05 errors/sec for 3m`
- **Strict SLA**: `> 0.01 errors/sec for 1m`

**Calculation**: `rate(http_errors_total[5m]) > threshold`

### Response Time

**Current Threshold**: `p95 > 2s for 5m`

**Recommendations**:
- **Development**: `p95 > 5s for 10m`
- **Production**: `p95 > 1s for 3m`
- **Real-Time Trading**: `p95 > 500ms for 1m`

**Query**: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > threshold`

---

## Trading Alerts

### Trade Rejection Rate

**Current Threshold**: `> 10% for 5m`

**Recommendations**:
- **Conservative**: `> 5% for 3m` (early detection)
- **Normal**: `> 10% for 5m` (current)
- **Aggressive**: `> 15% for 10m` (tolerate more)

**Calculation**: `sum(rate(trades_rejected_total[5m])) / (sum(rate(trades_executed_total[5m])) + sum(rate(trades_rejected_total[5m]))) > threshold`

### Broker Disconnection

**Current Threshold**: `== 0 for 2m`

**Recommendations**:
- **All Environments**: Keep at `== 0 for 1m` (critical)
- **Network Issues**: `== 0 for 30s` (very sensitive)

**Reasoning**: Any broker disconnection is critical for live trading.

### Slippage

**Current Threshold**: `p95 > 1% for 5m`

**Recommendations**:
- **Market Orders**: `p95 > 0.5% for 3m` (stricter)
- **Limit Orders**: `p95 > 2% for 10m` (more lenient)
- **High Volatility**: `p95 > 1.5% for 5m` (adjust for market conditions)

---

## Portfolio & Risk Alerts

### Portfolio Drawdown

**Current Threshold**: `<-$5000 for 10m`

**Recommendations**:
- **Small Account** (<$50k): `<-$2000 for 5m`
- **Medium Account** ($50k-$500k): `<-$5000 for 10m` (current)
- **Large Account** (>$500k): `<-$25000 for 15m`

**Alternative (Percentage-Based)**:
```promql
(portfolio_total_value - max_over_time(portfolio_total_value[24h])) / max_over_time(portfolio_total_value[24h]) < -0.10
```
Triggers at 10% drawdown.

### Daily Loss Limit

**Current**: Compares against `risk_daily_loss_limit`

**Recommendations**:
- Set `risk_daily_loss_limit` based on account size:
  - Small: `account_value * 0.02` (2%)
  - Medium: `account_value * 0.05` (5%)
  - Large: `account_value * 0.10` (10%)

### Maximum Drawdown

**Current Threshold**: `<-20% for 5m`

**Recommendations**:
- **Conservative**: `<-15% for 3m`
- **Normal**: `<-20% for 5m` (current)
- **Aggressive**: `<-25% for 10m`

---

## Provider Alerts

### Provider Error Rate

**Current Threshold**: `> 0.05 errors/sec for 5m`

**Recommendations**:
- **Critical Providers** (market data): `> 0.01 errors/sec for 3m`
- **Optional Providers** (sentiment): `> 0.1 errors/sec for 10m`
- **External APIs**: `> 0.05 errors/sec for 5m` (current)

### Rate Limit Hits

**Current Threshold**: `> 0.1 hits/sec for 5m`

**Recommendations**:
- **All Providers**: Keep at `> 0.1 hits/sec for 5m`
- **Strict Quotas**: `> 0.05 hits/sec for 3m`

**Reasoning**: Frequent rate limit hits indicate quota exhaustion or misconfiguration.

### Cache Hit Rate

**Current Threshold**: `< 50% for 10m` (info level)

**Recommendations**:
- **High-Volume**: `< 70% for 5m` (warning)
- **Low-Volume**: `< 30% for 15m` (info)

**Reasoning**: Low cache hit rate = more API calls = higher costs/rate limits.

---

## Strategy Alerts

### Strategy Evaluation Time

**Current Threshold**: `p95 > 1s for 5m`

**Recommendations**:
- **Real-Time**: `p95 > 500ms for 3m`
- **Batch Processing**: `p95 > 2s for 10m`
- **Complex Strategies**: `p95 > 3s for 5m`

### Strategy Win Rate

**Current Threshold**: `< 40% for 1h`

**Recommendations**:
- **New Strategy**: `< 30% for 24h` (longer evaluation)
- **Established Strategy**: `< 50% for 1h` (higher bar)
- **Risk-Adjusted**: Consider Sharpe ratio instead

**Note**: Win rate alone isn't sufficient. Consider profit factor, average win/loss ratio.

---

## Environment-Specific Configurations

### Development

```yaml
# More lenient thresholds, longer durations
HighCPUUsage: > 95% for 10m
HighErrorRate: > 1.0/sec for 10m
HighResponseTime: p95 > 5s for 10m
```

### Staging

```yaml
# Production-like but slightly more lenient
HighCPUUsage: > 85% for 5m
HighErrorRate: > 0.1/sec for 5m
HighResponseTime: p95 > 2s for 5m
```

### Production

```yaml
# Stricter thresholds, faster detection
HighCPUUsage: > 80% for 3m
HighErrorRate: > 0.05/sec for 3m
HighResponseTime: p95 > 1s for 3m
```

---

## Adjusting Thresholds

### Method 1: Edit alerts.yml

```yaml
- alert: HighCPUUsage
  expr: system_cpu_usage_percent > 80  # Changed from 90
  for: 3m  # Changed from 5m
```

### Method 2: Environment Variables (Advanced)

Use Prometheus relabeling or external labels:

```yaml
global:
  external_labels:
    environment: 'production'
    
# In alerts.yml, use label-based routing
- alert: HighCPUUsage
  expr: system_cpu_usage_percent > 80
  labels:
    environment: 'production'
```

### Reload Configuration

After changes:

```bash
# Reload Prometheus config
curl -X POST http://localhost:9090/-/reload

# Or restart
docker restart trading-bot-prometheus
```

---

## Monitoring Threshold Effectiveness

### Alert Frequency Analysis

Query alerts fired in last 24h:

```promql
count_over_time(
  ALERTS{alertname="HighCPUUsage",alertstate="firing"}[24h]
)
```

### False Positive Rate

Track alerts that fire but resolve quickly:

```promql
# Alerts that fire but resolve in < 1 minute
ALERTS{alertstate="firing"} - on(alertname) 
  ALERTS{alertstate="resolved"} offset 1m
```

### Threshold Tuning

1. **Start Conservative**: Higher thresholds initially
2. **Monitor**: Track alert frequency for 1-2 weeks
3. **Adjust**: Lower thresholds for critical issues, raise for noise
4. **Document**: Keep track of threshold changes and rationale

---

## Example: Production Configuration

```yaml
# System - Stricter
- alert: HighCPUUsage
  expr: system_cpu_usage_percent > 80
  for: 3m

- alert: HighMemoryUsage
  expr: system_memory_usage_percent > 80
  for: 3m

# Trading - Critical
- alert: BrokerDisconnected
  expr: broker_connection_status == 0
  for: 30s

- alert: HighTradeRejectionRate
  expr: sum(rate(trades_rejected_total[5m])) / (sum(rate(trades_executed_total[5m])) + sum(rate(trades_rejected_total[5m]))) > 0.05
  for: 3m

# Risk - Conservative
- alert: PortfolioDrawdown
  expr: portfolio_total_pnl < -2000
  for: 5m

- alert: MaxDrawdownExceeded
  expr: risk_max_drawdown < -15
  for: 3m
```

---

## Best Practices

1. **Start High**: Begin with conservative (higher) thresholds
2. **Monitor & Adjust**: Lower thresholds gradually based on actual behavior
3. **Document Changes**: Record why thresholds were adjusted
4. **Test Alerts**: Verify alerts fire when conditions are met
5. **Review Regularly**: Monthly review of alert effectiveness

---

## Related Documentation

- **Alert Rules**: `prometheus/alerts.yml`
- **Alertmanager Setup**: `docs/ALERTMANAGER_SETUP.md`
- **Metrics Reference**: `docs/METRICS_REFERENCE.md`

---

**Last Updated**: December 19, 2024

