# ADR 0003 - Business rules and HTTP API

- Date: 2026-10-29; Phase 03 / MVP1.
- Status: Implemented. Contributor: Codex assistant; human acceptance and active work time are not recorded.
- Requirements: FR-01–FR-06, exercise policies P-01–P-09, AC-01–AC-06 in [requirements](../requirements.md).

## Context and options

Phase 02 already owns atomic create/revise/decide operations, immutable rows, and SQLite writer serialization. Phase 03 needs transport contracts and read queries. Options were to reuse these operations or duplicate business rules in new service/repository layers; to use the configured demo login header or introduce full authentication; and to return a successful no-approval result or conflate it with a missing application.

## Decision and rationale

Use small FastAPI route modules with explicit session ownership, Pydantic transport validation, the existing settings/logging/error envelope, and the Phase 02 operations. No duplicate transaction framework or schema migration is needed. [The API contract](../phase-03-api-contract.md) defines the routes, response fields, statuses, and bounds.

`DEMO_IDENTITY_MODE=header` resolves `X-Demo-User` against stored logins. Default `off` returns 503 for business access; missing/unknown logins return 401 and missing roles return 403. Both internal roles can read all internal requests and lookups. Manager writes require ownership; reviews require reviewer membership and exclude the owner/submitter. This is simulated identity, not production authentication.

Creation returns 201, or 200 on exact caller/key/input replay with the original version-1 reference and `replayed:true`, including after subsequent decisions/revisions. Fingerprints preserve exact reason text; changed input or a new-key second logical request conflicts. Revisions become current and pending. Decisions identify the expected current version and cannot supply an amount, actor, or timestamp. Missing resources return 404, expected business conflicts 409, invalid input 422, unavailable/locked storage 503, and unexpected failures retain the generic 500 boundary. There is no automatic lock retry.

Only a decision approving the current version permits pricing retrieval. Existing applications without such approval return 200 `{application_id,status:"none"}`; missing applications return 404. History is ordered by UTC time then event UUID; embedded version/decision data describes the immutable terms and their associated final decision, not the state as of each event's time. Lists are unpaginated for this small exercise.

Discounts use positive integer basis points up to SQLite's signed 64-bit maximum; reasons preserve exact text, require nonblank content, and have a 2,000-character raw limit. This storage bound is technical, not a bank discount threshold. Input models reject extra fields. Explicit common OpenAPI error schemas match runtime envelopes.

## Consequences, verification, and revisit conditions

The first-statement no-op UPDATE in the existing operations obtains SQLite's writer lock before mutable reads; database uniqueness and transactional history remain authoritative. A decision committing before revision remains on its old version; revision committing first makes the old decision stale. Pending terms never inherit an old approval.

Assistant-observed tests and actual TCP HTTP workflows are recorded in the [Phase 03 build entry](../build-log.md#2026-10-29---phase-03-business-rules-api-and-final-acceptance). This supports MVP1 on the tested Windows/Python environment, without human acceptance, production authentication, cross-platform or multi-instance guarantees. Revisit read access, authentication, pagination, retry policy, and locking for a production workload or another database backend. ADRs [0001](0001-foundation-config-logging.md) and [0002](0002-database-and-seed-data.md) remain in force; none is superseded.
