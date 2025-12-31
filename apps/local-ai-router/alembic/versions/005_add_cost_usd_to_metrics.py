"""Add cost_usd column to metrics table

Revision ID: 005
Revises: 004
Create Date: 2025-12-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('metrics', sa.Column('cost_usd', sa.Float(), nullable=True))
    op.add_column('daily_stats', sa.Column('total_cost_usd', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('daily_stats', 'total_cost_usd')
    op.drop_column('metrics', 'cost_usd')
