"""
Prometheus Metrics Registry
============================

Core metrics registry and helper functions for creating metrics.
Thread-safe singleton pattern with automatic metric caching.
"""

import logging
import threading
import time
import asyncio
from typing import Optional, Dict, List, Any, Callable
from functools import wraps
from contextlib import contextmanager
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST
)

logger = logging.getLogger(__name__)

# Global metrics registry (thread-safe singleton)
_metrics_registry: Optional[CollectorRegistry] = None
_metrics_registry_lock = threading.Lock()

# Store created metrics to avoid duplicates
_metric_cache: Dict[str, Any] = {}
_metric_cache_lock = threading.Lock()


def get_metrics_registry() -> CollectorRegistry:
    """Get global metrics registry (thread-safe singleton)."""
    global _metrics_registry
    if _metrics_registry is None:
        with _metrics_registry_lock:
            if _metrics_registry is None:
                _metrics_registry = CollectorRegistry()
                logger.info("Metrics registry initialized")
    return _metrics_registry


def get_or_create_counter(
    name: str,
    documentation: str,
    labelnames: Optional[List[str]] = None,
    registry: Optional[CollectorRegistry] = None
) -> Counter:
    """Get or create a Counter metric."""
    registry = registry or get_metrics_registry()
    cache_key = f"counter:{name}:{labelnames}"

    with _metric_cache_lock:
        if cache_key not in _metric_cache:
            _metric_cache[cache_key] = Counter(
                name=name,
                documentation=documentation,
                labelnames=labelnames or [],
                registry=registry
            )
            logger.debug(f"Created Counter metric: {name}")
        return _metric_cache[cache_key]


def get_or_create_histogram(
    name: str,
    documentation: str,
    labelnames: Optional[List[str]] = None,
    buckets: Optional[List[float]] = None,
    registry: Optional[CollectorRegistry] = None
) -> Histogram:
    """Get or create a Histogram metric."""
    registry = registry or get_metrics_registry()
    cache_key = f"histogram:{name}:{labelnames}:{buckets}"

    with _metric_cache_lock:
        if cache_key not in _metric_cache:
            _metric_cache[cache_key] = Histogram(
                name=name,
                documentation=documentation,
                labelnames=labelnames or [],
                buckets=buckets,
                registry=registry
            )
            logger.debug(f"Created Histogram metric: {name}")
        return _metric_cache[cache_key]


def get_or_create_gauge(
    name: str,
    documentation: str,
    labelnames: Optional[List[str]] = None,
    registry: Optional[CollectorRegistry] = None
) -> Gauge:
    """Get or create a Gauge metric."""
    registry = registry or get_metrics_registry()
    cache_key = f"gauge:{name}:{labelnames}"

    with _metric_cache_lock:
        if cache_key not in _metric_cache:
            _metric_cache[cache_key] = Gauge(
                name=name,
                documentation=documentation,
                labelnames=labelnames or [],
                registry=registry
            )
            logger.debug(f"Created Gauge metric: {name}")
        return _metric_cache[cache_key]


def generate_metrics_output() -> bytes:
    """Generate Prometheus metrics output in exposition format."""
    registry = get_metrics_registry()
    return generate_latest(registry)


def get_metrics_content_type() -> str:
    """Get the content type for Prometheus metrics endpoint."""
    return CONTENT_TYPE_LATEST


def validate_metric_name(name: str) -> bool:
    """Validate metric name follows Prometheus conventions."""
    import re
    pattern = r'^[a-zA-Z_:][a-zA-Z0-9_:]*$'
    return bool(re.match(pattern, name))


def validate_label_names(labelnames: Optional[List[str]]) -> bool:
    """Validate label names follow Prometheus conventions."""
    if not labelnames:
        return True

    import re
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'

    for label in labelnames:
        if not re.match(pattern, label):
            return False
        if label.startswith('__'):
            return False
    return True


