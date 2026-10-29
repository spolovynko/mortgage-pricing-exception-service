# Phase 01 handoff - Foundation, configuration, and logging

- Date: 2026-10-29 (Europe/Brussels).
- Phase status: Complete.
- Milestone: MVP1 (foundation only; MVP1 as a whole is not complete).
- Current commit/branch: `e9358eb` on `main` before uncommitted Step 8 tests/records. No commits or pushes were made by the assistant.

## Read first

Read [project status](../project-status.md), [AGENTS.md](../../AGENTS.md), [ADR 0001](../adr/0001-foundation-config-logging.md), and the next [Phase 02 guide](../phases/phase-02-database-and-seed-data.md). The completed [Phase 01 guide](../phases/phase-01-foundation-config-logging.md) preserves incremental evidence. Inspect current Git status and source before extending it.

## Implemented outcome

- Installable `src/mortgage_pricing` package, Python 3.12 baseline, `pyproject.toml`/`uv.lock`, pytest and Ruff configuration.
- `config.py`: immutable Pydantic Settings, safe defaults and `.env.example`; precedence is constructor > environment > dotenv > defaults. Demo identity and LLM modes default to off. Reserved database/UI/model settings do not establish connections or implement those services.
- `main.py`: `create_app(settings=None)` factory with injected or validated settings and typed `GET /health` returning `{"status":"ok"}`. This is process liveness only.
- `logging_config.py` / `request_logging.py`: one logger per app, stdout JSON, UTC timestamp, severity/event, correlation ID, outcome, duration in seconds, approved metadata, and safe type/stack diagnostics. Concurrent requests use isolated ContextVar state. Bodies, queries, headers, unknown paths, and exception messages are excluded.
- `errors.py`: shared `{error: {code, message}, correlation_id}` envelope for HTTP/validation errors and unexpected failures. Status/HTTP headers are preserved; unsafe details are omitted. Unexpected failures before response start receive generic 500 and one diagnostic record. Responses return matching `X-Correlation-ID`.
- Tests isolate application environment variables and use temporary working directories. No developer dotenv file is loaded by ordinary tests.

## Verification performed

| Command or scenario | Observed outcome | Limitations |
| --- | --- | --- |
| `uv run --locked python -m pytest` | 48 passed | Windows/CPython 3.12.12; synthetic tests, no live model/database |
| `uv run --locked python -m ruff check .` | Passed | Configured lint groups |
| `uv run --locked python -m ruff format --check .` | Passed | Python/project files |
| `uv lock --check` / `uv pip check` | Passed; 28 resolved / 27 installed packages | Current platform resolution |
| Fresh `uv sync --locked` with temporary `UV_PROJECT_ENVIRONMENT` | Created a new venv, installed 27 packages; all 48 tests and lint/format checks passed | Used existing source/editable install and local package cache; not an offline-cache or other-platform certification |
| Fresh Uvicorn with copied `.env.example` | 200 `/health`, safe 404 `/missing`; response IDs matched one JSON completion record each; synthetic query secret absent | Loopback HTTP only; owned server/env removed afterward |
| Invalid shell settings and dotenv file outside repo, then `uv run --project <repo> --locked python -m pytest <repo>/tests` | All 48 passed | Demonstrates test isolation, not application acceptance of invalid settings |
| Invalid settings at `create_app()` | Validation fails before serving | Automated test |
| Step 7 live temporary failure route | Generic correlated 500, one safe diagnostic; exception message excluded | Route existed only in temporary stdin process; absent from app source |

Final whitespace/link/fence checks and any observations are recorded in [build log](../build-log.md).

## Decisions and rationale

[ADR 0001](../adr/0001-foundation-config-logging.md) records Python/uv, proportional module boundaries, configuration precedence, JSON logging/correlation policy, and safe errors. It is Implemented; human acceptance is not recorded. Defaults disable demo identity and AI; `auto` reserves discovery, never automatic inference. Demo identity `header` is configuration only, not implemented authorization.

The optional UI stub adds no working foundation behavior and was omitted; create `ui/app.py` in Phase 04. The suggested `middleware/` directory move remains unapplied; tracing already lives in a separate focused module. No generic repository/service hierarchy was introduced.

## Unfinished work and known issues

No unmet Phase 01 acceptance criteria based on observed checks. Limits carried forward:

- Failures after response start (stream/background failures) are logged/rethrown; a response already sent cannot be replaced.
- Generic validation messages omit field-level diagnostics to avoid reflecting untrusted data; Phase 03 should define safe domain-specific errors.
- Database URL validation accepts SQLite/PostgreSQL scheme prefixes only. No connection, driver readiness, schema, migrations, seed data, or persistence is implemented.
- No business permissions, runtime identity handling, UI, Docker/Compose, model discovery/inference, or live model evaluation is implemented.
- Only Windows/CPython 3.12.12 was verified. Production suitability and human code review are not claimed.

## Environment and reproducibility

Verified uv 0.11.6, CPython 3.12.12, FastAPI 0.162.0, Starlette 1.10.0, Uvicorn 0.54.0, Pydantic 2.14.1, Pydantic Settings 2.16.2, pytest 9.2.0, Ruff 0.17.3, and httpx2 2.16.0 (Starlette TestClient dependency). Resolved versions are in `uv.lock`.

From the repository root in PowerShell:

```powershell
uv sync --locked
uv lock --check
uv pip check
uv run --locked python -m pytest
uv run --locked python -m ruff check .
uv run --locked python -m ruff format --check .
uv run --locked uvicorn mortgage_pricing.main:create_app --factory --host 127.0.0.1 --port 8000 --log-config config/logging.json --no-access-log
```

In another terminal:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health -Headers @{'X-Correlation-ID'='demo-123'}
```

Optionally copy `.env.example` to a new local `.env`; do not overwrite existing local settings. No activation is needed. Database path is only a reserved default (`sqlite:///./data/mortgage_pricing.db`); no database was created. No seed identities or credentials exist. No live AI was tested.

## Records updated

- Phase guide: tasks/acceptance verified; optional UI omission explicit.
- ADR/index: ADR 0001 Implemented; Phase 01 complete, no human acceptance claim.
- Build log: commands, results, corrections, and limitations appended; actual work time not recorded.
- AI usage: actual assistant work, checks, and review limitations appended.
- Project status: Phase 01 complete, Phase 02 next and unstarted.
- README/architecture: implemented scope, setup/check commands, handoff link, and future boundaries updated. No business requirement was changed.

## Next action

Start Phase 02 (database models, migrations, and seed data) in a new implementation chat when requested. Preserve existing changes, read the Phase 02 guide, and do not infer database behavior from the reserved URL. Stop at the Phase 01 boundary here.
