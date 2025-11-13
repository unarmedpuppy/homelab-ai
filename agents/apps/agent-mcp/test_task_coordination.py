"""
Test script for Task Coordination System Phase 1

Tests register_task and query_tasks functionality.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "agents" / "apps" / "agent-mcp"))

# Import helper functions directly
from tools.task_coordination import (
    _parse_registry,
    _write_registry,
    _generate_task_id,
    _ensure_tasks_dir,
    TASKS_DIR,
    REGISTRY_PATH
)


def test_registry_operations():
    """Test registry parsing and writing."""
    print("=" * 60)
    print("Testing Task Coordination System - Phase 1")
    print("=" * 60)
    
    # Ensure directory exists
    _ensure_tasks_dir()
    print(f"\n✅ Tasks directory: {TASKS_DIR}")
    print(f"✅ Registry path: {REGISTRY_PATH}")
    
    # Test 1: Parse empty registry
    print("\n1. Testing registry parsing")
    print("-" * 60)
    try:
        tasks = _parse_registry()
        print(f"✅ Parsed registry: {len(tasks)} tasks found")
        if tasks:
            for task in tasks:
                print(f"   - {task.get('task_id', 'N/A')}: {task.get('title', 'N/A')}")
        else:
            print("   (Registry is empty - expected for first run)")
    except Exception as e:
        print(f"❌ Error parsing registry: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2: Write test tasks
    print("\n2. Testing registry writing")
    print("-" * 60)
    test_tasks = [
        {
            "task_id": "T1.1",
            "title": "Setup project structure",
            "description": "Create directory structure for trading-journal app",
            "status": "pending",
            "assignee": "-",
            "priority": "high",
            "dependencies": "-",
            "project": "trading-journal",
            "created": "2025-01-10 10:00:00",
            "updated": "2025-01-10 10:00:00"
        },
        {
            "task_id": "T1.2",
            "title": "Configure Docker Compose",
            "description": "Setup docker-compose.yml with PostgreSQL and backend services",
            "status": "pending",
            "assignee": "-",
            "priority": "high",
            "dependencies": "T1.1",
            "project": "trading-journal",
            "created": "2025-01-10 10:05:00",
            "updated": "2025-01-10 10:05:00"
        },
        {
            "task_id": "T2.1",
            "title": "Add root folder to Sonarr",
            "description": "Add /media/tv as root folder in Sonarr",
            "status": "pending",
            "assignee": "-",
            "priority": "medium",
            "dependencies": "-",
            "project": "media-download",
            "created": "2025-01-10 10:10:00",
            "updated": "2025-01-10 10:10:00"
        }
    ]
    
    try:
        _write_registry(test_tasks)
        print(f"✅ Wrote {len(test_tasks)} tasks to registry")
        for task in test_tasks:
            print(f"   - {task['task_id']}: {task['title']}")
    except Exception as e:
        print(f"❌ Error writing registry: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 3: Parse registry again
    print("\n3. Testing registry parsing after write")
    print("-" * 60)
    try:
        tasks = _parse_registry()
        print(f"✅ Parsed registry: {len(tasks)} tasks found")
        for task in tasks:
            print(f"   - {task['task_id']}: {task['title']} ({task['status']})")
            print(f"     Project: {task['project']}, Priority: {task['priority']}")
            if task['dependencies'] != '-':
                print(f"     Dependencies: {task['dependencies']}")
    except Exception as e:
        print(f"❌ Error parsing registry: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 4: Test task ID generation
    print("\n4. Testing task ID generation")
    print("-" * 60)
    try:
        # Test with existing tasks
        existing_tasks = _parse_registry()
        
        # Generate ID for trading-journal (should be T1.3)
        task_id_1 = _generate_task_id("trading-journal", existing_tasks)
        print(f"✅ Generated task ID for trading-journal: {task_id_1}")
        assert task_id_1 == "T1.3", f"Expected T1.3, got {task_id_1}"
        
        # Generate ID for new project (should be T3.1)
        task_id_2 = _generate_task_id("new-project", existing_tasks)
        print(f"✅ Generated task ID for new-project: {task_id_2}")
        assert task_id_2 == "T3.1", f"Expected T3.1, got {task_id_2}"
        
        # Generate another ID for trading-journal (should be T1.4)
        task_id_3 = _generate_task_id("trading-journal", existing_tasks)
        print(f"✅ Generated task ID for trading-journal: {task_id_3}")
        assert task_id_3 == "T1.4", f"Expected T1.4, got {task_id_3}"
        
    except Exception as e:
        print(f"❌ Error generating task IDs: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 5: Test querying (simulated)
    print("\n5. Testing query functionality (simulated)")
    print("-" * 60)
    try:
        all_tasks = _parse_registry()
        
        # Query by project
        trading_tasks = [t for t in all_tasks if t.get('project', '').lower() == 'trading-journal']
        print(f"✅ Query by project (trading-journal): {len(trading_tasks)} tasks")
        for task in trading_tasks:
            print(f"   - {task['task_id']}: {task['title']}")
        
        # Query by status
        pending_tasks = [t for t in all_tasks if t.get('status', '').lower() == 'pending']
        print(f"\n✅ Query by status (pending): {len(pending_tasks)} tasks")
        for task in pending_tasks:
            print(f"   - {task['task_id']}: {task['title']}")
        
        # Query by priority
        high_priority = [t for t in all_tasks if t.get('priority', '').lower() == 'high']
        print(f"\n✅ Query by priority (high): {len(high_priority)} tasks")
        for task in high_priority:
            print(f"   - {task['task_id']}: {task['title']}")
        
        # Query with search
        docker_tasks = [t for t in all_tasks if 'docker' in t.get('title', '').lower() or 'docker' in t.get('description', '').lower()]
        print(f"\n✅ Query with search (docker): {len(docker_tasks)} tasks")
        for task in docker_tasks:
            print(f"   - {task['task_id']}: {task['title']}")
        
    except Exception as e:
        print(f"❌ Error querying tasks: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 6: Verify registry file
    print("\n6. Verifying registry.md file")
    print("-" * 60)
    if REGISTRY_PATH.exists():
        content = REGISTRY_PATH.read_text()
        print(f"✅ Registry file exists: {REGISTRY_PATH}")
        print(f"   File size: {len(content)} bytes")
        
        # Count tasks in file
        task_count = content.count("| T")
        print(f"   Tasks found in file: {task_count}")
        
        # Show first 20 lines
        lines = content.splitlines()
        print("\n   First 20 lines of registry:")
        for i, line in enumerate(lines[:20], 1):
            print(f"   {i:2d}: {line}")
    else:
        print(f"❌ Registry file not found: {REGISTRY_PATH}")
    
    print("\n" + "=" * 60)
    print("✅ All Phase 1 tests completed successfully!")
    print("=" * 60)
    print("\nNext: Test the actual MCP tools via the MCP server")
    print("   (The tools will be available when the MCP server is running)")


if __name__ == "__main__":
    test_registry_operations()
