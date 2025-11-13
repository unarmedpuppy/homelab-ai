"""Troubleshooting and diagnostic tools."""
from typing import Dict, Any, Optional
from mcp.server import Server
from clients.sonarr import SonarrClient
from clients.radarr import RadarrClient
from clients.remote_exec import RemoteExecutor
# Import monitoring tools (will be called directly, not imported to avoid circular dependency)


executor = RemoteExecutor()


def register_troubleshooting_tools(server: Server):
    """Register troubleshooting tools with MCP server."""
    
    @server.tool()
    async def troubleshoot_failed_downloads(
        service: str = "sonarr",
        include_logs: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive diagnostic for failed downloads in Sonarr or Radarr.
        
        Args:
            service: "sonarr" or "radarr"
            include_logs: Whether to include recent error logs
            
        Returns:
            Queue issues, client issues, path issues, recommendations
        """
        try:
            if service.lower() == "sonarr":
                from tools.media_download import sonarr_queue_status, sonarr_check_download_clients
                queue_status = await sonarr_queue_status()
                client_status = await sonarr_check_download_clients()
            elif service.lower() == "radarr":
                from tools.media_download import radarr_queue_status, radarr_check_download_clients
                queue_status = await radarr_queue_status()
                client_status = await radarr_check_download_clients()
            else:
                return {
                    "status": "error",
                    "error_type": "ValueError",
                    "message": f"Service must be 'sonarr' or 'radarr', got '{service}'"
                }
            
            # Analyze queue issues
            queue_issues = {}
            if queue_status.get("status") == "success":
                data = queue_status.get("data", {})
                stuck_count = data.get("stuck_count", 0)
                if stuck_count > 0:
                    queue_issues = {
                        "stuck_items": stuck_count,
                        "statuses": list(set([item.get("status") for item in data.get("stuck_items", [])]))
                    }
            
            # Get client issues
            client_issues = []
            if client_status.get("status") == "success":
                client_issues = client_status.get("issues", [])
            
            # Check disk space (call monitoring tool directly)
            from tools.monitoring import check_disk_space
            disk_status = await check_disk_space()
            disk_issues = []
            if disk_status.get("status") == "success":
                disk_data = disk_status.get("data", {})
                if disk_data.get("status") != "ok":
                    disk_issues.append({
                        "problem": f"Disk space {disk_data.get('status')}",
                        "usage_percent": disk_data.get("usage_percent"),
                        "recommendation": disk_data.get("recommendations", [])
                    })
            
            # Build recommendations
            recommendations = []
            
            if queue_issues.get("stuck_items", 0) > 0:
                if "downloadClientUnavailable" in queue_issues.get("statuses", []):
                    recommendations.append("Check download client configuration")
                    recommendations.append("Run diagnose_download_client_unavailable tool")
                recommendations.append(f"Remove {queue_issues['stuck_items']} stuck items from queue")
            
            if client_issues:
                recommendations.append("Review and fix download client issues")
                for issue in client_issues:
                    recommendations.append(f"Fix: {issue.get('fix', 'Unknown issue')}")
            
            if disk_issues:
                recommendations.extend(disk_issues[0].get("recommendation", []))
            
            result = {
                "status": "success",
                "service": service,
                "queue_issues": queue_issues,
                "client_issues": client_issues,
                "disk_issues": disk_issues,
                "recommendations": recommendations
            }
            
            if include_logs:
                from tools.monitoring import get_recent_errors
                logs = await get_recent_errors(service=service, lines=50)
                result["recent_errors"] = logs
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def diagnose_download_client_unavailable(service: str) -> Dict[str, Any]:
        """
        Specific diagnostic for "downloadClientUnavailable" errors.
        
        Args:
            service: "sonarr" or "radarr"
            
        Returns:
            Root cause, affected items, fix steps, and auto-fix capability
        """
        try:
            if service.lower() == "sonarr":
                from tools.media_download import sonarr_queue_status, sonarr_check_download_clients
                queue_status = await sonarr_queue_status()
                client_status = await sonarr_check_download_clients()
            elif service.lower() == "radarr":
                from tools.media_download import radarr_queue_status, radarr_check_download_clients
                queue_status = await radarr_queue_status()
                client_status = await radarr_check_download_clients()
            else:
                return {
                    "status": "error",
                    "error_type": "ValueError",
                    "message": f"Service must be 'sonarr' or 'radarr', got '{service}'"
                }
            
            # Find stuck items
            stuck_items = []
            affected_count = 0
            
            if queue_status.get("status") == "success":
                data = queue_status.get("data", {})
                stuck_items = [item for item in data.get("stuck_items", []) 
                             if item.get("status") == "downloadClientUnavailable"]
                affected_count = len(stuck_items)
            
            # Analyze root cause
            root_cause = "Unknown"
            fix_steps = []
            can_auto_fix = False
            
            if client_status.get("status") == "success":
                clients = client_status.get("clients", [])
                issues = client_status.get("issues", [])
                
                # Check if qBittorrent is missing
                qbt_found = any(c.get("name", "").lower() == "qbittorrent" for c in clients)
                nzbget_found = any(c.get("name", "").lower() == "nzbget" for c in clients)
                
                # Check if clients are disabled
                disabled_clients = [c for c in clients if not c.get("enabled")]
                
                if disabled_clients:
                    root_cause = f"Download clients disabled: {', '.join([c['name'] for c in disabled_clients])}"
                    fix_steps = [
                        f"Enable {c['name']} in {service} settings" for c in disabled_clients
                    ]
                    can_auto_fix = False  # Requires UI or API update
                elif not qbt_found and any(item.get("protocol") == "torrent" for item in stuck_items):
                    root_cause = "qBittorrent not configured for torrent downloads"
                    fix_steps = [
                        "Add qBittorrent download client in Sonarr/Radarr",
                        "Configure: host=media-download-gluetun, port=8080, username=admin, password=adminadmin"
                    ]
                    can_auto_fix = False  # Could be automated but requires API implementation
                elif not nzbget_found and any(item.get("protocol") == "usenet" for item in stuck_items):
                    root_cause = "NZBGet not configured for Usenet downloads"
                    fix_steps = [
                        "Add NZBGet download client in Sonarr/Radarr",
                        "Configure: host=media-download-gluetun, port=6789, username=nzbget, password=nzbget"
                    ]
                    can_auto_fix = False
                else:
                    root_cause = "Download client connection issue (clients configured but unavailable)"
                    fix_steps = [
                        "Check if download clients are running",
                        "Verify network connectivity",
                        "Check authentication credentials",
                        "Review download client logs"
                    ]
                    can_auto_fix = False
            
            return {
                "status": "success",
                "service": service,
                "root_cause": root_cause,
                "affected_items": affected_count,
                "stuck_items_sample": stuck_items[:5],  # First 5 as sample
                "fix_steps": fix_steps,
                "can_auto_fix": can_auto_fix
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def check_service_dependencies(service_name: str) -> Dict[str, Any]:
        """
        Check if service dependencies are running.
        
        Args:
            service_name: Name of the service to check dependencies for
            
        Returns:
            Dependency status and missing services
        """
        try:
            # Get docker-compose file for the service
            # Try to find the app directory
            find_cmd = f"docker inspect {service_name} --format '{{{{.Config.Labels}}}}' 2>/dev/null | grep -o 'com.docker.compose.project.working_dir:[^ ]*' || echo ''"
            stdout, _, _ = await executor.execute(find_cmd)
            
            # Check if container is running
            check_cmd = f"docker ps --filter name={service_name} --format '{{{{.Names}}}}'"
            stdout2, _, returncode = await executor.execute(check_cmd)
            
            if returncode != 0 or not stdout2.strip():
                return {
                    "status": "error",
                    "error_type": "NotFoundError",
                    "message": f"Service {service_name} not found"
                }
            
            # Common dependency patterns
            dependencies = []
            missing = []
            
            # Check for common dependencies based on service name patterns
            if "sonarr" in service_name.lower() or "radarr" in service_name.lower():
                # Check for download clients
                nzbget_check = await executor.execute("docker ps --filter name=nzbget --format '{{.Names}}'")
                qbt_check = await executor.execute("docker ps --filter name=qbittorrent --format '{{.Names}}'")
                
                if nzbget_check[0].strip():
                    dependencies.append({"name": "nzbget", "status": "running"})
                else:
                    missing.append("nzbget")
                    dependencies.append({"name": "nzbget", "status": "stopped"})
                
                if qbt_check[0].strip():
                    dependencies.append({"name": "qbittorrent", "status": "running"})
                else:
                    dependencies.append({"name": "qbittorrent", "status": "stopped"})
            
            return {
                "status": "success",
                "service": service_name,
                "dependencies": dependencies,
                "missing_dependencies": missing,
                "all_dependencies_running": len(missing) == 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
