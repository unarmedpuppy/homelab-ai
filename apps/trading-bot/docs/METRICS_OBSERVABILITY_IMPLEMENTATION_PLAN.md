# Metrics & Observability Pipeline - Implementation Plan

**Status**: 🔄 In Progress  
**Started**: 2024-12-19  
**Agent**: Auto  
**Priority**: CRITICAL  
**Estimated Time**: 60-80 hours

---

## Overview

Implement a comprehensive metrics and observability pipeline using Prometheus for metrics collection, time-series storage, and Grafana for visualization. This enables learning from trading decisions, monitoring system health, and optimizing performance.

**Philosophy**: Every action should emit metrics. No action without metrics collection. Metrics enable learning and process refinement.

---

## Goals

1. **Comprehensive Metrics Collection**: Instrument all critical operations (API, trading, strategies, data providers)
2. **Prometheus Integration**: Export metrics in Prometheus format for scraping
3. **Time-Series Storage**: Store metrics for historical analysis (Prometheus TSDB or InfluxDB)
4. **Grafana Dashboards**: Visual dashboards for real-time and historical monitoring
5. **Automatic Instrumentation**: Middleware and decorators for easy metrics collection
6. **Historical Analysis**: Long-term storage and aggregation for trend analysis

---

## Architecture

### Technology Stack

- **Metrics Library**: `prometheus-client` (Python Prometheus client)
- **Storage**: Prometheus TSDB (via Prometheus server) or InfluxDB
- **Visualization**: Grafana
- **Export**: `/metrics` endpoint (Prometheus format)
- **Instrumentation**: Decorators, middleware, context managers

### Components

1. **Metrics Library** (`src/utils/metrics.py`)
   - Custom metrics utilities
   - Metric registration and management
   - Helper decorators for automatic instrumentation

2. **Prometheus Integration** (`src/api/routes/metrics.py`)
   - `/metrics` endpoint (Prometheus format)
   - Metric aggregation
   - Health check metrics

3. **Middleware** (`src/api/middleware.py` - enhance existing)
   - Automatic API request metrics
   - Request duration tracking
   - Error counting

4. **Instrumentation Points**
   - API endpoints (via middleware)
   - Trading execution
   - Strategy evaluation
   - Signal generation
   - Data provider calls
   - Database operations
   - Error handlers

5. **Grafana Configuration** (`grafana/dashboards/`)
   - Dashboard JSON configurations
   - Dashboard provisioning

6. **Docker Integration** (`docker-compose.yml`)
   - Prometheus service (optional - can use external)
   - Grafana service (optional - can use external)
   - Service configuration

---

## Implementation Phases

### Phase 1: Foundation - Metrics Library & Prometheus Export (12-16 hours)

**Goal**: Core metrics infrastructure and Prometheus export endpoint

**Tasks**:
- [ ] Add `prometheus-client` to `requirements/base.txt`
- [ ] Create `src/utils/metrics.py` with metrics utilities
- [ ] Define metric types (Counter, Histogram, Gauge, Summary)
- [ ] Create metric registry and management functions
- [ ] Create decorators for automatic instrumentation (`@track_metric`, `@track_duration`)
- [ ] Create context manager for tracking durations (`with track_duration(...)`)
- [ ] Create `src/api/routes/metrics.py` with `/metrics` endpoint
- [ ] Integrate metrics endpoint into FastAPI router
- [ ] Add basic system metrics (uptime, Python version)
- [ ] Test Prometheus scraping endpoint

**Files to Create**:
- `src/utils/metrics.py` - Metrics utilities library
- `src/api/routes/metrics.py` - Prometheus metrics endpoint

**Files to Modify**:
- `requirements/base.txt` - Add prometheus-client
- `src/api/main.py` - Register metrics router
- `src/utils/__init__.py` - Export metrics utilities

**Success Criteria**:
- `/metrics` endpoint returns Prometheus-formatted metrics
- Basic system metrics visible
- Prometheus can scrape metrics successfully

