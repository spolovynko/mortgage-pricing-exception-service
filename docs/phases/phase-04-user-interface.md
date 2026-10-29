# Phase 04 - User interface

- Status: Complete with structured-context follow-up (2026-10-29); implementation and verification evidence recorded. Human acceptance is not recorded.
- Milestone: MVP2.
- Prerequisite: Phase 03 API contracts and behavior verified.
- Primary ADR: [ADR 0004](../adr/0004-user-interface.md), superseded for runtime delivery by [ADR 0009](../adr/0009-single-process-html-ui.md); structured context is in [ADR 0010](../adr/0010-versioned-request-context.md).
- Handoff: [Phase 04](../handoffs/phase-04.md).

## Objective

Let an evaluator complete the human workflow in a minimal browser UI served by the API process. Keep an honest, unavailable AI control for Phase 06.

## Scope and boundaries

Keep `ui/index.html`, `ui/styles.css`, and `ui/app.js` separate. FastAPI serves them from the same origin as the API. The UI communicates over HTTP and never imports persistence code or calls Ollama. Permissions, business rules, versions, and decisions remain backend-enforced.

## Acceptance

- [x] One Uvicorn process serves the UI and API; its root page loads separate HTML, CSS, and JavaScript files.
- [x] Requests, Review, and History provide navigation, filters, and clear empty states; controls reflect the simulated demo user's role.
- [x] Request/application details show exact terms, structured context snapshots, versions, status, actors, decisions, and timestamps. Prior approvals are labelled historical; pricing is shown only when currently approved.
- [x] New versions capture typed mortgage facts, reason category, and optional unverified competitor offer alongside free-text reason; context is immutable per version and included in history.
- [x] Create and revision preserve entered text/context across failures; retries retain a session-scoped idempotency key that fingerprints structured context too. Revisions explain fresh review and retain a new context snapshot.
- [x] Decisions submit the version displayed to the reviewer. A stale conflict refreshes both detail and queue before a fresh review.
- [x] API error envelopes, timeout/unavailable states, and correlation IDs are visible and safe to retry.
- [x] The assistance preference is tab-session scoped; Generate assessment is disabled and labelled unavailable until Phase 06.
- [x] Rendering, filters, refreshes, and toggles do not trigger business writes or inference. Static-serving tests and live workflows provide UI evidence.
- [x] Synthetic presets fill editable fields only; a request is written only after explicit submission.

## Verification and evidence

The [architecture update build entry](../build-log.md#2026-10-29---phase-04-single-process-html-ui-update) and [structured-context follow-up](../build-log.md#2026-10-29---phase-04-structured-request-context) record commands/results, static-serving and API tests, live browser workflows against isolated migrated/seeded databases, session/retry/stale behavior, no-write checks, context snapshots, and limits. ADR 0010 records the additive data contract. The earlier Streamlit build evidence remains historical. The root `ui/` files are source-tree assets and must be included in the Phase 05 runtime image.

Stop after Phase 04. Phase 05 begins only with separate user authorization.
