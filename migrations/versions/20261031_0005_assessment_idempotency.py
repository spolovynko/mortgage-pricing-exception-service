"""Add content idempotency for generated advisory reports.

Revision ID: 20261031_0005
Revises: 20261030_0004
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261031_0005"
down_revision: str | None = "20261030_0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("pricing_assessments", sa.Column("idempotency_key", sa.String(64), nullable=True))
    op.create_index(
        "uq_pricing_assessments_idempotency_key",
        "pricing_assessments",
        ["idempotency_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_pricing_assessments_idempotency_key", table_name="pricing_assessments")
    op.drop_column("pricing_assessments", "idempotency_key")
