# Phase 01 - Foundation, configuration, and logging

- Status: In progress (Steps 2-6 verified, including structured logging and correlation; phase incomplete).
- Milestone: MVP1.
- Prerequisite: documentation scaffold; inspect actual repository state.
- Primary ADR to create: `docs/adr/0001-foundation-config-logging.md`.
- Handoff to create: `docs/handoffs/phase-01.md`.

## Objective

Create a small, testable Python project with a working health endpoint, validated configuration, consistent errors, and useful logging. Do not implement the full business service in this phase.

## Read first

[AGENTS.md](../../AGENTS.md), [project status](../project-status.md), [requirements](../requirements.md), [architecture](../architecture.md), [engineering guidelines](../python-engineering-guidelines.md), and [commit conventions](../commit-conventions.md).

## Scope and expected components

Establish the installable `mortgage_pricing` package under src/, tests/, UI entry-point location, and project/tool configuration. Choose a supported Python baseline and one reproducible dependency workflow. Proposed tools are FastAPI/Uvicorn, Pydantic Settings, pytest, and Ruff; add other runtime dependencies when their phase needs them.

## Implementation tasks

- [x] Inspect existing changes and prerequisites; do not overwrite user work.
- [x] Record the Step 4 configuration assumptions in ADR 0001, preserving proposed modes and defaults.
- [x] Create project metadata, dependency/lock configuration, .gitignore, and documented local installation steps. Existing .gitignore already covers the virtual environment and bytecode and was preserved.
- [x] Create the minimal API application with an application factory and process health endpoint.
- [x] Add central Pydantic Settings and .env.example. Cover application environment, log level, database URL, demo identity mode, UI API address, and reserved AI settings.
- [x] Define `LLM_MODE=off|auto`: auto permits later capability discovery, not automatic inference. No live AI is needed in this phase.
- [x] Add JSON logging with timestamp, severity, event, correlation_id, outcome, and duration; domain IDs are added when available.
- [ ] Bound/validate supplied correlation identifiers, return the operation identifier to callers, and avoid raw body/secret logging. Step 6 covers handled responses and safe request logs; unhandled 500 response correlation remains Step 7 work.
- [ ] Establish a consistent error envelope. Unexpected failures receive a safe response and useful server-side diagnostics.
- [ ] Create a minimal UI entry point if helpful, labelled as a scaffold rather than a working request workflow.
- [x] Establish formatting/lint and test commands; document dependency installation before showing runnable commands.

## Verification

### Incremental progress - 2026-10-29

The user requested one agreed step at a time. Step 1 inspected the baseline. Step 2 now supplies Python 3.12 metadata, a `src/mortgage_pricing` package, uv locking, and an isolated installation. `uv sync --locked`, `uv lock --check`, `uv pip check`, and isolated package/runtime imports passed on Windows/CPython 3.12.12. See [ADR 0001](../adr/0001-foundation-config-logging.md) and [README](../../README.md) for rationale and commands.

Step 3 now adds pytest/Ruff as locked development dependencies, configuration in `pyproject.toml`, documented commands, and one packaging integration test under `tests/`. `uv run --locked python -m pytest` observed **1 passed**. Ruff lint/format checks, lock consistency, and installed-dependency consistency passed. The test checks installation from a temporary working directory using an isolated interpreter; it does not exercise application behavior.

### Step 4 - central configuration (2026-10-29)

Added immutable `Settings` in `src/mortgage_pricing/config.py` with validated application/log/demo identity/LLM modes, database URL scheme, service URLs, model name, and bounded timeout. Added `.env.example`, documenting precedence (constructor > process environment > `.env` > defaults), and isolated tests for defaults, environment and dotenv precedence, rejected values, safe validation errors, and immutability. Defaults leave demo identity and AI off. `LLM_MODE=auto` is configuration for future capability discovery only. Database settings are not used to connect or create storage. README includes the configuration contract and test command. No API, logging, or error-response behavior has been implemented.

