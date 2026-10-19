"""Add the covering index used by customer financial insights.

Revision ID: g6b7c8d9e0f1
Revises: e5f6a7b8c9d0
"""
from typing import Sequence, Union

from alembic import op


revision: str = "g6b7c8d9e0f1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_transactions_account_date_category",
        "transactions",
        ["account_id", "transaction_date", "category"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_transactions_account_date_category",
        table_name="transactions",
    )
