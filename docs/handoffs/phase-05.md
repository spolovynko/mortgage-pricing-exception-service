# Phase 05 handoff - Containerisation

- Date: 2026-10-29 (Europe/Brussels).
- Status: Implemented and assistant-verified; human acceptance and active work time are not recorded.
- Git: `eb3ef4b` on `main`; phase-completion records are uncommitted. No assistant commit or push.

## Read first

[Project status](../project-status.md), [Phase 05 guide](../phases/phase-05-containerisation.md), [ADR 0005](../adr/0005-containerisation.md), [ADR 0009](../adr/0009-single-process-html-ui.md), and [build evidence](../build-log.md#2026-10-29---phase-05-containerisation).

## Implemented contracts

One digest-pinned multi-stage `Dockerfile` installs locked production dependencies and copies migrations, logging configuration, and root UI assets. `compose.yaml` defines one core `app` service: non-root UID/GID 10001, read-only root, named writable `/app/data` volume, host-loopback port, `/ready` healthcheck, and bounded local logs. Startup validates file-backed writable SQLite storage, migrates, repeatably seeds fixed fictional identities/applications, then replaces itself with one Uvicorn process. `/health` is liveness; `/ready` requires the current schema and a rollback-only write. Core mode sets `LLM_MODE=off`.

## Reproduce and evidence

Run `docker compose up --build`, then open `http://127.0.0.1:8000/`; set `APP_PORT` if occupied. Normal `docker compose down` preserves data. Exact commands and results are in the build entry. Docker Desktop Server 29.9.2, Compose 5.6.1, Linux/WSL2 x86_64, and Python 3.12.12 were observed. The 142-test gate and static/dependency checks passed. Real containers and the in-app browser verified synthetic create/approve/retrieve, recreation persistence, repeatable seeds, API recovery, startup failure on unwritable storage, and 200 liveness/503 readiness with read-only storage.

## Limits and next action

The checks used isolated synthetic volume `mpes-phase05-step4_application-data`; it was preserved. No Linux host outside Docker Desktop, backup/restore, production authentication, multi-instance SQLite, AI/model behavior, or human acceptance is claimed. Records updated: README, architecture, Phase 05 guide, ADR/index, build/AI logs, project status, and this handoff.

Begin Phase 06 only in a separately authorized chat; keep core startup independent of optional AI.
