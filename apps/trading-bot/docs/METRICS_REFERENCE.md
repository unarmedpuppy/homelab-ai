# Metrics Reference Guide

**Status**: Complete  
**Last Updated**: December 19, 2024

## Overview

This document provides a comprehensive reference for all Prometheus metrics exposed by the Trading Bot application. All metrics are available at `/api/monitoring/metrics` endpoint and follow Prometheus naming conventions.

## Metric Categories

### 1. System Metrics

#### `system_uptime_seconds` (Gauge)
- **Description**: Application uptime in seconds
- **Labels**: None
- **Example**: `system_uptime_seconds 3600.5`

#### `system_python_version_info` (Gauge)
- **Description**: Python version information
- **Labels**: `version`, `version_string`
- **Example**: `system_python_version_info{version="3.11",version_string="3.11.0"} 3.11`

#### `system_application_info` (Gauge)
- **Description**: Application version and environment
- **Labels**: `version`, `environment`
- **Example**: `system_application_info{version="2.0.0",environment="production"} 1.0`

#### `system_memory_usage_bytes` (Gauge)
- **Description**: System memory usage in bytes
- **Labels**: `type` (rss, virtual, available, total, used, free)
- **Example**: `system_memory_usage_bytes{type="used"} 524288000`

#### `system_memory_usage_percent` (Gauge)
- **Description**: System memory usage percentage
- **Labels**: None
- **Example**: `system_memory_usage_percent 45.2`

#### `system_cpu_usage_percent` (Gauge)
- **Description**: System CPU usage percentage
- **Labels**: None
- **Example**: `system_cpu_usage_percent 23.5`

#### `system_disk_usage_bytes` (Gauge)
- **Description**: System disk usage in bytes
- **Labels**: `device`, `mountpoint`, `type` (used, free, total)
- **Example**: `system_disk_usage_bytes{device="/dev/sda1",mountpoint="/",type="used"} 10737418240`

#### `system_disk_usage_percent` (Gauge)
- **Description**: System disk usage percentage
- **Labels**: `device`, `mountpoint`
- **Example**: `system_disk_usage_percent{device="/dev/sda1",mountpoint="/"} 65.3`

---

### 2. API Request Metrics

#### `http_requests_total` (Counter)
- **Description**: Total number of HTTP requests
- **Labels**: `method`, `endpoint`, `status_code`
- **Example**: `http_requests_total{method="GET",endpoint="/api/monitoring/health",status_code="200"} 150`

#### `http_request_duration_seconds` (Histogram)
- **Description**: HTTP request duration in seconds
- **Labels**: `method`, `endpoint`
- **Buckets**: 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0
- **Example**: `http_request_duration_seconds_bucket{method="GET",endpoint="/api/sentiment",le="0.1"} 45`

#### `http_request_size_bytes` (Histogram)
- **Description**: HTTP request size in bytes
- **Labels**: `method`, `endpoint`
- **Example**: `http_request_size_bytes_bucket{method="POST",endpoint="/api/trading",le="1000"} 20`

#### `http_response_size_bytes` (Histogram)
- **Description**: HTTP response size in bytes
- **Labels**: `method`, `endpoint`
- **Example**: `http_response_size_bytes_bucket{method="GET",endpoint="/api/sentiment",le="5000"} 30`

#### `http_errors_total` (Counter)
- **Description**: Total number of HTTP errors
- **Labels**: `method`, `endpoint`, `status_code`, `error_type`
- **Example**: `http_errors_total{method="GET",endpoint="/api/data",status_code="500",error_type="server_error"} 2`

---

### 3. Trading & Strategy Metrics

#### `trades_executed_total` (Counter)
- **Description**: Total number of trades executed
- **Labels**: `strategy`, `symbol`, `side` (BUY/SELL)
- **Example**: `trades_executed_total{strategy="SMAStrategy",symbol="AAPL",side="BUY"} 5`

#### `trades_rejected_total` (Counter)
- **Description**: Total number of trades rejected
- **Labels**: `reason`
- **Example**: `trades_rejected_total{reason="risk_limit"} 3`

