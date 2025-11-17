#!/usr/bin/env python3
"""
Add music indexers to Prowlarr.
This script adds common music-focused Usenet indexers to Prowlarr.
"""

import requests
import json
import sys
import xml.etree.ElementTree as ET

# Prowlarr configuration
PROWLARR_URL = "http://192.168.86.47:9696/api/v1"
PROWLARR_API_KEY = None  # Will be read from config

# Common music indexers (user will need to provide API keys)
INDEXERS = {
    "NZBGeek": {
        "implementation": "Newznab",
        "baseUrl": "https://api.nzbgeek.info/api",
        "description": "Most popular, good music coverage - $15 lifetime"
    },
    "DrunkenSlug": {
        "implementation": "Newznab",
        "baseUrl": "https://api.drunkenslug.com",
        "description": "Excellent automation, good catalog - $10/year"
    },
    "NZBPlanet": {
        "implementation": "Newznab",
        "baseUrl": "https://www.nzbplanet.net",
        "description": "Solid coverage, affordable - $10/year"
    }
}

# Music categories for indexers
MUSIC_CATEGORIES = [3000, 3010, 3040]  # 3000=Music, 3010=MP3, 3040=Lossless


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
    api_key = input("Prowlarr API Key: ").strip()
    if not api_key:
        print("✗ API key required")
        sys.exit(1)
    return api_key


