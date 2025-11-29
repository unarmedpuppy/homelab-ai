#!/usr/bin/env python3
"""
Set NZBGet maximum parallel downloads to 3.
This limits how many downloads can run simultaneously.
"""

import requests
import json
import sys

NZBGET_URL = "http://192.168.86.47:6789/jsonrpc"
NZBGET_USERNAME = "nzbget"
NZBGET_PASSWORD = "nzbget"
MAX_DOWNLOADS = 3


def call_nzbget(method, params=None):
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
                print(f"Error in response: {result}")
                return None
        else:
            print(f"HTTP Error: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None


def get_config():
    """Get current NZBGet configuration."""
    return call_nzbget("config")


def set_max_downloads(max_downloads):
    """Set maximum parallel downloads."""
    # Get current config to find the option name
    config = get_config()
    if not config:
        print("✗ Failed to get NZBGet configuration")
        return False
    
    # Find MaxDownloads option
    max_downloads_option = None
    for option in config:
        if option.get("Name") == "MaxDownloads":
            max_downloads_option = option
            break
    
    if not max_downloads_option:
        print("✗ MaxDownloads option not found in NZBGet config")
        return False
    
    current_value = max_downloads_option.get("Value")
    print(f"Current MaxDownloads: {current_value}")
    
    if current_value == max_downloads:
        print(f"✓ MaxDownloads is already set to {max_downloads}")
        return True
    
    # Set the new value
    result = call_nzbget("config", [f"MaxDownloads={max_downloads}"])
    
    if result:
        print(f"✓ MaxDownloads set to {max_downloads}")
        # Verify
        config = get_config()
        if config:
            for option in config:
                if option.get("Name") == "MaxDownloads":
                    new_value = option.get("Value")
                    if new_value == max_downloads:
                        print(f"✓ Verified: MaxDownloads is now {new_value}")
                        return True
                    else:
                        print(f"⚠ Warning: Set to {max_downloads} but value is {new_value}")
                        return False
        return True
    else:
        print("✗ Failed to set MaxDownloads")
        return False


def main():
    print("=" * 60)
    print("Set NZBGet Maximum Parallel Downloads")
    print("=" * 60)
    print(f"\nSetting MaxDownloads to {MAX_DOWNLOADS}...")
    print("This will limit how many downloads run simultaneously.")
    print("Sonarr and Radarr will queue downloads, but only 3 will")
    print("download at the same time.\n")
    
    success = set_max_downloads(MAX_DOWNLOADS)
    
    if success:
        print("\n" + "=" * 60)
        print("✓ Configuration updated successfully!")
        print("=" * 60)
        print(f"\nNZBGet will now limit parallel downloads to {MAX_DOWNLOADS}.")
        print("You can queue as many items as you want in Sonarr/Radarr,")
        print("but only 3 will download at once.")
    else:
        print("\n" + "=" * 60)
        print("✗ Failed to update configuration")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

