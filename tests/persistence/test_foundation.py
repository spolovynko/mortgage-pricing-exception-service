"""Resource lifetime and storage isolation, without business models or migrations."""

import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Column, Engine, Integer, MetaData, String, Table, insert, inspect, select
from sqlalchemy.exc import IntegrityError, OperationalError

from mortgage_pricing.config import Settings
from mortgage_pricing.persistence.database import create_database_engine, create_session_factory


@pytest.fixture
def database_settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        database_url=f"sqlite:///{(tmp_path / 'foundation.db').as_posix()}",
        sqlite_busy_timeout_seconds=0.25,
    )


@pytest.fixture
def engine(database_settings: Settings) -> Iterator[Engine]:
    database_engine = create_database_engine(database_settings)
    try:
        yield database_engine
    finally:
        database_engine.dispose()


@pytest.fixture
def probe_table(engine: Engine) -> Table:
    # This schema exists only in the pytest-owned temporary database. Business
    # metadata remains empty; operational schema creation will use Alembic.
    table = Table(
        "foundation_probe",
        MetaData(),
        Column("id", Integer, primary_key=True),
        Column("value", String, nullable=False),
    )
    table.create(engine)
    return table


def test_imports_do_not_load_settings_or_touch_storage(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DATABASE_URL", "invalid-settings-must-not-be-loaded")
    subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import alembic; import sqlalchemy; "
            "import mortgage_pricing.persistence.base; "
            "import mortgage_pricing.persistence.database",
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert list(tmp_path.iterdir()) == []


def test_resource_factories_are_lazy(database_settings: Settings, tmp_path: Path) -> None:
    engine = create_database_engine(database_settings)
    try:
        factory = create_session_factory(engine)
        with factory():
            assert not (tmp_path / "foundation.db").exists()
    finally:
        engine.dispose()


def test_unavailable_parent_is_not_created(tmp_path: Path) -> None:
    path = tmp_path / "missing" / "database.db"
    engine = create_database_engine(Settings(database_url=f"sqlite:///{path.as_posix()}"))
    try:
        assert not path.parent.exists()
        with pytest.raises(OperationalError), engine.connect():
            pass
        assert not path.parent.exists()
    finally:
        engine.dispose()


def test_connection_uses_timeout_without_creating_schema(engine: Engine) -> None:
    with engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA busy_timeout").scalar_one() == 250
        assert inspect(connection).get_table_names() == []


@pytest.mark.parametrize("scheme", ["postgresql", "postgresql+psycopg"])
def test_reserved_backend_fails_before_driver_loading_without_exposing_url(scheme: str) -> None:
    settings = Settings(database_url=f"{scheme}://user:synthetic-secret@localhost/example")
    with pytest.raises(ValueError, match="supports SQLite") as exc_info:
        create_database_engine(settings)
    assert "synthetic-secret" not in str(exc_info.value)


def test_success_commits_and_returns_connection_before_engine_reopening(
    engine: Engine, probe_table: Table, database_settings: Settings
) -> None:
    factory = create_session_factory(engine)
    with factory.begin() as session:
        session.execute(insert(probe_table).values(id=1, value="synthetic-saved-value"))
    assert engine.pool.checkedout() == 0
    engine.dispose()

    reopened_engine = create_database_engine(database_settings)
    try:
        with create_session_factory(reopened_engine)() as session:
            assert (
                session.execute(select(probe_table.c.value)).scalar_one() == "synthetic-saved-value"
            )
        assert reopened_engine.pool.checkedout() == 0
    finally:
        reopened_engine.dispose()


def test_failure_rolls_back_and_returns_connection(engine: Engine, probe_table: Table) -> None:
    factory = create_session_factory(engine)
    with pytest.raises(RuntimeError, match="synthetic failure"), factory.begin() as session:
        session.execute(insert(probe_table).values(id=1, value="synthetic-rollback-value"))
        raise RuntimeError("synthetic failure")
    assert engine.pool.checkedout() == 0

    with factory.begin() as session:
        assert session.execute(select(probe_table)).all() == []
        session.execute(insert(probe_table).values(id=2, value="synthetic-recovery-value"))
    with factory() as session:
        assert session.execute(select(probe_table.c.id)).scalars().all() == [2]


def test_plain_session_closure_does_not_commit(engine: Engine, probe_table: Table) -> None:
    factory = create_session_factory(engine)
    with factory() as session:
        session.execute(insert(probe_table).values(id=1, value="synthetic-unsaved-value"))
    assert engine.pool.checkedout() == 0
    with factory() as session:
        assert session.execute(select(probe_table)).all() == []


def test_factories_keep_different_database_files_isolated(
    engine: Engine, probe_table: Table, tmp_path: Path
) -> None:
    other_engine = create_database_engine(
        Settings(database_url=f"sqlite:///{(tmp_path / 'other.db').as_posix()}")
    )
    try:
        probe_table.create(other_engine)
        with create_session_factory(engine).begin() as session:
            session.execute(insert(probe_table).values(id=1, value="synthetic-first-database"))
        with create_session_factory(other_engine)() as session:
            assert session.execute(select(probe_table)).all() == []
    finally:
        other_engine.dispose()


def test_exception_diagnostics_hide_bound_values(engine: Engine, probe_table: Table) -> None:
    factory = create_session_factory(engine)
    with factory.begin() as session:
        session.execute(insert(probe_table).values(id=1, value="synthetic-existing-value"))
    with pytest.raises(IntegrityError) as exc_info, factory.begin() as session:
        session.execute(insert(probe_table).values(id=1, value="synthetic-private-value-987"))
    assert "synthetic-private-value-987" not in str(exc_info.value)
