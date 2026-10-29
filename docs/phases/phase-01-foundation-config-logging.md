# Phase 01 - Foundation, configuration, and logging

- Status: In progress (Step 2 project setup verified; phase incomplete).
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
- [ ] Translate any remaining scope ambiguity into explicit ADR assumptions, preserving the proposed requirements unless a material change is authorised.
- [x] Create project metadata, dependency/lock configuration, .gitignore, and documented local installation steps. Existing .gitignore already covers the virtual environment and bytecode and was preserved.
- [ ] Create the minimal API application with an application factory or equivalent testable setup and a process health endpoint.
- [ ] Add central Pydantic Settings and .env.example. Cover application environment, log level, database URL, demo identity mode, UI API address, and reserved AI settings.
- [ ] Define `LLM_MODE=off|auto`: auto permits later capability discovery, not automatic inference. No live AI is needed in this phase.
- [ ] Add JSON logging with timestamp, severity, event, correlation_id, outcome, and duration; domain IDs are added when available.
- [ ] Bound/validate supplied correlation identifiers, return the operation identifier to callers, and avoid raw body/secret logging.
- [ ] Establish a consistent error envelope. Unexpected failures receive a safe response and useful server-side diagnostics.
- [ ] Create a minimal UI entry point if helpful, labelled as a scaffold rather than a working request workflow.
- [ ] Establish formatting/lint and test commands; document dependency installation before showing runnable commands.

## Verification

### Incremental progress - 2026-10-29

The user requested one agreed step at a time. Step 1 inspected the baseline. Step 2 now supplies Python 3.12 metadata, a `src/mortgage_pricing` package, uv locking, and an isolated installation. `uv sync --locked`, `uv lock --check`, `uv pip check`, and isolated package/runtime imports passed on Windows/CPython 3.12.12. See [ADR 0001](../adr/0001-foundation-config-logging.md) and [README](../../README.md) for rationale and commands.

Next is Step 3: configure development checks. No API, settings implementation, logging, error handling, tests, or lint configuration has been created. All phase acceptance criteria below remain unchecked; installation alone does not complete the runnable-API criterion. The phase handoff will be written at phase completion.

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
