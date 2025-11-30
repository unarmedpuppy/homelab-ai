#!/usr/bin/env python3
"""
Configure qBittorrent download client in Lidarr.
"""

import requests
import json
import sys

LIDARR_URL = "http://192.168.86.47:8686/api/v1"

# qBittorrent configuration
QBIT_HOST = "media-download-gluetun"
QBIT_PORT = 8080
QBIT_USERNAME = "admin"
QBIT_PASSWORD = "adminadmin"  # Default, may need to check actual password


def get_lidarr_api_key():
    """Get Lidarr API key from user or config."""
    api_key = input("Enter Lidarr API key (or press Enter to get from config): ").strip()
    if not api_key:
        # Try to get from config file
        import subprocess
        try:
            result = subprocess.run(
                ["bash", "scripts/connect-server.sh", 
                 "grep -r 'ApiKey' ~/server/apps/media-download/lidarr/config/config.xml"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and "ApiKey" in result.stdout:
                # Extract API key from XML
                import re
                match = re.search(r'<ApiKey>([^<]+)</ApiKey>', result.stdout)
                if match:
                    api_key = match.group(1)
                    print(f"✓ Found API key from config")
        except:
            pass
    
    if not api_key:
        print("✗ API key required. Get it from Lidarr > Settings > General > Security")
        sys.exit(1)
    
    return api_key


def get_download_clients(api_key):
    """Get all download clients from Lidarr."""
    try:
        response = requests.get(
            f"{LIDARR_URL}/downloadClient",
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


def add_qbittorrent_client(api_key):
    """Add or update qBittorrent download client in Lidarr."""
    print("\n[1/2] Checking existing qBittorrent configuration...")
    
    clients = get_download_clients(api_key)
    qbit_client = None
    
    for client in clients:
        if client.get("implementation") == "Qbittorrent":
            qbit_client = client
            break
    
    if qbit_client:
        print(f"  Found existing qBittorrent client (ID: {qbit_client['id']})")
        update = True
    else:
        print("  No existing qBittorrent client found, creating new one...")
        update = False
    
    # qBittorrent configuration
    qbit_config = {
        "enable": True,
        "protocol": "torrent",
        "priority": 1,
        "removeCompletedDownloads": True,
        "removeFailedDownloads": True,
        "name": "qBittorrent",
        "fields": [
            {
                "order": 0,
                "name": "host",
                "label": "Host",
                "value": QBIT_HOST,
                "type": "textbox",
                "advanced": False
            },
            {
                "order": 1,
                "name": "port",
                "label": "Port",
                "value": QBIT_PORT,
                "type": "textbox",
                "advanced": False
            },
            {
                "order": 2,
                "name": "useSsl",
                "label": "Use SSL",
                "value": False,
                "type": "checkbox",
                "advanced": False
            },
            {
                "order": 3,
                "name": "username",
                "label": "Username",
                "value": QBIT_USERNAME,
                "type": "textbox",
                "advanced": False
            },
            {
                "order": 4,
                "name": "password",
                "label": "Password",
                "value": QBIT_PASSWORD,
                "type": "password",
                "advanced": False
            },
            {
                "order": 5,
                "name": "musicCategory",
                "label": "Category",
                "value": "music",
                "type": "textbox",
                "advanced": False
            },
            {
                "order": 6,
                "name": "musicImportedCategory",
                "label": "Imported Category",
                "value": "lidarr-imported",
                "type": "textbox",
                "advanced": True
            },
            {
                "order": 7,
                "name": "musicFailedCategory",
                "label": "Failed Category",
                "value": "lidarr-failed",
                "type": "textbox",
                "advanced": True
            }
        ],
        "implementationName": "qBittorrent",
        "implementation": "Qbittorrent",
        "configContract": "QbittorrentSettings"
    }
    
    if update:
        qbit_config["id"] = qbit_client["id"]
        url = f"{LIDARR_URL}/downloadClient/{qbit_client['id']}"
        method = "PUT"
        print(f"\n[2/2] Updating qBittorrent client...")
    else:
        url = f"{LIDARR_URL}/downloadClient"
        method = "POST"
        print(f"\n[2/2] Adding qBittorrent client...")
    
    try:
        response = requests.request(
            method,
            url,
            headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
            json=qbit_config,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            print(f"✓ qBittorrent client {'updated' if update else 'added'} successfully")
            
            # Test connection
            print("\n[3/3] Testing connection...")
            test_response = requests.post(
                f"{LIDARR_URL}/downloadClient/test",
                headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
                json=qbit_config,
                timeout=10
            )
            
            if test_response.status_code == 200:
                result = test_response.json()
                if result.get("isValid"):
                    print("✓ Connection test passed!")
                    return True
                else:
                    failures = result.get("validationFailures", [])
                    if failures:
                        print("⚠ Connection test warnings:")
                        for failure in failures:
                            print(f"  - {failure.get('propertyName')}: {failure.get('message')}")
                    return True
            else:
                print(f"⚠ Could not test connection: {test_response.status_code}")
                return True
        else:
            print(f"✗ Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    print("=" * 60)
    print("Configure qBittorrent for Lidarr")
    print("=" * 60)
    
    api_key = get_lidarr_api_key()
    
    success = add_qbittorrent_client(api_key)
    
    if success:
        print("\n" + "=" * 60)
        print("✓ Configuration complete!")
        print("=" * 60)
        print("\nqBittorrent is now configured in Lidarr:")
        print(f"  Host: {QBIT_HOST}")
        print(f"  Port: {QBIT_PORT}")
        print(f"  Username: {QBIT_USERNAME}")
        print(f"  Category: music")
    else:
        print("\n" + "=" * 60)
        print("✗ Configuration failed")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

