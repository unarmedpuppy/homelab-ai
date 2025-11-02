"""Add Twitter sentiment tables

Revision ID: 001
Revises: 
Create Date: 2024-12-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create tweets table
    op.create_table(
        'tweets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tweet_id', sa.String(length=50), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('author_id', sa.String(length=50), nullable=False),
        sa.Column('author_username', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('like_count', sa.Integer(), nullable=True),
        sa.Column('retweet_count', sa.Integer(), nullable=True),
        sa.Column('reply_count', sa.Integer(), nullable=True),
        sa.Column('quote_count', sa.Integer(), nullable=True),
        sa.Column('is_retweet', sa.Boolean(), nullable=True),
        sa.Column('is_quote', sa.Boolean(), nullable=True),
        sa.Column('is_reply', sa.Boolean(), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('symbols_mentioned', sa.Text(), nullable=True),
        sa.Column('raw_data', sa.Text(), nullable=True),
        sa.Column('stored_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tweets_tweet_id'), 'tweets', ['tweet_id'], unique=True)
    op.create_index(op.f('ix_tweets_author_id'), 'tweets', ['author_id'], unique=False)
    op.create_index(op.f('ix_tweets_created_at'), 'tweets', ['created_at'], unique=False)
    
    # Create tweet_sentiments table
    op.create_table(
        'tweet_sentiments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tweet_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('sentiment_score', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('sentiment_level', sa.String(length=20), nullable=False),
        sa.Column('vader_compound', sa.Float(), nullable=True),
        sa.Column('vader_pos', sa.Float(), nullable=True),
        sa.Column('vader_neu', sa.Float(), nullable=True),
        sa.Column('vader_neg', sa.Float(), nullable=True),
        sa.Column('engagement_score', sa.Float(), nullable=True),
        sa.Column('influencer_weight', sa.Float(), nullable=True),
        sa.Column('weighted_score', sa.Float(), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['tweet_id'], ['tweets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tweet_sentiments_tweet_id'), 'tweet_sentiments', ['tweet_id'], unique=False)
    op.create_index(op.f('ix_tweet_sentiments_symbol'), 'tweet_sentiments', ['symbol'], unique=False)
    op.create_index(op.f('ix_tweet_sentiments_analyzed_at'), 'tweet_sentiments', ['analyzed_at'], unique=False)
    
    # Create symbol_sentiments table
    op.create_table(
        'symbol_sentiments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('mention_count', sa.Integer(), nullable=False),
        sa.Column('average_sentiment', sa.Float(), nullable=False),
        sa.Column('weighted_sentiment', sa.Float(), nullable=False),
        sa.Column('influencer_sentiment', sa.Float(), nullable=True),
        sa.Column('engagement_score', sa.Float(), nullable=True),
        sa.Column('sentiment_level', sa.String(length=20), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('volume_trend', sa.String(length=20), nullable=True),
        sa.Column('tweet_ids', sa.Text(), nullable=True),
        sa.Column('aggregated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_symbol_sentiments_symbol'), 'symbol_sentiments', ['symbol'], unique=False)
    op.create_index(op.f('ix_symbol_sentiments_timestamp'), 'symbol_sentiments', ['timestamp'], unique=False)
    
    # Create influencers table
    op.create_table(
        'influencers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=50), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=True),
        sa.Column('follower_count', sa.Integer(), nullable=True),
        sa.Column('following_count', sa.Integer(), nullable=True),
        sa.Column('tweet_count', sa.Integer(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('is_protected', sa.Boolean(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('weight_multiplier', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('added_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_influencers_user_id'), 'influencers', ['user_id'], unique=True)
    op.create_index(op.f('ix_influencers_username'), 'influencers', ['username'], unique=True)
    op.create_index(op.f('ix_influencers_is_active'), 'influencers', ['is_active'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_influencers_is_active'), table_name='influencers')
    op.drop_index(op.f('ix_influencers_username'), table_name='influencers')
    op.drop_index(op.f('ix_influencers_user_id'), table_name='influencers')
    op.drop_table('influencers')
    
    op.drop_index(op.f('ix_symbol_sentiments_timestamp'), table_name='symbol_sentiments')
    op.drop_index(op.f('ix_symbol_sentiments_symbol'), table_name='symbol_sentiments')
    op.drop_table('symbol_sentiments')
    
    op.drop_index(op.f('ix_tweet_sentiments_analyzed_at'), table_name='tweet_sentiments')
    op.drop_index(op.f('ix_tweet_sentiments_symbol'), table_name='tweet_sentiments')
    op.drop_index(op.f('ix_tweet_sentiments_tweet_id'), table_name='tweet_sentiments')
    op.drop_table('tweet_sentiments')
    
    op.drop_index(op.f('ix_tweets_created_at'), table_name='tweets')
    op.drop_index(op.f('ix_tweets_author_id'), table_name='tweets')
    op.drop_index(op.f('ix_tweets_tweet_id'), table_name='tweets')
    op.drop_table('tweets')

