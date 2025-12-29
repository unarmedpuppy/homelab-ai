"""Add API keys table

Revision ID: 002
Revises: 001
Create Date: 2025-01-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create API keys table for managing provider API keys."""
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('provider_id', sa.Text(), nullable=False),
        sa.Column('key_name', sa.Text(), nullable=False),
        sa.Column('api_key', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('metadata', sa.Text(), nullable=True),
    )

    # Create index on provider_id for fast lookups
    op.create_index('idx_api_keys_provider', 'api_keys', ['provider_id'])

    # Create unique constraint on (provider_id, key_name)
    op.create_unique_constraint(
        'uq_api_keys_provider_name',
        'api_keys',
        ['provider_id', 'key_name']
    )


def downgrade() -> None:
    """Drop API keys table."""
    op.drop_index('idx_api_keys_provider', table_name='api_keys')
    op.drop_table('api_keys')
