"""Lazy SQLite engines and session factories with caller-owned resource lifetimes."""

from sqlite3 import Connection as SQLiteConnection

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from mortgage_pricing.config import Settings


def create_database_engine(settings: Settings) -> Engine:
    """Build an engine without connecting, creating directories, or creating schema.

    The caller closes all sessions/connections before disposing the engine.
    PostgreSQL URLs are reserved settings, not implemented persistence support.
    Each DBAPI connection uses explicit modern transaction control and foreign
    key enforcement. Schema setup remains the responsibility of Alembic.
    """
    url = make_url(settings.database_url)
    if url.drivername != "sqlite":
        raise ValueError("Persistence currently supports SQLite with the sqlite3 driver only.")

    engine = create_engine(
        url,
        connect_args={
            "timeout": settings.sqlite_busy_timeout_seconds,
            "check_same_thread": False,
            "autocommit": False,
        },
        echo=False,
        hide_parameters=True,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection: SQLiteConnection, _connection_record: object) -> None:
        # SQLite ignores this PRAGMA inside a transaction. Python 3.12+
        # autocommit=False opens one immediately, so briefly enable autocommit.
        previous_autocommit = dbapi_connection.autocommit
        try:
            dbapi_connection.autocommit = True
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA foreign_keys=ON")
            finally:
                cursor.close()
        finally:
            dbapi_connection.autocommit = previous_autocommit

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create sessions owned by one operation, never shared between threads/requests.

    Use ``with factory.begin() as session`` to commit on success, roll back on
    failure, and close on exit. ``with factory() as session`` only closes; it
    never commits implicitly. Keep SQLAlchemy's default expiration after commit.
    Error translation and safe logging belong to the calling boundary.
    """
    return sessionmaker(bind=engine)
