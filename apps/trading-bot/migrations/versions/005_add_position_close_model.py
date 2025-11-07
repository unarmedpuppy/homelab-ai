"""Add PositionClose model for tracking partial and full closes

Revision ID: 005
Revises: 004
Create Date: 2024-12-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Create position_closes table
    op.create_table(
        'position_closes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('position_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('quantity_closed', sa.Integer(), nullable=False),
        sa.Column('entry_price', sa.Float(), nullable=False),
        sa.Column('exit_price', sa.Float(), nullable=False),
        sa.Column('realized_pnl', sa.Float(), nullable=False),
        sa.Column('realized_pnl_pct', sa.Float(), nullable=False),
        sa.Column('closed_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_full_close', sa.Boolean(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['position_id'], ['positions.id'], ),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], )
    )
    
    # Create indexes
    op.create_index(op.f('ix_position_closes_position_id'), 'position_closes', ['position_id'], unique=False)
    op.create_index(op.f('ix_position_closes_account_id'), 'position_closes', ['account_id'], unique=False)
    op.create_index(op.f('ix_position_closes_symbol'), 'position_closes', ['symbol'], unique=False)
    op.create_index(op.f('ix_position_closes_closed_at'), 'position_closes', ['closed_at'], unique=False)
    op.create_index(op.f('ix_position_closes_is_full_close'), 'position_closes', ['is_full_close'], unique=False)
    
    # Create composite index for common queries
    op.create_index('idx_position_closes_account_symbol', 'position_closes', ['account_id', 'symbol'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index('idx_position_closes_account_symbol', table_name='position_closes')
    op.drop_index(op.f('ix_position_closes_is_full_close'), table_name='position_closes')
    op.drop_index(op.f('ix_position_closes_closed_at'), table_name='position_closes')
    op.drop_index(op.f('ix_position_closes_symbol'), table_name='position_closes')
    op.drop_index(op.f('ix_position_closes_account_id'), table_name='position_closes')
    op.drop_index(op.f('ix_position_closes_position_id'), table_name='position_closes')
    
    # Drop table
    op.drop_table('position_closes')

