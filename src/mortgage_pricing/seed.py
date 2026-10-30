"""Repeatable synthetic baseline data for a database that has already migrated."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from mortgage_pricing.config import Settings, get_settings
from mortgage_pricing.observability.logging import create_logger
from mortgage_pricing.persistence.database import create_database_engine, create_session_factory
from mortgage_pricing.persistence.models import (
    CreationIdempotencyRecord,
    MortgageApplication,
    PricingDecision,
    RequestHistoryEvent,
    RequestVersion,
    Role,
    User,
    UserRoleMembership,
)

SEED_NAMESPACE = uuid5(NAMESPACE_URL, "mortgage-pricing-exception-service/phase-02")


@dataclass(frozen=True)
class SeedUser:
    id: UUID
    login: str
    display_name: str
    roles: tuple[Role, ...]


@dataclass(frozen=True)
class SeedApplication:
    id: UUID
    reference: str
    manager_id: UUID
    loan_amount: Decimal
    property_value: Decimal
    standard_rate_bps: int
    term_months: int


@dataclass(frozen=True)
class SeedResult:
    users_created: int
    applications_created: int


class SeedConflictError(ValueError):
    """Raised when a seed identifier already belongs to different local data."""


USERS = (
    SeedUser(
        id=uuid5(SEED_NAMESPACE, "user:ada.manager"),
        login="ada.manager",
        display_name="Ada Manager (Fictional)",
        roles=(Role.RELATIONSHIP_MANAGER,),
    ),
    SeedUser(
        id=uuid5(SEED_NAMESPACE, "user:blake.reviewer"),
        login="blake.reviewer",
        display_name="Blake Reviewer (Fictional)",
        roles=(Role.REVIEWER,),
    ),
)

RETIRED_USERS = (
    SeedUser(
        id=uuid5(SEED_NAMESPACE, "user:grace.manager"),
        login="grace.manager",
        display_name="Grace Manager (Fictional)",
        roles=(Role.RELATIONSHIP_MANAGER,),
    ),
    SeedUser(
        id=uuid5(SEED_NAMESPACE, "user:casey.reviewer"),
        login="casey.reviewer",
        display_name="Casey Reviewer (Fictional)",
        roles=(Role.REVIEWER,),
    ),
)

APPLICATIONS = (
    SeedApplication(
        id=uuid5(SEED_NAMESPACE, "application:demo-clean"),
        reference="SYN-MORTGAGE-DEMO-CLEAN",
        manager_id=USERS[0].id,
        loan_amount=Decimal("250000.00"),
        property_value=Decimal("320000.00"),
        standard_rate_bps=425,
        term_months=300,
    ),
    SeedApplication(
        id=uuid5(SEED_NAMESPACE, "application:ada"),
        reference="SYN-MORTGAGE-ADA-001",
        manager_id=USERS[0].id,
        loan_amount=Decimal("180000.00"),
        property_value=Decimal("240000.00"),
        standard_rate_bps=475,
        term_months=240,
    ),
    SeedApplication(
        id=uuid5(SEED_NAMESPACE, "application:grace"),
        reference="SYN-MORTGAGE-GRACE-001",
        manager_id=USERS[0].id,
        loan_amount=Decimal("210000.00"),
        property_value=Decimal("300000.00"),
        standard_rate_bps=445,
        term_months=300,
    ),
    SeedApplication(
        id=uuid5(SEED_NAMESPACE, "application:ada-002"),
        reference="SYN-MORTGAGE-ADA-002",
        manager_id=USERS[0].id,
        loan_amount=Decimal("300000.00"),
        property_value=Decimal("400000.00"),
        standard_rate_bps=390,
        term_months=240,
    ),
    SeedApplication(
        id=uuid5(SEED_NAMESPACE, "application:ada-003"),
        reference="SYN-MORTGAGE-ADA-003",
        manager_id=USERS[0].id,
        loan_amount=Decimal("325000.00"),
        property_value=Decimal("450000.00"),
        standard_rate_bps=410,
        term_months=300,
    ),
    SeedApplication(
        id=uuid5(SEED_NAMESPACE, "application:ada-004"),
        reference="SYN-MORTGAGE-ADA-004",
        manager_id=USERS[0].id,
        loan_amount=Decimal("145000.00"),
        property_value=Decimal("225000.00"),
        standard_rate_bps=405,
        term_months=180,
    ),
    SeedApplication(
        id=uuid5(SEED_NAMESPACE, "application:grace-002"),
        reference="SYN-MORTGAGE-GRACE-002",
        manager_id=USERS[0].id,
        loan_amount=Decimal("275000.00"),
        property_value=Decimal("350000.00"),
        standard_rate_bps=420,
        term_months=300,
    ),
    SeedApplication(
        id=uuid5(SEED_NAMESPACE, "application:grace-003"),
        reference="SYN-MORTGAGE-GRACE-003",
        manager_id=USERS[0].id,
        loan_amount=Decimal("400000.00"),
        property_value=Decimal("550000.00"),
        standard_rate_bps=395,
        term_months=240,
    ),
    SeedApplication(
        id=uuid5(SEED_NAMESPACE, "application:grace-004"),
        reference="SYN-MORTGAGE-GRACE-004",
        manager_id=USERS[0].id,
        loan_amount=Decimal("220000.00"),
        property_value=Decimal("280000.00"),
        standard_rate_bps=430,
        term_months=360,
    ),
    SeedApplication(
        id=uuid5(SEED_NAMESPACE, "application:grace-005"),
        reference="SYN-MORTGAGE-GRACE-005",
        manager_id=USERS[0].id,
        loan_amount=Decimal("195000.00"),
        property_value=Decimal("260000.00"),
        standard_rate_bps=415,
        term_months=240,
    ),
)


def _existing_user(session: Session, definition: SeedUser) -> User | None:
    by_id = session.get(User, definition.id)
    by_login = session.scalar(select(User).where(User.login == definition.login))
    if by_id is not None and by_login is not None and by_id.id != by_login.id:
        raise SeedConflictError("Seed user identifier conflicts with existing data")
    return by_id or by_login


def _ensure_user(session: Session, definition: SeedUser) -> bool:
    existing = _existing_user(session, definition)
    if existing is None:
        session.add(
            User(
                id=definition.id,
                login=definition.login,
                display_name=definition.display_name,
                role_memberships=[UserRoleMembership(role=role) for role in definition.roles],
            )
        )
        return True
    if existing.id != definition.id or existing.display_name != definition.display_name:
        raise SeedConflictError("Seed user identifier conflicts with existing data")
    actual_roles = {membership.role for membership in existing.role_memberships}
    if actual_roles != set(definition.roles):
        raise SeedConflictError("Seed user roles conflict with existing data")
    return False


def _consolidate_demo_users(session: Session) -> None:
    """Transfer legacy demo ownership, removing only unchanged, unused seed users."""
    history_actors = (
        RequestVersion.submitted_by_id,
        PricingDecision.reviewer_id,
        RequestHistoryEvent.actor_id,
        CreationIdempotencyRecord.caller_id,
    )
    for definition in RETIRED_USERS:
        existing = _existing_user(session, definition)
        if existing is None:
            continue
        if (
            existing.id != definition.id
            or existing.login != definition.login
            or existing.display_name != definition.display_name
            or {membership.role for membership in existing.role_memberships}
            != set(definition.roles)
        ):
            raise SeedConflictError("Retired demo user conflicts with existing data")
        if any(
            session.scalar(select(actor).where(actor == existing.id).limit(1)) is not None
            for actor in history_actors
        ):
            raise SeedConflictError("Retired demo users with history must be preserved")
        if Role.RELATIONSHIP_MANAGER in definition.roles:
            session.execute(
                update(MortgageApplication)
                .where(MortgageApplication.manager_id == existing.id)
                .values(manager_id=USERS[0].id)
            )
        session.delete(existing)
        session.flush()


def _ensure_application(session: Session, definition: SeedApplication) -> bool:
    by_id = session.get(MortgageApplication, definition.id)
    by_reference = session.scalar(
        select(MortgageApplication).where(MortgageApplication.reference == definition.reference)
    )
    if by_id is not None and by_reference is not None and by_id.id != by_reference.id:
        raise SeedConflictError("Seed application identifier conflicts with existing data")
    existing = by_id or by_reference
    if existing is None:
        session.add(
            MortgageApplication(
                id=definition.id,
                reference=definition.reference,
                manager_id=definition.manager_id,
                loan_amount=definition.loan_amount,
                property_value=definition.property_value,
                standard_rate_bps=definition.standard_rate_bps,
                term_months=definition.term_months,
            )
        )
        return True
    if existing.id != definition.id or existing.manager_id != definition.manager_id:
        raise SeedConflictError("Seed application identifier conflicts with existing data")
    for field in ("loan_amount", "property_value", "standard_rate_bps", "term_months"):
        if getattr(existing, field) is None:
            setattr(existing, field, getattr(definition, field))
    return False


def seed_database(settings: Settings) -> SeedResult:
    """Reconcile the demo identities and insert missing fixed synthetic records."""
    engine = create_database_engine(settings)
    sessions = create_session_factory(engine)
    try:
        with sessions.begin() as session:
            users_created = sum(_ensure_user(session, definition) for definition in USERS)
            session.flush()
            _consolidate_demo_users(session)
            applications_created = sum(
                _ensure_application(session, definition) for definition in APPLICATIONS
            )
        return SeedResult(users_created=users_created, applications_created=applications_created)
    finally:
        engine.dispose()


def main() -> int:
    """Run the seed command with normal settings and safe operational output."""
    settings = get_settings()
    logger = create_logger(settings.log_level)
    try:
        result = seed_database(settings)
    except (SeedConflictError, SQLAlchemyError):
        logger.exception("database_seed_failed", extra={"outcome": "failure"})
        return 1
    logger.info(
        "database_seed_completed",
        extra={"outcome": "success", "users_created": result.users_created},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
