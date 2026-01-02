"""Add system_prompt column to agent_runs table

Revision ID: 006
Revises: 005
Create Date: 2025-12-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('agent_runs', sa.Column('system_prompt', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('agent_runs', 'system_prompt')
