"""
Database Configuration and Connection Management
===============================================

Database setup with SQLAlchemy and Alembic migrations.
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from contextlib import asynccontextmanager
import logging
from typing import Generator

from ..config.settings import settings

logger = logging.getLogger(__name__)

# Create base class for models
Base = declarative_base()

# Database engine
engine = None
SessionLocal = None

def init_database():
    """Initialize database connection"""
    global engine, SessionLocal
    
    try:
        # Create engine with appropriate settings
        if settings.database.url.startswith("sqlite"):
            engine = create_engine(
                settings.database.url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=settings.database.echo
            )
        else:
            engine = create_engine(
                settings.database.url,
                pool_size=settings.database.pool_size,
                max_overflow=settings.database.max_overflow,
                echo=settings.database.echo
            )
        
        # Create session factory
        SessionLocal = sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False
        )
        
        logger.info(f"Database initialized: {settings.database.url}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

def get_db_session():
    """Get database session"""
    if SessionLocal is None:
        init_database()
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@asynccontextmanager
async def get_async_db_session():
    """Get async database session"""
    if SessionLocal is None:
        init_database()
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all tables"""
    if engine is None:
        init_database()
    
    try:
        # Import all models to ensure they're registered
        from .models import *
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False

def drop_tables():
    """Drop all tables"""
    if engine is None:
        init_database()
    
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        return False

def get_engine():
    """Get database engine"""
    if engine is None:
        init_database()
    return engine

def get_session_local():
    """Get session factory"""
    if SessionLocal is None:
        init_database()
    return SessionLocal
