# Phase 02 - Database and seed data

- Status: In progress; execution Steps 1-9 complete. Step 10 requires the user's instruction.
- Milestone: MVP1.
- Prerequisite: Phase 01 complete or its unmet criteria explicitly resolved.
- Primary ADR: [ADR 0002](../adr/0002-database-and-seed-data.md), Implemented through Step 9 only.
- Handoff to create: `docs/handoffs/phase-02.md`.

## Objective

Create persistent, versioned storage that supports exact-term decisions, history, retries, and later AI assessments without losing data on restart.

## Read first

[AGENTS.md](../../AGENTS.md), [project status](../project-status.md), [requirements](../requirements.md), [architecture](../architecture.md), [engineering guidelines](../python-engineering-guidelines.md), the Phase 01 handoff, and relevant foundation ADRs.

## Scope and expected components

Use SQLAlchemy with SQLite and Alembic migrations. Expected locations are `src/mortgage_pricing/persistence/`, `src/mortgage_pricing/seed.py`, migrations/, and persistence tests. Avoid building unused generic repository abstractions.

## User-gated execution steps

Complete one step at a time. Record its checks, then wait for the user's instruction.

1. [x] Confirm the Phase 01 baseline and persistence boundaries.
2. [x] Add the persistence foundation.
3. [x] Configure and verify SQLite transactions.
4. [x] Define users, roles, mortgage applications, and manager ownership.
5. [x] Define logical requests and immutable submitted versions.
6. [x] Define decisions and append-only history.
7. [x] Define caller-scoped idempotency records.
8. [x] Define and verify atomic operation boundaries.
9. [x] Create and verify the initial Alembic migration.
10. [ ] Add repeatable synthetic seed data.
11. [ ] Add database readiness without changing process liveness.
12. [ ] Run final verification and complete Phase 02 records and handoff.

### Step 1 evidence - 2026-10-29

- The worktree was clean on `main` at `0bc29a0` before Step 1.
- Inspected the required instructions, Phase 01 handoff, Phase 02 guide, requirements, architecture, engineering guidance, commit guidance, ADR 0001, recent build evidence, actual source, tests, and dependency metadata.
- Actual source confirms that `DATABASE_URL` is validated configuration only. The project has no SQLAlchemy or Alembic dependency, persistence package, migration directory, seed command, database readiness check, or generated database.
- `uv run --locked python -m pytest` passed **48 tests**.
- `uv run --locked python -m ruff check .` passed.
- `uv run --locked python -m ruff format --check .` passed for **35 files**.
- `uv lock --check` passed with **28 resolved packages**. `uv pip check` passed with **29 installed packages checked**.
- Verification used uv 0.11.6, Windows, and CPython 3.12.12.
- No dependency, source, database, migration, seed, API, or configuration behavior changed. All Phase 02 implementation tasks and acceptance criteria remain unchecked.
- Human review or acceptance is not recorded. Active work time is not recorded.
- Next action: Step 2, add the persistence foundation, only after the user's instruction.

### Step 2 evidence - 2026-10-29

- Began from clean `main` at `54e219e`, with Step 1 records committed. Added SQLAlchemy/Alembic dependencies, shared metadata, lazy SQLite engine/session factories, `SQLITE_BUSY_TIMEOUT_SECONDS`, storage ignore rules, and isolated foundation tests. No business model, migration, seed, API wiring, or Step 3 configuration was added.
- Resource factories do not connect or initialize schema/directories. The caller owns disposal after sessions close. Standard session contexts provide basic commit/rollback/closure, with no generic repository wrapper. PostgreSQL URLs remain reserved settings and fail safely in this SQLite-only factory. SQL echo is disabled and bound parameters are hidden in exception text.
- `uv run --locked python -m pytest tests/persistence tests/test_config.py`: **33 passed**. Full `uv run --locked python -m pytest`: **62 passed**, including 11 foundation cases. Initial lint found one long assertion, corrected by formatting; all tests passed on their first runs.
- Ruff lint/format passed (39 formatted files); `uv lock --check` passed (33 packages); `uv pip check` passed (32 installed packages); Alembic CLI reports 1.20.1. SQLAlchemy is 2.0.55. See [build log](../build-log.md) for exact commands and final review.
- Foundation tests use only pytest-owned file-backed SQLite and a test-only probe table. They verify imports/factories without side effects, configured timeout, connection release, save/reopen, rollback/recovery, no implicit commit, database isolation, and safe diagnostic values.
- Limits: foreign-key enforcement and explicit SQLite driver transaction configuration remain Step 3. DDL/savepoint/concurrency guarantees and all Phase 02 acceptance criteria remain unverified. API storage lifecycle wiring belongs to Step 11; migrations belong to Step 9. No normal database was opened/reset. Human review and active work time are not recorded.
- Next action: Step 3 only on user instruction. All implementation tasks below remain unchecked because their complete behavior is still pending.

