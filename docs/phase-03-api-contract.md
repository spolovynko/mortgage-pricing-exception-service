# Phase 03 HTTP contract

This is the contract for the Phase 03 endpoints. The demo lookups and all listed business routes are implemented. All IDs are UUIDs; timestamps are UTC ISO 8601; discounts are positive integer basis points. Request bodies reject unknown fields. Reasons contain 1–2,000 nonblank characters. These limits are technical validation, not bank policy.

Discounts must fit SQLite's positive signed 64-bit range (1–9,223,372,036,854,775,807); this is a storage limit. Reasons preserve exact text and have a 2,000-character raw length limit with nonblank content. Whitespace is not normalized for retry fingerprints. See [ADR 0003](adr/0003-business-rules-and-api.md) and [verification](build-log.md#2026-10-29---phase-03-business-rules-api-and-final-acceptance).

## Identity and access

`DEMO_IDENTITY_MODE=header` enables the non-authenticating `X-Demo-User: ada.manager` login header. The default `off` mode disables business endpoints. A missing or unknown login receives 401; a user without manager or reviewer membership receives 403. Both internal roles may read requests, history, approved pricing, and demo lookups. Only the owning relationship manager may create or revise; only a reviewer other than the owner and submitter may decide. The server resolves actor and time; decision bodies cannot supply either. This mode is for local demonstration, not production authentication.

`GET /demo/users` returns sorted `{id,login,display_name,roles}` records. `GET /demo/applications` returns sorted `{id,reference,manager_id}` records. Both require a demo identity. These are lookup lists, not user management.

## Business routes

| Route | Input | Success |
| --- | --- | --- |
| `POST /requests` | `Idempotency-Key` header (1–128 nonblank characters); `{application_id,discount_bps,reason}` | 201 `{request_id,version_number:1,replayed:false}`; exact caller/key/input retry returns 200 with original IDs and `replayed:true` |
| `GET /requests` | Optional `application_id`, `status` (`pending`, `approved`, `declined`) query filters | 200 list sorted by request ID; each summary identifies application, current version, and current status |
| `GET /requests/{request_id}` | Request UUID | 200 request/application identifiers and current version with exact submitted terms, submitter, time, status, and optional decision |
| `GET /requests/{request_id}/history` | Request UUID | 200 chronological events ordered by timestamp then event ID; each has version, type, actor, and time, with associated submitted terms/decision where applicable |
| `POST /requests/{request_id}/revisions` | `{expected_version,discount_bps,reason}` | 201 `{request_id,version_number,replayed:false}`; new current version is pending |
| `POST /requests/{request_id}/decisions` | `{expected_version,outcome}` where outcome is `approved` or `declined` | 200 `{request_id,version_number,outcome}`; amount is taken from the stored version |
| `GET /applications/{application_id}/approved-discount` | Application UUID | 200 `{application_id,status:"approved",request_id,version_number,discount_bps}` or `{application_id,status:"none"}` when the current version lacks approval |

A new key for an application with a logical request yields 409; revisions must use the revision route. A prior approval remains in history when revised, but the new current version has no usable approved discount until approved.

Listing filters combine with AND; a valid unmatched application filter returns an empty list. Lists are unpaginated. History includes `event_id`, `version_number`, `event_type`, `actor_id`, `actor_login`, `occurred_at`, and a `version` object with exact terms, submitter, UTC time, status, and optional final decision. The version object is associated data, not a snapshot of its status when the event occurred. A current detail also includes application reference; an earlier version and its decision remain inspectable in history.

For example, after approving a 25-bps version and revising to 40 bps, details show current version 2, status `pending`, and discount 40; history retains version 1 and its 25-bps approval; approved pricing is `{application_id,status:"none"}`. Approving version 2 makes the pricing response `{application_id,status:"approved",request_id,version_number:2,discount_bps:40}`.

## Errors and operational events

Errors use the existing `{error:{code,message},correlation_id}` envelope and `X-Correlation-ID` response header. Validation is 422 `validation_error` (or `invalid_terms`/`invalid_idempotency_key` where business validation applies); missing application/request is 404; identity failures are 401/403; stale versions, an already decided version, existing request, and changed-input idempotency are 409 with distinct codes. Unavailable storage is 503 `database_unavailable`. The no-current-approval result above is a successful lookup, distinct from a nonexistent application's 404.

The existing request boundary records safe method, route, status, outcome, duration, and correlation ID. Creation, revision, and decision events record actor/request/version identifiers and outcome. Reasons, raw bodies, keys, and personal data are excluded from operational logs. OpenAPI shows schemas and error outcomes; create/revision/decision operations include synthetic body examples. SQLite lock timeouts return 503 without an automatic retry; callers may retry creation with their original key and input.