def normalize_metric_name(name: str) -> str:
    """Normalize metric name to follow Prometheus conventions."""
    import re
    name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
    name = re.sub(r'[^a-zA-Z0-9_:]', '_', name)
    if name and name[0].isdigit():
        name = '_' + name
    return name


# =============================================================================
# Decorators and Context Managers
# =============================================================================


def _extract_labels(func: Callable, args: tuple, kwargs: dict, labelnames: List[str]) -> Dict[str, str]:
    """Extract label values from function arguments."""
    import inspect

    labels = {}
    sig = inspect.signature(func)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()

    for label_name in labelnames:
        if label_name in bound.arguments:
            value = bound.arguments[label_name]
            labels[label_name] = str(value) if value is not None else 'unknown'
        else:
            labels[label_name] = 'unknown'

    return labels


def track_duration(
    metric_name: str,
    documentation: str,
    labelnames: Optional[List[str]] = None,
    buckets: Optional[List[float]] = None
):
    """Decorator to track function execution duration as a Histogram metric."""
    def decorator(func: Callable) -> Callable:
        histogram = get_or_create_histogram(
            name=metric_name,
            documentation=documentation,
            labelnames=labelnames or [],
            buckets=buckets
        )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                if labelnames:
                    labels = _extract_labels(func, args, kwargs, labelnames)
                    histogram.labels(**labels).observe(duration)
                else:
                    histogram.observe(duration)

                return result
            except Exception:
                duration = time.time() - start_time
                if labelnames:
                    try:
                        labels = _extract_labels(func, args, kwargs, labelnames)
                        histogram.labels(**labels).observe(duration)
                    except Exception:
                        histogram.observe(duration)
                else:
                    histogram.observe(duration)
                raise

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                if labelnames:
                    labels = _extract_labels(func, args, kwargs, labelnames)
                    histogram.labels(**labels).observe(duration)
                else:
                    histogram.observe(duration)

                return result
            except Exception:
                duration = time.time() - start_time
                if labelnames:
                    try:
                        labels = _extract_labels(func, args, kwargs, labelnames)
                        histogram.labels(**labels).observe(duration)
                    except Exception:
                        histogram.observe(duration)
                else:
                    histogram.observe(duration)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def track_call_count(
    metric_name: str,
    documentation: str,
    labelnames: Optional[List[str]] = None
):
    """Decorator to track function call count as a Counter metric."""
    def decorator(func: Callable) -> Callable:
        counter = get_or_create_counter(
            name=metric_name,
            documentation=documentation,
            labelnames=labelnames or []
        )

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)

                if labelnames:
                    labels = _extract_labels(func, args, kwargs, labelnames)
                    counter.labels(**labels).inc()
                else:
                    counter.inc()

                return result
            except Exception:
                if labelnames:
                    try:
                        labels = _extract_labels(func, args, kwargs, labelnames)
                        counter.labels(**labels).inc()
                    except Exception:
                        counter.inc()
                else:
                    counter.inc()
                raise

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)

                if labelnames:
                    labels = _extract_labels(func, args, kwargs, labelnames)
                    counter.labels(**labels).inc()
                else:
                    counter.inc()

                return result
            except Exception:
                if labelnames:
                    try:
                        labels = _extract_labels(func, args, kwargs, labelnames)
                        counter.labels(**labels).inc()
                    except Exception:
                        counter.inc()
                else:
                    counter.inc()
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


@contextmanager
def track_duration_context(
    metric_name: str,
    documentation: str,
    labels: Optional[Dict[str, str]] = None,
    buckets: Optional[List[float]] = None
):
    """Context manager to track code block execution duration."""
    histogram = get_or_create_histogram(
        name=metric_name,
        documentation=documentation,
        labelnames=list(labels.keys()) if labels else [],
        buckets=buckets
    )

    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        if labels:
            histogram.labels(**labels).observe(duration)
        else:
            histogram.observe(duration)
