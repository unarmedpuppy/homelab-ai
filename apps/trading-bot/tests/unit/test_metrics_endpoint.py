"""
Unit Tests for Metrics Endpoint
================================

Tests for the Prometheus metrics export endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from src.api.main import app
from src.utils.metrics import (
    get_or_create_counter,
    get_or_create_histogram,
    get_or_create_gauge,
    get_metrics_registry
)


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestMetricsEndpoint:
    """Test /metrics endpoint"""
    
    def test_metrics_endpoint_exists(self, client):
        """Test that /metrics endpoint exists"""
        response = client.get("/metrics")
        
        # Should return 200 OK
        assert response.status_code == 200
    
    def test_metrics_endpoint_content_type(self, client):
        """Test metrics endpoint content type"""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        assert 'text/plain' in response.headers.get('content-type', '')
    
    def test_metrics_endpoint_returns_prometheus_format(self, client):
        """Test that metrics endpoint returns Prometheus format"""
        # Create a test metric
        counter = get_or_create_counter(
            'test_prometheus_counter_total',
            'A test counter for Prometheus format'
        )
        counter.inc()
        
        response = client.get("/metrics")
        
        assert response.status_code == 200
        content = response.text
        
        # Should contain Prometheus format elements
        assert 'test_prometheus_counter_total' in content
        assert 'HELP' in content or '# HELP' in content
        assert 'TYPE' in content or '# TYPE' in content
    
    def test_metrics_endpoint_includes_multiple_metrics(self, client):
        """Test that endpoint includes multiple metric types"""
        # Create different metric types
        counter = get_or_create_counter('test_multi_counter_total', 'Counter')
        histogram = get_or_create_histogram('test_multi_histogram', 'Histogram')
        gauge = get_or_create_gauge('test_multi_gauge', 'Gauge')
        
        counter.inc()
        histogram.observe(1.5)
        gauge.set(42.0)
        
        response = client.get("/metrics")
        
        assert response.status_code == 200
        content = response.text
        
        assert 'test_multi_counter_total' in content
        assert 'test_multi_histogram' in content
        assert 'test_multi_gauge' in content
    
    def test_metrics_endpoint_includes_labeled_metrics(self, client):
        """Test that endpoint includes labeled metrics"""
        counter = get_or_create_counter(
            'test_labeled_counter_total',
            'Labeled counter',
            labelnames=['label1', 'label2']
        )
        
        counter.labels(label1='value1', label2='value2').inc(5)
        
        response = client.get("/metrics")
        
        assert response.status_code == 200
        content = response.text
        
        assert 'test_labeled_counter_total' in content
        assert 'label1="value1"' in content or 'label1=value1' in content
    
    def test_metrics_endpoint_updates_with_new_metrics(self, client):
        """Test that endpoint reflects new metrics"""
        # Initial request
        response1 = client.get("/metrics")
        assert response1.status_code == 200
        
        # Create new metric
        counter = get_or_create_counter('test_new_metric_total', 'New metric')
        counter.inc()
        
        # Second request should include new metric
        response2 = client.get("/metrics")
        assert response2.status_code == 200
        
        assert 'test_new_metric_total' not in response1.text
        assert 'test_new_metric_total' in response2.text