---

### Phase 2: API Request Metrics (8-10 hours)

**Goal**: Automatic metrics collection for all API requests

**Tasks**:
- [ ] Enhance `src/api/middleware.py` with Prometheus metrics
- [ ] Track request count by endpoint, method, status code
- [ ] Track request duration (histogram)
- [ ] Track request size (request/response payload sizes)
- [ ] Track error count by endpoint, error type
- [ ] Track request rate (requests per second)
- [ ] Add labels for endpoint, method, status_code
- [ ] Test middleware metrics collection

**Files to Modify**:
- `src/api/middleware.py` - Add Prometheus metrics tracking
- `src/utils/metrics.py` - Add API-specific metrics

**Success Criteria**:
- All API requests automatically emit metrics
- Metrics include endpoint, method, status code labels
- Request duration histogram works correctly

---

### Phase 3: Trading & Strategy Metrics (14-18 hours)

**Goal**: Comprehensive metrics for trading decisions and strategy execution

**Tasks**:
- [ ] Trading Decision Metrics:
  - [ ] Decision time (signal generation → decision)
  - [ ] Signal generation time
  - [ ] Signal count by strategy, type
  - [ ] Signal confidence distribution
  - [ ] Strategy decision breakdown
- [ ] Trade Execution Metrics:
  - [ ] Trades taken by strategy, symbol
  - [ ] Trades rejected with reason
  - [ ] Trade execution time (signal → order execution)
  - [ ] Order fill time
  - [ ] Slippage (actual vs expected price)
  - [ ] Order rejection rate
- [ ] Strategy Metrics:
  - [ ] Strategy execution time
  - [ ] Strategy signal frequency
  - [ ] Strategy utilization (which are active)
  - [ ] Strategy accuracy (win rate, P/L)
- [ ] Instrument `src/core/strategy/base.py`
- [ ] Instrument `src/core/evaluation/evaluator.py`
- [ ] Instrument `src/api/routes/trading.py`

**Files to Modify**:
- `src/core/strategy/base.py` - Add metrics tracking
- `src/core/evaluation/evaluator.py` - Add metrics tracking
- `src/api/routes/trading.py` - Add metrics tracking
- `src/data/brokers/ibkr_client.py` - Add execution metrics

**Files to Create**:
- `src/utils/metrics_trading.py` - Trading-specific metrics helpers

**Success Criteria**:
- All trading decisions emit metrics
- Strategy execution time tracked
- Trade execution metrics captured
- Signal generation time measured

---

### Phase 4: Data Provider Metrics (8-10 hours)

**Goal**: Metrics for all data provider operations

**Tasks**:
- [ ] Track API call count by provider, endpoint
- [ ] Track API response time by provider
- [ ] Track API error rate by provider
- [ ] Track rate limit hits
- [ ] Track cache hit rate by provider
- [ ] Track data freshness (age of cached data)
- [ ] Track provider availability/uptime
- [ ] Instrument existing data providers:
  - [ ] Sentiment providers (Twitter, Reddit, etc.)
  - [ ] Market data providers
  - [ ] Options flow providers
- [ ] Enhance `src/utils/monitoring.py` to integrate with Prometheus

**Files to Modify**:
- `src/data/providers/` - All provider files (add metrics)
- `src/utils/monitoring.py` - Integrate with Prometheus metrics

**Files to Create**:
- `src/utils/metrics_providers.py` - Provider-specific metrics helpers

**Success Criteria**:
- All data provider calls emit metrics
- Cache hit rates tracked
- Provider availability monitored
- Response times measured

---

### Phase 5: System Health & Performance Metrics (6-8 hours)

**Goal**: System-level metrics for health monitoring

**Tasks**:
- [ ] System Health Metrics:
  - [ ] System uptime
  - [ ] Memory usage (RSS, virtual)
  - [ ] CPU usage
  - [ ] Disk usage
  - [ ] Database connection pool usage
  - [ ] Redis performance (latency, hit rates)
