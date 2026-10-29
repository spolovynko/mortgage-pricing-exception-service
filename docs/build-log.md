# Build log

Append chronological entries. Preserve earlier observations; add a correction when later evidence changes a conclusion. Distinguish plans, implemented changes, verification results, and unresolved issues.

Record actual active work time when known, including AI-assisted work according to the submission approach. Do not fabricate durations or calculate work time from calendar gaps.

## Entry format

```text
Date/time and timezone:
Phase and milestone:
Work performed:
Files/components affected:
Decision record:
Checks run and observed outcomes:
AI contribution and human review:
Problems, limitations, and corrections:
Active work duration / cumulative recorded duration:
Next action:
```

## 2026-10-28 - Documentation scaffold

- Phase/milestone: pre-implementation planning, supporting MVP1.
- Work performed: drafted the project instructions, eight phase guides, requirements, architecture, coding and commit standards, ADR/handoff templates, and project records.
- Context: the user chose Python, a Streamlit UI, optional local AI with automated setup, and one shared application Dockerfile with one Compose file.
- Implementation state: application code, containers, database, tests, and local-model integration have not been built in this scaffold.
- Decision record: no formal phase ADR yet. Planning defaults are identified as proposals in requirements.md and architecture.md.
- Verification: static scaffold validation is pending at the time of this entry. No application or model tests have run.
- AI contribution: the assistant drafted the documents from the assignment and planning discussion. Human acceptance of the generated scaffold has not been recorded.
- Active/cumulative duration: not recorded.
- Next action: validate the documentation scaffold, then start Phase 01 in a separate chat.

## 2026-10-28 - Static scaffold verification

- Work performed: checked the generated scaffold with a temporary PowerShell validation helper outside the deliverable folder.
- Observed outcome: PASS; 21 Markdown files, eight phase guides, and 105 relative links checked. No missing expected files, empty files, broken local links, unbalanced code fences, excluded organisation names, or premature completed implementation checkboxes were found.
- Phase-guide checks: each guide has an objective, required reading, implementation tasks, acceptance criteria, initial Not started status, and planned ADR/handoff paths.
- Limits: this is a static documentation check, not a Markdown rendering guarantee or verification of the planned application. No Python application, container stack, or live model was run.
- AI contribution/human review: an assistant authored and executed the static checker and reviewed the document structure. Human acceptance remains unrecorded.
- Active/cumulative duration: not recorded.
- Next action: start Phase 01 from the same project folder in a new chat.

## 2026-10-28 - Place scaffold in the project working folder

- User request: place the generated documents in the active project folder.
- Destination: `C:\Projects\mortgage-pricing-exception-service`.
- Work performed: copied 20 new Markdown files and merged the scaffold README body while preserving the existing repository title. The existing .gitignore and Git repository were preserved. No commits were created.
- Verification: the destination passed the static check for 21 Markdown files, eight phase guides, and 105 relative links; git diff --check reported no whitespace errors. The .gitignore SHA256 was unchanged before/after placement.
- Limits: documentation placement only; no implementation phase, application test, container build, or live-model evaluation was performed.
- Active/cumulative duration: not recorded.
- Next action: implement Phase 01 in a separate chat opened in this project folder.

## 2026-10-29 - Phase 01, Step 2: Python project setup

- User request/scope: implement Step 2 only, then stop. Inspected the current instructions, phase/status/engineering references, prior records, and Git state; initial working tree was clean on `main` at `4e756fe`. No unrelated user changes were present.
- Work performed: added `pyproject.toml`, `.python-version`, `src/mortgage_pricing/__init__.py`, and `uv.lock`. Selected the Python 3.12 series and uv's project/lock workflow; pinned Hatchling 1.30.1 as build backend. Installed only FastAPI, Uvicorn, Pydantic Settings, and their resolved runtime dependencies. Existing .gitignore already excludes the environment and bytecode and was preserved.
- Commands/results: `uv lock` resolved 17 packages, including this project; `uv sync --locked` created a fresh `.venv` with CPython 3.12.12 and installed all 17 packages, including an editable project build. uv version: 0.11.6. Primary resolved versions: FastAPI 0.162.0, Uvicorn 0.54.0, Pydantic Settings 2.16.2; Pydantic 2.14.1 and Starlette 1.10.0 are transitive. Exact versions/hashes and public PyPI source are in `uv.lock`.
- Verification: `uv lock --check` passed. `uv pip check` reported all installed packages compatible. `uv run --locked python -I -c "import sys; import mortgage_pricing, fastapi, pydantic_settings, uvicorn; assert sys.version_info[:2] == (3, 12); assert sys.prefix != sys.base_prefix; print('Python:', sys.version.split()[0]); print('Virtual environment:', sys.prefix); print('Installed package:', mortgage_pricing.__file__); print('Runtime dependency imports: OK')"` passed, showing `.venv` and the installed source package. `git check-ignore .venv/pyvenv.cfg src/mortgage_pricing/__pycache__/__init__.cpython-312.pyc` confirmed both generated paths are ignored.
- Observations/corrections: concurrent uv verification commands emitted temporary cache-write `Access is denied` warnings but exited successfully. Sequential reruns of lock and isolated-import checks passed without warnings. No global cache or Git configuration was changed.
- Records updated: README setup/current scope, phase incremental checklist, project status, architecture packaging note, [ADR 0001](adr/0001-foundation-config-logging.md) and index, and AI-use record. ADR status is Implemented for Step 2 only; the phase remains In progress and all phase acceptance criteria remain unchecked. Final record/whitespace verification is recorded below.
- Final record checks: a temporary stdin helper run with `.venv/Scripts/python.exe -I -` passed for 22 Markdown files, 122 local links, balanced fenced blocks, Step 2 source scope, and no checked phase acceptance criteria. `git diff --check` passed; Git's existing CRLF configuration emitted informational conversion warnings. Reviewed the final tracked/untracked inventory; only Step 2 files and corresponding records changed, with generated environment/bytecode ignored.
- Limits: Windows/CPython 3.12.12 installation/import checks only. No tests or lint configuration, API, settings, logging, identity handling, database, UI, containers, or model implementation/testing. No human code acceptance or live-model result is recorded. The phase handoff remains a phase-completion task.
- AI contribution: assistant inspected source/tool outputs, selected routine setup details, authored code/docs, and executed checks. Human review of the resulting files is not recorded.
- Active/cumulative work duration: not recorded.
- Next action: Step 3 (development checks), only when the user requests it. No commits or pushes were made.

## 2026-10-29 - Phase 01, Step 3: development checks

- Scope/state: user requested Step 3 only. Inspected instructions, existing code/configuration/records, and Git status before changing files. Working tree was clean; Step 2 was committed at `d135997`. No unrelated changes were present.
- Work: `uv add --dev "pytest>=8,<10" "ruff>=0.9,<1"` added pytest 9.2.0 and Ruff 0.17.3 to the development dependency group, with 24 total locked packages including the project. Added pytest discovery under `tests/`, `importlib` import mode, strict configuration/marker checks, and warnings-as-errors. Added Ruff Python 3.12/100-character configuration with lint groups `E`, `F`, `I`, `UP`, `B`, `SIM`. Added one packaging integration test that imports the installed package and reads distribution metadata in an isolated subprocess from a temporary directory.
- Commands/results: `uv run --locked python -m pytest` -> **1 passed**; `uv run --locked python -m ruff check .` -> all checks passed; `uv run --locked python -m ruff format --check .` -> passed; `uv lock --check` -> passed, 24 packages; `uv pip check` -> all installed packages compatible. `uv run --locked python -m ruff check --show-files` confirmed discovery of `pyproject.toml`, source, and test. Tested Windows/CPython 3.12.12 with uv 0.11.6. No failing test/lint result or suppressed warning occurred.
- Records: updated README commands/current scope, ADR 0001 and its index, phase checklist, project status, and AI-use record. Step 2 evidence remains historical; Phase 01 behavioral acceptance criteria remain unchecked. Final static/diff review is recorded below after execution.
- Final review: `git diff --check` passed (informational CRLF conversion warnings only). A temporary stdin helper run with `.venv/Scripts/python.exe -I -` passed for 22 Markdown files, 122 local links, balanced fenced blocks, unchanged versions for all previously locked dependencies, Step 3-only source additions, deferred later phases/acceptance, and generated-cache ignore rules. Inspected the final tracked/untracked file inventory; no unrelated code or later-step implementation changed.
- Limits: the single test verifies packaging, not application behavior. No API, configuration, logging, error handling, business rule, database, UI, container, model, CI, or pre-commit implementation was added. No external network/database/model is needed by the test. Application behavior and other platforms remain unverified.
- AI/review: assistant authored config/test/records and inspected outputs, using local tools plus official pytest/Ruff documentation. No subagents used and no human review/acceptance of this change is recorded. Active/cumulative work time is not recorded.
- Next action: Step 4, central configuration, only when requested. No commit or push was made by the assistant.

