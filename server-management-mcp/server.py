"""Main MCP server for home server management."""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mcp.server import Server
from mcp.server.stdio import stdio_server

from tools.docker import register_docker_tools
from tools.media_download import register_media_tools
from tools.monitoring import register_monitoring_tools
from tools.troubleshooting import register_troubleshooting_tools
from tools.git import register_git_tools
from tools.networking import register_networking_tools
from tools.system import register_system_tools
from tools.memory import register_memory_tools
from tools.agent_management import register_agent_management_tools
from tools.skill_management import register_skill_management_tools
from tools.task_coordination import register_task_coordination_tools
from tools.activity_monitoring import register_activity_monitoring_tools
from tools.communication import register_communication_tools
from tools.skill_activation import register_skill_activation_tools
from tools.dev_docs import register_dev_docs_tools

# Create MCP server instance
server = Server("home-server-management")

# Register all tool categories
register_docker_tools(server)
register_media_tools(server)
register_monitoring_tools(server)
register_troubleshooting_tools(server)
register_git_tools(server)
register_networking_tools(server)
register_system_tools(server)
register_memory_tools(server)
register_agent_management_tools(server)
register_skill_management_tools(server)
register_task_coordination_tools(server)
register_activity_monitoring_tools(server)
register_communication_tools(server)
register_skill_activation_tools(server)
register_dev_docs_tools(server)


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())