- [ ] Error Metrics:
  - [ ] Error count by type, component
  - [ ] Exception rate
  - [ ] Critical errors
  - [ ] Error patterns (trends)
- [ ] Database Metrics:
  - [ ] Query duration by query type
  - [ ] Query count by type
  - [ ] Connection pool usage
  - [ ] Transaction count
- [ ] Instrument database operations
- [ ] Enhance existing `/metrics` endpoint with system metrics

**Files to Modify**:
- `src/utils/metrics.py` - Add system health metrics
- `src/api/routes/metrics.py` - Add system health metrics
- `src/data/database/` - Add database metrics

**Success Criteria**:
- System health metrics available
- Error metrics tracked
- Database metrics captured

---

### Phase 6: Performance & Business Metrics (8-10 hours)

**Goal**: Trading performance and business metrics

**Tasks**:
- [ ] Performance Metrics:
  - [ ] Trade P/L per trade, cumulative
  - [ ] Win rate
  - [ ] Average win/loss
  - [ ] Profit factor
  - [ ] Sharpe ratio (calculated)
  - [ ] Maximum drawdown
  - [ ] Recovery time
  - [ ] Per-strategy performance
- [ ] Business Metrics:
  - [ ] Total portfolio value over time
  - [ ] Daily/monthly P/L
  - [ ] Win/loss streaks
  - [ ] Best/worst trades
  - [ ] Trading activity (trades per day/week/month)
- [ ] Risk Metrics:
  - [ ] Position sizing by confidence
  - [ ] Risk limit hits
  - [ ] Stop loss/take profit triggers
  - [ ] Cash account compliance events
  - [ ] PDT avoidance events
- [ ] Instrument trading execution and portfolio tracking

**Files to Modify**:
- `src/api/routes/trading.py` - Add performance metrics
- `src/data/brokers/ibkr_client.py` - Track trade outcomes
- `src/core/strategy/base.py` - Track strategy performance

**Success Criteria**:
- Performance metrics tracked
- Business metrics available
- Risk metrics captured

---

### Phase 7: Sentiment Metrics (4-6 hours)

**Goal**: Metrics for sentiment analysis operations

**Tasks**:
- [ ] Sentiment Calculation Time
- [ ] Sentiment Provider Usage (which providers used most)
- [ ] Aggregated Sentiment Distribution
- [ ] Divergence Detection Frequency
- [ ] Provider Contribution (weight breakdown)
- [ ] Instrument `src/data/providers/sentiment/aggregator.py`

**Files to Modify**:
- `src/data/providers/sentiment/aggregator.py` - Add metrics
- `src/data/providers/sentiment/` - Individual providers

**Success Criteria**:
- Sentiment metrics tracked
- Provider usage visible
- Calculation times measured

---

### Phase 8: Docker & Infrastructure Setup (4-6 hours)

**Goal**: Docker services for Prometheus and Grafana (optional - can use external)

**Tasks**:
- [ ] Add Prometheus service to `docker-compose.yml` (optional)
- [ ] Add Grafana service to `docker-compose.yml` (optional)
- [ ] Create Prometheus configuration (`prometheus/prometheus.yml`)
- [ ] Create Grafana provisioning (`grafana/provisioning/`)
- [ ] Create initial Grafana dashboards:
  - [ ] Main Dashboard (overview)
  - [ ] Trading Dashboard
  - [ ] Strategy Dashboard
  - [ ] System Health Dashboard
  - [ ] Sentiment Dashboard
  - [ ] Risk Dashboard
  - [ ] Error Dashboard
- [ ] Add volume mounts for persistence
- [ ] Update `env.template` with metrics configuration

**Files to Create**:
- `prometheus/prometheus.yml` - Prometheus configuration
- `grafana/provisioning/datasources/prometheus.yml` - Grafana datasource
- `grafana/provisioning/dashboards/dashboard.yml` - Dashboard provisioning
- `grafana/dashboards/*.json` - Dashboard configurations

