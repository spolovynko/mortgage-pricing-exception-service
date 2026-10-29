# ADR 0009: Serve a separate-file web UI from FastAPI

- Date: 2026-10-29.
- Phase/milestone: Phase 04 architecture update, MVP2.
- Status: Implemented; human acceptance is not recorded.
- Contributor: User selected the direction; Codex implemented and verified it.
- Related requirements: BONUS-01, P-09; Phase 04 guide.
- Supersedes: the Streamlit runtime choice in [ADR 0004](0004-user-interface.md); the HTTP-only/backend-authority boundaries remain.

## Context

The completed Streamlit interface required a separate server process from Uvicorn. The user prefers one process and one command to start the API and UI. The API already exposes the required HTTP workflow and central error/correlation behavior.

## Decision

Replace Streamlit with separate `ui/index.html`, `ui/styles.css`, and `ui/app.js` files served by the existing FastAPI app. Browser requests use same-origin relative API paths and the existing `X-Demo-User`, `Idempotency-Key`, and `X-Correlation-ID` contracts. Keep permissions, request rules, revisions, and decisions in the backend. Store identity, AI preference, and in-flight create intent in per-tab `sessionStorage`; writes occur only after explicit form/button actions. Keep the assessment action disabled until Phase 06.

## Alternatives considered

- Keep Streamlit and start it beside Uvicorn: preserves Python UI tests but keeps two servers and two startup processes.
- Have Uvicorn spawn Streamlit as a child: hides process management behind one command but still runs two servers and complicates shutdown/errors.
- Build a frontend framework/bundler: adds a separate toolchain that is not needed for this small demo. Plain browser assets are sufficient.

## Consequences and revisit conditions

One Uvicorn process and port serve the frontend and current API. Same-origin calls avoid a separate API base URL and CORS setup. Browser code must preserve timeout/error/correlation diagnostics, exact opened-version decisions, and session-scoped idempotent retries. Replace AppTest coverage with static-serving tests and actual browser workflow checks; retain backend contract tests. The root `ui/` files must be included in the Phase 05 runtime image. The original Phase 05 plan separated API and UI containers and left browser routing unresolved. On 2026-10-29, the user authorized one application container running this same Uvicorn process, resolving that conflict without changing browser/API contracts; see the [updated requirement](../requirements.md#project-additions-selected-by-the-user). Container implementation and verification remain Phase 05 work; this approval of the requirement change is not human acceptance of an implementation. Reconsider if UI complexity, accessibility needs, or production authentication justify a frontend framework or separate origin.

Human review and acceptance are not recorded; this record does not imply production readiness.

Verification evidence and limits are recorded in the [Phase 04 architecture update build entry](../build-log.md#2026-10-29---phase-04-single-process-html-ui-update).
