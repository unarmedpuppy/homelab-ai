"""Initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-01-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create trades table
    op.create_table(
        'trades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('ticker', sa.String(length=20), nullable=False),
        sa.Column('trade_type', sa.String(length=20), nullable=False),
        # Entry details
        sa.Column('entry_price', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('entry_quantity', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('entry_time', sa.TIMESTAMP(), nullable=False),
        sa.Column('entry_commission', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        # Exit details
        sa.Column('exit_price', sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column('exit_quantity', sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column('exit_time', sa.TIMESTAMP(), nullable=True),
        sa.Column('exit_commission', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        # Options specific
        sa.Column('strike_price', sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column('expiration_date', sa.Date(), nullable=True),
        sa.Column('option_type', sa.String(length=4), nullable=True),
        sa.Column('delta', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('gamma', sa.Numeric(precision=8, scale=6), nullable=True),
        sa.Column('theta', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('vega', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('rho', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('implied_volatility', sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column('volume', sa.BigInteger(), nullable=True),
        sa.Column('open_interest', sa.BigInteger(), nullable=True),
        sa.Column('bid_price', sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column('ask_price', sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column('bid_ask_spread', sa.Numeric(precision=12, scale=4), nullable=True),
        # Crypto specific
        sa.Column('crypto_exchange', sa.String(length=50), nullable=True),
        sa.Column('crypto_pair', sa.String(length=20), nullable=True),
        # Prediction market specific
        sa.Column('prediction_market_platform', sa.String(length=50), nullable=True),
        sa.Column('prediction_outcome', sa.String(length=200), nullable=True),
        # Calculated fields
        sa.Column('net_pnl', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('net_roi', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('realized_r_multiple', sa.Numeric(precision=8, scale=4), nullable=True),
        # Metadata
        sa.Column('status', sa.String(length=20), nullable=False, server_default='open'),
        sa.Column('side', sa.String(length=10), nullable=False),
        sa.Column('playbook', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.Text()), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for trades table
    op.create_index('idx_trades_entry_time', 'trades', ['entry_time'])
    op.create_index('idx_trades_ticker', 'trades', ['ticker'])
    op.create_index('idx_trades_status', 'trades', ['status'])
    op.create_index('idx_trades_trade_type', 'trades', ['trade_type'])
    op.create_index('idx_trades_expiration_date', 'trades', ['expiration_date'])
    
    # Create daily_summaries table
    op.create_table(
        'daily_summaries',
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('total_trades', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('winners', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('losers', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('gross_pnl', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0'),
        sa.Column('commissions', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('volume', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('profit_factor', sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column('winrate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('date')
    )
    
    # Create index for daily_summaries
    op.create_index('idx_daily_summaries_date', 'daily_summaries', ['date'])
    
    # Create price_cache table
    op.create_table(
        'price_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticker', sa.String(length=20), nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP(), nullable=False),
        sa.Column('timeframe', sa.String(length=10), nullable=False),
        sa.Column('open_price', sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column('high_price', sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column('low_price', sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column('close_price', sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column('volume', sa.BigInteger(), nullable=True),
        sa.Column('cached_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ticker', 'timestamp', 'timeframe', name='uq_price_cache_ticker_timestamp_timeframe')
    )
    
    # Create indexes for price_cache
    op.create_index('idx_price_cache_ticker_timestamp', 'price_cache', ['ticker', 'timestamp'])
    op.create_index('idx_price_cache_timeframe', 'price_cache', ['timeframe'])
    
    # Create daily_notes table
    op.create_table(
        'daily_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date')
    )
    
    # Create index for daily_notes
    op.create_index('idx_daily_notes_date', 'daily_notes', ['date'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_daily_notes_date', table_name='daily_notes')
    op.drop_index('idx_price_cache_timeframe', table_name='price_cache')
    op.drop_index('idx_price_cache_ticker_timestamp', table_name='price_cache')
    op.drop_index('idx_daily_summaries_date', table_name='daily_summaries')
    op.drop_index('idx_trades_expiration_date', table_name='trades')
    op.drop_index('idx_trades_trade_type', table_name='trades')
    op.drop_index('idx_trades_status', table_name='trades')
    op.drop_index('idx_trades_ticker', table_name='trades')
    op.drop_index('idx_trades_entry_time', table_name='trades')
    
    # Drop tables
    op.drop_table('daily_notes')
    op.drop_table('price_cache')
    op.drop_table('daily_summaries')
    op.drop_table('trades')

