"""
Test script for Phase 2.2 - Conversation metadata tracking

Tests that username, source, and display_name are properly tracked
from request headers and stored in conversations.
"""
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Set database path before importing modules
os.environ["DATABASE_PATH"] = str(Path(__file__).parent / "test_metadata.db")

from models import ConversationCreate
from memory import create_conversation, get_conversation, delete_conversation, generate_conversation_id
from database import init_database


def test_conversation_metadata_tracking():
    """Test that new metadata fields are stored and retrieved correctly."""
    print("=== Testing Phase 2.2: Conversation Metadata Tracking ===\n")

    # Initialize database
    print("Initializing database...")
    init_database()
    print("✅ Database initialized\n")

    # Test 1: Create conversation with all metadata
    print("--- Test 1: Create conversation with metadata ---")
    conv_id = generate_conversation_id()

    conv = create_conversation(
        ConversationCreate(
            id=conv_id,
            user_id="test_user",
            session_id="test_session",
            project="test_project",
            title="Test Conversation",
            username="josh",
            source="claude-code",
            display_name="Joshua Jenquist",
        )
    )

    print(f"✅ Created conversation: {conv_id}")
    print(f"   Username: {conv.username}")
    print(f"   Source: {conv.source}")
    print(f"   Display Name: {conv.display_name}")
    print()

    # Test 2: Retrieve conversation and verify metadata
    print("--- Test 2: Retrieve conversation ---")
    retrieved = get_conversation(conv_id)

    if not retrieved:
        print(f"❌ Failed to retrieve conversation {conv_id}")
        return False

    assert retrieved.username == "josh", f"Username mismatch: {retrieved.username}"
    assert retrieved.source == "claude-code", f"Source mismatch: {retrieved.source}"
    assert retrieved.display_name == "Joshua Jenquist", f"Display name mismatch: {retrieved.display_name}"

    print(f"✅ Retrieved conversation with correct metadata:")
    print(f"   Username: {retrieved.username}")
    print(f"   Source: {retrieved.source}")
    print(f"   Display Name: {retrieved.display_name}")
    print()

    # Test 3: Create conversation with partial metadata (None values)
    print("--- Test 3: Create conversation with partial metadata ---")
    conv_id2 = generate_conversation_id()

    conv2 = create_conversation(
        ConversationCreate(
            id=conv_id2,
            user_id="test_user2",
            username="bob",
            # source and display_name intentionally omitted (None)
        )
    )

    print(f"✅ Created conversation: {conv_id2}")
    print(f"   Username: {conv2.username}")
    print(f"   Source: {conv2.source}")
    print(f"   Display Name: {conv2.display_name}")

    assert conv2.username == "bob", f"Username mismatch: {conv2.username}"
    assert conv2.source is None, f"Source should be None: {conv2.source}"
    assert conv2.display_name is None, f"Display name should be None: {conv2.display_name}"
    print()

    # Test 4: Create conversation with no metadata
    print("--- Test 4: Create conversation with no metadata ---")
    conv_id3 = generate_conversation_id()

    conv3 = create_conversation(
        ConversationCreate(
            id=conv_id3,
            user_id="test_user3",
        )
    )

    print(f"✅ Created conversation: {conv_id3}")
    print(f"   Username: {conv3.username}")
    print(f"   Source: {conv3.source}")
    print(f"   Display Name: {conv3.display_name}")

    assert conv3.username is None, f"Username should be None: {conv3.username}"
    assert conv3.source is None, f"Source should be None: {conv3.source}"
    assert conv3.display_name is None, f"Display name should be None: {conv3.display_name}"
    print()

    # Cleanup
    print("--- Cleanup ---")
    delete_conversation(conv_id)
    delete_conversation(conv_id2)
    delete_conversation(conv_id3)
    print("✅ Cleaned up test conversations\n")

    print("=== All Tests Passed ✅ ===")
    return True


if __name__ == "__main__":
    try:
        success = test_conversation_metadata_tracking()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
