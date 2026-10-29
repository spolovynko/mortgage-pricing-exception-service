# Phase 03 - Business rules and API

- Status: Complete.
- Milestone: MVP1.
- Prerequisite: Phase 02 storage and seed data verified.
- Primary ADR: [0003](../adr/0003-business-rules-and-api.md), Implemented; human acceptance not recorded.
- Handoff: [Phase 03](../handoffs/phase-03.md).

## Objective

Deliver the complete human approval workflow through an HTTP API, including immutable submitted versions, safe retries, and atomic decisions.

## Read first

[AGENTS.md](../../AGENTS.md), [requirements](../requirements.md), [architecture](../architecture.md), [engineering guidelines](../python-engineering-guidelines.md), current status, the Phase 02 handoff, and schema/foundation ADRs.

## Proposed HTTP operations

These routes are implemented. Exact request/response/error contracts are in the [API contract](../phase-03-api-contract.md) and OpenAPI.

| Operation | Proposed route |
| --- | --- |
| Create logical request and first submitted version | `POST /requests` |
| Filter/list requests | `GET /requests` |
| Inspect current details and version references | `GET /requests/{request_id}` |
| Inspect ordered history | `GET /requests/{request_id}/history` |
| Submit revised terms against an expected current version | `POST /requests/{request_id}/revisions` |
| Decide the exact reviewed version | `POST /requests/{request_id}/decisions` |
| Retrieve current approved pricing | `GET /applications/{application_id}/approved-discount` |

Return a stable machine-readable outcome when no current approval exists, distinguish it from a nonexistent application, and document the chosen HTTP status. Never return a pending amount as approved pricing.

## Implementation tasks

- [x] Implement focused backend use cases for creation, revision, review, history, and approved-discount selection.
- [x] Validate application existence/ownership, role permissions, positive integer discount, and nonblank bounded reason.
- [x] Resolve acting identity through the configured demo mechanism; never trust an actor/timestamp supplied in the decision body.
- [x] Enforce no self-review and define consistent read permissions for internal users.
- [x] Preserve submitted input. Revisions create a new pending version and change the current-version reference atomically.
- [x] Require the reviewed version in decision input; accept approve or decline only, not a replacement amount.
- [x] Enforce one final decision per version using database-backed concurrency control.
- [x] Implement atomic caller-scoped idempotency: matching retries replay the original creation result, changed input conflicts, and competing first attempts cannot create duplicates.
- [x] Ensure a second create for the same application with a new key follows the documented logical-request conflict policy.
- [x] Save history with each associated business change and return it in a deterministic order.
- [x] Add clear error codes/messages, operational events, and realistic OpenAPI examples.
- [x] Expose any seed-user/application lookup needed to make the later UI usable, without introducing a full user-management system.

## Verification

Test all AC-01 through AC-06 scenarios in requirements.md. Include invalid/missing applications, role failures, self-review, duplicate payloads, conflicting payloads, retries after a decision/revision, terminal decisions, and current-only approved pricing.

Use separate connections to a temporary file-backed SQLite database for competing creation and decision tests. Test a revision racing a decision: the final state must be coherent and no decision may authorise new terms accidentally. A decision that commits before a revision can legitimately remain in history while the new version is pending; define and test that ordering rather than assuming every simultaneous pair must fail.

Run the complete create/approve/retrieve and create/decline/history scenarios manually through the API documentation or an HTTP client. Add tests as features are implemented, not after the entire API is written.

## Acceptance criteria

- [x] The full approval and decline workflows work against persistent seed data.
- [x] Approved-discount retrieval references the correct request/version/amount.
- [x] Revision, retry, permission, self-review, and competing-update guarantees are backed by passing tests.
- [x] Failed business operations leave no partial decisions/history or accidental approved terms.
- [x] API contracts and errors are understandable and reflected in OpenAPI examples.
- [x] The service works with no UI, model, GPU, paid API, or private infrastructure.

## Decision record and handover

Explain the HTTP contracts, identity/read-access assumptions, idempotency replay semantics, version policy, and actual concurrency mechanism. Record tests and manual outcomes. Update this guide, requirements/architecture if details changed, the ADR index, [build log](../build-log.md), [AI usage](../ai-usage.md), and [project status](../project-status.md). Create the phase handoff.

## Completion evidence

Implementation, focused tests, the full suite, dependency/static checks, and actual TCP approval/decline/revision workflows support MVP1 completion. The [build log](../build-log.md#2026-10-29---phase-03-business-rules-api-and-final-acceptance) maps AC-01–AC-06 to observed evidence and records exact commands, failures/corrections, and limits. The [ADR](../adr/0003-business-rules-and-api.md) explains contracts and trade-offs; the [handoff](../handoffs/phase-03.md) supplies reproducible setup and next reading. Human acceptance and active work duration are not recorded.

Stop after Phase 03. Phase 04 requires a separate user instruction.
