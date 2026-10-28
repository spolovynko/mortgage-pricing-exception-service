# mortgage-pricing-exception-service

A Python service for managing mortgage rate discount requests, reviewer decisions, request versions, and approved-discount retrieval.

## Current state

This repository currently contains the documentation scaffold. The application, tests, Dockerfile, Compose configuration, and model setup have **not** been implemented. No application or model tests have been run as part of creating this scaffold.

The service manages a pricing exception for an existing mortgage application. A human reviewer approves or declines the discount. Mortgage underwriting and credit approval are outside scope.

## Start here

1. Read [project status](docs/project-status.md).
2. Read [requirements](docs/requirements.md) and the [implementation plan](docs/implementation-plan.md).
3. Start a new chat for [Phase 01](docs/phases/phase-01-foundation-config-logging.md).
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
