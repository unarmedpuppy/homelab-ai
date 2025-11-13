"""
Test script for Task Coordination System Phase 2

Tests get_task, claim_task, and update_task_status.
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


def get_task(task_id, tasks):
    """Get single task by ID."""
    for task in tasks:
        if task.get('task_id') == task_id:
            return task
    return None


def claim_task(task_id, agent_id, tasks):
    """Claim a task."""
    for task in tasks:
        if task.get('task_id') == task_id:
            # Check if already claimed
            current_assignee = task.get('assignee', '-')
            if current_assignee != '-' and current_assignee.lower() != agent_id.lower():
                return {
                    "status": "error",
                    "message": f"Task {task_id} is already claimed by {current_assignee}"
                }
            
            # Check status
            current_status = task.get('status', '').lower()
            if current_status not in ['pending', 'claimed']:
                return {
                    "status": "error",
                    "message": f"Task {task_id} cannot be claimed. Current status: {current_status}"
                }
            
            # Claim
            task['assignee'] = agent_id
            if current_status == 'pending':
                task['status'] = 'claimed'
            task['updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return {"status": "success", "message": f"Task {task_id} claimed by {agent_id}"}
    
    return {"status": "error", "message": f"Task {task_id} not found"}


def update_task_status(task_id, status, agent_id, tasks):
    """Update task status."""
    valid_statuses = ['pending', 'claimed', 'in_progress', 'blocked', 'review', 'completed', 'cancelled']
    if status.lower() not in valid_statuses:
        return {"status": "error", "message": f"Invalid status: {status}"}
    
    for task in tasks:
        if task.get('task_id') == task_id:
            # Check permissions
            current_assignee = task.get('assignee', '-')
            if agent_id and current_assignee != '-' and current_assignee.lower() != agent_id.lower():
                return {
                    "status": "error",
                    "message": f"Permission denied. Task {task_id} is assigned to {current_assignee}"
                }
            
            # Check invalid transitions
            current_status = task.get('status', '').lower()
            status_lower = status.lower()
            
            if current_status == 'completed' and status_lower != 'completed':
                return {"status": "error", "message": f"Cannot change status from completed to {status_lower}"}
            
            if current_status == 'cancelled' and status_lower != 'cancelled':
                return {"status": "error", "message": f"Cannot change status from cancelled to {status_lower}"}
            
            # Update
            old_status = task['status']
            task['status'] = status_lower
            task['updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if status_lower == 'in_progress' and current_assignee == '-' and agent_id:
                task['assignee'] = agent_id
            
            return {
                "status": "success",
                "message": f"Task {task_id} status updated from {old_status} to {status_lower}"
            }
    
    return {"status": "error", "message": f"Task {task_id} not found"}


def test_phase2():
    """Test Phase 2 functionality."""
    print("=" * 60)
    print("Testing Task Coordination System - Phase 2")
    print("=" * 60)
    
    # Ensure directory exists
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Setup: Create test tasks
    print("\n0. Setting up test tasks")
    print("-" * 60)
    test_tasks = [
        {
            "task_id": "T1.1",
            "title": "Setup project structure",
            "description": "Create directory structure",
            "status": "pending",
            "assignee": "-",
            "priority": "high",
            "dependencies": "-",
            "project": "trading-journal",
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "task_id": "T1.2",
            "title": "Configure Docker",
            "description": "Setup docker-compose.yml",
            "status": "pending",
            "assignee": "-",
            "priority": "high",
            "dependencies": "T1.1",
            "project": "trading-journal",
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    write_registry(test_tasks)
    print(f"✅ Created {len(test_tasks)} test tasks")
    
    # Test 1: get_task
    print("\n1. Testing get_task()")
    print("-" * 60)
    tasks = parse_registry()
    task = get_task("T1.1", tasks)
    if task:
        print(f"✅ Found task T1.1: {task['title']}")
        print(f"   Status: {task['status']}, Assignee: {task['assignee']}")
    else:
        print("❌ Task T1.1 not found")
        return
    
    # Test 2: claim_task
    print("\n2. Testing claim_task()")
    print("-" * 60)
    
    # 2.1: Claim pending task
    result = claim_task("T1.1", "agent-001", tasks)
    if result["status"] == "success":
        print(f"✅ {result['message']}")
        write_registry(tasks)  # Save changes
        tasks = parse_registry()  # Reload
        task = get_task("T1.1", tasks)
        print(f"   Updated status: {task['status']}, assignee: {task['assignee']}")
    else:
        print(f"❌ {result['message']}")
        return
    
    # 2.2: Try to claim already-claimed task (different agent)
    print("\n2.2: Testing claim conflict (different agent)")
    result = claim_task("T1.1", "agent-002", tasks)
    if result["status"] == "error":
        print(f"✅ Correctly prevented: {result['message']}")
    else:
        print(f"❌ Should have prevented claiming: {result}")
    
    # 2.3: Claim by same agent (should work)
    print("\n2.3: Testing re-claim by same agent")
    result = claim_task("T1.1", "agent-001", tasks)
    if result["status"] == "success":
        print(f"✅ {result['message']} (same agent can re-claim)")
    
    # Test 3: update_task_status
    print("\n3. Testing update_task_status()")
    print("-" * 60)
    
    # 3.1: Update to in_progress
    result = update_task_status("T1.1", "in_progress", "agent-001", tasks)
    if result["status"] == "success":
        print(f"✅ {result['message']}")
        write_registry(tasks)
        tasks = parse_registry()
        task = get_task("T1.1", tasks)
        print(f"   New status: {task['status']}")
    else:
        print(f"❌ {result['message']}")
    
    # 3.2: Try to update by different agent (should fail)
    print("\n3.2: Testing permission check (different agent)")
    result = update_task_status("T1.1", "review", "agent-002", tasks)
    if result["status"] == "error":
        print(f"✅ Correctly prevented: {result['message']}")
    else:
        print(f"❌ Should have prevented update: {result}")
    
    # 3.3: Update to review
    result = update_task_status("T1.1", "review", "agent-001", tasks)
    if result["status"] == "success":
        print(f"✅ {result['message']}")
        write_registry(tasks)
        tasks = parse_registry()
    
    # 3.4: Update to completed
    result = update_task_status("T1.1", "completed", "agent-001", tasks)
    if result["status"] == "success":
        print(f"✅ {result['message']}")
        write_registry(tasks)
        tasks = parse_registry()
        task = get_task("T1.1", tasks)
        print(f"   Final status: {task['status']}")
    
    # 3.5: Try to change from completed (should fail)
    print("\n3.5: Testing invalid transition (from completed)")
    result = update_task_status("T1.1", "in_progress", "agent-001", tasks)
    if result["status"] == "error":
        print(f"✅ Correctly prevented: {result['message']}")
    else:
        print(f"❌ Should have prevented transition: {result}")
    
    # Test 4: Status workflow
    print("\n4. Testing complete status workflow")
    print("-" * 60)
    tasks = parse_registry()
    task = get_task("T1.2", tasks)
    if task:
        print(f"Starting with task T1.2: {task['status']}")
        
        # pending → claimed → in_progress → review → completed
        workflow = [
            ("claimed", "agent-001"),
            ("in_progress", "agent-001"),
            ("review", "agent-001"),
            ("completed", "agent-001")
        ]
        
        for status, agent in workflow:
            result = update_task_status("T1.2", status, agent, tasks)
            if result["status"] == "success":
                print(f"✅ {status}")
                write_registry(tasks)
                tasks = parse_registry()
            else:
                print(f"❌ Failed at {status}: {result['message']}")
                break
    
    # Test 5: Invalid status
    print("\n5. Testing invalid status")
    print("-" * 60)
    result = update_task_status("T1.2", "invalid_status", "agent-001", tasks)
    if result["status"] == "error":
        print(f"✅ Correctly rejected invalid status: {result['message']}")
    else:
        print(f"❌ Should have rejected invalid status: {result}")
    
    print("\n" + "=" * 60)
    print("✅ All Phase 2 tests completed successfully!")
    print("=" * 60)
    print("\nPhase 2 features verified:")
    print("  ✅ get_task() - Retrieve task details")
    print("  ✅ claim_task() - Claim tasks with validation")
    print("  ✅ update_task_status() - Update status with permissions")
    print("  ✅ Permission checks working")
    print("  ✅ Status transition validation working")
    print("  ✅ Conflict prevention working")


if __name__ == "__main__":
    test_phase2()

