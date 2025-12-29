"""
RAG (Retrieval-Augmented Generation) module for conversation context injection.

Provides semantic search over conversation history using embeddings.
"""
import logging
import numpy as np
from typing import List, Optional, Tuple
from datetime import datetime, timezone

from database import get_db_connection
from memory import get_conversation_messages
from models import Message

logger = logging.getLogger(__name__)

# Simple in-memory embedding cache
_embedding_cache = {}


def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for text using a simple TF-IDF-like approach.

    For production, consider using:
    - sentence-transformers (local)
    - OpenAI embeddings API
    - Cohere embeddings API

    This simple implementation uses word frequency as a baseline.
    """
    # Check cache first
    if text in _embedding_cache:
        return _embedding_cache[text]

    # Simple bag-of-words embedding (300 dimensions)
    # This is a placeholder - use real embeddings in production
    words = text.lower().split()

    # Create a simple hash-based embedding
    embedding = [0.0] * 300
    for i, word in enumerate(words[:100]):  # Limit to 100 words
        # Hash word to dimension index
        hash_val = hash(word) % 300
        embedding[hash_val] += 1.0 / (i + 1)  # Position-weighted

    # Normalize
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = (np.array(embedding) / norm).tolist()

    # Cache result
    _embedding_cache[text] = embedding

    return embedding


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a_arr = np.array(a)
    b_arr = np.array(b)

    dot_product = np.dot(a_arr, b_arr)
    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(dot_product / (norm_a * norm_b))


def embed_message(message: Message) -> Optional[str]:
    """
    Generate and store embedding for a message.

    Returns the embedding as a JSON string (for SQLite storage).
    """
    if not message.content:
        return None

    try:
        embedding = generate_embedding(message.content)
        # Store as comma-separated string for SQLite
        return ",".join(str(x) for x in embedding)
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return None


def search_similar_conversations(
    query: str,
    limit: int = 5,
    similarity_threshold: float = 0.3,
    user_id: Optional[str] = None,
    project: Optional[str] = None,
) -> List[Tuple[str, float]]:
    """
    Search for conversations similar to the query.

    Returns list of (conversation_id, similarity_score) tuples.

    Note: This is a simple implementation. For production:
    - Use proper vector database (Qdrant, Weaviate, Pinecone)
    - Or use sqlite-vec extension for SQLite
    - Implement proper indexing for performance
    """
    query_embedding = generate_embedding(query)

    # Get all messages with content
    with get_db_connection() as conn:
        cursor = conn.cursor()

        sql = """
            SELECT DISTINCT m.conversation_id, m.content, c.user_id, c.project
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            WHERE m.content IS NOT NULL AND m.content != ''
        """
        params = []

        if user_id:
            sql += " AND c.user_id = ?"
            params.append(user_id)

        if project:
            sql += " AND c.project = ?"
            params.append(project)

        cursor.execute(sql, params)
        rows = cursor.fetchall()

    # Calculate similarities
    similarities = []
    for row in rows:
        conversation_id = row["conversation_id"]
        content = row["content"]

        # Generate embedding for this message
        message_embedding = generate_embedding(content)

        # Calculate similarity
        similarity = cosine_similarity(query_embedding, message_embedding)

        if similarity >= similarity_threshold:
            similarities.append((conversation_id, similarity))

    # Sort by similarity (descending) and deduplicate by conversation_id
    seen = set()
    unique_results = []
    for conv_id, score in sorted(similarities, key=lambda x: x[1], reverse=True):
        if conv_id not in seen:
            seen.add(conv_id)
            unique_results.append((conv_id, score))

    return unique_results[:limit]


def get_relevant_context(
    query: str,
    limit: int = 3,
    similarity_threshold: float = 0.3,
    user_id: Optional[str] = None,
    project: Optional[str] = None,
) -> List[dict]:
    """
    Get relevant conversation context for RAG.

    Returns list of context snippets with metadata.
    """
    similar_conversations = search_similar_conversations(
        query=query,
        limit=limit,
        similarity_threshold=similarity_threshold,
        user_id=user_id,
        project=project,
    )

    context = []
    for conversation_id, similarity_score in similar_conversations:
        # Get conversation messages
        messages = get_conversation_messages(conversation_id)

        # Format as context
        conversation_text = "\n".join(
            f"{msg.role}: {msg.content}"
            for msg in messages
            if msg.content
        )

        context.append({
            "conversation_id": conversation_id,
            "similarity_score": similarity_score,
            "text": conversation_text,
            "message_count": len(messages),
        })

    return context


def inject_context_into_messages(
    messages: List[dict],
    context: List[dict],
    max_context_tokens: int = 2000,
) -> List[dict]:
    """
    Inject RAG context into message history.

    Adds a system message with relevant context at the beginning.
    """
    if not context:
        return messages

    # Build context text
    context_parts = []
    for ctx in context:
        context_parts.append(
            f"[Relevant past conversation (similarity: {ctx['similarity_score']:.2f})]:\n{ctx['text']}\n"
        )

    context_text = "\n---\n".join(context_parts)

    # Rough token estimate (4 chars per token)
    estimated_tokens = len(context_text) // 4
    if estimated_tokens > max_context_tokens:
        # Truncate context
        target_chars = max_context_tokens * 4
        context_text = context_text[:target_chars] + "... [truncated]"

    # Create context message
    context_message = {
        "role": "system",
        "content": f"""You have access to relevant past conversations for context:

{context_text}

Use this context to provide more helpful and contextually aware responses."""
    }

    # Insert at beginning
    return [context_message] + messages


# ============================================================================
# Database Schema Extension for Embeddings (Future)
# ============================================================================

def init_embeddings_table():
    """
    Initialize embeddings table in database.

    Note: This is for future use. Currently embeddings are generated on-the-fly.
    For production, pre-compute and store embeddings for faster search.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_embeddings (
                message_id INTEGER PRIMARY KEY,
                embedding TEXT NOT NULL,  -- Comma-separated floats
                created_at DATETIME NOT NULL,
                FOREIGN KEY (message_id) REFERENCES messages(id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_message_id
            ON message_embeddings(message_id)
        """)

        conn.commit()

    logger.info("Embeddings table initialized")


if __name__ == "__main__":
    # Test RAG functionality
    logging.basicConfig(level=logging.INFO)

    # Test embedding generation
    text1 = "How do I deploy to production?"
    text2 = "What's the deployment process?"
    text3 = "How do I make pizza?"

    emb1 = generate_embedding(text1)
    emb2 = generate_embedding(text2)
    emb3 = generate_embedding(text3)

    sim_12 = cosine_similarity(emb1, emb2)
    sim_13 = cosine_similarity(emb1, emb3)

    print(f"Similarity (deploy/deployment): {sim_12:.3f}")
    print(f"Similarity (deploy/pizza): {sim_13:.3f}")

    # Test search
    results = search_similar_conversations("deployment")
    print(f"\nSearch results for 'deployment': {len(results)}")
    for conv_id, score in results:
        print(f"  {conv_id}: {score:.3f}")
