"""SQLite integrity and transaction behavior in isolated file-backed databases."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Column, Engine, ForeignKey, Integer, MetaData, Table, inspect, text
from sqlalchemy.exc import IntegrityError, OperationalError

from mortgage_pricing.config import Settings
from mortgage_pricing.persistence.database import create_database_engine


@pytest.fixture
def engine(tmp_path: Path) -> Iterator[Engine]:
    database_engine = create_database_engine(
        Settings(
            _env_file=None,
            database_url=f"sqlite:///{(tmp_path / 'transactions.db').as_posix()}",
            sqlite_busy_timeout_seconds=0.1,
        )
    )
    try:
        yield database_engine
    finally:
        database_engine.dispose()


def test_every_connection_enforces_foreign_keys_with_modern_transactions(engine) -> None:
    metadata = MetaData()
    parent = Table("parent_probe", metadata, Column("id", Integer, primary_key=True))
    child = Table(
        "child_probe",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("parent_id", Integer, ForeignKey("parent_probe.id"), nullable=False),
    )
    metadata.create_all(engine)

    with engine.connect() as first, engine.connect() as second:
        for connection in (first, second):
            driver_connection = connection.connection.driver_connection
            assert driver_connection.autocommit is False
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
            with pytest.raises(IntegrityError):
                connection.execute(child.insert().values(id=1, parent_id=999))
            connection.rollback()

    with engine.begin() as connection:
        connection.execute(parent.insert().values(id=1))
        connection.execute(child.insert().values(id=1, parent_id=1))


def test_ddl_is_rolled_back_without_prior_dml(engine) -> None:
    with pytest.raises(RuntimeError, match="synthetic abort"), engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE rolled_back_probe (id INTEGER PRIMARY KEY)")
        raise RuntimeError("synthetic abort")

    assert not inspect(engine).has_table("rolled_back_probe")


def test_savepoint_rollback_preserves_outer_write(engine) -> None:
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE savepoint_probe (id INTEGER PRIMARY KEY)")

    with engine.begin() as connection:
        connection.exec_driver_sql("INSERT INTO savepoint_probe (id) VALUES (1)")
        with (
            pytest.raises(RuntimeError, match="synthetic nested abort"),
            connection.begin_nested(),
        ):
            connection.exec_driver_sql("INSERT INTO savepoint_probe (id) VALUES (2)")
            raise RuntimeError("synthetic nested abort")

    with engine.connect() as connection:
        assert connection.execute(text("SELECT id FROM savepoint_probe")).scalars().all() == [1]


def test_released_savepoint_still_rolls_back_with_outer_transaction(engine) -> None:
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE outer_probe (id INTEGER PRIMARY KEY)")

    with pytest.raises(RuntimeError, match="synthetic outer abort"), engine.begin() as connection:
        with connection.begin_nested():
            connection.exec_driver_sql("INSERT INTO outer_probe (id) VALUES (1)")
        raise RuntimeError("synthetic outer abort")

    with engine.connect() as connection:
        assert connection.exec_driver_sql("SELECT id FROM outer_probe").all() == []


def test_competing_writer_times_out_and_can_retry_after_release(engine) -> None:
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE lock_probe (id INTEGER PRIMARY KEY)")

    with engine.connect() as first, engine.connect() as second:
        first.exec_driver_sql("INSERT INTO lock_probe (id) VALUES (1)")
        assert second.exec_driver_sql("PRAGMA busy_timeout").scalar_one() == 100
        with pytest.raises(OperationalError, match="database is locked"):
            second.exec_driver_sql("INSERT INTO lock_probe (id) VALUES (2)")
        second.rollback()
        first.commit()
        second.exec_driver_sql("INSERT INTO lock_probe (id) VALUES (2)")
        second.commit()

    with engine.connect() as connection:
        ids = connection.exec_driver_sql("SELECT id FROM lock_probe ORDER BY id").scalars().all()
        assert ids == [1, 2]
