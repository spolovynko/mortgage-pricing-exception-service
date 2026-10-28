# Phase 03 - Business rules and API

- Status: Not started.
- Milestone: MVP1.
- Prerequisite: Phase 02 storage and seed data verified.
- Primary ADR to create: `docs/adr/0003-business-rules-and-api.md`.
- Handoff to create: `docs/handoffs/phase-03.md`.

## Objective

Deliver the complete human approval workflow through an HTTP API, including immutable submitted versions, safe retries, and atomic decisions.

## Read first

[AGENTS.md](../../AGENTS.md), [requirements](../requirements.md), [architecture](../architecture.md), [engineering guidelines](../python-engineering-guidelines.md), current status, the Phase 02 handoff, and schema/foundation ADRs.

## Proposed HTTP operations

These routes are planning defaults. Settle exact request/response/error contracts in this phase and keep examples, OpenAPI, and tests consistent.

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

- [ ] Implement focused backend use cases for creation, revision, review, history, and approved-discount selection.
- [ ] Validate application existence/ownership, role permissions, positive integer discount, and nonblank bounded reason.
- [ ] Resolve acting identity through the configured demo mechanism; never trust an actor/timestamp supplied in the decision body.
- [ ] Enforce no self-review and define consistent read permissions for internal users.
- [ ] Preserve submitted input. Revisions create a new pending version and change the current-version reference atomically.
- [ ] Require the reviewed version in decision input; accept approve or decline only, not a replacement amount.
- [ ] Enforce one final decision per version using database-backed concurrency control.
- [ ] Implement atomic caller-scoped idempotency: matching retries replay the original creation result, changed input conflicts, and competing first attempts cannot create duplicates.
- [ ] Ensure a second create for the same application with a new key follows the documented logical-request conflict policy.
- [ ] Save history with each associated business change and return it in a deterministic order.
- [ ] Add clear error codes/messages, operational events, and realistic OpenAPI examples.
- [ ] Expose any seed-user/application lookup needed to make the later UI usable, without introducing a full user-management system.

## Verification

Test all AC-01 through AC-06 scenarios in requirements.md. Include invalid/missing applications, role failures, self-review, duplicate payloads, conflicting payloads, retries after a decision/revision, terminal decisions, and current-only approved pricing.

Use separate connections to a temporary file-backed SQLite database for competing creation and decision tests. Test a revision racing a decision: the final state must be coherent and no decision may authorise new terms accidentally. A decision that commits before a revision can legitimately remain in history while the new version is pending; define and test that ordering rather than assuming every simultaneous pair must fail.

Run the complete create/approve/retrieve and create/decline/history scenarios manually through the API documentation or an HTTP client. Add tests as features are implemented, not after the entire API is written.

## Acceptance criteria

- [ ] The full approval and decline workflows work against persistent seed data.
- [ ] Approved-discount retrieval references the correct request/version/amount.
- [ ] Revision, retry, permission, self-review, and competing-update guarantees are backed by passing tests.
- [ ] Failed business operations leave no partial decisions/history or accidental approved terms.
- [ ] API contracts and errors are understandable and reflected in OpenAPI examples.
- [ ] The service works with no UI, model, GPU, paid API, or private infrastructure.

## Decision record and handover

Explain the HTTP contracts, identity/read-access assumptions, idempotency replay semantics, version policy, and actual concurrency mechanism. Record tests and manual outcomes. Update this guide, requirements/architecture if details changed, the ADR index, [build log](../build-log.md), [AI usage](../ai-usage.md), and [project status](../project-status.md). Create the phase handoff.

Stop after Phase 03. MVP1 is complete only if the actual acceptance evidence supports it.
