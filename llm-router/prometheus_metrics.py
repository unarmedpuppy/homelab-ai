"""
Prometheus metrics for Local AI Router.

Exposes metrics for monitoring request rates, latency, provider health,
and routing decisions.
"""
from prometheus_client import Counter, Histogram, Gauge, Info, REGISTRY
from prometheus_client.exposition import generate_latest, CONTENT_TYPE_LATEST
from functools import wraps
import time
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# Request Metrics
# ============================================================================

REQUEST_COUNT = Counter(
    'local_ai_requests_total',
    'Total number of requests to the router',
    ['endpoint', 'model', 'provider', 'status']
)

REQUEST_DURATION = Histogram(
    'local_ai_request_duration_seconds',
    'Request duration in seconds',
    ['endpoint', 'provider'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)

TOKENS_TOTAL = Counter(
    'local_ai_tokens_total',
    'Total tokens processed',
    ['provider', 'type']  # type: prompt, completion
)

# ============================================================================
# Provider Metrics
# ============================================================================

PROVIDER_HEALTH = Gauge(
    'local_ai_provider_health',
    'Provider health status (1=healthy, 0=unhealthy)',
    ['provider']
)

PROVIDER_ACTIVE_REQUESTS = Gauge(
    'local_ai_provider_active_requests',
    'Current active requests per provider',
    ['provider']
)

PROVIDER_MAX_CONCURRENT = Gauge(
    'local_ai_provider_max_concurrent',
    'Maximum concurrent requests per provider',
    ['provider']
)

PROVIDER_CONSECUTIVE_FAILURES = Gauge(
    'local_ai_provider_consecutive_failures',
    'Number of consecutive health check failures',
    ['provider']
)

PROVIDER_RESPONSE_TIME = Gauge(
    'local_ai_provider_response_time_ms',
    'Last health check response time in milliseconds',
    ['provider']
)

# ============================================================================
# Routing Metrics
# ============================================================================

ROUTING_DECISIONS = Counter(
    'local_ai_routing_decisions_total',
    'Number of routing decisions by type',
    ['requested_model', 'selected_provider', 'selected_model']
)

FAILOVER_COUNT = Counter(
    'local_ai_failover_total',
    'Number of failovers from one provider to another',
    ['from_provider', 'to_provider', 'reason']
)

COMPLEXITY_CLASSIFICATIONS = Counter(
    'local_ai_complexity_classifications_total',
    'Request complexity classifications',
    ['tier', 'primary_signal']
)

# ============================================================================
# Error Metrics
# ============================================================================

ERROR_COUNT = Counter(
    'local_ai_errors_total',
    'Total number of errors',
    ['endpoint', 'error_type']
)

# ============================================================================
# Memory/Conversation Metrics
# ============================================================================

CONVERSATIONS_TOTAL = Gauge(
    'local_ai_conversations_total',
    'Total number of conversations in memory'
)

MESSAGES_TOTAL = Gauge(
    'local_ai_messages_total',
    'Total number of messages in memory'
)

# ============================================================================
# System Info
# ============================================================================

ROUTER_INFO = Info(
    'local_ai_router',
    'Router version and configuration info'
)


def init_router_info(version: str = "1.0.0"):
    """Initialize router info metric."""
    ROUTER_INFO.info({
        'version': version,
        'name': 'local-ai-router'
    })


# ============================================================================
# Helper Functions
# ============================================================================

def get_metrics() -> bytes:
    """Generate Prometheus metrics output."""
    return generate_latest(REGISTRY)


def get_content_type() -> str:
    """Get Prometheus content type."""
    return CONTENT_TYPE_LATEST


def record_request(
    endpoint: str,
    model: str,
    provider: str,
    status: str,
    duration_seconds: float,
    prompt_tokens: int = 0,
    completion_tokens: int = 0
):
    """Record a completed request."""
    REQUEST_COUNT.labels(
        endpoint=endpoint,
        model=model,
        provider=provider,
        status=status
    ).inc()
    
    REQUEST_DURATION.labels(
        endpoint=endpoint,
        provider=provider
    ).observe(duration_seconds)
    
    if prompt_tokens > 0:
        TOKENS_TOTAL.labels(provider=provider, type='prompt').inc(prompt_tokens)
    if completion_tokens > 0:
        TOKENS_TOTAL.labels(provider=provider, type='completion').inc(completion_tokens)


def record_error(endpoint: str, error_type: str):
    """Record an error."""
    ERROR_COUNT.labels(endpoint=endpoint, error_type=error_type).inc()


def record_routing_decision(requested_model: str, selected_provider: str, selected_model: str):
    """Record a routing decision."""
    ROUTING_DECISIONS.labels(
        requested_model=requested_model,
        selected_provider=selected_provider,
        selected_model=selected_model
    ).inc()


def record_failover(from_provider: str, to_provider: str, reason: str):
    """Record a failover event."""
    FAILOVER_COUNT.labels(
        from_provider=from_provider,
        to_provider=to_provider,
        reason=reason
    ).inc()


def record_complexity_classification(tier: str, primary_signal: str):
    """Record a complexity classification decision."""
    COMPLEXITY_CLASSIFICATIONS.labels(
        tier=tier,
        primary_signal=primary_signal,
    ).inc()


def update_provider_metrics(
    provider_id: str,
    is_healthy: bool,
    active_requests: int,
    max_concurrent: int,
    consecutive_failures: int = 0,
    response_time_ms: float = 0
):
    """Update provider metrics."""
    PROVIDER_HEALTH.labels(provider=provider_id).set(1 if is_healthy else 0)
    PROVIDER_ACTIVE_REQUESTS.labels(provider=provider_id).set(active_requests)
    PROVIDER_MAX_CONCURRENT.labels(provider=provider_id).set(max_concurrent)
    PROVIDER_CONSECUTIVE_FAILURES.labels(provider=provider_id).set(consecutive_failures)
    if response_time_ms > 0:
        PROVIDER_RESPONSE_TIME.labels(provider=provider_id).set(response_time_ms)


def update_memory_metrics(conversations: int, messages: int):
    """Update memory/conversation metrics."""
    CONVERSATIONS_TOTAL.set(conversations)
    MESSAGES_TOTAL.set(messages)


class RequestTimer:
    """Context manager for timing requests."""
    
    def __init__(self, endpoint: str, provider: str):
        self.endpoint = endpoint
        self.provider = provider
        self.start_time: float = 0.0
        self.duration: float = 0.0
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = time.perf_counter() - self.start_time
        return False
    
    def get_duration(self) -> float:
        return self.duration