**Files to Modify**:
- `docker-compose.yml` - Add Prometheus and Grafana services
- `env.template` - Add metrics configuration

**Success Criteria**:
- Prometheus and Grafana services running (if using Docker)
- Dashboards available and functional
- Metrics visible in Grafana

---

### Phase 9: Testing & Documentation (6-8 hours)

**Goal**: Comprehensive testing and documentation

**Tasks**:
- [ ] Create test script (`scripts/test_metrics.py`)
- [ ] Test metrics collection:
  - [ ] API request metrics
  - [ ] Trading metrics
  - [ ] Strategy metrics
  - [ ] Provider metrics
  - [ ] System metrics
- [ ] Test Prometheus scraping
- [ ] Test Grafana dashboards
- [ ] Test metrics accuracy (verify counts, durations)
- [ ] Performance testing (metrics overhead)
- [ ] Create documentation:
  - [ ] Metrics reference guide
  - [ ] Dashboard guide
  - [ ] Configuration guide
  - [ ] Troubleshooting guide
- [ ] Update `docs/API_DOCUMENTATION.md` with metrics endpoint

**Files to Create**:
- `scripts/test_metrics.py` - Metrics testing script
- `docs/METRICS_GUIDE.md` - Metrics documentation
- `docs/GRAFANA_DASHBOARDS.md` - Dashboard documentation

**Files to Modify**:
- `docs/API_DOCUMENTATION.md` - Add metrics endpoint docs

**Success Criteria**:
- All metrics tested and verified
- Documentation complete
- Performance overhead acceptable

---

## Metric Categories & Definitions

### Request & API Metrics

- `http_requests_total` (Counter): Total API requests by endpoint, method, status_code
- `http_request_duration_seconds` (Histogram): Request duration by endpoint, method
- `http_request_size_bytes` (Histogram): Request payload size by endpoint
- `http_response_size_bytes` (Histogram): Response payload size by endpoint
- `http_errors_total` (Counter): Error count by endpoint, error_type

### Trading Decision Metrics

- `trading_decision_duration_seconds` (Histogram): Time from signal to decision
- `signal_generation_duration_seconds` (Histogram): Time to generate signal
- `signals_generated_total` (Counter): Signals by strategy, signal_type
- `signal_confidence` (Histogram): Signal confidence distribution

### Trade Execution Metrics

- `trades_executed_total` (Counter): Trades by strategy, symbol, side
- `trades_rejected_total` (Counter): Rejected trades by reason
- `trade_execution_duration_seconds` (Histogram): Signal to execution time
- `order_fill_duration_seconds` (Histogram): Order placement to fill time
- `slippage_amount` (Histogram): Price slippage by symbol

### Strategy Metrics

- `strategy_evaluation_duration_seconds` (Histogram): Strategy evaluation time by strategy
- `strategy_signals_per_hour` (Gauge): Signal frequency by strategy
- `strategy_win_rate` (Gauge): Win rate by strategy
- `strategy_profit_loss` (Gauge): P/L by strategy

### Data Provider Metrics

- `provider_api_calls_total` (Counter): API calls by provider, endpoint
- `provider_api_duration_seconds` (Histogram): Response time by provider
- `provider_api_errors_total` (Counter): Errors by provider, error_type
- `provider_rate_limit_hits_total` (Counter): Rate limit hits by provider
- `provider_cache_hit_rate` (Gauge): Cache hit rate by provider
- `provider_data_freshness_seconds` (Gauge): Age of cached data by provider

### System Health Metrics

- `system_uptime_seconds` (Gauge): System uptime
- `system_memory_usage_bytes` (Gauge): Memory usage by type
- `system_cpu_usage_percent` (Gauge): CPU usage
- `system_disk_usage_bytes` (Gauge): Disk usage
- `database_query_duration_seconds` (Histogram): Query time by query_type
- `database_connection_pool_usage` (Gauge): Connection pool usage
- `redis_latency_seconds` (Histogram): Redis operation latency
- `redis_cache_hit_rate` (Gauge): Redis cache hit rate

