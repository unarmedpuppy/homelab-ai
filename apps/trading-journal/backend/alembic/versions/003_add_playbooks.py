"""Add playbooks and playbook_templates tables

Revision ID: 003_add_playbooks
Revises: 002_add_exit_time_index
Create Date: 2025-11-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_add_playbooks'
down_revision: Union[str, None] = '002_add_exit_time_index'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create playbook_templates table first (no dependencies)
    op.create_table(
        'playbook_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('user_id', sa.Integer(), nullable=False, server_default='1'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_playbook_templates_category', 'playbook_templates', ['category'])
    op.create_index('idx_playbook_templates_system', 'playbook_templates', ['is_system'])
    
    # Create playbooks table
    op.create_table(
        'playbooks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_shared', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('user_id', sa.Integer(), nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['template_id'], ['playbook_templates.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('idx_playbooks_name', 'playbooks', ['name'])
    op.create_index('idx_playbooks_active', 'playbooks', ['is_active'])
    op.create_index('idx_playbooks_user', 'playbooks', ['user_id'])
    
    # Add playbook_id column to trades table
    op.add_column('trades', sa.Column('playbook_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_trades_playbook_id', 'trades', 'playbooks', ['playbook_id'], ['id'], ondelete='SET NULL')
    op.create_index('idx_trades_playbook_id', 'trades', ['playbook_id'])
    
    # Migrate existing playbook string values to playbook_id
    # First, create playbooks from existing playbook names
    # Use raw SQL to handle the migration
    connection = op.get_bind()
    connection.execute(sa.text("""
        INSERT INTO playbooks (name, description, is_active, user_id)
        SELECT DISTINCT playbook, NULL, true, 1
        FROM trades
        WHERE playbook IS NOT NULL AND playbook != ''
        ON CONFLICT (name) DO NOTHING
    """))
    
    # Update trades to reference playbook_id
    connection.execute(sa.text("""
        UPDATE trades
        SET playbook_id = playbooks.id
        FROM playbooks
        WHERE trades.playbook = playbooks.name
    """))
    
    # Note: We keep the old playbook column for now to avoid breaking existing code
    # It will be removed in a future migration after frontend is updated


def downgrade() -> None:
    # Remove playbook_id from trades
    op.drop_index('idx_trades_playbook_id', table_name='trades')
    op.drop_constraint('fk_trades_playbook_id', 'trades', type_='foreignkey')
    op.drop_column('trades', 'playbook_id')
    
    # Drop playbooks table
    op.drop_index('idx_playbooks_user', table_name='playbooks')
    op.drop_index('idx_playbooks_active', table_name='playbooks')
    op.drop_index('idx_playbooks_name', table_name='playbooks')
    op.drop_table('playbooks')
    
    # Drop playbook_templates table
    op.drop_index('idx_playbook_templates_system', table_name='playbook_templates')
    op.drop_index('idx_playbook_templates_category', table_name='playbook_templates')
    op.drop_table('playbook_templates')

