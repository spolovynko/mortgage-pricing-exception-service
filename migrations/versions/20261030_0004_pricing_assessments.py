"""Store advisory assessments separately from human decisions.

Revision ID: 20261030_0004
Revises: 20261030_0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261030_0004"
down_revision: str | None = "20261030_0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pricing_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("model_identity", sa.String(length=200), nullable=False),
        sa.Column("prompt_version", sa.String(length=80), nullable=False),
        sa.Column(
            "status",
            sa.Enum("completed", "stale", name="assessmentstatus", native_enum=False),
            nullable=False,
        ),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "version_number >= 1", name="ck_pricing_assessments_assessment_version_positive"
        ),
        sa.CheckConstraint(
            "length(model_identity) BETWEEN 1 AND 200",
            name="ck_pricing_assessments_assessment_model_length",
        ),
        sa.CheckConstraint(
            "length(prompt_version) BETWEEN 1 AND 80",
            name="ck_pricing_assessments_assessment_prompt_length",
        ),
        sa.CheckConstraint(
            "length(status) <= 16", name="ck_pricing_assessments_assessment_status_length"
        ),
        sa.ForeignKeyConstraint(
            ["request_id", "version_number"],
            ["request_versions.request_id", "request_versions.version_number"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pricing_assessments_request_id", "pricing_assessments", ["request_id"])


def downgrade() -> None:
    op.drop_index("ix_pricing_assessments_request_id", table_name="pricing_assessments")
    op.drop_table("pricing_assessments")
