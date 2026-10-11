"""Add indexes for the paginated customer directory.

Revision ID: d4e5f6a7b8c9
Revises: c7d8e9f0a1b2
"""
from typing import Sequence, Union

from alembic import op


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_accounts_customer_status",
        "accounts",
        ["customer_id", "status"],
    )
    op.create_index(
        "ix_fraud_alerts_customer_status",
        "fraud_alerts",
        ["customer_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_fraud_alerts_customer_status", table_name="fraud_alerts")
    op.drop_index("ix_accounts_customer_status", table_name="accounts")
