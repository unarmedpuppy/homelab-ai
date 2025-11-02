"""Add Cash Account and Risk Management tables

Revision ID: 003
Revises: 002
Create Date: 2024-12-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Add risk management fields to trades table
    op.add_column('trades', sa.Column('settlement_date', sa.DateTime(), nullable=True))
    op.add_column('trades', sa.Column('is_day_trade', sa.Boolean(), nullable=True, server_default='0'))
    op.add_column('trades', sa.Column('confidence_score', sa.Float(), nullable=True))
    op.create_index(op.f('ix_trades_is_day_trade'), 'trades', ['is_day_trade'], unique=False)
    
    # Create cash_account_state table
    op.create_table(
        'cash_account_state',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('balance', sa.Float(), nullable=False),
        sa.Column('is_cash_account_mode', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('threshold', sa.Float(), nullable=False, server_default='25000.0'),
        sa.Column('last_checked', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.UniqueConstraint('account_id')
    )
    op.create_index(op.f('ix_cash_account_state_account_id'), 'cash_account_state', ['account_id'], unique=True)
    op.create_index(op.f('ix_cash_account_state_is_cash_account_mode'), 'cash_account_state', ['is_cash_account_mode'], unique=False)
    op.create_index('idx_cash_account_mode', 'cash_account_state', ['is_cash_account_mode'], unique=False)
    
    # Create day_trades table
    op.create_table(
        'day_trades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('buy_trade_id', sa.Integer(), nullable=False),
        sa.Column('sell_trade_id', sa.Integer(), nullable=False),
        sa.Column('trade_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.ForeignKeyConstraint(['buy_trade_id'], ['trades.id'], ),
        sa.ForeignKeyConstraint(['sell_trade_id'], ['trades.id'], )
    )
    op.create_index(op.f('ix_day_trades_account_id'), 'day_trades', ['account_id'], unique=False)
    op.create_index(op.f('ix_day_trades_symbol'), 'day_trades', ['symbol'], unique=False)
    op.create_index(op.f('ix_day_trades_trade_date'), 'day_trades', ['trade_date'], unique=False)
    op.create_index('idx_day_trade_account_date', 'day_trades', ['account_id', 'trade_date'], unique=False)
    
    # Create settlement_tracking table
    op.create_table(
        'settlement_tracking',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('trade_id', sa.Integer(), nullable=False),
        sa.Column('trade_date', sa.DateTime(), nullable=False),
        sa.Column('settlement_date', sa.DateTime(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('is_settled', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('settled_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
        sa.ForeignKeyConstraint(['trade_id'], ['trades.id'], ),
        sa.UniqueConstraint('trade_id')
    )
    op.create_index(op.f('ix_settlement_tracking_account_id'), 'settlement_tracking', ['account_id'], unique=False)
    op.create_index(op.f('ix_settlement_tracking_trade_id'), 'settlement_tracking', ['trade_id'], unique=True)
    op.create_index(op.f('ix_settlement_tracking_trade_date'), 'settlement_tracking', ['trade_date'], unique=False)
    op.create_index(op.f('ix_settlement_tracking_settlement_date'), 'settlement_tracking', ['settlement_date'], unique=False)
    op.create_index(op.f('ix_settlement_tracking_is_settled'), 'settlement_tracking', ['is_settled'], unique=False)
    op.create_index('idx_settlement_account_date', 'settlement_tracking', ['account_id', 'settlement_date'], unique=False)
    
    # Create trade_frequency_tracking table
    op.create_table(
        'trade_frequency_tracking',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('daily_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('weekly_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('week_start_date', sa.DateTime(), nullable=False),
        sa.Column('last_trade_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], )
    )
    op.create_index(op.f('ix_trade_frequency_tracking_account_id'), 'trade_frequency_tracking', ['account_id'], unique=False)
    op.create_index(op.f('ix_trade_frequency_tracking_date'), 'trade_frequency_tracking', ['date'], unique=False)
    op.create_index('idx_frequency_account_date', 'trade_frequency_tracking', ['account_id', 'date'], unique=True)
    op.create_index('idx_frequency_week_start', 'trade_frequency_tracking', ['account_id', 'week_start_date'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index('idx_frequency_week_start', table_name='trade_frequency_tracking')
    op.drop_index('idx_frequency_account_date', table_name='trade_frequency_tracking')
    op.drop_index(op.f('ix_trade_frequency_tracking_date'), table_name='trade_frequency_tracking')
    op.drop_index(op.f('ix_trade_frequency_tracking_account_id'), table_name='trade_frequency_tracking')
    op.drop_table('trade_frequency_tracking')
    
    op.drop_index('idx_settlement_account_date', table_name='settlement_tracking')
    op.drop_index(op.f('ix_settlement_tracking_is_settled'), table_name='settlement_tracking')
    op.drop_index(op.f('ix_settlement_tracking_settlement_date'), table_name='settlement_tracking')
    op.drop_index(op.f('ix_settlement_tracking_trade_date'), table_name='settlement_tracking')
    op.drop_index(op.f('ix_settlement_tracking_trade_id'), table_name='settlement_tracking')
    op.drop_index(op.f('ix_settlement_tracking_account_id'), table_name='settlement_tracking')
    op.drop_table('settlement_tracking')
    
    op.drop_index('idx_day_trade_account_date', table_name='day_trades')
    op.drop_index(op.f('ix_day_trades_trade_date'), table_name='day_trades')
    op.drop_index(op.f('ix_day_trades_symbol'), table_name='day_trades')
    op.drop_index(op.f('ix_day_trades_account_id'), table_name='day_trades')
    op.drop_table('day_trades')
    
    op.drop_index('idx_cash_account_mode', table_name='cash_account_state')
    op.drop_index(op.f('ix_cash_account_state_is_cash_account_mode'), table_name='cash_account_state')
    op.drop_index(op.f('ix_cash_account_state_account_id'), table_name='cash_account_state')
    op.drop_table('cash_account_state')
    
    # Remove columns from trades table
    op.drop_index(op.f('ix_trades_is_day_trade'), table_name='trades')
    op.drop_column('trades', 'confidence_score')
    op.drop_column('trades', 'is_day_trade')
    op.drop_column('trades', 'settlement_date')

