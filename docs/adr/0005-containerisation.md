# ADR 0005: Run the core UI and API in one application container

- Date: 2026-10-29; Phase 05 / MVP2.
- Status: Implemented. The user selected the single-container direction; Codex implemented and verified it. Human acceptance is not recorded.
- Requirements: container addition in [requirements](../requirements.md), Phase 05 guide, and [ADR 0009](0009-single-process-html-ui.md).

## Context and decision

ADR 0009 made FastAPI serve the browser assets and HTTP API from one Uvicorn process. A separate UI container or reverse proxy would add a second runtime without improving this demo's same-origin contract.

Use one multi-stage `Dockerfile` and one `compose.yaml` with one core `app` service. Build locked production dependencies with uv 0.11.6 on the digest-pinned Python 3.12.12 slim-bookworm image; install the project non-editably and copy migrations, logging configuration, and root UI assets. A focused `.dockerignore` excludes local state, secrets, caches, Git data, databases, and model weights.

Run as non-root user `app` (UID/GID 10001) with a read-only root filesystem and a named writable volume at `/app/data`. Publish container port 8000 only on host loopback, configurable through `APP_PORT`. Keep `LLM_MODE=off`; Phase 05 has no Ollama service, API key, or AI readiness dependency.

The Python container entrypoint validates file-backed writable SQLite storage, upgrades Alembic to head, inserts only missing fixed synthetic seeds, and then replaces itself with Uvicorn. Preparation failure exits before business operations become available. `/health` remains process liveness; `/ready` checks the schema revision and performs a rolled-back no-op write so read-only storage returns 503. Compose uses `/ready` for health, JSON stdout/stderr logs, and the local logging driver capped at three 10 MB files.

## Alternatives and consequences

A separate UI container/reverse proxy was rejected because it conflicts with the selected single-process UI and adds routing/configuration. A shell command chain was simpler, but a Python entrypoint makes storage validation, structured failure logging, and focused tests portable. Baking a database into the image was rejected because migrations, seeds, and business records belong on persistent writable storage.

One application process avoids competing migration/seed attempts in the core deployment. SQLite and a single Uvicorn process remain exercise constraints, not a production multi-instance design. The named volume survives normal `docker compose down`; deliberate volume deletion is destructive and documented separately. Optional AI services remain Phase 06 work.

Assistant-observed automated, container, API, and browser evidence is in the [Phase 05 build entry](../build-log.md#2026-10-29---phase-05-containerisation). Testing used Docker Desktop's Linux engine on Windows/WSL2 with synthetic isolated storage. Cross-platform, backup/restore, production authentication, orchestration, AI behavior, and human acceptance are not claimed.
