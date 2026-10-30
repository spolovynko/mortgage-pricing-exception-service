# mortgage-pricing-exception-service

A Python service for managing mortgage rate discount requests, reviewer decisions, request versions, and approved-discount retrieval.

## Current state

Phase 01 is complete: installable Python package, locked development tools, validated configuration, health API, structured request logging, and safe correlated error responses. Its fresh-install verification passed on Windows/CPython 3.12.12 with **48 tests passing**. See the [Phase 01 handoff](docs/handoffs/phase-01.md).

Phases 02–05 are implemented and assistant-verified; human acceptance is not recorded. SQLite persistence, synthetic seeds, the human approval API, and a minimal HTML/CSS/JavaScript UI for requests, review, and history are available from one Uvicorn process. `/health` reports process liveness and `/ready` checks migrated storage. The UI uses same-origin HTTP only; demo identities are simulated and assessment generation is deferred to optional Phase 09. See the [Phase 03 contract](docs/phase-03-api-contract.md), [ADR 0003](docs/adr/0003-business-rules-and-api.md), [ADR 0009](docs/adr/0009-single-process-html-ui.md), and [Phase 04 handoff](docs/handoffs/phase-04.md). Core container startup is implemented; optional model integration is deferred. Phase 06 now covers [UI/database hardening and reproducibility](docs/phases/phase-06-ui-and-database-hardening.md); see the [revised roadmap](docs/implementation-plan.md).

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

No activation is required. Python's `-I` mode excludes the current directory and `PYTHONPATH`, so the import checks the installed package. The package contains central settings, the FastAPI app factory, and persistence metadata/factories. Runtime dependencies are FastAPI, Uvicorn, Pydantic Settings, SQLAlchemy, and Alembic. pytest, Ruff, and the Starlette-compatible `httpx2` test client are development dependencies in the `dev` group, installed by the setup command above.

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

pytest discovers `tests/`, uses `importlib` import mode without adding a source path, rejects unknown configuration/markers, and treats warnings as errors. Tests cover foundation, persistence, and business HTTP behavior, including permissions, retries, versions, current pricing, and competing updates. An autouse fixture clears application settings and uses temporary working directories, keeping real `.env` files out of tests. Tests create only temporary SQLite files; no existing database, database server, Docker, or model is needed. Current results are recorded in the build log.

Ruff targets Python 3.12 with a 100-character line length. Enabled rule groups check common style errors (`E`), undefined/unused names and imports (`F`), import ordering (`I`), Python modernization (`UP`), likely bug patterns (`B`), and simplifications (`SIM`). The existing .gitignore covers pytest/Ruff caches and Python bytecode.

## Configuration (Step 4)

`mortgage_pricing.config.Settings` is the central, immutable settings model. Defaults are safe for local development: demo identity is off and `LLM_MODE` is off. Copy `.env.example` to `.env` to override values locally; `.env` is gitignored. Precedence is explicit constructor values, process environment, `.env`, then code defaults. Tests pass isolated settings or disable `.env` loading so they do not depend on a developer's machine.

Accepted modes and bounds are validated while constructing `Settings`. Supported environment values are development/test/production; log levels DEBUG/INFO/WARNING/ERROR/CRITICAL; demo identity off/header; and LLM mode off/auto. `auto` reserves capability discovery only; it does not run assessment inference. Settings accept SQLite and reserved PostgreSQL URL schemes without connecting. The persistence factory currently supports SQLite only. `SQLITE_BUSY_TIMEOUT_SECONDS` defaults to 5 seconds, greater than 0 and at most 30. AI settings are configuration only; no model integration is implemented. When service containers are added, their addresses will need container-specific overrides.

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

## Persistence foundation (Phase 02)

`persistence/base.py` defines shared metadata with stable constraint names. `persistence/database.py` provides `create_database_engine(settings)` and `create_session_factory(engine)` without import-time or construction-time I/O. The caller closes sessions/connections and then disposes the engine. Use `with factory.begin() as session` for basic commit/rollback/closure; a plain session context never commits implicitly. Each operation owns its session. SQL echo is off and bound parameter values are hidden in exception text.

SQLite connections use Python 3.12+ `autocommit=False` and enforce foreign keys. The configured busy timeout bounds waits for a competing writer; callers must handle lock errors. Users have unique logins and role memberships. Mortgage applications have unique references and an owner who must hold the relationship-manager role. A unique logical request per application contains numbered versions with positive basis-point discounts, bounded nonblank reasons, submitters, and UTC timestamps. The current pointer can only refer to a version of that request. ORM edits/deletes and migration triggers prevent direct SQL changes to immutable submitted terms, decisions, history, and retry mappings. The API owns a lazy engine for `/ready`; operational schema setup uses Alembic and repeatable baseline data uses the seed command.

Decisions reference exact versions and require a reviewer-role user; only one decision can exist per version. Typed history events record version, actor, and UTC time. ORM guards and migration triggers reject edits/deletes of immutable records. Atomic operations enforce self-review and current-version checks and commit decisions with history.

