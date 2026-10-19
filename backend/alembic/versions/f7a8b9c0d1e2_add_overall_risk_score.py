"""add overall risk score

Revision ID: f7a8b9c0d1e2
Revises: e5f6a7b8c9d0
"""

from alembic import op
import sqlalchemy as sa


revision = "f7a8b9c0d1e2"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "customer_risk_profiles",
        sa.Column("overall_risk_score", sa.Numeric(precision=7, scale=4), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("customer_risk_profiles", "overall_risk_score")
