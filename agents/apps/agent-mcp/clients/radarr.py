"""Radarr API client."""
import json
from typing import Dict, Any, List, Optional
from clients.remote_exec import RemoteExecutor


class RadarrClient:
    """Client for Radarr API operations."""
    
    def __init__(self):
        from config.settings import settings
        self.api_key = settings.get("radarr", "api_key")
        self.base_url = settings.get("radarr", "base_url")
        self.container = settings.get("radarr", "container")
        self.executor = RemoteExecutor()
    
    async def _api_call(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make API call to Radarr."""
        url = f"{self.base_url}{endpoint}?apikey={self.api_key}"
        
        if method == "GET":
            command = f"docker exec {self.container} curl -s '{url}'"
        elif method == "DELETE":
            command = f"docker exec {self.container} curl -s -X DELETE '{url}'"
        elif method == "POST":
            json_data = json.dumps(data) if data else "{}"
            command = f"docker exec {self.container} curl -s -X POST '{url}' -H 'Content-Type: application/json' -d '{json_data}'"
        elif method == "PUT":
            json_data = json.dumps(data) if data else "{}"
            command = f"docker exec {self.container} curl -s -X PUT '{url}' -H 'Content-Type: application/json' -d '{json_data}'"
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        stdout, stderr, returncode = await self.executor.execute(command)
        
        if returncode != 0:
            raise Exception(f"API call failed: {stderr}")
        
        if not stdout.strip():
            return {}
        
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            raise Exception(f"Invalid JSON response: {stdout}")
    
    async def get_queue(self, page_size: int = 200) -> Dict:
        """Get queue items."""
        return await self._api_call("GET", f"/api/v3/queue?pageSize={page_size}")
    
    async def remove_queue_item(self, item_id: int, remove_from_client: bool = True, blocklist: bool = False) -> Dict:
        """Remove item from queue."""
        params = f"removeFromClient={str(remove_from_client).lower()}&blocklist={str(blocklist).lower()}"
        return await self._api_call("DELETE", f"/api/v3/queue/{item_id}?{params}")
    
    async def get_download_clients(self) -> List[Dict]:
        """Get configured download clients."""
        return await self._api_call("GET", "/api/v3/downloadclient")
    
    async def get_root_folders(self) -> List[Dict]:
        """Get root folders."""
        return await self._api_call("GET", "/api/v3/rootfolder")
    
    async def add_root_folder(self, path: str) -> Dict:
        """Add a root folder."""
        return await self._api_call("POST", "/api/v3/rootfolder", data={"path": path})
    
    async def trigger_command(self, command_name: str, **kwargs) -> Dict:
        """Trigger a Radarr command."""
        data = {"name": command_name, **kwargs}
        return await self._api_call("POST", "/api/v3/command", data=data)
    
    async def get_system_status(self) -> Dict:
        """Get system status."""
        return await self._api_call("GET", "/api/v3/system/status")
