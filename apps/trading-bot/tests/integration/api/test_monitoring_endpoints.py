"""
Integration Tests for Monitoring API Endpoints
==============================================

Tests that verify monitoring and health check endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestHealthCheckEndpoints:
    """Test health check endpoints"""
    
    def test_health_endpoint(self, client):
        """Test basic health check endpoint"""
        response = client.get("/api/monitoring/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "healthy" in data or isinstance(data, dict)
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint"""
        response = client.get("/api/monitoring/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_system_status_endpoint(self, client):
        """Test system status endpoint"""
        response = client.get("/api/monitoring/status")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestRateLimitEndpoints:
    """Test rate limit monitoring endpoints"""
    
    def test_rate_limits_endpoint(self, client):
        """Test rate limits status endpoint"""
        response = client.get("/api/monitoring/rate-limits")
        
        # Should return rate limit information
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


@pytest.mark.integration
class TestMonitoringEndpointErrorHandling:
    """Test error handling in monitoring endpoints"""
    
    def test_health_endpoint_always_responds(self, client):
        """Test that health endpoint always responds (even on errors)"""
        # Health checks should be resilient
        response = client.get("/api/monitoring/health")
        
        # Should always return 200 (even if unhealthy, should report status)
        assert response.status_code == 200

