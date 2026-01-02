# Local AI Router - Prometheus Metrics Reference

> **⚠️ MIGRATION NOTICE (January 2025)**
> 
> The Local AI stack has been migrated to the [homelab-ai](https://github.com/unarmedpuppy/homelab-ai) repository.
> 
> - **Source code**: Now in `homelab-ai` repo (llm-router, dashboard, llm-manager)
> - **Deployment**: Use `apps/homelab-ai/docker-compose.yml` to pull pre-built Harbor images
> - **Old code**: Moved to `inactive/local-ai-router/` for reference only
> 
> This documentation remains valid for the metrics reference - the metrics system is unchanged.

Quick reference for the Prometheus metrics exposed by the Local AI Router.

**Related**: [homelab-ai repo](https://github.com/unarmedpuppy/homelab-ai) | [Grafana Dashboard](#grafana-dashboard)

## Overview

The Local AI Router exposes Prometheus metrics at `/metrics` for monitoring request rates, latency, provider health, and routing decisions.

**Endpoint**: `http://local-ai-router:8000/metrics`  
**Scrape Interval**: 10s (configured in Prometheus)

## Metrics Reference

### Request Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `local_ai_requests_total` | Counter | `endpoint`, `model`, `provider`, `status` | Total number of requests to the router |
| `local_ai_request_duration_seconds` | Histogram | `endpoint`, `provider` | Request duration in seconds |
| `local_ai_tokens_total` | Counter | `provider`, `type` | Total tokens processed (type: `prompt` or `completion`) |

**Request Duration Buckets**: 0.1s, 0.5s, 1s, 2.5s, 5s, 10s, 30s, 60s, 120s, 300s

### Provider Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `local_ai_provider_health` | Gauge | `provider` | Provider health status (1=healthy, 0=unhealthy) |
| `local_ai_provider_active_requests` | Gauge | `provider` | Current active requests per provider |
| `local_ai_provider_max_concurrent` | Gauge | `provider` | Maximum concurrent requests per provider |
| `local_ai_provider_consecutive_failures` | Gauge | `provider` | Number of consecutive health check failures |
| `local_ai_provider_response_time_ms` | Gauge | `provider` | Last health check response time in milliseconds |

### Routing Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `local_ai_routing_decisions_total` | Counter | `requested_model`, `selected_provider`, `selected_model` | Number of routing decisions by type |
| `local_ai_failover_total` | Counter | `from_provider`, `to_provider`, `reason` | Number of failovers from one provider to another |

### Error Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `local_ai_errors_total` | Counter | `endpoint`, `error_type` | Total number of errors |

### Memory/Conversation Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `local_ai_conversations_total` | Gauge | - | Total number of conversations in memory |
| `local_ai_messages_total` | Gauge | - | Total number of messages in memory |

### System Info

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `local_ai_router_info` | Info | `version`, `name` | Router version and configuration info |

## Label Values

### Providers
- `3090` - Gaming PC (RTX 3090)
- `3070` - Home Server (RTX 3070)
- `opencode` - OpenCode service

### Endpoints
- `/v1/chat/completions` - Chat completions
- `/v1/completions` - Text completions
- `/v1/embeddings` - Embeddings

### Status
- `success` - Request completed successfully
- `error` - Request failed
- `timeout` - Request timed out

### Error Types
- `provider_unavailable` - No healthy provider available
- `timeout` - Request timeout
- `rate_limit` - Rate limit exceeded
- `invalid_request` - Invalid request format
- `internal_error` - Internal server error

## Example Queries

### Request Rate (per minute)
```promql
rate(local_ai_requests_total[1m]) * 60
```

### Average Request Duration by Provider
```promql
rate(local_ai_request_duration_seconds_sum[5m]) / rate(local_ai_request_duration_seconds_count[5m])
```

### Token Throughput by Provider
```promql
rate(local_ai_tokens_total[5m]) * 60
```

### Provider Health Status
```promql
local_ai_provider_health
```

### Error Rate
```promql
rate(local_ai_errors_total[5m]) * 60
```

### 95th Percentile Latency
```promql
histogram_quantile(0.95, rate(local_ai_request_duration_seconds_bucket[5m]))
```

### Routing Distribution
```promql
sum by (selected_provider) (rate(local_ai_routing_decisions_total[5m]))
```

### Failover Events
```promql
sum by (reason) (rate(local_ai_failover_total[5m]))
```

## Grafana Dashboard

**Dashboard**: Local AI Router  
**Location**: Grafana > Dashboards > Local AI Router  
**URL**: https://grafana.server.unarmedpuppy.com

### Panels

| Panel | Description | Metric |
|-------|-------------|--------|
| Request Rate | Requests per minute | `local_ai_requests_total` |
| Latency (P95) | 95th percentile response time | `local_ai_request_duration_seconds` |
| Provider Health | Health status of all providers | `local_ai_provider_health` |
| Active Requests | Current requests per provider | `local_ai_provider_active_requests` |
| Token Throughput | Tokens processed per minute | `local_ai_tokens_total` |
| Error Rate | Errors per minute | `local_ai_errors_total` |
| Routing Distribution | Requests by provider | `local_ai_routing_decisions_total` |
| Memory Stats | Conversations and messages count | `local_ai_conversations_total`, `local_ai_messages_total` |

## Architecture

```
                                   ┌─────────────────┐
                                   │  Grafana        │
                                   │  Dashboard      │
                                   └────────┬────────┘
                                            │
                                            ▼
┌─────────────────┐              ┌─────────────────┐
│ Local AI Router │◄─────────────│   Prometheus    │
│  :8000/metrics  │   scrape     │     :9090       │
└─────────────────┘   (10s)      └─────────────────┘
```

### Data Flow

1. **Local AI Router** exposes metrics at `/metrics`
2. **Prometheus** scrapes metrics every 10 seconds
3. **Grafana** queries Prometheus and displays dashboards

### Configuration Files

| Component | File | Purpose |
|-----------|------|---------|
| Prometheus | `apps/grafana/config/prometheus/prometheus.yml` | Scrape configuration |
| Metrics | `apps/local-ai-router/prometheus_metrics.py` | Metric definitions |
| Router | `apps/local-ai-router/router.py` | `/metrics` endpoint |
| Dashboard | `apps/grafana/config/dashboards/local-ai-router.json` | Grafana dashboard JSON |

## Instrumentation Points

Metrics are recorded at these points in the code:

| Location | Metrics Updated |
|----------|-----------------|
| `dependencies.py:get_provider()` | `REQUEST_COUNT`, `REQUEST_DURATION`, `TOKENS_TOTAL` |
| `router.py:health_check()` | `PROVIDER_HEALTH`, `PROVIDER_RESPONSE_TIME` |
| `router.py:chat_completions()` | `ROUTING_DECISIONS`, `FAILOVER_COUNT`, `ERROR_COUNT` |
| `memory.py:save_conversation()` | `CONVERSATIONS_TOTAL`, `MESSAGES_TOTAL` |

## Adding New Metrics

To add a new metric:

1. Define in `prometheus_metrics.py`:
```python
NEW_METRIC = Counter(
    'local_ai_new_metric_total',
    'Description of the metric',
    ['label1', 'label2']
)
```

2. Create a helper function:
```python
def record_new_metric(label1: str, label2: str):
    NEW_METRIC.labels(label1=label1, label2=label2).inc()
```

3. Call from the relevant code path
4. Add to Grafana dashboard

## Troubleshooting

### Metrics Not Appearing

1. Check if local-ai-router is running:
```bash
curl http://localhost:8012/health
```

2. Check if metrics endpoint is accessible:
```bash
curl http://localhost:8012/metrics
```

3. Check Prometheus targets:
```bash
curl http://localhost:9090/api/v1/targets
```

4. Verify scrape config in `prometheus.yml`:
```yaml
- job_name: 'local-ai-router'
  static_configs:
    - targets: ['local-ai-router:8000']
```

### Dashboard Shows "No Data"

1. Verify Prometheus datasource in Grafana
2. Check time range (metrics may not exist for selected range)
3. Verify metric names match queries
4. Check if the router has received any requests

### High Cardinality Warning

If you see cardinality warnings:
- Review label usage (avoid high-cardinality labels like request IDs)
- Consider aggregating or removing unnecessary labels
- Use recording rules for frequently-queried metrics