Observed checks: `uv run --locked python -m pytest` -> **12 passed** (including existing packaging test); `uv run --locked python -m ruff check .` -> passed; `uv run --locked python -m ruff format --check .` -> passed after formatting one source file; `uv lock --check` -> passed (24 packages); `uv pip check` -> all installed packages compatible; `git diff --check` -> passed (Git emitted its informational LF-to-CRLF conversion warning). Windows / CPython 3.12.12, pytest 9.2.0, Ruff 0.17.3, uv 0.11.6. These checks cover configuration and packaging only. All Phase 01 acceptance criteria remain unchecked; the handoff remains due at phase completion.

### Step 5 - minimal API and health endpoint (2026-10-29)

Added `create_app(settings=None)` in `src/mortgage_pricing/main.py`, a typed `GET /health` response (`{"status":"ok"}`), and API tests for the health response and isolated settings injection. Added `httpx2` to the locked dev dependencies because the resolved Starlette 1.10 TestClient deprecates legacy `httpx`; warnings are treated as errors. README now documents the Uvicorn factory command and process-liveness scope. `uv run --locked python -m pytest` -> **14 passed**; Ruff lint/format, `uv lock --check` (28 packages), `uv pip check`, and `git diff --check` passed. Started Uvicorn at `127.0.0.1:8765`; `Invoke-RestMethod http://127.0.0.1:8765/health` returned `{"status":"ok"}`. The server was stopped after the check. Windows / CPython 3.12.12. This endpoint is liveness only; it does not probe database or model readiness. Phase acceptance criteria remain unchecked pending remaining work.

### Step 6 - structured logging and correlation (2026-10-29)

Added standard-library JSON logging, independent per-app handlers/levels, and pure ASGI request middleware. Logs include UTC time, severity, event, correlation ID, outcome, duration in seconds, method, route template, and status. Only approved domain metadata is accepted; no raw bodies, headers, query strings, unknown paths, or exception messages/source text are emitted. Exception type and stack locations remain available. Caller IDs are bounded/validated; absent, invalid, or duplicate IDs receive UUIDs. ContextVar state is restored after requests. Handled responses return `X-Correlation-ID`; unhandled 500 responses require the Step 7 error boundary.

Observed: `uv run --locked python -m pytest` -> **28 passed** (14 logging cases). Ruff lint/format, lock consistency (28 packages), and installed-dependency checks passed. Live Uvicorn using `--log-config config/logging.json --no-access-log` returned 200 `/health` and 404 `/missing?token=synthetic-secret` with matching response/log IDs (`live-success`/`live-failure`), correct outcome/severity, and no query secret in logs. The server was stopped afterward. Error envelopes and complete phase acceptance/handoff remain pending.

Test settings defaults, environment overrides, invalid values, isolated test settings, health responses, correlation propagation, and safe error/log behaviour. Tests must not require a real database, Docker, an external network, or a model.

Use the actual supported commands. Expected forms after installation include `python -m pytest` and `python -m ruff check .`; configure them before claiming they work. Manually start the minimal API and inspect one success and one failure log.

## Acceptance criteria

- [ ] A documented fresh local environment can install and run the minimal API.
- [ ] Invalid configuration fails clearly before normal operation.
- [ ] Repeated application/test creation does not accumulate handlers or share mutable request state.
- [ ] Health and error responses are consistent and traceable in logs.
- [ ] Relevant tests and lint checks pass with observed evidence.
- [ ] No business/AI/container capability is falsely claimed as implemented.

## Decision record and handover

Explain the Python baseline, dependency workflow, configuration precedence, logging schema, identity shortcut, and any meaningful project-layout choices. Update this guide, the ADR index, [build log](../build-log.md), [AI usage](../ai-usage.md), and [project status](../project-status.md). Write the phase handoff with exact setup/check commands and remaining issues. Use [the handoff template](../handoffs/template.md).

Stop after Phase 01. The next phase creates database models, migrations, and seed data.
