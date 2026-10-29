# ADR 0004: Minimal Streamlit user interface

- Date: 2026-10-29.
- Phase/milestone: Phase 04, MVP2.
- Status: Superseded by [ADR 0009](0009-single-process-html-ui.md). The original Streamlit implementation was completed; the replacement decision is recorded separately. Human acceptance is not recorded.
- Contributor: Codex, following user-authorized implementation steps.
- Related requirements: BONUS-01, P-09; Phase 04 guide.
- Verification: [Phase 04 build log](../build-log.md#2026-10-29---phase-04-user-interface-and-final-acceptance).

## Context

Evaluators need a minimal way to create, review, inspect, and revise pricing requests without constructing HTTP payloads. The backend already owns identity/role enforcement, business rules, versions, idempotency, decisions, and transactions. The interface must label simulated identity and unavailable AI honestly, and Streamlit reruns must not create side effects.

## Decision

Use a small Streamlit application at the repository-root `ui/app.py` with a focused HTTP client in `ui/client.py`. Provide Requests, Review, and History screens; explicit forms for writes; session-scoped demo identity, assistance preference, and create-intent retry key; and clear backend error/stale-version paths. Send the reviewed version in decisions. Earlier approvals are labelled historical; an unapproved revision suppresses current approved pricing. Disable assessment generation until Phase 06.

## Alternatives considered

- A custom HTML/CSS/JavaScript frontend would add a distinct runtime/build and client API layer for this evaluator-focused demo; retain it as an option if richer interaction or production frontend requirements emerge.
- Embedding views in the backend package would couple presentation to the business/API package and is unnecessary for an HTTP-only boundary. The root source directory remains excluded from the Python wheel; the next shared application image must copy/include it.

## Consequences and revisit conditions

The UI is intentionally compact, Python-based, and uses the existing service configuration and API error/correlation contracts. Client visibility is not authorization: all permissions and decision checks remain server-side. Session state is local to each Streamlit session and demo identity is not authentication. Retry intent persists only for the session; a genuinely new submission gets a new key. Phase 05 must package the root `ui/` source tree with the shared runtime. Reconsider the frontend choice if evaluator needs, accessibility testing, concurrent-user deployment, or production authentication require a different delivery model.

Human review and acceptance are not recorded. No production readiness or human sign-off is implied.