#### `trade_execution_duration_seconds` (Histogram)
- **Description**: Time to execute a trade (signal to order execution)
- **Labels**: `strategy`, `symbol`
- **Example**: `trade_execution_duration_seconds_bucket{strategy="SMAStrategy",symbol="AAPL",le="1.0"} 4`

#### `signals_generated_total` (Counter)
- **Description**: Total number of trading signals generated
- **Labels**: `strategy`, `type` (BUY/SELL/HOLD), `symbol`
- **Example**: `signals_generated_total{strategy="SMAStrategy",type="BUY",symbol="AAPL"} 12`

#### `signal_confidence` (Histogram)
- **Description**: Signal confidence score distribution
- **Labels**: `strategy`, `type`
- **Buckets**: 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0
- **Example**: `signal_confidence_bucket{strategy="SMAStrategy",type="BUY",le="0.8"} 8`

#### `strategy_evaluation_duration_seconds` (Histogram)
- **Description**: Time to evaluate a strategy
- **Labels**: `strategy`
- **Example**: `strategy_evaluation_duration_seconds_bucket{strategy="SMAStrategy",le="0.5"} 25`

#### `strategy_win_rate` (Gauge)
- **Description**: Win rate for each strategy (0.0 to 1.0)
- **Labels**: `strategy`
- **Example**: `strategy_win_rate{strategy="SMAStrategy"} 0.65`

---

### 4. Data Provider Metrics

#### `provider_requests_total` (Counter)
- **Description**: Total number of provider API requests
- **Labels**: `provider`, `status` (success, failure, cached)
- **Example**: `provider_requests_total{provider="twitter",status="success"} 150`

#### `provider_response_time_seconds` (Histogram)
- **Description**: Provider API response time in seconds
- **Labels**: `provider`
- **Example**: `provider_response_time_seconds_bucket{provider="twitter",le="1.0"} 120`

#### `provider_errors_total` (Counter)
- **Description**: Total number of provider errors
- **Labels**: `provider`, `error_type`
- **Example**: `provider_errors_total{provider="twitter",error_type="rate_limit"} 2`

#### `provider_rate_limit_hits_total` (Counter)
- **Description**: Total number of rate limit hits
- **Labels**: `provider`
- **Example**: `provider_rate_limit_hits_total{provider="twitter"} 5`

#### `provider_cache_hit_rate` (Gauge)
- **Description**: Cache hit rate per provider (0.0 to 1.0)
- **Labels**: `provider`
- **Example**: `provider_cache_hit_rate{provider="twitter"} 0.75`

---

### 5. Sentiment Metrics

#### `sentiment_calculations_total` (Counter)
- **Description**: Total number of sentiment calculations
- **Labels**: `symbol`, `result` (success, failed, cached)
- **Example**: `sentiment_calculations_total{symbol="AAPL",result="success"} 50`

#### `sentiment_calculation_duration_seconds` (Histogram)
- **Description**: Time to calculate sentiment by provider
- **Labels**: `provider`
- **Example**: `sentiment_calculation_duration_seconds_bucket{provider="twitter",le="1.0"} 45`

#### `sentiment_provider_usage_total` (Counter)
- **Description**: Number of times each sentiment provider was used
- **Labels**: `provider`, `symbol`, `status`
- **Example**: `sentiment_provider_usage_total{provider="twitter",symbol="AAPL",status="success"} 30`

#### `sentiment_score_distribution` (Histogram)
- **Description**: Distribution of aggregated sentiment scores
- **Labels**: `symbol`
- **Buckets**: -1.0, -0.8, -0.6, -0.4, -0.2, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0
- **Example**: `sentiment_score_distribution_bucket{symbol="AAPL",le="0.4"} 20`

#### `sentiment_divergence_detected_total` (Counter)
- **Description**: Number of times sentiment divergence was detected
- **Labels**: `symbol`, `severity` (low, medium, high)
- **Example**: `sentiment_divergence_detected_total{symbol="AAPL",severity="medium"} 3`

---

### 6. Portfolio & Business Metrics

#### `portfolio_total_pnl` (Gauge)
- **Description**: Total portfolio profit/loss
- **Labels**: None
- **Example**: `portfolio_total_pnl 1250.50`

#### `portfolio_daily_pnl` (Gauge)
- **Description**: Daily portfolio profit/loss
- **Labels**: None
- **Example**: `portfolio_daily_pnl 125.25`

