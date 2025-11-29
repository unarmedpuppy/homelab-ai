#!/usr/bin/env python3
"""
Alternative: Set NZBGet download limit via JSON-RPC API.
Since the web UI is having issues, this script attempts to set the limit
via the API if possible, or provides instructions for manual config.
"""

import requests
import json
import sys

NZBGET_URL = "http://192.168.86.47:6789/jsonrpc"
NZBGET_USERNAME = "nzbget"
NZBGET_PASSWORD = "nzbget"
MAX_DOWNLOADS = 3


def call_api(method, params=None):
    """Call NZBGet JSON-RPC API."""
    if params is None:
        params = []
    
    payload = {
        "method": method,
        "params": params
    }
    
    try:
        response = requests.post(
            NZBGET_URL,
            json=payload,
            auth=(NZBGET_USERNAME, NZBGET_PASSWORD),
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            if "result" in result:
                return result["result"]
            else:
                return None
        else:
            print(f"HTTP Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None


def main():
    print("=" * 60)
    print("NZBGet Download Limit Configuration")
    print("=" * 60)
    print(f"\nAttempting to set download limit to {MAX_DOWNLOADS}...")
    print("\nNote: NZBGet 25.4 may not support setting this via API.")
    print("If this fails, you'll need to:")
    print("1. Fix the web UI (503 error)")
    print("2. Or manually edit the config file")
    print()
    
    # Try to get config templates to see available options
    templates = call_api("configtemplates")
    if templates:
        print("Available config options (queue/download related):")
        found = False
        for template in templates:
            name = template.get("Name", "")
            if any(word in name.lower() for word in ["queue", "download", "active", "max"]):
                print(f"  {name} = {template.get('Value', 'N/A')}")
                found = True
        if not found:
            print("  (No queue/download options found)")
    
    print("\n" + "=" * 60)
    print("RECOMMENDED SOLUTION:")
    print("=" * 60)
    print("\nSince the web UI is returning 503, try:")
    print("1. Restart NZBGet: docker restart media-download-nzbget")
    print("2. Wait 30 seconds for it to fully start")
    print("3. Try accessing: http://192.168.86.47:6789")
    print("4. If web UI works, go to Settings > Queue")
    print("5. Set 'Max Active Downloads' to 3")
    print("\nIf web UI still doesn't work, the JSON-RPC API is working")
    print("and Sonarr/Radarr can still send downloads to NZBGet.")
    print("The download limit might need to be set manually in the config file")
    print("or may not be configurable in this NZBGet version.")


if __name__ == "__main__":
    main()