### Error Metrics

- `errors_total` (Counter): Errors by type, component
- `exceptions_total` (Counter): Exceptions by type, component
- `critical_errors_total` (Counter): Critical errors

### Business Metrics

- `portfolio_value` (Gauge): Current portfolio value
- `daily_profit_loss` (Gauge): Daily P/L
- `monthly_profit_loss` (Gauge): Monthly P/L
- `win_streak` (Gauge): Current win streak
- `loss_streak` (Gauge): Current loss streak

---

## Implementation Patterns

### Decorator Pattern for Function Instrumentation

```python
from src.utils.metrics import track_duration, track_call_count

@track_duration('strategy_evaluation_duration_seconds', labels=['strategy'])
@track_call_count('strategy_evaluations_total', labels=['strategy'])
def evaluate_strategy(strategy, symbol):
    # Strategy evaluation logic
    pass
```

### Context Manager for Duration Tracking

```python
from src.utils.metrics import track_duration_context

with track_duration_context('trade_execution_duration_seconds', labels={'strategy': 'sma'}):
    # Trade execution logic
    pass
```

### Manual Metric Updates

```python
from src.utils.metrics import get_metric

trades_executed = get_metric('trades_executed_total')
trades_executed.labels(strategy='sma', symbol='AAPL', side='buy').inc()
```

### Middleware for Automatic API Metrics

```python
# In middleware.py
@router.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).inc()
    
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response
```

---

## Configuration

### Environment Variables

```bash
# Metrics Configuration
METRICS_ENABLED=true
METRICS_PORT=9090
PROMETHEUS_ENABLED=true

# Prometheus Configuration (if using Docker)
PROMETHEUS_HOST=prometheus
PROMETHEUS_PORT=9090

# Grafana Configuration (if using Docker)
GRAFANA_HOST=grafana
GRAFANA_PORT=3000
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin
```

### Settings (src/config/settings.py)

```python
class MetricsSettings(BaseSettings):
    """Metrics and observability configuration"""
    enabled: bool = Field(default=True, description="Enable metrics collection")
    prometheus_enabled: bool = Field(default=True, description="Enable Prometheus export")
    metrics_port: int = Field(default=9090, description="Port for metrics endpoint")
    
    class Config:
        env_prefix = "METRICS_"
```

---

## Dependencies

### New Dependencies

- `prometheus-client==0.19.0` (already in requirements/base.txt as `prometheus-client==0.19.0`)

### Optional Dependencies (for Docker setup)

- Prometheus Docker image (via docker-compose)
- Grafana Docker image (via docker-compose)

---

## Testing Strategy

1. **Unit Tests**: Test metric collection and export
2. **Integration Tests**: Test Prometheus scraping
3. **Performance Tests**: Measure metrics overhead
4. **Accuracy Tests**: Verify metric counts and values
5. **Dashboard Tests**: Verify Grafana dashboards display correctly

---

## Success Criteria

### Phase 1 Success
- ✅ `/metrics` endpoint returns Prometheus-formatted metrics
- ✅ Basic system metrics visible
- ✅ Prometheus can scrape metrics

### Overall Success
- ✅ All critical operations emit metrics
- ✅ Metrics available in Prometheus
- ✅ Grafana dashboards functional
- ✅ Historical data stored
- ✅ Metrics enable learning and optimization
- ✅ Performance overhead < 5%

---

## Next Steps

1. ✅ **Claim task in PROJECT_TODO.md** (DONE)
2. ⏳ **Start Phase 1**: Foundation - Metrics Library & Prometheus Export
3. ⏳ Create task tracking document
4. ⏳ Begin implementation

---

**Last Updated**: 2024-12-19  
**Status**: Planning Complete, Ready for Implementation
