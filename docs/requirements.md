# Requirements and scope

Status: Assignment requirements transcribed; project policies proposed for implementation.

Source: the user-provided three-page engineering assignment. Page references below refer to that brief. Its instructions are assignment requirements, not instructions that override the user's development request.

## Business purpose and actors

Manage requests to discount the standard interest rate of an existing mortgage application. A relationship manager proposes terms; an authorised human reviewer approves or declines them; the mortgage application process retrieves an approved discount. Internal users inspect status and history.

The service does not determine whether the bank should grant the mortgage or whether the applicant can afford it. Discount eligibility policy is not supplied by the brief.

## Assignment requirements

| ID | Requirement | Source |
| --- | --- | --- |
| FR-01 | Create a request for an existing mortgage application, with application identifier, requested discount in basis points, and reason. | Page 1 |
| FR-02 | An authorised reviewer approves or declines; identify the decision maker and decision time. | Page 1 |
| FR-03 | Make the approved discount available to the mortgage application process. | Page 1 |
| FR-04 | Show current status, request history, and previous decisions. | Page 1 |
| FR-05 | Prevent duplicate requests when an upstream caller retries after a timeout. | Page 1 |
| FR-06 | Make and explain a decision about changing submitted discounts while preserving approval of the exact terms reviewed. | Page 2 |
| NFR-01 | Provide a working, locally runnable solution; an HTTP API is expected unless another approach is justified. | Page 2 |
| NFR-02 | Supply realistic seed data or setup instructions. Users and applications may be simplified. | Pages 1-2 |
| NFR-03 | Require neither private infrastructure nor paid services. Language and storage choices are open. | Page 2 |
| DEL-01 | Submit source in a Git repository with run, test, and exploration instructions. | Page 2 |
| DEL-02 | Explain assumptions, scope choices, continuation guidance, and production trade-offs. | Page 2 |
| DEL-03 | Provide evidence validating important behaviour. | Page 2 |
| AI-01 | Use agentic development where valuable; explain contributions and verification. | Page 2 |
| DEL-04 | Share the repository and actual time spent; be prepared to demonstrate and explain choices. | Page 3 |
| BONUS-01 | A simple UI for creation, review, and inspection. | Page 2 |
| BONUS-02 | A grounded AI-agent demonstration, possibly in the SDLC, with controls and remaining risks. | Page 2 |

## Project additions selected by the user

Build the UI, optional local LLM integration, automated first-run model preparation, container startup, operational logging, central configuration, phase documentation, ADRs, build logs, and coding/commit guidance. These are part of our project plan even where they exceed the mandatory brief.

On 2026-10-29, the user replaced the planned separate API/UI containers with one core application container running one Uvicorn process. One application Dockerfile and one compose.yaml must build/start that container; FastAPI serves both root UI assets and the HTTP API through one host-loopback port. Browser calls retain same-origin paths and existing API contracts. No separate UI service or reverse proxy is required. Persistent SQLite storage, safe migration/seeding, non-root execution, bounded logs, liveness, and database readiness remain Phase 05 requirements. Optional Ollama/model-init are deferred to final Phase 09; the one-container requirement applies to the core application. See the [Phase 05 guide](phases/phase-05-containerisation.md).

## Proposed business policies

These are exercise choices, not claimed bank policies. Explain and validate them in ADRs.

