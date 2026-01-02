"""Add conversation metadata columns

Revision ID: 001
Revises:
Create Date: 2025-01-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add username, source, and display_name columns to conversations table."""
    # Add new columns
    op.add_column('conversations', sa.Column('username', sa.Text(), nullable=True))
    op.add_column('conversations', sa.Column('source', sa.Text(), nullable=True))
    op.add_column('conversations', sa.Column('display_name', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove metadata columns from conversations table."""
    op.drop_column('conversations', 'display_name')
    op.drop_column('conversations', 'source')
    op.drop_column('conversations', 'username')
