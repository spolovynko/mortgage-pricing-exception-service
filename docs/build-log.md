# Build log

Append chronological entries. Preserve earlier observations; add a correction when later evidence changes a conclusion. Distinguish plans, implemented changes, verification results, and unresolved issues.

Record actual active work time when known, including AI-assisted work according to the submission approach. Do not fabricate durations or calculate work time from calendar gaps.

## Entry format

```text
Date/time and timezone:
Phase and milestone:
Work performed:
Files/components affected:
Decision record:
Checks run and observed outcomes:
AI contribution and human review:
Problems, limitations, and corrections:
Active work duration / cumulative recorded duration:
Next action:
```

## 2026-10-28 - Documentation scaffold

- Phase/milestone: pre-implementation planning, supporting MVP1.
- Work performed: drafted the project instructions, eight phase guides, requirements, architecture, coding and commit standards, ADR/handoff templates, and project records.
- Context: the user chose Python, a Streamlit UI, optional local AI with automated setup, and one shared application Dockerfile with one Compose file.
- Implementation state: application code, containers, database, tests, and local-model integration have not been built in this scaffold.
- Decision record: no formal phase ADR yet. Planning defaults are identified as proposals in requirements.md and architecture.md.
- Verification: static scaffold validation is pending at the time of this entry. No application or model tests have run.
- AI contribution: the assistant drafted the documents from the assignment and planning discussion. Human acceptance of the generated scaffold has not been recorded.
- Active/cumulative duration: not recorded.
- Next action: validate the documentation scaffold, then start Phase 01 in a separate chat.

## 2026-10-28 - Static scaffold verification

- Work performed: checked the generated scaffold with a temporary PowerShell validation helper outside the deliverable folder.
- Observed outcome: PASS; 21 Markdown files, eight phase guides, and 105 relative links checked. No missing expected files, empty files, broken local links, unbalanced code fences, excluded organisation names, or premature completed implementation checkboxes were found.
- Phase-guide checks: each guide has an objective, required reading, implementation tasks, acceptance criteria, initial Not started status, and planned ADR/handoff paths.
- Limits: this is a static documentation check, not a Markdown rendering guarantee or verification of the planned application. No Python application, container stack, or live model was run.
- AI contribution/human review: an assistant authored and executed the static checker and reviewed the document structure. Human acceptance remains unrecorded.
- Active/cumulative duration: not recorded.
- Next action: start Phase 01 from the same project folder in a new chat.

## 2026-10-28 - Place scaffold in the project working folder

- User request: place the generated documents in the active project folder.
- Destination: `C:\Projects\mortgage-pricing-exception-service`.
- Work performed: copied 20 new Markdown files and merged the scaffold README body while preserving the existing repository title. The existing .gitignore and Git repository were preserved. No commits were created.
- Verification: the destination passed the static check for 21 Markdown files, eight phase guides, and 105 relative links; git diff --check reported no whitespace errors. The .gitignore SHA256 was unchanged before/after placement.
- Limits: documentation placement only; no implementation phase, application test, container build, or live-model evaluation was performed.
- Active/cumulative duration: not recorded.
- Next action: implement Phase 01 in a separate chat opened in this project folder.

## 2026-10-29 - Phase 01, Step 2: Python project setup

- User request/scope: implement Step 2 only, then stop. Inspected the current instructions, phase/status/engineering references, prior records, and Git state; initial working tree was clean on `main` at `4e756fe`. No unrelated user changes were present.
- Work performed: added `pyproject.toml`, `.python-version`, `src/mortgage_pricing/__init__.py`, and `uv.lock`. Selected the Python 3.12 series and uv's project/lock workflow; pinned Hatchling 1.30.1 as build backend. Installed only FastAPI, Uvicorn, Pydantic Settings, and their resolved runtime dependencies. Existing .gitignore already excludes the environment and bytecode and was preserved.
- Commands/results: `uv lock` resolved 17 packages, including this project; `uv sync --locked` created a fresh `.venv` with CPython 3.12.12 and installed all 17 packages, including an editable project build. uv version: 0.11.6. Primary resolved versions: FastAPI 0.162.0, Uvicorn 0.54.0, Pydantic Settings 2.16.2; Pydantic 2.14.1 and Starlette 1.10.0 are transitive. Exact versions/hashes and public PyPI source are in `uv.lock`.
- Verification: `uv lock --check` passed. `uv pip check` reported all installed packages compatible. `uv run --locked python -I -c "import sys; import mortgage_pricing, fastapi, pydantic_settings, uvicorn; assert sys.version_info[:2] == (3, 12); assert sys.prefix != sys.base_prefix; print('Python:', sys.version.split()[0]); print('Virtual environment:', sys.prefix); print('Installed package:', mortgage_pricing.__file__); print('Runtime dependency imports: OK')"` passed, showing `.venv` and the installed source package. `git check-ignore .venv/pyvenv.cfg src/mortgage_pricing/__pycache__/__init__.cpython-312.pyc` confirmed both generated paths are ignored.
- Observations/corrections: concurrent uv verification commands emitted temporary cache-write `Access is denied` warnings but exited successfully. Sequential reruns of lock and isolated-import checks passed without warnings. No global cache or Git configuration was changed.
- Records updated: README setup/current scope, phase incremental checklist, project status, architecture packaging note, [ADR 0001](adr/0001-foundation-config-logging.md) and index, and AI-use record. ADR status is Implemented for Step 2 only; the phase remains In progress and all phase acceptance criteria remain unchecked. Final record/whitespace verification is recorded below.
- Final record checks: a temporary stdin helper run with `.venv/Scripts/python.exe -I -` passed for 22 Markdown files, 122 local links, balanced fenced blocks, Step 2 source scope, and no checked phase acceptance criteria. `git diff --check` passed; Git's existing CRLF configuration emitted informational conversion warnings. Reviewed the final tracked/untracked inventory; only Step 2 files and corresponding records changed, with generated environment/bytecode ignored.
- Limits: Windows/CPython 3.12.12 installation/import checks only. No tests or lint configuration, API, settings, logging, identity handling, database, UI, containers, or model implementation/testing. No human code acceptance or live-model result is recorded. The phase handoff remains a phase-completion task.
- AI contribution: assistant inspected source/tool outputs, selected routine setup details, authored code/docs, and executed checks. Human review of the resulting files is not recorded.
- Active/cumulative work duration: not recorded.
- Next action: Step 3 (development checks), only when the user requests it. No commits or pushes were made.

