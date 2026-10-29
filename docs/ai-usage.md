# AI development and evaluation record

Maintain this record throughout development. Explain useful agentic contributions and how their output was checked. Product AI features do not replace evidence of AI-assisted engineering.

## Contribution entry template

```text
Date and phase:
Task given to the assistant/agent:
Context and tools it used:
Output/change produced:
Human review actually performed:
Suggestions accepted, corrected, or rejected:
Independent checks and observed results:
Remaining risks or verification gaps:
Related files, ADR, build-log entry, and commit if present:
```

State who actually reviewed something. An assistant's own review is not human review. Generated tests and their implementation can share the same mistaken assumption, so validate them against the written acceptance examples.

## 2026-10-28 - Requirements discussion and scaffold generation

- Task: translate the supplied assignment and the user's choices into a phase-by-phase Python implementation scaffold.
- Contribution: the assistant read the assignment, explained the workflow, researched relevant official documentation, and drafted the project documents. The user selected the repository name, requested optional local AI and automated setup, chose one shared Dockerfile, and requested phase/ADR/build/commit guidance.
- Corrections during planning: pricing-exception approval was distinguished from mortgage credit approval; the original two-Dockerfile proposal was changed to a shared image used by separate service containers.
- Generated artefacts: the Markdown scaffold described in README.md.
- Human review: the user steered the planning choices. Review/acceptance of these final generated documents is not yet recorded.
- Verification: see the actual scaffold-validation entry in the build log once completed. No application behaviour, judge accuracy, or model performance has been validated by this planning work.
- Remaining gaps: all implementation phases, real test results, local-model resource measurements, and human-labelled AI evaluation are outstanding.

## Product AI evidence to add in Phases 06-07

Record the actual runtime image/version, model name and digest, quantisation, prompt/checklist/rubric versions, input/output limits, sampling settings, hardware, and evaluation date.

Keep the live review assistant and offline LLM judge distinct. Define what the judge grades and compare it with human-labelled cases. Report false passes, unsupported statements, repeated-run variability, and latency. Label synthetic data, fakes, fixtures, and live outputs accurately.

If the model cannot be downloaded or tested, record that limitation. Do not substitute invented scores, claim a fixture is live inference, or mark the live-model criteria complete.

## 2026-10-29 - Phase 01, Step 2: Python project setup

- Task and scope: user authorised Step 2 only. Read current repository instructions, phase/status/engineering documents, relevant requirements/architecture, and existing records; inspected clean Git state and installed interpreters/uv.
- Contribution/tools: assistant created Python 3.12 metadata, an importable source package, uv lockfile, and setup/status/decision records; used PowerShell, Git, uv, isolated Python imports, and official Python/uv documentation. No subagents or product-model calls were used.
- Observed checks: fresh `uv sync --locked` installed 17 packages in `.venv`; lock consistency, installed dependency consistency, isolated package/runtime imports, Python version/venv assertions, and ignored-output checks passed. Transient uv cache warnings during concurrent checks were absent on sequential reruns. See [build log](build-log.md) for exact commands and final record checks.
- Human review: implementation authorisation was provided; review/acceptance of the resulting code and documents is not recorded. All output inspection described here was by the assistant.
- Limits: no application behavior tests or lint checks were configured/run; only packaging/import compatibility was checked, on Windows/CPython 3.12.12. Phase 01 remains incomplete. No active work duration, production suitability, or model quality is claimed.
- Related records: [ADR 0001](adr/0001-foundation-config-logging.md), [phase guide](phases/phase-01-foundation-config-logging.md), [project status](project-status.md). Next step is development-check configuration; no commit or push made.

## 2026-10-29 - Phase 01, Step 3: development checks

- Task/scope: implement Step 3 only. Assistant inspected a clean working tree at `d135997`, current project configuration, phase instructions, and existing records before editing.
- Contribution: added pytest/Ruff as locked development dependencies, configured test/lint/format commands, and wrote one packaging integration test using an isolated interpreter outside the repository working directory. Updated README and incremental decision/status/checklist records. Used PowerShell, uv, Python, pytest, Ruff, Git, and official pytest/Ruff documentation; no subagents or product-model calls.
- Actual verification: pytest **1 passed**; Ruff lint and format checks passed; lock/dependency consistency passed. Ruff's file listing confirmed intended configuration/source/test discovery. Exact commands and final static checks are recorded in the build log.
- Review/limits: assistant inspected generated output and actual tool results. Human acceptance of Step 3 is not recorded. The test verifies installed-package availability and distribution metadata; it establishes no API/configuration/logging/business behavior. Only Windows/CPython 3.12.12 was tested; no duration or production/model-quality claim is made.
- Continuation: Step 4 remains unstarted; Phase 01 remains incomplete. The assistant created no commits or pushes.

## 2026-10-29 - Phase 01, Step 4: central configuration