## 2026-10-29 - Phase 01, Step 4: central configuration

- Scope/state: user requested Step 4 after Steps 2-3. The worktree was clean at `986bd18`; inspected the phase guide, requirements/architecture and engineering guidance, current settings/package/tests, README, ADR, status, and .gitignore before editing.
- Work: added immutable Pydantic `Settings` and on-demand `get_settings()` in `src/mortgage_pricing/config.py`; added safe `.env.example`; added tests for defaults, env and dotenv precedence, invalid mode/bounds/database scheme, validation input hiding, and immutability. Documented configuration/setup usage in README; updated the Phase 01 checklist, architecture, project status, ADR 0001/index. No database/model/service connection or API behavior was added.
- Verification: first test run exposed a flawed test assertion that searched for invalid values also present in validation constraints; narrowed it to the unique invalid app-environment string and reran. Final `uv run --locked python -m pytest` -> **12 passed**. `uv run --locked python -m ruff check .`, `uv run --locked python -m ruff format --check .`, `uv lock --check` (24 packages), `uv pip check`, and `git diff --check` passed. Ruff formatter changed `config.py` before final successful checks. Git emitted informational LF-to-CRLF conversion warning. Windows/CPython 3.12.12, pytest 9.2.0, Ruff 0.17.3, uv 0.11.6.
- Limits: this verifies settings construction and existing package import only. No app startup, HTTP health/error response, logging, database connection, model discovery/inference, or cross-platform behavior was tested. Phase 01 remains incomplete and its acceptance criteria remain unchecked. No human code review/acceptance or work duration is recorded.
- Next action: Step 5 (minimal API and health endpoint), only on user request. No commit or push was made.

## 2026-10-29 - Phase 01, Step 5: minimal API and health endpoint

- Scope/state: user requested Step 5 after Step 4 commit `2ceb97e`. Inspected Git state and the phase guide, requirements/architecture, README, status, and ADR before edits; no uncommitted user changes were present.
- Work: added `create_app(settings=None)`, a typed process-liveness `GET /health`, and API tests for response shape and per-app settings isolation. Added `httpx2>=2,<3` to the dev group and lock because installed Starlette 1.10 deprecates legacy httpx in its TestClient and project pytest treats warnings as errors. Documented the launch/check commands; updated the phase checklist, architecture, ADR/index, status, README, AI usage, and this log. No business routes, structured logging, error envelope, readiness probes, or service connection were implemented.
- Verification: first test collection failed on Starlette's warning-as-error with legacy httpx; switched to its supported httpx2 dependency. Final `uv run --locked python -m pytest` -> **14 passed**. Ruff lint/format, `uv lock --check` (28 packages), `uv pip check`, and `git diff --check` passed. Live check: Uvicorn factory served at `127.0.0.1:8765`; PowerShell `Invoke-RestMethod` to `/health` returned `{"status":"ok"}`; server stopped after request. Windows/CPython 3.12.12, uv 0.11.6, FastAPI 0.162.0, Starlette 1.10.0.
- Limits/review: health is process liveness only, not dependency readiness. No error/logging behavior or cross-platform check. Assistant reviewed outputs; human review/acceptance and active work duration are not recorded. Phase acceptance remains unchecked and handoff remains due at phase completion. No commit/push.
- Next action: Step 6 (structured logging), only when requested.

## 2026-10-29 - Phase 01, Step 6: structured logging and correlation

- State/scope: inspected clean worktree at `5b8ed82`, app/settings/tests, phase/status, architecture, logging requirements, engineering guidance, and recent records. User authorized Step 6 only.
- Work: added independent per-app standard-library JSON logging, context-based correlation and pure ASGI request middleware. Added bounded/validated incoming IDs, UUID fallback, handled-response headers, completion/failure events, metadata allowlist and safe stack diagnostics. Added Uvicorn JSON configuration and documented `--no-access-log`. Updated README, architecture, phase checklist, ADR 0001/index, project status, and AI-use evidence. No dependencies changed.
- Checks: `uv run --locked python -m pytest tests/test_logging.py` initially passed 13 cases; added the 64-character boundary test before the full run. `uv run --locked python -m pytest` -> **28 passed** (14 logging cases). `uv run --locked python -m ruff check .` and `uv run --locked python -m ruff format --check .` passed. `uv lock --check` -> 28 packages; `uv pip check` -> all installed packages compatible. Formatter applied to new source/test files before verification. Final diff/record inspection is recorded below after execution.
- Live verification: `uv run --locked uvicorn mortgage_pricing.main:create_app --factory --host 127.0.0.1 --port 8765 --log-config config/logging.json --no-access-log`; a temporary stdin Python urllib client requested `/health` with ID `live-success` and `/missing?token=synthetic-secret` with ID `live-failure`. Observed 200/404 with matching response IDs and one JSON completion record each (INFO/success and WARNING/failure), durations, matched health route and null unknown route. Server lifecycle messages were JSON; the query secret was absent. Stopped the server after inspection.
- Review/limits: Windows/CPython 3.12.12 only. Tests cover overlapping async request isolation/reset, levels/handlers, safe metadata/diagnostics and correlation. Unhandled exceptions are logged/rethrown; their consistent envelope and response correlation remain Step 7 work. Phase remains incomplete; handoff remains due at completion. Assistant inspected outputs; human review/acceptance and work duration are not recorded. No commit/push.
- Next action: Step 7 (consistent, safe HTTP errors), only when requested.
- Final review: `git diff --check` passed after record updates (existing informational LF-to-CRLF warnings). Inspected new source/tests/configuration and final changed-file inventory; changes are limited to Step 6 and its records, with no dependency/lock changes or phase-completion claim.

## 2026-10-29 - Phase 01, Step 7: safe, consistent HTTP errors

