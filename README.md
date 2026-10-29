# mortgage-pricing-exception-service

A Python service for managing mortgage rate discount requests, reviewer decisions, request versions, and approved-discount retrieval.

## Current state

Phase 01 is complete: installable Python package, locked development tools, validated configuration, health API, structured request logging, and safe correlated error responses. Fresh-install verification passed on Windows/CPython 3.12.12 with **48 tests passing**. See the [Phase 01 handoff](docs/handoffs/phase-01.md). Business endpoints, database implementation, UI, containers, and model integration belong to later phases.

The service manages a pricing exception for an existing mortgage application. A human reviewer approves or declines the discount. Mortgage underwriting and credit approval are outside scope.

## Local project setup (Step 2)

Use Python 3.12 and uv 0.11.6. From the repository root in PowerShell:

```powershell
# Bootstrap uv only if it is not already installed.
py -3.12 -m pip install uv==0.11.6
uv sync --locked
```

`.python-version` selects the 3.12 series; `requires-python` restricts this project to that series. The verified environment uses CPython 3.12.12 on Windows. Installation needs package-index access or a populated local cache; uv can obtain Python if the selected series is missing. No paid API, model, database, or Docker is required for this step.

`uv sync --locked` creates `.venv` and installs the package in editable mode. Changes under `src/mortgage_pricing` are then available without reinstalling it. `pyproject.toml` declares dependencies and `uv.lock` records exact resolved versions and hashes. The existing .gitignore excludes `.venv` and Python bytecode; the lockfile belongs in Git.

Verify after installation:

```powershell
uv lock --check
uv pip check
uv run --locked python -I -c "import mortgage_pricing, fastapi, pydantic_settings, uvicorn; print(mortgage_pricing.__file__)"
```

No activation is required. Python's `-I` mode excludes the current directory and `PYTHONPATH`, so the import checks the installed package. The package contains its initializer, central settings model, and FastAPI app factory. Runtime dependencies are FastAPI, Uvicorn, and Pydantic Settings. pytest, Ruff, and the Starlette-compatible `httpx2` test client are development dependencies in the `dev` group, installed by the setup command above.

For deliberate dependency changes, use `uv add <package>` and review both dependency files. Normal setup uses `--locked` so stale metadata fails rather than silently updating the lock. See [ADR 0001](docs/adr/0001-foundation-config-logging.md) for rationale and verification limits.

## Development checks (Step 3)

Run from the repository root, after installation:

```powershell
uv sync --locked
uv run --locked python -m pytest
uv run --locked python -m ruff check .
uv run --locked python -m ruff format --check .
```

These commands use the locked project tools, rather than whichever pytest or Ruff is installed globally. Tested versions: pytest 9.2.0 and Ruff 0.17.3 on Windows/CPython 3.12.12. To apply formatting, use `uv run --locked python -m ruff format .`.

pytest discovers `tests/`, uses `importlib` import mode without adding a source path, rejects unknown configuration/markers, and treats warnings as errors. Tests cover package installation/import, configuration, health, errors, logging, and concurrent correlation isolation. An autouse fixture removes application settings from the test environment and uses temporary working directories, keeping real `.env` files out of tests. The 48 tests also passed with deliberately invalid external settings and dotenv content. No database, Docker, or model is needed.

Ruff targets Python 3.12 with a 100-character line length. Enabled rule groups check common style errors (`E`), undefined/unused names and imports (`F`), import ordering (`I`), Python modernization (`UP`), likely bug patterns (`B`), and simplifications (`SIM`). The existing .gitignore covers pytest/Ruff caches and Python bytecode.

## Configuration (Step 4)

`mortgage_pricing.config.Settings` is the central, immutable settings model. Defaults are safe for local development: demo identity is off and `LLM_MODE` is off. Copy `.env.example` to `.env` to override values locally; `.env` is gitignored. Precedence is explicit constructor values, process environment, `.env`, then code defaults. Tests pass isolated settings or disable `.env` loading so they do not depend on a developer's machine.

Accepted modes and bounds are validated while constructing `Settings`. Supported environment values are development/test/production; log levels DEBUG/INFO/WARNING/ERROR/CRITICAL; demo identity off/header; and LLM mode off/auto. `auto` reserves capability discovery only; it does not run assessment inference. The database URL currently accepts SQLite and PostgreSQL schemes, without connecting to or creating a database. AI settings are configuration only; no model integration is implemented. When service containers are added, their addresses will need container-specific overrides.

The API uses a factory, so Uvicorn can construct an app and load validated settings at startup:

```powershell
uv run --locked uvicorn mortgage_pricing.main:create_app --factory --host 127.0.0.1 --port 8000 --log-config config/logging.json --no-access-log
```

Check process liveness at `http://127.0.0.1:8000/health`; the response is `{"status":"ok"}`. This is process liveness only and does not indicate database or model readiness.

Verify configuration and the API with:

```powershell
uv run --locked python -m pytest
```

## Structured logging (Step 6)

Application logs go to stdout as JSON with UTC `timestamp`, `level`, `event`, `correlation_id`, `outcome`, and `duration` (seconds). Request completion adds method, matched route template, and status. Domain IDs are supported when later features supply them. `LOG_LEVEL` controls application logs; `WARNING` and higher omit successful request logs. Uvicorn's JSON configuration above covers server messages; `--no-access-log` disables its raw access log to avoid recording URLs and query strings twice.

Send an optional `X-Correlation-ID` header: one value of 1-64 ASCII letters, digits, dots, underscores, or hyphens, starting with a letter or digit. Missing, invalid, and duplicate values receive a generated UUID. The ID is returned in the response header and applied to logs during that request. For example, `Invoke-WebRequest http://127.0.0.1:8000/health -Headers @{'X-Correlation-ID'='demo-123'}` produces a matching response header and request log.

Logs include metadata rather than bodies, query strings, headers, or raw unknown paths. Exception diagnostics include type and stack locations, excluding messages and source text. Use fixed internal event names when adding application logging. Correlation IDs do not establish identity or permission. Unexpected failures before response headers are sent receive the safe response below; failures during an already-started response are logged and rethrown.

Run the logging tests with `uv run --locked python -m pytest tests/test_logging.py`.

## Error responses (Step 7)

`errors.py` owns the shared envelope and framework handlers. HTTP errors use stable codes derived from status names (for example, `not_found` or `method_not_allowed`) and standard status phrases. Invalid input receives 422 with code `validation_error`; input values and validation internals are excluded. Expected HTTP exceptions preserve status and headers such as `Allow`, `Retry-After`, and `WWW-Authenticate`, while their detail payloads are hidden. Later business errors will define their own reviewed contracts.

Unexpected exceptions before response start receive HTTP 500:

```json
{"error":{"code":"internal_error","message":"An unexpected error occurred."},"correlation_id":"demo-123"}
```

The same ID appears in `X-Correlation-ID` and the failure log. The request boundary logs the diagnostic once and sends the safe response. HTTP exceptions with 5xx status also receive a generic internal-error message. Already-started streams/background failures cannot replace a response; they are logged and rethrown. Run `uv run --locked python -m pytest tests/test_errors.py` to verify the error contract.

## Continue implementation

1. Read [project status](docs/project-status.md).
2. Read [requirements](docs/requirements.md) and the [implementation plan](docs/implementation-plan.md).
3. Read the [Phase 01 handoff](docs/handoffs/phase-01.md), then start [Phase 02: database and seed data](docs/phases/phase-02-database-and-seed-data.md) in the next implementation chat.
4. Have the agent read [AGENTS.md](AGENTS.md) before implementing that phase.

Suggested phase-chat prompt:

```text
Implement Phase 02 in this repository. Read AGENTS.md, docs/project-status.md,
docs/handoffs/phase-01.md, the phase guide, and its required references first. Complete the phase's
verification, write its ADR and handoff, and update the build log, AI usage
record, and project status. Stop after this phase and report any unmet criteria.
```

Change the phase number and guide for each subsequent chat. Use the same repository so the agent has access to its documentation and implementation.

## Documentation

| Document | Purpose |
| --- | --- |
| [Implementation plan](docs/implementation-plan.md) | Eight phases, dependencies, and completion milestones |
| [Requirements](docs/requirements.md) | Assignment requirements, project assumptions, and acceptance scenarios |
| [Architecture](docs/architecture.md) | Proposed components, boundaries, data flow, and runtime |
| [Python engineering guidelines](docs/python-engineering-guidelines.md) | Design, implementation, and verification standards |
| [Commit conventions](docs/commit-conventions.md) | Area, action, and milestone tags |
| [Architecture decisions](docs/adr/README.md) | Decision index and record-writing instructions |
| [Build log](docs/build-log.md) | Chronological work and verification evidence |
| [AI usage](docs/ai-usage.md) | AI contributions, review, corrections, and limitations |
| [Handoff template](docs/handoffs/template.md) | Context for the next phase chat |

## Planned stack

Python, FastAPI/Uvicorn, Pydantic Settings, SQLAlchemy, SQLite, Alembic, Streamlit, HTTPX, and pytest. A single application Dockerfile will build an image shared by separate API, UI, and model-initialisation containers. Optional Ollama services will provide local AI assistance.

## Target startup experience

These commands are **future acceptance targets** for container implementation:

```bash
# Core UI and API
docker compose up --build

# Core application plus optional local AI
docker compose --profile ai up --build
```

The interviewer will need Docker with Compose, available local ports, and internet access for the initial image/dependency/model downloads. Cached restarts should work offline after setup. The optional model candidate is `qwen3:4b-instruct-2507-q4_K_M`; its accuracy and resource requirements still need project-specific verification.

## Submission notes

Record actual active work time in the build log. At handover, add verified setup commands, seed identities, demonstration steps, test results, AI evaluation results, and production limitations. Do not infer implementation progress from the existence of this scaffold.
