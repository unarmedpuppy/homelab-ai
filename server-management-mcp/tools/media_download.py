"""Media download stack tools (Sonarr/Radarr/NZBGet)."""
from typing import Dict, Any, List, Optional
from mcp.server import Server
from clients.sonarr import SonarrClient
from clients.radarr import RadarrClient
from clients.remote_exec import RemoteExecutor
from tools.logging_decorator import with_automatic_logging


executor = RemoteExecutor()


def register_media_tools(server: Server):
    """Register media download tools with MCP server."""
    
    # Sonarr Tools
    
    @server.tool()
    @with_automatic_logging()
    async def sonarr_clear_queue(
        blocklist: bool = False,
        remove_from_client: bool = True
    ) -> Dict[str, Any]:
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
            queue = await client.get_queue()
            
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
                    await client.remove_queue_item(
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
                "message": str(e)
            }
    
    @server.tool()
    @with_automatic_logging()
    async def sonarr_queue_status() -> Dict[str, Any]:
        """
        Get summary of Sonarr queue status.
        
        Returns:
            Dictionary with total_items, by_status, by_protocol, stuck_items
        """
        try:
            client = SonarrClient()
            queue = await client.get_queue()
            
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
                        "status": status,
                        "protocol": protocol
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
    
    @server.tool()
    @with_automatic_logging()
    async def sonarr_trigger_import_scan(path: Optional[str] = None) -> Dict[str, Any]:
        """
        Trigger manual import scan for completed TV downloads.
        
        Args:
            path: Optional specific path to scan (default: /downloads/completed/tv)
            
        Returns:
            Command ID and status
        """
        try:
            client = SonarrClient()
            scan_path = path or "/downloads/completed/tv"
            
            result = await client.trigger_command("DownloadedEpisodesScan", path=scan_path)
            
            return {
                "status": "success",
                "command_id": result.get("id"),
                "command_name": result.get("name"),
                "message": f"Import scan triggered for {scan_path}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    @with_automatic_logging()
    async def sonarr_check_download_clients() -> Dict[str, Any]:
        """
        Check Sonarr download client configuration and status.
        
        Returns:
            Clients list, connection status, and issues
        """
        try:
            client = SonarrClient()
            clients = await client.get_download_clients()
            
            client_info = []
            issues = []
            
            for client_config in clients:
                client_info.append({
                    "name": client_config.get("name"),
                    "protocol": client_config.get("protocol"),
                    "enabled": client_config.get("enable", False),
                    "host": next((f.get("value") for f in client_config.get("fields", []) if f.get("name") == "host"), "unknown"),
                    "port": next((f.get("value") for f in client_config.get("fields", []) if f.get("name") == "port"), "unknown")
                })
                
                if not client_config.get("enable", False):
                    issues.append({
                        "client": client_config.get("name"),
                        "problem": "Client is disabled",
                        "fix": f"Enable {client_config.get('name')} in Sonarr settings"
                    })
            
            return {
                "status": "success",
                "clients": client_info,
                "issues": issues,
                "total_clients": len(clients)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    # Radarr Tools
    
    @server.tool()
    @with_automatic_logging()
    async def radarr_clear_queue(
        blocklist: bool = False,
        remove_from_client: bool = True
    ) -> Dict[str, Any]:
        """
        Clear all items from Radarr's download queue.
        
        Args:
            blocklist: Whether to add removed items to blocklist
            remove_from_client: Whether to remove from download client
            
        Returns:
            Dictionary with removed_count and status
        """
        try:
            client = RadarrClient()
            queue = await client.get_queue()
            
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
                    await client.remove_queue_item(
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
                "message": str(e)
            }
    
    @server.tool()
    @with_automatic_logging()
    async def radarr_queue_status() -> Dict[str, Any]:
        """
        Get summary of Radarr queue status.
        
        Returns:
            Dictionary with total_items, by_status, by_protocol, stuck_items
        """
        try:
            client = RadarrClient()
            queue = await client.get_queue()
            
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
                        "status": status,
                        "protocol": protocol
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
    
    @server.tool()
    @with_automatic_logging()
    async def radarr_trigger_import_scan(path: Optional[str] = None) -> Dict[str, Any]:
        """
        Trigger manual import scan for completed movie downloads.
        
        Args:
            path: Optional specific path to scan (default: /downloads/completed/movies)
            
        Returns:
            Command ID and status
        """
        try:
            client = RadarrClient()
            scan_path = path or "/downloads/completed/movies"
            
            result = await client.trigger_command("DownloadedMoviesScan", path=scan_path)
            
            return {
                "status": "success",
                "command_id": result.get("id"),
                "command_name": result.get("name"),
                "message": f"Import scan triggered for {scan_path}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    @with_automatic_logging()
    async def radarr_list_root_folders() -> Dict[str, Any]:
        """
        List all Radarr root folders.
        
        Returns:
            List of root folders with paths and IDs
        """
        try:
            client = RadarrClient()
            folders = await client.get_root_folders()
            
            return {
                "status": "success",
                "folders": folders,
                "total": len(folders)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    @with_automatic_logging()
    async def radarr_add_root_folder(path: str) -> Dict[str, Any]:
        """
        Add a root folder to Radarr.
        
        Args:
            path: Path to add as root folder (e.g., "/movies/Kids/Films")
            
        Returns:
            Folder ID, accessibility status, and unmapped folders
        """
        try:
            client = RadarrClient()
            result = await client.add_root_folder(path)
            
            return {
                "status": "success",
                "folder_id": result.get("id"),
                "path": result.get("path"),
                "accessible": result.get("accessible", False),
                "unmapped_folders": result.get("unmappedFolders", []),
                "message": f"Root folder added: {path}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    @with_automatic_logging()
    async def radarr_check_download_clients() -> Dict[str, Any]:
        """
        Check Radarr download client configuration and status.
        
        Returns:
            Clients list, connection status, and issues
        """
        try:
            client = RadarrClient()
            clients = await client.get_download_clients()
            
            client_info = []
            issues = []
            
            for client_config in clients:
                client_info.append({
                    "name": client_config.get("name"),
                    "protocol": client_config.get("protocol"),
                    "enabled": client_config.get("enable", False),
                    "host": next((f.get("value") for f in client_config.get("fields", []) if f.get("name") == "host"), "unknown"),
                    "port": next((f.get("value") for f in client_config.get("fields", []) if f.get("name") == "port"), "unknown")
                })
                
                if not client_config.get("enable", False):
                    issues.append({
                        "client": client_config.get("name"),
                        "problem": "Client is disabled",
                        "fix": f"Enable {client_config.get('name')} in Radarr settings"
                    })
            
            return {
                "status": "success",
                "clients": client_info,
                "issues": issues,
                "total_clients": len(clients)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    @with_automatic_logging()
    async def remove_stuck_downloads(
        service: str,
        status_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Remove only items stuck with error/unavailable status from Sonarr or Radarr queue.
        
        Args:
            service: "sonarr" or "radarr"
            status_filter: Optional list of statuses to filter (default: ["downloadClientUnavailable"])
            
        Returns:
            Removed count and status
        """
        try:
            if service.lower() == "sonarr":
                client = SonarrClient()
            elif service.lower() == "radarr":
                client = RadarrClient()
            else:
                return {
                    "status": "error",
                    "error_type": "ValueError",
                    "message": f"Service must be 'sonarr' or 'radarr', got '{service}'"
                }
            
            queue = await client.get_queue()
            records = queue.get("records", [])
            
            if not records:
                return {
                    "status": "success",
                    "removed_count": 0,
                    "message": "Queue is empty"
                }
            
            filter_statuses = status_filter or ["downloadClientUnavailable"]
            stuck_items = [r for r in records if r.get("status") in filter_statuses]
            
            if not stuck_items:
                return {
                    "status": "success",
                    "removed_count": 0,
                    "message": f"No stuck items found with statuses: {filter_statuses}"
                }
            
            removed = 0
            errors = []
            
            for item in stuck_items:
                try:
                    await client.remove_queue_item(
                        item["id"],
                        remove_from_client=True,
                        blocklist=False
                    )
                    removed += 1
                except Exception as e:
                    errors.append(f"Failed to remove item {item['id']}: {str(e)}")
            
            result = {
                "status": "success",
                "removed_count": removed,
                "total_stuck": len(stuck_items),
                "message": f"Removed {removed} stuck items from {service}"
            }
            
            if errors:
                result["errors"] = errors
                result["status"] = "partial_success"
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
