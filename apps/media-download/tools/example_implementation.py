"""
Example implementation of agent tools for media download stack.

This is a reference implementation showing how tools would be structured.
Not production-ready - for demonstration purposes only.
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any


class Config:
    """Load configuration from context document or environment."""
    
    DEFAULTS = {
        "sonarr": {
            "api_key": "dd7148e5a3dd4f7aa0c579194f45edff",
            "base_url": "http://127.0.0.1:8989",
            "container": "media-download-sonarr"
        },
        "radarr": {
            "api_key": "afb58cf1eaee44208099b403b666e29c",
            "base_url": "http://127.0.0.1:7878",
            "container": "media-download-radarr"
        },
        "server": {
            "connect_script": "scripts/connect-server.sh"
        }
    }
    
    @classmethod
    def get(cls, service: str, key: str) -> str:
        """Get configuration value."""
        import os
        env_key = f"{service.upper()}_{key.upper()}"
        return os.environ.get(env_key, cls.DEFAULTS[service][key])


class RemoteExecutor:
    """Execute commands on remote server."""
    
    def __init__(self):
        self.connect_script = Config.get("server", "connect_script")
    
    def execute(self, command: str) -> tuple[str, str, int]:
        """
        Execute command on remote server.
        
        Returns:
            (stdout, stderr, returncode)
        """
        try:
            result = subprocess.run(
                [self.connect_script, command],
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Command timed out", 1
        except Exception as e:
            return "", str(e), 1


class SonarrClient:
    """Client for Sonarr API operations."""
    
    def __init__(self):
        self.api_key = Config.get("sonarr", "api_key")
        self.base_url = Config.get("sonarr", "base_url")
        self.container = Config.get("sonarr", "container")
        self.executor = RemoteExecutor()
    
    def _api_call(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make API call to Sonarr."""
        url = f"{self.base_url}{endpoint}?apikey={self.api_key}"
        
        if method == "GET":
            command = f"docker exec {self.container} curl -s '{url}'"
        elif method == "DELETE":
            command = f"docker exec {self.container} curl -s -X DELETE '{url}'"
        elif method == "POST":
            json_data = json.dumps(data) if data else "{}"
            command = f"docker exec {self.container} curl -s -X POST '{url}' -H 'Content-Type: application/json' -d '{json_data}'"
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        stdout, stderr, returncode = self.executor.execute(command)
        
        if returncode != 0:
            raise Exception(f"API call failed: {stderr}")
        
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            raise Exception(f"Invalid JSON response: {stdout}")
    
    def get_queue(self, page_size: int = 200) -> Dict:
        """Get queue items."""
        return self._api_call("GET", f"/api/v3/queue?pageSize={page_size}")
    
    def remove_queue_item(self, item_id: int, remove_from_client: bool = True, blocklist: bool = False) -> Dict:
        """Remove item from queue."""
        params = f"removeFromClient={str(remove_from_client).lower()}&blocklist={str(blocklist).lower()}"
        return self._api_call("DELETE", f"/api/v3/queue/{item_id}?{params}")
    
    def get_download_clients(self) -> List[Dict]:
        """Get configured download clients."""
        return self._api_call("GET", "/api/v3/downloadclient")
    
    def get_root_folders(self) -> List[Dict]:
        """Get root folders."""
        return self._api_call("GET", "/api/v3/rootfolder")


# Tool implementations

def clear_sonarr_queue(blocklist: bool = False, remove_from_client: bool = True) -> Dict[str, Any]:
    """
    Clear all items from Sonarr's download queue.
    
    Args:
        blocklist: Whether to add removed items to blocklist
        remove_from_client: Whether to remove from download client
        
    Returns:
        Dictionary with removed_count and status
    """
    try:
        client = SonarrClient()
        queue = client.get_queue()
        
        if not queue.get("records"):
            return {
                "status": "success",
                "removed_count": 0,
                "message": "Queue is already empty"
            }
        
        removed = 0
        errors = []
        
        for item in queue["records"]:
            try:
                client.remove_queue_item(
                    item["id"],
                    remove_from_client=remove_from_client,
                    blocklist=blocklist
                )
                removed += 1
            except Exception as e:
                errors.append(f"Failed to remove item {item['id']}: {str(e)}")
        
        result = {
            "status": "success",
            "removed_count": removed,
            "total_items": len(queue["records"]),
            "message": f"Removed {removed} of {len(queue['records'])} items"
        }
        
        if errors:
            result["errors"] = errors
            result["status"] = "partial_success"
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "message": str(e),
            "details": {
                "service": "sonarr",
                "operation": "clear_queue"
            }
        }


