"""Simple test script to verify MCP server setup."""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from clients.remote_exec import RemoteExecutor


async def test_remote_exec():
    """Test remote execution."""
    print("Testing remote execution...")
    executor = RemoteExecutor()
    
    # Simple test command
    stdout, stderr, returncode = await executor.execute("echo 'Hello from server'")
    
    print(f"Return code: {returncode}")
    print(f"Stdout: {stdout}")
    if stderr:
        print(f"Stderr: {stderr}")
    
    if returncode == 0:
        print("✅ Remote execution works!")
        return True
    else:
        print("❌ Remote execution failed")
        return False


async def test_docker_list():
    """Test Docker container listing."""
    print("\nTesting Docker container listing...")
    executor = RemoteExecutor()
    
    command = "docker ps --format '{{.Names}}\t{{.Status}}' | head -5"
    stdout, stderr, returncode = await executor.execute(command)
    
    print(f"Return code: {returncode}")
    if stdout:
        print("Sample containers:")
        for line in stdout.strip().split('\n')[:5]:
            if line.strip():
                print(f"  - {line}")
    
    if returncode == 0:
        print("✅ Docker access works!")
        return True
    else:
        print(f"❌ Docker access failed: {stderr}")
        return False


async def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    sonarr_key = settings.get("sonarr", "api_key")
    server_host = settings.get("server", "host")
    
    print(f"Sonarr API Key: {sonarr_key[:10]}...")
    print(f"Server Host: {server_host}")
    
    if sonarr_key and server_host:
        print("✅ Configuration loaded!")
        return True
    else:
        print("❌ Configuration missing")
        return False


async def main():
    """Run all tests."""
    print("=" * 50)
    print("MCP Server Setup Test")
    print("=" * 50)
    
    results = []
    
    # Test configuration
    results.append(await test_config())
    
    # Test remote execution
    results.append(await test_remote_exec())
    
    # Test Docker access
    results.append(await test_docker_list())
    
    print("\n" + "=" * 50)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 50)
    
    if all(results):
        print("\n✅ All tests passed! MCP server should work.")
        return 0
    else:
        print("\n❌ Some tests failed. Check configuration and server access.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