def get_indexers(api_key):
    """Get current indexers in Prowlarr."""
    try:
        response = requests.get(
            f"{PROWLARR_URL}/indexer",
            headers={"X-Api-Key": api_key},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting indexers: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Error getting indexers: {e}")
        return []


def add_indexer(api_key, indexer_name, api_key_value, base_url=None):
    """Add a Newznab indexer to Prowlarr."""
    if not api_key_value:
        print(f"⚠ Skipping {indexer_name} (no API key provided)")
        return None
    
    # Get indexer config from our list or use provided base_url
    indexer_config = INDEXERS.get(indexer_name, {})
    if not base_url:
        base_url = indexer_config.get("baseUrl", "")
    
    if not base_url:
        print(f"✗ No base URL configured for {indexer_name}")
        return None
    
    # Check if indexer already exists
    existing_indexers = get_indexers(api_key)
    existing_indexer = None
    for idx in existing_indexers:
        if idx.get("name") == indexer_name:
            existing_indexer = idx
            break
    
    # Build indexer configuration
    newznab_config = {
        "name": indexer_name,
        "enable": True,
        "appProfileId": 1,  # Required: App profile ID (default is 1)
        "priority": 25,  # Required: Priority between 1-50 (25 is middle)
        "redirect": True,  # Required: Redirect must be enabled for Usenet indexers
        "implementation": "Newznab",
        "implementationName": "Newznab",
        "configContract": "NewznabSettings",
        "fields": [
            {
                "order": 0,
                "name": "baseUrl",
                "label": "URL",
                "value": base_url,
                "type": "textbox"
            },
            {
                "order": 1,
                "name": "apiPath",
                "label": "API Path",
                "value": "",
                "type": "textbox"
            },
            {
                "order": 2,
                "name": "apiKey",
                "label": "API Key",
                "value": api_key_value,
                "type": "textbox"
            },
            {
                "order": 3,
                "name": "categories",
                "label": "Categories",
                "value": MUSIC_CATEGORIES,
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
        newznab_config["id"] = existing_indexer["id"]
        url = f"{PROWLARR_URL}/indexer/{existing_indexer['id']}"
        method = requests.put
        print(f"Updating existing {indexer_name} indexer (ID: {existing_indexer['id']})...")
    else:
        # Add new indexer
        url = f"{PROWLARR_URL}/indexer"
        method = requests.post
        print(f"Adding {indexer_name} indexer...")
    
    response = method(
        url,
        headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
        json=newznab_config,
        timeout=10
    )
    
    if response.status_code in [200, 201, 202]:
        print(f"✓ {indexer_name} indexer configured successfully")
        return response.json()
    else:
        print(f"✗ Error configuring {indexer_name}: {response.status_code} - {response.text}")
        return None


def test_indexer(api_key, indexer_id):
    """Test an indexer connection."""
    try:
        response = requests.post(
            f"{PROWLARR_URL}/indexer/test/{indexer_id}",
            headers={"X-Api-Key": api_key},
            timeout=10
        )
        if response.status_code == 200:
            result = response.json() if response.text else {}
            if not result or result.get("isValid", True):
                return True
            else:
                failures = result.get('validationFailures', [])
                if failures:
                    print(f"  ⚠ Test warnings: {failures}")
                return len(failures) == 0
        return False
    except:
        return False


def get_api_keys():
    """Get API keys from command line arguments or environment."""
    api_keys = {}
    
    # Try to get from command line arguments
    # Format: --nzbgeek-key=KEY --drunken-key=KEY --nzbplanet-key=KEY
    for arg in sys.argv[1:]:
        if arg.startswith("--nzbgeek-key="):
            api_keys["NZBGeek"] = arg.split("=", 1)[1]
        elif arg.startswith("--drunken-key=") or arg.startswith("--drunken-slug-key="):
            api_keys["DrunkenSlug"] = arg.split("=", 1)[1]
        elif arg.startswith("--nzbplanet-key="):
            api_keys["NZBPlanet"] = arg.split("=", 1)[1]
    
    # If no keys from command line, try interactive (if TTY)
    if not api_keys and sys.stdin.isatty():
        print("\n" + "=" * 60)
        print("Music Indexer API Keys")
        print("=" * 60)
        print("\nEnter API keys for the indexers you want to add.")
        print("Press Enter to skip an indexer.")
        print("\nOr pass as arguments: --nzbgeek-key=KEY --drunken-key=KEY --nzbplanet-key=KEY\n")
        
        for name, config in INDEXERS.items():
            print(f"{name}: {config['description']}")
            try:
                api_key = input(f"  API Key for {name} (or press Enter to skip): ").strip()
                if api_key:
                    api_keys[name] = api_key
                print()
            except (EOFError, KeyboardInterrupt):
                print("\nSkipping interactive input...")
                break
    
    return api_keys


def main():
    print("=" * 60)
    print("Add Music Indexers to Prowlarr")
    print("=" * 60)
    
    # Get Prowlarr API key
    print("\n[1/3] Getting Prowlarr API key...")
    prowlarr_api_key = get_prowlarr_api_key()
    if not prowlarr_api_key:
        print("✗ Prowlarr API key required")
        sys.exit(1)
    print("✓ Prowlarr API key obtained")
    
    # Get indexer API keys
    print("\n[2/3] Getting indexer API keys...")
    api_keys = get_api_keys()
    
    if not api_keys:
        print("✗ No API keys provided. Exiting.")
        sys.exit(1)
    
    # Add indexers
    print("\n[3/3] Adding indexers to Prowlarr...")
    added_count = 0
    for indexer_name, api_key_value in api_keys.items():
        result = add_indexer(prowlarr_api_key, indexer_name, api_key_value)
        if result:
            added_count += 1
            # Test the indexer
            indexer_id = result.get("id")
            if indexer_id:
                print(f"  Testing {indexer_name}...")
                if test_indexer(prowlarr_api_key, indexer_id):
                    print(f"  ✓ {indexer_name} test passed")
                else:
                    print(f"  ⚠ {indexer_name} test had warnings (may still work)")
    
    print("\n" + "=" * 60)
    print("Configuration complete!")
    print("=" * 60)
    print(f"\n✓ Added {added_count} indexer(s) to Prowlarr")
    print("\nNext steps:")
    print("1. Check Prowlarr: http://192.168.86.47:9696 → Indexers")
    print("2. Indexers will automatically sync to Lidarr")
    print("3. Check Lidarr: http://192.168.86.47:8686 → Settings → Indexers")
    print("4. Test a search in Lidarr to verify indexers are working")


if __name__ == "__main__":
    main()

