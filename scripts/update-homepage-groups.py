#!/usr/bin/env python3
"""
Update homepage.group labels in all docker-compose.yml files to logical categories
"""

import os
import re
import yaml
from pathlib import Path

# Define logical categories and their apps
CATEGORIES = {
    "Infrastructure & Services": [
        "adguard-home",
        "cloudflare-ddns",
        "grafana",
        "traefik",
        "tailscale",
        "homepage"
    ],
    "Media & Entertainment": [
        "jellyfin",
        "plex",
        "tunarr",
        "immich",
        "metube",
        "spotifydl"
    ],
    "Media Management": [
        "media-download",
        "paperless-ngx"
    ],
    "Gaming": [
        "minecraft",
        "rust",
        "bedrock-viz",
        "maptapdat"
    ],
    "Productivity & Organization": [
        "planka",
        "monica",
        "maybe",
        "open-archiver",
        "mealie",
        "grist"
    ],
    "Finance & Trading": [
        "trading-bot",
        "trading-journal",
        "tradingagents",
        "tradenote",
        "maybe"
    ],
    "AI & Machine Learning": [
        "local-ai-app",
        "ollama-docker",
        "open-health"
    ],
    "Automation & Workflows": [
        "n8n",
        "homeassistant"
    ],
    "Communication & Social": [
        "campfire",
        "libreddit",
        "freshRSS",
        "ghost"
    ],
    "Security & Privacy": [
        "vaultwarden"
    ]
}

def update_compose_file(file_path, app_name, new_group):
    """Update homepage.group in a docker-compose.yml file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if file has homepage labels (might need to add)
        has_homepage_labels = 'homepage.' in content
        if not has_homepage_labels:
            print(f"  ⚠️  {app_name}: No homepage labels found, skipping")
            return False
        
        # Replace or add homepage.group line
        pattern = r'(\s*-\s*"homepage\.group=)[^"]*(")'
        
        if re.search(pattern, content):
            # Replace existing homepage.group
            replacement = f'\\1{new_group}\\2'
            new_content = re.sub(pattern, replacement, content)
        else:
            # Add homepage.group before other homepage labels
            homepage_pattern = r'(\s*-\s*"homepage\.(name|icon|href|description)=)'
            if re.search(homepage_pattern, content):
                # Insert before first homepage label
                new_content = re.sub(
                    homepage_pattern,
                    f'      - "homepage.group={new_group}"\\n      \\1',
                    content,
                    count=1
                )
            else:
                # Add to labels section
                labels_pattern = r'(\s*labels:\s*\n)'
                if re.search(labels_pattern, content):
                    new_content = re.sub(
                        labels_pattern,
                        f'\\1      - "homepage.group={new_group}"\\n',
                        content,
                        count=1
                    )
                else:
                    print(f"  ⚠️  {app_name}: Could not find labels section")
                    return False
        
        if new_content != content:
            with open(file_path, 'w') as f:
                f.write(new_content)
            print(f"  ✅ {app_name}: Updated to '{new_group}'")
            return True
        else:
            print(f"  ℹ️  {app_name}: Already set to '{new_group}'")
            return False
    except Exception as e:
        print(f"  ❌ {app_name}: Error - {e}")
        return False

def main():
    apps_dir = Path(__file__).parent.parent / "apps"
    
    if not apps_dir.exists():
        print(f"❌ Apps directory not found: {apps_dir}")
        return
    
    print("Updating homepage.group labels...")
    print("=" * 60)
    
    # Create reverse mapping: app_name -> category
    app_to_category = {}
    for category, apps in CATEGORIES.items():
        for app in apps:
            app_to_category[app] = category
    
    updated_count = 0
    skipped_count = 0
    
    # Process each app directory
    for app_dir in sorted(apps_dir.iterdir()):
        if not app_dir.is_dir():
            continue
        
        app_name = app_dir.name
        compose_file = app_dir / "docker-compose.yml"
        
        if not compose_file.exists():
            continue
        
        if app_name in app_to_category:
            new_group = app_to_category[app_name]
            if update_compose_file(compose_file, app_name, new_group):
                updated_count += 1
        else:
            print(f"  ⚠️  {app_name}: Not in category mapping, skipping")
            skipped_count += 1
    
    print("=" * 60)
    print(f"✅ Updated: {updated_count} apps")
    if skipped_count > 0:
        print(f"⚠️  Skipped: {skipped_count} apps (not in category mapping)")
    print("\nCategories:")
    for category, apps in CATEGORIES.items():
        print(f"  • {category}: {len(apps)} apps")

if __name__ == '__main__':
    main()

