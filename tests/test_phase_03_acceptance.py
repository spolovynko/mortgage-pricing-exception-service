"""Remaining HTTP acceptance paths with migrated, isolated synthetic storage."""

from collections.abc import Iterator
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from mortgage_pricing.config import Settings
from mortgage_pricing.main import create_app
from mortgage_pricing.persistence.database import create_session_factory
from mortgage_pricing.persistence.operations import OperationError, create_request
from mortgage_pricing.seed import APPLICATIONS, USERS, seed_database

ROOT = Path(__file__).resolve().parents[1]
MANAGER = {"X-Demo-User": "ada.manager"}
REVIEWER = {"X-Demo-User": "blake.reviewer"}


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    settings = Settings(
        _env_file=None,
        demo_identity_mode="header",
        database_url=f"sqlite:///{(tmp_path / 'acceptance.db').as_posix()}",
    )
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["settings"] = settings
    command.upgrade(config, "head")
    seed_database(settings)
    with TestClient(create_app(settings)) as connected:
        yield connected


def test_read_filters_history_and_original_retry_after_decision_and_revision(
    client: TestClient,
) -> None:
    assert client.get("/requests", headers=REVIEWER).json() == []
    terms = {
        "application_id": str(APPLICATIONS[0].id),
        "discount_bps": 25,
        "reason": "Exact terms ",
    }
    headers = {**MANAGER, "Idempotency-Key": "original"}
    created = client.post("/requests", headers=headers, json=terms)
    assert created.status_code == 201
    request_id = created.json()["request_id"]
    url = f"/requests/{request_id}"
    assert client.get(url, headers=REVIEWER).json()["current_version"]["reason"] == terms["reason"]
    assert (
        client.post(
            f"{url}/decisions",
            headers=REVIEWER,
            json={"expected_version": 1, "outcome": "approved"},
        ).status_code
        == 200
    )
    replay = client.post("/requests", headers=headers, json=terms)
    assert replay.status_code == 200
    assert replay.json() == {
        **created.json(),
        "replayed": True,
    }
    assert (
        client.post(
            f"{url}/revisions",
            headers=MANAGER,
            json={"expected_version": 1, "discount_bps": 40, "reason": "New terms"},
        ).status_code
        == 201
    )
    replay = client.post("/requests", headers=headers, json=terms)
    assert replay.status_code == 200
    assert replay.json() == {
        **created.json(),
        "replayed": True,
    }
    pricing_url = f"/applications/{APPLICATIONS[0].id}/approved-discount"
    assert client.get(pricing_url, headers=REVIEWER).json()["status"] == "none"
    assert (
        client.post(
            f"{url}/decisions",
            headers=REVIEWER,
            json={"expected_version": 2, "outcome": "approved"},
        ).status_code
        == 200
    )
    assert client.get(pricing_url, headers=REVIEWER).json() == {
        "application_id": str(APPLICATIONS[0].id),
        "status": "approved",
        "request_id": request_id,
        "version_number": 2,
        "discount_bps": 40,
    }
    assert (
        client.post(
            f"{url}/revisions",
            headers=MANAGER,
            json={"expected_version": 2, "discount_bps": 50, "reason": "Final synthetic terms"},
        ).status_code
        == 201
    )
    assert (
        client.post(
            f"{url}/decisions",
            headers=REVIEWER,
            json={"expected_version": 3, "outcome": "declined"},
        ).status_code
        == 200
    )
    for login in ("ada.manager", "grace.manager", "blake.reviewer"):
        actor = {"X-Demo-User": login}
        rows = client.get("/requests", headers=actor, params={"status": "declined"}).json()
        assert [row["request_id"] for row in rows] == [request_id]
        assert rows[0]["current_version_number"] == 3
        assert client.get("/requests", headers=actor, params={"status": "approved"}).json() == []
        assert (
            client.get(
                "/requests", headers=actor, params={"application_id": str(APPLICATIONS[1].id)}
            ).json()
            == []
        )
        assert (
            len(
                client.get(
                    "/requests", headers=actor, params={"application_id": terms["application_id"]}
                ).json()
            )
            == 1
        )
    history = client.get(f"{url}/history", headers=REVIEWER).json()
    assert [row["event_type"] for row in history] == [
        "created",
        "approved",
        "revised",
        "approved",
        "revised",
        "declined",
    ]
    assert history == sorted(history, key=lambda row: (row["occurred_at"], row["event_id"]))
    assert history[0]["version"]["discount_bps"] == 25
    assert history[-1]["version"]["discount_bps"] == 50
    decision = history[-1]["version"]["decision"]
    assert decision["reviewer_id"] == str(USERS[2].id)
    assert decision["decided_at"].endswith("Z")
    assert (
        client.get(f"/applications/{APPLICATIONS[0].id}/approved-discount", headers=MANAGER).json()[
            "status"
        ]
        == "none"
    )


def test_read_errors_and_openapi_envelopes(client: TestClient) -> None:
    for path in (f"/requests/{uuid4()}", f"/requests/{uuid4()}/history"):
        response = client.get(path, headers={**REVIEWER, "X-Correlation-ID": "missing-resource"})
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "request_not_found"
        assert response.json()["correlation_id"] == response.headers["X-Correlation-ID"]
    for path in ("/requests?status=unknown", "/requests?application_id=bad", "/requests/bad"):
        response = client.get(path, headers=REVIEWER)
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "validation_error"
    paths = client.get("/openapi.json").json()["paths"]
    for path in (
        "/requests",
        "/requests/{request_id}",
        "/applications/{application_id}/approved-discount",
    ):
        schema = paths[path]["get"]["responses"]["422"]["content"]["application/json"]["schema"]
        assert schema["$ref"].endswith("/ErrorResponse")


def test_integer_storage_limit_is_validation_not_server_failure(client: TestClient) -> None:
    terms = {
        "application_id": str(APPLICATIONS[0].id),
        "discount_bps": 2**63,
        "reason": "Synthetic",
    }
    response = client.post(
        "/requests", headers={**MANAGER, "Idempotency-Key": "too-large"}, json=terms
    )
    assert response.status_code == 422
    assert client.get("/requests", headers=MANAGER).json() == []
    with pytest.raises(OperationError, match="invalid_terms"):
        create_request(
            create_session_factory(client.app.state.database_engine),
            caller_id=USERS[0].id,
            application_id=UUID(terms["application_id"]),
            discount_bps=2**63,
            reason="Synthetic",
            idempotency_key="too-large",
        )
    terms["discount_bps"] = 2**63 - 1
    created = client.post(
        "/requests", headers={**MANAGER, "Idempotency-Key": "storage-max"}, json=terms
    )
    assert created.status_code == 201
    request_id = created.json()["request_id"]
    assert (
        client.post(
            f"/requests/{request_id}/revisions",
            headers=MANAGER,
            json={"expected_version": 1, "discount_bps": 2**63, "reason": "Synthetic"},
        ).status_code
        == 422
    )
    assert (
        client.get(f"/requests/{request_id}", headers=MANAGER).json()["current_version_number"] == 1
    )