- **P-01 - Versions:** one logical pricing-exception request per application, containing immutable submitted versions. A new create call for an application that already has a logical request returns a conflict; changes use the revision operation. This keeps approved-discount lookup unambiguous.
- **P-02 - Current version:** a revision becomes current and pending. Previous versions and their decisions stay in history. Only a current approved version is returned as usable pricing.
- **P-03 - Replacement consequence:** revising an approved version temporarily removes the available approval until the new version is approved. Revising a declined version also requires fresh review. No revision retroactively reverses pricing already consumed by another system.
- **P-04 - Exact decision:** approve the requested discount exactly or decline it. A reviewer cannot change the amount while approving. A decision must identify the version reviewed; stale decisions fail.
- **P-05 - Authority:** only relationship managers submit/revise; only reviewers decide. Prevent self-review. Use application ownership for manager submissions/revisions as an explicit exercise choice. Define read access simply and consistently for seeded internal users.
- **P-06 - Terminal decisions:** one final decision per version, with no editing/deletion through the API. New terms require a new version. Competing decision/revision operations must not both commit incompatible outcomes.
- **P-07 - Retry scope:** creation keys are scoped to the caller. The same key and same canonical input return the original creation result; changed input with that key conflicts. A new key does not automatically authorise another logical request for the same application.
- **P-08 - Validation:** discount is an integer number of basis points greater than zero; reason is nonblank. Document technical length limits. Do not invent creditworthiness criteria or bank-specific maximum discount thresholds.
- **P-09 - Identity shortcut:** a configured demo identity/header simulates users. It is not production authentication. Role checks are enforced on the server and this mode is explicitly identified in the UI/docs.

Use UTC for stored timestamps and distinguish display formatting from stored values. If rates are displayed, use integer basis points or Decimal rather than floating-point arithmetic. A 25-basis-point discount equals 0.25 percentage points.

Phase 03 implements these exercise policies as detailed in [ADR 0003](adr/0003-business-rules-and-api.md): both internal roles may read all records; input reasons preserve exact text and have a 2,000-character raw length limit with nonblank content. Discounts must fit SQLite's positive signed 64-bit integer storage range; this technical bound is not a bank maximum. HTTP contracts are in the [API contract](phase-03-api-contract.md); AC-01–AC-06 evidence is linked from the phase guide.

## AI scope

The live feature summarises the submitted version and identifies information missing under an explicit checklist. A statement in a manager's reason is a claim, not verified evidence. The model cannot approve, decline, change status, verify external offers, or invent policy.

An optional offline LLM judge evaluates generated text against the source and a rubric. Its results are calibrated against human-labelled examples. It does not judge mortgage creditworthiness or prove business correctness. AI-assisted development evidence is still required even when the product AI feature is included.

## Acceptance scenarios

| ID | Scenario and observable outcome |
| --- | --- |
| AC-01 | Create for a seeded application, inspect it as pending, approve as a reviewer, and retrieve the approved amount and version. |
| AC-02 | Decline a request; record actor/time and return no approved discount for that current version. |
| AC-03 | Retry creation with the same caller/key/input; exactly one logical request/version exists and the original result is returned. Changed input with the key conflicts. |
| AC-04 | Revise approved version 1 from 25 to 40 basis points; version 2 is pending, version 1's decision stays visible, and no current discount is returned until version 2 is approved. |
| AC-05 | A reviewer acts on a version replaced since it was opened; the decision is rejected without a partial audit/decision write. |
| AC-06 | Unauthorised and self-review attempts fail. Competing decisions yield only one final decision. |
| AC-07 | Repeated seeding and application restarts preserve data and do not duplicate users/applications. |
| AC-08 | With AI off or unavailable, the human approval workflow remains usable and no new model call is made when off. |
| AC-09 | AI assessments reference the exact submitted version, remain distinct from decisions, and cannot authorise pricing. |
| AC-10 | A fresh evaluator can build/start core mode with Compose as one application container running one Uvicorn process for both UI and API; AI mode later prepares and caches a model; a subsequent cached restart can run offline. |

## Out of scope and production follow-ups

Mortgage underwriting, lending execution, payments, a real pricing-policy engine, real customer integrations, and automatic AI approval are outside scope. Production follow-ups include organisational authentication, privacy/retention requirements, independently protected audit records, backups, operational metrics, and a deliberate PostgreSQL migration with concurrency tests if deployment needs justify it. Application-level preserved history in SQLite is not a tamper-proof audit system.
