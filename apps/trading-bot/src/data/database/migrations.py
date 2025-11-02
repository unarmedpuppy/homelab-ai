"""
Database Migration Utilities
=============================

Utilities for managing database schema migrations and versioning.
"""

import logging
from typing import Optional
from datetime import datetime
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from . import engine, SessionLocal, Base
from .models import (
    Tweet, TweetSentiment, SymbolSentiment, Influencer,
    RedditPost, RedditSentiment,
    AggregatedSentiment, ConfluenceScore,
    CashAccountState, DayTrade, SettlementTracking, TradeFrequencyTracking
)

logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Manages database schema migrations
    """
    
    def __init__(self):
        """Initialize migration manager"""
        self.engine = engine
    
    def create_all_tables(self):
        """Create all tables if they don't exist"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("All database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}", exc_info=True)
            raise
    
    def drop_all_tables(self):
        """Drop all tables (WARNING: Destructive!)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
        except Exception as e:
            logger.error(f"Error dropping tables: {e}", exc_info=True)
            raise
    
    def get_table_info(self) -> dict:
        """
        Get information about existing tables
        
        Returns:
            Dictionary with table names and column information
        """
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()
        
        info = {}
        for table_name in tables:
            columns = inspector.get_columns(table_name)
            indexes = inspector.get_indexes(table_name)
            foreign_keys = inspector.get_foreign_keys(table_name)
            
            info[table_name] = {
                'columns': [col['name'] for col in columns],
                'indexes': [idx['name'] for idx in indexes],
                'foreign_keys': [fk['name'] for fk in foreign_keys] if foreign_keys else []
            }
        
        return info
    
    def check_missing_tables(self) -> list:
        """
        Check for missing tables based on models
        
        Returns:
            List of table names that should exist but don't
        """
        inspector = inspect(self.engine)
        existing_tables = set(inspector.get_table_names())
        
        # Expected tables from models
        expected_tables = {
            'tweets',
            'tweet_sentiments',
            'symbol_sentiments',
            'influencers',
            'reddit_posts',
            'reddit_sentiments',
            'aggregated_sentiments',
            'confluence_scores'
        }
        
        missing = expected_tables - existing_tables
        return list(missing)
    
    def check_missing_indexes(self) -> dict:
        """
        Check for missing indexes
        
        Returns:
            Dictionary mapping table names to missing index names
        """
        inspector = inspect(self.engine)
        missing_indexes = {}
        
        # Expected indexes by table
        expected_indexes = {
            'tweets': ['ix_tweets_symbol_created_at', 'ix_tweets_author_username'],
            'tweet_sentiments': ['ix_tweet_sentiments_symbol_timestamp'],
            'symbol_sentiments': ['ix_symbol_sentiments_symbol_timestamp'],
            'aggregated_sentiments': ['ix_aggregated_sentiments_symbol_timestamp'],
            'confluence_scores': ['ix_confluence_scores_symbol_timestamp']
        }
        
        for table_name, expected in expected_indexes.items():
            if table_name not in inspector.get_table_names():
                continue
            
            existing_indexes = {idx['name'] for idx in inspector.get_indexes(table_name)}
            missing = set(expected) - existing_indexes
            if missing:
                missing_indexes[table_name] = list(missing)
        
        return missing_indexes
    
    def verify_schema(self) -> dict:
        """
        Verify database schema matches models
        
        Returns:
            Dictionary with verification results
        """
        result = {
            'valid': True,
            'missing_tables': [],
            'missing_indexes': {},
            'warnings': []
        }
        
        missing_tables = self.check_missing_tables()
        if missing_tables:
            result['valid'] = False
            result['missing_tables'] = missing_tables
        
        missing_indexes = self.check_missing_indexes()
        if missing_indexes:
            result['warnings'].append("Some indexes are missing - performance may be degraded")
            result['missing_indexes'] = missing_indexes
        
        return result
    
    def get_schema_version(self, db: Optional[Session] = None) -> Optional[str]:
        """
        Get current schema version
        
        Returns:
            Schema version string or None
        """
        if db is None:
            db = SessionLocal()
        
        try:
            # Check if schema_version table exists
            inspector = inspect(self.engine)
            if 'schema_version' not in inspector.get_table_names():
                return None
            
            result = db.execute(text("SELECT version FROM schema_version ORDER BY created_at DESC LIMIT 1"))
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.debug(f"Error getting schema version: {e}")
            return None
        finally:
            if db:
                db.close()

