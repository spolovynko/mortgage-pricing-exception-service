# ADR 0002 - Database foundation and seed data

- Date: 2026-10-29 (Europe/Brussels).
- Phase / milestone: 02 / MVP1.
- Status: Implemented through execution Step 9 only; Phase 02 remains in progress.
- Implementation state: partial; SQLite configuration, storage models, atomic operations, and initial migration verified.
- Decision owner or contributor: Codex assistant within the user's incremental Phase 02 requests.
- Human acceptance: not recorded for the resulting implementation.
- Related requirements and phase guide: NFR-01/03, DEL-02/03; [Phase 02](../phases/phase-02-database-and-seed-data.md).

## Context

Step 1 verified the Phase 01 baseline. Step 2 began from clean `main` at `54e219e`, with the Step 1 records committed. The user authorized each later step separately. Steps 3-7 added SQLite transaction guarantees and business storage models; Step 8 added atomic operations; Step 9 adds the initial migration. Seeds remain Step 10, and API/database readiness wiring remains Step 11.

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
- Add `SQLITE_BUSY_TIMEOUT_SECONDS`, default 5 seconds, greater than 0 and at most 30. Pass it as the DBAPI connection timeout. Tests use 0.25 seconds and verify the resulting 250 ms `PRAGMA busy_timeout`; later tests exercise actual contention.
- Set `check_same_thread=False` so file-backed pooled connections can move between worker threads. A session must still belong to one operation; this flag does not make a session safe for simultaneous use.
- Disable SQL echo and hide bound parameters in SQLAlchemy diagnostics. Do not add low-level catch/log/rethrow wrappers. Callers retain responsibility for error translation and safe logging through the established boundaries.
- Create `create_session_factory(engine)` returning SQLAlchemy's standard `sessionmaker`. Retain normal expiration after commit. Use `with factory.begin() as session` for commit on success, rollback on failure, and session closure. Plain `with factory()` closes without implicitly committing.
- The engine owner must close sessions/connections before calling `engine.dispose()`. Current tests own this lifecycle. API construction/shutdown wiring belongs to Step 11, when the API first owns a database resource; `main.py` is unchanged in Step 2.
- Step 3 uses Python 3.12+ sqlite3 `autocommit=False` so SELECT, DDL, and savepoints participate in explicit transactions. An engine-local listener sets `PRAGMA foreign_keys=ON` on every DBAPI connection, temporarily enabling autocommit solely for that PRAGMA. Keep the configured busy timeout; a lock failure rolls back the attempted operation and leaves retry policy to a future business boundary. Do not enable WAL or automatic retry without a concrete workload and verification need.
- Step 4 uses UUID primary keys for internal users and mortgage applications, unique nonblank technical identifiers, and UTC-normalized timestamps that restore timezone information after SQLite reads. Users hold roles through a membership table, allowing a future user to hold both current roles. Applications reference their manager through a composite foreign key to a `relationship_manager` membership; a reviewer-only user cannot own an application. This added `manager_role` column is a fixed relational guard for that composite reference, constrained to `relationship_manager`; it is not an API input. Later services still enforce actor permissions and self-review rules.
- Step 5 stores one `PricingRequest` per application through a unique application foreign key. `RequestVersion` has a composite `(request_id, version_number)` primary key, positive integer basis-point discount, reason length 1-2,000 after trimming, existing submitter reference, and UTC submission time. The request's nullable `current_version_number` uses a composite foreign key `(id, current_version_number)` to the version's key, preventing a pointer to another request. A new request is inserted before its first version; the pointer is set after the version exists in the same transaction.
- The ORM rejects updates and deletion of submitted versions with mapper events. The Step 9 migration adds SQLite triggers that also reject direct SQL and bulk changes to stored version rows. No status is stored on versions yet: a version without a Step 6 decision is pending, and only the current version will be eligible for approved-pricing retrieval.
- Step 6 stores one `PricingDecision` per `(request_id, version_number)` with a database unique constraint and composite foreign key to the exact submitted version. Its outcome is approved or declined, and its decision maker must have reviewer membership. No discount is copied into the decision, so the version retains the authoritative reviewed amount. Typed `RequestHistoryEvent` rows reference the exact version and an existing actor. Both carry UTC timestamps. ORM mapper events reject update/delete; Step 9 migration triggers must protect direct SQL writes. Operational JSON logs remain separate from business history.
- Step 7 stores creation retry keys in `CreationIdempotencyRecord` with a composite `(caller_id, key)` primary key; callers can use the same key independently. The record retains a 64-character lowercase SHA-256 hexadecimal fingerprint of canonical input and a composite foreign key to the original request's version 1. It stores an existing caller and UTC creation time. Key length is 1-128 after trimming. ORM update/delete guards protect the mapping; direct SQL triggers remain Step 9 work.
- Step 8 adds focused create, revise, and decide persistence functions, each owning `factory.begin()` so the business row and corresponding history commit or roll back together. Creation fingerprints deterministic JSON with sorted keys and compact separators, UTF-8 encoding, the application UUID, integer discount, and exact reason text; caller identity is carried by the composite key. Identical caller/key/input replays the stored version-1 reference even after later revisions, while changed input or a new key for an already requested application conflicts. Validation keeps the submitted reason unchanged. The manager must own the application and hold manager membership; the decision maker needs reviewer membership and cannot be the owner or version submitter. Revision and decision require the expected current version; a decided version cannot be decided twice.
- Each write operation first performs a no-op UPDATE of its existing application or request row. SQLite obtains its single-writer lock before state reads, so competing writes serialize and recheck current state; a bounded busy failure propagates without automatic retry. This is a pragmatic SQLite-specific lock acquisition under the current `autocommit=False` transaction configuration. A future PostgreSQL implementation needs a different locking strategy. Tests use isolated files and real competing connections; no HTTP business contract is introduced here.
- Step 9 configures Alembic to load validated `Settings` only when invoked, then applies explicit revision `20261029_0001`. It creates every Phase 02 table and database constraint without any startup schema creation. The initial revision adds SQLite `BEFORE UPDATE` and `BEFORE DELETE` triggers for submitted versions, decisions, history events, and retry mappings, extending ORM protection to direct SQL. The request/current-version foreign-key cycle uses `use_alter=True` in metadata so migration tooling can order it. SQLite reflection still produces false positive unique-constraint differences during `alembic check`; applied-schema tests verify this migration instead. Downgrade removes triggers before dropping the tables.
- Add ignore rules for local `data/`, SQLite database files, and journal/WAL/shared-memory sidecars. No real settings, normal database, or existing data directory is opened or removed.

