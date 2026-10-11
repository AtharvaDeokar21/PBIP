"""Add indexes for internal analytics filters and aggregations.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
"""
from typing import Sequence, Union

from alembic import op


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_behaviour_events_session_customer_timestamp",
        "behaviour_events",
        ["session_id", "customer_id", "timestamp"],
    )
    op.create_index(
        "ix_behaviour_events_timestamp_type_product",
        "behaviour_events",
        ["timestamp", "event_type", "product_category"],
    )
    op.create_index(
        "ix_transactions_account_type_date",
        "transactions",
        ["account_id", "transaction_type", "transaction_date"],
    )
    op.create_index(
        "ix_transactions_date_type",
        "transactions",
        ["transaction_date", "transaction_type"],
    )
    op.create_index(
        "ix_customers_segment_name",
        "customers",
        ["customer_segment", "last_name", "first_name"],
    )


def downgrade() -> None:
    op.drop_index("ix_customers_segment_name", table_name="customers")
    op.drop_index("ix_transactions_date_type", table_name="transactions")
    op.drop_index("ix_transactions_account_type_date", table_name="transactions")
    op.drop_index(
        "ix_behaviour_events_timestamp_type_product",
        table_name="behaviour_events",
    )
    op.drop_index(
        "ix_behaviour_events_session_customer_timestamp",
        table_name="behaviour_events",
    )
