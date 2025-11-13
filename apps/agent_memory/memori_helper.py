"""
Memori Helper - Setup and configuration for agent memory

Memori automatically:
- Injects context before LLM calls
- Records all conversations
- Learns patterns in background
"""

import os
from typing import Optional
from memori import Memori, ConfigManager


def get_memori_instance(
    database_connect: Optional[str] = None,
    conscious_ingest: bool = True,
    auto_ingest: bool = True,
    openai_api_key: Optional[str] = None,
) -> Memori:
    """
    Get configured Memori instance.
    
    Args:
        database_connect: Database connection string (defaults to env var)
        conscious_ingest: Enable short-term working memory (default: True)
        auto_ingest: Enable dynamic search per query (default: True)
        openai_api_key: OpenAI API key (defaults to env var)
    
    Returns:
        Configured Memori instance (already enabled)
    
    Environment Variables:
        MEMORI_DATABASE__CONNECTION_STRING: Database connection string
        MEMORI_AGENTS__OPENAI_API_KEY: OpenAI API key
        MEMORI_MEMORY__NAMESPACE: Memory namespace (default: "home-server")
    """
    # Use ConfigManager for automatic environment variable loading
    config = ConfigManager()
    config.auto_load()
    
    # Get database connection from parameter or environment
    db_connect = database_connect or os.getenv(
        "MEMORI_DATABASE__CONNECTION_STRING",
        "sqlite:///./agent_memory.db"  # Default to SQLite in current directory
    )
    
    # Get API key from parameter or environment
    api_key = openai_api_key or os.getenv("MEMORI_AGENTS__OPENAI_API_KEY")
    
    # Create Memori instance
    memori = Memori(
        database_connect=db_connect,
        conscious_ingest=conscious_ingest,
        auto_ingest=auto_ingest,
        openai_api_key=api_key,
    )
    
    # Enable memory (this activates automatic interception)
    memori.enable()
    
    return memori


def setup_memori(
    namespace: str = "home-server",
    database_connect: Optional[str] = None,
) -> Memori:
    """
    Setup Memori with home-server defaults.
    
    Args:
        namespace: Memory namespace (default: "home-server")
        database_connect: Database connection string
    
    Returns:
        Configured and enabled Memori instance
    """
    # Set namespace in environment if not already set
    if not os.getenv("MEMORI_MEMORY__NAMESPACE"):
        os.environ["MEMORI_MEMORY__NAMESPACE"] = namespace
    
    return get_memori_instance(database_connect=database_connect)


# Global instance (lazy initialization)
_memori_instance: Optional[Memori] = None


def get_global_memori() -> Memori:
    """
    Get global Memori instance (singleton pattern).
    
    Returns:
        Global Memori instance
    """
    global _memori_instance
    if _memori_instance is None:
        _memori_instance = setup_memori()
    return _memori_instance

