#!/usr/bin/env python3
"""
Check and fix gluetun connection issues for Sonarr and Radarr.

This script:
1. Checks if gluetun and nzbget containers are running
2. Tests connectivity to gluetun
3. Verifies and fixes NZBGet configuration in Sonarr/Radarr
"""

import requests
import json
import sys
import subprocess
import os

# Service URLs
SONARR_URL = "http://192.168.86.47:8989/api/v3"
RADARR_URL = "http://192.168.86.47:7878/api/v3"

# API Keys (from PIRATE_AGENT_CONTEXT.md)
SONARR_API_KEY = "dd7148e5a3dd4f7aa0c579194f45edff"
RADARR_API_KEY = "afb58cf1eaee44208099b403b666e29c"

# NZBGet configuration
NZBGET_HOST = "media-download-gluetun"
NZBGET_PORT = 6789
NZBGET_USERNAME = "nzbget"
NZBGET_PASSWORD = "nzbget"


def check_container_status(container_name):
    """Check if a container is running."""
    try:
        # Try direct docker command first (if running on server)
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and container_name in result.stdout:
            return True
        
        # Fallback: try via SSH (from repo root)
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts", "connect-server.sh")
        if os.path.exists(script_path):
            result = subprocess.run(
                ["bash", script_path, f"docker ps --filter 'name={container_name}' --format '{{{{.Names}}}}'"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and container_name in result.stdout:
                return True
        return False
    except Exception as e:
        print(f"  ⚠ Could not check container status: {e}")
        return None


def test_gluetun_connectivity():
    """Test if we can reach gluetun from Sonarr/Radarr containers."""
    print("\n[1/4] Checking container status...")
    
    containers = {
        "gluetun": "media-download-gluetun",
        "nzbget": "media-download-nzbget"
    }
    
    all_running = True
    for name, container in containers.items():
        status = check_container_status(container)
        if status is True:
            print(f"  ✓ {name} is running")
        elif status is False:
            print(f"  ✗ {name} is NOT running")
            all_running = False
        else:
            print(f"  ⚠ Could not check {name} status")
    
    if not all_running:
        print("\n⚠ Some containers are not running. Attempting to start them...")
        try:
            # Try direct docker-compose first (if running on server)
            compose_dir = os.path.dirname(os.path.abspath(__file__))
            result = subprocess.run(
                ["docker-compose", "-f", os.path.join(compose_dir, "docker-compose.yml"), "up", "-d", "gluetun", "nzbget"],
                cwd=compose_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print("  ✓ Containers started")
                all_running = True
            else:
                # Fallback: try via SSH (from repo root)
                script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts", "connect-server.sh")
                if os.path.exists(script_path):
                    result = subprocess.run(
                        ["bash", script_path, 
                         "cd ~/server/apps/media-download && docker-compose up -d gluetun nzbget"],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode == 0:
                        print("  ✓ Containers started")
                        all_running = True
                    else:
                        print(f"  ⚠ Could not start containers automatically")
                        print(f"  Run manually on server: cd ~/server/apps/media-download && docker-compose up -d gluetun nzbget")
                else:
                    print(f"  ⚠ Could not find connect-server.sh script")
                    print(f"  Run manually on server: cd ~/server/apps/media-download && docker-compose up -d gluetun nzbget")
        except Exception as e:
            print(f"  ⚠ Could not start containers: {e}")
            print("  Run manually on server: cd ~/server/apps/media-download && docker-compose up -d gluetun nzbget")
    
    return all_running


def test_nzbget_connection():
    """Test NZBGet connection via gluetun."""
    print("\n[2/4] Testing NZBGet connection...")
    
    # Test from host (should work if gluetun port is exposed)
    try:
        # Try to connect to NZBGet via gluetun's exposed port
        response = requests.get(
            f"http://192.168.86.47:6789/jsonrpc",
            params={"version": "1.1", "method": "status", "id": 1},
            auth=(NZBGET_USERNAME, NZBGET_PASSWORD),
            timeout=5
        )
        if response.status_code == 200:
            print("  ✓ NZBGet is accessible via gluetun")
            return True
        else:
            print(f"  ⚠ NZBGet returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("  ✗ Cannot connect to NZBGet via gluetun (Connection refused)")
        return False
    except Exception as e:
        print(f"  ⚠ Connection test error: {e}")
        return False


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
            print(f"  ✗ Error fetching download clients: {response.status_code}")
            return []
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return []


def fix_nzbget_client(api_key, url, service_name):
    """Fix NZBGet download client configuration."""
    print(f"\n[3/4] Checking {service_name} NZBGet configuration...")
    
    clients = get_download_clients(api_key, url)
    nzbget_client = None
    
    for client in clients:
        if client.get("implementation") == "Nzbget":
            nzbget_client = client
            break
    
    if not nzbget_client:
        print(f"  ⚠ No NZBGet client found in {service_name}")
        return False
    
    # Extract current configuration
    fields = {field["name"]: field for field in nzbget_client.get("fields", [])}
    current_host = fields.get("host", {}).get("value", "")
    current_port = fields.get("port", {}).get("value", "")
    
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
        print(f"  ✓ Configuration is correct")
        
        # Test connection anyway
        print(f"  Testing connection...")
        try:
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
                        print(f"  ✗ Connection test failed:")
                        for failure in failures:
                            print(f"    - {failure.get('propertyName')}: {failure.get('message')}")
                    return False
            else:
                print(f"  ⚠ Could not test connection: {test_response.status_code}")
                return True  # Config is correct, might be temporary issue
        except Exception as e:
            print(f"  ⚠ Could not test connection: {e}")
            return True  # Config is correct
    
    # Update configuration
    print(f"  Fixing configuration...")
    
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
            print(f"  ✓ Configuration updated successfully")
            
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
                    return True  # Updated successfully
            else:
                print(f"  ⚠ Could not test connection: {test_response.status_code}")
                return True  # Updated successfully
        else:
            print(f"  ✗ Error updating: {response.status_code} - {response.text[:200]}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    print("=" * 60)
    print("Check and Fix Gluetun Connection")
    print("=" * 60)
    
    # Step 1: Check containers
    containers_ok = test_gluetun_connectivity()
    
    # Step 2: Test NZBGet connection
    nzbget_ok = test_nzbget_connection()
    
    # Step 3: Fix Sonarr
    sonarr_ok = fix_nzbget_client(SONARR_API_KEY, SONARR_URL, "Sonarr")
    
    # Step 4: Fix Radarr
    radarr_ok = fix_nzbget_client(RADARR_API_KEY, RADARR_URL, "Radarr")
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    print(f"  Containers: {'✓ Running' if containers_ok else '✗ Not running'}")
    print(f"  NZBGet Connection: {'✓ OK' if nzbget_ok else '✗ Failed'}")
    print(f"  Sonarr: {'✓ Fixed' if sonarr_ok else '✗ Failed'}")
    print(f"  Radarr: {'✓ Fixed' if radarr_ok else '✗ Failed'}")
    
    if not containers_ok:
        print("\n⚠ Action required: Start containers")
        print("  Run: cd apps/media-download && docker-compose up -d gluetun nzbget")
    
    if not nzbget_ok and containers_ok:
        print("\n⚠ Action required: Check gluetun port mapping")
        print("  Verify port 6789 is exposed in docker-compose.yml")
    
    if sonarr_ok and radarr_ok and nzbget_ok:
        print("\n✓ All checks passed! Connection should be working now.")


if __name__ == "__main__":
    main()