- State/scope: inspected clean worktree at Step 6 commit `2f691b5`, app/tracing/settings, phase/status/architecture/error requirements and current records. User authorized Step 7.
- Work: added `errors.py` with typed error envelope, response builder and HTTP/validation handlers; registered handlers in the app factory. Extended the existing tracing boundary to log unexpected exceptions once and send safe correlated 500s before response start. Already-started responses still log/rethrow. Added 12 error tests and updated README, architecture, ADR/index, phase checklist, project status, and AI-use records. No dependencies changed; discussed directory refactor remains unapplied.
- Checks: `uv run --locked python -m pytest tests/test_errors.py` -> **12 passed**. Ruff initially flagged one long test comment; shortened it. Full `uv run --locked python -m pytest` -> **40 passed**; `uv run --locked python -m ruff check .` and `uv run --locked python -m ruff format --check .` passed; `uv lock --check` -> 28 packages; `uv pip check` -> all installed packages compatible. Windows/CPython 3.12.12.
- Live verification: temporary stdin Python script constructed the real app with one in-memory synthetic failure route and ran Uvicorn at `127.0.0.1:8765` using `config/logging.json` and `access_log=False`. A urllib client observed 200 `/health` and 500 `/__test_failure`; IDs `step7-success` and `step7-failure` matched response headers/logs, and the 500 body included the same ID and generic message. One diagnostic failure log contained RuntimeError type/locations with no synthetic exception message. Stopped the server; no test route/file was retained in application source.
- Review/limits: assistant inspected code and observed outputs; no human review/acceptance or duration recorded. Tests cover invalid config at app creation, safe malformed/invalid input, header/status fidelity, correlation/recovery, and already-started response failure. Fresh-environment final phase verification and handoff remain pending; no Phase 02 work, commit, or push.
- Next action: final Phase 01 verification and completion records, only when requested. Phase remains in progress.
- Final review: `git diff --check` passed after documentation updates (existing informational LF-to-CRLF warnings only). Inspected final changed-file inventory and error/tracing integration. Dependencies and lockfile are unchanged; no synthetic test route was retained in source.

## 2026-10-29 - Phase 01, Step 8: final verification and completion

- State/scope: inspected clean `main` at `e9358eb`, phase/status, settings/tests and relevant records/template. User requested final Phase 01 step. No later-phase work.
- Work: found `_env_file=None` left tests exposed to shell settings. Added `tests/conftest.py` autouse isolation (clear known settings variables and use temporary working directories). Added full precedence, valid `.env.example`, URL/model/timeout boundary checks. Optional UI scaffold omitted with rationale in ADR 0001; no UI functionality claimed. Created handoff from template and updated phase acceptance/tasks, ADR/index, README, architecture, project status and AI usage. Existing evidence entries preserved. No dependencies changed.
- Workspace commands/results: `uv run --locked python -m pytest` -> **48 passed**; `uv run --locked python -m ruff check .` -> all checks passed; `uv run --locked python -m ruff format --check .` -> 34 files already formatted; `uv lock --check` -> 28 packages; `uv pip check` -> all installed packages compatible. All passed on first Step 8 run.
- Fresh environment: a temporary stdin Python helper created `C:\Users\User\AppData\Local\Temp\mortgage-phase01-1w84odet\venv` and set only its child-process `UV_PROJECT_ENVIRONMENT` to that path (removed inherited `VIRTUAL_ENV`). `uv sync --locked` created the venv and installed 27 packages. `uv run --locked python -m pytest` -> **48 passed**; Ruff lint/format passed; `uv pip check --python <temporary-venv>/Scripts/python.exe` passed. The helper used subprocesses with the project working directory; the developer `.venv` was preserved.
- Fresh live API: copied `.env.example` only into the owned temporary directory. Ran `uv run --project <repository> --locked uvicorn mortgage_pricing.main:create_app --factory --host 127.0.0.1 --port 8765 --log-config <repository>/config/logging.json --no-access-log` there with the fresh venv. A urllib client observed 200 `/health` (`fresh-health`) and safe 404 `/missing?token=fresh-synthetic-secret` (`fresh-error`), matching response/log IDs, correct outcomes/status/durations, and no query secret. Stopped only that helper's server process tree.
- External-settings scenario: placed invalid APP_ENV/LOG_LEVEL values in the owned temporary `.env` and set invalid APP_ENV/LOG_LEVEL/LLM_MODE only in the child environment; `uv run --project <repository> --locked python -m pytest <repository>/tests` -> **48 passed** from that directory. Confirmed test isolation; ordinary invalid application config still fails as tested. Removed the owned temporary environment after checking its absolute parent/prefix. No user settings or storage were deleted.
- Environment: Windows, CPython 3.12.12, uv 0.11.6, FastAPI 0.162.0, Starlette 1.10.0, Uvicorn 0.54.0, Pydantic 2.14.1, Pydantic Settings 2.16.2, pytest 9.2.0, Ruff 0.17.3, httpx2 2.16.0. Fresh install used available package cache and editable source; no claim about empty caches/offline setup, other operating systems, or production suitability.
- Completion/limits: all Phase 01 acceptance criteria satisfied on the verified platform. UI/database/business/container/model capability remains unimplemented; failures after response start cannot replace responses. Human review/acceptance and active work duration are not recorded. No commits or pushes made. Static record/whitespace results are appended after execution below.
- Next action: Phase 02 database models, migrations, and seed data in a new chat when requested. Stop after Phase 01.
- Final static review: temporary stdin Python check passed for **23 Markdown files, 145 local links, balanced fences**, completed Phase 01 checkboxes, and handoff presence. `git diff --check` passed (existing informational LF-to-CRLF warnings only). Inspected changed-file inventory: Step 8 isolation/tests and completion records only; dependency/lock files unchanged. No user changes, model files, databases, or existing environments removed.

## 2026-10-29 - Phase 02, Step 1: baseline and persistence boundaries

- Scope/state: user authorized execution Step 1 only. Inspected the required repository instructions, project status, Phase 01 handoff, Phase 02 guide, requirements, architecture, engineering and commit guidance, ADR 0001/index, recent build/AI records, actual source, tests, and dependency metadata. The worktree was clean on `main` at `0bc29a0` before record updates. No unrelated user changes were present.
- Findings: Phase 01 is fully present in the current commit, despite the handoff's historical pre-commit wording. `DATABASE_URL` is validated configuration only. The repository contains no SQLAlchemy/Alembic dependency, persistence package, migration directory, seed command/data, database readiness behavior, or generated database. `/health` remains process liveness only. No normal or temporary database was opened.
- Commands/results: `uv run --locked python -m pytest` -> **48 passed**; `uv run --locked python -m ruff check .` -> passed; `uv run --locked python -m ruff format --check .` -> **35 files already formatted**; `uv lock --check` -> **28 resolved packages**; `uv pip check` -> **29 installed packages checked, all compatible**. Runtime: uv 0.11.6, Windows, CPython 3.12.12.
- Records: marked Phase 02 In progress and execution Step 1 complete; added the twelve user-gated execution steps; updated project status and implementation-plan status; appended AI-use evidence. No Phase 02 implementation task or acceptance criterion was checked. ADR 0002 and the Phase 02 handoff remain due when their implementation evidence exists.
- Limits/review: this step verifies the foundation baseline only. It provides no database, migration, seed, transaction, persistence, readiness, business, container, or model evidence. Assistant inspected the actual results. Human review/acceptance and active/cumulative work time are not recorded.
- Next action: execution Step 2 (persistence foundation), only after user instruction. No dependency/source behavior change, commit, or push.
- Final record review: `git diff --check` passed. The final inventory contains only five Phase 02 progress/evidence documents. All implementation-task and acceptance-criteria checkboxes remain unchecked.

## 2026-10-29 - Phase 02, Step 2: persistence foundation