Creation idempotency records scope a key to a caller, store a SHA-256 fingerprint of canonical input, and point to the original request's version 1. Step 8 operations fingerprint deterministic JSON of exact input and replay the original reference for the same caller/key/input; changed input conflicts. Business rows, history, and the retry mapping commit together. Alembic revision `20261029_0001` creates this schema and SQLite triggers reject direct SQL changes to immutable versions, decisions, history events, and retry records.

Run `uv run --locked python -m pytest tests/persistence` to verify persistence, or `uv run --locked python -m pytest` for the complete suite. Tests apply migrations to temporary database files. No application code creates tables or directories. Apply operational schema changes with `uv run --locked python -m alembic upgrade head`. See [ADR 0002](docs/adr/0002-database-and-seed-data.md) for the resource contract and limitations.

After migration, run `uv run --locked python -m mortgage_pricing.seed` to prepare two clearly fictional users: Ada (`ada.manager`), the manager for all ten demo mortgage applications, and Blake (`blake.reviewer`), the reviewer. It reserves `SYN-MORTGAGE-DEMO-CLEAN` without requests for the create/approve demonstration on fresh storage. Re-running the command creates no duplicates. For the previous four-user demo, it transfers Grace's applications to Ada and removes unused Grace/Casey identities; existing application identifiers remain unchanged. If either retired identity has submitted or audited activity, seeding fails and rolls back rather than deleting historical actors. Unrelated user records are preserved.

Set `DATABASE_URL` to the intended SQLite file before migration, for example `$env:DATABASE_URL = "sqlite:///./data/mortgage_pricing.db"` in PowerShell. Ensure its parent directory exists. Tests inject temporary database settings through Alembic configuration attributes; operational setup must use migrations rather than `Base.metadata.create_all()`.

Each of the ten demo applications stores a fictional loan amount and property value in EUR, a standard rate in whole basis points, and a term in months. Migration `20261030_0003` adds those application columns; seeding fills missing demo values and preserves values already saved. Selecting an application prefills the four editable request fields from the database. Submitted versions retain their own immutable context snapshots, so later application changes do not rewrite reviewed terms. See the [current workflow and complete data model](docs/current-workflow-and-data-model.md).

`GET /ready` returns ready only when the configured SQLite database exists and has the current Alembic revision. Storage failure returns a correlated 503. `GET /health` stays available as process liveness.

## Business API (Phase 03)

After migration and seeding, set `$env:DEMO_IDENTITY_MODE = "header"` before starting the Uvicorn factory with the command above. Default `off` disables business access. Open `/docs` for request/response schemas and synthetic examples. Demo identity is simulated, not production authentication.

## User interface (Phase 04)

After migration and seeding, start the API and UI together from the repository root:

```powershell
$env:DEMO_IDENTITY_MODE = "header"
uv run --locked uvicorn mortgage_pricing.main:create_app --factory --host 127.0.0.1 --port 8000 --log-config config/logging.json --no-access-log
```

Open `http://127.0.0.1:8000/`. FastAPI serves separate `ui/index.html`, `ui/styles.css`, `ui/app.js`, and `ui/workspace.js` files; browser requests use same-origin API routes. Manager and Reviewer tabs select fictional demo identities. The workspace provides Requests, Applications, role-specific New request or Review queue, and History. Writes require explicit actions. Optional AI is deferred to Phase 09. See [ADR 0009](docs/adr/0009-single-process-html-ui.md), the [Phase 04 guide](docs/phases/phase-04-user-interface.md), and the [handoff](docs/handoffs/phase-04.md).

Each new request version records structured mortgage context (purpose, rate type, loan/property values with currency, term, and standard rate) alongside a free-text reason and reason category. Competitor offer details are optional and labelled manager-reported/unverified. The form includes synthetic example presets that prefill editable fields; they do not save until Submit. No borrower-identifying or creditworthiness data is requested. Context is versioned and returned in details/history for future assistance; see [ADR 0010](docs/adr/0010-versioned-request-context.md) and the [API contract](docs/phase-03-api-contract.md).

Known fictional logins are `ada.manager` and `blake.reviewer`. A client can bootstrap the user selector by supplying `X-Demo-User: ada.manager` to `/demo/users`; `/demo/applications` exposes references and owners. Both internal roles can read all internal records. Only the owning manager can submit/revise; the independent reviewer decides.

For a deliberately prepared demo database and running local server:

