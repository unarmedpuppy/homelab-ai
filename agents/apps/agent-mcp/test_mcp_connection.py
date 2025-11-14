#!/usr/bin/env python3
"""Test MCP server connection via stdio (simulates Cursor connection)."""
import json
import sys
import subprocess
from pathlib import Path

def test_mcp_server():
    """Test the MCP server by sending initialization and list_tools requests."""
    
    server_path = Path(__file__).parent / "server.py"
    python_path = "/opt/homebrew/bin/python3"
    project_root = Path(__file__).parent.parent.parent.parent
    
    # Set up environment
    env = {
        **dict(os.environ),
        "PYTHONPATH": str(project_root),
        "AGENT_MONITORING_API_URL": "http://localhost:3001"
    }
    
    # Start the server
    process = subprocess.Popen(
        [python_path, str(server_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        cwd=str(server_path.parent)
    )
    
    try:
        # Send initialization request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("Sending initialization request...")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read response (with timeout)
        import select
        import time
        
        timeout = 5
        start = time.time()
        response_lines = []
        
        while time.time() - start < timeout:
            if process.stdout.readable():
                line = process.stdout.readline()
                if line:
                    response_lines.append(line.strip())
                    try:
                        response = json.loads(line)
                        if response.get("id") == 1:
                            print(f"✅ Initialization response received:")
                            print(json.dumps(response, indent=2))
                            break
                    except json.JSONDecodeError:
                        continue
        
        # Send list_tools request
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        print("\nSending list_tools request...")
        process.stdin.write(json.dumps(list_tools_request) + "\n")
        process.stdin.flush()
        
        # Read tools response
        start = time.time()
        while time.time() - start < timeout:
            if process.stdout.readable():
                line = process.stdout.readline()
                if line:
                    try:
                        response = json.loads(line)
                        if response.get("id") == 2:
                            tools = response.get("result", {}).get("tools", [])
                            print(f"✅ List tools response received: {len(tools)} tools")
                            if tools:
                                print(f"\nFirst 5 tools:")
                                for tool in tools[:5]:
                                    print(f"  - {tool.get('name')}: {tool.get('description', '')[:50]}")
                            return True
                    except json.JSONDecodeError:
                        continue
        
        print("❌ No response received")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        process.terminate()
        process.wait(timeout=2)

if __name__ == "__main__":
    import os
    result = test_mcp_server()
    sys.exit(0 if result else 1)

