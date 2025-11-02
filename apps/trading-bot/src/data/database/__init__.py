"""
Database Module
===============

Database connection and session management with metrics instrumentation.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from typing import Generator
import logging
import time

from ...config.settings import settings

logger = logging.getLogger(__name__)

# Database URL from settings
DATABASE_URL = settings.database.url

# Create engine with connection pool optimization
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
pool_args = {}

# Connection pool settings (only for non-SQLite databases)
if "sqlite" not in DATABASE_URL:
    pool_args = {
        "pool_size": 10,  # Number of connections to maintain
        "max_overflow": 20,  # Max connections beyond pool_size
        "pool_pre_ping": True,  # Verify connections before use
        "pool_recycle": 3600,  # Recycle connections after 1 hour
        "pool_timeout": 30,  # Timeout for getting connection from pool
    }

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=settings.database.echo,
    **pool_args
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import Base from models to ensure all models are registered
from .models import Base

# Instrument database queries with metrics if enabled
if settings.metrics.enabled:
    try:
        from ...utils.metrics_system import (
            record_database_query,
            update_connection_pool_usage,
            record_transaction
        )
        
        @event.listens_for(Engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Record query start time"""
            context._query_start_time = time.time()
        
        @event.listens_for(Engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Record query duration and count"""
            try:
                if hasattr(context, '_query_start_time'):
                    duration = time.time() - context._query_start_time
                    # Determine query type from statement
                    query_type = "unknown"
                    statement_upper = statement.upper().strip() if statement else ""
                    if statement_upper.startswith("SELECT"):
                        query_type = "select"
                    elif statement_upper.startswith("INSERT"):
                        query_type = "insert"
                    elif statement_upper.startswith("UPDATE"):
                        query_type = "update"
                    elif statement_upper.startswith("DELETE"):
                        query_type = "delete"
                    
                    record_database_query(query_type, duration)
            except Exception as e:
                logger.debug(f"Error recording database query metric: {e}")
        
        @event.listens_for(Session, "after_commit")
        def receive_after_commit(session):
            """Record committed transaction"""
            try:
                record_transaction("committed")
            except Exception as e:
                logger.debug(f"Error recording transaction metric: {e}")
        
        @event.listens_for(Session, "after_rollback")
        def receive_after_rollback(session):
            """Record rolled back transaction"""
            try:
                record_transaction("rolled_back")
            except Exception as e:
                logger.debug(f"Error recording transaction metric: {e}")
        
        logger.debug("Database metrics instrumentation enabled")
        
    except (ImportError, Exception) as e:
        logger.debug(f"Could not enable database metrics instrumentation: {e}")

def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
        # Update pool metrics after session use
        if settings.metrics.enabled:
            try:
                if hasattr(engine.pool, 'size') and hasattr(engine.pool, 'checkedout'):
                    pool_size = engine.pool.size()
                    checked_out = engine.pool.checkedout()
                    from ...utils.metrics_system import update_connection_pool_usage
                    update_connection_pool_usage("default", checked_out, pool_size)
            except Exception:
                pass  # Non-critical, skip if fails
    finally:
        db.close()

async def init_db():
    """Initialize database"""
    logger.info("Initializing database...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    logger.info("Database initialized successfully")