#### `portfolio_monthly_pnl` (Gauge)
- **Description**: Monthly portfolio profit/loss
- **Labels**: None
- **Example**: `portfolio_monthly_pnl 1250.50`

#### `portfolio_total_value` (Gauge)
- **Description**: Total portfolio value
- **Labels**: None
- **Example**: `portfolio_total_value 50125.50`

---

### 7. Risk Metrics

#### `risk_max_drawdown` (Gauge)
- **Description**: Maximum drawdown percentage
- **Labels**: None
- **Example**: `risk_max_drawdown -5.2`

#### `risk_daily_loss_limit` (Gauge)
- **Description**: Daily loss limit (absolute value)
- **Labels**: None
- **Example**: `risk_daily_loss_limit 500.0`

#### `risk_position_size_limit` (Gauge)
- **Description**: Maximum position size
- **Labels**: None
- **Example**: `risk_position_size_limit 10000.0`

#### `risk_per_trade` (Gauge)
- **Description**: Maximum risk per trade
- **Labels**: None
- **Example**: `risk_per_trade 200.0`

---

### 8. Error Metrics

#### `errors_total` (Counter)
- **Description**: Total number of errors by type and component
- **Labels**: `type`, `component`
- **Example**: `errors_total{type="validation_error",component="api"} 5`

#### `exceptions_total` (Counter)
- **Description**: Total number of exceptions by type and component
- **Labels**: `exception_type`, `component`
- **Example**: `exceptions_total{exception_type="ValueError",component="strategy"} 2`

#### `critical_errors_total` (Counter)
- **Description**: Total number of critical errors by component
- **Labels**: `component`
- **Example**: `critical_errors_total{component="trading"} 1`

---

## Common Queries

### Request Rate
```promql
rate(http_requests_total[5m])
```

### Error Rate
```promql
rate(http_errors_total[5m])
```

### Average Response Time
```promql
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

### Cache Hit Rate
```promql
provider_cache_hit_rate{provider="twitter"}
```

### Strategy Win Rate
```promql
strategy_win_rate{strategy="SMAStrategy"}
```

### Portfolio P/L
```promql
portfolio_total_pnl
```

### System Memory Usage
```promql
system_memory_usage_percent
```

---

## Prometheus Configuration

The metrics endpoint is configured in `prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'trading-bot'
    scrape_interval: 15s
    metrics_path: '/api/monitoring/metrics'
    static_configs:
      - targets: ['bot:8000']
```

---

## Accessing Metrics

### Via HTTP
```bash
curl http://localhost:8000/api/monitoring/metrics
```

### Via Prometheus
- Prometheus UI: `http://localhost:9090`
- Query metrics: `http://localhost:9090/graph`

### Via Grafana
- Grafana UI: `http://localhost:3000`
- Pre-configured dashboards available
- Datasource: Prometheus (auto-configured)

---

## Troubleshooting

### Metrics Not Appearing

1. **Check metrics are enabled**: Set `METRICS_ENABLED=true`
2. **Verify endpoint**: `curl http://localhost:8000/api/monitoring/metrics`
3. **Check Prometheus targets**: `http://localhost:9090/targets`
4. **Check application logs** for metrics errors

### Metric Values Not Changing

1. **Verify operations are being performed** (API calls, trades, etc.)
2. **Check metric labels** match expected format
3. **Verify no caching** is preventing updates

### High Cardinality Warnings

1. **Review metric labels** - avoid high-cardinality labels (IDs, timestamps)
2. **Use metric relabeling** in Prometheus config if needed
3. **Consider metric aggregation** for high-volume metrics

---

## Best Practices

1. **Metric Naming**: Follow Prometheus conventions (snake_case, units)
2. **Label Cardinality**: Limit labels to avoid high cardinality
3. **Histogram Buckets**: Choose appropriate buckets for your use case
4. **Error Handling**: Metrics should never cause application failures
5. **Performance**: Metrics collection overhead should be minimal

---

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
- [Grafana Dashboards Guide](docs/GRAFANA_DASHBOARDS.md)
- [Metrics Implementation Plan](docs/METRICS_OBSERVABILITY_IMPLEMENTATION_PLAN.md)