### Step 3 evidence - 2026-10-29

- Began from a clean worktree after Step 2 was committed by the user. Configured Python 3.12+ sqlite3 `autocommit=False` for all factory connections and enabled `PRAGMA foreign_keys=ON` on each connection using an engine-local listener. The PRAGMA runs with temporary autocommit because SQLite ignores it inside a transaction. Existing timeout and session ownership remain in place.
- Five new file-backed tests verify foreign keys on two simultaneous connections, transactional DDL rollback, nested savepoint rollback, released savepoint participation in outer rollback, and bounded competing-writer failure followed by retry after lock release. These tests use only pytest-owned temporary files and probe tables.
- `uv run --locked python -m pytest tests/persistence -q`: **16 passed**. Full `uv run --locked python -m pytest -q`: **67 passed**. Final lint/format and dependency checks are recorded in the build log.
- The writer test establishes a bounded lock error and manual retry after release; it does not claim automatic retry, multi-process safety, or a complete competing-update protocol. Business models, migrations, seeds, and API readiness remain pending. The session/SQLite configuration task is checked; atomic business operation boundaries remain unchecked until Step 8. No phase acceptance criterion is complete.
- Next action: Step 4 only on user instruction.

### Step 4 evidence - 2026-10-29

- Began from clean `main` at `0add25c`, after the user committed Step 3. Added ORM models for internal users, role memberships, and mortgage applications. No migration, seed, API endpoint, business operation, or normal database was created.
- A user has a stable UUID, a unique nonblank login, a display name, timezone-aware UTC creation time, and zero or more role memberships. Memberships are unique by user/role and allow the two current roles: `relationship_manager` and `reviewer`.
- An application has a UUID, unique nonblank reference, creation time, and one manager. Its composite foreign key requires that owner to hold `relationship_manager`; a reviewer-only user cannot own an application. Later service operations still enforce who may submit/revise and who may decide; this schema does not implement API authorization.
- `uv run --locked python -m pytest tests/persistence/test_models.py -q`: **6 passed**. `uv run --locked python -m pytest tests/persistence -q`: **22 passed**. Full-suite and static-check results are recorded in the build log.
- Tests use `Base.metadata.create_all()` only in pytest-owned temporary SQLite files. They verify persistence/reopen, role membership, manager ownership, unique login/reference/membership, missing/reviewer-only manager failures, invalid role failure, and blank identifier failures. The schema will first be operationally created by Step 9 Alembic migration.
- Next action: Step 5 only on user instruction. The broader request/version/decision/history constraint task remains unchecked, and no phase acceptance criterion is complete.

### Step 5 evidence - 2026-10-29

