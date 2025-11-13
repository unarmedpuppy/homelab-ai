"""Networking and infrastructure tools."""
import json
from typing import Dict, Any, Optional
from mcp.server import Server
from clients.remote_exec import RemoteExecutor


executor = RemoteExecutor()


def register_networking_tools(server: Server):
    """Register networking and infrastructure tools with MCP server."""
    
    @server.tool()
    async def check_port_status(port: int, host: str = "localhost") -> Dict[str, Any]:
        """
        Check if a port is listening.
        
        Args:
            port: Port number to check
            host: Host to check (default: localhost)
            
        Returns:
            Port status and process using port
        """
        try:
            # Try netstat first, fallback to ss
            command = f"netstat -tuln 2>/dev/null | grep ':{port} ' || ss -tuln 2>/dev/null | grep ':{port} '"
            stdout, stderr, returncode = await executor.execute(command)
            
            if returncode != 0 or not stdout:
                return {
                    "status": "success",
                    "port": port,
                    "host": host,
                    "in_use": False,
                    "message": f"Port {port} is not in use on {host}"
                }
            
            # Find which container/process is using it
            from tools.monitoring import find_service_by_port
            service_info = await find_service_by_port(port)
            
            return {
                "status": "success",
                "port": port,
                "host": host,
                "in_use": True,
                "containers": service_info.get("containers", []),
                "netstat_output": stdout.strip() if stdout else ""
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def vpn_status() -> Dict[str, Any]:
        """
        Check VPN services status (Gluetun, Tailscale).
        
        Returns:
            Connection status and active connections
        """
        try:
            from tools.docker import docker_container_status
            
            vpn_statuses = {}
            
            # Check Gluetun
            gluetun_status = await docker_container_status("media-download-gluetun")
            if gluetun_status.get("status") == "success":
                vpn_statuses["gluetun"] = {
                    "running": gluetun_status.get("running", False),
                    "health": gluetun_status.get("health", "unknown"),
                    "state": gluetun_status.get("state", "unknown")
                }
            
            # Check Tailscale
            tailscale_status = await docker_container_status("tailscale")
            if tailscale_status.get("status") == "success":
                vpn_statuses["tailscale"] = {
                    "running": tailscale_status.get("running", False),
                    "health": tailscale_status.get("health", "unknown"),
                    "state": tailscale_status.get("state", "unknown")
                }
            
            return {
                "status": "success",
                "vpn_services": vpn_statuses
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }
    
    @server.tool()
    async def check_dns_status() -> Dict[str, Any]:
        """
        Check DNS service status (AdGuard).
        
        Returns:
            DNS status and query stats
        """
        try:
            from tools.docker import docker_container_status
            
            # Check AdGuard container
            adguard_status = await docker_container_status("adguard-home")
            
            if adguard_status.get("status") != "success":
                return {
                    "status": "error",
                    "message": "AdGuard Home container not found"
                }
            
            # Try to get stats from AdGuard API (if accessible)
            # This would require AdGuard API credentials
            
            return {
                "status": "success",
                "service": "adguard-home",
                "running": adguard_status.get("running", False),
                "health": adguard_status.get("health", "unknown"),
                "note": "Query stats require AdGuard API access"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }

