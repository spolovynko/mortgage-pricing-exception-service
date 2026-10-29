# ADR 0001 - Foundation, configuration, and logging

- Date: 2026-10-29 (Europe/Brussels).
- Phase / milestone: 01 / MVP1.
- Status: Implemented for Steps 2-6, including JSON logging and request correlation.
- Implementation state: partial phase; consistent HTTP error responses and unhandled 500 correlation headers remain pending.
- Decision owner or contributor: Codex assistant within the user's separate incremental Step 2-6 requests.
- Human acceptance: not recorded for the resulting implementation.
- Related requirements and phase guide: NFR-01, NFR-03, DEL-01/02/03; [Phase 01](../phases/phase-01-foundation-config-logging.md).

## Context

The repository was a clean documentation scaffold on `main` at `4e756fe`. The user requested incremental work and authorised only Step 2: Python baseline, dependency workflow, project metadata, installable package, virtual environment, and minimal dependencies. API/configuration/logging and development checks remain later steps. Python 3.12 is the planning baseline; it and uv are already installed locally.

Step 3 was subsequently requested separately. Its initial working tree was clean, with Step 2 committed as `d135997`. The authorised addition is development-check tooling and verification; configuration/API implementation remains deferred.

Step 4 was then requested with a clean worktree following the Step 3 commit `986bd18`. Configuration is the only authorized behavior in this increment; API, logging, error envelopes, and all later-phase work remain deferred.

Step 5 was requested with a clean worktree after Step 4 had been committed as `2ceb97e`. It authorizes the minimal API factory and process health endpoint. Structured logging and error behavior remain deferred.

Step 6 was requested after Step 5 commit `5b8ed82`, with a clean working tree. Logging and request tracing are authorized; consistent HTTP error responses remain Step 7 work.

## Options considered

| Option | Benefits | Costs and limitations |
| --- | --- | --- |
| Python 3.12 + uv + one project lockfile | Matches the baseline; isolated setup and resolved runtime dependency versions | Adds uv as a development tool; platform compatibility still needs verification |
| Unlocked pip installation | Simple initial command | Dependency resolutions can drift between installations |
| Several dependency manifests/resolvers | Allows several installation styles | Creates duplicated sources that can disagree without a concrete current need |

## Decision

- Use the Python 3.12 series: `.python-version` selects it and `requires-python = ">=3.12,<3.13"` bounds the supported series. Verification used the available CPython 3.12.12; this is not a claim that the patch is the newest release.
- Use uv 0.11.6 with `pyproject.toml` and `uv.lock`. `uv sync --locked` creates `.venv` and an editable installation, rejecting stale lock metadata. Runtime resolutions/hashes are recorded in `uv.lock`; Hatchling 1.30.1 is the pinned build backend. Do not maintain a second dependency list.
- Use a `src/mortgage_pricing` package. It now contains the initializer, central settings, and a minimal application factory; the distribution name is `mortgage-pricing-exception-service`, version `0.1.0`; the import name uses underscores. No unused application layers are created.
- Runtime dependencies remain FastAPI, Uvicorn, and Pydantic Settings, plus their resolved transitive dependencies. Step 4 uses Pydantic Settings for one immutable `Settings` model with an on-demand loader instead of a cached global, so tests and future app setup can inject isolated values. Configuration precedence follows Pydantic Settings: explicit constructor values, process environment, dotenv, then defaults. `.env.example` contains safe values; the existing .gitignore excludes the real `.env` file.
- Validate app environment, log level, demo identity mode, and `LLM_MODE` with literal choices; constrain model name and timeout, validate service URL shapes, and accept only SQLite/PostgreSQL database URL schemes without creating storage or connecting. Use `LLM_MODE=off` and demo identity `off` by default. `auto` is reserved for capability discovery and must not start assessment inference. AI endpoint/model settings are inert configuration only.
- Add `create_app(settings=None)` as the single application construction boundary. It accepts explicit Settings for isolated tests and loads validated settings when none are supplied. Do not create a module-global app; Uvicorn runs the factory via `--factory`, avoiding import-time configuration and shared test state. Implement `/health` as a stable `{"status":"ok"}` process-liveness response only. It must not be reported as database/model readiness.
- Steps 3 and 5 add pytest, Ruff, and Starlette's supported `httpx2` test client in the `dev` dependency group with resolved versions in the same lockfile. Preserve the existing .gitignore, which already excludes `.venv`, bytecode, and tool caches.
- Configure pytest discovery under `tests/`, `importlib` import mode, strict configuration/markers, and warnings as errors. Do not add a `pythonpath` workaround. A packaging integration test runs an isolated interpreter from a temporary directory, checking that imports and distribution metadata work independently of the repository working directory. No placeholder API or synthetic business test is needed at this step.
- Configure Ruff in `pyproject.toml` for Python 3.12, a 100-character line length, and `E`, `F`, `I`, `UP`, `B`, `SIM` lint groups. Use the same tool for formatting. Run tools through `uv run --locked python -m ...` so project versions are selected consistently; do not add CI or pre-commit automation in this step.

Use standard-library logging with a JSON formatter and one independently owned logger/handler per app, avoiding global handler accumulation or changing other apps' configured levels. A pure ASGI middleware wraps request completion and failure without buffering bodies. A ContextVar propagates the correlation ID through asynchronous calls and worker threads; reset its token in `finally`. `app.state.logger` is the application logging boundary for later services. An additional logging library or global logging registry provides no current benefit.

The schema contains UTC timestamp, level, trusted internal event name, correlation_id, outcome, and duration in seconds. Request metadata is restricted to method, matched route template, and HTTP status; optional actor/request/version IDs can be supplied later. Use INFO for success, WARNING for 4xx, ERROR for 5xx/exceptions. Non-request events have null correlation/outcome/duration. Application `LOG_LEVEL` filters these records. Exception diagnostics contain type and stack file/function/line, excluding exception messages, source text, and local values. Extra fields are allowlisted; callers must use fixed internal event names and avoid placing user input in the event string.

Accept one `X-Correlation-ID` containing 1-64 ASCII letters/digits/dots/underscores/hyphens, beginning with a letter/digit. Generate UUIDs for missing, invalid, or duplicate inputs instead of rejecting an otherwise valid operation. Caller IDs are tracing hints, never identity or authorization. Store the ID in request state and return it in handled response headers. Log escaping uses JSON serialization. Unknown paths, queries, bodies, headers, and settings are excluded. Unhandled failures are logged and rethrown; the outer Starlette error boundary generates their responses, so Step 7 must attach their response ID and safe envelope.

Use `config/logging.json` only at the Uvicorn command boundary to apply the same formatter to server logs. Disable its separate raw access log with `--no-access-log`, keeping one application completion event per request. Uvicorn lifecycle/error events remain distinct server diagnostics, with null correlation when emitted outside a request context. Do not configure global server loggers in `create_app`.

Consistent HTTP errors, runtime demo identity behavior, and UI implementation remain pending. No business policy changed.

## Consequences

The package imports through an isolated virtual environment and normal setup reuses the recorded dependency resolution. Editable installation makes source changes visible during development. The Python-series constraint prevents an accidental switch to the machine's default Python 3.14 launcher. This limits supported interpreters until a deliberate compatibility change is made. The API currently supports process liveness and structured request logs. Safe diagnostics omit exception messages, trading some debugging detail for predictable data exclusion. No business endpoints or dependency readiness probes exist yet.

## Verification and evidence

### Step 2 evidence

- `uv lock`: resolved 17 packages from the public PyPI index, including this project.
- `uv sync --locked`: created a fresh `.venv` with CPython 3.12.12 and installed all 17 packages, including the editable project.
- `uv lock --check`: passed. `uv pip check`: all installed packages compatible.
- `uv run --locked python -I -c "import mortgage_pricing, fastapi, pydantic_settings, uvicorn; print(mortgage_pricing.__file__)"`: imports passed; the package resolves to this repository's `src/mortgage_pricing/__init__.py`. An extended check asserted Python 3.12 and `sys.prefix != sys.base_prefix`, confirming the virtual environment.
- `git check-ignore .venv/pyvenv.cfg src/mortgage_pricing/__pycache__/__init__.cpython-312.pyc`: both generated paths are ignored.
- Limits: installation/import/dependency checks only, on Windows/CPython 3.12.12. No test suite, linter configuration, API, or model was run. Phase 01 remains incomplete. See the [build log](../build-log.md) for actual observations.

### Step 3 evidence

