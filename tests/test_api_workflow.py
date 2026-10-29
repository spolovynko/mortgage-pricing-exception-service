"""HTTP workflow against migrated synthetic SQLite with separate request sessions."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import UUID

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from mortgage_pricing.config import Settings
from mortgage_pricing.main import create_app
from mortgage_pricing.persistence.database import create_session_factory
from mortgage_pricing.persistence.models import (
    PricingDecision,
    PricingRequest,
    RequestHistoryEvent,
    RequestVersion,
    Role,
    UserRoleMembership,
)
from mortgage_pricing.seed import APPLICATIONS, USERS, seed_database

ROOT = Path(__file__).resolve().parents[1]
MANAGER = {"X-Demo-User": "ada.manager"}
REVIEWER = {"X-Demo-User": "blake.reviewer"}


def prepared_client(tmp_path: Path) -> TestClient:
    settings = Settings(
        _env_file=None,
        demo_identity_mode="header",
        database_url=f"sqlite:///{(tmp_path / 'workflow.db').as_posix()}",
    )
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["settings"] = settings
    command.upgrade(config, "head")
    seed_database(settings)
    return TestClient(create_app(settings))


def create(client: TestClient, application_index: int = 0) -> str:
    response = client.post(
        "/requests",
        headers={**MANAGER, "Idempotency-Key": f"workflow-{application_index}"},
        json={
            "application_id": str(APPLICATIONS[application_index].id),
            "discount_bps": 25,
            "reason": "Synthetic original terms",
        },
    )
    assert response.status_code == 201
    return response.json()["request_id"]


def count(client: TestClient, model: type) -> int:
    with create_session_factory(client.app.state.database_engine)() as session:
        return session.scalar(select(func.count()).select_from(model)) or 0


def test_revision_and_exact_version_decision(tmp_path: Path) -> None:
    with prepared_client(tmp_path) as client:
        request_id = create(client)
        url = f"/requests/{request_id}"
        assert (
            client.post(
                f"{url}/decisions",
                headers=MANAGER,
                json={"expected_version": 1, "outcome": "approved"},
            ).status_code
            == 403
        )
        approved = client.post(
            f"{url}/decisions",
            headers=REVIEWER,
            json={"expected_version": 1, "outcome": "approved"},
        )
        assert approved.status_code == 200
        assert approved.json()["outcome"] == "approved"
        duplicate = client.post(
            f"{url}/decisions",
            headers=REVIEWER,
            json={"expected_version": 1, "outcome": "declined"},
        )
        assert duplicate.status_code == 409
        assert duplicate.json()["error"]["code"] == "already_decided"
        revised = client.post(
            f"{url}/revisions",
            headers=MANAGER,
            json={"expected_version": 1, "discount_bps": 40, "reason": "Synthetic revised terms"},
        )
        assert revised.status_code == 201
        assert revised.json()["version_number"] == 2
        assert (
            client.post(
                f"{url}/revisions",
                headers=REVIEWER,
                json={"expected_version": 2, "discount_bps": 50, "reason": "Not permitted"},
            ).status_code
            == 403
        )
        assert (
            client.post(
                f"{url}/revisions",
                headers=MANAGER,
                json={"expected_version": 1, "discount_bps": 50, "reason": "Stale"},
            ).status_code
            == 409
        )
        stale = client.post(
            f"{url}/decisions",
            headers=REVIEWER,
            json={"expected_version": 1, "outcome": "approved"},
        )
        assert stale.status_code == 409
        assert stale.json()["error"]["code"] == "stale_version"
        details = client.get(url, headers=REVIEWER).json()
        assert details["current_version"]["discount_bps"] == 40
        assert details["status"] == "pending"
        history = client.get(f"{url}/history", headers=MANAGER).json()
        assert [event["event_type"] for event in history] == ["created", "approved", "revised"]
        assert count(client, PricingDecision) == 1
        assert count(client, RequestHistoryEvent) == 3


def test_self_review_and_invalid_decision_leave_no_writes(tmp_path: Path) -> None:
    with prepared_client(tmp_path) as client:
        request_id = create(client)
        sessions = create_session_factory(client.app.state.database_engine)
        with sessions.begin() as session:
            session.add(UserRoleMembership(user_id=USERS[0].id, role=Role.REVIEWER))
        url = f"/requests/{request_id}/decisions"
        self_review = client.post(
            url, headers=MANAGER, json={"expected_version": 1, "outcome": "approved"}
        )
        assert self_review.status_code == 403
        assert self_review.json()["error"]["code"] == "self_review"
        assert (
            client.post(
                url,
                headers=REVIEWER,
                json={"expected_version": 1, "outcome": "approved", "discount_bps": 90},
            ).status_code
            == 422
        )
        assert (
            client.post(
                url,
                headers=REVIEWER,
                json={"expected_version": 1, "outcome": "changed"},
            ).status_code
            == 422
        )
        assert count(client, PricingDecision) == 0
        assert count(client, RequestHistoryEvent) == 1


def test_competing_decisions_and_revision_decision_race(tmp_path: Path) -> None:
    with prepared_client(tmp_path) as client:
        request_id = create(client)
        url = f"/requests/{request_id}"

        def decide(outcome: str) -> int:
            return client.post(
                f"{url}/decisions",
                headers=REVIEWER,
                json={"expected_version": 1, "outcome": outcome},
            ).status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(decide, ("approved", "declined")))
        assert sorted(statuses) == [200, 409]
        assert count(client, PricingDecision) == 1
        assert count(client, RequestHistoryEvent) == 2

        second_id = create(client, 1)
        second_url = f"/requests/{second_id}"

        def revise() -> int:
            return client.post(
                f"{second_url}/revisions",
                headers=MANAGER,
                json={"expected_version": 1, "discount_bps": 40, "reason": "Synthetic revision"},
            ).status_code

        def decide_second() -> int:
            return client.post(
                f"{second_url}/decisions",
                headers=REVIEWER,
                json={"expected_version": 1, "outcome": "approved"},
            ).status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            revision_future = pool.submit(revise)
            decision_future = pool.submit(decide_second)
            revision_status, decision_status = revision_future.result(), decision_future.result()
        assert revision_status == 201
        assert decision_status in (200, 409)
        with create_session_factory(client.app.state.database_engine)() as session:
            second = session.get(PricingRequest, UUID(second_id))
            assert second.current_version_number == 2
            assert session.get(RequestVersion, (second.id, 2)).discount_bps == 40
            decisions = session.scalars(
                select(PricingDecision).where(PricingDecision.request_id == second.id)
            ).all()
            assert len(decisions) == (1 if decision_status == 200 else 0)
            assert all(decision.version_number == 1 for decision in decisions)
        assert client.get(second_url, headers=REVIEWER).json()["status"] == "pending"
