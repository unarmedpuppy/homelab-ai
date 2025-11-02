"""
Unit Tests for Metrics Utilities
=================================

Tests for Prometheus metrics collection utilities.
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, patch, MagicMock
from prometheus_client import CollectorRegistry

from src.utils.metrics import (
    get_metrics_registry,
    get_or_create_counter,
    get_or_create_histogram,
    get_or_create_gauge,
    track_duration,
    track_call_count,
    track_duration_context,
    generate_metrics_output,
    get_metrics_content_type,
    validate_metric_name,
    validate_label_names,
    normalize_metric_name
)


class TestMetricsRegistry:
    """Test metrics registry management"""
    
    def test_get_metrics_registry_singleton(self):
        """Test that get_metrics_registry returns singleton"""
        registry1 = get_metrics_registry()
        registry2 = get_metrics_registry()
        
        assert registry1 is registry2
        assert isinstance(registry1, CollectorRegistry)
    
    def test_registry_thread_safety(self):
        """Test registry initialization is thread-safe"""
        import threading
        
        registries = []
        
        def get_registry():
            registries.append(get_metrics_registry())
        
        threads = [threading.Thread(target=get_registry) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All should be the same registry instance
        assert all(r is registries[0] for r in registries)


class TestCounterMetrics:
    """Test Counter metric creation and usage"""
    
    def test_create_counter_without_labels(self):
        """Test creating a counter without labels"""
        counter = get_or_create_counter(
            'test_counter_total',
            'A test counter',
            labelnames=None
        )
        
        assert counter is not None
        counter.inc()
        assert counter._value.get() == 1.0
    
    def test_create_counter_with_labels(self):
        """Test creating a counter with labels"""
        counter = get_or_create_counter(
            'test_labeled_counter_total',
            'A test labeled counter',
            labelnames=['label1', 'label2']
        )
        
        counter.labels(label1='value1', label2='value2').inc()
        assert counter.labels(label1='value1', label2='value2')._value.get() == 1.0
    
    def test_counter_idempotent_creation(self):
        """Test that creating the same counter twice returns same instance"""
        counter1 = get_or_create_counter('test_idempotent_total', 'Test')
        counter2 = get_or_create_counter('test_idempotent_total', 'Test')
        
        assert counter1 is counter2


class TestHistogramMetrics:
    """Test Histogram metric creation and usage"""
    
    def test_create_histogram_without_labels(self):
        """Test creating a histogram without labels"""
        histogram = get_or_create_histogram(
            'test_histogram_seconds',
            'A test histogram',
            labelnames=None,
            buckets=[0.1, 0.5, 1.0, 2.0]
        )
        
        assert histogram is not None
        histogram.observe(0.25)
        histogram.observe(0.75)
    
    def test_create_histogram_with_labels(self):
        """Test creating a histogram with labels"""
        histogram = get_or_create_histogram(
            'test_labeled_histogram_seconds',
            'A test labeled histogram',
            labelnames=['operation'],
            buckets=[0.1, 0.5, 1.0]
        )
        
        histogram.labels(operation='test_op').observe(0.3)
    
    def test_histogram_default_buckets(self):
        """Test histogram with default buckets"""
        histogram = get_or_create_histogram(
            'test_default_histogram',
            'Test histogram',
            labelnames=None
        )
        
        histogram.observe(0.5)


class TestGaugeMetrics:
    """Test Gauge metric creation and usage"""
    
    def test_create_gauge_without_labels(self):
        """Test creating a gauge without labels"""
        gauge = get_or_create_gauge(
            'test_gauge',
            'A test gauge',
            labelnames=None
        )
        
        gauge.set(10.0)
        assert gauge._value.get() == 10.0
        
        gauge.inc(5.0)
        assert gauge._value.get() == 15.0
        
        gauge.dec(3.0)
        assert gauge._value.get() == 12.0
    
    def test_create_gauge_with_labels(self):
        """Test creating a gauge with labels"""
        gauge = get_or_create_gauge(
            'test_labeled_gauge',
            'A test labeled gauge',
            labelnames=['resource']
        )
        
        gauge.labels(resource='cpu').set(50.0)
        assert gauge.labels(resource='cpu')._value.get() == 50.0


class TestTrackDurationDecorator:
    """Test @track_duration decorator"""
    
    def test_track_duration_sync_function(self):
        """Test duration tracking on synchronous function"""
        @track_duration('test_duration_seconds', 'Test duration', [])
        def test_function():
            time.sleep(0.01)
            return "success"
        
        result = test_function()
        assert result == "success"
    
    def test_track_duration_with_labels(self):
        """Test duration tracking with labels"""
        @track_duration('test_labeled_duration', 'Test', ['operation'])
        def test_function(operation):
            time.sleep(0.01)
            return operation
        
        result = test_function('test_op')
        assert result == 'test_op'
    
    @pytest.mark.asyncio
    async def test_track_duration_async_function(self):
        """Test duration tracking on async function"""
        @track_duration('test_async_duration', 'Test async', [])
        async def async_function():
            await asyncio.sleep(0.01)
            return "async_success"
        
        result = await async_function()
        assert result == "async_success"


class TestTrackCallCountDecorator:
    """Test @track_call_count decorator"""
    
    def test_track_call_count_sync_function(self):
        """Test call count tracking on synchronous function"""
        @track_call_count('test_call_count_total', 'Test calls', [])
        def test_function():
            return "success"
        
        result1 = test_function()
        result2 = test_function()
        
        assert result1 == "success"
        assert result2 == "success"
    
    def test_track_call_count_with_labels(self):
        """Test call count tracking with labels"""
        @track_call_count('test_labeled_calls', 'Test', ['type'])
        def test_function(type):
            return type
        
        result = test_function('test_type')
        assert result == 'test_type'


class TestTrackDurationContext:
    """Test track_duration_context context manager"""
    
    def test_context_manager_basic(self):
        """Test basic context manager usage"""
        with track_duration_context(
            'test_context_duration',
            'Test context',
            labels=None
        ):
            time.sleep(0.01)
    
    def test_context_manager_with_labels(self):
        """Test context manager with labels"""
        with track_duration_context(
            'test_labeled_context',
            'Test',
            labels={'operation': 'test_op'}
        ):
            time.sleep(0.01)
    
    def test_context_manager_exception(self):
        """Test context manager still tracks duration on exception"""
        with pytest.raises(ValueError):
            with track_duration_context(
                'test_exception_duration',
                'Test exception',
                labels=None
            ):
                time.sleep(0.01)
                raise ValueError("Test exception")


class TestMetricsOutput:
    """Test metrics output generation"""
    
    def test_generate_metrics_output(self):
        """Test generating Prometheus metrics output"""
        # Create a test metric
        counter = get_or_create_counter('test_output_counter_total', 'Test counter')
        counter.inc()
        
        output = generate_metrics_output()
        
        assert output is not None
        assert isinstance(output, bytes)
        assert b'test_output_counter_total' in output
    
    def test_get_metrics_content_type(self):
        """Test getting metrics content type"""
        content_type = get_metrics_content_type()
        assert content_type == 'text/plain; version=0.0.4; charset=utf-8'


class TestMetricValidation:
    """Test metric name and label validation"""
    
    def test_validate_metric_name_valid(self):
        """Test validation of valid metric names"""
        assert validate_metric_name('valid_metric_name')
        assert validate_metric_name('valid:metric:name')
        assert validate_metric_name('_valid_metric')
        assert validate_metric_name('valid123_metric')
    
    def test_validate_metric_name_invalid(self):
        """Test validation of invalid metric names"""
        assert not validate_metric_name('123invalid')  # Starts with number
        assert not validate_metric_name('invalid-metric')  # Contains hyphen
        assert not validate_metric_name('invalid.metric')  # Contains dot
        assert not validate_metric_name('')  # Empty
    
    def test_validate_label_names_valid(self):
        """Test validation of valid label names"""
        assert validate_label_names(['label1', 'label2', '_label3'])
        assert validate_label_names(None)
        assert validate_label_names([])
    
    def test_validate_label_names_invalid(self):
        """Test validation of invalid label names"""
        assert not validate_label_names(['123invalid'])  # Starts with number
        assert not validate_label_names(['__reserved'])  # Reserved prefix
        assert not validate_label_names(['invalid-label'])  # Contains hyphen
    
    def test_normalize_metric_name(self):
        """Test metric name normalization"""
        assert normalize_metric_name('ValidMetricName') == 'valid_metric_name'
        assert normalize_metric_name('metric-name') == 'metric_name'
        assert normalize_metric_name('123Metric') == '_123_metric'
        assert normalize_metric_name('metric.name') == 'metric_name'


class TestMetricsIntegration:
    """Integration tests for metrics system"""
    
    def test_multiple_metrics_coexist(self):
        """Test that multiple metrics can coexist"""
        counter = get_or_create_counter('multi_counter_total', 'Counter')
        histogram = get_or_create_histogram('multi_histogram', 'Histogram')
        gauge = get_or_create_gauge('multi_gauge', 'Gauge')
        
        counter.inc()
        histogram.observe(1.0)
        gauge.set(10.0)
        
        # All should work independently
        assert counter._value.get() == 1.0
        assert gauge._value.get() == 10.0
    
    def test_metrics_persist_across_calls(self):
        """Test that metrics persist their values"""
        counter = get_or_create_counter('persist_counter_total', 'Test')
        
        counter.inc(5)
        assert counter._value.get() == 5.0
        
        # Get same counter again
        counter2 = get_or_create_counter('persist_counter_total', 'Test')
        assert counter2 is counter
        
        counter2.inc(3)
        assert counter._value.get() == 8.0
        assert counter2._value.get() == 8.0

