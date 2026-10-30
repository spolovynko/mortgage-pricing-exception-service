"""Business storage models introduced incrementally through Phase 02."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mortgage_pricing.persistence.base import Base
from mortgage_pricing.persistence.types import UTCDateTime


def utc_now() -> datetime:
    """Return a timezone-aware timestamp for ORM-created records."""
    return datetime.now(UTC)


class Role(StrEnum):
    """Roles available to the deliberately small internal-user model."""

    RELATIONSHIP_MANAGER = "relationship_manager"
    REVIEWER = "reviewer"


ROLE_ENUM = Enum(
    Role,
    name="user_role",
    native_enum=False,
    create_constraint=True,
    validate_strings=True,
    values_callable=lambda roles: [role.value for role in roles],
)


class User(Base):
    """An internal user identified by a stable, non-secret login name."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("length(login) BETWEEN 1 AND 64", name="login_length"),
        CheckConstraint("length(display_name) BETWEEN 1 AND 120", name="display_name_length"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    login: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now, nullable=False)

    role_memberships: Mapped[list[UserRoleMembership]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    managed_applications: Mapped[list[MortgageApplication]] = relationship(back_populates="manager")


class UserRoleMembership(Base):
    """A user's role membership; the pair is unique by the composite primary key."""

    __tablename__ = "user_role_memberships"

    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="RESTRICT"),
        primary_key=True,
    )
    role: Mapped[Role] = mapped_column(
        ROLE_ENUM,
        primary_key=True,
    )

    user: Mapped[User] = relationship(back_populates="role_memberships")


class MortgageApplication(Base):
    """An existing mortgage application owned by one relationship manager."""

    __tablename__ = "mortgage_applications"
    __table_args__ = (
        UniqueConstraint("reference", name="reference"),
        CheckConstraint("length(reference) BETWEEN 1 AND 64", name="reference_length"),
        CheckConstraint(
            "loan_amount IS NULL OR (loan_amount > 0 AND loan_amount < 1000000000000)",
            name="loan_amount_range",
        ),
        CheckConstraint(
            "property_value IS NULL OR (property_value > 0 AND property_value < 1000000000000)",
            name="property_value_range",
        ),
        CheckConstraint(
            "standard_rate_bps IS NULL OR "
            "(standard_rate_bps >= 0 AND typeof(standard_rate_bps) = 'integer')",
            name="standard_rate_valid",
        ),
        CheckConstraint(
            "term_months IS NULL OR (term_months > 0 AND typeof(term_months) = 'integer')",
            name="term_valid",
        ),
        CheckConstraint(
            "manager_role = 'relationship_manager'",
            name="manager_role_is_relationship_manager",
        ),
        ForeignKeyConstraint(
            ["manager_id", "manager_role"],
            ["user_role_memberships.user_id", "user_role_memberships.role"],
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    reference: Mapped[str] = mapped_column(String(64), nullable=False)
    manager_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    manager_role: Mapped[Role] = mapped_column(
        ROLE_ENUM, default=Role.RELATIONSHIP_MANAGER, nullable=False
    )
    loan_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    property_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    standard_rate_bps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    term_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now, nullable=False)

    manager: Mapped[User] = relationship(back_populates="managed_applications")


class PricingRequest(Base):
    """The single logical pricing exception request for an application."""

    __tablename__ = "pricing_requests"
    __table_args__ = (
        UniqueConstraint("application_id", name="application_id"),
        CheckConstraint(
            "current_version_number IS NULL OR current_version_number >= 1",
            name="current_version_positive",
        ),
        ForeignKeyConstraint(
            ["id", "current_version_number"],
            ["request_versions.request_id", "request_versions.version_number"],
            ondelete="RESTRICT",
            use_alter=True,
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("mortgage_applications.id", ondelete="RESTRICT"), nullable=False
    )
    current_version_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now, nullable=False)

    application: Mapped[MortgageApplication] = relationship()
    versions: Mapped[list[RequestVersion]] = relationship(
        back_populates="request",
        foreign_keys="RequestVersion.request_id",
        order_by="RequestVersion.version_number",
    )


class RequestVersion(Base):
    """Submitted terms identified by request and monotonic version number."""

    __tablename__ = "request_versions"
    __table_args__ = (
        CheckConstraint("version_number >= 1", name="version_positive"),
        CheckConstraint("discount_bps > 0", name="discount_positive"),
        CheckConstraint("typeof(discount_bps) = 'integer'", name="discount_integer"),
        CheckConstraint("length(trim(reason)) BETWEEN 1 AND 2000", name="reason_length"),
    )

    request_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("pricing_requests.id", ondelete="RESTRICT"), primary_key=True
    )
    version_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    discount_bps: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(2000), nullable=False)
    context: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    submitted_by_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    submitted_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now, nullable=False)

    request: Mapped[PricingRequest] = relationship(
        back_populates="versions", foreign_keys=[request_id]
    )
    submitted_by: Mapped[User] = relationship()


