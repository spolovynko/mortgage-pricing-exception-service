"""Demo identity and small read-only lookup routes for the business API."""

from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.engine import make_url

from mortgage_pricing.errors import ErrorResponse, error_response
from mortgage_pricing.persistence.database import create_session_factory
from mortgage_pricing.persistence.models import MortgageApplication, Role, User

router = APIRouter(
    tags=["demo lookups"],
    responses={
        401: {
            "model": ErrorResponse,
            "description": "Missing or unknown demo identity",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "demo_identity_required",
                            "message": "A valid X-Demo-User login is required.",
                        },
                        "correlation_id": "demo-123",
                    }
                }
            },
        },
        403: {"model": ErrorResponse, "description": "No internal role"},
        422: {"model": ErrorResponse, "description": "Invalid header input"},
        503: {"model": ErrorResponse, "description": "Demo identity or storage unavailable"},
    },
)


class DemoUser(BaseModel):
    id: UUID
    login: str
    display_name: str
    roles: list[Role]


class DemoApplication(BaseModel):
    id: UUID
    reference: str
    manager_id: UUID


def acting_user(request: Request, x_demo_user: str | None = Header(default=None)) -> UUID:
    """Resolve a login from the explicitly enabled, non-authenticating demo header."""
    if request.app.state.settings.demo_identity_mode != "header":
        raise DemoError(503, "demo_identity_disabled", "Demo identity is disabled.")
    if not x_demo_user or len(x_demo_user) > 64:
        raise DemoError(401, "demo_identity_required", "A valid X-Demo-User login is required.")
    url = make_url(request.app.state.settings.database_url)
    if url.database != ":memory:" and not Path(url.database).is_file():
        raise DemoError(503, "database_unavailable", "Database is unavailable.")
    with create_session_factory(request.app.state.database_engine)() as session:
        user = session.scalar(select(User).where(User.login == x_demo_user))
        if user is None:
            raise DemoError(401, "demo_identity_unknown", "Demo user was not found.")
        if not any(
            m.role in (Role.RELATIONSHIP_MANAGER, Role.REVIEWER) for m in user.role_memberships
        ):
            raise DemoError(403, "forbidden", "The user has no internal role.")
        return user.id


ActorId = Annotated[UUID, Depends(acting_user)]


class DemoError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        self.status, self.code, self.message = status, code, message


async def demo_error_handler(request: Request, exc: DemoError):
    return error_response(exc.status, exc.code, exc.message, request.state.correlation_id)


@router.get("/demo/users", response_model=list[DemoUser], summary="List fictional demo identities")
def demo_users(request: Request, _actor: ActorId) -> list[DemoUser]:
    with create_session_factory(request.app.state.database_engine)() as session:
        users = session.scalars(select(User).order_by(User.login)).all()
        return [
            DemoUser(
                id=user.id,
                login=user.login,
                display_name=user.display_name,
                roles=sorted((m.role for m in user.role_memberships), key=str),
            )
            for user in users
        ]


@router.get(
    "/demo/applications",
    response_model=list[DemoApplication],
    summary="List fictional demo applications",
)
def demo_applications(request: Request, _actor: ActorId) -> list[DemoApplication]:
    with create_session_factory(request.app.state.database_engine)() as session:
        applications = session.scalars(
            select(MortgageApplication).order_by(MortgageApplication.reference)
        ).all()
        return [
            DemoApplication(id=app.id, reference=app.reference, manager_id=app.manager_id)
            for app in applications
        ]
