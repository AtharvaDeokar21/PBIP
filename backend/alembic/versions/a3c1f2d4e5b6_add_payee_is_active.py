"""add payees.is_active for soft deactivation

Revision ID: a3c1f2d4e5b6
Revises: 795f175d435c
Create Date: 2026-10-03 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a3c1f2d4e5b6'
down_revision: Union[str, Sequence[str], None] = '795f175d435c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'payees',
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column('payees', 'is_active')
