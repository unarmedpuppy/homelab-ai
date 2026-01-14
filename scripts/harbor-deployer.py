#!/usr/bin/env python3
"""
Harbor Auto-Deployer - Polls Harbor registry and auto-deploys updated containers.

Replaces Watchtower with a simple, maintainable solution.

Usage:
    python3 harbor-deployer.py                    # Run as daemon (default)
    python3 harbor-deployer.py --dry-run --once   # Check once without deploying
    python3 harbor-deployer.py --debug            # Enable debug logging
    python3 harbor-deployer.py --container pokedex  # Check specific container
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import docker
import requests

# =============================================================================
# Configuration
# =============================================================================

DEFAULT_CONFIG = {
    "poll_interval": 60,
    "harbor_url": "https://harbor.server.unarmedpuppy.com",
    "mattermost_webhook": "",
    "label": "com.centurylinklabs.watchtower.enable",
    "log_file": "/home/unarmedpuppy/server/logs/harbor-deployer.log",
    "compose_base_path": "/home/unarmedpuppy/server/apps",
    "container_to_app": {
        "llm-router": "homelab-ai",
        "llm-manager": "homelab-ai",
        "homelab-ai-dashboard": "homelab-ai",
        "claude-harness": "homelab-ai",
        "agent-core": "agent-gateway",
        "agent-gateway": "agent-gateway",
        "polymarket-bot": "polyjuiced",
    },
}

# =============================================================================
# Logging Setup
# =============================================================================


def setup_logging(log_file: str, debug: bool = False) -> logging.Logger:
    """Configure logging to both file and console."""
    logger = logging.getLogger("harbor-deployer")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Console handler with colors
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG if debug else logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s %(levelname)-5s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console.setFormatter(console_format)
    logger.addHandler(console)

    # File handler
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s %(levelname)-5s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    return logger


# =============================================================================
# Harbor Deployer Class
# =============================================================================


class HarborDeployer:
    """Polls Harbor registry and auto-deploys updated containers."""

    def __init__(self, config: Dict, dry_run: bool = False, logger: logging.Logger = None):
        self.config = config
        self.dry_run = dry_run
        self.logger = logger or logging.getLogger("harbor-deployer")
        self.docker_client = docker.from_env()
        self.session = requests.Session()
        self.session.headers.update(
            {"Accept": "application/vnd.docker.distribution.manifest.v2+json"}
        )

    def get_watched_containers(self, container_filter: str = None) -> List[docker.models.containers.Container]:
        """Get all containers with the watchtower enable label."""
        label = self.config["label"]
        containers = self.docker_client.containers.list(
            filters={"label": f"{label}=true"}
        )

        if container_filter:
            containers = [c for c in containers if c.name == container_filter]

        return containers

    def get_image_parts(self, image_name: str) -> tuple:
        """Parse image name into registry, repository, and tag."""
        # Format: harbor.server.unarmedpuppy.com/library/pokedex:latest
        if ":" in image_name:
            image, tag = image_name.rsplit(":", 1)
        else:
            image, tag = image_name, "latest"

        # Extract registry and repository
        parts = image.split("/")
        if len(parts) >= 3:
            registry = parts[0]
            repository = "/".join(parts[1:])
        else:
            registry = self.config["harbor_url"].replace("https://", "").replace("http://", "")
            repository = image

        return registry, repository, tag

    def get_remote_digest(self, image_name: str) -> Optional[str]:
        """Query Harbor API to get the remote image digest."""
        _, repository, tag = self.get_image_parts(image_name)

        # Harbor API endpoint for manifest
        url = f"{self.config['harbor_url']}/v2/{repository}/manifests/{tag}"

        try:
            response = self.session.head(url, timeout=10)
            if response.status_code == 200:
                return response.headers.get("Docker-Content-Digest")
            elif response.status_code == 401:
                # Try without auth for public repos
                self.logger.debug(f"Got 401 for {url}, attempting token auth")
                return self._get_digest_with_token(repository, tag)
            else:
                self.logger.error(f"Failed to get digest for {image_name}: HTTP {response.status_code}")
                return None
        except requests.RequestException as e:
            self.logger.error(f"Error fetching digest for {image_name}: {e}")
            return None

    def _get_digest_with_token(self, repository: str, tag: str) -> Optional[str]:
        """Get digest using Harbor token authentication."""
        harbor_url = self.config["harbor_url"]

        # Get token
        token_url = f"{harbor_url}/service/token?service=harbor-registry&scope=repository:{repository}:pull"
        try:
            token_response = self.session.get(token_url, timeout=10)
            if token_response.status_code != 200:
                self.logger.debug(f"Token request failed: {token_response.status_code}")
                return None

            token = token_response.json().get("token")
            if not token:
                return None

            # Get manifest with token
            manifest_url = f"{harbor_url}/v2/{repository}/manifests/{tag}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.docker.distribution.manifest.v2+json",
            }
            response = self.session.head(manifest_url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.headers.get("Docker-Content-Digest")
        except requests.RequestException as e:
            self.logger.debug(f"Token auth failed: {e}")

        return None

    def get_local_digest(self, container: docker.models.containers.Container) -> Optional[str]:
        """Get the digest of the image running in the container."""
        try:
            image = container.image
            # RepoDigests format: ['harbor.server.unarmedpuppy.com/library/pokedex@sha256:abc123']
            repo_digests = image.attrs.get("RepoDigests", [])
            if repo_digests:
                # Extract digest from first entry
                digest_part = repo_digests[0].split("@")[-1]
                return digest_part
            return None
        except Exception as e:
            self.logger.error(f"Error getting local digest for {container.name}: {e}")
            return None

    def get_compose_path(self, container_name: str) -> Path:
        """Determine the docker-compose.yml path for a container."""
        base_path = Path(self.config["compose_base_path"])

        # Check for explicit mapping
        app_name = self.config["container_to_app"].get(container_name, container_name)

        compose_path = base_path / app_name / "docker-compose.yml"
        return compose_path

    def update_container(self, container: docker.models.containers.Container) -> bool:
        """Pull new image and restart container using docker compose."""
        container_name = container.name
        image_name = container.image.tags[0] if container.image.tags else container.attrs["Config"]["Image"]
        compose_path = self.get_compose_path(container_name)

        if not compose_path.exists():
            self.logger.error(f"Compose file not found: {compose_path}")
            return False

        self.logger.info(f"Updating {container_name}...")

        if self.dry_run:
            self.logger.info(f"  [DRY-RUN] Would pull {image_name}")
            self.logger.info(f"  [DRY-RUN] Would restart via {compose_path}")
            return True

        try:
            # Pull new image
            self.logger.info(f"  Pulling {image_name}...")
            self.docker_client.images.pull(image_name)

            # Stop and remove container
            self.logger.info(f"  Stopping {container_name}...")
            container.stop(timeout=30)
            container.remove()

            # Restart via docker compose
            self.logger.info(f"  Starting via docker compose...")
            result = subprocess.run(
                ["docker", "compose", "-f", str(compose_path), "up", "-d"],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                self.logger.error(f"  Docker compose failed: {result.stderr}")
                return False

            self.logger.info(f"  Successfully updated {container_name}")
            return True

        except Exception as e:
            self.logger.error(f"  Failed to update {container_name}: {e}")
            return False

    def notify_mattermost(self, updates: List[Dict]) -> None:
        """Send notification to Mattermost."""
        webhook_url = self.config.get("mattermost_webhook")
        if not webhook_url:
            self.logger.debug("No Mattermost webhook configured, skipping notification")
            return

        if self.dry_run:
            self.logger.info("[DRY-RUN] Would send Mattermost notification")
            return

        try:
            # Build message
            if len(updates) == 1:
                text = f"**Harbor Deployer** updated `{updates[0]['container']}`"
            else:
                names = ", ".join(f"`{u['container']}`" for u in updates)
                text = f"**Harbor Deployer** updated {len(updates)} containers: {names}"

            # Build attachments
            attachments = []
            for update in updates:
                attachment = {
                    "color": "#36a64f" if update["success"] else "#ff0000",
                    "fields": [
                        {"short": True, "title": "Container", "value": update["container"]},
                        {"short": True, "title": "Image", "value": update["image"]},
                    ],
                }
                if update.get("digest"):
                    attachment["fields"].append(
                        {"short": False, "title": "New Digest", "value": f"`{update['digest'][:20]}...`"}
                    )
                if update.get("error"):
                    attachment["fields"].append(
                        {"short": False, "title": "Error", "value": update["error"]}
                    )
                attachments.append(attachment)

            payload = {"text": text, "attachments": attachments}

            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code != 200:
                self.logger.error(f"Mattermost notification failed: {response.status_code}")
            else:
                self.logger.debug("Mattermost notification sent")

        except Exception as e:
            self.logger.error(f"Failed to send Mattermost notification: {e}")

    def notify_error(self, container_name: str, error: str) -> None:
        """Send error notification to Mattermost."""
        webhook_url = self.config.get("mattermost_webhook")
        if not webhook_url or self.dry_run:
            return

        try:
            payload = {
                "text": f"**Harbor Deployer** failed to update `{container_name}`",
                "attachments": [
                    {
                        "color": "#ff0000",
                        "fields": [
                            {"short": False, "title": "Error", "value": str(error)},
                        ],
                    }
                ],
            }
            requests.post(webhook_url, json=payload, timeout=10)
        except Exception:
            pass  # Don't fail on notification errors

    def check_and_update(self, container_filter: str = None) -> Dict:
        """Check all watched containers and update if needed."""
        containers = self.get_watched_containers(container_filter)

        if not containers:
            self.logger.warning("No containers found with watchtower enable label")
            return {"checked": 0, "updated": 0, "failed": 0}

        self.logger.info(f"Checking {len(containers)} containers...")

        checked = 0
        updated = 0
        failed = 0
        updates = []

        for container in containers:
            checked += 1
            container_name = container.name

            try:
                # Get image name - prefer Config (what compose specified) over tags
                # This ensures we check :latest even if old version tags exist locally
                image_name = container.attrs["Config"].get("Image")
                if not image_name:
                    image_name = container.image.tags[0] if container.image.tags else None

                if not image_name:
                    self.logger.warning(f"  Could not determine image for {container_name}")
                    continue

                self.logger.debug(f"Checking {container_name} ({image_name})")

                # Get digests
                local_digest = self.get_local_digest(container)
                remote_digest = self.get_remote_digest(image_name)

                if not remote_digest:
                    self.logger.warning(f"  Could not get remote digest for {container_name}")
                    continue

                if not local_digest:
                    self.logger.warning(f"  Could not get local digest for {container_name}")
                    continue

                self.logger.debug(f"  Local:  {local_digest[:20]}...")
                self.logger.debug(f"  Remote: {remote_digest[:20]}...")

                # Compare digests
                if local_digest != remote_digest:
                    self.logger.info(f"  Update available for {container_name}")

                    success = self.update_container(container)
                    if success:
                        updated += 1
                        updates.append({
                            "container": container_name,
                            "image": image_name,
                            "digest": remote_digest,
                            "success": True,
                        })
                    else:
                        failed += 1
                        updates.append({
                            "container": container_name,
                            "image": image_name,
                            "success": False,
                            "error": "Update failed",
                        })
                else:
                    self.logger.debug(f"  No update needed for {container_name}")

            except Exception as e:
                self.logger.error(f"Error checking {container_name}: {e}")
                failed += 1
                self.notify_error(container_name, str(e))

        # Send notification if there were updates
        if updates:
            self.notify_mattermost(updates)

        return {"checked": checked, "updated": updated, "failed": failed}

    def run(self, once: bool = False, container_filter: str = None) -> None:
        """Main loop - poll and update containers."""
        poll_interval = self.config["poll_interval"]

        self.logger.info(f"Starting Harbor Deployer (poll_interval={poll_interval}s)")
        if self.dry_run:
            self.logger.info("Running in DRY-RUN mode - no changes will be made")

        while True:
            try:
                result = self.check_and_update(container_filter)
                self.logger.info(
                    f"Session done: checked={result['checked']}, "
                    f"updated={result['updated']}, failed={result['failed']}"
                )
            except Exception as e:
                self.logger.error(f"Session error: {e}")

            if once:
                break

            time.sleep(poll_interval)


# =============================================================================
# Main Entry Point
# =============================================================================


def load_config(config_path: str) -> Dict:
    """Load configuration from JSON file or use defaults."""
    config = DEFAULT_CONFIG.copy()

    if config_path and Path(config_path).exists():
        with open(config_path, "r") as f:
            user_config = json.load(f)
            config.update(user_config)

    # Also check for environment variable overrides
    if os.environ.get("HARBOR_URL"):
        config["harbor_url"] = os.environ["HARBOR_URL"]
    if os.environ.get("MATTERMOST_WEBHOOK"):
        config["mattermost_webhook"] = os.environ["MATTERMOST_WEBHOOK"]
    if os.environ.get("POLL_INTERVAL"):
        config["poll_interval"] = int(os.environ["POLL_INTERVAL"])

    return config


def main():
    parser = argparse.ArgumentParser(
        description="Harbor Auto-Deployer - Polls Harbor registry and auto-deploys updated containers."
    )
    parser.add_argument(
        "--config",
        default="harbor-deployer.json",
        help="Path to config file (default: harbor-deployer.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check for updates but don't deploy",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (don't loop)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--container",
        help="Only check specific container",
    )
    args = parser.parse_args()

    # Load config
    config = load_config(args.config)

    # Setup logging
    logger = setup_logging(config["log_file"], args.debug)

    # Create deployer and run
    deployer = HarborDeployer(config, dry_run=args.dry_run, logger=logger)

    try:
        deployer.run(once=args.once, container_filter=args.container)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
