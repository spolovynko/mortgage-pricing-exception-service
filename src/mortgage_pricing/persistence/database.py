"""Lazy SQLite engines and session factories with caller-owned resource lifetimes."""

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from mortgage_pricing.config import Settings


def create_database_engine(settings: Settings) -> Engine:
    """Build an engine without connecting, creating directories, or creating schema.

    The caller closes all sessions/connections before disposing the engine.
    PostgreSQL URLs are reserved settings, not implemented persistence support.
    SQLite foreign keys and explicit driver transaction mode are Step 3 work;
    this foundation must not yet be used for business writes.
    """
    url = make_url(settings.database_url)
    if url.drivername != "sqlite":
        raise ValueError("Persistence currently supports SQLite with the sqlite3 driver only.")

    return create_engine(
        url,
        connect_args={
            "timeout": settings.sqlite_busy_timeout_seconds,
            "check_same_thread": False,
        },
        echo=False,
        hide_parameters=True,
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create sessions owned by one operation, never shared between threads/requests.

    Use ``with factory.begin() as session`` to commit on success, roll back on
    failure, and close on exit. ``with factory() as session`` only closes; it
    never commits implicitly. Keep SQLAlchemy's default expiration after commit.
    Error translation and safe logging belong to the calling boundary.
    """
    return sessionmaker(bind=engine)
