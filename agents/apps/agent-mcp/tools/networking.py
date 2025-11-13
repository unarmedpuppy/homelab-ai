"""Networking and infrastructure tools."""
import json
import re
from typing import Dict, Any, Optional, List
from mcp.server import Server
from clients.remote_exec import RemoteExecutor
from tools.logging_decorator import with_automatic_logging


executor = RemoteExecutor()


def register_networking_tools(server: Server):
    """Register networking and infrastructure tools with MCP server."""
    
    @server.tool()
    @with_automatic_logging()
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
    @with_automatic_logging()
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
    @with_automatic_logging()
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
    
    @server.tool()
    @with_automatic_logging()
    async def get_available_port(
        preferred_range: Optional[str] = None,
        min_port: int = 3000,
        max_port: int = 3100,
        count: int = 5
    ) -> Dict[str, Any]:
        """
        Find available ports for new Docker containers by checking:
        1. Running containers (docker ps)
        2. Docker Compose files (apps/*/docker-compose.yml)
        3. System listening ports
        
        Args:
            preferred_range: Preferred port range as "min-max" (e.g., "3000-3100", "8000-8100")
            min_port: Minimum port to check (default: 3000)
            max_port: Maximum port to check (default: 3100)
            count: Number of available ports to return (default: 5)
            
        Returns:
            List of available ports with details about why they're available
        """
        try:
            # Parse preferred range if provided
            if preferred_range:
                range_match = re.match(r'(\d+)-(\d+)', preferred_range)
                if range_match:
                    min_port = int(range_match.group(1))
                    max_port = int(range_match.group(2))
            
            # Get all ports in use from running containers
            docker_cmd = "docker ps --format '{{.Ports}}' | grep -oE ':[0-9]+->' | sed 's/://g' | sed 's/->//g' | sort -u"
            docker_stdout, _, _ = await executor.execute(docker_cmd)
            docker_ports = set()
            for line in docker_stdout.strip().split('\n'):
                if line.strip():
                    try:
                        docker_ports.add(int(line.strip()))
                    except ValueError:
                        pass
            
            # Get ports from docker-compose files
            compose_cmd = "find apps -name 'docker-compose.yml' -exec grep -hE ':[0-9]+:[0-9]+' {} \\; | grep -oE ':[0-9]+:' | sed 's/://g' | sort -u"
            compose_stdout, _, _ = await executor.execute(compose_cmd)
            compose_ports = set()
            for line in compose_stdout.strip().split('\n'):
                if line.strip():
                    try:
                        # Extract host port (first number in "HOST:CONTAINER")
                        port_match = re.match(r'(\d+):', line.strip())
                        if port_match:
                            compose_ports.add(int(port_match.group(1)))
                    except (ValueError, AttributeError):
                        pass
            
            # Get system listening ports
            system_cmd = "netstat -tuln 2>/dev/null | grep LISTEN | awk '{print $4}' | grep -oE ':[0-9]+$' | sed 's/://g' | sort -u || ss -tuln 2>/dev/null | grep LISTEN | awk '{print $4}' | grep -oE ':[0-9]+$' | sed 's/://g' | sort -u"
            system_stdout, _, _ = await executor.execute(system_cmd)
            system_ports = set()
            for line in system_stdout.strip().split('\n'):
                if line.strip():
                    try:
                        system_ports.add(int(line.strip()))
                    except ValueError:
                        pass
            
            # Combine all used ports
            all_used_ports = docker_ports | compose_ports | system_ports
            
            # Find available ports in range
            available_ports = []
            for port in range(min_port, max_port + 1):
                if port not in all_used_ports:
                    # Double-check by testing if port is actually listening
                    test_cmd = f"timeout 0.1 bash -c '</dev/tcp/localhost/{port}' 2>/dev/null || echo 'available'"
                    test_stdout, _, _ = await executor.execute(test_cmd)
                    is_listening = "available" not in test_stdout
                    
                    if not is_listening:
                        available_ports.append({
                            "port": port,
                            "available": True,
                            "checked_against": {
                                "running_containers": port in docker_ports,
                                "docker_compose_files": port in compose_ports,
                                "system_listening": port in system_ports
                            }
                        })
                        if len(available_ports) >= count:
                            break
            
            # Get summary of used ports in range
            used_in_range = [p for p in all_used_ports if min_port <= p <= max_port]
            
            return {
                "status": "success",
                "preferred_range": f"{min_port}-{max_port}",
                "available_ports": available_ports,
                "used_ports_in_range": sorted(used_in_range),
                "total_available": len(available_ports),
                "total_checked": len(used_in_range),
                "sources_checked": {
                    "running_containers": len(docker_ports),
                    "docker_compose_files": len(compose_ports),
                    "system_listening": len(system_ports)
                },
                "recommendation": available_ports[0]["port"] if available_ports else None
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "message": str(e)
            }

