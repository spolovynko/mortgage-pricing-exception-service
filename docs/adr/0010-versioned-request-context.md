# ADR 0010: Preserve structured pricing context by request version

- Date: 2026-10-29.
- Phase/milestone: Phase 04 follow-up, MVP2.
- Status: Implemented; human acceptance is not recorded.
- Contributor: User requested structured mortgage and request details to support future AI analysis; Codex implemented.
- Related requirements: P-01, P-04, P-08; Phase 04 guide.
- Verification: [Phase 04 structured-context build entry](../build-log.md#2026-10-29---phase-04-structured-request-context).

## Context

The original API stored application reference, requested discount, and a free-text reason. Text alone makes requests harder to compare consistently. Future assistance needs typed attributes without drifting into borrower underwriting or unverified bank policy.

## Decision

Keep the free-text reason and add an optional, strictly validated `context` object to create and revision bodies. It captures mortgage purpose, rate type, loan/property value and currency, term, standard rate, reason category, and an optional manager-reported competitor rate/expiry. These values are a snapshot on each immutable request version. The API returns the snapshot in current details and history, and creation idempotency fingerprints include it. The UI requires structured application fields for new versions, calculates LTV for display, offers a collapsible competitor section, and can prefill clearly synthetic examples; prefill never submits.

Persist the context as JSON in `request_versions`. The Pydantic schema controls keys, types, enums, and bounds. This keeps one versioned snapshot rather than duplicating fields on the mutable application record. The migration is additive and nullable so old versions and clients remain compatible. Competitor data is labelled unverified. Do not collect borrower-identifying data or use the fields as creditworthiness criteria.

## Alternatives

- Keep reason text only: simpler, but makes comparisons less consistent.
- Append optional values to reason: preserves the old contract, but turns typed values back into prose.
- Add every feature as a database column: easier SQL filtering, but more schema churn for this small demo. Revisit if analytics need indexed filtering.

## Consequences and limits

Old request versions return `context: null`; new UI submissions require the structured fields, while the API accepts omitted context for compatibility. Revisions record a new context snapshot and do not rewrite the reviewed version. The future AI can receive structured values and narrative but no inference or pattern-accuracy claim is made here. Future-phase pattern analysis may justify normalized/indexed columns and a governed evaluation dataset.
