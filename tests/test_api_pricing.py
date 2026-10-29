"""Current approved pricing across pending, decided, and revised versions."""

from pathlib import Path
from uuid import uuid4

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from mortgage_pricing.config import Settings
from mortgage_pricing.main import create_app
from mortgage_pricing.seed import APPLICATIONS, seed_database

ROOT = Path(__file__).resolve().parents[1]
MANAGER = {"X-Demo-User": "ada.manager"}
REVIEWER = {"X-Demo-User": "blake.reviewer"}


def test_only_current_approval_is_usable(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        demo_identity_mode="header",
        database_url=f"sqlite:///{(tmp_path / 'pricing.db').as_posix()}",
    )
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["settings"] = settings
    command.upgrade(config, "head")
    seed_database(settings)
    app_id = APPLICATIONS[0].id
    pricing_url = f"/applications/{app_id}/approved-discount"
    with TestClient(create_app(settings)) as client:
        assert client.get(pricing_url, headers=MANAGER).json() == {
            "application_id": str(app_id),
            "status": "none",
        }
        assert (
            client.get(f"/applications/{uuid4()}/approved-discount", headers=REVIEWER).status_code
            == 404
        )
        created = client.post(
            "/requests",
            headers={**MANAGER, "Idempotency-Key": "pricing-1"},
            json={"application_id": str(app_id), "discount_bps": 25, "reason": "Synthetic"},
        )
        assert created.status_code == 201
        request_id = created.json()["request_id"]
        assert client.get(pricing_url, headers=REVIEWER).json()["status"] == "none"
        assert (
            client.post(
                f"/requests/{request_id}/decisions",
                headers=REVIEWER,
                json={"expected_version": 1, "outcome": "approved"},
            ).status_code
            == 200
        )
        assert client.get(pricing_url, headers=MANAGER).json() == {
            "application_id": str(app_id),
            "status": "approved",
            "request_id": request_id,
            "version_number": 1,
            "discount_bps": 25,
        }
        assert (
            client.post(
                f"/requests/{request_id}/revisions",
                headers=MANAGER,
                json={"expected_version": 1, "discount_bps": 40, "reason": "Synthetic revision"},
            ).status_code
            == 201
        )
        assert client.get(pricing_url, headers=REVIEWER).json()["status"] == "none"
        assert (
            client.post(
                f"/requests/{request_id}/decisions",
                headers=REVIEWER,
                json={"expected_version": 2, "outcome": "declined"},
            ).status_code
            == 200
        )
        assert client.get(pricing_url, headers=REVIEWER).json()["status"] == "none"
        assert (
            client.post(
                f"/requests/{request_id}/revisions",
                headers=MANAGER,
                json={"expected_version": 2, "discount_bps": 50, "reason": "Synthetic revision 3"},
            ).status_code
            == 201
        )
        assert (
            client.post(
                f"/requests/{request_id}/decisions",
                headers=REVIEWER,
                json={"expected_version": 3, "outcome": "approved"},
            ).status_code
            == 200
        )
        assert client.get(pricing_url, headers=REVIEWER).json()["discount_bps"] == 50
        assert client.get(pricing_url, headers=REVIEWER).json()["version_number"] == 3
