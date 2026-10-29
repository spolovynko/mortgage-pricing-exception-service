# ADR 0002 - Database foundation and seed data

- Date: 2026-10-29 (Europe/Brussels).
- Phase / milestone: 02 / MVP1.
- Status: Implemented for execution Step 2 only; Phase 02 remains in progress.
- Implementation state: partial; resource factories/configuration verified, business storage not yet implemented.
- Decision owner or contributor: Codex assistant within the user's incremental Phase 02 requests.
- Human acceptance: not recorded for the resulting implementation.
- Related requirements and phase guide: NFR-01/03, DEL-02/03; [Phase 02](../phases/phase-02-database-and-seed-data.md).

## Context

Step 1 verified the Phase 01 baseline. Step 2 began from clean `main` at `54e219e`, with the Step 1 records committed. The user authorized the persistence foundation only. SQLite driver transaction configuration is Step 3; business models are Steps 4-7, atomic operation checks Step 8, migrations Step 9, seeds Step 10, and API/database readiness wiring Step 11.

The project already uses immutable central settings, explicit application factories, safe JSON diagnostics, and shared HTTP error handling. Persistence should fit those boundaries. The agreed stack is SQLite through SQLAlchemy, with Alembic for schema evolution.

## Options considered

| Option | Benefits | Costs and limitations |
| --- | --- | --- |
| Direct SQLAlchemy engine/session factories | Explicit dependencies and lifetime; existing transaction contexts; little custom code | Callers must close sessions and dispose the engine correctly |
| Generic repository and custom unit-of-work hierarchy | Could isolate a future domain query boundary | Duplicates session capabilities without a current need |
| Global engine/session plus automatic table creation | Short startup code | Import-time I/O, shared mutable state, and schema changes outside migrations |
| Multiple database backends immediately | More deployment options | Requires unrequested drivers, migrations, and concurrency verification |

## Decision

- Add SQLAlchemy `>=2.0.55,<2.1` and Alembic `>=1.16,<2` as runtime dependencies, since deployment must eventually run migrations. The project lock resolves SQLAlchemy 2.0.55 and Alembic 1.20.1. Use the SQLAlchemy 2.0 API consistently. No Alembic configuration or migration is generated in this step.
- Create `persistence/base.py` with one declarative base and deterministic names for primary keys, foreign keys, unique constraints, checks, and indexes. Composite constraint names include all local columns. Check constraints must receive an explicit short name. Shared metadata has no business tables yet.
- Create `create_database_engine(settings)` in `persistence/database.py`. It receives the existing `Settings`, constructs a lazy engine, and performs no connection, directory creation, migration, or seed operation. No module-global engine or session exists.
- Implement SQLite through the standard-library sqlite3 driver only. Existing settings continue accepting reserved PostgreSQL URLs; the persistence factory rejects those URLs with a fixed message before loading a driver. This does not change the existing settings contract or claim PostgreSQL support.
- Add `SQLITE_BUSY_TIMEOUT_SECONDS`, default 5 seconds, greater than 0 and at most 30. Pass it as the DBAPI connection timeout. Tests use 0.25 seconds and verify the resulting 250 ms `PRAGMA busy_timeout`. Actual contention and timeout limitations remain Step 3 verification.
- Set `check_same_thread=False` so file-backed pooled connections can move between worker threads. A session must still belong to one operation; this flag does not make a session safe for simultaneous use.
- Disable SQL echo and hide bound parameters in SQLAlchemy diagnostics. Do not add low-level catch/log/rethrow wrappers. Callers retain responsibility for error translation and safe logging through the established boundaries.
- Create `create_session_factory(engine)` returning SQLAlchemy's standard `sessionmaker`. Retain normal expiration after commit. Use `with factory.begin() as session` for commit on success, rollback on failure, and session closure. Plain `with factory()` closes without implicitly committing.
- The engine owner must close sessions/connections before calling `engine.dispose()`. Current tests own this lifecycle. API construction/shutdown wiring belongs to Step 11, when the API first owns a database resource; `main.py` is unchanged in Step 2.
- Add ignore rules for local `data/`, SQLite database files, and journal/WAL/shared-memory sidecars. No real settings, normal database, or existing data directory is opened or removed.

