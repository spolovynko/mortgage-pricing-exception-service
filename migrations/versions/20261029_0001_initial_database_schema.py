"""Create the initial pricing-exception database schema.

Revision ID: 20261029_0001
Revises:
Create Date: 2026-10-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261029_0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


ROLE = sa.Enum(
    "relationship_manager",
    "reviewer",
    name="user_role",
    native_enum=False,
    create_constraint=True,
)
OUTCOME = sa.Enum(
    "approved",
    "declined",
    name="decision_outcome",
    native_enum=False,
    create_constraint=True,
)
EVENT_TYPE = sa.Enum(
    "created",
    "revised",
    "approved",
    "declined",
    name="history_event_type",
    native_enum=False,
    create_constraint=True,
)


def upgrade() -> None:
    """Create schema and SQLite triggers that protect immutable records."""
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("login", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("length(login) BETWEEN 1 AND 64", name="ck_users_login_length"),
        sa.CheckConstraint(
            "length(display_name) BETWEEN 1 AND 120", name="ck_users_display_name_length"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("login", name="uq_users_login"),
    )
    op.create_table(
        "user_role_memberships",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", ROLE, nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_role_memberships_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("user_id", "role", name="pk_user_role_memberships"),
    )
    op.create_table(
        "mortgage_applications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("reference", sa.String(length=64), nullable=False),
        sa.Column("manager_id", sa.Uuid(), nullable=False),
        sa.Column("manager_role", ROLE, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "manager_role = 'relationship_manager'",
            name="ck_mortgage_applications_manager_role_is_relationship_manager",
        ),
        sa.CheckConstraint(
            "length(reference) BETWEEN 1 AND 64", name="ck_mortgage_applications_reference_length"
        ),
        sa.ForeignKeyConstraint(
            ["manager_id"],
            ["users.id"],
            name="fk_mortgage_applications_manager_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["manager_id", "manager_role"],
            ["user_role_memberships.user_id", "user_role_memberships.role"],
            name="fk_mortgage_applications_manager_id_manager_role_user_role_memberships",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_mortgage_applications"),
        sa.UniqueConstraint("reference", name="uq_mortgage_applications_reference"),
    )
    op.create_table(
        "pricing_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("current_version_number", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "current_version_number IS NULL OR current_version_number >= 1",
            name="ck_pricing_requests_current_version_positive",
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["mortgage_applications.id"],
            name="fk_pricing_requests_application_id_mortgage_applications",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["id", "current_version_number"],
            ["request_versions.request_id", "request_versions.version_number"],
            name="fk_pricing_requests_id_current_version_number_request_versions",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_pricing_requests"),
        sa.UniqueConstraint("application_id", name="uq_pricing_requests_application_id"),
    )
    op.create_table(
        "request_versions",
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("discount_bps", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=2000), nullable=False),
        sa.Column("submitted_by_id", sa.Uuid(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("discount_bps > 0", name="ck_request_versions_discount_positive"),
        sa.CheckConstraint(
            "typeof(discount_bps) = 'integer'", name="ck_request_versions_discount_integer"
        ),
        sa.CheckConstraint(
            "length(trim(reason)) BETWEEN 1 AND 2000", name="ck_request_versions_reason_length"
        ),
        sa.CheckConstraint("version_number >= 1", name="ck_request_versions_version_positive"),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["pricing_requests.id"],
            name="fk_request_versions_request_id_pricing_requests",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["submitted_by_id"],
            ["users.id"],
            name="fk_request_versions_submitted_by_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("request_id", "version_number", name="pk_request_versions"),
    )
    op.create_table(
        "pricing_decisions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("outcome", OUTCOME, nullable=False),
        sa.Column("reviewer_id", sa.Uuid(), nullable=False),
        sa.Column("reviewer_role", ROLE, nullable=False),
        sa.Column("decided_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "reviewer_role = 'reviewer'", name="ck_pricing_decisions_reviewer_role_is_reviewer"
        ),
        sa.ForeignKeyConstraint(
            ["request_id", "version_number"],
            ["request_versions.request_id", "request_versions.version_number"],
            name="fk_pricing_decisions_request_id_version_number_request_versions",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_id", "reviewer_role"],
            ["user_role_memberships.user_id", "user_role_memberships.role"],
            name="fk_pricing_decisions_reviewer_id_reviewer_role_user_role_memberships",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_pricing_decisions"),
        sa.UniqueConstraint(
            "request_id", "version_number", name="uq_pricing_decisions_request_version"
        ),
    )
    op.create_table(
        "request_history_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("event_type", EVENT_TYPE, nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name="fk_request_history_events_actor_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["request_id", "version_number"],
            ["request_versions.request_id", "request_versions.version_number"],
            name="fk_request_history_events_request_id_version_number_request_versions",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_request_history_events"),
    )
    op.create_table(
        "creation_idempotency_records",
        sa.Column("caller_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("input_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "length(input_fingerprint) = 64 AND input_fingerprint NOT GLOB '*[^0-9a-f]*'",
            name="ck_creation_idempotency_records_fingerprint_sha256_hex",
        ),
        sa.CheckConstraint(
            "length(trim(key)) BETWEEN 1 AND 128", name="ck_creation_idempotency_records_key_length"
        ),
        sa.CheckConstraint(
            "version_number = 1", name="ck_creation_idempotency_records_original_version_one"
        ),
        sa.ForeignKeyConstraint(
            ["caller_id"],
            ["users.id"],
            name="fk_creation_idempotency_records_caller_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["request_id", "version_number"],
            ["request_versions.request_id", "request_versions.version_number"],
            name="fk_creation_idempotency_records_request_id_version_number_request_versions",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("caller_id", "key", name="pk_creation_idempotency_records"),
    )
    for table in (
        "request_versions",
        "pricing_decisions",
        "request_history_events",
        "creation_idempotency_records",
    ):
        op.execute(
            f"CREATE TRIGGER prevent_{table}_update BEFORE UPDATE ON {table} "
            f"BEGIN SELECT RAISE(ABORT, '{table} is immutable'); END"
        )
        op.execute(
            f"CREATE TRIGGER prevent_{table}_delete BEFORE DELETE ON {table} "
            f"BEGIN SELECT RAISE(ABORT, '{table} is immutable'); END"
        )


def downgrade() -> None:
    """Remove the initial schema and its immutability triggers."""
    for table in (
        "creation_idempotency_records",
        "request_history_events",
        "pricing_decisions",
        "request_versions",
    ):
        op.execute(f"DROP TRIGGER prevent_{table}_delete")
        op.execute(f"DROP TRIGGER prevent_{table}_update")
    op.drop_table("creation_idempotency_records")
    op.drop_table("request_history_events")
    op.drop_table("pricing_decisions")
    op.drop_table("request_versions")
    op.drop_table("pricing_requests")
    op.drop_table("mortgage_applications")
    op.drop_table("user_role_memberships")
    op.drop_table("users")
