# Phase 05 - Containerisation

- Status: Not started.
- Milestone: MVP2.
- Prerequisite: Phase 04 UI/API human workflow verified.
- Primary ADR to create: `docs/adr/0005-containerisation.md`.
- Handoff to create: `docs/handoffs/phase-05.md`.

## Objective

Start the core application through one Compose command using **one application Dockerfile and one Compose file**. One application container runs one Uvicorn process serving both the HTML/CSS/JavaScript UI and HTTP API. The user authorized this requirement change on 2026-10-29, replacing the separate API/UI container plan while preserving ADR 0009's same-origin runtime and existing HTTP contracts.

## Read first

[AGENTS.md](../../AGENTS.md), [architecture](../architecture.md), [engineering guidelines](../python-engineering-guidelines.md), current status, the Phase 04 handoff, and foundation/database/UI ADRs.

## Expected files and services

Create Dockerfile, compose.yaml, and .dockerignore. Define one core application service with a startup command that safely prepares storage before serving UI and API together. No separate UI service or reverse proxy is required. A Python model-init job may later reuse the image; Ollama will use its own official image in Phase 06. Do not implement Phase 06 here.

Use a named application-data volume owned/writable by the non-root application runtime user. Do not add a separate database-server container for SQLite.

## Implementation tasks

- [ ] Build a compact Python application image from pinned, tested dependencies and a pinned base image.
- [ ] Include root UI assets, the Python package, and locked dependencies in the application image. Keep model weights, databases, .env files, caches, and Git internals out of the build context.
- [ ] Define reliable application-image build behaviour for a clean checkout, not just a host that already has an image tag cached.
- [ ] Define one application command, Compose networking, validated environment settings, and one host-loopback application port.
- [ ] Serve UI assets and API routes from the same Uvicorn process; retain same-origin browser requests without a separate UI service or reverse proxy.
- [ ] Run migrations and repeatable seed setup safely before serving business operations. Avoid conflicting schema setup across processes.
- [ ] Add process liveness and core database readiness checks. Verify healthcheck commands exist in their actual images.
- [ ] Keep core readiness/startup independent of optional AI. Reserve the later profile/interface without falsely claiming model readiness.
- [ ] Write structured service logs to stdout/stderr and configure bounded container log retention.
- [ ] Verify non-root execution and persistent-volume permissions.
- [ ] Document startup, normal shutdown, log inspection, occupied-port recovery, and persistence behaviour. Any destructive reset must be separately explained and never run automatically.

## Verification

On isolated disposable test storage, run the target startup command from a clean application-image state:

```bash
docker compose up --build
```

Confirm UI access, API readiness, seed availability, and create/approve/retrieve through the real containers. Stop/recreate the test stack without deleting its volume, then confirm records persist. Verify repeated setup does not duplicate seed records.

Inspect service logs and health behaviour when the API is unavailable or the database path is not writable. Do not use the normal evaluator database to test destructive failure/recovery scenarios.

## Acceptance criteria

- [ ] One documented command builds/starts the core UI and API from a fresh checkout.
- [ ] The repository has one application Dockerfile and one Compose file; one core application container runs one Uvicorn process serving UI and API.
- [ ] The human workflow works in containers without host Python, Ollama, or an API key.
- [ ] Restart/recreation preserves business records and seed execution remains safe.
- [ ] Health checks and logs provide useful failure information without an AI dependency.
- [ ] Tested configuration, port, storage, and image details are recorded.

## Decision record and handover

Explain the user-authorized single-container choice and its trade-offs, same-origin routing, networking, persistence, migration/seed startup, readiness, and logging in ADR 0005. Record actual Docker/Compose versions, tested platform, image versions, and commands/results. Update this guide, the ADR index, [build log](../build-log.md), [AI usage](../ai-usage.md), and [project status](../project-status.md). Write the handoff.

Stop after Phase 05. MVP2 is complete only when the containerised human workflow is verified.
