"""
API key authentication for Local AI Router.

This module handles generation, storage, and validation of client API keys.
Keys are stored as SHA-256 hashes - the full key is never stored after generation.
"""
import hashlib
import json
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple, List

from database import get_db_connection

logger = logging.getLogger(__name__)


@dataclass
class ApiKey:
    """Represents a validated API key with its metadata."""
    id: int
    name: str
    key_prefix: str
    enabled: bool
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    scopes: Optional[List[str]]
    metadata: Optional[dict]


def generate_api_key() -> Tuple[str, str, str]:
    """
    Generate a new API key.
    
    Returns:
        Tuple of (full_key, key_hash, key_prefix)
        - full_key: The complete key to give to the user (e.g., "lai_5f4d3c2b1a9e8d7c6b5a4e3d2c1b0a9f")
        - key_hash: SHA-256 hash for storage (64 hex chars)
        - key_prefix: First 8 chars for display (e.g., "lai_5f4d")
    """
    # Generate 16 random bytes = 32 hex chars
    random_part = secrets.token_hex(16)
    full_key = f"lai_{random_part}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    key_prefix = full_key[:8]  # "lai_5f4d"
    
    return full_key, key_hash, key_prefix


def hash_api_key(key: str) -> str:
    """Hash an API key for lookup."""
    return hashlib.sha256(key.encode()).hexdigest()


async def validate_api_key(key: str) -> Optional[ApiKey]:
    """
    Validate an API key and return its metadata if valid.
    
    Args:
        key: The full API key to validate
        
    Returns:
        ApiKey object if valid and enabled, None otherwise
    """
    if not key or not key.startswith("lai_"):
        return None
    
    key_hash = hash_api_key(key)
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Look up the key by hash
            cursor.execute("""
                SELECT id, name, key_prefix, enabled, created_at, 
                       last_used_at, expires_at, scopes, metadata
                FROM client_api_keys
                WHERE key_hash = ?
            """, (key_hash,))
            
            row = cursor.fetchone()
            if not row:
                logger.debug(f"API key not found: {key[:8]}...")
                return None
            
            # Check if key is enabled
            if not row['enabled']:
                logger.warning(f"API key is disabled: {row['name']} ({row['key_prefix']}...)")
                return None
            
            # Check if key has expired
            expires_at = None
            if row['expires_at']:
                expires_at = datetime.fromisoformat(row['expires_at']) if isinstance(row['expires_at'], str) else row['expires_at']
                if expires_at < datetime.utcnow():
                    logger.warning(f"API key has expired: {row['name']} ({row['key_prefix']}...)")
                    return None
            
            # Update last_used_at
            cursor.execute("""
                UPDATE client_api_keys
                SET last_used_at = ?
                WHERE id = ?
            """, (datetime.utcnow().isoformat(), row['id']))
            conn.commit()
            
            # Parse JSON fields
            scopes = json.loads(row['scopes']) if row['scopes'] else None
            metadata = json.loads(row['metadata']) if row['metadata'] else None
            
            # Parse datetime fields
            created_at = datetime.fromisoformat(row['created_at']) if isinstance(row['created_at'], str) else row['created_at']
            last_used_at = None
            if row['last_used_at']:
                last_used_at = datetime.fromisoformat(row['last_used_at']) if isinstance(row['last_used_at'], str) else row['last_used_at']
            
            logger.debug(f"API key validated: {row['name']} ({row['key_prefix']}...)")
            
            return ApiKey(
                id=row['id'],
                name=row['name'],
                key_prefix=row['key_prefix'],
                enabled=bool(row['enabled']),
                created_at=created_at,
                last_used_at=last_used_at,
                expires_at=expires_at,
                scopes=scopes,
                metadata=metadata
            )
            
    except Exception as e:
        logger.error(f"Error validating API key: {e}")
        return None


