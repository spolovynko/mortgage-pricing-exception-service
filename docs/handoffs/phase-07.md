# Phase 07 handoff - Core integration testing and CI

- Date: 2026-10-30 (Europe/Brussels). Status: Implemented and assistant-verified; formal human acceptance is not recorded.
- Git: branch `main`; starting HEAD `5ab3a33`. Changes remain uncommitted; no push or PR.
- Read first: [status](../project-status.md), [Phase 07 guide](../phases/phase-07-testing-evaluation-and-ci.md), [ADR 0007](../adr/0007-testing-evaluation-and-ci.md), and [verification](../build-log.md#2026-10-30---phase-07-core-integration-testing-and-ci).
- Changes: retry and stale-review UI regressions; corrected nullable financial fields in the Phase 03 lookup contract; `.github/workflows/ci.yml` for locked setup, Ruff, JS syntax, Node and pytest; `scripts/core-container-smoke.ps1` for isolated synthetic startup, create, reviewer approval, history, cached-image recreation and replay.
- Verification: 155 Python tests, 8 Node tests, Ruff lint/format, JS syntax, lock/dependency checks, Compose config, and isolated container smoke passed. Live local browser outage/retry, stale decision/refresh and 390 px width/focus checks passed. Full command details and limits are in the build entry.
- Reproduce smoke: from PowerShell use `./scripts/core-container-smoke.ps1 -ProjectName mpes-p07-<unique-guid> -Port <free-loopback-port>`. It builds then tests with a unique Compose project. It removes the service/network but intentionally preserves the uniquely named application-data volume; remove it only through explicit project-specific cleanup if desired.
- Limits: hosted CI not run; package installation used registry access; offline first build, second host, exhaustive accessibility and AI quality/judge behavior not verified. AI-specific AC-08/09 and AC-10 model portion are deferred to Phase 09. No production auth claim. No assistant commit/push.
- Records: Phase 07 guide, ADR/index, build log, AI-use log, project status, Phase 03 API contract and this handoff.
- Next: Phase 08 documentation and handover.