- Task/scope: implement central configuration only. Assistant inspected current files and worktree at `986bd18` before edits.
- Contribution: authored immutable Pydantic settings, `.env.example`, configuration tests, and related README/ADR/architecture/status/checklist/build-log updates. Used PowerShell, Git, uv, Python, pytest, Ruff, and the existing local project documentation. No subagents, API/model calls, or external sources were used.
- Actual verification: `uv run --locked python -m pytest` -> 12 passed; Ruff lint/format, lock consistency, installed dependency checks, and `git diff --check` passed. See [build log](build-log.md) for exact commands, environment, and the initial assertion correction.
- Review/limits: assistant inspected tool output. Human review and acceptance are not recorded. The tests validate settings construction only, not app startup, health/errors, logging, database/model operations, or platform compatibility. No duration is recorded. Phase remains incomplete; no commit/push was made.

## 2026-10-29 - Phase 01, Step 5: minimal API and health endpoint

- Task/scope: implement the app factory and process health endpoint only. Assistant inspected clean Git state and scoped references before editing.
- Contribution: authored the FastAPI factory/health response, tests, selected the Starlette-supported test-client dependency after an observed deprecation failure, and updated setup/phase/architecture/ADR/status records. Used local PowerShell, Git, uv, Uvicorn, pytest, Ruff, and project docs. No subagents or external model/API calls.
- Actual verification: 14 pytest cases passed, Ruff lint/format, lock/dependency checks and diff check passed. A live Uvicorn `/health` request returned `{"status":"ok"}`. Exact commands and versions are in [build log](build-log.md).
- Review/limits: assistant inspected outputs; human review/acceptance is not recorded. Endpoint proves process liveness only. No structured logging, errors, database/model readiness, cross-platform behavior, or work duration is claimed. Phase incomplete; no commit/push.

## 2026-10-29 - Phase 01, Step 6: structured logging and correlation

- Task/scope: Step 6 only, starting from clean Step 5 commit `5b8ed82`. Assistant inspected current app/config/tests and relevant project instructions/records before editing.
- Contribution: selected standard-library JSON logging and pure ASGI middleware, authored code, 14 logging tests, Uvicorn log configuration, README/architecture/ADR/checklist/status updates, and evidence records. Used local PowerShell, Python, Git, uv, pytest, Ruff, and Uvicorn. No subagents or external AI/API calls.
- Verification: 28 total tests passed; lint/format and lock/dependency checks passed. Live local Uvicorn success/404 requests returned correlation headers matching JSON logs and excluded the synthetic query secret. Exact commands/results and final review are in [build log](build-log.md).
- Review/limits: assistant reviewed code and output; no human review/acceptance or duration is recorded. HTTP error envelopes and unhandled 500 response correlation remain Step 7 work. No business/database/model/container verification; Windows/CPython 3.12.12 only. Phase incomplete; no commit/push.

## 2026-10-29 - Phase 01, Step 7: safe, consistent HTTP errors

- Task/scope: Step 7 only; inspected clean Step 6 commit `2f691b5` and current code/instructions/records.
- Contribution: authored `errors.py`, integrated handlers and safe unexpected-error handling into existing tracing, wrote 12 meaningful error tests, and updated README/architecture/ADR/checklist/status/evidence. Used local PowerShell, Python, uv, Git, pytest, Ruff, and Uvicorn; no subagents or external model/API calls.
- Actual verification: 40 total tests passed; lint/format and dependency/lock checks passed. Live 200/500 requests against a temporary in-memory Uvicorn test route returned safe correlated responses and one diagnostic per failure; synthetic exception message absent. Exact commands and scope are in [build log](build-log.md).
- Review/limits: assistant inspected outputs; human review/acceptance and work duration not recorded. Already-started responses cannot be replaced. No business/database/model/container checks or phase-completion claim. Fresh-environment verification and handoff remain pending. No commit/push.

## 2026-10-29 - Phase 01, Step 8: final verification and completion

- Task/scope: finish Phase 01 only, starting from clean `e9358eb` on `main`. Assistant inspected existing state/template and found the remaining test-environment isolation gap.
- Contribution: added test isolation plus configuration precedence/example/URL/model/timeout checks; performed fresh installation, live health/error logging, and invalid external-settings scenarios; completed checklist, ADR/index, handoff, README, architecture/status and evidence records. Used local Python/PowerShell, Git, uv, pytest, Ruff, and Uvicorn. No subagents or external AI/API/model calls.
- Observed verification: 48 tests pass in workspace, fresh temporary venv, and intentionally invalid external shell/dotenv scenario. Lint/format, lock/dependency consistency pass. Fresh API returned correlated 200/404 responses with safe matching logs. Owned verification process/environment artifacts were removed; developer `.venv`/settings preserved. Exact commands, versions and final static checks are in [build log](build-log.md).
- Review/limits: assistant reviewed implementation and actual outputs. User authorized incremental work; human code review or acceptance is not recorded. No time estimate, production-readiness, cross-platform or live-model result is claimed. Optional UI stub omitted explicitly; future phases remain unimplemented. Phase 01 is complete based on its observed acceptance evidence. No commit/push.