- `uv add --dev "pytest>=8,<10" "ruff>=0.9,<1"`: installed pytest 9.2.0 and Ruff 0.17.3 plus their transitive dependencies; 24 total locked packages including this project.
- `uv run --locked python -m pytest`: **1 passed**, the isolated installed-package/distribution check. No external network, storage service, or model is used.
- `uv run --locked python -m ruff check .`: all checks passed. `uv run --locked python -m ruff format --check .`: passed.
- `uv lock --check` and `uv pip check`: passed. `ruff check --show-files` confirmed discovery includes the project configuration, source package, and test file.
- Limits: Windows/CPython 3.12.12 only; no configuration/health/logging/error behavior or business workflow has been tested. Strict warning handling may expose future dependency deprecations; address observed issues specifically rather than broadly suppressing warnings. Phase 01 acceptance remains incomplete.

### Step 4 evidence

- `uv run --locked python -m pytest`: **12 passed**, including 11 configuration cases and the prior packaging test. Configuration checks cover default modes, environment and dotenv precedence, invalid modes/bounds/database scheme, safe error display, and immutability.
- `uv run --locked python -m ruff check .`: passed. `uv run --locked python -m ruff format --check .`: passed. `uv lock --check`: passed with 24 packages. `uv pip check`: all installed packages compatible. `git diff --check`: passed; Git printed an informational LF-to-CRLF working-copy warning.
- Limits: Windows/CPython 3.12.12 only. Settings construction was tested; no app factory/startup, health endpoint, logging, HTTP error handling, database connection, model discovery/inference, or other application behavior is implemented or verified. Phase 01 remains incomplete; acceptance checkboxes are not complete.

### Step 5 evidence

- Added `httpx2>=2,<3` in the locked dev group (resolved 2.16.0). The first TestClient run found Starlette 1.10 emits a deprecation warning when legacy `httpx` is used; since pytest treats warnings as errors, use the TestClient's supported `httpx2` dependency rather than suppressing that warning.
- `uv run --locked python -m pytest`: **14 passed**, including factory state-isolation and health response tests. `uv run --locked python -m ruff check .`, `uv run --locked python -m ruff format --check .`, `uv lock --check` (28 packages), `uv pip check`, and `git diff --check` passed.
- Live local verification: started Uvicorn using `uv run --locked uvicorn mortgage_pricing.main:create_app --factory --host 127.0.0.1 --port 8765 --log-level warning`; `Invoke-RestMethod -Uri 'http://127.0.0.1:8765/health' -Method Get` returned `{"status":"ok"}`. The local server was stopped after the request.
- Limits: Windows/CPython 3.12.12 only. Health indicates process liveness only. No database/model readiness, business endpoint, structured logging, error handling, or other-platform behavior is claimed. Phase 01 remains incomplete.

### Step 6 evidence

- `uv run --locked python -m pytest`: **28 passed**, including 14 logging cases for schema/time, response correlation, generated/invalid/duplicate/boundary IDs, failure severity and safe diagnostics, unknown metadata exclusion, handler/level independence, and overlapping request context isolation/reset.
- Ruff lint/format, `uv lock --check` (28 packages), and `uv pip check` passed. Dependencies were unchanged.
- Live Uvicorn with `--log-config config/logging.json --no-access-log` produced JSON startup and request logs. `/health` returned 200 with `live-success`; `/missing?token=synthetic-secret` returned 404 with `live-failure`. Log IDs matched response headers, severity/outcome/duration were correct, and the query secret was absent. The server was stopped afterward.
- Limits: Windows/CPython 3.12.12 only. Unhandled failures have safe operational diagnostics, but their HTTP response envelope and correlation header await Step 7. No business/database/model/container behavior or human acceptance is claimed. Phase 01 remains incomplete.

## Alternatives rejected and revisit conditions

Avoid unpinned installs and duplicated manifests because reproducible dependencies are required. Revisit the Python series or resolver only for an observed compatibility/maintenance need, then regenerate the lock and verify installation. Extend this ADR as the remaining Phase 01 decisions become concrete.

## Production implications

This step establishes development packaging, not production deployment or security controls. Packaging/dependency consistency does not establish application correctness, vulnerability absence, or production readiness. Containers remain Phase 05 work.

## References and supersession

- [Phase guide](../phases/phase-01-foundation-config-logging.md), [requirements](../requirements.md), [engineering guidelines](../python-engineering-guidelines.md), [AGENTS.md](../../AGENTS.md).
- [Python version lifecycle](https://devguide.python.org/versions/) lists 3.12 in security support.
- [uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/) documents editable installs and stale-lock rejection with `--locked`.
- [pytest integration practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html) describes virtual-environment installation, development dependency groups, and import-mode choices.
- [Ruff configuration](https://docs.astral.sh/ruff/configuration/) documents project configuration and source discovery.
- No prior ADR is superseded.
