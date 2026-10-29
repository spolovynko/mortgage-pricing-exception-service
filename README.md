# mortgage-pricing-exception-service

A Python service for managing mortgage rate discount requests, reviewer decisions, request versions, and approved-discount retrieval.

## Current state

Phase 01 is in progress. Steps 2-3 supply an installable `mortgage_pricing` package, an isolated Python environment, locked dependencies, and configured development checks. One packaging test passes, along with lint/format checks. The API, configuration, logging, UI, Dockerfile, Compose configuration, and model setup have **not** been implemented; application behavior and models remain untested.

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

No activation is required. Python's `-I` mode excludes the current directory and `PYTHONPATH`, so the import checks the installed package. The only package source is currently `src/mortgage_pricing/__init__.py`; no server command exists yet. Runtime dependencies are FastAPI, Uvicorn, and Pydantic Settings. pytest and Ruff are development dependencies in the `dev` group, installed by the setup command above.

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

pytest discovers `tests/`, uses `importlib` import mode without adding a source path, rejects unknown configuration/markers, and treats warnings as errors. The current test launches an isolated Python process from a temporary directory and verifies both package import and installed distribution metadata. It needs no network, database, Docker, or model. This is a packaging integration check; behavioral tests will accompany the later features.

Ruff targets Python 3.12 with a 100-character line length. Enabled rule groups check common style errors (`E`), undefined/unused names and imports (`F`), import ordering (`I`), Python modernization (`UP`), likely bug patterns (`B`), and simplifications (`SIM`). The existing .gitignore covers pytest/Ruff caches and Python bytecode.

## Start here

1. Read [project status](docs/project-status.md).
2. Read [requirements](docs/requirements.md) and the [implementation plan](docs/implementation-plan.md).
3. Continue [Phase 01](docs/phases/phase-01-foundation-config-logging.md) one agreed step at a time. Step 4 (central configuration) is next.
4. Have the agent read [AGENTS.md](AGENTS.md) before implementing that phase.

Suggested phase-chat prompt:

```text
Implement Phase 01 in this repository. Read AGENTS.md, docs/project-status.md,
the phase guide, and its required references first. Complete the phase's
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

These commands are **future acceptance targets**, not commands supported by this documentation-only scaffold:

```bash
# Core UI and API
docker compose up --build

# Core application plus optional local AI
docker compose --profile ai up --build
```

The interviewer will need Docker with Compose, available local ports, and internet access for the initial image/dependency/model downloads. Cached restarts should work offline after setup. The optional model candidate is `qwen3:4b-instruct-2507-q4_K_M`; its accuracy and resource requirements still need project-specific verification.

## Submission notes

Record actual active work time in the build log. At handover, add verified setup commands, seed identities, demonstration steps, test results, AI evaluation results, and production limitations. Do not infer implementation progress from the existence of this scaffold.