- Began with Step 4 changes still uncommitted and preserved them. Added `PricingRequest` with one row per application, and `RequestVersion` with a request-scoped positive number, positive integer discount in basis points, nonblank reason of at most 2,000 characters, submitter reference, and UTC submission time.
- `current_version_number` is a nullable pointer on the logical request. A composite foreign key requires it to identify a version belonging to that request. Creation inserts the request, then its first version, then sets the pointer in one transaction; Step 8 will define the application operation and its concurrency rules. The temporary null state is needed for this insertion order.
- ORM update/delete events reject modification of submitted versions. Direct SQL can bypass these events; Step 9 must add SQLite triggers for stored-row immutability. No API operation or claim of database-level append-only protection is made yet.
- Ten isolated file-backed tests cover two preserved versions and the current pointer, duplicate request/version rejection, wrong or absent current version rejection, invalid or overlong terms, missing submitter, and ORM edit/delete rejection. `uv run --locked python -m pytest tests/persistence/test_request_versions.py -q`: **10 passed**. Full suite: **83 passed**; Ruff lint/format, lock and dependency checks passed. The build log records exact commands and corrections.
- Request/version/decision/history combined task and whole-phase acceptance criteria remain unchecked until their later work is complete. No migration, seed, normal database, or business endpoint was created. Next action: Step 6 only on user instruction.

### Step 6 evidence - 2026-10-29

- Began from clean `main` at `f3ae4d1`, after the user committed Steps 4-5. Added `PricingDecision` for one approved/declined human decision per exact request version and `RequestHistoryEvent` for typed created/revised/approved/declined events. Each record stores actor and UTC time; neither stores a duplicate discount amount.
- The database requires a valid version for decisions and history, one decision per version, a valid actor for history, and reviewer membership for the decision maker. ORM events reject updates/deletes of decisions and history. Direct SQL immutability still requires Step 9 migration triggers.
- Seven isolated file-backed tests verify exact-version links, actor/time round trips, duplicate decision rejection, missing-version failures, reviewer-only authority, and ORM update/delete rejection. `uv run --locked python -m pytest tests/persistence/test_decisions_history.py -q --tb=short`: **7 passed**. Full suite: **90 passed**; final static results are in the build log.
- A user holding both roles can still self-review at schema level; the later business service must reject it. Decision-plus-history atomicity, current-version checks, and competing writes remain Step 8 work. All phase acceptance criteria remain unchecked. Next action: Step 7 only on user instruction.

### Step 7 evidence - 2026-10-29

- Began from clean `main` at `882bdfa`, after the user committed Step 6. Added `CreationIdempotencyRecord` with `(caller_id, key)` as its composite primary key, a 64-character lowercase hexadecimal SHA-256 fingerprint, and the original request/version-1 reference. Key length is 1-128 after trimming. Foreign keys require an existing caller and submitted version.
- ORM update/delete events protect the stored retry mapping. Direct SQL protection remains Step 9 migration work. Step 8 must define canonical input, same-key replay/conflict behavior, and atomic request/version/history/idempotency writes. This step adds storage only.
- Twelve isolated file-backed tests verify different callers can reuse a key, same-caller duplicates fail even with changed input, original references and timestamps survive reopening, invalid keys/fingerprints fail, missing references fail, and ORM changes/deletion fail. Full suite: **102 passed**; final lint/format and dependency checks are recorded in the build log.
- No migration, seed, normal database, or endpoint was created. All phase acceptance criteria remain unchecked. Next action: Step 8 only on user instruction.

### Step 8 evidence - 2026-10-29

- Began from clean `main` at `b76a404` after the user committed Step 7. Added focused persistence operations for creation, revision, and exact-version human decision. Each owns one session transaction and writes its matching history event with the business rows; failed writes roll back together.
- Creation hashes deterministic UTF-8 JSON of application ID, exact discount, and exact reason. A caller/key with matching input replays its original version-1 reference, including after revision; changed input conflicts. A new key for an already requested application conflicts. Manager ownership and role, reviewer role, current-version freshness, self-review, and one decision per version are checked server-side.
- Each operation makes a no-op update to its existing application or request as its first SQL statement. On SQLite this obtains the writer lock before reading mutable state; competing writers serialize or receive a bounded lock error. No automatic retry is claimed. Eight isolated file-backed tests cover replay/conflict, exact versions, permissions, stale/duplicate decisions, rollback of partial creation and decision/history, competing revisions/decisions, and lock contention. Focused **8 passed**; full suite **110 passed**. Static/dependency checks are in the build log.
- Schema still exists only in test-owned temporary databases. Step 9 must migrate it and protect immutable rows against direct SQL. API error mapping, endpoints, seeds, and readiness remain pending. Phase acceptance remains unchecked; Step 9 requires the user's instruction.

