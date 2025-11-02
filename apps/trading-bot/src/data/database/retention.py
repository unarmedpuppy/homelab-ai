"""
Data Retention Policies
=======================

Utilities for managing data retention and archival policies.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, exists

from . import SessionLocal
from .models import (
    Tweet as TweetModel,
    TweetSentiment as TweetSentimentModel,
    SymbolSentiment as SymbolSentimentModel,
    RedditPost as RedditPostModel,
    RedditSentiment as RedditSentimentModel,
    AggregatedSentiment as AggregatedSentimentModel,
    ConfluenceScore as ConfluenceScoreModel
)

logger = logging.getLogger(__name__)


class DataRetentionPolicy:
    """
    Manages data retention policies for different data types
    """
    
    # Default retention periods (days)
    DEFAULT_RETENTION = {
        'tweets': 90,  # 3 months
        'tweet_sentiments': 90,
        'reddit_posts': 90,
        'reddit_sentiments': 90,
        'symbol_sentiments': 180,  # 6 months (aggregated data)
        'aggregated_sentiments': 180,
        'confluence_scores': 180,
        'options_flow': 90
    }
    
    def __init__(self, retention_days: Optional[dict] = None):
        """
        Initialize retention policy
        
        Args:
            retention_days: Override retention periods (dict mapping model type to days)
        """
        self.retention_days = {**self.DEFAULT_RETENTION}
        if retention_days:
            self.retention_days.update(retention_days)
    
    def cleanup_old_data(
        self, 
        db: Optional[Session] = None, 
        dry_run: bool = False,
        batch_size: int = 1000
    ) -> dict:
        """
        Clean up data older than retention period
        
        Args:
            db: Database session (creates new if None)
            dry_run: If True, only report what would be deleted
            batch_size: Number of records to delete per batch (prevents lock contention)
        
        Returns:
            Dictionary with deletion counts by model type
        """
        if db is None:
            db = SessionLocal()
            created_session = True
        else:
            created_session = False
        
        results = {}
        
        try:
            # Cleanup tweet sentiments FIRST (child records) to avoid FK constraint issues
            if 'tweet_sentiments' in self.retention_days:
                cutoff = datetime.now() - timedelta(days=self.retention_days['tweet_sentiments'])
                query = db.query(TweetSentimentModel).filter(TweetSentimentModel.analyzed_at < cutoff)
                count = query.count()
                
                if not dry_run:
                    deleted = self._batch_delete(db, TweetSentimentModel, TweetSentimentModel.analyzed_at < cutoff, batch_size)
                    count = deleted
                
                results['tweet_sentiments'] = count
                logger.info(f"{'Would delete' if dry_run else 'Deleted'} {count} tweet sentiments older than {cutoff}")
            
            # Cleanup tweets (parent records) after sentiments are deleted
            if 'tweets' in self.retention_days:
                cutoff = datetime.now() - timedelta(days=self.retention_days['tweets'])
                query = db.query(TweetModel).filter(TweetModel.created_at < cutoff)
                count = query.count()
                
                if not dry_run:
                    deleted = self._batch_delete(db, TweetModel, TweetModel.created_at < cutoff, batch_size)
                    count = deleted
                
                results['tweets'] = count
                logger.info(f"{'Would delete' if dry_run else 'Deleted'} {count} tweets older than {cutoff}")
            
            # Cleanup Reddit sentiments FIRST (child records)
            if 'reddit_sentiments' in self.retention_days:
                cutoff = datetime.now() - timedelta(days=self.retention_days['reddit_sentiments'])
                query = db.query(RedditSentimentModel).filter(RedditSentimentModel.analyzed_at < cutoff)
                count = query.count()
                
                if not dry_run:
                    deleted = self._batch_delete(db, RedditSentimentModel, RedditSentimentModel.analyzed_at < cutoff, batch_size)
                    count = deleted
                
                results['reddit_sentiments'] = count
                logger.info(f"{'Would delete' if dry_run else 'Deleted'} {count} Reddit sentiments older than {cutoff}")
            
            # Cleanup Reddit posts (parent records) after sentiments
            if 'reddit_posts' in self.retention_days:
                cutoff = datetime.now() - timedelta(days=self.retention_days['reddit_posts'])
                query = db.query(RedditPostModel).filter(RedditPostModel.created_at < cutoff)
                count = query.count()
                
                if not dry_run:
                    deleted = self._batch_delete(db, RedditPostModel, RedditPostModel.created_at < cutoff, batch_size)
                    count = deleted
                
                results['reddit_posts'] = count
                logger.info(f"{'Would delete' if dry_run else 'Deleted'} {count} Reddit posts older than {cutoff}")
            
            # Cleanup symbol sentiments (keep longer)
            if 'symbol_sentiments' in self.retention_days:
                cutoff = datetime.now() - timedelta(days=self.retention_days['symbol_sentiments'])
                query = db.query(SymbolSentimentModel).filter(SymbolSentimentModel.timestamp < cutoff)
                count = query.count()
                
                if not dry_run:
                    deleted = self._batch_delete(db, SymbolSentimentModel, SymbolSentimentModel.timestamp < cutoff, batch_size)
                    count = deleted
                
                results['symbol_sentiments'] = count
                logger.info(f"{'Would delete' if dry_run else 'Deleted'} {count} symbol sentiments older than {cutoff}")
            
            # Cleanup aggregated sentiments
            if 'aggregated_sentiments' in self.retention_days:
                cutoff = datetime.now() - timedelta(days=self.retention_days['aggregated_sentiments'])
                query = db.query(AggregatedSentimentModel).filter(AggregatedSentimentModel.timestamp < cutoff)
                count = query.count()
                
                if not dry_run:
                    deleted = self._batch_delete(db, AggregatedSentimentModel, AggregatedSentimentModel.timestamp < cutoff, batch_size)
                    count = deleted
                
                results['aggregated_sentiments'] = count
                logger.info(f"{'Would delete' if dry_run else 'Deleted'} {count} aggregated sentiments older than {cutoff}")
            
            # Cleanup confluence scores
            if 'confluence_scores' in self.retention_days:
                cutoff = datetime.now() - timedelta(days=self.retention_days['confluence_scores'])
                query = db.query(ConfluenceScoreModel).filter(ConfluenceScoreModel.timestamp < cutoff)
                count = query.count()
                
                if not dry_run:
                    deleted = self._batch_delete(db, ConfluenceScoreModel, ConfluenceScoreModel.timestamp < cutoff, batch_size)
                    count = deleted
                
                results['confluence_scores'] = count
                logger.info(f"{'Would delete' if dry_run else 'Deleted'} {count} confluence scores older than {cutoff}")
            
            # Cleanup options flow (if model exists)
            if 'options_flow' in self.retention_days:
                try:
                    from .models import OptionsFlow as OptionsFlowModel
                    cutoff = datetime.now() - timedelta(days=self.retention_days['options_flow'])
                    query = db.query(OptionsFlowModel).filter(OptionsFlowModel.timestamp < cutoff)
                    count = query.count()
                    
                    if not dry_run:
                        deleted = self._batch_delete(db, OptionsFlowModel, OptionsFlowModel.timestamp < cutoff, batch_size)
                        count = deleted
                    
                    results['options_flow'] = count
                    logger.info(f"{'Would delete' if dry_run else 'Deleted'} {count} options flow records older than {cutoff}")
                except ImportError:
                    logger.debug("OptionsFlow model not found, skipping")
                    results['options_flow'] = 0
            
            # Note: Each _batch_delete call commits its own batches
            # For external sessions, all commits are handled by batch_delete
            
            return results
            
        except Exception as e:
            if not created_session:
                db.rollback()
            logger.error(f"Error during data retention cleanup: {e}", exc_info=True)
            raise
        finally:
            if created_session and db:
                db.close()
    
    def _batch_delete(self, db: Session, model_class, filter_condition, batch_size: int = 1000) -> int:
        """
        Delete records in batches to prevent lock contention
        
        Args:
            db: Database session
            model_class: SQLAlchemy model class
            filter_condition: Filter condition for deletion
            batch_size: Number of records per batch
        
        Returns:
            Total number of records deleted
        """
        total_deleted = 0
        
        while True:
            # Get batch of IDs to delete
            batch_ids = db.query(model_class.id).filter(filter_condition).limit(batch_size).all()
            batch_ids = [id_tuple[0] for id_tuple in batch_ids]
            
            if not batch_ids:
                break
            
            # Delete this batch
            deleted = db.query(model_class).filter(model_class.id.in_(batch_ids)).delete(synchronize_session=False)
            db.commit()
            total_deleted += deleted
            
            logger.debug(f"Deleted batch of {deleted} records (total: {total_deleted})")
            
            # Small delay to prevent lock contention
            if len(batch_ids) == batch_size:
                import time
                time.sleep(0.1)  # 100ms delay between batches
        
        return total_deleted
    
    def get_data_counts(self, db: Optional[Session] = None) -> dict:
        """
        Get counts of data by age buckets
        
        Returns:
            Dictionary with data counts by model and age bucket
        """
        if db is None:
            db = SessionLocal()
        
        try:
            now = datetime.now()
            buckets = {
                'last_24h': now - timedelta(hours=24),
                'last_7d': now - timedelta(days=7),
                'last_30d': now - timedelta(days=30),
                'last_90d': now - timedelta(days=90),
                'older_than_90d': None
            }
            
            counts = {}
            
            # Count tweets
            counts['tweets'] = {}
            for bucket_name, cutoff in buckets.items():
                if cutoff:
                    count = db.query(func.count(TweetModel.id)).filter(
                        TweetModel.created_at >= cutoff
                    ).scalar()
                else:
                    count = db.query(func.count(TweetModel.id)).filter(
                        TweetModel.created_at < buckets['last_90d']
                    ).scalar()
                counts['tweets'][bucket_name] = count
            
            # Count symbol sentiments
            counts['symbol_sentiments'] = {}
            for bucket_name, cutoff in buckets.items():
                if cutoff:
                    count = db.query(func.count(SymbolSentimentModel.id)).filter(
                        SymbolSentimentModel.timestamp >= cutoff
                    ).scalar()
                else:
                    count = db.query(func.count(SymbolSentimentModel.id)).filter(
                        SymbolSentimentModel.timestamp < buckets['last_90d']
                    ).scalar()
                counts['symbol_sentiments'][bucket_name] = count
            
            # Count aggregated sentiments
            counts['aggregated_sentiments'] = {}
            for bucket_name, cutoff in buckets.items():
                if cutoff:
                    count = db.query(func.count(AggregatedSentimentModel.id)).filter(
                        AggregatedSentimentModel.timestamp >= cutoff
                    ).scalar()
                else:
                    count = db.query(func.count(AggregatedSentimentModel.id)).filter(
                        AggregatedSentimentModel.timestamp < buckets['last_90d']
                    ).scalar()
                counts['aggregated_sentiments'][bucket_name] = count
            
            return counts
            
        finally:
            if db:
                db.close()

