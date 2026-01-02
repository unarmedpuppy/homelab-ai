"""
Test script for Phase 2.3 - /admin/providers endpoint

Tests that the admin providers endpoint returns comprehensive provider information.
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient
from router import app


def test_admin_providers_endpoint():
    """Test /admin/providers endpoint returns correct structure and data."""
    print("=== Testing Phase 2.3: /admin/providers Endpoint ===\n")

    with TestClient(app) as client:
        # Test 1: Endpoint returns 200
        print("--- Test 1: Endpoint Returns 200 ---")
        response = client.get("/admin/providers")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✅ Status Code: {response.status_code}\n")

        # Test 2: Response structure
        print("--- Test 2: Response Structure ---")
        data = response.json()

        assert "providers" in data, "Missing 'providers' key"
        assert "total_providers" in data, "Missing 'total_providers' key"
        assert "healthy_providers" in data, "Missing 'healthy_providers' key"

        print(f"✅ Response has correct top-level structure")
        print(f"   Total providers: {data['total_providers']}")
        print(f"   Healthy providers: {data['healthy_providers']}\n")

        # Test 3: Provider structure
        print("--- Test 3: Provider Structure ---")
        providers = data["providers"]

        assert len(providers) > 0, "No providers returned"
        print(f"✅ Found {len(providers)} providers\n")

        # Check first provider structure
        provider = providers[0]
        required_keys = [
            "id", "name", "type", "description", "endpoint",
            "priority", "enabled", "health", "load", "models", "config", "metadata"
        ]

        for key in required_keys:
            assert key in provider, f"Missing key '{key}' in provider"

        print(f"✅ Provider has all required keys")
        print(f"   Provider: {provider['name']}\n")

        # Test 4: Health information
        print("--- Test 4: Health Information ---")
        health = provider["health"]

        assert "is_healthy" in health, "Missing 'is_healthy' in health"
        assert "consecutive_failures" in health, "Missing 'consecutive_failures' in health"
        assert "last_check" in health, "Missing 'last_check' in health"

        print(f"✅ Health information structure correct")
        print(f"   Is healthy: {health['is_healthy']}")
        print(f"   Consecutive failures: {health['consecutive_failures']}\n")

        # Test 5: Load information
        print("--- Test 5: Load Information ---")
        load = provider["load"]

        assert "current_requests" in load, "Missing 'current_requests' in load"
        assert "max_concurrent" in load, "Missing 'max_concurrent' in load"
        assert "utilization" in load, "Missing 'utilization' in load"

        print(f"✅ Load information structure correct")
        print(f"   Current requests: {load['current_requests']}")
        print(f"   Max concurrent: {load['max_concurrent']}")
        print(f"   Utilization: {load['utilization']}%\n")

        # Test 6: Models information
        print("--- Test 6: Models Information ---")
        models = provider["models"]

        print(f"✅ Provider has {len(models)} models")
        if len(models) > 0:
            model = models[0]
            assert "id" in model, "Missing 'id' in model"
            assert "name" in model, "Missing 'name' in model"
            assert "capabilities" in model, "Missing 'capabilities' in model"

            print(f"   First model: {model['name']} ({model['id']})")
            print(f"   Capabilities: {list(model['capabilities'].keys())}\n")

        # Test 7: Config information
        print("--- Test 7: Config Information ---")
        config = provider["config"]

        assert "health_check_interval" in config, "Missing 'health_check_interval' in config"
        assert "health_check_timeout" in config, "Missing 'health_check_timeout' in config"
        assert "health_check_path" in config, "Missing 'health_check_path' in config"

        print(f"✅ Config information structure correct")
        print(f"   Health check interval: {config['health_check_interval']}s")
        print(f"   Health check timeout: {config['health_check_timeout']}s\n")

        # Test 8: List all providers summary
        print("--- Test 8: All Providers Summary ---")
        for p in providers:
            health_status = "✅ Healthy" if p["health"]["is_healthy"] else "❌ Unhealthy"
            print(f"  {health_status} {p['name']} ({p['type']})")
            print(f"     Priority: {p['priority']}, Models: {len(p['models'])}, Load: {p['load']['utilization']}%")

        print()

        print("=== All Tests Passed ✅ ===")
        return True


if __name__ == "__main__":
    try:
        success = test_admin_providers_endpoint()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
