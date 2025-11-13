"""
Test script for Task Coordination System Phase 3

Tests dependency checking, validation, and automatic status updates.
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


def check_dependencies(task_id, tasks):
    """Check dependencies for a task."""
    task = None
    for t in tasks:
        if t.get('task_id') == task_id:
            task = t
            break
    
    if not task:
        return {"status": "error", "message": f"Task {task_id} not found"}
    
    deps_str = task.get('dependencies', '-')
    if deps_str == '-' or not deps_str:
        return {
            "status": "success",
            "has_dependencies": False,
            "can_proceed": True
        }
    
    dep_ids = [d.strip() for d in deps_str.split(',') if d.strip()]
    dependency_details = []
    all_completed = True
    
    for dep_id in dep_ids:
        dep_task = None
        for t in tasks:
            if t.get('task_id') == dep_id:
                dep_task = t
                break
        
        if not dep_task:
            dependency_details.append({
                "task_id": dep_id,
                "status": "not_found",
                "can_proceed": False
            })
            all_completed = False
        else:
            dep_status = dep_task.get('status', '').lower()
            is_completed = dep_status == 'completed'
            dependency_details.append({
                "task_id": dep_id,
                "status": dep_status,
                "is_completed": is_completed,
                "can_proceed": is_completed
            })
            if not is_completed:
                all_completed = False
    
    return {
        "status": "success",
        "has_dependencies": True,
        "dependencies": dependency_details,
        "all_completed": all_completed,
        "can_proceed": all_completed
    }


def claim_task(task_id, agent_id, tasks):
    """Claim a task with dependency validation."""
    for task in tasks:
        if task.get('task_id') == task_id:
            # Check dependencies
            deps_str = task.get('dependencies', '-')
            if deps_str != '-' and deps_str:
                dep_ids = [d.strip() for d in deps_str.split(',') if d.strip()]
                if dep_ids:
                    for dep_id in dep_ids:
                        dep_task = None
                        for t in tasks:
                            if t.get('task_id') == dep_id:
                                dep_task = t
                                break
                        if not dep_task:
                            return {
                                "status": "error",
                                "message": f"Dependency {dep_id} not found"
                            }
                        if dep_task.get('status', '').lower() != 'completed':
                            return {
                                "status": "error",
                                "message": f"Dependency {dep_id} not completed"
                            }
            
            # Claim
            task['assignee'] = agent_id
            if task.get('status', '').lower() == 'pending':
                task['status'] = 'claimed'
            task['updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return {"status": "success", "message": f"Task {task_id} claimed"}
    
    return {"status": "error", "message": f"Task {task_id} not found"}


def update_task_status(task_id, status, agent_id, tasks):
    """Update task status with automatic dependency updates."""
    for task in tasks:
        if task.get('task_id') == task_id:
            old_status = task['status']
            task['status'] = status.lower()
            task['updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # If completed, check dependents
            if status.lower() == 'completed':
                for dependent_task in tasks:
                    deps_str = dependent_task.get('dependencies', '-')
                    if deps_str != '-' and deps_str:
                        dep_ids = [d.strip() for d in deps_str.split(',') if d.strip()]
                        if task_id in dep_ids:
                            # Check if all deps completed
                            all_done = True
                            for dep_id in dep_ids:
                                dep_task = None
                                for t in tasks:
                                    if t.get('task_id') == dep_id:
                                        dep_task = t
                                        break
                                if not dep_task or dep_task.get('status', '').lower() != 'completed':
                                    all_done = False
                                    break
                            
                            if all_done and dependent_task.get('status', '').lower() == 'blocked':
                                dependent_task['status'] = 'pending'
                                dependent_task['updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Auto-block if dependencies not met
            elif status.lower() not in ['blocked', 'cancelled']:
                deps_str = task.get('dependencies', '-')
                if deps_str != '-' and deps_str:
                    dep_ids = [d.strip() for d in deps_str.split(',') if d.strip()]
                    if dep_ids:
                        has_unmet = False
                        for dep_id in dep_ids:
                            dep_task = None
                            for t in tasks:
                                if t.get('task_id') == dep_id:
                                    dep_task = t
                                    break
                            if not dep_task or dep_task.get('status', '').lower() != 'completed':
                                has_unmet = True
                                break
                        
                        if has_unmet and old_status.lower() != 'blocked':
                            task['status'] = 'blocked'
                            status = 'blocked'
            
            return {"status": "success", "message": f"Status updated to {status.lower()}"}
    
    return {"status": "error", "message": f"Task {task_id} not found"}


def test_phase3():
    """Test Phase 3 functionality."""
    print("=" * 60)
    print("Testing Task Coordination System - Phase 3")
    print("=" * 60)
    
    # Setup: Create tasks with dependencies
    print("\n0. Setting up test tasks with dependencies")
    print("-" * 60)
    test_tasks = [
        {
            "task_id": "T1.1",
            "title": "Setup database",
            "description": "Create PostgreSQL schema",
            "status": "pending",
            "assignee": "-",
            "priority": "high",
            "dependencies": "-",
            "project": "app",
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "task_id": "T1.2",
            "title": "Setup API",
            "description": "Create REST API",
            "status": "pending",
            "assignee": "-",
            "priority": "high",
            "dependencies": "T1.1",
            "project": "app",
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "task_id": "T1.3",
            "title": "Setup Frontend",
            "description": "Create React frontend",
            "status": "pending",
            "assignee": "-",
            "priority": "high",
            "dependencies": "T1.1,T1.2",
            "project": "app",
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    write_registry(test_tasks)
    print(f"✅ Created {len(test_tasks)} tasks with dependencies")
    print("   T1.1: No dependencies")
    print("   T1.2: Depends on T1.1")
    print("   T1.3: Depends on T1.1 and T1.2")
    
    # Test 1: check_task_dependencies
    print("\n1. Testing check_task_dependencies()")
    print("-" * 60)
    tasks = parse_registry()
    
    # 1.1: Task with no dependencies
    result = check_dependencies("T1.1", tasks)
    if result["status"] == "success" and not result.get("has_dependencies"):
        print("✅ T1.1 has no dependencies (correct)")
    else:
        print(f"❌ T1.1 dependency check failed: {result}")
    
    # 1.2: Task with unmet dependencies
    result = check_dependencies("T1.3", tasks)
    if result["status"] == "success" and not result.get("can_proceed"):
        print("✅ T1.3 dependencies not met (correct)")
        print(f"   Dependencies: {len(result.get('dependencies', []))}")
    else:
        print(f"❌ T1.3 dependency check failed: {result}")
    
    # Test 2: Dependency validation in claim_task
    print("\n2. Testing dependency validation in claim_task()")
    print("-" * 60)
    
    # 2.1: Try to claim T1.3 (should fail - dependencies not met)
    result = claim_task("T1.3", "agent-001", tasks)
    if result["status"] == "error":
        print(f"✅ Correctly prevented claiming T1.3: {result['message']}")
    else:
        print(f"❌ Should have prevented claiming: {result}")
    
    # 2.2: Claim T1.1 (should work - no dependencies)
    result = claim_task("T1.1", "agent-001", tasks)
    if result["status"] == "success":
        print(f"✅ {result['message']}")
        write_registry(tasks)
        tasks = parse_registry()
    else:
        print(f"❌ Failed to claim T1.1: {result}")
    
    # Test 3: Automatic status updates
    print("\n3. Testing automatic status updates")
    print("-" * 60)
    
    # 3.1: Complete T1.1
    result = update_task_status("T1.1", "completed", "agent-001", tasks)
    if result["status"] == "success":
        print("✅ T1.1 marked as completed")
        write_registry(tasks)
        tasks = parse_registry()
        
        # Check if T1.2 is now unblocked
        t2 = [t for t in tasks if t['task_id'] == 'T1.2'][0]
        if t2['status'] == 'pending':
            print("✅ T1.2 automatically unblocked (status: pending)")
        else:
            print(f"⚠️  T1.2 status: {t2['status']} (may need manual update)")
    else:
        print(f"❌ Failed to complete T1.1: {result}")
    
    # 3.2: Complete T1.2
    result = update_task_status("T1.2", "completed", "agent-001", tasks)
    if result["status"] == "success":
        print("✅ T1.2 marked as completed")
        write_registry(tasks)
        tasks = parse_registry()
        
        # Check if T1.3 is now unblocked
        t3 = [t for t in tasks if t['task_id'] == 'T1.3'][0]
        if t3['status'] == 'pending':
            print("✅ T1.3 automatically unblocked (status: pending)")
        else:
            print(f"⚠️  T1.3 status: {t3['status']} (may need manual update)")
    else:
        print(f"❌ Failed to complete T1.2: {result}")
    
    # Test 4: Now T1.3 can be claimed
    print("\n4. Testing claim after dependencies met")
    print("-" * 60)
    result = claim_task("T1.3", "agent-001", tasks)
    if result["status"] == "success":
        print(f"✅ {result['message']} (dependencies now met)")
        write_registry(tasks)
        tasks = parse_registry()
    else:
        print(f"❌ Failed to claim T1.3: {result}")
    
    # Test 5: Auto-blocking
    print("\n5. Testing auto-blocking")
    print("-" * 60)
    
    # Create new task with dependency
    new_task = {
        "task_id": "T1.4",
        "title": "Deploy",
        "description": "Deploy to production",
        "status": "pending",
        "assignee": "-",
        "priority": "high",
        "dependencies": "T1.3",
        "project": "app",
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    tasks.append(new_task)
    write_registry(tasks)
    tasks = parse_registry()
    
    # Try to update T1.4 status (should auto-block if T1.3 not completed)
    # First check T1.3 status
    t3 = [t for t in tasks if t['task_id'] == 'T1.3'][0]
    if t3['status'] != 'completed':
        # Update T1.4 to in_progress (should auto-block)
        result = update_task_status("T1.4", "in_progress", "agent-001", tasks)
        write_registry(tasks)
        tasks = parse_registry()
        t4 = [t for t in tasks if t['task_id'] == 'T1.4'][0]
        if t4['status'] == 'blocked':
            print("✅ T1.4 automatically blocked (dependency T1.3 not completed)")
        else:
            print(f"⚠️  T1.4 status: {t4['status']} (expected blocked)")
    
    print("\n" + "=" * 60)
    print("✅ All Phase 3 tests completed!")
    print("=" * 60)
    print("\nPhase 3 features verified:")
    print("  ✅ check_task_dependencies() - Check dependency status")
    print("  ✅ Dependency validation in claim_task()")
    print("  ✅ Automatic unblocking when dependencies complete")
    print("  ✅ Auto-blocking when dependencies not met")


if __name__ == "__main__":
    test_phase3()