## Consequences

The common persistence boundary is available for later steps without adding business models or unnecessary abstraction layers. Factories can be injected and tested against separate files. Storage failures reach the calling boundary with no fabricated success.

**This is an incomplete business persistence foundation.** Core models, SQLite-specific atomic writes, and the initial operational migration are verified in temporary databases. Seed data and API integration remain pending.

Step 3 configures Python 3.12+ sqlite3 with `autocommit=False`, rather than relying on the driver's legacy mode. An engine-local connection listener temporarily enables autocommit to run `PRAGMA foreign_keys=ON`, then restores the prior value. This applies to every pooled DBAPI connection before use and does not introduce import-time I/O. A short busy timeout still raises a lock error under contention; callers must end the failed transaction and choose whether a later retry is valid. Journal mode remains SQLite's default; no automatic retry or cross-process update protocol is claimed. Keep business write transactions short.

File-backed tests establish FK rejection, transactional DDL/savepoints, bounded writer contention, business storage constraints, Step 8 operation atomicity, competing-write outcomes, and the initial applied migration. Seed data and API integration remain pending.

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

No production readiness, authentication, backup, audit, or multi-instance guarantee follows from these factories. Business storage remains incomplete. Database operations must remain short; future model calls must occur outside active write transactions. Deployment lifecycle and migration sequencing require verification in their later steps/phases.

## References and supersession

- [Phase 02 guide](../phases/phase-02-database-and-seed-data.md), [requirements](../requirements.md), [architecture](../architecture.md), [engineering guidelines](../python-engineering-guidelines.md), [AGENTS.md](../../AGENTS.md).
- [SQLAlchemy SQLite transactions and foreign keys](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html), [SQLAlchemy engine configuration](https://docs.sqlalchemy.org/en/20/core/engines.html), [SQLAlchemy session contexts](https://docs.sqlalchemy.org/en/20/orm/session_basics.html), [Alembic installation and dependencies](https://alembic.sqlalchemy.org/en/latest/front.html).
- [ADR 0001](0001-foundation-config-logging.md) continues to govern settings, logging, and HTTP errors. No prior ADR is superseded.
