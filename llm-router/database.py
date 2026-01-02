"""
Database initialization and connection management for memory and metrics storage.
"""
import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Optional
import os

logger = logging.getLogger(__name__)

DATABASE_PATH = os.getenv("DATABASE_PATH", "/data/local-ai-router.db")


def get_db_path() -> Path:
    """Get the database file path, creating parent directory if needed."""
    db_path = Path(DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


@contextmanager
def get_db_connection():
    """Context manager for database connections with WAL mode."""
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Enable dict-like access

    # Enable WAL mode for better concurrent access
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")

    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """Initialize database schema if it doesn't exist."""
    db_path = get_db_path()

    if db_path.exists():
        logger.info(f"Database already exists at {db_path}, ensuring schema is up to date")
    else:
        logger.info(f"Initializing new database at {db_path}")

    # Always run schema creation - CREATE TABLE IF NOT EXISTS is idempotent

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Create conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                session_id TEXT,
                user_id TEXT,
                project TEXT,
                title TEXT,
                username TEXT,
                source TEXT,
                display_name TEXT,
                metadata TEXT,
                message_count INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0
            )
        """)

        # Create messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                role TEXT NOT NULL,
                content TEXT,
                model_used TEXT,
                backend TEXT,
                tokens_prompt INTEGER,
                tokens_completion INTEGER,
                tool_calls TEXT,
                tool_results TEXT,
                image_refs TEXT,
                metadata TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)

        # Migration: Add image_refs column if it doesn't exist (for existing databases)
        try:
            cursor.execute("SELECT image_refs FROM messages LIMIT 1")
        except sqlite3.OperationalError:
            logger.info("Migrating: Adding image_refs column to messages table")
            cursor.execute("ALTER TABLE messages ADD COLUMN image_refs TEXT")

        # Migration: Add cost_usd column to metrics table
        try:
            cursor.execute("SELECT cost_usd FROM metrics LIMIT 1")
        except sqlite3.OperationalError:
            logger.info("Migrating: Adding cost_usd column to metrics table")
            cursor.execute("ALTER TABLE metrics ADD COLUMN cost_usd REAL")

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation
            ON messages(conversation_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_timestamp
            ON messages(timestamp)
        """)

        # Create metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                date DATE NOT NULL,
                conversation_id TEXT,
                session_id TEXT,
                endpoint TEXT,
                model_requested TEXT,
                model_used TEXT,
                backend TEXT,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                duration_ms INTEGER,
                success BOOLEAN,
                error TEXT,
                streaming BOOLEAN,
                tool_calls_count INTEGER,
                user_id TEXT,
                project TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_date
            ON metrics(date)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_timestamp
            ON metrics(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_backend
            ON metrics(backend)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_user_project
            ON metrics(user_id, project)
        """)

        # Create daily_stats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                date DATE PRIMARY KEY,
                total_requests INTEGER,
                total_messages INTEGER,
                total_tokens INTEGER,
                unique_conversations INTEGER,
                unique_sessions INTEGER,
                models_used TEXT,
                backends_used TEXT,
                avg_duration_ms REAL,
                success_rate REAL,
                updated_at DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS client_api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_hash TEXT NOT NULL UNIQUE,
                key_prefix TEXT NOT NULL,
                name TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                last_used_at DATETIME,
                expires_at DATETIME,
                enabled BOOLEAN NOT NULL DEFAULT 1,
                scopes TEXT,
                metadata TEXT
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_client_api_keys_hash
            ON client_api_keys(key_hash)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_client_api_keys_enabled
            ON client_api_keys(enabled)
        """)

        # Create agent_runs table for tracking agent executions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_runs (
                id TEXT PRIMARY KEY,
                task TEXT NOT NULL,
                working_directory TEXT,
                model_requested TEXT,
                model_used TEXT,
                backend TEXT,
                status TEXT NOT NULL,
                final_answer TEXT,
                total_steps INTEGER DEFAULT 0,
                started_at DATETIME NOT NULL,
                completed_at DATETIME,
                duration_ms INTEGER,
                source TEXT,
                triggered_by TEXT,
                error TEXT,
                metadata TEXT
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_runs_status
            ON agent_runs(status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_runs_started
            ON agent_runs(started_at)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_runs_source
            ON agent_runs(source)
        """)

        # Create agent_steps table for tracking individual steps
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_run_id TEXT NOT NULL,
                step_number INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                tool_name TEXT,
                tool_args TEXT,
                tool_result TEXT,
                thinking TEXT,
                error TEXT,
                started_at DATETIME NOT NULL,
                duration_ms INTEGER,
                FOREIGN KEY (agent_run_id) REFERENCES agent_runs(id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_steps_run
            ON agent_steps(agent_run_id)
        """)

        # Migration: Add token columns to agent_steps table
        try:
            cursor.execute("SELECT prompt_tokens FROM agent_steps LIMIT 1")
        except sqlite3.OperationalError:
            logger.info("Migrating: Adding token columns to agent_steps table")
            cursor.execute("ALTER TABLE agent_steps ADD COLUMN prompt_tokens INTEGER")
            cursor.execute("ALTER TABLE agent_steps ADD COLUMN completion_tokens INTEGER")

        conn.commit()
        logger.info("Database schema created successfully")


def check_database_health() -> dict:
    """Check database health and return stats."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get table counts
            cursor.execute("SELECT COUNT(*) FROM conversations")
            conversation_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM messages")
            message_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM metrics")
            metrics_count = cursor.fetchone()[0]

            # Get database file size
            db_path = get_db_path()
            db_size_mb = db_path.stat().st_size / (1024 * 1024) if db_path.exists() else 0

            return {
                "status": "healthy",
                "database_path": str(db_path),
                "database_size_mb": round(db_size_mb, 2),
                "conversations": conversation_count,
                "messages": message_count,
                "metrics": metrics_count,
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


if __name__ == "__main__":
    # Initialize database when run directly
    logging.basicConfig(level=logging.INFO)
    init_database()
    print("Database initialized!")
    print(check_database_health())