def get_sonarr_queue_status() -> Dict[str, Any]:
    """
    Get summary of Sonarr queue status.
    
    Returns:
        Dictionary with total_items, by_status, by_protocol, stuck_items
    """
    try:
        client = SonarrClient()
        queue = client.get_queue()
        
        records = queue.get("records", [])
        
        # Count by status
        by_status = {}
        by_protocol = {}
        stuck_items = []
        
        for item in records:
            status = item.get("status", "unknown")
            protocol = item.get("protocol", "unknown")
            
            by_status[status] = by_status.get(status, 0) + 1
            by_protocol[protocol] = by_protocol.get(protocol, 0) + 1
            
            if status in ["downloadClientUnavailable", "error", "warning"]:
                stuck_items.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "status": status
                })
        
        return {
            "status": "success",
            "data": {
                "total_items": len(records),
                "by_status": by_status,
                "by_protocol": by_protocol,
                "stuck_items": stuck_items,
                "stuck_count": len(stuck_items)
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "message": str(e)
        }


def troubleshoot_failed_downloads(service: str = "sonarr", include_logs: bool = True) -> Dict[str, Any]:
    """
    Comprehensive diagnostic for failed downloads.
    
    Args:
        service: "sonarr" or "radarr"
        include_logs: Whether to include recent error logs
        
    Returns:
        Dictionary with queue_issues, client_issues, path_issues, recommendations
    """
    try:
        if service == "sonarr":
            client = SonarrClient()
        else:
            # Would use RadarrClient here
            raise ValueError(f"Service {service} not yet implemented")
        
        # Check queue status
        queue_status = get_sonarr_queue_status()
        queue_issues = {}
        
        if queue_status["status"] == "success":
            data = queue_status["data"]
            if data["stuck_count"] > 0:
                queue_issues = {
                    "stuck_items": data["stuck_count"],
                    "statuses": list(set([item["status"] for item in data["stuck_items"]]))
                }
        
        # Check download clients
        clients = client.get_download_clients()
        client_issues = []
        
        for client_config in clients:
            if not client_config.get("enable", False):
                client_issues.append({
                    "client": client_config.get("name"),
                    "problem": "Client is disabled",
                    "fix": f"Enable {client_config.get('name')} in Sonarr settings"
                })
        
        # Check root folders
        root_folders = client.get_root_folders()
        path_issues = []
        
        # Would check for missing root folders here
        # (would need to cross-reference with library items)
        
        # Build recommendations
        recommendations = []
        
        if queue_issues.get("stuck_items", 0) > 0:
            if "downloadClientUnavailable" in queue_issues.get("statuses", []):
                recommendations.append("Check download client configuration")
                recommendations.append("Run diagnose_download_client_unavailable('sonarr')")
        
        if client_issues:
            recommendations.append("Review and fix download client issues")
        
        result = {
            "status": "success",
            "data": {
                "queue_issues": queue_issues,
                "client_issues": client_issues,
                "path_issues": path_issues,
                "recommendations": recommendations
            }
        }
        
        if include_logs:
            # Would fetch logs here
            result["data"]["logs"] = "Log fetching not yet implemented"
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "message": str(e)
        }


# CLI interface

def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python example_implementation.py <tool_name> [args]")
        sys.exit(1)
    
    tool_name = sys.argv[1]
    
    if tool_name == "clear_sonarr_queue":
        blocklist = "--blocklist" in sys.argv
        result = clear_sonarr_queue(blocklist=blocklist)
        print(json.dumps(result, indent=2))
    
    elif tool_name == "get_sonarr_queue_status":
        result = get_sonarr_queue_status()
        print(json.dumps(result, indent=2))
    
    elif tool_name == "troubleshoot_failed_downloads":
        service = sys.argv[2] if len(sys.argv) > 2 else "sonarr"
        result = troubleshoot_failed_downloads(service)
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown tool: {tool_name}")
        sys.exit(1)


if __name__ == "__main__":
    main()

