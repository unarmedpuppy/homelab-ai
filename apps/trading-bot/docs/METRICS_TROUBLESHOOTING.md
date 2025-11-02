# Metrics Troubleshooting Guide

**Status**: ✅ Complete  
**Last Updated**: December 19, 2024

---

## Common Issues and Solutions

### Issue: Metrics Endpoint Returns 404

**Symptoms**:
- `GET /metrics` returns 404 Not Found
- Prometheus cannot scrape metrics

**Possible Causes**:
1. Metrics are disabled in configuration
2. Route not registered
3. Application not running

**Solutions**:
1. Check `METRICS_ENABLED=true` in environment variables
2. Verify metrics route is registered in `src/api/routes/monitoring.py`
3. Check application logs for startup errors
4. Verify application is running: `docker ps` or `curl http://localhost:8000/health`

---

### Issue: No Metrics Data in Prometheus

**Symptoms**:
- Prometheus shows "no data" for all metrics
- Target status shows "DOWN"

**Possible Causes**:
1. Prometheus cannot reach the application
2. Scrape configuration incorrect
3. Network connectivity issues

**Solutions**:
1. Check Prometheus targets: `http://localhost:9090/targets`
2. Verify scrape config in `prometheus/prometheus.yml`:
   ```yaml
   - job_name: 'trading-bot'
     static_configs:
       - targets: ['bot:8000']
   ```
3. Check network connectivity:
   ```bash
   docker exec trading-bot-prometheus wget -O- http://bot:8000/metrics
   ```
4. Verify service names match in `docker-compose.yml`
5. Check Prometheus logs: `docker logs trading-bot-prometheus`

---

### Issue: High Memory Usage from Metrics

**Symptoms**:
- Application memory usage is high
- OOM (Out of Memory) errors

**Possible Causes**:
1. Too many unique metric labels (high cardinality)
2. Long metric retention
3. Too many metrics being collected

**Solutions**:
1. Review label cardinality - avoid dynamic values in labels (e.g., user IDs, random tokens)
2. Reduce metric retention in Prometheus (default: 15 days)
3. Disable unnecessary metrics if possible
4. Increase application memory limits in Docker

**Best Practices**:
- Use fixed label values where possible
- Aggregate high-cardinality data before exposing as metrics
- Use histograms for distributions instead of many gauges

---

### Issue: Metrics Show Incorrect Values

**Symptoms**:
- Metrics values don't match actual system state
- Zero values when activity is occurring

**Possible Causes**:
1. Metrics not being updated
2. Metric calculation error
3. Time range issues in queries

**Solutions**:
1. Check if metrics are being recorded:
   ```bash
   curl http://localhost:8000/metrics | grep metric_name
   ```
2. Verify metric update code is being called
3. Check application logs for metric recording errors
4. Verify time range in Grafana/Prometheus queries (try "Last 1 hour")

---

### Issue: Grafana Dashboards Show No Data

**Symptoms**:
- Dashboards are empty
- Panels show "No data"

**Possible Causes**:
1. Prometheus data source not configured
2. Time range too narrow
3. Metric names changed
4. Prometheus has no data

**Solutions**:
1. Verify Prometheus datasource in Grafana:
   - Settings → Data Sources → Prometheus
   - URL: `http://prometheus:9090`
   - Test connection
2. Check time range (try "Last 6 hours")
3. Verify metric names match in dashboard queries
4. Check Prometheus for data: `http://localhost:9090/graph`
5. Test query directly in Prometheus:
   ```promql
   up{job="trading-bot"}
   ```

---

### Issue: Alert Rules Not Firing

**Symptoms**:
- Alerts are configured but not triggering
- Prometheus shows alert as "inactive"

**Possible Causes**:
1. Alert rules not loaded
2. Alert condition not met
3. Alertmanager not configured
4. Alert evaluation interval too long

**Solutions**:
1. Check alert rules are loaded:
   - Prometheus → Status → Rules
   - Verify alerts.yml is present
2. Test alert condition manually:
   ```promql
   system_cpu_usage_percent > 90
   ```
3. Verify alert rule syntax in `prometheus/alerts.yml`
4. Check Prometheus logs for rule evaluation errors
5. Configure Alertmanager if using alerting (optional)

---

### Issue: Provider Metrics Not Updating

**Symptoms**:
- `provider_requests_total` not increasing
- `provider_cache_hit_rate` stays at 0

**Possible Causes**:
1. Metrics not integrated in provider code
2. Provider not being used
3. Metrics disabled