- Scope/state: user authorized execution Step 2 only. Inspected clean `main` at `54e219e`, the committed Step 1 records, applicable instructions, settings/app/logging/errors/tests, dependency metadata, and ADR template/index. No unrelated changes were present. This increment adds resource factories and configuration; Step 3's SQLite integrity/driver transaction work remains pending.
- Work: added SQLAlchemy/Alembic dependencies, shared empty metadata with deterministic constraint/index names, lazy SQLite engine and session factories, `SQLITE_BUSY_TIMEOUT_SECONDS` (default 5; greater than 0 and at most 30), database/sidecar ignore rules, and 11 isolated file-backed foundation tests. Added three timeout validation cases and assertions for default/env override. No generic repositories, global engines/sessions, business models, schema bootstrap, migration, seed, or API lifecycle/readiness wiring.
- Dependencies: `uv add "sqlalchemy>=2.0.55,<2.1" "alembic>=1.16,<2"` resolved **33 packages**, rebuilt the editable project, and installed Alembic 1.20.1, Mako 1.4.3, and MarkupSafe 3.0.4. SQLAlchemy 2.0.55 and greenlet 3.5.6 were already in the ignored environment. A stdin Python/tomllib comparison against `git show HEAD:uv.lock` verified all **28 prior package versions unchanged**; new lock entries are alembic, greenlet, mako, markupsafe, and sqlalchemy. This is not a fresh-environment verification.
- Design: direct SQLAlchemy `sessionmaker` contexts own commit/rollback/closure; the caller disposes the engine after sessions close. The factory receives existing immutable Settings and does no construction-time I/O. It supports SQLite only and safely rejects reserved PostgreSQL URL forms before driver loading. SQLite DBAPI timeout is configured; thread checks are disabled for pooled worker use, while sessions remain operation-owned. Echo is disabled, bound values hidden in exception text, and logging/error translation remains with the existing caller boundary. API lifecycle wiring is deferred to Step 11 because the API does not own an engine yet. See ADR 0002 for scope and tradeoffs.
- Commands/results: `uv run --locked python -m pytest tests/persistence tests/test_config.py` -> **33 passed**; `uv run --locked python -m pytest` -> **62 passed**; `uv run --locked python -m ruff check .` -> passed; `uv run --locked python -m ruff format --check .` -> **39 files already formatted**; `uv lock --check` -> **33 packages**; `uv pip check` -> **32 installed packages compatible**; `uv run --locked python -m alembic --version` -> **alembic 1.20.1**. Initial scoped lint found one long assertion; formatting corrected it before final lint. No test failed and no warning rule was suppressed.
- Evidence: imports in an isolated interpreter with invalid app settings caused no settings load/storage creation. Engine/session construction created no database; a missing parent failed without creating directories. A connection created no schema and reported the configured 250 ms test timeout. Test-only probe tables verified commit/reopen through a new engine, rollback/recovery, plain session closure without commit, independent database files, and pool connection return after context exit. Duplicate probe inserts verified hidden bound values in exception text. Normal storage was never opened/reset; no user data was removed.
- Records: Step 2 checked in the guide; all implementation tasks and six phase acceptance criteria remain pending. Created ADR 0002 with Implemented status restricted to Step 2, registered it, and updated README, architecture, implementation-plan status, project status, and AI-use record. Phase completion handoff remains due.
- Limits/review: Windows, CPython 3.12.12, SQLite 3.50.4, uv 0.11.6, pytest 9.2.0, Ruff 0.17.3. Foreign keys and explicit SQLite transaction mode are not implemented yet; these factories are not ready for business writes. No DDL/savepoint/lock-contention guarantee, business workflow, migration/seed/readiness result, cross-process restart, fresh installation, other-platform, or live-model evidence is claimed. Assistant reviewed code/results using official SQLAlchemy/Alembic documentation; human review/acceptance and active/cumulative time are not recorded. No subagents, commits, or pushes.
- Static review: a stdin Python check passed for **24 Markdown files, 164 local links, balanced fences**, Steps 1-2 checked, Steps 3-12 pending, and all six acceptance criteria unchecked. Confirmed API/logging/error modules unchanged and business models/migrations/seed absent. `git diff --check` passed; Git emitted existing informational LF-to-CRLF warnings. `git check-ignore data/check.db check.db check.db-journal check.db-wal check.db-shm check.sqlite check.sqlite3` confirmed exclusions without creating those paths. Reviewed tracked/untracked files and source/test changes; scope is Step 2 plus its records.
- Next action: Step 3 (SQLite transaction configuration), only after the user's instruction. Stop before Step 3.

## 2026-10-29 - Phase 02, Step 3: SQLite transaction configuration

- Scope/state: user authorized Step 3 only. Inspected a clean worktree, existing persistence code/tests, phase guide, ADR, status, and recent evidence. No unrelated changes were present.
- Work: configured Python 3.12+ sqlite3 `autocommit=False`; installed an engine-local connection listener that temporarily enables autocommit for `PRAGMA foreign_keys=ON`, then restores the previous mode. Existing timeout and session ownership remain. Added five isolated file-backed transaction tests. No business tables, migration, seed, API wiring, or automatic lock retry.
- Actual checks: `uv run --locked python -m pytest tests/persistence -q` -> **16 passed**; `uv run --locked python -m pytest -q` -> **67 passed**; `uv run --locked python -m ruff check .` -> passed; `uv run --locked python -m ruff format --check .` -> **41 files already formatted**; `uv lock --check` -> **33 packages**; `uv pip check` -> **32 compatible packages**. Initial lint found one unused import, nested-with formatting, and one long line; corrected them, then final lint/format passed. No test failed.
- Evidence: two concurrent connections each report `foreign_keys=1` and reject a missing parent; the DBAPI reports `autocommit=False`. DDL without prior DML rolls back. Nested savepoint rollback retains the outer write; a released savepoint's write rolls back with the outer transaction. A competing writer gets a bounded `database is locked` error at 100 ms test timeout, then succeeds after the first writer commits and the failed transaction is rolled back.
- Limits/review: tests use temporary probe tables/files only; the normal database was not opened/reset. No automatic retry, update-conflict protocol, WAL tuning, cross-process test, business-model integrity, migrations, seeds, or readiness result is claimed. Assistant reviewed source/results using official SQLAlchemy SQLite guidance. Human review/acceptance and active time are not recorded. No commits/pushes.
- Records: updated Phase 02 guide, ADR/index, architecture, implementation plan, README, project status, and AI-use record. The session/SQLite configuration task is checked; all six phase acceptance criteria remain pending. Step 4 requires user instruction.

## 2026-10-29 - Phase 02, Step 4: users, roles, and applications

- Scope/state: user authorized Step 4 only. Inspected clean `main` at `0add25c`, existing SQLite behavior, persistence foundation, required data rules, and project records. No unrelated changes were present.
- Work: added ORM models for users, user-role memberships, and mortgage applications; added a small UTC SQLite datetime type; added six isolated model tests. A user can hold one or both current roles. Application ownership has a user foreign key and a composite foreign key to the relationship-manager role membership, so a reviewer-only user cannot own an application. UUIDs, unique nonblank logins/references, and timestamps are modeled. No migration, seed, API endpoint, service, normal database, or schema bootstrap was added.
- Actual checks: `uv run --locked python -m pytest tests/persistence/test_models.py -q` -> **6 passed**; `uv run --locked python -m pytest tests/persistence -q` -> **22 passed**; final full-suite/static checks are recorded below. Initial model tests found SQLite did not restore timezone data from `DateTime(timezone=True)` and an invalid enum test reached SQLAlchemy validation instead of the database. Added UTC normalization/restoration and used driver SQL to verify the database enum check. No test was suppressed.
- Evidence: tests persist/reopen an application with a multi-role manager; reject duplicate login, reference, and membership; reject absent or reviewer-only owners; reject an unrecognized role at the database; and reject blank identifiers. `Base.metadata.create_all()` runs only in pytest-owned temporary file databases. The live/normal database was not opened, reset, or removed.
- Limits/review: ownership remains a structural guarantee only. Later service code must enforce acting-user permissions, application ownership for submissions/revisions, read access, and self-review. SQLite schema exists only in tests until Step 9 Alembic migration. Assistant inspected source and results; human review/acceptance and active time are not recorded. No commit/push.
- Records: updated Phase 02 guide, ADR/index, architecture, implementation plan, README, project status, and AI-use record. User/application task is checked; all acceptance criteria remain pending. Step 5 requires user instruction.
- Final review: `uv run --locked python -m pytest -q` -> **73 passed**; `uv run --locked python -m ruff check .` -> passed; `uv run --locked python -m ruff format --check .` -> **44 files already formatted**; `uv lock --check` -> **33 packages**; `uv pip check` -> **32 compatible packages**. `git diff --check` passed; Git issued only existing LF-to-CRLF informational warnings. Reviewed the changed-file inventory and confirmed no migration, seed, API, or later-step file was added.

