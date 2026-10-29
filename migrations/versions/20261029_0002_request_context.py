"""Add immutable structured context to request versions.

Revision ID: 20261029_0002
Revises: 20261029_0001
Create Date: 2026-10-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261029_0002"
down_revision: str | None = "20261029_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("request_versions", sa.Column("context", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("request_versions", "context")
