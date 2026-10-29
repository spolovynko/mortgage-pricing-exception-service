"""Demo identity and read-only lookup contracts against migrated synthetic data."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from mortgage_pricing.config import Settings
from mortgage_pricing.main import create_app
from mortgage_pricing.seed import APPLICATIONS, USERS, seed_database

ROOT = Path(__file__).resolve().parents[1]


def test_demo_identity_and_lookups(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        demo_identity_mode="header",
        database_url=f"sqlite:///{(tmp_path / 'lookup.db').as_posix()}",
    )
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["settings"] = settings
    command.upgrade(config, "head")
    seed_database(settings)

    with TestClient(create_app(settings)) as client:
        missing = client.get("/demo/users", headers={"X-Correlation-ID": "identity-test"})
        assert missing.status_code == 401
        assert missing.json() == {
            "error": {
                "code": "demo_identity_required",
                "message": "A valid X-Demo-User login is required.",
            },
            "correlation_id": "identity-test",
        }
        assert client.get("/demo/users", headers={"X-Demo-User": "unknown"}).status_code == 401
        for user in (USERS[0], USERS[2]):
            headers = {"X-Demo-User": user.login}
            users = client.get("/demo/users", headers=headers)
            applications = client.get("/demo/applications", headers=headers)
            assert users.status_code == applications.status_code == 200
            assert [row["login"] for row in users.json()] == sorted(u.login for u in USERS)
            assert [row["reference"] for row in applications.json()] == sorted(
                a.reference for a in APPLICATIONS
            )
        paths = client.get("/openapi.json").json()["paths"]
        assert "401" in paths["/demo/users"]["get"]["responses"]
        assert "503" in paths["/demo/applications"]["get"]["responses"]


def test_disabled_demo_identity_does_not_touch_database(tmp_path: Path) -> None:
    path = tmp_path / "absent.db"
    settings = Settings(_env_file=None, database_url=f"sqlite:///{path.as_posix()}")
    with TestClient(create_app(settings)) as client:
        response = client.get("/demo/users", headers={"X-Demo-User": "ada.manager"})
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "demo_identity_disabled"
    assert not path.exists()