## 2026-10-29 - Phase 02, Step 5: logical requests and versions

- Scope/state: user authorized Step 5 only. Inspected Git, actual Step 4 models/tests, Phase 02 guide, requirements, architecture, ADR, and status. Step 4 changes were still uncommitted; preserved them.
- Work: added one logical `PricingRequest` per application and `RequestVersion` with composite request/number identity, exact integer basis-point discount, nonblank bounded reason, submitter, and UTC time. Composite foreign key constrains the nullable current-version pointer to the same request. ORM events reject version updates/deletes; direct SQL immutability requires Step 9 database triggers. No operation service, migration, seed, or API wiring.
- Tests: new `tests/persistence/test_request_versions.py` has ten file-backed cases for preserved versions/current pointer, duplicate request/number, wrong or absent current pointer, invalid terms including overlong reason, missing actor, and ORM update/delete rejection. Initial test run had four failures because a helper flushed an application before its manager role membership, and a later run had one detached-instance test error; helper/test corrected. No warning was suppressed.
- Final checks: `uv run --locked python -m pytest tests/persistence/test_request_versions.py -q` -> **10 passed**; `uv run --locked python -m pytest -q` -> **83 passed**; `uv run --locked python -m ruff check .` -> passed; `uv run --locked python -m ruff format --check .` -> **45 files already formatted**; `uv lock --check` -> **33 packages**; `uv pip check` -> **32 compatible packages**. `git diff --check` passed with an informational LF-to-CRLF warning.
- Limits/review: test-only `Base.metadata.create_all()` runs in pytest-owned temporary SQLite files. A null current pointer is an insertion intermediate; Step 8 must enforce complete operation transactions. Direct SQL can still update/delete submitted rows until Step 9 migration triggers. No phase acceptance criterion is marked complete. Assistant reviewed actual results; human review/acceptance and active time are not recorded. No commit/push. Step 6 awaits user instruction.

## 2026-10-29 - Phase 02, Step 6: decisions and history

- Scope/state: user authorized Step 6 only. Inspected clean `main` at `f3ae4d1`, actual models, Phase 02 guide, requirements, architecture, ADR, and prior evidence. No unrelated changes.
- Work: added `PricingDecision` with approved/declined outcome, exact version key, reviewer-role membership, UTC time, and one-decision-per-version uniqueness. Added typed `RequestHistoryEvent` with exact version, actor, and UTC time. Neither stores a duplicate discount. ORM mapper events reject update/delete for decisions and history. No service, API, migration, seed, or ordinary database was created.
- Tests: `uv run --locked python -m pytest tests/persistence/test_decisions_history.py -q --tb=short` -> **7 passed**. File-backed cases cover persisted exact-version decision/history actor/time, duplicate decision, absent version, reviewer-only decision maker, and ORM update/delete rejection. Full `uv run --locked python -m pytest -q` -> **90 passed**. All test databases are pytest-owned temporary SQLite files.
- Final checks: `uv run --locked python -m ruff check .` -> passed; initial `ruff format --check .` found one formatting change, corrected with `uv run --locked python -m ruff format src/mortgage_pricing/persistence/models.py`, final `uv run --locked python -m ruff format --check .` -> **46 files already formatted**; `uv lock --check` -> **33 packages**; `uv pip check` -> **32 compatible packages**.
- Limits/review: self-review by a dual-role user, current-version freshness, and decision/history atomicity need Step 8 operation rules. Direct SQL can bypass mapper immutability until Step 9 migration triggers. No human review/acceptance or active time recorded; no commit/push. Step 7 requires user instruction.
- Final static review: `git diff --check` passed (Git showed only informational LF-to-CRLF warnings). Inspected changed-file inventory: Step 6 models/tests and records only; no migration, seed, API, or later-phase file.

## 2026-10-29 - Phase 02, Step 7: caller-scoped idempotency storage

- Scope/state: user authorized Step 7 only. Inspected clean `main` at `882bdfa`, existing models, Phase 02 guide, requirements, ADR, and project status. No unrelated changes.
- Work: added `CreationIdempotencyRecord` with `(caller_id, key)` primary key, lowercase 64-character SHA-256 input fingerprint, version-1 original result reference, and UTC time. Database constraints require a nonblank 1-128-character key, valid fingerprint, existing caller, and existing version. ORM events reject changes/deletion of retry mappings. No canonicalization, replay service, operation transaction, migration, seed, or API endpoint was added.
- Tests: `uv run --locked python -m pytest tests/persistence/test_idempotency.py -q --tb=short` initially -> **11 passed**; added whitespace-only key test and version-1 constraint. Final focused run -> **12 passed**. File-backed cases cover same key for separate callers, duplicate same-caller key, stable original mapping, invalid key/fingerprint, missing references, and ORM immutability. Tests use only pytest-owned temporary SQLite files.
- Checks: full `uv run --locked python -m pytest -q` -> **102 passed**. `uv lock --check` -> **33 packages** and `uv pip check` -> **32 compatible packages**. Initial Ruff lint found one long test line and formatter found two files; formatted both. Final `uv run --locked python -m ruff check .` -> passed; `uv run --locked python -m ruff format --check .` -> **47 files already formatted**; `git diff --check` -> passed with informational LF-to-CRLF warnings.
- Limits/review: Step 8 must define canonical input and replay/conflict semantics and write request/version/history/idempotency atomically. Direct SQL immutability needs Step 9 migration triggers. Assistant inspected code/results; no human review/acceptance or active time recorded. No normal database, commit, or push. Step 8 requires user instruction.

## 2026-10-29 - Phase 02, Step 8: atomic persistence operations

- Scope/state: user authorized Step 8 only. Began from clean `main` at `b76a404`; inspected the guide, requirements, architecture, ADR, code, and Git state. No unrelated changes.
- Work: added `persistence/operations.py` with atomic create, revise, and decide functions. Creation fingerprints deterministic JSON of exact input, replays the original version for the same caller/key/input, and conflicts on changed input or another key for the same application. Operations enforce manager/reviewer roles, manager ownership, self-review, expected current version, and terminal decisions. Each change and its history share one transaction; first-statement no-op UPDATE obtains the SQLite writer lock before mutable reads. No automatic lock retry.
- Tests: `uv run --locked python -m pytest tests/persistence/test_operations.py -q --tb=short` -> **8 passed**. Temporary file-backed tests cover replay after revision, conflicting keys, permissions, stale and duplicate decisions, rollback when creation or decision history fails, competing decisions and revisions, and bounded writer contention. Full `uv run --locked python -m pytest -q` -> **110 passed**.
- Checks: initial Ruff lint found import order and a long test line; initial format check found two files. Corrected with `ruff check --fix` and `ruff format`. Final `uv run --locked python -m ruff check .` -> passed; `uv run --locked python -m ruff format --check .` -> **49 files already formatted**; `uv lock --check` -> **33 packages**; `uv pip check` -> **32 compatible packages**.
- Limits/review: tests alone create schema in isolated files. Migration/SQL triggers, seed, API error mapping/endpoints, and database readiness remain pending. SQLite-specific no-op locking is documented in ADR 0002. `git diff --check` passed with informational LF-to-CRLF warnings. `AGENTS.md` changed separately during this step; the assistant did not edit it and preserved that change. Assistant inspected results; human review/acceptance and active time are not recorded. No normal database, commit, or push. Step 9 requires user instruction.

## 2026-10-29 - Phase 02, Step 9: initial Alembic migration

