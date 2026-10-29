"""Creation HTTP behavior against migrated, seeded file-backed SQLite."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from mortgage_pricing.config import Settings
from mortgage_pricing.main import create_app
from mortgage_pricing.persistence.database import create_session_factory
from mortgage_pricing.persistence.models import (
    CreationIdempotencyRecord,
    PricingRequest,
    RequestHistoryEvent,
    RequestVersion,
)
from mortgage_pricing.seed import APPLICATIONS, seed_database

ROOT = Path(__file__).resolve().parents[1]
MANAGER = {"X-Demo-User": "ada.manager"}


def prepared_client(tmp_path: Path) -> TestClient:
    settings = Settings(
        _env_file=None,
        demo_identity_mode="header",
        database_url=f"sqlite:///{(tmp_path / 'api-create.db').as_posix()}",
    )
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["settings"] = settings
    command.upgrade(config, "head")
    seed_database(settings)
    return TestClient(create_app(settings))


def payload(application_index: int = 0) -> dict[str, object]:
    return {
        "application_id": str(APPLICATIONS[application_index].id),
        "discount_bps": 25,
        "reason": "Synthetic customer retention request",
    }


def test_create_replay_conflicts_and_permissions(tmp_path: Path) -> None:
    with prepared_client(tmp_path) as client:
        headers = {**MANAGER, "Idempotency-Key": "create-1"}
        created = client.post("/requests", headers=headers, json=payload())
        assert created.status_code == 201
        assert created.json()["version_number"] == 1
        assert created.json()["replayed"] is False
        replay = client.post("/requests", headers=headers, json=payload())
        assert replay.status_code == 200
        assert replay.json() == {**created.json(), "replayed": True}
        changed = client.post("/requests", headers=headers, json={**payload(), "discount_bps": 40})
        assert changed.status_code == 409
        assert changed.json()["error"]["code"] == "idempotency_conflict"
        new_key = client.post(
            "/requests", headers={**MANAGER, "Idempotency-Key": "create-2"}, json=payload()
        )
        assert new_key.status_code == 409
        assert new_key.json()["error"]["code"] == "request_exists"
        assert (
            client.post(
                "/requests",
                headers={**MANAGER, "Idempotency-Key": "missing"},
                json={**payload(), "application_id": str(uuid4())},
            ).status_code
            == 404
        )
        assert (
            client.post(
                "/requests",
                headers={"X-Demo-User": "blake.reviewer", "Idempotency-Key": "reviewer"},
                json=payload(1),
            ).status_code
            == 403
        )
        assert (
            client.post(
                "/requests",
                headers={**MANAGER, "Idempotency-Key": "other-owner"},
                json=payload(2),
            ).status_code
            == 403
        )
        assert client.post("/requests", headers=MANAGER, json=payload(1)).status_code == 422
        assert (
            client.post(
                "/requests",
                headers={**MANAGER, "Idempotency-Key": "invalid"},
                json={**payload(1), "discount_bps": True},
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/requests",
                headers={**MANAGER, "Idempotency-Key": "invalid"},
                json={**payload(1), "reason": "   "},
            ).status_code
            == 422
        )
        with create_session_factory(client.app.state.database_engine)() as session:
            for model in (
                PricingRequest,
                RequestVersion,
                RequestHistoryEvent,
                CreationIdempotencyRecord,
            ):
                assert session.scalar(select(func.count()).select_from(model)) == 1
        spec = client.get("/openapi.json").json()["paths"]["/requests"]["post"]
        assert "Idempotency-Key" in str(spec["parameters"])
        assert "409" in spec["responses"]


def test_competing_same_key_replays_once(tmp_path: Path) -> None:
    with prepared_client(tmp_path) as client:
        headers = {**MANAGER, "Idempotency-Key": "compete-1"}

        def attempt() -> tuple[int, dict]:
            response = client.post("/requests", headers=headers, json=payload())
            return response.status_code, response.json()

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _: attempt(), range(2)))
        assert sorted(status for status, _ in outcomes) == [200, 201]
        assert outcomes[0][1]["request_id"] == outcomes[1][1]["request_id"]
        with create_session_factory(client.app.state.database_engine)() as session:
            assert session.scalar(select(func.count()).select_from(PricingRequest)) == 1
            assert session.scalar(select(func.count()).select_from(RequestHistoryEvent)) == 1


def test_competing_different_keys_conflict_without_duplicate(tmp_path: Path) -> None:
    with prepared_client(tmp_path) as client:

        def attempt(key: str) -> tuple[int, dict]:
            response = client.post(
                "/requests",
                headers={**MANAGER, "Idempotency-Key": key},
                json=payload(),
            )
            return response.status_code, response.json()

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(attempt, ("first-key", "second-key")))
        assert sorted(status for status, _ in outcomes) == [201, 409]
        assert next(body for status, body in outcomes if status == 409)["error"]["code"] == (
            "request_exists"
        )
        with create_session_factory(client.app.state.database_engine)() as session:
            for model in (
                PricingRequest,
                RequestVersion,
                RequestHistoryEvent,
                CreationIdempotencyRecord,
            ):
                assert session.scalar(select(func.count()).select_from(model)) == 1
