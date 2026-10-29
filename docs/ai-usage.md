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
