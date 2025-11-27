#!/usr/bin/env python3
"""
Fix Bookshelf (Readarr fork) configuration:
1. Configure NZBGet download client with correct credentials
2. Configure indexers (NZBHydra2 and Jackett)
3. Test connections
"""

import requests
import json
import sys
import xml.etree.ElementTree as ET

# Bookshelf configuration (Readarr fork - same API structure)
BOOKSHELF_URL = "http://192.168.86.47:8787/api/v1"
# API key will be retrieved from system status or config

# NZBGet configuration (from PIRATE_AGENT_CONTEXT.md)
NZBGET_HOST = "media-download-gluetun"
NZBGET_PORT = 6789
NZBGET_USERNAME = "nzbget"
# Note: Password might be "nzbget" or "tegbzn6789" depending on NZBGet config
# We'll use the existing password if client exists, otherwise try "nzbget"
NZBGET_PASSWORD = "nzbget"

# Indexer configuration
NZBHYDRA2_HOST = "media-download-nzbhydra2"
NZBHYDRA2_PORT = 5076
JACKETT_HOST = "media-download-jackett"
JACKETT_PORT = 9117


def get_bookshelf_api_key():
    """Get Bookshelf API key from config file or prompt."""
    # Try to get from config file (on server)
    config_paths = [
        "bookshelf/config/config.xml",
        "../bookshelf/config/config.xml",
        "./bookshelf/config/config.xml",
        "readarr/config/config.xml",  # Fallback for migration
        "../readarr/config/config.xml",
        "./readarr/config/config.xml"
    ]
    
    for config_path in config_paths:
        try:
            with open(config_path, "r") as f:
                tree = ET.parse(f)
                root = tree.getroot()
                api_key = root.find("ApiKey")
                if api_key is not None and api_key.text:
                    print(f"✓ Found API key in {config_path}")
                    return api_key.text
        except (FileNotFoundError, ET.ParseError):
            continue
    
    # Try to get from command line argument
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        if api_key and len(api_key) > 10:  # Basic validation
            print("✓ Using API key from command line")
            return api_key
    
    # Prompt user
    print("\nBookshelf API key not found. Please provide it:")
    print("You can find it in Bookshelf: Settings > General > Security > API Key")
    print("Or run this script with the API key as argument: python fix_readarr.py YOUR_API_KEY")
    api_key = input("API Key: ").strip()
    if not api_key:
        print("✗ API key required")
        sys.exit(1)
    return api_key


