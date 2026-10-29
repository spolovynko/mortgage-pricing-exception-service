# ADR 0001 - Foundation, configuration, and logging

- Date: 2026-10-29 (Europe/Brussels).
- Phase / milestone: 01 / MVP1.
- Status: Implemented for Step 2 project setup only.
- Implementation state: partial phase; project setup verified, remaining foundation decisions pending.
- Decision owner or contributor: Codex assistant within the user's Step 2 request.
- Human acceptance: not recorded for the resulting implementation.
- Related requirements and phase guide: NFR-01, NFR-03, DEL-01/02/03; [Phase 01](../phases/phase-01-foundation-config-logging.md).

## Context

The repository was a clean documentation scaffold on `main` at `4e756fe`. The user requested incremental work and authorised only Step 2: Python baseline, dependency workflow, project metadata, installable package, virtual environment, and minimal dependencies. API/configuration/logging and development checks remain later steps. Python 3.12 is the planning baseline; it and uv are already installed locally.

## Options considered

| Option | Benefits | Costs and limitations |
| --- | --- | --- |
| Python 3.12 + uv + one project lockfile | Matches the baseline; isolated setup and resolved runtime dependency versions | Adds uv as a development tool; platform compatibility still needs verification |
| Unlocked pip installation | Simple initial command | Dependency resolutions can drift between installations |
| Several dependency manifests/resolvers | Allows several installation styles | Creates duplicated sources that can disagree without a concrete current need |

## Decision

- Use the Python 3.12 series: `.python-version` selects it and `requires-python = ">=3.12,<3.13"` bounds the supported series. Verification used the available CPython 3.12.12; this is not a claim that the patch is the newest release.
- Use uv 0.11.6 with `pyproject.toml` and `uv.lock`. `uv sync --locked` creates `.venv` and an editable installation, rejecting stale lock metadata. Runtime resolutions/hashes are recorded in `uv.lock`; Hatchling 1.30.1 is the pinned build backend. Do not maintain a second dependency list.
- Use a `src/mortgage_pricing` package, currently containing only `__init__.py`. The distribution name is `mortgage-pricing-exception-service`, version `0.1.0`; the import name uses underscores. No unused application layers are created.
- Install only FastAPI, Uvicorn, and Pydantic Settings, plus their resolved transitive dependencies. These prepare the agreed foundation without implementing it. Add pytest/Ruff and their configuration in Step 3. Preserve the existing .gitignore, which already excludes `.venv` and bytecode.

Configuration precedence, tracing, error/log contracts, demo identity behavior, and UI location decisions will be added when their steps are implemented. No business policy changed.

## Consequences

The package imports through an isolated virtual environment and normal setup reuses the recorded dependency resolution. Editable installation makes source changes visible during development. The Python-series constraint prevents an accidental switch to the machine's default Python 3.14 launcher. This limits supported interpreters until a deliberate compatibility change is made. The repository has no API or executable workflow yet.

## Verification and evidence

- `uv lock`: resolved 17 packages from the public PyPI index, including this project.
- `uv sync --locked`: created a fresh `.venv` with CPython 3.12.12 and installed all 17 packages, including the editable project.
- `uv lock --check`: passed. `uv pip check`: all installed packages compatible.
- `uv run --locked python -I -c "import mortgage_pricing, fastapi, pydantic_settings, uvicorn; print(mortgage_pricing.__file__)"`: imports passed; the package resolves to this repository's `src/mortgage_pricing/__init__.py`. An extended check asserted Python 3.12 and `sys.prefix != sys.base_prefix`, confirming the virtual environment.
- `git check-ignore .venv/pyvenv.cfg src/mortgage_pricing/__pycache__/__init__.cpython-312.pyc`: both generated paths are ignored.
- Limits: installation/import/dependency checks only, on Windows/CPython 3.12.12. No test suite, linter configuration, API, or model was run. Phase 01 remains incomplete. See the [build log](../build-log.md) for actual observations.

## Alternatives rejected and revisit conditions

Avoid unpinned installs and duplicated manifests because reproducible dependencies are required. Revisit the Python series or resolver only for an observed compatibility/maintenance need, then regenerate the lock and verify installation. Extend this ADR as the remaining Phase 01 decisions become concrete.

## Production implications

This step establishes development packaging, not production deployment or security controls. Packaging/dependency consistency does not establish application correctness, vulnerability absence, or production readiness. Containers remain Phase 05 work.

## References and supersession

- [Phase guide](../phases/phase-01-foundation-config-logging.md), [requirements](../requirements.md), [engineering guidelines](../python-engineering-guidelines.md), [AGENTS.md](../../AGENTS.md).
- [Python version lifecycle](https://devguide.python.org/versions/) lists 3.12 in security support.
- [uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/) documents editable installs and stale-lock rejection with `--locked`.
- No prior ADR is superseded.