## 2026-10-29 - Phase 02, Step 1: baseline and persistence boundaries

- Task/scope: user authorized Step 1 only. The assistant inspected the clean `0bc29a0` baseline, all required phase references, actual source/tests, and dependency metadata. No subagents or product-model calls were used.
- Contribution: confirmed the persistence boundary and twelve-step execution order; ran and inspected the existing test, lint, format, lock, and dependency checks; corrected current status records to show Phase 01 committed and Phase 02 baseline work in progress.
- Actual verification: **48 tests passed**; Ruff lint and format checks passed; lock consistency passed with 28 resolved packages; installed dependency consistency passed for 29 checked packages. Exact commands and limitations are in the build log.
- Review/limits: assistant review only; no human review or acceptance is recorded. No database capability or later-step behavior was implemented or claimed. Active work time is not recorded. Step 2 requires a new user instruction. No commit/push.

## 2026-10-29 - Phase 02, Step 2: persistence foundation

- Task/scope: user authorized Step 2 only. Assistant inspected clean `54e219e`, current instructions/records, actual app/configuration/logging/error boundaries, tests, and dependencies before changes.
- Contribution: authored lazy SQLite engine/session factories, shared metadata, timeout settings/validation, storage ignore rules, 11 file-backed resource tests, ADR 0002/index, and related setup/architecture/progress/evidence updates. Used PowerShell, Python, Git, uv, pytest, Ruff, and official SQLAlchemy/Alembic documentation. No subagents or product-model calls.
- Actual verification: targeted suite **33 passed**, full suite **62 passed**; Ruff lint/format, lock/dependency checks, and Alembic version command passed. All 28 previous locked package versions remain unchanged; five packages added. One initial long-line lint finding was corrected by formatting. Exact commands, runtime versions, static checks, and observed resource-lifetime behavior are in the build log.
- Review/limits: assistant inspected source and actual outputs; human review/acceptance is not recorded. Probe schemas exist only in pytest-owned temporary databases. Step 3 foreign keys/driver transaction configuration, business models, operational migrations/seeds, API storage lifecycle/readiness, and whole-phase acceptance remain pending. No normal database was opened/reset, no work duration is claimed, and no commit/push was made. Stop before Step 3 until instructed.

## 2026-10-29 - Phase 02, Step 3: SQLite transaction configuration

- Task/scope: user authorized Step 3 only. Assistant inspected a clean worktree, persistence source/tests, phase instructions and records. No subagents or external model/API calls were used.
- Contribution: implemented explicit sqlite3 transaction mode and per-connection foreign keys, wrote five file-backed behavior tests, and updated ADR/progress/evidence. Used PowerShell, Git, uv, pytest, Ruff, and official SQLAlchemy SQLite documentation.
- Actual verification: 16 persistence tests and 67 total tests passed; final Ruff lint/format, lock, and dependency checks passed. An initial lint finding was corrected. Exact commands and observed results are in the build log.
- Review/limits: assistant inspected code and output; human review/acceptance and work duration are not recorded. Tests cover temporary SQLite probe schemas, not business models or operational migrations. No normal database was touched, no commit/push. Step 4 remains user-gated.

## 2026-10-29 - Phase 02, Step 4: users, roles, and applications

- Task/scope: user authorized Step 4 only. Assistant inspected clean `0add25c`, persistence foundation, requirements, architecture, and current records. No subagents or product-model calls were used.
- Contribution: authored user, role-membership, application, and UTC datetime models; six database-backed model tests; and the associated ADR/progress/evidence updates. Used PowerShell, Git, uv, pytest, Ruff, and SQLAlchemy's installed API.
- Actual verification: model suite **6 passed** and persistence suite **22 passed**. Initial tests exposed SQLite timezone round-trip loss and SQLAlchemy enum parameter validation; implementation/test changes made the storage behavior explicit and verified the database enum check. Exact final commands/results are in the build log.
- Review/limits: assistant inspected source and observed outputs; human review/acceptance and work duration are not recorded. No migration, seed, normal database, business endpoint, permission service, or self-review control was added. No commit/push. Step 5 remains user-gated.

## 2026-10-29 - Phase 02, Step 5: logical requests and versions

- Task/scope: user authorized Step 5 only. Assistant inspected the dirty worktree and preserved uncommitted Step 4 changes. No subagents or product-model calls were used.
- Contribution: authored request/version ORM models, current-version relationship constraint, ORM immutability guard, ten isolated file-backed tests, and progress/decision records. Used PowerShell, Git, uv, pytest, Ruff, and installed SQLAlchemy.
- Actual verification: focused version suite **10 passed**, full suite **83 passed**; final Ruff lint/format and lock/dependency checks passed. Initial helper ordering and detached-instance test failures were corrected. Exact commands and limits appear in the build log.
- Review/limits: assistant inspected source and outputs; human review/acceptance and work duration are not recorded. Direct SQL immutability, decision/history schema, migration, seeds, and business operations remain pending. No normal database, commit, or push. Step 6 remains user-gated.