def create_api_key(
    name: str,
    scopes: Optional[List[str]] = None,
    expires_at: Optional[datetime] = None,
    metadata: Optional[dict] = None
) -> Tuple[str, int]:
    """
    Create a new API key and store it in the database.
    
    Args:
        name: Human-readable name for the key (e.g., "agent-1", "opencode")
        scopes: Optional list of allowed scopes (e.g., ["chat", "agent"])
        expires_at: Optional expiration datetime
        metadata: Optional additional metadata dict
        
    Returns:
        Tuple of (full_key, key_id)
        
    Note:
        The full_key is only returned once at creation time.
        Store it securely - it cannot be retrieved later.
    """
    full_key, key_hash, key_prefix = generate_api_key()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO client_api_keys 
            (key_hash, key_prefix, name, created_at, expires_at, enabled, scopes, metadata)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?)
        """, (
            key_hash,
            key_prefix,
            name,
            datetime.utcnow().isoformat(),
            expires_at.isoformat() if expires_at else None,
            json.dumps(scopes) if scopes else None,
            json.dumps(metadata) if metadata else None
        ))
        
        conn.commit()
        
        key_id = cursor.lastrowid
        if key_id is None:
            raise RuntimeError("Failed to get lastrowid after INSERT")
        
        logger.info(f"Created API key: {name} ({key_prefix}...) with id={key_id}")
        
        return full_key, key_id


def list_api_keys(include_disabled: bool = False) -> List[dict]:
    """
    List all API keys (without the actual key values).
    
    Args:
        include_disabled: Whether to include disabled keys
        
    Returns:
        List of key metadata dicts
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if include_disabled:
            cursor.execute("""
                SELECT id, name, key_prefix, enabled, created_at, 
                       last_used_at, expires_at, scopes, metadata
                FROM client_api_keys
                ORDER BY created_at DESC
            """)
        else:
            cursor.execute("""
                SELECT id, name, key_prefix, enabled, created_at, 
                       last_used_at, expires_at, scopes, metadata
                FROM client_api_keys
                WHERE enabled = 1
                ORDER BY created_at DESC
            """)
        
        rows = cursor.fetchall()
        
        keys = []
        for row in rows:
            keys.append({
                'id': row['id'],
                'name': row['name'],
                'key_prefix': row['key_prefix'],
                'enabled': bool(row['enabled']),
                'created_at': row['created_at'],
                'last_used_at': row['last_used_at'],
                'expires_at': row['expires_at'],
                'scopes': json.loads(row['scopes']) if row['scopes'] else None,
                'metadata': json.loads(row['metadata']) if row['metadata'] else None
            })
        
        return keys


def disable_api_key(key_id: int) -> bool:
    """
    Disable an API key by ID.
    
    Returns:
        True if key was disabled, False if key not found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE client_api_keys
            SET enabled = 0
            WHERE id = ?
        """, (key_id,))
        
        if cursor.rowcount == 0:
            return False
        
        conn.commit()
        logger.info(f"Disabled API key id={key_id}")
        return True


def enable_api_key(key_id: int) -> bool:
    """
    Enable an API key by ID.
    
    Returns:
        True if key was enabled, False if key not found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE client_api_keys
            SET enabled = 1
            WHERE id = ?
        """, (key_id,))
        
        if cursor.rowcount == 0:
            return False
        
        conn.commit()
        logger.info(f"Enabled API key id={key_id}")
        return True


def delete_api_key(key_id: int) -> bool:
    """
    Permanently delete an API key by ID.
    
    Returns:
        True if key was deleted, False if key not found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM client_api_keys
            WHERE id = ?
        """, (key_id,))
        
        if cursor.rowcount == 0:
            return False
        
        conn.commit()
        logger.info(f"Deleted API key id={key_id}")
        return True


def get_api_key_by_id(key_id: int) -> Optional[dict]:
    """
    Get API key metadata by ID.
    
    Returns:
        Key metadata dict or None if not found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, key_prefix, enabled, created_at, 
                   last_used_at, expires_at, scopes, metadata
            FROM client_api_keys
            WHERE id = ?
        """, (key_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            'id': row['id'],
            'name': row['name'],
            'key_prefix': row['key_prefix'],
            'enabled': bool(row['enabled']),
            'created_at': row['created_at'],
            'last_used_at': row['last_used_at'],
            'expires_at': row['expires_at'],
            'scopes': json.loads(row['scopes']) if row['scopes'] else None,
            'metadata': json.loads(row['metadata']) if row['metadata'] else None
        }
