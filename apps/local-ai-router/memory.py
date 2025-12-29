"""
Memory module for conversation storage and retrieval.
Handles long-term agent memory with full conversation history.
"""
import logging
import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import uuid4

from database import get_db_connection
from models import (
    Conversation,
    ConversationCreate,
    ConversationUpdate,
    Message,
    MessageCreate,
    ConversationSearchResult,
    SearchQuery,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Conversation Operations
# ============================================================================

def create_conversation(conv: ConversationCreate) -> Conversation:
    """Create a new conversation."""
    now = datetime.now(timezone.utc)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO conversations
            (id, created_at, updated_at, session_id, user_id, project, title, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conv.id,
                now,
                now,
                conv.session_id,
                conv.user_id,
                conv.project,
                conv.title,
                json.dumps(conv.metadata) if conv.metadata else None,
            ),
        )
        conn.commit()

    logger.info(f"Created conversation {conv.id}")
    return get_conversation(conv.id)


def get_conversation(conversation_id: str) -> Optional[Conversation]:
    """Get a conversation by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        row = cursor.fetchone()

    if not row:
        return None

    return _row_to_conversation(row)


def update_conversation(
    conversation_id: str,
    update: ConversationUpdate
) -> Optional[Conversation]:
    """Update a conversation."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Build update query dynamically
        updates = []
        params = []

        if update.title is not None:
            updates.append("title = ?")
            params.append(update.title)

        if update.metadata is not None:
            updates.append("metadata = ?")
            params.append(json.dumps(update.metadata))

        if not updates:
            return get_conversation(conversation_id)

        updates.append("updated_at = ?")
        params.append(datetime.now(timezone.utc))
        params.append(conversation_id)

        cursor.execute(
            f"UPDATE conversations SET {', '.join(updates)} WHERE id = ?",
            params
        )
        conn.commit()

    logger.info(f"Updated conversation {conversation_id}")
    return get_conversation(conversation_id)


def delete_conversation(conversation_id: str) -> bool:
    """Delete a conversation and all its messages."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Delete messages first (foreign key constraint)
        cursor.execute(
            "DELETE FROM messages WHERE conversation_id = ?",
            (conversation_id,)
        )

        # Delete conversation
        cursor.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,)
        )

        deleted = cursor.rowcount > 0
        conn.commit()

    if deleted:
        logger.info(f"Deleted conversation {conversation_id}")
    return deleted


def list_conversations(
    user_id: Optional[str] = None,
    project: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Conversation]:
    """List conversations with optional filters."""
    query = "SELECT * FROM conversations WHERE 1=1"
    params = []

    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)

    if project:
        query += " AND project = ?"
        params.append(project)

    if session_id:
        query += " AND session_id = ?"
        params.append(session_id)

    query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    return [_row_to_conversation(row) for row in rows]


# ============================================================================
# Message Operations
# ============================================================================

def add_message(msg: MessageCreate) -> Message:
    """Add a message to a conversation."""
    now = datetime.now(timezone.utc)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Insert message
        cursor.execute(
            """
            INSERT INTO messages
            (conversation_id, timestamp, role, content, model_used, backend,
             tokens_prompt, tokens_completion, tool_calls, tool_results, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                msg.conversation_id,
                now,
                msg.role.value,
                msg.content,
                msg.model_used,
                msg.backend,
                msg.tokens_prompt,
                msg.tokens_completion,
                json.dumps(msg.tool_calls) if msg.tool_calls else None,
                json.dumps(msg.tool_results) if msg.tool_results else None,
                json.dumps(msg.metadata) if msg.metadata else None,
            ),
        )

        message_id = cursor.lastrowid

        # Update conversation stats
        total_tokens = (msg.tokens_prompt or 0) + (msg.tokens_completion or 0)
        cursor.execute(
            """
            UPDATE conversations
            SET message_count = message_count + 1,
                total_tokens = total_tokens + ?,
                updated_at = ?
            WHERE id = ?
            """,
            (total_tokens, now, msg.conversation_id)
        )

        conn.commit()

    logger.debug(f"Added message to conversation {msg.conversation_id}")
    return get_message(message_id)


def get_message(message_id: int) -> Optional[Message]:
    """Get a message by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM messages WHERE id = ?",
            (message_id,)
        )
        row = cursor.fetchone()

    if not row:
        return None

    return _row_to_message(row)


def get_conversation_messages(
    conversation_id: str,
    limit: Optional[int] = None,
    offset: int = 0,
) -> List[Message]:
    """Get all messages in a conversation."""
    query = """
        SELECT * FROM messages
        WHERE conversation_id = ?
        ORDER BY timestamp ASC
    """
    params = [conversation_id]

    if limit:
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    return [_row_to_message(row) for row in rows]


def delete_message(message_id: int) -> bool:
    """Delete a message."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM messages WHERE id = ?",
            (message_id,)
        )
        deleted = cursor.rowcount > 0
        conn.commit()

    return deleted


# ============================================================================
# Search Operations
# ============================================================================

