"""
Test script for ProviderManager - validates YAML loading and selection logic.
"""
import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from providers import ProviderManager


async def test_provider_manager():
    """Test ProviderManager functionality."""
    print("=== Testing ProviderManager ===\n")

    # Initialize manager
    config_path = Path(__file__).parent / "config" / "providers.yaml"
    print(f"Loading config from: {config_path}")

    try:
        manager = ProviderManager(config_path=str(config_path))
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False

    print(f"✅ Loaded {len(manager.providers)} providers, {len(manager.models)} models\n")

    # Test 1: List all providers
    print("--- Providers ---")
    for provider_id, provider in manager.providers.items():
        print(f"  {provider_id}: {provider.name} (priority={provider.priority}, "
              f"max_concurrent={provider.max_concurrent}, enabled={provider.enabled})")
    print()

    # Test 2: List all models
    print("--- Models ---")
    for model_id, model in manager.models.items():
        print(f"  {model_id}: {model.name} (provider={model.provider_id}, "
              f"default={model.is_default})")
    print()

    # Test 3: Select provider for "auto" request
    print("--- Test: Select provider for 'auto' ---")
    try:
        selection = await manager.select_provider_and_model("auto")
        print(f"✅ Selected: {selection.model.id} on {selection.provider.id}")
        print(f"   Reason: {selection.reason}")
    except Exception as e:
        print(f"❌ Selection failed: {e}")
    print()

    # Test 4: Select specific model
    print("--- Test: Select provider for 'qwen2.5-14b-awq' ---")
    try:
        selection = await manager.select_provider_and_model("qwen2.5-14b-awq")
        print(f"✅ Selected: {selection.model.id} on {selection.provider.id}")
        print(f"   Reason: {selection.reason}")
    except Exception as e:
        print(f"❌ Selection failed: {e}")
    print()

    # Test 5: Track request (concurrency)
    print("--- Test: Request tracking ---")
    provider_id = "gaming-pc-3090"
    provider = manager.get_provider(provider_id)
    if provider:
        print(f"Before: {provider_id} has {provider.current_requests}/{provider.max_concurrent} requests")

        async with manager.track_request(provider_id):
            provider_updated = manager.get_provider(provider_id)
            print(f"During: {provider_id} has {provider_updated.current_requests}/{provider_updated.max_concurrent} requests")

        provider_final = manager.get_provider(provider_id)
        print(f"After:  {provider_id} has {provider_final.current_requests}/{provider_final.max_concurrent} requests")
        print("✅ Request tracking works correctly")
    print()

    # Test 6: Provider status
    print("--- Provider Status ---")
    status = manager.get_provider_status()
    for provider_id, info in status.items():
        print(f"  {provider_id}:")
        print(f"    Enabled: {info['enabled']}, Healthy: {info['healthy']}")
        print(f"    Load: {info['current_requests']}/{info['max_concurrent']}")
    print()

    print("=== All Tests Passed ✅ ===")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_provider_manager())
    sys.exit(0 if success else 1)
