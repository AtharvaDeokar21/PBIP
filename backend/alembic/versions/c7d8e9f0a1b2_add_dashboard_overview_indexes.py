"""Add indexes used by the internal dashboard overview.

Revision ID: c7d8e9f0a1b2
Revises: a5b4f1ff43aa
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "a5b4f1ff43aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_behaviour_events_customer_timestamp",
        "behaviour_events",
        ["customer_id", "timestamp"],
    )
    op.create_index(
        "ix_fraud_alerts_status",
        "fraud_alerts",
        ["status"],
    )
    op.create_index(
        "ix_fraud_investigations_completed_at",
        "fraud_investigations",
        ["completed_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_fraud_investigations_completed_at", table_name="fraud_investigations")
    op.drop_index("ix_fraud_alerts_status", table_name="fraud_alerts")
    op.drop_index("ix_behaviour_events_customer_timestamp", table_name="behaviour_events")
