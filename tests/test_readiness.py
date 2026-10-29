"""Core readiness reflects migrated storage while liveness stays independent."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from mortgage_pricing.config import Settings
from mortgage_pricing.main import create_app

ROOT = Path(__file__).resolve().parents[1]


def test_missing_database_is_not_created_and_liveness_works(tmp_path: Path) -> None:
    path = tmp_path / "missing.db"
    app = create_app(Settings(_env_file=None, database_url=f"sqlite:///{path.as_posix()}"))
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        response = client.get("/ready", headers={"X-Correlation-ID": "ready-1"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "database_unavailable"
    assert response.json()["correlation_id"] == "ready-1"
    assert not path.exists()


def test_migrated_database_is_ready_and_unmigrated_database_is_not(tmp_path: Path) -> None:
    path = tmp_path / "ready.db"
    settings = Settings(_env_file=None, database_url=f"sqlite:///{path.as_posix()}")
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["settings"] = settings
    command.upgrade(config, "head")
    with TestClient(create_app(settings)) as client:
        assert client.get("/ready").json() == {"status": "ready"}
    other = tmp_path / "unmigrated.db"
    other.touch()
    with TestClient(
        create_app(Settings(_env_file=None, database_url=f"sqlite:///{other.as_posix()}"))
    ) as client:
        assert client.get("/ready").status_code == 503
        assert client.get("/health").status_code == 200


def test_read_only_database_is_not_ready(tmp_path: Path) -> None:
    path = tmp_path / "read-only.db"
    writable_settings = Settings(_env_file=None, database_url=f"sqlite:///{path.as_posix()}")
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["settings"] = writable_settings
    command.upgrade(config, "head")

    read_only_url = f"sqlite:///file:{path.as_posix()}?mode=ro&uri=true"
    with TestClient(create_app(Settings(_env_file=None, database_url=read_only_url))) as client:
        assert client.get("/ready").status_code == 503
        assert client.get("/health").status_code == 200