- Scope/state: user authorized Step 9 only. Began from clean `main` at `dac5937`; inspected migration requirements, actual models, persistence operations, and Git state.
- Work: added Alembic configuration and revision `20261029_0001` to create every Phase 02 table and constraint. It adds SQLite triggers that abort direct update/delete attempts for submitted versions, decisions, history events, and idempotency mappings. The environment reads validated settings on invocation and supports injected temporary settings in tests; it does not create application schema at import/startup.
- Tests: `uv run --locked python -m pytest tests/persistence/test_migrations.py -q --tb=short` -> **3 passed**. Tests use temporary file-backed databases to apply/reapply, downgrade/re-upgrade, preserve data across a repeat upgrade, and verify foreign-key and trigger failures. `alembic check` was evaluated but SQLite reflection reports false remove/add unique-constraint differences, so it is not used as acceptance evidence.
- Final checks: `uv run --locked python -m pytest -q` -> **113 passed**; `uv run --locked python -m ruff check .` -> passed; `uv run --locked python -m ruff format --check .` -> **53 files already formatted**; `uv lock --check` -> **33 packages**; `uv pip check` -> **32 compatible packages**.
- Limits/review: no normal database was created. Seed data, API readiness, and phase acceptance completion remain pending. Assistant inspected code/results; human review/acceptance and active time are not recorded. No commit/push. Step 10 requires user instruction.

## 2026-10-29 - Phase 02, Step 10: repeatable synthetic seed data

- Scope/state: user authorized Step 10 only. Began from clean `main` at `e61dc05`; inspected seed requirements, migrated schema, operations, configuration, logging, and Git state.
- Work: added `mortgage_pricing.seed` with fixed UUIDv5 fictional users and applications. It requires an applied migration, runs in one transaction, creates only missing matching rows, preserves unrelated data, and raises a conflict rather than altering a seeded identifier collision. `SYN-MORTGAGE-DEMO-CLEAN` has no request. The module command emits a JSON success/failure outcome event without record content.
- Tests: `uv run --locked python -m pytest tests/persistence/test_seed.py -q --tb=short` -> **5 passed**. Temporary file-backed migration/seed cases cover repeat execution, clean demo state, unrelated data, rollback on collision, missing schema, and safe command output. Full `uv run --locked python -m pytest -q` -> **118 passed**.
- Final checks: `uv run --locked python -m ruff check .` -> passed; `uv run --locked python -m ruff format --check .` -> **55 files already formatted**; `uv lock --check` -> **33 packages**; `uv pip check` -> **32 compatible packages**.
- Limits/review: no normal database was opened or seeded. No sample requests, decisions, or history are created. API readiness and final phase acceptance remain pending. Assistant inspected code/results; human review/acceptance and active time are not recorded. No commit/push. Step 11 requires user instruction.

## 2026-10-29 - Phase 02, Step 11: database readiness

- Scope/state: user authorized Step 11 only. Began from clean `main` at `54acbdc`; inspected API, settings, persistence factory, error envelope, and phase records.
- Work: added `GET /ready` to check an existing configured SQLite file and current Alembic revision. Missing or unmigrated storage returns safe correlated 503; `/health` remains process liveness. The app owns a lazy engine and disposes it at lifespan shutdown. No optional AI probe or schema creation.
- Tests: `uv run --locked python -m pytest tests/test_readiness.py -q --tb=short` -> **2 passed**. Temporary databases cover migrated readiness, missing/unmigrated 503, no absent-file creation, and healthy process liveness during storage failure. Full `uv run --locked python -m pytest -q` -> **120 passed**. Initial Ruff lint/format findings were corrected.
- Final static checks: `uv run --locked python -m ruff check .` passed; `uv run --locked python -m ruff format --check .` -> **56 files already formatted**; `git diff --check` passed with informational LF-to-CRLF warnings.
- Limits/review: whole-phase acceptance and handoff remain Step 12. No normal database, commit, or push; no human review/acceptance or active time recorded.

## 2026-10-29 - Phase 02, Step 12: final verification and handover

- Scope/state: user authorized the final Phase 02 step. Began from clean `main` at `6d743d7`, then added a single isolated acceptance scenario and completed the required phase records. No normal database, user data, commit, or push was created, opened, reset, or removed.
- Work: added `tests/test_phase_02_acceptance.py`. It creates a pytest-owned file-backed SQLite database, applies the migration twice, seeds twice, closes/disposes the first engine, opens a new engine to verify persisted data, then verifies `GET /ready` through the application factory.
- Observed checks: `uv run --locked python -m pytest tests/test_phase_02_acceptance.py -q` -> **1 passed**; `uv run --locked python -m pytest -q` -> **121 passed**; `uv run --locked python -m ruff check .` -> passed; `uv run --locked python -m ruff format --check .` -> **58 files already formatted**; `uv lock --check` -> **33 packages**; `uv pip check` -> **32 installed packages compatible**; `git diff --check` -> passed.
- Acceptance evidence: existing migration tests show repeat upgrade safety, foreign-key enforcement, uniqueness, trigger-protected immutable rows, and downgrade/re-upgrade; seed tests show repeatability, unrelated-row preservation, and collision rollback; operation tests show multi-record rollback; readiness tests show safe 503 behavior without creating missing storage. The new acceptance scenario verifies their principal operational path together. Assistant inspected the actual results.
- Limits/review: Windows/CPython 3.12.12 only. No production deployment, backup/recovery, multi-instance database behavior, live business HTTP workflow, live model, human review, human acceptance, or active work duration is claimed. Phase 03 remains unstarted.

## 2026-10-29 - Phase 03: business rules, API, and final acceptance

- Scope/state: implemented the six user-gated Phase 03 steps from the Phase 02 operations. Final completion began on clean `main` at `615a480` (one commit ahead of `origin/main`). The assistant made no commit/push and used only temporary synthetic databases for checks.
- Implemented: configured demo identity, seed lookups, create/list/details/history, revisions, exact-version decisions, current-only approved pricing, error mapping, OpenAPI, and metadata-only operational events. Final review added missing HTTP read/filter/retry acceptance coverage, aligned OpenAPI validation errors with the common envelope, and rejected values beyond SQLite's signed 64-bit storage limit before writes. This technical limit is not a bank threshold.
- Focused implementation evidence: `uv run --locked python -m pytest tests/test_api_foundation.py tests/test_api.py tests/test_errors.py -q` -> 16 passed; `uv run --locked python -m pytest tests/test_api_create.py tests/test_api_foundation.py tests/persistence/test_operations.py -q` -> 13 passed; `uv run --locked python -m pytest tests/test_api_workflow.py tests/test_api_create.py tests/persistence/test_operations.py -q` -> 14 passed; `uv run --locked python -m pytest tests/test_api_pricing.py tests/test_api_workflow.py tests/persistence/test_operations.py -q` -> 12 passed.
- Final gate: `uv run --locked python -m pytest -q` -> 133 passed (the earlier interrupted Step 6 run passed 130 before the added acceptance tests). `uv run --locked python -m pytest tests/test_phase_03_acceptance.py -q --tb=short` -> 3 passed, including the explicit 25-to-40-bps revision/approval path and original-reference retries after later changes. The full suite was repeated after those final acceptance assertions changed and again passed 133. `uv run --locked python -m ruff check .` -> passed; `uv run --locked python -m ruff format --check .` -> 68 files formatted; `uv lock --check` -> 33 resolved packages; `uv pip check` -> 32 compatible installed packages. `git diff --check` passed with informational Windows line-ending warnings after correcting an extra trailing blank line in this log. No dependencies changed.
- Material failures/corrections: initial lint/format findings were fixed. A new race-test assertion passed a string instead of a UUID to SQLAlchemy; corrected and rerun successfully. The first Step 5 live script imported unavailable `httpx` (the project uses `httpx2`); it stopped before HTTP requests. The standard-library HTTP client then completed live approval/decline checks. The first Step 6 response stopped after tests and left the phase records incomplete; this finalization resolves that omission. No failure was counted as acceptance evidence.
- Live HTTP: Step 5's real Uvicorn/urllib run created both requests (201), inspected pending state (200), approved or declined as the fictional reviewer (200), retrieved pricing (200: version 1/25 bps or `none`), and inspected two-event histories with reviewer/time (200). The final command below repeats those paths and adds revision to 40 bps, no current approval while pending, stale decision 409, original creation replay 200/version 1, and final approval of version 2/40 bps. The TCP server and migrated seed database are temporary; they are distinct from TestClient fixtures.