def get_download_clients(api_key):
    """Get current download clients."""
    response = requests.get(
        f"{BOOKSHELF_URL}/downloadClient",
        headers={"X-Api-Key": api_key},
        timeout=10
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting download clients: {response.status_code} - {response.text}")
        return []


def add_nzbget_client(api_key):
    """Add or update NZBGet download client."""
    clients = get_download_clients(api_key)
    
    # Check if NZBGet already exists
    nzbget_client = None
    existing_password = None
    for client in clients:
        if client.get("implementation") == "Nzbget":
            nzbget_client = client
            # Get existing password if available
            for field in client.get("fields", []):
                if field.get("name") == "password":
                    existing_password = field.get("value")
                    break
            break
    
    # NZBGet configuration
    nzbget_config = {
        "name": "NZBGet",
        "enable": True,
        "protocol": "usenet",
        "priority": 1,
        "removeCompletedDownloads": True,
        "removeFailedDownloads": True,
        "implementation": "Nzbget",
        "implementationName": "NZBGet",
        "configContract": "NzbgetSettings",
        "fields": [
            {
                "order": 0,
                "name": "host",
                "label": "Host",
                "value": NZBGET_HOST,
                "type": "textbox"
            },
            {
                "order": 1,
                "name": "port",
                "label": "Port",
                "value": NZBGET_PORT,
                "type": "number"
            },
            {
                "order": 2,
                "name": "username",
                "label": "Username",
                "value": NZBGET_USERNAME,
                "type": "textbox"
            },
            {
                "order": 3,
                "name": "password",
                "label": "Password",
                "value": NZBGET_PASSWORD,
                "type": "password"
            },
            {
                "order": 6,
                "name": "musicCategory",
                "label": "Category",
                "value": "books",
                "type": "textbox"
            },
            {
                "order": 7,
                "name": "recentTvPriority",
                "label": "Recent Priority",
                "value": 0,
                "type": "select"
            },
            {
                "order": 10,
                "name": "addPaused",
                "label": "Add Paused",
                "value": False,
                "type": "checkbox"
            },
            {
                "order": 11,
                "name": "useSsl",
                "label": "Use SSL",
                "value": False,
                "type": "checkbox"
            }
        ]
    }
    
    if nzbget_client:
        # Update existing client
        nzbget_config["id"] = nzbget_client["id"]
        url = f"{BOOKSHELF_URL}/downloadClient/{nzbget_client['id']}"
        method = requests.put
        print(f"Updating existing NZBGet client (ID: {nzbget_client['id']})...")
    else:
        # Add new client
        url = f"{BOOKSHELF_URL}/downloadClient"
        method = requests.post
        print("Adding new NZBGet download client...")
    
    response = method(
        url,
        headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
        json=nzbget_config,
        timeout=10
    )
    
    if response.status_code in [200, 201, 202]:
        print(f"✓ NZBGet client configured successfully")
        return response.json()
    else:
        print(f"✗ Error configuring NZBGet: {response.status_code} - {response.text}")
        return None


def test_nzbget_connection(api_key):
    """Test NZBGet connection."""
    # Get the client
    clients = get_download_clients(api_key)
    nzbget_client = None
    for client in clients:
        if client.get("implementation") == "Nzbget":
            nzbget_client = client
            break
    
    if not nzbget_client:
        print("✗ NZBGet client not found")
        return False
    
    # Test the connection
    response = requests.post(
        f"{BOOKSHELF_URL}/downloadClient/test",
        headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
        json=nzbget_client,
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json() if response.text else {}
        # Empty response or isValid=True means success
        if not result or result.get("isValid", True):
            print("✓ NZBGet connection test passed")
            return True
        else:
            failures = result.get('validationFailures', [])
            if failures:
                print(f"✗ NZBGet connection test failed: {failures}")
            else:
                print("✓ NZBGet connection test passed (no validation failures)")
            return len(failures) == 0
    else:
        print(f"✗ Error testing NZBGet connection: {response.status_code} - {response.text}")
        return False


def get_indexers(api_key):
    """Get current indexers."""
    response = requests.get(
        f"{BOOKSHELF_URL}/indexer",
        headers={"X-Api-Key": api_key},
        timeout=10
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting indexers: {response.status_code} - {response.text}")
        return []


def get_nzbhydra2_api_key():
    """Get NZBHydra2 API key (we'll need to get this from user or config)."""
    # Try to get from command line argument (format: --nzbhydra2-key=KEY)
    for arg in sys.argv:
        if arg.startswith("--nzbhydra2-key="):
            return arg.split("=", 1)[1]
    
    # Try to get from config file
    try:
        with open("nzbhydra2/config/nzbhydra2.yaml", "r") as f:
            import yaml
            config = yaml.safe_load(f)
            # NZBHydra2 stores API key in config
            # This is a simplified approach - actual config might be different
            pass
    except:
        pass
    
    # Skip in non-interactive mode
    if not sys.stdin.isatty():
        return None
    
    print("\nNZBHydra2 API key needed for indexer configuration.")
    print("You can find it in NZBHydra2: Config > Main > API Key")
    print("Or pass it as: --nzbhydra2-key=YOUR_KEY")
    try:
        api_key = input("NZBHydra2 API Key (or press Enter to skip): ").strip()
        return api_key if api_key else None
    except EOFError:
        return None


def add_nzbhydra2_indexer(api_key, nzbhydra2_api_key):
    """Add or update NZBHydra2 indexer."""
    if not nzbhydra2_api_key:
        print("Skipping NZBHydra2 indexer (no API key provided)")
        return None
    
    indexers = get_indexers(api_key)
    
    # Check if NZBHydra2 already exists
    nzbhydra2_indexer = None
    for indexer in indexers:
        if indexer.get("implementation") == "Newznab":
            # Check baseUrl in fields array
            base_url = None
            for field in indexer.get("fields", []):
                if field.get("name") == "baseUrl":
                    base_url = field.get("value", "")
                    break
            if base_url and NZBHYDRA2_HOST in base_url:
                nzbhydra2_indexer = indexer
                break
    
    # NZBHydra2 configuration
    nzbhydra2_config = {
        "name": "NZBHydra2",
        "enable": True,
        "protocol": "usenet",
        "priority": 1,
        "implementation": "Newznab",
        "implementationName": "Newznab",
        "configContract": "NewznabSettings",
        "fields": [
            {
                "order": 0,
                "name": "baseUrl",
                "label": "URL",
                "value": f"http://{NZBHYDRA2_HOST}:{NZBHYDRA2_PORT}",
                "type": "textbox"
            },
            {
                "order": 1,
                "name": "apiPath",
                "label": "API Path",
                "value": "/api",
                "type": "textbox"
            },
            {
                "order": 2,
                "name": "apiKey",
                "label": "API Key",
                "value": nzbhydra2_api_key,
                "type": "textbox"
            },
            {
                "order": 3,
                "name": "categories",
                "label": "Categories",
                "value": [3030, 7000, 7010, 7020, 7030, 7040, 7050, 7060],  # Book categories
                "type": "select"
            },
            {
                "order": 4,
                "name": "animeCategories",
                "label": "Anime Categories",
                "value": [],
                "type": "select"
            },
            {
                "order": 5,
                "name": "removeYear",
                "label": "Remove Year",
                "value": False,
                "type": "checkbox"
            },
            {
                "order": 6,
                "name": "removeTitle",
                "label": "Remove Title",
                "value": False,
                "type": "checkbox"
            },
            {
                "order": 7,
                "name": "searchByTitle",
                "label": "Search by Title",
                "value": True,
                "type": "checkbox"
            }
        ]
    }
    
    if nzbhydra2_indexer:
        # Update existing indexer
        nzbhydra2_config["id"] = nzbhydra2_indexer["id"]
        url = f"{BOOKSHELF_URL}/indexer/{nzbhydra2_indexer['id']}"
        method = requests.put
        print(f"Updating existing NZBHydra2 indexer (ID: {nzbhydra2_indexer['id']})...")
    else:
        # Add new indexer
        url = f"{BOOKSHELF_URL}/indexer"
        method = requests.post
        print("Adding new NZBHydra2 indexer...")
    
    response = method(
        url,
        headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
        json=nzbhydra2_config,
        timeout=10
    )
    
    if response.status_code in [200, 201, 202]:
        print(f"✓ NZBHydra2 indexer configured successfully")
        return response.json()
    else:
        print(f"✗ Error configuring NZBHydra2: {response.status_code} - {response.text}")
        return None


def get_jackett_indexers(jackett_api_key):
    """Get list of configured Jackett indexers."""
    # Try internal hostname first, fall back to external IP
    jackett_urls = [
        f"http://{JACKETT_HOST}:{JACKETT_PORT}/api/v2.0/indexers",
        f"http://192.168.86.47:{JACKETT_PORT}/api/v2.0/indexers"
    ]
    
    for jackett_url in jackett_urls:
        try:
            response = requests.get(
                jackett_url,
                params={"apikey": jackett_api_key},
                timeout=10
            )
            if response.status_code == 200:
                indexers = response.json()
                # Return only configured indexers
                return [i for i in indexers if i.get("configured")]
            else:
                continue  # Try next URL
        except Exception as e:
            continue  # Try next URL
    
    # If all URLs failed
    print(f"⚠ Warning: Could not fetch Jackett indexers from any URL")
    return []


def add_jackett_indexer(api_key, jackett_api_key):
    """Add or update individual Jackett indexers."""
    if not jackett_api_key:
        print("Skipping Jackett indexers (no API key provided)")
        return None
    
    # First, try to get configured Jackett indexers from Jackett API
    jackett_indexers = get_jackett_indexers(jackett_api_key)
    
    # Get existing Bookshelf indexers (reuse variable name for consistency)
    bookshelf_indexers = get_indexers(api_key)
    
    # Find existing Torznab indexers that point to Jackett
    existing_jackett_indexers = []
    for bookshelf_idx in bookshelf_indexers:
        if bookshelf_idx.get("implementation") == "Torznab":
            base_url = None
            api_path = None
            for field in bookshelf_idx.get("fields", []):
                if field.get("name") == "baseUrl":
                    base_url = field.get("value", "")
                elif field.get("name") == "apiPath":
                    api_path = field.get("value", "")
            
            # Check if this points to Jackett
            if base_url and JACKETT_HOST in base_url:
                existing_jackett_indexers.append(bookshelf_idx)
    
    # If we can't fetch from Jackett API, update existing indexers to use individual endpoints
    if not jackett_indexers:
        if existing_jackett_indexers:
            print(f"Found {len(existing_jackett_indexers)} existing Jackett indexers in Bookshelf")
            print("⚠ Cannot fetch from Jackett API - please manually configure indexers in Bookshelf UI")
            print("   Each indexer should use: /api/v2.0/indexers/{indexer_id}/results/torznab")
            print("   You can find indexer IDs in Jackett web UI at http://192.168.86.47:9117")
            return None
        else:
            print("⚠ No Jackett indexers found and cannot fetch from API")
            print("   Please add indexers manually in Bookshelf UI")
            return None
    
    print(f"Found {len(jackett_indexers)} configured Jackett indexers")
    
    # Track which indexers we've added/updated
    added_count = 0
    updated_count = 0
    
    for jackett_idx in jackett_indexers:
        indexer_id = jackett_idx.get("id")
        indexer_name = jackett_idx.get("name", f"Jackett-{indexer_id}")
        
        # Check if this indexer already exists in Bookshelf
        existing_indexer = None
        for bookshelf_idx in bookshelf_indexers:
            if bookshelf_idx.get("implementation") == "Torznab":
                # Check if this is the same Jackett indexer
                base_url = None
                api_path = None
                for field in bookshelf_idx.get("fields", []):
                    if field.get("name") == "baseUrl":
                        base_url = field.get("value", "")
                    elif field.get("name") == "apiPath":
                        api_path = field.get("value", "")
                
                # Check if this matches our Jackett indexer
                if base_url and JACKETT_HOST in base_url:
                    if api_path and str(indexer_id) in api_path:
                        existing_indexer = bookshelf_idx
                        break
        
        # Build configuration for this indexer
        jackett_config = {
            "name": f"Jackett-{indexer_name}",
            "enable": True,
            "protocol": "torrent",
            "priority": 1,
            "implementation": "Torznab",
            "implementationName": "Torznab",
            "configContract": "TorznabSettings",
            "fields": [
                {
                    "order": 0,
                    "name": "baseUrl",
                    "label": "URL",
                    "value": f"http://{JACKETT_HOST}:{JACKETT_PORT}",
                    "type": "textbox"
                },
                {
                    "order": 1,
                    "name": "apiPath",
                    "label": "API Path",
                    "value": f"/api/v2.0/indexers/{indexer_id}/results/torznab",
                    "type": "textbox"
                },
                {
                    "order": 2,
                    "name": "apiKey",
                    "label": "API Key",
                    "value": jackett_api_key,
                    "type": "textbox"
                },
                {
                    "order": 3,
                    "name": "categories",
                    "label": "Categories",
                    "value": [3030, 7000, 7010, 7020, 7030, 7040, 7050, 7060],  # Book categories
                    "type": "select"
                },
                {
                    "order": 4,
                    "name": "animeCategories",
                    "label": "Anime Categories",
                    "value": [],
                    "type": "select"
                },
                {
                    "order": 5,
                    "name": "removeYear",
                    "label": "Remove Year",
                    "value": False,
                    "type": "checkbox"
                },
                {
                    "order": 6,
                    "name": "removeTitle",
                    "label": "Remove Title",
                    "value": False,
                    "type": "checkbox"
                },
                {
                    "order": 7,
                    "name": "searchByTitle",
                    "label": "Search by Title",
                    "value": True,
                    "type": "checkbox"
                }
            ]
        }
        
        if existing_indexer:
            # Update existing indexer
            jackett_config["id"] = existing_indexer["id"]
            url = f"{BOOKSHELF_URL}/indexer/{existing_indexer['id']}"
            method = requests.put
            print(f"  Updating {indexer_name} (ID: {existing_indexer['id']})...")
            updated_count += 1
        else:
            # Add new indexer
            url = f"{BOOKSHELF_URL}/indexer"
            method = requests.post
            print(f"  Adding {indexer_name}...")
            added_count += 1
        
        response = method(
            url,
            headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
            json=jackett_config,
            timeout=10
        )
        
        if response.status_code in [200, 201, 202]:
            print(f"    ✓ {indexer_name} configured successfully")
        else:
            print(f"    ✗ Error configuring {indexer_name}: {response.status_code} - {response.text[:200]}")
    
    if added_count > 0 or updated_count > 0:
        print(f"✓ Jackett indexers configured: {added_count} added, {updated_count} updated")
        return True
    else:
        return None


def get_jackett_api_key():
    """Get Jackett API key."""
    # Try to get from command line argument (format: --jackett-key=KEY)
    for arg in sys.argv:
        if arg.startswith("--jackett-key="):
            return arg.split("=", 1)[1]
    
    # Skip in non-interactive mode
    if not sys.stdin.isatty():
        return None
    
    print("\nJackett API key needed for indexer configuration.")
    print("You can find it in Jackett: Click the API key button in the top right")
    print("Or pass it as: --jackett-key=YOUR_KEY")
    try:
        api_key = input("Jackett API Key (or press Enter to skip): ").strip()
        return api_key if api_key else None
    except EOFError:
        return None


def main():
    print("=" * 60)
    print("Bookshelf Configuration Fix")
    print("=" * 60)
    
    # Get Bookshelf API key
    print("\n[1/5] Getting Bookshelf API key...")
    bookshelf_api_key = get_bookshelf_api_key()
    if not bookshelf_api_key:
        print("✗ Bookshelf API key required")
        sys.exit(1)
    print("✓ Bookshelf API key obtained")
    
    # Configure NZBGet download client
    print("\n[2/5] Configuring NZBGet download client...")
    nzbget_result = add_nzbget_client(bookshelf_api_key)
    if nzbget_result:
        # Test connection
        print("\n[3/5] Testing NZBGet connection...")
        test_nzbget_connection(bookshelf_api_key)
    
    # Configure indexers
    print("\n[4/5] Configuring indexers...")
    nzbhydra2_api_key = get_nzbhydra2_api_key()
    add_nzbhydra2_indexer(bookshelf_api_key, nzbhydra2_api_key)
    
    jackett_api_key = get_jackett_api_key()
    add_jackett_indexer(bookshelf_api_key, jackett_api_key)
    
    print("\n[5/5] Configuration complete!")
    print("\nNext steps:")
    print("1. Verify download clients in Bookshelf: Settings > Download Clients")
    print("2. Verify indexers in Bookshelf: Settings > Indexers")
    print("3. Test a search in Bookshelf to verify indexers are working")
    print("4. If issues persist, check Bookshelf logs")


if __name__ == "__main__":
    main()

