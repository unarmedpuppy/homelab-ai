"""Add position sync fields to positions table

Revision ID: 004
Revises: 003
Create Date: 2024-12-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Check if columns already exist (in case table was created with Base.metadata.create_all)
    from sqlalchemy import inspect
    from sqlalchemy.engine import reflection
    
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('positions')]
    
    # Add position sync fields to positions table (only if they don't exist)
    if 'last_synced_at' not in columns:
        op.add_column('positions', sa.Column('last_synced_at', sa.DateTime(), nullable=True))
    
    if 'realized_pnl' not in columns:
        op.add_column('positions', sa.Column('realized_pnl', sa.Float(), nullable=True))
    
    # Create index on last_synced_at for efficient queries (only if it doesn't exist)
    indexes = [idx['name'] for idx in inspector.get_indexes('positions')]
    if 'ix_positions_last_synced_at' not in indexes:
        op.create_index(op.f('ix_positions_last_synced_at'), 'positions', ['last_synced_at'], unique=False)


def downgrade():
    # Drop index
    op.drop_index(op.f('ix_positions_last_synced_at'), table_name='positions')
    
    # Remove columns
    op.drop_column('positions', 'realized_pnl')
    op.drop_column('positions', 'last_synced_at')

