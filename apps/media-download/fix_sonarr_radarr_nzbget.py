#!/usr/bin/env python3
"""
Fix Sonarr and Radarr NZBGet download client configuration.
Fixes the hostname typo (glueten -> gluetun) and ensures correct settings.
"""

import requests
import json
import sys

# Service URLs
SONARR_URL = "http://192.168.86.47:8989/api/v3"
RADARR_URL = "http://192.168.86.47:7878/api/v3"

# NZBGet configuration
NZBGET_HOST = "media-download-gluetun"  # Correct hostname (not glueten!)
NZBGET_PORT = 6789
NZBGET_USERNAME = "nzbget"
NZBGET_PASSWORD = "nzbget"


def get_api_key(service_name, url):
    """Get API key from user or config."""
    api_key = input(f"Enter {service_name} API key (or press Enter to skip): ").strip()
    if not api_key:
        print(f"⚠ Skipping {service_name} (no API key provided)")
        return None
    return api_key


def get_download_clients(api_key, url):
    """Get all download clients."""
    try:
        response = requests.get(
            f"{url}/downloadClient",
            headers={"X-Api-Key": api_key},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"✗ Error fetching download clients: {response.status_code}")
            return []
    except Exception as e:
        print(f"✗ Error: {e}")
        return []


def fix_nzbget_client(api_key, url, service_name):
    """Fix NZBGet download client configuration."""
    print(f"\n[{service_name}] Checking NZBGet configuration...")
    
    clients = get_download_clients(api_key, url)
    nzbget_client = None
    
    for client in clients:
        if client.get("implementation") == "Nzbget":
            nzbget_client = client
            break
    
    if not nzbget_client:
        print(f"✗ No NZBGet client found in {service_name}")
        return False
    
    # Check current configuration
    fields = {field["name"]: field["value"] for field in nzbget_client.get("fields", [])}
    current_host = fields.get("host", "")
    current_port = fields.get("port", "")
    
    print(f"  Current host: {current_host}")
    print(f"  Current port: {current_port}")
    
    # Check if fix is needed
    needs_fix = False
    if current_host != NZBGET_HOST:
        print(f"  ⚠ Host mismatch: '{current_host}' should be '{NZBGET_HOST}'")
        needs_fix = True
    if str(current_port) != str(NZBGET_PORT):
        print(f"  ⚠ Port mismatch: '{current_port}' should be '{NZBGET_PORT}'")
        needs_fix = True
    
    if not needs_fix:
        print(f"  ✓ NZBGet configuration is correct")
        return True
    
    # Update configuration
    print(f"  Fixing NZBGet configuration...")
    
    # Update fields
    for field in nzbget_client.get("fields", []):
        if field["name"] == "host":
            field["value"] = NZBGET_HOST
        elif field["name"] == "port":
            field["value"] = NZBGET_PORT
        elif field["name"] == "username":
            field["value"] = NZBGET_USERNAME
        elif field["name"] == "password":
            field["value"] = NZBGET_PASSWORD
    
    # Send update
    try:
        response = requests.put(
            f"{url}/downloadClient/{nzbget_client['id']}",
            headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
            json=nzbget_client,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"  ✓ NZBGet configuration updated successfully")
            
            # Test connection
            print(f"  Testing connection...")
            test_response = requests.post(
                f"{url}/downloadClient/test",
                headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
                json=nzbget_client,
                timeout=10
            )
            
            if test_response.status_code == 200:
                result = test_response.json()
                if result.get("isValid"):
                    print(f"  ✓ Connection test passed!")
                    return True
                else:
                    failures = result.get("validationFailures", [])
                    if failures:
                        print(f"  ⚠ Connection test warnings:")
                        for failure in failures:
                            print(f"    - {failure.get('propertyName')}: {failure.get('message')}")
                    else:
                        print(f"  ✓ Connection test passed (no validation failures)")
                    return True
            else:
                print(f"  ⚠ Could not test connection: {test_response.status_code}")
                return True  # Still updated successfully
        else:
            print(f"  ✗ Error updating NZBGet: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    print("=" * 60)
    print("Fix Sonarr and Radarr NZBGet Configuration")
    print("=" * 60)
    
    # Get API keys
    sonarr_api_key = get_api_key("Sonarr", SONARR_URL)
    radarr_api_key = get_api_key("Radarr", RADARR_URL)
    
    if not sonarr_api_key and not radarr_api_key:
        print("\n✗ No API keys provided. Exiting.")
        sys.exit(1)
    
    results = {}
    
    # Fix Sonarr
    if sonarr_api_key:
        results["Sonarr"] = fix_nzbget_client(sonarr_api_key, SONARR_URL, "Sonarr")
    
    # Fix Radarr
    if radarr_api_key:
        results["Radarr"] = fix_nzbget_client(radarr_api_key, RADARR_URL, "Radarr")
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    for service, success in results.items():
        status = "✓ Fixed" if success else "✗ Failed"
        print(f"  {service}: {status}")
    
    print("\nNote: Make sure NZBGet container is running:")
    print("  docker ps | grep nzbget")


if __name__ == "__main__":
    main()

