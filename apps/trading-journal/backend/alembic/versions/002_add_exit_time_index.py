"""Add exit_time index for query optimization

Revision ID: 002_add_exit_time_index
Revises: 001_initial_schema
Create Date: 2025-11-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_add_exit_time_index'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add index on exit_time for faster queries on closed trades
    op.create_index('idx_trades_exit_time', 'trades', ['exit_time'])


def downgrade() -> None:
    op.drop_index('idx_trades_exit_time', table_name='trades')