**Solutions**:
1. Verify provider integration:
   ```python
   from src.utils.metrics_providers import record_provider_request
   record_provider_request("twitter", success=True, cached=False)
   ```
2. Check provider is actually being called (application logs)
3. Verify `METRICS_ENABLED=true`
4. Check provider metrics endpoint:
   ```bash
   curl http://localhost:8000/metrics | grep provider_requests_total
   ```

---

### Issue: System Metrics Not Available

**Symptoms**:
- `system_cpu_usage_percent` missing
- `system_memory_usage_percent` not updating

**Possible Causes**:
1. `psutil` library not installed
2. Permission issues
3. System metrics not initialized

**Solutions**:
1. Check `psutil` installation:
   ```bash
   docker exec trading-bot-bot pip list | grep psutil
   ```
2. Verify it's in requirements: `requirements/base.txt`
3. Check application logs for import errors
4. Verify system metrics initialization in `src/api/main.py`
5. Check metrics are enabled: `METRICS_ENABLED=true`

**Note**: System metrics will gracefully degrade if `psutil` is unavailable.

---

### Issue: High Cardinality Warnings

**Symptoms**:
- Prometheus warnings about high cardinality
- Slow queries
- High memory usage

**Possible Causes**:
1. Dynamic values in metric labels
2. Too many unique label combinations

**Solutions**:
1. Review metrics with high cardinality:
   ```bash
   curl http://localhost:8000/metrics | grep -E "^[^#]" | cut -d'{' -f1 | sort | uniq -c | sort -rn
   ```
2. Remove or aggregate dynamic labels
3. Use fixed label values
4. Consider logging instead of metrics for high-cardinality data

**Example Fix**:
```python
# Bad: High cardinality (every unique symbol)
counter.labels(symbol=symbol).inc()

# Good: Fixed or aggregated labels
counter.labels(category="equity").inc()
```

---

### Issue: Metric Endpoint Slow

**Symptoms**:
- `/metrics` endpoint takes > 1 second
- Timeouts when scraping

**Possible Causes**:
1. Too many metrics being collected
2. Slow metric registry operations
3. High cardinality

**Solutions**:
1. Check endpoint response time:
   ```bash
   time curl http://localhost:8000/metrics > /dev/null
   ```
2. Reduce number of metrics collected
3. Increase Prometheus scrape timeout:
   ```yaml
   scrape_timeout: 30s
   ```
4. Optimize metric collection code

---

### Issue: Counter Resets to Zero

**Symptoms**:
- Counter metrics reset unexpectedly
- Metrics show zero after restart

**Possible Causes**:
1. Application restart (normal behavior for counters)
2. Prometheus retention expired
3. Metric registry reset

**Solutions**:
1. **This is normal**: Counters reset on application restart. Use `rate()` or `increase()` in queries:
   ```promql
   rate(trades_executed_total[5m])
   ```
2. Use `increase()` for total over time:
   ```promql
   increase(trades_executed_total[1h])
   ```
3. Check Prometheus retention settings

---

## Debugging Steps

### 1. Verify Metrics Endpoint
```bash
curl -v http://localhost:8000/metrics
```

### 2. Check Prometheus Targets
```
http://localhost:9090/targets
```

### 3. Test Prometheus Query
```
http://localhost:9090/graph?g0.expr=up{job="trading-bot"}&g0.tab=0
```

### 4. Check Application Logs
```bash
docker logs trading-bot-bot | grep -i metric
```

### 5. Verify Metrics Configuration
```bash
docker exec trading-bot-bot env | grep METRICS
```

### 6. Check Prometheus Configuration
```bash
docker exec trading-bot-prometheus cat /etc/prometheus/prometheus.yml
```

---

## Getting Help

1. Check application logs: `docker logs trading-bot-bot`
2. Check Prometheus logs: `docker logs trading-bot-prometheus`
3. Review metrics reference: `docs/METRICS_REFERENCE.md`
4. Check dashboard documentation: `docs/GRAFANA_DASHBOARDS.md`

---

## Performance Best Practices

1. **Limit Label Cardinality**: Use fixed label values
2. **Aggregate Data**: Pre-aggregate high-cardinality data
3. **Use Histograms**: For distributions, use histograms not many gauges
4. **Sample Rates**: Consider sampling for very high-frequency metrics
5. **Retention**: Adjust retention based on needs (default: 15 days)

---

**Last Updated**: December 19, 2024

