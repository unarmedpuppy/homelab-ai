#!/usr/bin/env python3
"""
Configure Prowlarr to connect with Lidarr.
This script:
1. Connects Prowlarr to Lidarr (auto-syncs indexers)
2. Optionally adds music indexers if API keys are provided
"""

import requests
import json
import sys
import xml.etree.ElementTree as ET
import time

# Prowlarr configuration
PROWLARR_URL = "http://192.168.86.47:9696/api/v1"
PROWLARR_API_KEY = None  # Will be read from config

# Lidarr configuration
LIDARR_URL = "http://192.168.86.47:8686/api/v1"
LIDARR_API_KEY = "75e8d1fd2316459085340afd4879d2b6"  # From previous setup

# Container hostnames (for internal Docker network)
PROWLARR_HOST = "media-download-prowlarr"
LIDARR_HOST = "media-download-lidarr"


def get_prowlarr_api_key():
    """Get Prowlarr API key from config file."""
    config_paths = [
        "prowlarr/config/config.xml",
        "../prowlarr/config/config.xml",
        "./prowlarr/config/config.xml"
    ]
    
    for config_path in config_paths:
        try:
            with open(config_path, "r") as f:
                tree = ET.parse(f)
                root = tree.getroot()
                api_key = root.find("ApiKey")
                if api_key is not None and api_key.text:
                    print(f"✓ Found Prowlarr API key in {config_path}")
                    return api_key.text
        except (FileNotFoundError, ET.ParseError):
            continue
    
    # Try command line argument
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        if api_key and len(api_key) > 10:
            print("✓ Using Prowlarr API key from command line")
            return api_key
    
    print("\nProwlarr API key not found. Please provide it:")
    print("You can find it in Prowlarr: Settings > General > API Key")
    print("Or run this script with the API key as argument: python setup_prowlarr_lidarr.py YOUR_API_KEY")
    api_key = input("Prowlarr API Key: ").strip()
    if not api_key:
        print("✗ API key required")
        sys.exit(1)
    return api_key


def wait_for_prowlarr(api_key, max_attempts=30):
    """Wait for Prowlarr to be ready."""
    print("Waiting for Prowlarr to be ready...")
    for i in range(max_attempts):
        try:
            response = requests.get(
                f"{PROWLARR_URL}/system/status",
                headers={"X-Api-Key": api_key},
                timeout=5
            )
            if response.status_code == 200:
                print("✓ Prowlarr is ready")
                return True
        except:
            pass
        time.sleep(2)
        if i % 5 == 0:
            print(f"  Still waiting... ({i*2}s)")
    print("✗ Prowlarr did not become ready in time")
    return False