```powershell
$demoHeaders = @{ "X-Demo-User" = "ada.manager" }
$demoApps = Invoke-RestMethod http://127.0.0.1:8000/demo/applications -Headers $demoHeaders
$demoApplication = $demoApps | Where-Object reference -eq "SYN-MORTGAGE-DEMO-CLEAN"
$createHeaders = @{ "X-Demo-User" = "ada.manager"; "Idempotency-Key" = [guid]::NewGuid().ToString() }
$createBody = @{ application_id = $demoApplication.id; discount_bps = 25; reason = "Synthetic retention request" } | ConvertTo-Json
$created = Invoke-RestMethod http://127.0.0.1:8000/requests -Method Post -Headers $createHeaders -ContentType application/json -Body $createBody
$reviewHeaders = @{ "X-Demo-User" = "blake.reviewer" }
$decisionBody = @{ expected_version = $created.version_number; outcome = "approved" } | ConvertTo-Json
Invoke-RestMethod "http://127.0.0.1:8000/requests/$($created.request_id)/decisions" -Method Post -Headers $reviewHeaders -ContentType application/json -Body $decisionBody
Invoke-RestMethod "http://127.0.0.1:8000/applications/$($demoApplication.id)/approved-discount" -Headers $demoHeaders
```

Reuse the saved key and exact body when retrying creation. A new key cannot create a second logical request for that application: use revisions if it already has a request. A revision requires fresh review, and earlier approvals remain historical. No current approval returns 200 with `status: "none"`; an unknown application returns 404. Expected business conflicts return 409, invalid input 422, and unavailable or locked storage 503 without automatic retry. See the [contract](docs/phase-03-api-contract.md) for all routes, limits, history fields, and error envelopes.

## Continue implementation

1. Read [project status](docs/project-status.md).
2. Read [requirements](docs/requirements.md) and the [implementation plan](docs/implementation-plan.md).
3. Read the [Phase 04 handoff](docs/handoffs/phase-04.md) and active Phase 05 guide.
4. Have the agent read [AGENTS.md](AGENTS.md) before implementing the next phase.

Suggested phase-chat prompt:

```text
Implement the next requested phase only. Read AGENTS.md, docs/project-status.md,
the previous handoff, the active phase guide, relevant ADRs, and their required references. Inspect
Git/source state and preserve existing changes. Do not commit or push.
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
| [Repository instructions](AGENTS.md) | Working defaults and phase handoff requirements |

## Stack

Python, FastAPI/Uvicorn, Pydantic Settings, SQLAlchemy, SQLite, Alembic, plain HTML/CSS/JavaScript, pytest, and one Docker Compose application service. One non-root Uvicorn process serves UI and API through the same host-loopback port. Optional Ollama/model-initialisation services remain optional Phase 09 work. See [ADR 0005](docs/adr/0005-containerisation.md).

## Container startup and operations

Build and start the core UI and API from the repository root:

```bash
docker compose up --build
```

Open `http://127.0.0.1:8000/`. Startup validates writable storage, applies migrations, inserts missing synthetic seeds, and then starts Uvicorn. The named application-data volume preserves records across container recreation. AI infrastructure and an API key are not required.

For background operation and inspection:

```bash
docker compose up --build --detach --wait
docker compose ps
docker compose logs --follow app
docker compose restart app
docker compose down
```

Normal `docker compose down` removes the container and network but preserves the named volume. `docker compose down --volumes` permanently deletes that stored database; use it only when intentionally discarding local data. No startup path resets or deletes the volume.

If port 8000 is occupied, set another loopback port before startup: PowerShell `$env:APP_PORT = "8010"`; POSIX shell `APP_PORT=8010 docker compose up --build`. Check liveness at `/health` and migrated writable database readiness at `/ready`. Configuration failures and migration/seed failures stop startup and appear in `docker compose logs app`. Container logs use bounded local retention (three 10 MB files).

Docker with Compose and internet access are required for the first image/dependency download. Cached restarts can work offline. The optional model candidate remains optional Phase 09 work; no model readiness is claimed here.

### Reproducing the project elsewhere

The source repository supplies the Dockerfile, Compose configuration, dependency lockfile, migrations, synthetic seed definitions, and configuration examples. Another evaluator should build/start core mode with the command above; startup creates their own database rather than requiring a copy of the developer's data. Phase 06 exercised setup from isolated source and storage; see [verification](docs/build-log.md#2026-10-30---phase-06-ui-database-and-reproducibility). Existing Phase 05 checks were on Windows/WSL2 Docker Desktop; an actual second-machine or different-architecture result is not yet recorded.

Optional Phase 09 will add a pinned Ollama runtime and a model-init job that downloads and verifies the selected model into a persistent cache. These services do not exist yet. Model weights belong in that runtime cache, outside Git and the application image; the repository will carry model identity/digest, licence information, configuration, and setup code. Ollama documents [container-backed persistent storage](https://docs.ollama.com/docker) and its [model download API](https://docs.ollama.com/api/pull). First-time setup requires network access unless the necessary images, packages, and licensed model artefacts are supplied separately. Cached offline operation must be tested before it is claimed.

## Submission notes

Active work time is not recorded. Verified container commands, demonstration evidence, and limitations are linked from the [Phase 05 handoff](docs/handoffs/phase-05.md). AI evaluation remains later work.