class DecisionOutcome(StrEnum):
    APPROVED = "approved"
    DECLINED = "declined"


class PricingDecision(Base):
    """One final human decision about one submitted request version."""

    __tablename__ = "pricing_decisions"
    __table_args__ = (
        UniqueConstraint("request_id", "version_number", name="request_version"),
        ForeignKeyConstraint(
            ["request_id", "version_number"],
            ["request_versions.request_id", "request_versions.version_number"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["reviewer_id", "reviewer_role"],
            ["user_role_memberships.user_id", "user_role_memberships.role"],
            ondelete="RESTRICT",
        ),
        CheckConstraint("reviewer_role = 'reviewer'", name="reviewer_role_is_reviewer"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    outcome: Mapped[DecisionOutcome] = mapped_column(
        Enum(
            DecisionOutcome,
            name="decision_outcome",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=lambda outcomes: [outcome.value for outcome in outcomes],
        ),
        nullable=False,
    )
    reviewer_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    reviewer_role: Mapped[Role] = mapped_column(ROLE_ENUM, default=Role.REVIEWER, nullable=False)
    decided_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now, nullable=False)

    version: Mapped[RequestVersion] = relationship(
        primaryjoin="and_(PricingDecision.request_id == RequestVersion.request_id, "
        "PricingDecision.version_number == RequestVersion.version_number)",
        foreign_keys=[request_id, version_number],
    )
    reviewer: Mapped[User] = relationship(
        primaryjoin="PricingDecision.reviewer_id == User.id",
        foreign_keys=[reviewer_id],
    )


class HistoryEventType(StrEnum):
    CREATED = "created"
    REVISED = "revised"
    APPROVED = "approved"
    DECLINED = "declined"


class RequestHistoryEvent(Base):
    """Append-only event for a business change to an exact request version."""

    __tablename__ = "request_history_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["request_id", "version_number"],
            ["request_versions.request_id", "request_versions.version_number"],
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[HistoryEventType] = mapped_column(
        Enum(
            HistoryEventType,
            name="history_event_type",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=lambda types: [event_type.value for event_type in types],
        ),
        nullable=False,
    )
    actor_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    occurred_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now, nullable=False)

    actor: Mapped[User] = relationship()
    version: Mapped[RequestVersion] = relationship(
        primaryjoin="and_(RequestHistoryEvent.request_id == RequestVersion.request_id, "
        "RequestHistoryEvent.version_number == RequestVersion.version_number)",
        foreign_keys=[request_id, version_number],
    )


class CreationIdempotencyRecord(Base):
    """Caller-scoped creation key and immutable reference to its first result."""

    __tablename__ = "creation_idempotency_records"
    __table_args__ = (
        CheckConstraint("length(trim(key)) BETWEEN 1 AND 128", name="key_length"),
        CheckConstraint("version_number = 1", name="original_version_one"),
        CheckConstraint(
            "length(input_fingerprint) = 64 AND input_fingerprint NOT GLOB '*[^0-9a-f]*'",
            name="fingerprint_sha256_hex",
        ),
        ForeignKeyConstraint(
            ["request_id", "version_number"],
            ["request_versions.request_id", "request_versions.version_number"],
            ondelete="RESTRICT",
        ),
    )

    caller_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True
    )
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    input_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utc_now, nullable=False)

    caller: Mapped[User] = relationship()
    original_version: Mapped[RequestVersion] = relationship(
        primaryjoin="and_(CreationIdempotencyRecord.request_id == RequestVersion.request_id, "
        "CreationIdempotencyRecord.version_number == RequestVersion.version_number)",
        foreign_keys=[request_id, version_number],
    )


@event.listens_for(RequestVersion, "before_update")
@event.listens_for(RequestVersion, "before_delete")
def protect_submitted_version(*_args: object) -> None:
    """Reject ORM mutation; Step 9 migration will also protect direct SQL writes."""
    raise ValueError("Submitted request versions cannot be changed or deleted")


@event.listens_for(PricingDecision, "before_update")
@event.listens_for(PricingDecision, "before_delete")
@event.listens_for(RequestHistoryEvent, "before_update")
@event.listens_for(RequestHistoryEvent, "before_delete")
def protect_decision_history(*_args: object) -> None:
    """Protect ORM records; Step 9 migration must protect direct SQL writes."""
    raise ValueError("Decisions and history events cannot be changed or deleted")


@event.listens_for(CreationIdempotencyRecord, "before_update")
@event.listens_for(CreationIdempotencyRecord, "before_delete")
def protect_idempotency_record(*_args: object) -> None:
    """Keep original retry mapping stable through ORM writes."""
    raise ValueError("Creation idempotency records cannot be changed or deleted")