## 2026-10-29 - Phase 01, Step 3: development checks

- Scope/state: user requested Step 3 only. Inspected instructions, existing code/configuration/records, and Git status before changing files. Working tree was clean; Step 2 was committed at `d135997`. No unrelated changes were present.
- Work: `uv add --dev "pytest>=8,<10" "ruff>=0.9,<1"` added pytest 9.2.0 and Ruff 0.17.3 to the development dependency group, with 24 total locked packages including the project. Added pytest discovery under `tests/`, `importlib` import mode, strict configuration/marker checks, and warnings-as-errors. Added Ruff Python 3.12/100-character configuration with lint groups `E`, `F`, `I`, `UP`, `B`, `SIM`. Added one packaging integration test that imports the installed package and reads distribution metadata in an isolated subprocess from a temporary directory.
- Commands/results: `uv run --locked python -m pytest` -> **1 passed**; `uv run --locked python -m ruff check .` -> all checks passed; `uv run --locked python -m ruff format --check .` -> passed; `uv lock --check` -> passed, 24 packages; `uv pip check` -> all installed packages compatible. `uv run --locked python -m ruff check --show-files` confirmed discovery of `pyproject.toml`, source, and test. Tested Windows/CPython 3.12.12 with uv 0.11.6. No failing test/lint result or suppressed warning occurred.
- Records: updated README commands/current scope, ADR 0001 and its index, phase checklist, project status, and AI-use record. Step 2 evidence remains historical; Phase 01 behavioral acceptance criteria remain unchecked. Final static/diff review is recorded below after execution.
- Final review: `git diff --check` passed (informational CRLF conversion warnings only). A temporary stdin helper run with `.venv/Scripts/python.exe -I -` passed for 22 Markdown files, 122 local links, balanced fenced blocks, unchanged versions for all previously locked dependencies, Step 3-only source additions, deferred later phases/acceptance, and generated-cache ignore rules. Inspected the final tracked/untracked file inventory; no unrelated code or later-step implementation changed.
- Limits: the single test verifies packaging, not application behavior. No API, configuration, logging, error handling, business rule, database, UI, container, model, CI, or pre-commit implementation was added. No external network/database/model is needed by the test. Application behavior and other platforms remain unverified.
- AI/review: assistant authored config/test/records and inspected outputs, using local tools plus official pytest/Ruff documentation. No subagents used and no human review/acceptance of this change is recorded. Active/cumulative work time is not recorded.
- Next action: Step 4, central configuration, only when requested. No commit or push was made by the assistant.

## 2026-10-29 - Phase 01, Step 4: central configuration

