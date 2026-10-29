# Phase 04 - User interface

- Status: Complete (2026-10-29); implementation and acceptance evidence recorded below.
- Milestone: MVP2.
- Prerequisite: Phase 03 API contracts and behaviour verified.
- Primary ADR to create: `docs/adr/0004-user-interface.md`.
- Handoff to create: `docs/handoffs/phase-04.md`.

## Objective

Let an evaluator complete the human workflow in a simple Streamlit UI. Provide an honest, initially unavailable AI control that can be connected in Phase 06.

## Read first

[AGENTS.md](../../AGENTS.md), [requirements](../requirements.md), [architecture](../architecture.md), [engineering guidelines](../python-engineering-guidelines.md), current status, the Phase 03 handoff, and API/version-policy ADRs.

## Scope and expected components

Create ui/app.py and a small HTTP API client. Split views only when it makes the UI clearer. The UI must not import persistence code or talk directly to Ollama.

## Implementation tasks

- [x] Create Requests, Review, and History screens with useful navigation and empty states.
- [x] Add a clearly labelled demo-user selector using seeded identities and server-side role checks.
- [x] List/select applications and requests; show submitted terms, current version, status, creator, decisions, and timestamps.
- [x] Provide create and revision forms with helpful input errors and an explanation that revised terms need fresh review.
- [x] Preserve an idempotency key for one submission across retries. Generate a new key only for a genuinely new submission intent.
- [x] Submit the version the reviewer actually opened with each decision. On a stale-version conflict, show a clear refresh/review path.
- [x] Display earlier approved versions as historical when a newer version is pending; do not suggest they are currently usable.
- [x] Handle API errors, timeouts, and unavailable backend states without losing entered text unnecessarily.
- [x] Add a session-scoped Use AI assistance toggle and explicit Generate assessment action. Until Phase 06, disable generation and show that AI is not implemented/available; do not fabricate output.
- [x] Keep all side-effecting operations behind explicit user actions and prevent Streamlit reruns from resubmitting requests or decisions.
- [x] Add UI tests for important interactions using Streamlit AppTest with an explicit fake API client where appropriate.

## Verification

Manually complete create/approve/retrieve, decline/history, and revise/review flows through the real backend. Switch between two user sessions or simulated session contexts and verify assistance choices do not become global state. Confirm direct API calls still enforce permissions regardless of UI visibility.

Test a backend failure, a repeated form action/retry, and an outdated review screen. Verify changing filters or toggles does not make unintended write calls.

## Acceptance criteria

- [x] An evaluator can use the complete human workflow without manually constructing JSON.
- [x] UI state matches backend state, including current versions and old approvals.
- [x] Important UI tests pass, and actual end-to-end human scenarios have been exercised.
- [x] Demo identity and unavailable AI are labelled accurately.
- [x] Toggle changes/reruns do not trigger inference or business writes automatically.

## Decision record and handover

Explain screen layout, UI/API separation, session/retry handling, error states, and the planned AI interaction. Record manual and automated outcomes. Update this guide, the ADR index, [build log](../build-log.md), [AI usage](../ai-usage.md), and [project status](../project-status.md), then write the handoff.

Stop after Phase 04. The next phase packages the working human UI/API workflow in containers.

## Completion evidence

The final build-log entry records the exact commands, AppTest evidence, live HTTP/UI workflows, session/error/retry/stale checks, static/dependency gate, and limits. Live workflows used a temporary migrated file-backed SQLite database with fictional seed identities; AppTest uses an explicit fake API client. The assistant reviewed code and results. Human review/acceptance and active work time are not recorded. The root `ui/` source tree is used by the repository-run Streamlit entry point and is not included in the Python wheel package list; Phase 05 must include this tree in its shared runtime image.
