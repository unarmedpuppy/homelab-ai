"""
Test script for Phase 2.1 - ProviderManager integration into router.py

Tests:
1. App startup and lifespan initialization
2. /health endpoint with provider status
3. /v1/models endpoint with dynamic model listing
4. Provider selection for different model requests
"""
import asyncio
from pathlib import Path

# Add current directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient
from router import app, provider_manager, health_checker


def test_startup():
    """Test that app starts and initializes providers."""
    print("=== Test 1: App Startup ===")

    with TestClient(app) as client:
        # Check that provider_manager was initialized
        assert provider_manager is not None, "ProviderManager not initialized"
        assert health_checker is not None, "HealthChecker not initialized"

        print(f"✅ ProviderManager initialized: {len(provider_manager.providers)} providers")
        print(f"✅ HealthChecker initialized")

        # List providers
        for provider in provider_manager.get_all_providers():
            print(f"   - {provider.name} ({provider.id}): enabled={provider.enabled}")


def test_health_endpoint():
    """Test /health endpoint returns provider status."""
    print("\n=== Test 2: /health Endpoint ===")

    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"

        data = response.json()
        assert "status" in data
        assert "backends" in data

        print(f"✅ Health status: {data['status']}")
        print(f"   Backends reported: {len(data['backends'])}")

        for backend_id, backend_info in data["backends"].items():
            healthy_status = "✅" if backend_info.get("healthy") else "❌"
            print(f"   {healthy_status} {backend_id}: {backend_info}")


def test_models_endpoint():
    """Test /v1/models endpoint returns models from ProviderManager."""
    print("\n=== Test 3: /v1/models Endpoint ===")

    with TestClient(app) as client:
        response = client.get("/v1/models")
        assert response.status_code == 200, f"Models list failed: {response.status_code}"

        data = response.json()
        assert "data" in data
        assert "object" in data

        models = data["data"]
        print(f"✅ Models returned: {len(models)}")

        # Check for configured models
        model_ids = [m["id"] for m in models]
        print(f"   Model IDs: {model_ids}")

        # Check for routing aliases
        assert "auto" in model_ids, "Missing 'auto' alias"
        assert "small" in model_ids, "Missing 'small' alias"
        assert "big" in model_ids, "Missing 'big' alias"

        print(f"✅ Routing aliases present")


def test_provider_selection():
    """Test provider selection logic."""
    print("\n=== Test 4: Provider Selection ===")

    # Test auto-selection
    print("\n--- Auto Selection ---")
    selection = provider_manager.select_provider(model_id=None)
    if selection:
        print(f"✅ Auto-selected: {selection.provider.name} / {selection.model.name}")
    else:
        print(f"⚠️  No provider selected (all unhealthy)")

    # Test specific model selection
    print("\n--- Specific Model Selection ---")
    test_models = ["qwen2.5-14b-awq", "llama3-8b", "glm-4-flash"]

    for model_id in test_models:
        selection = provider_manager.select_provider(model_id=model_id)
        if selection:
            print(f"✅ {model_id}: {selection.provider.name}")
        else:
            print(f"⚠️  {model_id}: No healthy provider")

    # Test concurrency tracking
    print("\n--- Concurrency Tracking ---")
    provider_id = "gaming-pc-3090"
    provider = provider_manager.get_provider(provider_id)

    if provider:
        initial_count = provider.current_requests
        print(f"Initial requests for {provider_id}: {initial_count}")

        provider_manager.track_request_start(provider_id)
        print(f"After start: {provider.current_requests} (should be {initial_count + 1})")

        provider_manager.track_request_end(provider_id)
        print(f"After end: {provider.current_requests} (should be {initial_count})")

        assert provider.current_requests == initial_count, "Concurrency tracking broken"
        print(f"✅ Concurrency tracking working")


def test_backward_compatibility():
    """Test that old model aliases still work."""
    print("\n=== Test 5: Backward Compatibility ===")

    with TestClient(app) as client:
        # Test old model aliases
        response = client.get("/v1/models")
        data = response.json()
        model_ids = [m["id"] for m in data["data"]]

        # Check for old aliases
        old_aliases = ["auto", "small", "fast", "medium", "big"]
        for alias in old_aliases:
            if alias in model_ids:
                print(f"✅ Alias '{alias}' supported")
            else:
                print(f"❌ Alias '{alias}' missing")


if __name__ == "__main__":
    print("=== Testing Phase 2.1: ProviderManager Integration ===\n")

    try:
        test_startup()
        test_health_endpoint()
        test_models_endpoint()
        test_provider_selection()
        test_backward_compatibility()

        print("\n=== All Tests Passed ✅ ===")
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
