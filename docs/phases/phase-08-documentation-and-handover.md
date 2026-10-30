# Phase 08 - Documentation, demonstration, and handover

- Status: Implemented and assistant-verified; formal human acceptance is not recorded.
- Milestone: Core handover; optional AI follows in Phase 09.
- Prerequisite: prior phase outcomes and unresolved issues inspected.
- Primary ADR to create: `docs/adr/0008-documentation-and-handover.md`.
- Handoff to create: `docs/handoffs/phase-08.md`.

## Objective

Make the solution easy for an evaluator to run, test, demonstrate, and continue. Verify the final claims against a fresh setup and document the actual remaining limitations.

## Read first

[AGENTS.md](../../AGENTS.md), [README](../../README.md), [requirements](../requirements.md), [architecture](../architecture.md), [implementation plan](../implementation-plan.md), current status, the Phase 07 handoff, ADRs, the build log, and the actual evaluation report if created.

## Implementation tasks

- [x] Replace scaffold-only README statements with accurate implemented status while retaining visible limitations.
- [x] Document core Compose startup, application/API URLs, image/dependency downloads, cached-image expectations, and observed platform. Label AI/profile/model setup as deferred to Phase 09; do not claim unmeasured minimum resources.
- [x] Document seed identities/applications, demo identity limitations, and setup/test/exploration commands.
- [x] Create `docs/demo.md` for create/approve/retrieve, retry, revision, decline/history, and human-only operation. AI-on controls are absent; AI behavior is deferred to Phase 09.
- [x] Add configuration reference and troubleshooting for Docker, ports, persistence, failed downloads, model readiness, and resource constraints.
- [x] Explain normal shutdown/restart and separately identify destructive volume removal. Startup never resets evaluator data.
- [x] Create `docs/production-notes.md` for authentication/authorization, audit protection/retention, backups, privacy, monitoring, policy/integrations, and database migration/concurrency.
- [x] Reconcile documented behavior with requirements, architecture, ADRs, and implementation while preserving historical decisions and assumptions.
- [x] Record assistant/tool contributions, user-directed corrections, lack of formal human acceptance, absence of Phase 09 model evaluation, and remaining model risks in the AI-use log and handoff.
- [x] Check work-time records; active time was not recorded and is not estimated.
- [x] Check tracked repository paths and ignore rules for credentials, `.env`, live databases, model weights, and temporary artefacts.
- [x] Prepare the visual walkthrough and continuation guidance. No publish, push, deployment, or PR was made.

## Fresh-setup verification

Use an isolated fresh checkout/copy and synthetic storage so the evaluator-like setup does not benefit from hidden local configuration or destroy ongoing work. Follow only the README. Confirm core UI/API startup, seed scenario, tests, cached-image restart, and the human workflow without AI. Distinguish same-host fresh setup from actual second-machine verification; AI setup and model-cache offline checks are deferred to Phase 09.

Check links and command examples. Inspect logs from both ordinary operation and an intentional bounded failure. A local Compose demo is not evidence of production readiness; report the demonstrated scope.

## Demonstration sequence

1. Start the core application and identify its seeded actors/applications.
2. Submit and approve a request; retrieve the exact approved amount/version.
3. Decline another request and inspect its history.
4. Retry a submission and show that no duplicate is created.
5. Revise approved terms and show that fresh review is required.
6. Show that AI generation is deferred and complete a human decision without a model.
7. Show relevant core tests, an ADR, reproducibility evidence, and production follow-ups.

If live AI or judge calibration remains unverified, demonstrate the verified subset and state that limitation instead of silently displaying fixtures as live output.

## Acceptance criteria

- [x] The README supports a fresh same-host evaluator-like setup and documented core workflow; second-machine setup is unverified.
- [x] Startup/test commands and create/retry/approve/retrieve/revise/decline/history scenarios were executed and recorded.
- [x] Bonus UI/AI capabilities and verification limits are accurately labelled; no AI control exists in the current UI.
- [x] Production limitations, assumptions, decision rationale, continuation guidance, and missing work-time record are present.
- [x] Tracked source excludes `.env`, database files, model weights, and temporary artefacts; ignore rules protect local runtime data.
- [x] Project status lists remaining limits; formal human acceptance, hosted CI, second-machine/offline-first-build checks, and Phase 09 AI evaluation remain outstanding.

## Decision record and final handoff

Use the phase ADR to explain core handover/release-readiness decisions based on actual evidence. Register it in the ADR index. Update this guide, [build log](../build-log.md), [AI usage](../ai-usage.md), and [project status](../project-status.md). Write the core handoff with supported commands, verified functionality, open issues, and optional Phase 09 as the next separately authorised phase. Phase 09 must refresh affected handover guidance after AI implementation.

Stop after the handover. Do not publish, push, deploy, or create a pull request solely because the documentation is complete.
