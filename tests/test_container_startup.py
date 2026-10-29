"""Focused checks for safe container database preparation."""

from pathlib import Path

import pytest
from sqlalchemy import func, select

from mortgage_pricing.config import Settings
from mortgage_pricing.container_startup import prepare_database, sqlite_storage_path
from mortgage_pricing.persistence.database import create_database_engine, create_session_factory
from mortgage_pricing.persistence.models import User


def test_prepare_database_migrates_and_seeds_repeatably(tmp_path: Path) -> None:
    database_path = tmp_path / "nested" / "container.db"
    settings = Settings(_env_file=None, database_url=f"sqlite:///{database_path.as_posix()}")

    first = prepare_database(settings)
    second = prepare_database(settings)

    assert first.users_created > 0
    assert second.users_created == 0
    assert second.applications_created == 0
    engine = create_database_engine(settings)
    try:
        with create_session_factory(engine)() as session:
            assert session.scalar(select(func.count()).select_from(User)) == first.users_created
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    "database_url",
    ["sqlite:///:memory:", "sqlite:///file:data/read-only.db?mode=ro&uri=true"],
)
def test_container_startup_rejects_non_persistent_or_read_only_storage(
    database_url: str,
) -> None:
    settings = Settings(_env_file=None, database_url=database_url)

    with pytest.raises(ValueError):
        sqlite_storage_path(settings)