## Consequences

The common persistence boundary is available for later steps without adding business models or unnecessary abstraction layers. Factories can be injected and tested against separate files. Storage failures reach the calling boundary with no fabricated success.

**This is an incomplete persistence foundation.** SQLite foreign keys are not yet enabled, and the driver still uses its default transaction mode. Step 3 must establish these guarantees before business writes. The basic DML commit/rollback tests do not establish DDL/savepoint behavior, relationship integrity, or competing-operation safety. Bounded lock waiting alone does not solve concurrency.

Only tests create a simple probe table in pytest-owned temporary files. Application code does not create a schema. Operational schema setup must use Alembic in Step 9. The absence of a data directory will produce a storage error on connection; no implicit filesystem setup occurs here.

## Verification and evidence

- `uv add "sqlalchemy>=2.0.55,<2.1" "alembic>=1.16,<2"` resolved 33 packages and installed Alembic 1.20.1, Mako 1.4.3, and MarkupSafe 3.0.4. SQLAlchemy 2.0.55 and greenlet 3.5.6 were already present in the ignored environment; this step adds them to the authoritative project metadata/lock.
- `uv run --locked python -m pytest tests/persistence tests/test_config.py`: **33 passed**. Initial lint found one long assertion; formatting corrected it before final checks. No test failure or warning suppression occurred.
- `uv run --locked python -m pytest`: **62 passed**, including 11 persistence-foundation cases and 22 configuration cases.
- New cases verify imports outside the repository with deliberately invalid settings, lazy engine/session construction, missing-parent failure without directory creation, connection without schema creation, configured timeout, safe rejection of two reserved PostgreSQL URL forms, committed data after a new engine opens the same file, rollback/recovery, no implicit commit, separate database isolation, connection return on context exit, and hidden bound values in exception text.
- `uv run --locked python -m ruff check .`: passed. `uv run --locked python -m ruff format --check .`: 39 files already formatted. `uv lock --check`: 33 packages. `uv pip check`: 32 installed packages compatible. `uv run --locked python -m alembic --version`: `alembic 1.20.1`.
- Tests use Windows/CPython 3.12.12 and temporary file-backed SQLite. No migration, business schema, seed, database readiness, live API/storage integration, other-platform, or whole-phase acceptance result is claimed. Final dependency comparison and static checks are recorded in the [build log](../build-log.md).

## Alternatives rejected and revisit conditions

Use direct sessions until a concrete query ownership or testing need warrants another abstraction. Do not automatically initialize schema at startup. Revisit PostgreSQL only with an explicit driver, migration, and concurrency verification plan. Extend this ADR as subsequent user-authorized steps implement their decisions; do not describe future guarantees as already implemented.

## Production implications

No production readiness, authentication, backup, audit, or multi-instance guarantee follows from these factories. The current foundation is intentionally incomplete until Step 3. Database operations must remain short; future model calls must occur outside active write transactions. Deployment lifecycle and migration sequencing require verification in their later steps/phases.

## References and supersession

- [Phase 02 guide](../phases/phase-02-database-and-seed-data.md), [requirements](../requirements.md), [architecture](../architecture.md), [engineering guidelines](../python-engineering-guidelines.md), [AGENTS.md](../../AGENTS.md).
- [SQLAlchemy engine configuration](https://docs.sqlalchemy.org/en/20/core/engines.html), [SQLAlchemy session contexts](https://docs.sqlalchemy.org/en/20/orm/session_basics.html), [Alembic installation and dependencies](https://alembic.sqlalchemy.org/en/latest/front.html).
- [ADR 0001](0001-foundation-config-logging.md) continues to govern settings, logging, and HTTP errors. No prior ADR is superseded.
