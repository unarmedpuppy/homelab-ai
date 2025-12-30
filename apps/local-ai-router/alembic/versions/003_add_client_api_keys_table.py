"""Add client API keys table for authenticating clients to our API

Revision ID: 003
Revises: 002
Create Date: 2025-12-30

This table is for OUR API keys (authenticating clients to the Local AI Router),
NOT for external provider API keys (which are in the api_keys table from migration 002).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create client_api_keys table for authenticating clients."""
    op.create_table(
        'client_api_keys',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        # SHA-256 hash of the full key (64 hex chars)
        sa.Column('key_hash', sa.String(64), nullable=False, unique=True),
        # First 8 chars of the key for display (e.g., "lai_5f4d")
        sa.Column('key_prefix', sa.String(12), nullable=False),
        # Human-readable name (e.g., "agent-1", "opencode", "dashboard")
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='1'),
        # JSON string for future scope restrictions (e.g., ["chat", "agent"])
        sa.Column('scopes', sa.Text(), nullable=True),
        # JSON string for additional metadata
        sa.Column('metadata', sa.Text(), nullable=True),
    )

    # Index for fast validation lookups by hash
    op.create_index('idx_client_api_keys_hash', 'client_api_keys', ['key_hash'])
    # Index for listing enabled keys
    op.create_index('idx_client_api_keys_enabled', 'client_api_keys', ['enabled'])


def downgrade() -> None:
    """Drop client_api_keys table."""
    op.drop_index('idx_client_api_keys_enabled', table_name='client_api_keys')
    op.drop_index('idx_client_api_keys_hash', table_name='client_api_keys')
    op.drop_table('client_api_keys')
