"""Structured context belongs to the exact request version that was submitted."""

from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from mortgage_pricing.config import Settings
from mortgage_pricing.domain.request_context import RequestContext
from mortgage_pricing.main import create_app
from mortgage_pricing.seed import APPLICATIONS, seed_database

ROOT = Path(__file__).resolve().parents[1]
MANAGER = {"X-Demo-User": "ada.manager"}


def prepared_client(tmp_path: Path) -> TestClient:
    settings = Settings(
        _env_file=None,
        demo_identity_mode="header",
        database_url=f"sqlite:///{(tmp_path / 'context-api.db').as_posix()}",
    )
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["settings"] = settings
    command.upgrade(config, "head")
    seed_database(settings)
    return TestClient(create_app(settings))


def sample_context() -> dict[str, object]:
    return {
        "application": {
            "purpose": "purchase",
            "rate_type": "fixed",
            "loan_amount": "250000.00",
            "property_value": "320000.00",
            "currency_code": "EUR",
            "term_months": 300,
            "standard_rate_bps": 425,
        },
        "reason_category": "competitive_offer",
        "competitor_offer": {"rate_bps": 390, "expires_on": "2027-01-31"},
    }


def test_amounts_serialize_as_fixed_decimal_strings() -> None:
    context = sample_context() | {
        "application": sample_context()["application"]
        | {"loan_amount": "1e2", "property_value": "2e2"}
    }

    result = RequestContext.model_validate(context).model_dump(mode="json")

    assert result["application"]["loan_amount"] == "100.00"
    assert result["application"]["property_value"] == "200.00"


def test_create_and_revision_return_immutable_version_context(tmp_path: Path) -> None:
    with prepared_client(tmp_path) as client:
        payload = {
            "application_id": str(APPLICATIONS[0].id),
            "discount_bps": 25,
            "reason": "Synthetic competition example",
            "context": sample_context(),
        }
        headers = {**MANAGER, "Idempotency-Key": str(uuid4())}
        created = client.post("/requests", headers=headers, json=payload)
        assert created.status_code == 201
        request_id = created.json()["request_id"]

        detail = client.get(f"/requests/{request_id}", headers=MANAGER).json()
        assert detail["current_version"]["context"] == sample_context()
        replay = client.post("/requests", headers=headers, json=payload)
        assert replay.status_code == 200 and replay.json()["replayed"] is True
        changed = client.post(
            "/requests",
            headers=headers,
            json=payload | {"context": sample_context() | {"reason_category": "retention"}},
        )
        assert changed.status_code == 409
        assert changed.json()["error"]["code"] == "idempotency_conflict"

        revision_context = sample_context() | {
            "application": sample_context()["application"] | {"loan_amount": "240000.00"},
            "reason_category": "retention",
            "competitor_offer": None,
        }
        revised = client.post(
            f"/requests/{request_id}/revisions",
            headers=MANAGER,
            json={
                "expected_version": 1,
                "discount_bps": 30,
                "reason": "Synthetic revised terms",
                "context": revision_context,
            },
        )
        assert revised.status_code == 201
        current = client.get(f"/requests/{request_id}", headers=MANAGER).json()
        assert current["current_version"]["context"] == revision_context
        history = client.get(f"/requests/{request_id}/history", headers=MANAGER).json()
        assert history[0]["version"]["context"] == sample_context()
        assert history[1]["version"]["context"] == revision_context


def test_context_rejects_unknown_fields_and_invalid_values(tmp_path: Path) -> None:
    with prepared_client(tmp_path) as client:
        payload = {
            "application_id": str(APPLICATIONS[0].id),
            "discount_bps": 25,
            "reason": "Synthetic context validation",
            "context": sample_context(),
        }
        headers = {**MANAGER, "Idempotency-Key": "context-invalid"}
        invalid_cases = (
            payload | {"context": sample_context() | {"unreviewed_field": "value"}},
            payload | {"context": sample_context() | {"reason_category": "creditworthy"}},
            payload
            | {
                "context": sample_context()
                | {"application": sample_context()["application"] | {"currency_code": "usd"}}
            },
        )
        for invalid in invalid_cases:
            response = client.post("/requests", headers=headers, json=invalid)
            assert response.status_code == 422
