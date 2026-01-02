"""
Test script for HealthChecker - validates health checking functionality.
"""
import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from providers import ProviderManager, HealthChecker


async def test_health_checker():
    """Test HealthChecker functionality."""
    print("=== Testing HealthChecker ===\n")

    # Initialize manager
    config_path = Path(__file__).parent / "config" / "providers.yaml"
    print(f"Loading config from: {config_path}")

    try:
        manager = ProviderManager(config_path=str(config_path))
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False

    print(f"✅ Loaded {len(manager.providers)} providers\n")

    # Create health checker with short interval for testing
    health_checker = HealthChecker(manager, check_interval=5)
    print("Created HealthChecker with 5s check interval\n")

    # Test 1: Force check on gaming-pc-3090
    print("--- Test 1: Force health check on gaming-pc-3090 ---")
    provider_id = "gaming-pc-3090"
    provider = manager.get_provider(provider_id)

    if provider:
        print(f"Before check: is_healthy={provider.is_healthy}, "
              f"consecutive_failures={provider.consecutive_failures}")

        result = await health_checker.force_check(provider_id)

        if result:
            print(f"Health check result:")
            print(f"  Provider: {result.provider_id}")
            print(f"  Healthy: {result.is_healthy}")
            print(f"  Response time: {result.response_time_ms:.0f}ms" if result.response_time_ms else "  Response time: N/A")
            print(f"  Error: {result.error}" if result.error else "  No errors")

            provider_after = manager.get_provider(provider_id)
            print(f"After check: is_healthy={provider_after.is_healthy}, "
                  f"consecutive_failures={provider_after.consecutive_failures}")
        else:
            print("❌ Force check returned None")
    print()

    # Test 2: Check all providers status
    print("--- Test 2: Get all health statuses ---")
    all_status = health_checker.get_all_health_status()
    for pid, result in all_status.items():
        status_emoji = "✅" if result.is_healthy else "❌"
        print(f"  {status_emoji} {pid}: healthy={result.is_healthy}, "
              f"response_time={result.response_time_ms:.0f}ms" if result.response_time_ms else f"  {status_emoji} {pid}: healthy={result.is_healthy}")
    print()

    # Test 3: Start background checker and run for a short time
    print("--- Test 3: Background health checker ---")
    print("Starting background health checker for 10 seconds...")

    await health_checker.start()

    # Wait and show updates
    for i in range(10):
        await asyncio.sleep(1)
        print(f"  [{i+1}/10s] Checker running...")

    await health_checker.stop()
    print("✅ Background health checker stopped\n")

    # Test 4: Final provider status
    print("--- Test 4: Final Provider Status ---")
    status = manager.get_provider_status()
    for provider_id, info in status.items():
        status_emoji = "✅" if info['healthy'] else "❌"
        print(f"  {status_emoji} {provider_id}:")
        print(f"    Enabled: {info['enabled']}, Healthy: {info['healthy']}")
        print(f"    Load: {info['current_requests']}/{info['max_concurrent']}")
        print(f"    Priority: {info['priority']}")
    print()

    print("=== All Tests Completed ✅ ===")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_health_checker())
    sys.exit(0 if success else 1)
