#!/usr/bin/env python3
"""
Test Local AI Router integration with OpenAI SDK.

This script verifies that the Local AI Router works correctly as an
OpenAI-compatible backend, which is required for OpenCode integration.

Usage:
    # Set your API key
    export LOCAL_AI_API_KEY="lai_your_api_key_here"
    
    # Run tests
    python scripts/test-opencode-integration.py
    
    # Or specify key directly
    python scripts/test-opencode-integration.py --api-key lai_xxx
    
    # Test specific endpoint
    python scripts/test-opencode-integration.py --base-url http://localhost:8012
"""

import argparse
import os
import sys
import time

def check_openai_sdk():
    """Check if OpenAI SDK is installed."""
    try:
        from openai import OpenAI
        return True
    except ImportError:
        print("ERROR: OpenAI SDK not installed.")
        print("Install with: pip install openai")
        return False


def test_health(base_url: str) -> bool:
    """Test health endpoint."""
    import urllib.request
    import json
    
    print("\n=== Testing Health Endpoint ===")
    health_url = base_url.replace("/v1", "/health")
    
    try:
        req = urllib.request.Request(health_url)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            print(f"Status: {data.get('status', 'unknown')}")
            if 'backends' in data:
                print("Backends:")
                for backend, status in data['backends'].items():
                    print(f"  - {backend}: {status}")
            return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False


def test_models(client) -> bool:
    """Test listing models."""
    print("\n=== Testing List Models ===")
    try:
        models = client.models.list()
        model_list = list(models)
        print(f"Found {len(model_list)} models:")
        for model in model_list[:5]:  # Show first 5
            print(f"  - {model.id}")
        if len(model_list) > 5:
            print(f"  ... and {len(model_list) - 5} more")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False


def test_chat_completion(client, model: str = "auto") -> bool:
    """Test non-streaming chat completion."""
    print(f"\n=== Testing Chat Completion (model={model}) ===")
    try:
        start = time.time()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Say 'Hello from Local AI Router!' and nothing else."}
            ],
            max_tokens=50
        )
        elapsed = time.time() - start
        
        content = response.choices[0].message.content
        print(f"Response: {content}")
        print(f"Model used: {response.model}")
        print(f"Tokens: {response.usage.prompt_tokens} in, {response.usage.completion_tokens} out")
        print(f"Time: {elapsed:.2f}s")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False


def test_streaming(client, model: str = "auto") -> bool:
    """Test streaming chat completion."""
    print(f"\n=== Testing Streaming (model={model}) ===")
    try:
        start = time.time()
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Count from 1 to 5, one number per line."}
            ],
            max_tokens=50,
            stream=True
        )
        
        print("Response: ", end="", flush=True)
        chunk_count = 0
        for chunk in stream:
            chunk_count += 1
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
        print()  # newline
        
        elapsed = time.time() - start
        print(f"Chunks received: {chunk_count}")
        print(f"Time: {elapsed:.2f}s")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False


def test_force_big(client) -> bool:
    """Test force-big routing (3090)."""
    print("\n=== Testing Force-Big Routing ===")
    try:
        response = client.chat.completions.create(
            model="big",
            messages=[
                {"role": "user", "content": "What model are you? Answer briefly."}
            ],
            max_tokens=100
        )
        
        content = response.choices[0].message.content
        print(f"Response: {content}")
        print(f"Model used: {response.model}")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        print("Note: This may fail if gaming mode is active or 3090 is offline.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test Local AI Router OpenAI compatibility")
    parser.add_argument(
        "--api-key",
        default=os.environ.get("LOCAL_AI_API_KEY"),
        help="API key (default: LOCAL_AI_API_KEY env var)"
    )
    parser.add_argument(
        "--base-url",
        default="https://local-ai-api.server.unarmedpuppy.com/v1",
        help="Router base URL"
    )
    parser.add_argument(
        "--model",
        default="auto",
        help="Model to test (default: auto)"
    )
    parser.add_argument(
        "--skip-streaming",
        action="store_true",
        help="Skip streaming test"
    )
    parser.add_argument(
        "--skip-force-big",
        action="store_true",
        help="Skip force-big test"
    )
    
    args = parser.parse_args()
    
    if not args.api_key:
        print("ERROR: No API key provided.")
        print("Set LOCAL_AI_API_KEY environment variable or use --api-key")
        print("\nGenerate a key with:")
        print("  cd apps/local-ai-router")
        print("  python scripts/manage-api-keys.py create 'opencode'")
        sys.exit(1)
    
    if not check_openai_sdk():
        sys.exit(1)
    
    from openai import OpenAI
    
    print("=" * 60)
    print("Local AI Router - OpenCode Integration Test")
    print("=" * 60)
    print(f"Base URL: {args.base_url}")
    print(f"API Key: {args.api_key[:12]}...")
    print(f"Model: {args.model}")
    
    # Initialize client
    client = OpenAI(
        base_url=args.base_url,
        api_key=args.api_key
    )
    
    # Run tests
    results = {}
    
    results["health"] = test_health(args.base_url)
    results["models"] = test_models(client)
    results["chat"] = test_chat_completion(client, args.model)
    
    if not args.skip_streaming:
        results["streaming"] = test_streaming(client, args.model)
    
    if not args.skip_force_big:
        results["force_big"] = test_force_big(client)
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = 0
    failed = 0
    for test_name, success in results.items():
        status = "PASS" if success else "FAIL"
        print(f"  {test_name}: {status}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("\nSome tests failed. Check the output above for details.")
        print("\nCommon issues:")
        print("  - Router not running: curl the health endpoint")
        print("  - Invalid API key: regenerate with manage-api-keys.py")
        print("  - Gaming mode active: force-big test may fail")
        print("  - Model loading: first request takes 60-90s")
        sys.exit(1)
    else:
        print("\nAll tests passed! OpenCode integration should work correctly.")
        print("\nNext steps:")
        print("  1. Create ~/.config/opencode/opencode.json (see docs)")
        print("  2. Set LOCAL_AI_API_KEY in your shell profile")
        print("  3. Run 'opencode' and use your local AI!")
        sys.exit(0)


if __name__ == "__main__":
    main()
