#!/usr/bin/env python3
"""
Configure LazyLibrarian indexers and download clients.
This script sets up NZBHydra2 and Jackett indexers, and NZBGet download client.
"""

import requests
import json
import sys

LAZYLIBRARIAN_URL = "http://192.168.86.47:8787"

# Indexer configuration
NZBHYDRA2_HOST = "media-download-nzbhydra2"
NZBHYDRA2_PORT = 5076
NZBHYDRA2_API_KEY = "2SQ42T9209NUIQCAJTPBMTLBJF"

JACKETT_HOST = "media-download-jackett"
JACKETT_PORT = 9117
JACKETT_API_KEY = "orjbnk0p7ar5s2u521emxrwb8cjvrz8c"

# Download client configuration
NZBGET_HOST = "media-download-gluetun"
NZBGET_PORT = 6789
NZBGET_USERNAME = "nzbget"
NZBGET_PASSWORD = "nzbget"

def get_lazylibrarian_api_key():
    """Get LazyLibrarian API key from config file."""
    try:
        with open("lazylibrarian/config/config.ini", "r") as f:
            for line in f:
                if line.startswith("api_key"):
                    return line.split("=", 1)[1].strip()
    except:
        pass
    
    # Try server path
    try:
        import subprocess
        result = subprocess.run(
            ["bash", "scripts/connect-server.sh", "grep '^api_key' ~/server/apps/media-download/lazylibrarian/config/config.ini | cut -d'=' -f2"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except:
        pass
    
    print("\nLazyLibrarian API key not found.")
    print("You can find it in LazyLibrarian: Config > General > API Key")
    print("Or run this script with the API key as argument: python configure_lazylibrarian.py YOUR_API_KEY")
    
    if len(sys.argv) > 1:
        return sys.argv[1]
    
    api_key = input("API Key (or press Enter to skip API configuration): ").strip()
    return api_key if api_key else None

def configure_nzbhydra2(api_key):
    """Configure NZBHydra2 indexer."""
    if not api_key:
        print("Skipping NZBHydra2 (no API key)")
        return False
    
    print("\n[1/3] Configuring NZBHydra2 indexer...")
    
    # LazyLibrarian uses Newznab format for NZBHydra2
    params = {
        "cmd": "addIndexer",
        "apikey": api_key,
        "name": "NZBHydra2",
        "host": f"http://{NZBHYDRA2_HOST}:{NZBHYDRA2_PORT}",
        "apipath": "/api",
        "apikey_indexer": NZBHYDRA2_API_KEY,
        "enabled": "True",
        "type": "newznab"
    }
    
    try:
        response = requests.get(f"{LAZYLIBRARIAN_URL}/api", params=params, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("result") == "success":
                print("✓ NZBHydra2 configured successfully")
                return True
            else:
                print(f"✗ Error: {result.get('message', 'Unknown error')}")
        else:
            print(f"✗ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    return False

def configure_jackett(api_key):
    """Configure Jackett indexer."""
    if not api_key:
        print("Skipping Jackett (no API key)")
        return False
    
    print("\n[2/3] Configuring Jackett indexer...")
    
    # Get list of Jackett indexers
    try:
        jackett_response = requests.get(
            f"http://{JACKETT_HOST}:{JACKETT_PORT}/api/v2.0/indexers/all/results/torznab",
            params={"apikey": JACKETT_API_KEY, "t": "caps"},
            timeout=10
        )
        
        if jackett_response.status_code == 200:
            print("✓ Jackett connection verified")
            
            # LazyLibrarian uses Torznab format for Jackett
            params = {
                "cmd": "addIndexer",
                "apikey": api_key,
                "name": "Jackett",
                "host": f"http://{JACKETT_HOST}:{JACKETT_PORT}",
                "apipath": "/api/v2.0/indexers/all/results/torznab",
                "apikey_indexer": JACKETT_API_KEY,
                "enabled": "True",
                "type": "torznab"
            }
            
            response = requests.get(f"{LAZYLIBRARIAN_URL}/api", params=params, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get("result") == "success":
                    print("✓ Jackett configured successfully")
                    return True
                else:
                    print(f"✗ Error: {result.get('message', 'Unknown error')}")
        else:
            print(f"✗ Could not connect to Jackett: {jackett_response.status_code}")
    except Exception as e:
        print(f"✗ Error configuring Jackett: {e}")
    
    return False

def configure_nzbget(api_key):
    """Configure NZBGet download client."""
    if not api_key:
        print("Skipping NZBGet (no API key)")
        return False
    
    print("\n[3/3] Configuring NZBGet download client...")
    
    params = {
        "cmd": "setDownloader",
        "apikey": api_key,
        "downloader": "nzbget",
        "nzbget_host": NZBGET_HOST,
        "nzbget_port": str(NZBGET_PORT),
        "nzbget_username": NZBGET_USERNAME,
        "nzbget_password": NZBGET_PASSWORD,
        "nzbget_category": "books",
        "nzbget_priority": "0"
    }
    
    try:
        response = requests.get(f"{LAZYLIBRARIAN_URL}/api", params=params, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("result") == "success":
                print("✓ NZBGet configured successfully")
                return True
            else:
                print(f"✗ Error: {result.get('message', 'Unknown error')}")
        else:
            print(f"✗ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    return False

def main():
    print("=" * 60)
    print("LazyLibrarian Configuration")
    print("=" * 60)
    
    api_key = get_lazylibrarian_api_key()
    
    if not api_key:
        print("\n⚠ No API key provided. Configuration will be skipped.")
        print("\nTo configure manually:")
        print("1. Open LazyLibrarian: http://192.168.86.47:8787")
        print("2. Go to Config > Search Providers")
        print("3. Add NZBHydra2:")
        print(f"   - Name: NZBHydra2")
        print(f"   - Host: http://{NZBHYDRA2_HOST}:{NZBHYDRA2_PORT}")
        print(f"   - API Path: /api")
        print(f"   - API Key: {NZBHYDRA2_API_KEY}")
        print("4. Add Jackett:")
        print(f"   - Name: Jackett")
        print(f"   - Host: http://{JACKETT_HOST}:{JACKETT_PORT}")
        print(f"   - API Path: /api/v2.0/indexers/all/results/torznab")
        print(f"   - API Key: {JACKETT_API_KEY}")
        print("5. Go to Config > Downloaders")
        print("6. Configure NZBGet:")
        print(f"   - Host: {NZBGET_HOST}")
        print(f"   - Port: {NZBGET_PORT}")
        print(f"   - Username: {NZBGET_USERNAME}")
        print(f"   - Password: {NZBGET_PASSWORD}")
        return
    
    configure_nzbhydra2(api_key)
    configure_jackett(api_key)
    configure_nzbget(api_key)
    
    print("\n" + "=" * 60)
    print("Configuration complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Verify indexers in LazyLibrarian: Config > Search Providers")
    print("2. Verify download client in LazyLibrarian: Config > Downloaders")
    print("3. Add books to your wishlist")
    print("4. LazyLibrarian will automatically search and download!")

if __name__ == "__main__":
    main()

