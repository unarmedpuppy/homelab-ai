#!/usr/bin/env python3
"""
Database Initialization Script
==============================

Script to initialize the database and create initial migration.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.data.database import init_database, create_tables
from src.config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_alembic():
    """Initialize Alembic if not already done"""
    migrations_dir = Path("migrations")
    if not migrations_dir.exists():
        logger.info("Initializing Alembic...")
        subprocess.run(["alembic", "init", "migrations"], check=True)
        logger.info("Alembic initialized")
    else:
        logger.info("Alembic already initialized")

def create_initial_migration():
    """Create initial migration"""
    logger.info("Creating initial migration...")
    try:
        subprocess.run([
            "alembic", "revision", 
            "--autogenerate", 
            "-m", "Initial migration"
        ], check=True)
        logger.info("Initial migration created")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create migration: {e}")
        return False
    return True

def run_migrations():
    """Run database migrations"""
    logger.info("Running migrations...")
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        logger.info("Migrations completed")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run migrations: {e}")
        return False
    return True

def main():
    """Main initialization function"""
    logger.info("Starting database initialization...")
    
    # Initialize database connection
    if not init_database():
        logger.error("Failed to initialize database")
        return False
    
    # Initialize Alembic
    init_alembic()
    
    # Create initial migration
    if not create_initial_migration():
        logger.error("Failed to create initial migration")
        return False
    
    # Run migrations
    if not run_migrations():
        logger.error("Failed to run migrations")
        return False
    
    logger.info("Database initialization completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
