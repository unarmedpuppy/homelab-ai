#!/usr/bin/env python3
"""
Quick verification script to check if Sonarr and Radarr can connect to NZBGet.
"""

import requests
import json

SONARR_URL = "http://192.168.86.47:8989/api/v3"
RADARR_URL = "http://192.168.86.47:7878/api/v3"
SONARR_API_KEY = "dd7148e5a3dd4f7aa0c579194f45edff"
RADARR_API_KEY = "afb58cf1eaee44208099b403b666e29c"

def check_download_client(api_key, url, service_name):
    """Check download client status."""
    try:
        response = requests.get(
            f"{url}/downloadClient",
            headers={"X-Api-Key": api_key},
            timeout=10
        )
        if response.status_code == 200:
            clients = response.json()
            nzbget = [c for c in clients if c.get("implementation") == "Nzbget"]
            if nzbget:
                client = nzbget[0]
                enabled = client.get("enable", False)
                fields = {f["name"]: f.get("value", "") for f in client.get("fields", [])}
                host = fields.get("host", "unknown")
                port = fields.get("port", "unknown")
                
                print(f"\n{service_name} NZBGet Configuration:")
                print(f"  Enabled: {enabled}")
                print(f"  Host: {host}")
                print(f"  Port: {port}")
                
                # Test connection
                try:
                    test_response = requests.post(
                        f"{url}/downloadClient/test",
                        headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
                        json=client,
                        timeout=10
                    )
                    if test_response.status_code == 200:
                        result = test_response.json()
                        if result.get("isValid"):
                            print(f"  Status: ✓ Connected")
                            return True
                        else:
                            failures = result.get("validationFailures", [])
                            if failures:
                                print(f"  Status: ✗ Connection failed")
                                for failure in failures:
                                    print(f"    - {failure.get('propertyName')}: {failure.get('message')}")
                            return False
                except Exception as e:
                    print(f"  Status: ⚠ Could not test: {e}")
                    return None
            else:
                print(f"\n{service_name}: No NZBGet client configured")
                return False
        else:
            print(f"\n{service_name}: Error {response.status_code}")
            return False
    except Exception as e:
        print(f"\n{service_name}: Error - {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Download Client Connection Verification")
    print("=" * 60)
    
    sonarr_ok = check_download_client(SONARR_API_KEY, SONARR_URL, "Sonarr")
    radarr_ok = check_download_client(RADARR_API_KEY, RADARR_URL, "Radarr")
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    print(f"  Sonarr: {'✓ Connected' if sonarr_ok else '✗ Not connected'}")
    print(f"  Radarr: {'✓ Connected' if radarr_ok else '✗ Not connected'}")
    
    if sonarr_ok and radarr_ok:
        print("\n✓ All connections working!")
    else:
        print("\n⚠ Some connections need attention")
        print("  Check container status: docker ps | grep -E '(gluetun|nzbget)'")
        print("  Check logs: docker logs media-download-nzbget")