- Scope/state: user requested Step 4 after Steps 2-3. The worktree was clean at `986bd18`; inspected the phase guide, requirements/architecture and engineering guidance, current settings/package/tests, README, ADR, status, and .gitignore before editing.
- Work: added immutable Pydantic `Settings` and on-demand `get_settings()` in `src/mortgage_pricing/config.py`; added safe `.env.example`; added tests for defaults, env and dotenv precedence, invalid mode/bounds/database scheme, validation input hiding, and immutability. Documented configuration/setup usage in README; updated the Phase 01 checklist, architecture, project status, ADR 0001/index. No database/model/service connection or API behavior was added.
- Verification: first test run exposed a flawed test assertion that searched for invalid values also present in validation constraints; narrowed it to the unique invalid app-environment string and reran. Final `uv run --locked python -m pytest` -> **12 passed**. `uv run --locked python -m ruff check .`, `uv run --locked python -m ruff format --check .`, `uv lock --check` (24 packages), `uv pip check`, and `git diff --check` passed. Ruff formatter changed `config.py` before final successful checks. Git emitted informational LF-to-CRLF conversion warning. Windows/CPython 3.12.12, pytest 9.2.0, Ruff 0.17.3, uv 0.11.6.
- Limits: this verifies settings construction and existing package import only. No app startup, HTTP health/error response, logging, database connection, model discovery/inference, or cross-platform behavior was tested. Phase 01 remains incomplete and its acceptance criteria remain unchecked. No human code review/acceptance or work duration is recorded.
- Next action: Step 5 (minimal API and health endpoint), only on user request. No commit or push was made.

## 2026-10-29 - Phase 01, Step 5: minimal API and health endpoint

- Scope/state: user requested Step 5 after Step 4 commit `2ceb97e`. Inspected Git state and the phase guide, requirements/architecture, README, status, and ADR before edits; no uncommitted user changes were present.
- Work: added `create_app(settings=None)`, a typed process-liveness `GET /health`, and API tests for response shape and per-app settings isolation. Added `httpx2>=2,<3` to the dev group and lock because installed Starlette 1.10 deprecates legacy httpx in its TestClient and project pytest treats warnings as errors. Documented the launch/check commands; updated the phase checklist, architecture, ADR/index, status, README, AI usage, and this log. No business routes, structured logging, error envelope, readiness probes, or service connection were implemented.
- Verification: first test collection failed on Starlette's warning-as-error with legacy httpx; switched to its supported httpx2 dependency. Final `uv run --locked python -m pytest` -> **14 passed**. Ruff lint/format, `uv lock --check` (28 packages), `uv pip check`, and `git diff --check` passed. Live check: Uvicorn factory served at `127.0.0.1:8765`; PowerShell `Invoke-RestMethod` to `/health` returned `{"status":"ok"}`; server stopped after request. Windows/CPython 3.12.12, uv 0.11.6, FastAPI 0.162.0, Starlette 1.10.0.
- Limits/review: health is process liveness only, not dependency readiness. No error/logging behavior or cross-platform check. Assistant reviewed outputs; human review/acceptance and active work duration are not recorded. Phase acceptance remains unchecked and handoff remains due at phase completion. No commit/push.
- Next action: Step 6 (structured logging), only when requested.

## 2026-10-29 - Phase 01, Step 6: structured logging and correlation

- State/scope: inspected clean worktree at `5b8ed82`, app/settings/tests, phase/status, architecture, logging requirements, engineering guidance, and recent records. User authorized Step 6 only.
- Work: added independent per-app standard-library JSON logging, context-based correlation and pure ASGI request middleware. Added bounded/validated incoming IDs, UUID fallback, handled-response headers, completion/failure events, metadata allowlist and safe stack diagnostics. Added Uvicorn JSON configuration and documented `--no-access-log`. Updated README, architecture, phase checklist, ADR 0001/index, project status, and AI-use evidence. No dependencies changed.
- Checks: `uv run --locked python -m pytest tests/test_logging.py` initially passed 13 cases; added the 64-character boundary test before the full run. `uv run --locked python -m pytest` -> **28 passed** (14 logging cases). `uv run --locked python -m ruff check .` and `uv run --locked python -m ruff format --check .` passed. `uv lock --check` -> 28 packages; `uv pip check` -> all installed packages compatible. Formatter applied to new source/test files before verification. Final diff/record inspection is recorded below after execution.
- Live verification: `uv run --locked uvicorn mortgage_pricing.main:create_app --factory --host 127.0.0.1 --port 8765 --log-config config/logging.json --no-access-log`; a temporary stdin Python urllib client requested `/health` with ID `live-success` and `/missing?token=synthetic-secret` with ID `live-failure`. Observed 200/404 with matching response IDs and one JSON completion record each (INFO/success and WARNING/failure), durations, matched health route and null unknown route. Server lifecycle messages were JSON; the query secret was absent. Stopped the server after inspection.
- Review/limits: Windows/CPython 3.12.12 only. Tests cover overlapping async request isolation/reset, levels/handlers, safe metadata/diagnostics and correlation. Unhandled exceptions are logged/rethrown; their consistent envelope and response correlation remain Step 7 work. Phase remains incomplete; handoff remains due at completion. Assistant inspected outputs; human review/acceptance and work duration are not recorded. No commit/push.
- Next action: Step 7 (consistent, safe HTTP errors), only when requested.
- Final review: `git diff --check` passed after record updates (existing informational LF-to-CRLF warnings). Inspected new source/tests/configuration and final changed-file inventory; changes are limited to Step 6 and its records, with no dependency/lock changes or phase-completion claim.
