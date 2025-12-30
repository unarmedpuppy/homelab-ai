"""Add image_refs column to messages table

Revision ID: 004
Revises: 003
Create Date: 2025-12-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add image_refs column (JSON string) for storing image metadata."""
    op.add_column('messages', sa.Column('image_refs', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove image_refs column."""
    op.drop_column('messages', 'image_refs')
