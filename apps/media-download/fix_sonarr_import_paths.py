#!/usr/bin/env python3
"""
Fix Sonarr import path issues by updating remote path mappings.
The issue is that NZBGet downloads to /downloads/ but Sonarr expects /downloads/completed/tv/
"""

import requests
import json
import sys

SONARR_URL = "http://192.168.86.47:8989/api/v3"
SONARR_API_KEY = "dd7148e5a3dd4f7aa0c579194f45edff"


def get_remote_path_mappings():
    """Get current remote path mappings."""
    response = requests.get(
        f"{SONARR_URL}/remotePathMapping",
        headers={"X-Api-Key": SONARR_API_KEY},
        timeout=10
    )
    if response.status_code == 200:
        return response.json()
    return []


def update_remote_path_mapping(mapping_id, host, remote_path, local_path):
    """Update a remote path mapping."""
    mapping = {
        "id": mapping_id,
        "host": host,
        "remotePath": remote_path,
        "localPath": local_path
    }
    
    response = requests.put(
        f"{SONARR_URL}/remotePathMapping/{mapping_id}",
        headers={"X-Api-Key": SONARR_API_KEY, "Content-Type": "application/json"},
        json=mapping,
        timeout=10
    )
    return response.status_code == 200


def main():
    print("=" * 60)
    print("Fix Sonarr Import Path Issues")
    print("=" * 60)
    
    mappings = get_remote_path_mappings()
    
    if not mappings:
        print("\nNo remote path mappings found. Creating one...")
        # Create new mapping
        mapping = {
            "host": "media-download-gluetun",
            "remotePath": "/downloads/",
            "localPath": "/downloads/"
        }
        response = requests.post(
            f"{SONARR_URL}/remotePathMapping",
            headers={"X-Api-Key": SONARR_API_KEY, "Content-Type": "application/json"},
            json=mapping,
            timeout=10
        )
        if response.status_code == 201:
            print("✓ Created remote path mapping")
        else:
            print(f"✗ Failed to create mapping: {response.status_code}")
            print(response.text)
    else:
        print(f"\nFound {len(mappings)} remote path mapping(s):")
        for mapping in mappings:
            print(f"  ID: {mapping.get('id')}")
            print(f"  Host: {mapping.get('host')}")
            print(f"  Remote: {mapping.get('remotePath')}")
            print(f"  Local: {mapping.get('localPath')}")
            print()
        
        # The mapping looks correct, but the issue might be that NZBGet
        # is downloading to /downloads/ instead of /downloads/completed/tv/
        print("The remote path mapping looks correct.")
        print("\nThe issue is likely that:")
        print("1. NZBGet is downloading to /downloads/ (main dir)")
        print("2. But should download to /downloads/completed/tv/ (category dir)")
        print("\nThis happens when the category isn't set correctly in NZBGet.")
        print("Check that Sonarr is sending downloads with category 'tv'.")


if __name__ == "__main__":
    main()

