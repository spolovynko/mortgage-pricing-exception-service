# Phase 05 - Containerisation

- Status: Not started.
- Milestone: MVP2.
- Prerequisite: Phase 04 UI/API human workflow verified.
- Primary ADR to create: `docs/adr/0005-containerisation.md`.
- Handoff to create: `docs/handoffs/phase-05.md`.

## Objective

Start the core application through one Compose command using **one shared application Dockerfile and one Compose file**. Separate API and UI processes run in separate containers from the same application image.

## Read first

[AGENTS.md](../../AGENTS.md), [architecture](../architecture.md), [engineering guidelines](../python-engineering-guidelines.md), current status, the Phase 04 handoff, and foundation/database/UI ADRs.

## Expected files and services

Create Dockerfile, compose.yaml, and .dockerignore. API and UI services share the built image with different startup commands. A Python model-init job may later reuse it; Ollama will use its own official image in Phase 06.

Use a named application-data volume owned/writable by the API runtime user. Do not add a separate database-server container for SQLite.

## Implementation tasks

- [ ] Build a compact Python application image from pinned, tested dependencies and a pinned base image.
- [ ] Include API/UI code and their dependencies in the shared image. Keep model weights, databases, .env files, caches, and Git internals out of the build context.
- [ ] Define reliable shared-image build behaviour for a clean checkout, not just a host that already has an image tag cached.
- [ ] Define API and UI commands, service-name networking, validated environment settings, and necessary host-loopback ports.
- [ ] Make the UI call the API service address inside Compose, not its own localhost.
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
- [ ] The repository has one application Dockerfile and one Compose file, with separate service commands.
- [ ] The human workflow works in containers without host Python, Ollama, or an API key.
- [ ] Restart/recreation preserves business records and seed execution remains safe.
- [ ] Health checks and logs provide useful failure information without an AI dependency.
- [ ] Tested configuration, port, storage, and image details are recorded.

## Decision record and handover

Explain shared-image trade-offs, networking, persistence, migration/seed startup, readiness, and logging. Record actual Docker/Compose versions, tested platform, image versions, and commands/results. Update this guide, the ADR index, [build log](../build-log.md), [AI usage](../ai-usage.md), and [project status](../project-status.md). Write the handoff.

Stop after Phase 05. MVP2 is complete only when the containerised human workflow is verified.
