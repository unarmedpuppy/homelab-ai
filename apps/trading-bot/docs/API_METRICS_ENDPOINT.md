# Metrics Endpoint Documentation

**Status**: ✅ Complete  
**Last Updated**: December 19, 2024

---

## Endpoint: `/metrics`

Exposes application metrics in Prometheus exposition format.

### Request

```http
GET /metrics
```

### Response

**Status Code**: `200 OK`

**Content-Type**: `text/plain; version=0.0.4; charset=utf-8`

**Response Body**: Prometheus metrics in text format

### Example Response

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/health",status_code="200"} 1523

# HELP system_cpu_usage_percent CPU usage percentage
# TYPE system_cpu_usage_percent gauge
system_cpu_usage_percent 45.2

# HELP portfolio_total_pnl Total portfolio profit/loss
# TYPE portfolio_total_pnl gauge
portfolio_total_pnl 1250.75
```

### Authentication

No authentication required (internal monitoring endpoint).

### Rate Limiting

Not rate limited (metrics endpoint should be accessible to Prometheus).

### Configuration

Metrics can be disabled via environment variable:

```bash
METRICS_ENABLED=false
```

When disabled, the endpoint returns an empty response.

### Metrics Available

See `docs/METRICS_REFERENCE.md` for complete list of available metrics.

### Scraping

Configure Prometheus to scrape this endpoint:

```yaml
scrape_configs:
  - job_name: 'trading-bot'
    static_configs:
      - targets: ['bot:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Error Handling

- **404**: Metrics disabled or route not registered
- **500**: Error generating metrics (check application logs)

### Related Documentation

- **Metrics Reference**: `docs/METRICS_REFERENCE.md`
- **Troubleshooting**: `docs/METRICS_TROUBLESHOOTING.md`
- **Grafana Dashboards**: `docs/GRAFANA_DASHBOARDS.md`

---

**Last Updated**: December 19, 2024

