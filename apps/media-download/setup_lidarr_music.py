#!/usr/bin/env python3
"""
Complete setup for Lidarr music downloads:
1. Enable existing indexers
2. Configure music categories
3. Connect Prowlarr to Lidarr
4. Verify configuration
"""

import requests
import json
import sys
import xml.etree.ElementTree as ET
import subprocess

LIDARR_URL = "http://192.168.86.47:8686/api/v1"
LIDARR_API_KEY = "75e8d1fd2316459085340afd4879d2b6"
PROWLARR_URL = "http://192.168.86.47:9696/api/v1"

MUSIC_CATEGORIES = [3000, 3010, 3040]  # Music, MP3, Lossless


def get_prowlarr_api_key():
    """Get Prowlarr API key from config file."""
    try:
        result = subprocess.run(
            ["bash", "scripts/connect-server.sh", 
             "grep -r 'ApiKey' ~/server/apps/media-download/prowlarr/config/config.xml"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and "ApiKey" in result.stdout:
            import re
            match = re.search(r'<ApiKey>([^<]+)</ApiKey>', result.stdout)
            if match:
                return match.group(1)
    except:
        pass
    return None


def enable_lidarr_indexers():
    """Enable and configure indexers in Lidarr."""
    print("\n[1/3] Enabling Lidarr Indexers...")
    
    response = requests.get(
        f"{LIDARR_URL}/indexer",
        headers={"X-Api-Key": LIDARR_API_KEY},
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"✗ Error fetching indexers: {response.status_code}")
        return False
    
    indexers = response.json()
    enabled = 0
    
    for idx in indexers:
        name = idx.get("name", "Unknown")
        idx_id = idx.get("id")
        currently_enabled = idx.get("enable", False)
        
        if currently_enabled:
            print(f"  ✓ {name}: Already enabled")
            enabled += 1
            continue
        
        # Enable it
        idx["enable"] = True
        
        # Set music categories
        for field in idx.get("fields", []):
            if field.get("name") == "categories":
                current = field.get("value", [])
                if isinstance(current, list):
                    combined = list(set(current + MUSIC_CATEGORIES))
                    field["value"] = combined
                else:
                    field["value"] = MUSIC_CATEGORIES
        
        try:
            update_response = requests.put(
                f"{LIDARR_URL}/indexer/{idx_id}",
                headers={"X-Api-Key": LIDARR_API_KEY, "Content-Type": "application/json"},
                json=idx,
                timeout=10
            )
            
            # 202 is also success (Accepted)
            if update_response.status_code in [200, 202]:
                print(f"  ✓ {name}: Enabled")
                enabled += 1
            else:
                print(f"  ⚠ {name}: API returned {update_response.status_code}")
                # Still count as enabled if it's a validation warning
                if update_response.status_code == 202:
                    enabled += 1
        except Exception as e:
            print(f"  ✗ {name}: Error - {e}")
    
    return enabled > 0


def connect_prowlarr_to_lidarr():
    """Connect Prowlarr to Lidarr."""
    print("\n[2/3] Connecting Prowlarr to Lidarr...")
    
    prowlarr_api_key = get_prowlarr_api_key()
    
    if not prowlarr_api_key:
        print("  ⚠ Could not get Prowlarr API key automatically")
        print("  You'll need to connect manually:")
        print("    1. Open Prowlarr: http://192.168.86.47:9696")
        print("    2. Apps > Add Application > Lidarr")
        print(f"    3. Lidarr URL: http://media-download-lidarr:8686")
        print(f"    4. API Key: {LIDARR_API_KEY}")
        return False
    
    # Check if already connected
    try:
        response = requests.get(
            f"{PROWLARR_URL}/application",
            headers={"X-Api-Key": prowlarr_api_key},
            timeout=10
        )
        if response.status_code == 200:
            apps = response.json()
            lidarr_app = [a for a in apps if a.get("name", "").lower() == "lidarr"]
            if lidarr_app:
                print(f"  ✓ Prowlarr already connected to Lidarr")
                return True
    except:
        pass
    
    # Add Lidarr to Prowlarr
    lidarr_app = {
        "name": "Lidarr",
        "implementation": "Lidarr",
        "implementationName": "Lidarr",
        "configContract": "LidarrSettings",
        "fields": [
            {
                "order": 0,
                "name": "baseUrl",
                "label": "Base URL",
                "value": "http://media-download-lidarr:8686",
                "type": "textbox"
            },
            {
                "order": 1,
                "name": "apiKey",
                "label": "API Key",
                "value": LIDARR_API_KEY,
                "type": "textbox"
            },
            {
                "order": 2,
                "name": "syncLevel",
                "label": "Sync Level",
                "value": "addAndRemoveOnly",
                "type": "select"
            }
        ],
        "syncLevel": "addAndRemoveOnly"
    }
    
    try:
        response = requests.post(
            f"{PROWLARR_URL}/application",
            headers={"X-Api-Key": prowlarr_api_key, "Content-Type": "application/json"},
            json=lidarr_app,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            print(f"  ✓ Prowlarr connected to Lidarr")
            return True
        else:
            print(f"  ⚠ Failed to connect: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def verify_configuration():
    """Verify the configuration is working."""
    print("\n[3/3] Verifying Configuration...")
    
    # Check indexers
    response = requests.get(
        f"{LIDARR_URL}/indexer",
        headers={"X-Api-Key": LIDARR_API_KEY},
        timeout=10
    )
    
    if response.status_code == 200:
        indexers = response.json()
        enabled = [idx for idx in indexers if idx.get("enable")]
        
        print(f"  Indexers: {len(enabled)} enabled, {len(indexers) - len(enabled)} disabled")
        
        if len(enabled) > 0:
            print(f"  ✓ At least one indexer is enabled")
        else:
            print(f"  ⚠ No indexers enabled - enable manually in Lidarr UI")
    
    # Check download clients
    response = requests.get(
        f"{LIDARR_URL}/downloadClient",
        headers={"X-Api-Key": LIDARR_API_KEY},
        timeout=10
    )
    
    if response.status_code == 200:
        clients = response.json()
        enabled_clients = [c for c in clients if c.get("enable")]
        
        print(f"  Download Clients: {len(enabled_clients)} enabled")
        
        if len(enabled_clients) > 0:
            print(f"  ✓ Download clients configured")
        else:
            print(f"  ⚠ No download clients enabled")


def main():
    print("=" * 60)
    print("Complete Lidarr Music Setup")
    print("=" * 60)
    
    # Step 1: Enable indexers
    indexers_ok = enable_lidarr_indexers()
    
    # Step 2: Connect Prowlarr
    prowlarr_ok = connect_prowlarr_to_lidarr()
    
    # Step 3: Verify
    verify_configuration()
    
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    
    print("\nSummary:")
    if indexers_ok:
        print("  ✓ Indexers enabled")
    else:
        print("  ⚠ Indexers may need manual enabling")
    
    if prowlarr_ok:
        print("  ✓ Prowlarr connected")
    else:
        print("  ⚠ Prowlarr connection may need manual setup")
    
    print("\nNext Steps:")
    print("1. Test indexers in Lidarr: Settings > Indexers > Test each one")
    print("2. Try searching for music - should find results now")
    print("3. If still no results, add music indexers:")
    print("   - NZBGeek ($15 lifetime) - Add to Prowlarr or NZBHydra2")
    print("   - DrunkenSlug ($10/year) - Add to Prowlarr or NZBHydra2")
    print("\nFor rare music, consider:")
    print("  - Tubifarry plugin (YouTube + Soulseek)")
    print("  - See: apps/media-download/LIDARR_MUSIC_INDEXERS.md")


if __name__ == "__main__":
    main()

