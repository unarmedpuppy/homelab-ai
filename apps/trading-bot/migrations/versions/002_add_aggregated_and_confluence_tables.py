"""Add AggregatedSentiment and ConfluenceScore tables

Revision ID: 002
Revises: 001
Create Date: 2024-12-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Create aggregated_sentiments table
    op.create_table(
        'aggregated_sentiments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('unified_sentiment', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('sentiment_level', sa.String(length=20), nullable=False),
        sa.Column('source_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('provider_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_mention_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('divergence_detected', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('divergence_score', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('volume_trend', sa.String(length=20), nullable=True, server_default='stable'),
        sa.Column('twitter_sentiment', sa.Float(), nullable=True),
        sa.Column('reddit_sentiment', sa.Float(), nullable=True),
        sa.Column('news_sentiment', sa.Float(), nullable=True),
        sa.Column('options_flow_sentiment', sa.Float(), nullable=True),
        sa.Column('source_breakdown', sa.Text(), nullable=True),
        sa.Column('providers_used', sa.Text(), nullable=True),
        sa.Column('aggregated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_aggregated_sentiments_symbol'), 'aggregated_sentiments', ['symbol'], unique=False)
    op.create_index(op.f('ix_aggregated_sentiments_timestamp'), 'aggregated_sentiments', ['timestamp'], unique=False)
    op.create_index('idx_aggregated_sentiment_symbol_timestamp', 'aggregated_sentiments', ['symbol', 'timestamp'], unique=False)
    
    # Create confluence_scores table
    op.create_table(
        'confluence_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('confluence_score', sa.Float(), nullable=False),
        sa.Column('directional_bias', sa.Float(), nullable=False),
        sa.Column('confluence_level', sa.String(length=20), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('technical_score', sa.Float(), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('options_flow_score', sa.Float(), nullable=True),
        sa.Column('technical_contribution', sa.Float(), nullable=True),
        sa.Column('sentiment_contribution', sa.Float(), nullable=True),
        sa.Column('options_flow_contribution', sa.Float(), nullable=True),
        sa.Column('technical_breakdown', sa.Text(), nullable=True),
        sa.Column('components_used', sa.Text(), nullable=True),
        sa.Column('meets_minimum_threshold', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('meets_high_threshold', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('volume_trend', sa.String(length=20), nullable=True, server_default='stable'),
        sa.Column('calculated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_confluence_scores_symbol'), 'confluence_scores', ['symbol'], unique=False)
    op.create_index(op.f('ix_confluence_scores_timestamp'), 'confluence_scores', ['timestamp'], unique=False)
    op.create_index(op.f('ix_confluence_scores_meets_minimum_threshold'), 'confluence_scores', ['meets_minimum_threshold'], unique=False)
    op.create_index(op.f('ix_confluence_scores_meets_high_threshold'), 'confluence_scores', ['meets_high_threshold'], unique=False)
    op.create_index('idx_confluence_symbol_timestamp', 'confluence_scores', ['symbol', 'timestamp'], unique=False)
    op.create_index('idx_confluence_meets_thresholds', 'confluence_scores', ['meets_minimum_threshold', 'meets_high_threshold'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index('idx_confluence_meets_thresholds', table_name='confluence_scores')
    op.drop_index('idx_confluence_symbol_timestamp', table_name='confluence_scores')
    op.drop_index(op.f('ix_confluence_scores_meets_high_threshold'), table_name='confluence_scores')
    op.drop_index(op.f('ix_confluence_scores_meets_minimum_threshold'), table_name='confluence_scores')
    op.drop_index(op.f('ix_confluence_scores_timestamp'), table_name='confluence_scores')
    op.drop_index(op.f('ix_confluence_scores_symbol'), table_name='confluence_scores')
    op.drop_table('confluence_scores')
    
    op.drop_index('idx_aggregated_sentiment_symbol_timestamp', table_name='aggregated_sentiments')
    op.drop_index(op.f('ix_aggregated_sentiments_timestamp'), table_name='aggregated_sentiments')
    op.drop_index(op.f('ix_aggregated_sentiments_symbol'), table_name='aggregated_sentiments')
    op.drop_table('aggregated_sentiments')

