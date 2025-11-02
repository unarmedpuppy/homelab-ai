"""
Database Module
===============

Database connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from ..config.settings import settings

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

def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_db():
    """Initialize database"""
    logger.info("Initializing database...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    logger.info("Database initialized successfully")