| Acceptance | Observed evidence |
| --- | --- |
| AC-01, AC-02 | Pricing/workflow tests and actual TCP approval/decline scenarios; exact pricing reference, reviewer, UTC time, and history |
| AC-03 | Create tests and final acceptance test: matching and changed input, caller scope in persistence tests, new-key conflict, original-reference replay after decisions/revision |
| AC-04 | Final acceptance test and live revision: 25 -> 40, pending suppresses pricing, old approval remains historical, version 2 approval returns 40 |
| AC-05 | Workflow tests reject stale reviews without a new decision/history row |
| AC-06 | Role/ownership/self-review tests; separate-request sessions/connections on file-backed SQLite for competing creates/decisions and revision-versus-decision; coherent current pending terms |
| Atomic failures | Existing persistence failure-injection tests roll back create/retry/history and decision/history together |
| Contract/access | Read/filter/missing-resource tests; common OpenAPI validation envelope; default-disabled/missing/unknown demo identities |

- Limits/review: assistant inspected commands, responses, and code. Windows/CPython 3.12.12 only; no human review/acceptance or active duration recorded. No production authentication, cross-platform/multi-instance guarantee, backup/recovery, UI, containers, model, or private infrastructure. Lists are unpaginated; lock waits are bounded with no automatic retry. Phase 04 remains unstarted.

## 2026-10-29 - Phase 04: user interface and final acceptance

- Scope/result: completed the minimal Streamlit Requests, Review, and History interface with HTTP-only API access, session-scoped demo identity/AI preference/create retry intent, explicit writes, version-aware decisions, current-pricing/history display, and safe backend/stale states. The only final code correction was a source-script import fallback because `streamlit run ui/app.py` does not make root `ui` importable as a package. No API contract gap blocked this phase.
- Automated evidence: `uv run --locked python -m pytest tests/test_ui_app.py tests/test_ui_client.py -q --tb=short` -> **13 passed**. Coverage includes separate AppTest sessions, identity/role navigation, no writes from reruns/filters/toggle, timeout/envelope/correlation handling, retained create payload/key on retry, decision opened-version payload, and stale-version refresh without repost.
- Live evidence: assistant-operated browser UI against Uvicorn and an isolated temporary migrated/seeded SQLite file created request `1b3993a4-8082-43f2-af55-31a27bb711ea` (25 bps); Blake Reviewer approved version 1 and the request detail showed current 25 bps. Ada Manager revised it to 40 bps (version 2), the UI showed pending/new terms and no current approved pricing, Blake approved version 2, and the UI displayed current 40 bps with both version decisions in History (version 1 explicitly historical). A second synthetic request on `SYN-MORTGAGE-DEMO-CLEAN` (15 bps) was declined by Blake and History showed the actor/time. An HTTP decision attempt as `ada.manager` returned **403 forbidden** with the standard correlated error envelope. Final backend reads confirmed version 2/40 bps remained current and the second request stayed declined after the forbidden call. This exercises live create/approve/retrieve, revision/review, decline/history, and a direct backend permission check. The AppTest fake-client scenarios, not a second live browser session, establish per-session toggle isolation and simulated stale/failure/rerun behavior.
- Gate commands/results: `uv run --locked python -m ruff check .` -> passed; `uv run --locked python -m ruff format --check .` -> 73 files formatted; `uv lock --check` -> 59 packages resolved; `uv pip check` -> 58 installed packages compatible; `uv run --locked python -m pytest -q` -> **146 passed**; `git diff --check` -> passed (Git reported an informational LF-to-CRLF warning for `ui/app.py`). No dependencies changed.
- Material issue/limits: an earlier browser tab had lost its Streamlit websocket after the script reload; a fresh loopback UI session completed the actions and confirmed backend state. The root `ui/` source directory is intentionally outside the Python wheel's `packages` list and must be copied into the Phase 05 shared runtime image. Windows/CPython 3.12.12 only. No container, production authentication, cross-platform behavior, live LLM, human review/acceptance, or active work duration is claimed. Temporary live data was synthetic; no user database was touched.
- Exact verification command sequence: focused UI tests; lint; format check; lock/dependency check; final full suite; `git diff --check` as listed above. See [ADR 0004](adr/0004-user-interface.md), [Phase 04 guide](phases/phase-04-user-interface.md), and [handoff](handoffs/phase-04.md). No commit or push.
- Documentation check: the final local-link/fence/acceptance check reported **27 Markdown files**, **223 local links**, **16 Phase 04 boxes checked**, and a **299-word handoff**; the subsequent `git diff --check` passed.

<details>
<summary>Exact final live HTTP command (repository root, PowerShell)</summary>

```powershell
@'
import json
import socket
import tempfile
import threading
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import uvicorn
from alembic import command
from alembic.config import Config
from mortgage_pricing.config import Settings
from mortgage_pricing.main import create_app
from mortgage_pricing.seed import APPLICATIONS, seed_database

with tempfile.TemporaryDirectory(prefix="phase03-live-") as temporary:
    settings = Settings(_env_file=None, log_level="ERROR", demo_identity_mode="header",
        database_url=f"sqlite:///{(Path(temporary) / 'live.db').as_posix()}")
    config = Config(str(Path("alembic.ini").resolve()))
    config.attributes["settings"] = settings
    command.upgrade(config, "head")
    seed_database(settings)
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(create_app(settings), host="127.0.0.1",
        port=port, log_level="error", access_log=False))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    def call(path, method="GET", headers=None, body=None):
        data = json.dumps(body).encode() if body is not None else None
        supplied = {**(headers or {}), "X-Correlation-ID": "phase03-live"}
        if data is not None:
            supplied["Content-Type"] = "application/json"
        request = Request(f"http://127.0.0.1:{port}{path}", data=data,
            method=method, headers=supplied)
        try:
            with urlopen(request, timeout=5) as response:
                assert response.headers["X-Correlation-ID"] == "phase03-live"
                return response.status, json.load(response)
        except HTTPError as error:
            with error:
                return error.code, json.load(error)
    try:
        for _ in range(100):
            try:
                if call("/health")[0] == 200:
                    break
            except OSError:
                time.sleep(0.05)
        else:
            raise RuntimeError("server did not start")
        manager = {"X-Demo-User": "ada.manager"}
        reviewer = {"X-Demo-User": "blake.reviewer"}
        results = {}
        for index, outcome in ((0, "approved"), (1, "declined")):
            application_id = str(APPLICATIONS[index].id)
            terms = {"application_id": application_id, "discount_bps": 25 + index,
                "reason": "Synthetic live HTTP scenario"}
            headers = {**manager, "Idempotency-Key": f"live-{index}"}
            status, created = call("/requests", "POST", headers, terms)
            assert status == 201
            request_id = created["request_id"]
            url = f"/requests/{request_id}"
            pricing_url = f"/applications/{application_id}/approved-discount"
            assert call(url, headers=manager)[1]["status"] == "pending"
            assert call(url + "/decisions", "POST", reviewer,
                {"expected_version": 1, "outcome": outcome})[0] == 200
            pricing = call(pricing_url, headers=manager)[1]
            assert pricing["status"] == ("approved" if outcome == "approved" else "none")
            history = call(url + "/history", headers=reviewer)[1]
            assert [event["event_type"] for event in history] == ["created", outcome]
            assert history[-1]["actor_login"] == "blake.reviewer"
            assert history[-1]["occurred_at"]
            results[outcome] = {"create": status, "pricing": pricing["status"],
                "history_events": len(history), "reviewer": history[-1]["actor_login"]}
            if outcome == "approved":
                assert pricing["version_number"] == 1 and pricing["discount_bps"] == 25
                assert call(url + "/revisions", "POST", manager,
                    {"expected_version": 1, "discount_bps": 40, "reason": "Synthetic revision"})[0] == 201
                assert call(pricing_url, headers=reviewer)[1]["status"] == "none"
                stale = call(url + "/decisions", "POST", reviewer,
                    {"expected_version": 1, "outcome": "approved"})
                assert stale[0] == 409 and stale[1]["error"]["code"] == "stale_version"
                replay_status, replay = call("/requests", "POST", headers, terms)
                assert replay_status == 200 and replay == {**created, "replayed": True}
                assert call(url + "/decisions", "POST", reviewer,
                    {"expected_version": 2, "outcome": "approved"})[0] == 200
                current = call(pricing_url, headers=reviewer)[1]
                assert current["version_number"] == 2 and current["discount_bps"] == 40
                results[outcome].update(replay_version=replay["version_number"],
                    stale_status=stale[0], current_version=2, current_discount_bps=40)
        print(json.dumps(results, sort_keys=True))
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        assert not thread.is_alive(), "server did not stop"
'@ | uv run --locked python -
```

