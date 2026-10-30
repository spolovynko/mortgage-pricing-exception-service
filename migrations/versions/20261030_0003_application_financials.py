"""Add application financial values used to prefill new discount requests.

Revision ID: 20261030_0003
Revises: 20261029_0002
Create Date: 2026-10-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261030_0003"
down_revision: str | None = "20261029_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Use additive columns without rebuilding the referenced application table."""
    definitions = (
        (
            "loan_amount",
            sa.Numeric(14, 2),
            "loan_amount_range",
            "loan_amount IS NULL OR (loan_amount > 0 AND loan_amount < 1000000000000)",
        ),
        (
            "property_value",
            sa.Numeric(14, 2),
            "property_value_range",
            "property_value IS NULL OR (property_value > 0 AND property_value < 1000000000000)",
        ),
        (
            "standard_rate_bps",
            sa.Integer(),
            "standard_rate_valid",
            "standard_rate_bps IS NULL OR "
            "(standard_rate_bps >= 0 AND typeof(standard_rate_bps) = 'integer')",
        ),
        (
            "term_months",
            sa.Integer(),
            "term_valid",
            "term_months IS NULL OR (term_months > 0 AND typeof(term_months) = 'integer')",
        ),
    )
    for name, column_type, constraint_name, check in definitions:
        op.add_column(
            "mortgage_applications",
            sa.Column(
                name,
                column_type,
                sa.CheckConstraint(check, name=op.f(f"ck_mortgage_applications_{constraint_name}")),
                nullable=True,
            ),
        )


def downgrade() -> None:
    for name in ("term_months", "standard_rate_bps", "property_value", "loan_amount"):
        op.drop_column("mortgage_applications", name)
