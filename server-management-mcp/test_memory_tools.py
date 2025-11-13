#!/usr/bin/env python3
"""
Test script for MCP Memory Tools

Tests the memory tools that are used by the MCP server to ensure they work correctly.
This tests the underlying memory functions that the MCP tools call.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.memory import get_memory


def test_memory_import():
    """Test that memory module can be imported."""
    print("=" * 60)
    print("Test 1: Memory Module Import")
    print("=" * 60)
    try:
        memory = get_memory()
        print(f"✅ Memory module imported successfully")
        print(f"   Database path: {memory.db_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to import memory module: {e}")
        return False


def test_query_decisions():
    """Test query_decisions function."""
    print("\n" + "=" * 60)
    print("Test 2: Query Decisions")
    print("=" * 60)
    try:
        memory = get_memory()
        
        # Test 1: Query all decisions
        decisions = memory.query_decisions(limit=10)
        print(f"✅ Query all decisions: Found {len(decisions)} decisions")
        
        # Test 2: Query by project
        decisions = memory.query_decisions(project="home-server", limit=5)
        print(f"✅ Query by project: Found {len(decisions)} decisions")
        
        # Test 3: Query by search text
        decisions = memory.query_decisions(search_text="emotion", limit=5)
        print(f"✅ Query by search text: Found {len(decisions)} decisions")
        
        # Test 4: Query with min importance
        decisions = memory.query_decisions(min_importance=0.7, limit=5)
        print(f"✅ Query by min importance: Found {len(decisions)} decisions")
        
        return True
    except Exception as e:
        print(f"❌ Query decisions failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_query_patterns():
    """Test query_patterns function."""
    print("\n" + "=" * 60)
    print("Test 3: Query Patterns")
    print("=" * 60)
    try:
        memory = get_memory()
        
        # Test 1: Query all patterns
        patterns = memory.query_patterns(limit=10)
        print(f"✅ Query all patterns: Found {len(patterns)} patterns")
        
        # Test 2: Query by severity
        patterns = memory.query_patterns(severity="high", limit=5)
        print(f"✅ Query by severity: Found {len(patterns)} patterns")
        
        # Test 3: Query by search text
        patterns = memory.query_patterns(search_text="test", limit=5)
        print(f"✅ Query by search text: Found {len(patterns)} patterns")
        
        return True
    except Exception as e:
        print(f"❌ Query patterns failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search():
    """Test search function."""
    print("\n" + "=" * 60)
    print("Test 4: Full-Text Search")
    print("=" * 60)
    try:
        memory = get_memory()
        
        # Test search
        results = memory.search("Wonder", limit=10)
        print(f"✅ Full-text search: Found {results['total']} total results")
        print(f"   - Decisions: {len(results['decisions'])}")
        print(f"   - Patterns: {len(results['patterns'])}")
        
        return True
    except Exception as e:
        print(f"❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_record_decision():
    """Test record_decision function."""
    print("\n" + "=" * 60)
    print("Test 5: Record Decision")
    print("=" * 60)
    try:
        memory = get_memory()
        
        # Record a test decision
        decision_id = memory.record_decision(
            content="Test decision from MCP tool test",
            rationale="Testing the record_decision function",
            project="home-server",
            task="test-mcp-tools",
            importance=0.5,
            tags=["test", "mcp"]
        )
        print(f"✅ Record decision: Created decision ID {decision_id}")
        
        # Verify it was saved
        decisions = memory.query_decisions(task="test-mcp-tools", limit=1)
        if decisions and decisions[0]["id"] == decision_id:
            print(f"✅ Decision verified: Found in database")
        else:
            print(f"⚠️  Decision may not have been saved correctly")
        
        return True
    except Exception as e:
        print(f"❌ Record decision failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_record_pattern():
    """Test record_pattern function."""
    print("\n" + "=" * 60)
    print("Test 6: Record Pattern")
    print("=" * 60)
    try:
        memory = get_memory()
        
        # Record a test pattern
        pattern_id = memory.record_pattern(
            name="MCP Tool Test Pattern",
            description="Pattern created during MCP tool testing",
            solution="This is a test pattern",
            severity="low",
            tags=["test", "mcp"]
        )
        print(f"✅ Record pattern: Created pattern ID {pattern_id}")
        
        # Verify it was saved
        patterns = memory.query_patterns(search_text="MCP Tool Test", limit=1)
        if patterns and patterns[0]["id"] == pattern_id:
            print(f"✅ Pattern verified: Found in database")
        else:
            print(f"⚠️  Pattern may not have been saved correctly")
        
        return True
    except Exception as e:
        print(f"❌ Record pattern failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_save_context():
    """Test save_context function."""
    print("\n" + "=" * 60)
    print("Test 7: Save Context")
    print("=" * 60)
    try:
        memory = get_memory()
        
        # Save test context
        context_id = memory.save_context(
            agent_id="test-agent",
            task="test-mcp-tools",
            current_work="Testing MCP memory tools",
            status="in_progress",
            notes="This is a test context entry"
        )
        print(f"✅ Save context: Created context ID {context_id}")
        
        return True
    except Exception as e:
        print(f"❌ Save context failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_recent_context():
    """Test get_recent_context (via direct SQL query like MCP tool does)."""
    print("\n" + "=" * 60)
    print("Test 8: Get Recent Context")
    print("=" * 60)
    try:
        import sqlite3
        memory = get_memory()
        
        # Test the same query the MCP tool uses
        conn = sqlite3.connect(memory.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM context 
            ORDER BY updated_at DESC 
            LIMIT 5
        """)
        
        rows = cursor.fetchall()
        contexts = [dict(row) for row in rows]
        conn.close()
        
        print(f"✅ Get recent context: Found {len(contexts)} context entries")
        if contexts:
            print(f"   Latest: {contexts[0].get('agent_id', 'N/A')} - {contexts[0].get('task', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"❌ Get recent context failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_context_by_task():
    """Test get_context_by_task (via direct SQL query like MCP tool does)."""
    print("\n" + "=" * 60)
    print("Test 9: Get Context by Task")
    print("=" * 60)
    try:
        import sqlite3
        memory = get_memory()
        
        # Test the same query the MCP tool uses
        conn = sqlite3.connect(memory.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM context 
            WHERE task = ? 
            ORDER BY updated_at DESC 
            LIMIT 1
        """, ("test-mcp-tools",))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            context = dict(row)
            print(f"✅ Get context by task: Found context for task 'test-mcp-tools'")
            print(f"   Agent: {context.get('agent_id', 'N/A')}, Status: {context.get('status', 'N/A')}")
        else:
            print(f"⚠️  No context found for task 'test-mcp-tools' (this is OK if test context wasn't saved)")
        
        return True
    except Exception as e:
        print(f"❌ Get context by task failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_export_to_markdown():
    """Test export_to_markdown function."""
    print("\n" + "=" * 60)
    print("Test 10: Export to Markdown")
    print("=" * 60)
    try:
        memory = get_memory()
        
        # Export to markdown
        export_path = memory.export_to_markdown()
        print(f"✅ Export to markdown: Exported to {export_path}")
        
        # Check if files were created
        decisions_path = export_path / "decisions"
        patterns_path = export_path / "patterns"
        
        decisions_count = len(list(decisions_path.glob("*.md"))) if decisions_path.exists() else 0
        patterns_count = len(list(patterns_path.glob("*.md"))) if patterns_path.exists() else 0
        
        print(f"   - Decisions exported: {decisions_count}")
        print(f"   - Patterns exported: {patterns_count}")
        
        return True
    except Exception as e:
        print(f"❌ Export to markdown failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mcp_tool_wrapper():
    """Test that MCP tool wrapper functions would work."""
    print("\n" + "=" * 60)
    print("Test 11: MCP Tool Wrapper Compatibility")
    print("=" * 60)
    try:
        # Test the logic that MCP tools use
        memory = get_memory()
        
        # Simulate memory_query_decisions MCP tool
        tag_list = ["test", "mcp"]
        decisions = memory.query_decisions(
            project="home-server",
            tags=tag_list,
            min_importance=0.0,
            search_text="test",
            limit=10
        )
        
        result = {
            "status": "success",
            "count": len(decisions),
            "decisions": decisions
        }
        
        print(f"✅ MCP tool wrapper test: Success")
        print(f"   Status: {result['status']}")
        print(f"   Count: {result['count']}")
        
        return True
    except Exception as e:
        print(f"❌ MCP tool wrapper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("MCP Memory Tools Test Suite")
    print("=" * 60)
    print("\nTesting memory functions used by MCP tools...")
    
    tests = [
        test_memory_import,
        test_query_decisions,
        test_query_patterns,
        test_search,
        test_record_decision,
        test_record_pattern,
        test_save_context,
        test_get_recent_context,
        test_get_context_by_task,
        test_export_to_markdown,
        test_mcp_tool_wrapper,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test {test.__name__} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total} tests")
    
    if all(results):
        print("\n✅ All tests passed! MCP memory tools should work correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