</details>

<details>
<summary>Exact documentation completeness/link check (PowerShell)</summary>

```powershell
@'
import re
from pathlib import Path
paths = [Path('README.md'), Path('docs/project-status.md'), Path('docs/phase-03-api-contract.md'), Path('docs/phases/phase-03-business-rules-and-api.md'), Path('docs/adr/0003-business-rules-and-api.md'), Path('docs/adr/README.md'), Path('docs/handoffs/phase-03.md'), Path('docs/requirements.md'), Path('docs/architecture.md'), Path('docs/implementation-plan.md'), Path('docs/build-log.md'), Path('docs/ai-usage.md')]
links = 0
for path in paths:
    raw = path.read_text(encoding='utf-8')
    fence = chr(96) * 3
    assert raw.count(fence) % 2 == 0, f'Unbalanced fences: {path}'
    text = re.sub(fence + r'.*?' + fence, '', raw, flags=re.S)
    for target in re.findall(r'\]\(([^)]+)\)', text):
        if '://' in target or target.startswith('#'):
            continue
        resolved = (path.parent / target.split('#')[0]).resolve()
        assert resolved.exists(), f'Missing {path}: {target}'
        links += 1
phase = Path('docs/phases/phase-03-business-rules-and-api.md').read_text(encoding='utf-8')
assert '- [ ]' not in phase and phase.count('- [x]') == 18
words = len(Path('docs/handoffs/phase-03.md').read_text(encoding='utf-8').split())
print(f'{len(paths)} documentation files checked; {links} local links exist; 18 Phase 03 checkboxes checked; handoff {words} words.')
'@ | uv run --locked python -
```

Observed: 12 documentation files, 110 local links exist, all 18 phase task/acceptance boxes checked, and handoff 287 words. This checks local link targets and fence balance, not external sites or business behavior.

</details>

## 2026-10-29 - Phase 04: single-process HTML UI update

- Change: replaced Streamlit with separate `ui/index.html`, `ui/styles.css`, and `ui/app.js` assets served by FastAPI. Removed Streamlit runtime dependencies and `UI_API_URL`; same-origin browser calls retain configured timeout, error envelopes, correlation IDs, demo identity, and idempotency behavior. [ADR 0009](adr/0009-single-process-html-ui.md) supersedes the runtime choice in ADR 0004.
- Focused verification: `uv run --locked python -m pytest tests/test_ui_serving.py tests/test_api.py tests/test_api_foundation.py tests/test_config.py -q --tb=short` -> 27 passed; `uv run --locked python -m ruff check .` -> passed; initial `uv run --locked python -m ruff format --check .` found one formatting issue in `tests/test_ui_serving.py`, fixed with `uv run --locked python -m ruff format tests/test_ui_serving.py`.
- Final gate: `uv run --locked python -m pytest -q` -> 134 passed; `uv run --locked python -m ruff check .` -> passed; `uv run --locked python -m ruff format --check .` -> 73 files already formatted; `node --check ui/app.js` -> passed; `uv lock --check` -> 33 packages resolved; `uv pip check` -> 58 packages compatible; `git diff --check` -> passed (Git emitted informational LF-to-CRLF warnings).
- Live browser: Uvicorn served frontend and API together at `127.0.0.1:8012` using an isolated migrated/seeded SQLite file because port 8000 was already occupied; the other listener was left untouched. Actual UI flows created/approved/retrieved a request, revised/reviewed/approved the new version, declined another request and inspected history, and verified current vs historical pricing. Separate tabs retained separate AI preferences. An unavailable backend preserved form text and showed a retry action; restarting against the same DB and retrying created one request. A concurrent update produced a stale-version screen; refresh updated queue and detail before the reviewer decided against the newly opened version. Before/after filter, toggle, and refresh database counts were unchanged: 3 requests, 7 versions, 6 decisions, 13 history events.
- Limits: automated frontend coverage verifies FastAPI asset serving and API continuity; workflows above were assistant-operated browser checks, not human acceptance. The live database was synthetic and temporary. Phase 05 must resolve same-origin browser routing alongside its planned API/UI container split. No containers, model integration, production authentication, human acceptance, commit, or push are claimed.

## 2026-10-29 - Phase 04: structured request context

- Change: added optional, typed context to create/revision API requests and immutable `request_versions.context` snapshots via Alembic `20261029_0002`. Context contains mortgage purpose, rate type, loan/property amounts and currency, term, standard rate, reason category, and optional manager-reported competitor rate/expiry. Free-text reason remains. Legacy records/clients remain supported; omitted context preserves the prior creation fingerprint format for replay compatibility. See [ADR 0010](adr/0010-versioned-request-context.md).
- UI: added structured form fields, collapsible competitor-offer details labelled unverified, exact snapshot details/history, derived LTV using integer arithmetic, and three editable synthetic presets. Prefill performs no write; explicit Submit sends the request through the HTTP API.
- Verification: `uv run --locked python -m pytest -q` -> 138 passed; `uv run --locked python -m ruff check .` -> passed; `uv run --locked python -m ruff format --check .` -> 77 files already formatted; `node --check ui/app.js` -> passed; `uv lock --check` -> 33 packages resolved; `uv pip check` -> 58 packages compatible; `git diff --check` -> passed (informational LF-to-CRLF warnings only).
- Migration/API evidence: `uv run --locked python -m pytest tests/test_api_request_context.py tests/test_api_create.py tests/test_api_workflow.py tests/persistence/test_migrations.py tests/persistence/test_operations.py -q --tb=short` -> 20 passed before the fixed-decimal serialization regression test was added; the 138-test full suite includes that added test. Migration verification preserved an existing v1 context as `null` and replayed its existing idempotency key after upgrading to head.
- Live UI: `uv run --locked python -m alembic upgrade head`, `uv run --locked python -m mortgage_pricing.seed`, then Uvicorn at `127.0.0.1:8127` used isolated `C:\Users\User\AppData\Local\Temp\mortgage-context-20261029.db` because 8000/8012 were occupied. Browser workflows created and approved a competitive-offer request, revised it with changed context, and confirmed v1 context stayed in history. A backend outage preserved all entered context; retry after restart created exactly one additional request. Fill-example did not change counts: 1 request, 2 versions, 1 decision, 3 history events before and after; after explicit retry final counts were 2 requests, 3 versions, 1 decision, 4 history events.
- Limits: automated HTTP/UI-serving tests and assistant-operated browser checks are distinct; no human acceptance is claimed. No model consumed the fields and no pattern-recognition accuracy is claimed. Data was synthetic and temporary; no dependencies changed, no commit/push.