def search_conversations(query: SearchQuery) -> List[ConversationSearchResult]:
    """
    Search conversations by content.

    Note: This is a simple text search. For production, consider:
    - Full-text search (FTS5)
    - Embedding-based semantic search
    - Vector database integration
    """
    sql = """
        SELECT DISTINCT c.*, COUNT(m.id) as match_count
        FROM conversations c
        JOIN messages m ON c.id = m.conversation_id
        WHERE m.content LIKE ?
    """
    params = [f"%{query.q}%"]

    if query.user_id:
        sql += " AND c.user_id = ?"
        params.append(query.user_id)

    if query.project:
        sql += " AND c.project = ?"
        params.append(query.project)

    if query.start_date:
        sql += " AND c.created_at >= ?"
        params.append(query.start_date)

    if query.end_date:
        sql += " AND c.created_at <= ?"
        params.append(query.end_date)

    sql += """
        GROUP BY c.id
        ORDER BY match_count DESC, c.updated_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([query.limit, query.offset])

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    results = []
    for row in rows:
        conv = _row_to_conversation(row)
        messages = get_conversation_messages(conv.id)

        # Simple relevance scoring based on match count
        match_count = row["match_count"]
        relevance = min(1.0, match_count / 10.0)  # Normalize to 0-1

        results.append(
            ConversationSearchResult(
                conversation=conv,
                messages=messages,
                relevance_score=relevance,
            )
        )

    return results


def search_by_metadata(
    user_id: Optional[str] = None,
    project: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 50,
) -> List[Conversation]:
    """
    Search conversations by metadata.

    Note: This uses JSON LIKE queries which aren't ideal for performance.
    For production, consider extracting common metadata to columns.
    """
    query = "SELECT * FROM conversations WHERE 1=1"
    params = []

    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)

    if project:
        query += " AND project = ?"
        params.append(project)

    if tags:
        # Search for tags in metadata JSON
        # This is simplified - production should use proper JSON queries
        for tag in tags:
            query += " AND metadata LIKE ?"
            params.append(f'%"{tag}"%')

    query += " ORDER BY updated_at DESC LIMIT ?"
    params.append(limit)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    return [_row_to_conversation(row) for row in rows]


# ============================================================================
# Helper Functions
# ============================================================================

def _row_to_conversation(row: Any) -> Conversation:
    """Convert database row to Conversation model."""
    return Conversation(
        id=row["id"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        session_id=row["session_id"],
        user_id=row["user_id"],
        project=row["project"],
        title=row["title"],
        metadata=json.loads(row["metadata"]) if row["metadata"] else None,
        message_count=row["message_count"],
        total_tokens=row["total_tokens"],
    )


def _row_to_message(row: Any) -> Message:
    """Convert database row to Message model."""
    return Message(
        id=row["id"],
        conversation_id=row["conversation_id"],
        timestamp=datetime.fromisoformat(row["timestamp"]),
        role=row["role"],
        content=row["content"],
        model_used=row["model_used"],
        backend=row["backend"],
        tokens_prompt=row["tokens_prompt"],
        tokens_completion=row["tokens_completion"],
        tool_calls=json.loads(row["tool_calls"]) if row["tool_calls"] else None,
        tool_results=json.loads(row["tool_results"]) if row["tool_results"] else None,
        metadata=json.loads(row["metadata"]) if row["metadata"] else None,
    )


def generate_conversation_id() -> str:
    """Generate a unique conversation ID."""
    return f"conv-{uuid4().hex[:12]}"


# ============================================================================
# Utility Functions
# ============================================================================

def get_conversation_stats() -> Dict[str, Any]:
    """Get overall conversation statistics."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM conversations")
        total_conversations = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM messages")
        total_messages = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(total_tokens) FROM conversations")
        total_tokens = cursor.fetchone()[0] or 0

        cursor.execute(
            """
            SELECT COUNT(DISTINCT user_id) FROM conversations
            WHERE user_id IS NOT NULL
            """
        )
        unique_users = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(DISTINCT project) FROM conversations
            WHERE project IS NOT NULL
            """
        )
        unique_projects = cursor.fetchone()[0]

    return {
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "total_tokens": total_tokens,
        "unique_users": unique_users,
        "unique_projects": unique_projects,
    }


if __name__ == "__main__":
    # Test the memory module
    logging.basicConfig(level=logging.INFO)

    # Create test conversation
    conv_id = generate_conversation_id()
    conv = create_conversation(
        ConversationCreate(
            id=conv_id,
            user_id="test_user",
            project="test_project",
            title="Test Conversation",
        )
    )
    print(f"Created conversation: {conv.id}")

    # Add messages
    add_message(
        MessageCreate(
            conversation_id=conv_id,
            role="user",
            content="Hello!",
            tokens_prompt=5,
        )
    )
    add_message(
        MessageCreate(
            conversation_id=conv_id,
            role="assistant",
            content="Hi there!",
            model_used="3090",
            backend="3090",
            tokens_completion=10,
        )
    )

    # Retrieve messages
    messages = get_conversation_messages(conv_id)
    print(f"Messages in conversation: {len(messages)}")
    for msg in messages:
        print(f"  [{msg.role}] {msg.content}")

    # Get stats
    stats = get_conversation_stats()
    print(f"\nStats: {stats}")

    # Clean up
    delete_conversation(conv_id)
    print(f"\nDeleted test conversation")
