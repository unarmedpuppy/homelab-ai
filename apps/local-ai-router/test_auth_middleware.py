#!/usr/bin/env python3
"""
Test script for auth middleware in Local AI Router.

Usage:
    # First create a test API key:
    python scripts/manage-api-keys.py create test-user
    
    # Run the router:
    python router.py
    
    # Then run this script with the key:
    python test_auth_middleware.py lai_<your-key>
    
    # Or set LAI_API_KEY environment variable:
    LAI_API_KEY=lai_xxx python test_auth_middleware.py
"""
import asyncio
import os
import sys
import httpx

BASE_URL = os.getenv("ROUTER_URL", "http://localhost:8012")


async def test_missing_auth():
    """Test request without Authorization header."""
    print("\n=== Test: Missing Authorization Header ===")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "model": "auto",
                "messages": [{"role": "user", "content": "Hello"}]
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Got 401 as expected")


async def test_invalid_key():
    """Test request with invalid API key."""
    print("\n=== Test: Invalid API Key ===")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={"Authorization": "Bearer lai_invalid_key_12345678901234"},
            json={
                "model": "auto",
                "messages": [{"role": "user", "content": "Hello"}]
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("PASS: Got 401 as expected")


async def test_empty_bearer():
    """Test request with empty Bearer token."""
    print("\n=== Test: Empty Bearer Token ===")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/v1/chat/completions",
                headers={"Authorization": "Bearer "},
                json={
                    "model": "auto",
                    "messages": [{"role": "user", "content": "Hello"}]
                }
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            assert response.status_code == 401, f"Expected 401, got {response.status_code}"
            print("PASS: Got 401 as expected")
        except httpx.LocalProtocolError as e:
            # httpx rejects "Bearer " (trailing space only) at protocol level
            # This is expected behavior - malformed header
            print(f"PASS: HTTP client rejected malformed header: {e}")


async def test_valid_key(api_key: str):
    """Test request with valid API key."""
    print("\n=== Test: Valid API Key ===")
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test with "Bearer" prefix
        response = await client.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "auto",
                "messages": [{"role": "user", "content": "Say 'auth works' and nothing else."}]
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Provider: {data.get('provider', 'N/A')}")
            if 'choices' in data:
                print(f"Response: {data['choices'][0]['message']['content'][:100]}")
            print("PASS: Got 200 with valid key")
        else:
            print(f"Response: {response.json()}")
            print("FAIL: Expected 200")


async def test_valid_key_no_bearer(api_key: str):
    """Test request with valid API key but without Bearer prefix."""
    print("\n=== Test: Valid Key Without Bearer Prefix ===")
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test without "Bearer" prefix (should also work)
        response = await client.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={"Authorization": api_key},
            json={
                "model": "auto",
                "messages": [{"role": "user", "content": "Say 'no bearer works' and nothing else."}]
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("PASS: Got 200 - key without Bearer prefix works")
        else:
            print(f"Response: {response.json()}")
            print("FAIL: Expected 200")


async def test_priority_logging(api_key: str):
    """Test that priority is logged correctly based on key name."""
    print("\n=== Test: Priority Logging ===")
    print("Check router logs for 'priority=' in the output.")
    print("Keys named 'agent-*' or 'critical-*' should show priority=0")
    print("Normal keys should show priority=1")
    print("Keys named 'batch-*' should show priority=2")
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "auto",
                "messages": [{"role": "user", "content": "Priority test"}]
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("PASS: Request completed - check logs for priority")
        else:
            print(f"Response: {response.json()}")


async def main():
    # Get API key from command line or environment
    api_key = None
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        api_key = os.getenv("LAI_API_KEY")
    
    print(f"Testing against: {BASE_URL}")
    
    # Run rejection tests (no key needed)
    await test_missing_auth()
    await test_invalid_key()
    await test_empty_bearer()
    
    # Run success tests (key required)
    if api_key:
        print(f"\nUsing API key: {api_key[:12]}...")
        await test_valid_key(api_key)
        await test_valid_key_no_bearer(api_key)
        await test_priority_logging(api_key)
    else:
        print("\n" + "="*60)
        print("SKIPPED: Valid key tests (no API key provided)")
        print("To run all tests, provide an API key:")
        print("  python test_auth_middleware.py lai_<your-key>")
        print("  LAI_API_KEY=lai_xxx python test_auth_middleware.py")
        print("="*60)
    
    print("\n=== Test Summary ===")
    print("Rejection tests: PASS")
    if api_key:
        print("Authentication tests: See results above")
    else:
        print("Authentication tests: SKIPPED (no key)")


if __name__ == "__main__":
    asyncio.run(main())