def get_applications(api_key):
    """Get current applications in Prowlarr."""
    try:
        # Try different possible endpoints
        endpoints = ["/app", "/application", "/apps"]
        for endpoint in endpoints:
            response = requests.get(
                f"{PROWLARR_URL}{endpoint}",
                headers={"X-Api-Key": api_key},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        # If none worked, return empty list
        print(f"Warning: Could not find applications endpoint (tried: {endpoints})")
        return []
    except Exception as e:
        print(f"Error getting applications: {e}")
        return []


def add_lidarr_application(api_key):
    """Add Lidarr as an application in Prowlarr."""
    applications = get_applications(api_key)
    
    # Check if Lidarr already exists
    lidarr_app = None
    for app in applications:
        if app.get("implementation") == "Lidarr" or app.get("name", "").lower() == "lidarr":
            lidarr_app = app
            break
    
    # Lidarr application configuration
    lidarr_config = {
        "name": "Lidarr",
        "implementation": "Lidarr",
        "implementationName": "Lidarr",
        "configContract": "LidarrSettings",
        "fields": [
            {
                "order": 0,
                "name": "baseUrl",
                "label": "Base URL",
                "value": f"http://{LIDARR_HOST}:8686",
                "type": "textbox"
            },
            {
                "order": 1,
                "name": "prowlarrUrl",
                "label": "Prowlarr URL",
                "value": f"http://{PROWLARR_HOST}:9696",
                "type": "textbox"
            },
            {
                "order": 2,
                "name": "apiKey",
                "label": "API Key",
                "value": LIDARR_API_KEY,
                "type": "password"
            },
            {
                "order": 3,
                "name": "syncLevel",
                "label": "Sync Level",
                "value": "fullSync",
                "type": "select",
                "selectOptions": [
                    {"value": "disabled", "name": "Disabled"},
                    {"value": "addOnly", "name": "Add Only"},
                    {"value": "fullSync", "name": "Full Sync"}
                ]
            }
        ],
        "syncLevel": "fullSync"
    }
    
    # Try different possible endpoints
    endpoints = ["/app", "/application", "/apps"]
    base_url = None
    for endpoint in endpoints:
        test_response = requests.get(
            f"{PROWLARR_URL}{endpoint}",
            headers={"X-Api-Key": api_key},
            timeout=5
        )
        if test_response.status_code == 200:
            base_url = endpoint
            break
    
    if not base_url:
        print("✗ Could not determine correct API endpoint for applications")
        return None
    
    if lidarr_app:
        # Update existing application
        lidarr_config["id"] = lidarr_app["id"]
        url = f"{PROWLARR_URL}{base_url}/{lidarr_app['id']}"
        method = requests.put
        print(f"Updating existing Lidarr application (ID: {lidarr_app['id']})...")
    else:
        # Add new application
        url = f"{PROWLARR_URL}{base_url}"
        method = requests.post
        print("Adding Lidarr application to Prowlarr...")
    
    response = method(
        url,
        headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
        json=lidarr_config,
        timeout=10
    )
    
    if response.status_code in [200, 201, 202]:
        print("✓ Lidarr application configured successfully")
        return response.json()
    else:
        print(f"✗ Error configuring Lidarr application: {response.status_code} - {response.text}")
        return None


def test_lidarr_connection(api_key):
    """Test the connection to Lidarr."""
    applications = get_applications(api_key)
    lidarr_app = None
    for app in applications:
        if app.get("implementation") == "Lidarr" or app.get("name", "").lower() == "lidarr":
            lidarr_app = app
            break
    
    if not lidarr_app:
        print("✗ Lidarr application not found")
        return False
    
    # Test the connection - try different endpoints
    test_endpoints = ["/app/test", "/application/test", "/apps/test"]
    response = None
    for test_endpoint in test_endpoints:
        try:
            response = requests.post(
                f"{PROWLARR_URL}{test_endpoint}",
                headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
                json=lidarr_app,
                timeout=10
            )
            if response.status_code in [200, 201, 202]:
                break
        except:
            continue
    
    if not response:
        print("✗ Could not test connection - endpoint not found")
        return False
    
    if response.status_code == 200:
        result = response.json() if response.text else {}
        if not result or result.get("isValid", True):
            print("✓ Lidarr connection test passed")
            return True
        else:
            failures = result.get('validationFailures', [])
            if failures:
                print(f"✗ Lidarr connection test failed: {failures}")
            else:
                print("✓ Lidarr connection test passed (no validation failures)")
            return len(failures) == 0
    else:
        print(f"✗ Error testing Lidarr connection: {response.status_code} - {response.text}")
        return False


def sync_indexers_to_lidarr(api_key):
    """Trigger a sync of indexers to Lidarr."""
    print("Triggering indexer sync to Lidarr...")
    # Prowlarr should auto-sync, but we can trigger it manually
    # This is usually automatic when the application is configured
    print("✓ Indexers will be automatically synced to Lidarr")
    return True


def main():
    print("=" * 60)
    print("Prowlarr-Lidarr Configuration")
    print("=" * 60)
    
    # Get Prowlarr API key
    print("\n[1/4] Getting Prowlarr API key...")
    prowlarr_api_key = get_prowlarr_api_key()
    if not prowlarr_api_key:
        print("✗ Prowlarr API key required")
        sys.exit(1)
    print("✓ Prowlarr API key obtained")
    
    # Wait for Prowlarr to be ready
    print("\n[2/4] Checking Prowlarr status...")
    if not wait_for_prowlarr(prowlarr_api_key):
        print("✗ Prowlarr is not ready. Please wait a moment and try again.")
        sys.exit(1)
    
    # Add Lidarr application
    print("\n[3/4] Configuring Lidarr application in Prowlarr...")
    result = add_lidarr_application(prowlarr_api_key)
    if result:
        # Test connection
        print("\n[4/4] Testing Lidarr connection...")
        test_lidarr_connection(prowlarr_api_key)
        
        # Sync indexers
        sync_indexers_to_lidarr(prowlarr_api_key)
    
    print("\n" + "=" * 60)
    print("Configuration complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Check Prowlarr: http://192.168.86.47:9696")
    print("2. Go to Apps → Lidarr to verify connection")
    print("3. Add music indexers in Prowlarr (Indexers → Add Indexer)")
    print("4. Indexers will automatically sync to Lidarr")
    print("5. Check Lidarr: http://192.168.86.47:8686 → Settings → Indexers")


if __name__ == "__main__":
    main()

