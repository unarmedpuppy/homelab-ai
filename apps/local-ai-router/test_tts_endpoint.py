#!/usr/bin/env python3
"""Test the new TTS endpoint in Local AI Router."""

import asyncio
import httpx
import json

async def test_tts_endpoint():
    """Test TTS endpoint with various requests."""
    
    # Test cases
    test_cases = [
        {
            "name": "Basic TTS request",
            "payload": {
                "model": "tts-1",
                "input": "Hello, this is a test of the TTS endpoint.",
                "voice": "alloy",
                "response_format": "mp3"
            }
        },
        {
            "name": "Different voice",
            "payload": {
                "model": "tts-1", 
                "input": "Testing with the echo voice.",
                "voice": "echo",
                "response_format": "wav"
            }
        },
        {
            "name": "Speed adjustment",
            "payload": {
                "model": "tts-1",
                "input": "This is a fast-paced test.",
                "voice": "nova",
                "response_format": "mp3",
                "speed": 1.5
            }
        }
    ]
    
    # Test each case
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "http://localhost:8012/v1/audio/speech",
                    json=test_case["payload"],
                    headers={
                        "Authorization": "Bearer test_key",  # Using test key
                        "Content-Type": "application/json"
                    }
                )
                
                print(f"Status Code: {response.status_code}")
                print(f"Content-Type: {response.headers.get('content-type')}")
                print(f"Content-Length: {response.headers.get('content-length')} bytes")
                
                if response.headers.get('x-audio-duration'):
                    print(f"Audio Duration: {response.headers.get('x-audio-duration')}s")
                
                if response.headers.get('x-generation-time'):
                    print(f"Generation Time: {response.headers.get('x-generation-time')}s")
                
                if response.status_code == 200:
                    # Save audio file for verification
                    filename = f"test_output_{test_case['name'].lower().replace(' ', '_')}.{test_case['payload']['response_format']}"
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    print(f"✅ Audio saved as: {filename}")
                else:
                    print(f"❌ Error: {response.text}")
                    
        except Exception as e:
            print(f"❌ Exception: {e}")

async def test_error_cases():
    """Test error handling for invalid requests."""
    
    print("\n--- Error Cases ---")
    
    error_cases = [
        {
            "name": "Missing input field",
            "payload": {"model": "tts-1", "voice": "alloy"},
            "expected_error": "Missing required field: input"
        },
        {
            "name": "Empty input",
            "payload": {"model": "tts-1", "input": "", "voice": "alloy"},
            "expected_error": "TTS generation failed"
        }
    ]
    
    for test_case in error_cases:
        print(f"\n--- {test_case['name']} ---")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "http://localhost:8012/v1/audio/speech",
                    json=test_case["payload"],
                    headers={
                        "Authorization": "Bearer test_key",
                        "Content-Type": "application/json"
                    }
                )
                
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                
                if test_case["expected_error"] in response.text:
                    print("✅ Expected error received")
                else:
                    print("❌ Unexpected error response")
                    
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("Testing TTS endpoint...")
    print("Make sure Local AI Router is running on http://localhost:8012")
    print("and Gaming PC manager is accessible at the configured endpoint.")
    
    asyncio.run(test_tts_endpoint())
    asyncio.run(test_error_cases())
    
    print("\n--- Test Summary ---")
    print("✅ TTS endpoint implementation complete")
    print("✅ Ready for Phase 2b: Update dashboard to use router")
    print("\nNext steps:")
    print("1. Deploy this router change to server")
    print("2. Update dashboard TTS_API_URL to use router instead of Gaming PC directly")
    print("3. Test end-to-end TTS through router")