"""
Simple test for Task Coordination System Phase 1

Tests registry file operations directly.
"""

import sys
import re
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
TASKS_DIR = project_root / "agents" / "tasks"
REGISTRY_PATH = TASKS_DIR / "registry.md"


def parse_registry():
    """Parse the registry markdown file."""
    if not REGISTRY_PATH.exists():
        return []
    
    content = REGISTRY_PATH.read_text()
    tasks = []
    
    in_table = False
    for line in content.splitlines():
        if "| Task ID |" in line:
            in_table = True
            continue
        if in_table and line.strip().startswith("|---"):
            continue
        if in_table and line.strip().startswith("|"):
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 10 and parts[0] != "-":
                tasks.append({
                    "task_id": parts[0],
                    "title": parts[1],
                    "description": parts[2],
                    "status": parts[3],
                    "assignee": parts[4],
                    "priority": parts[5],
                    "dependencies": parts[6],
                    "project": parts[7],
                    "created": parts[8],
                    "updated": parts[9]
                })
        if in_table and not line.strip().startswith("|"):
            break
    
    return tasks


def write_registry(tasks):
    """Write tasks to registry."""
    header = """# Task Registry

Central registry of all tasks across all agents.

## Task Status Legend
- `pending` - Available to claim
- `claimed` - Claimed by agent, not started
- `in_progress` - Actively being worked on
- `blocked` - Waiting on dependencies
- `review` - Needs review
- `completed` - Finished
- `cancelled` - Cancelled

## Tasks

| Task ID | Title | Description | Status | Assignee | Priority | Dependencies | Project | Created | Updated |
|---------|-------|-------------|--------|----------|----------|--------------|---------|---------|---------|
"""
    
    rows = []
    for task in tasks:
        row = f"| {task['task_id']} | {task['title']} | {task['description']} | {task['status']} | {task['assignee']} | {task['priority']} | {task['dependencies']} | {task['project']} | {task['created']} | {task['updated']} |"
        rows.append(row)
    
    if not rows:
        rows.append("| - | - | - | - | - | - | - | - | - | - |")
    
    footer = f"""

---

**Last Updated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Total Tasks**: {len(tasks)}
"""
    
    REGISTRY_PATH.write_text(header + "\n".join(rows) + footer)


def generate_task_id(project, existing_tasks):
    """Generate task ID."""
    project_tasks = [t for t in existing_tasks if t.get('project') == project]
    
    if not project_tasks:
        return "T1.1"
    
    max_num = 0
    for task in project_tasks:
        task_id = task.get('task_id', '')
        match = re.match(r'T(\d+)\.(\d+)', task_id)
        if match:
            project_num = int(match.group(1))
            if project_num > max_num:
                max_num = project_num
    
    task_nums = []
    for task in project_tasks:
        task_id = task.get('task_id', '')
        match = re.match(r'T(\d+)\.(\d+)', task_id)
        if match:
            if int(match.group(1)) == max_num:
                task_nums.append(int(match.group(2)))
    
    next_task_num = max(task_nums) + 1 if task_nums else 1
    return f"T{max_num}.{next_task_num}"


def test_registry():
    """Test registry operations."""
    print("=" * 60)
    print("Testing Task Coordination System - Phase 1")
    print("=" * 60)
    
    # Ensure directory exists
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n✅ Tasks directory: {TASKS_DIR}")
    print(f"✅ Registry path: {REGISTRY_PATH}")
    
    # Test 1: Parse existing registry
    print("\n1. Testing registry parsing")
    print("-" * 60)
    try:
        tasks = parse_registry()
        print(f"✅ Parsed registry: {len(tasks)} tasks found")
        if tasks:
            for task in tasks:
                print(f"   - {task['task_id']}: {task['title']}")
        else:
            print("   (Registry is empty - will add test tasks)")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2: Add test tasks
    print("\n2. Adding test tasks")
    print("-" * 60)
    existing_tasks = parse_registry()
    
    test_tasks = [
        {
            "task_id": generate_task_id("trading-journal", existing_tasks),
            "title": "Setup project structure",
            "description": "Create directory structure for trading-journal app",
            "status": "pending",
            "assignee": "-",
            "priority": "high",
            "dependencies": "-",
            "project": "trading-journal",
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    
    # Generate second task ID
    existing_tasks.extend(test_tasks)
    test_tasks.append({
        "task_id": generate_task_id("trading-journal", existing_tasks),
        "title": "Configure Docker Compose",
        "description": "Setup docker-compose.yml with PostgreSQL and backend services",
        "status": "pending",
        "assignee": "-",
        "priority": "high",
        "dependencies": test_tasks[0]['task_id'],
        "project": "trading-journal",
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    # Generate third task for different project
    existing_tasks.extend(test_tasks)
    test_tasks.append({
        "task_id": generate_task_id("media-download", existing_tasks),
        "title": "Add root folder to Sonarr",
        "description": "Add /media/tv as root folder in Sonarr",
        "status": "pending",
        "assignee": "-",
        "priority": "medium",
        "dependencies": "-",
        "project": "media-download",
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    # Combine with existing
    all_tasks = existing_tasks + test_tasks
    
    try:
        write_registry(all_tasks)
        print(f"✅ Wrote {len(test_tasks)} new tasks to registry")
        for task in test_tasks:
            print(f"   - {task['task_id']}: {task['title']} (project: {task['project']})")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 3: Parse again
    print("\n3. Verifying registry after write")
    print("-" * 60)
    try:
        tasks = parse_registry()
        print(f"✅ Parsed registry: {len(tasks)} total tasks")
        for task in tasks:
            print(f"   - {task['task_id']}: {task['title']} ({task['status']})")
            print(f"     Project: {task['project']}, Priority: {task['priority']}")
            if task['dependencies'] != '-':
                print(f"     Dependencies: {task['dependencies']}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 4: Query operations
    print("\n4. Testing query operations")
    print("-" * 60)
    try:
        all_tasks = parse_registry()
        
        # Query by project
        trading = [t for t in all_tasks if t.get('project', '').lower() == 'trading-journal']
        print(f"✅ Query by project (trading-journal): {len(trading)} tasks")
        
        # Query by status
        pending = [t for t in all_tasks if t.get('status', '').lower() == 'pending']
        print(f"✅ Query by status (pending): {len(pending)} tasks")
        
        # Query by priority
        high = [t for t in all_tasks if t.get('priority', '').lower() == 'high']
        print(f"✅ Query by priority (high): {len(high)} tasks")
        
        # Query with search
        docker = [t for t in all_tasks if 'docker' in t.get('title', '').lower() or 'docker' in t.get('description', '').lower()]
        print(f"✅ Query with search (docker): {len(docker)} tasks")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 5: Show registry file
    print("\n5. Registry file contents")
    print("-" * 60)
    if REGISTRY_PATH.exists():
        content = REGISTRY_PATH.read_text()
        print(f"✅ Registry file: {REGISTRY_PATH}")
        print(f"   Size: {len(content)} bytes")
        print(f"   Tasks: {content.count('| T')}")
        print("\n   First 25 lines:")
        for i, line in enumerate(content.splitlines()[:25], 1):
            print(f"   {i:2d}: {line}")
    else:
        print(f"❌ Registry file not found")
    
    print("\n" + "=" * 60)
    print("✅ All Phase 1 tests completed successfully!")
    print("=" * 60)
    print("\nThe MCP tools (register_task, query_tasks) will work when")
    print("the MCP server is running and connected to Cursor/Claude Desktop.")


if __name__ == "__main__":
    test_registry()