### Step 9 evidence - 2026-10-29

- Began from clean `main` at `dac5937` after the user committed Step 8. Added Alembic configuration and the initial explicit migration for every Phase 02 table, relationship, unique constraint, and check constraint. Operational setup now uses `DATABASE_URL` through validated `Settings`; it does not call test-only metadata creation.
- SQLite triggers reject direct `UPDATE` and `DELETE` statements against submitted versions, decisions, history events, and creation idempotency records. The migration is revision `20261029_0001`; downgrade removes its triggers and tables. The request/current-version cyclic foreign key is marked as deferred metadata for future migration tooling while retaining the SQLite constraint.
- Three isolated file-backed migration tests apply the migration, reapply it without losing data, verify foreign-key and trigger rejection, then downgrade/re-upgrade. Focused **3 passed**; full suite **113 passed**. Ruff, lock, and dependency results are in the build log.
- SQLite schema-drift autogeneration still reports false unique-constraint remove/add operations because SQLite reflection does not preserve enough constraint identity. The explicit migration and applied-schema tests are the verification for this initial revision. Seed data, readiness, and Phase 02 acceptance completion remain pending; Step 10 requires the user's instruction.

## Implementation tasks

- [x] Define users/role membership and mortgage applications with a documented manager-ownership relationship.
- [x] Define a logical request unique per application, submitted versions, current-version reference, decisions, and history events.
- [x] Define caller-scoped idempotency storage: key, canonical input fingerprint, and the original creation result/reference.
- [x] Decide how exact version input and actor/time metadata are preserved through application operations.
- [x] Define database constraints for relationships, unique version numbers, caller/key uniqueness, and at most one decision per version.
- [x] Establish explicit session/transaction lifetime and SQLite foreign-key/transaction configuration. Document limitations and lock handling.
- [x] Create and verify the initial Alembic migration. Do not rely on wiping the database to evolve the schema.
- [ ] Add repeatable seed data: at least two managers, two reviewers, and three clearly fictional applications. Reserve a clean application for the create/approve demo.
- [ ] Optionally include clearly fictional approved/declined examples, with coherent historical versions/events rather than fabricated live decisions.
- [ ] Add database access to core readiness; keep process liveness separate and avoid optional AI dependencies.
- [ ] Add seed/migration operational logs without sensitive record dumps.

## Verification

Apply migrations to an empty temporary file-backed database. Seed twice and verify counts/identities remain stable. Save records, close the process/session, reopen, and verify persistence. Exercise uniqueness and foreign-key failures with the actual database. Verify a failed multi-record transaction leaves no partial business/history rows.

Use a test database per test or isolated test group. Never run destructive persistence tests against the developer/evaluator's normal data file.

## Acceptance criteria

- [ ] A fresh database is created through migrations, and a second migration/setup run is safe.
- [ ] Seed execution is repeatable and preserves existing work.
- [ ] Relationships and critical uniqueness rules are enforced by the database.
- [ ] Decision/history data supports the exact-version requirements without editing earlier submitted terms.
- [ ] Persistence and transaction tests pass against file-backed SQLite.
- [ ] The API reports database readiness accurately and fails safely when storage is unavailable.

## Decision record and handover

Explain schema relationships, the one-logical-request policy, history preservation, SQLite configuration, transaction boundaries, and the seed strategy. Record exact migration/seed commands and known limitations. Update the ADR index, this guide, [build log](../build-log.md), [AI usage](../ai-usage.md), and [project status](../project-status.md); create the handoff using [the template](../handoffs/template.md).

Stop after Phase 02. The next phase implements business operations and their HTTP contracts.
