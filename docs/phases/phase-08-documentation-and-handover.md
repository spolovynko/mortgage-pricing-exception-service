# Phase 08 - Documentation, demonstration, and handover

- Status: Not started.
- Milestone: Core handover; optional AI follows in Phase 09.
- Prerequisite: prior phase outcomes and unresolved issues inspected.
- Primary ADR to create: `docs/adr/0008-documentation-and-handover.md`.
- Handoff to create: `docs/handoffs/phase-08.md`.

## Objective

Make the solution easy for an evaluator to run, test, demonstrate, and continue. Verify the final claims against a fresh setup and document the actual remaining limitations.

## Read first

[AGENTS.md](../../AGENTS.md), [README](../../README.md), [requirements](../requirements.md), [architecture](../architecture.md), [implementation plan](../implementation-plan.md), current status, the Phase 07 handoff, ADRs, the build log, and the actual evaluation report if created.

## Implementation tasks

- [ ] Replace scaffold-only README statements with accurate implemented status while retaining visible limitations.
- [ ] Document core Compose startup, application/API URLs, image/dependency downloads, cached-image expectations, and actual tested platforms/resources. Label AI-profile startup as deferred to Phase 09.
- [ ] Document seed identities/applications, demo identity limitations, and exact run/test/exploration commands.
- [ ] Create docs/demo.md with a realistic create/approve/retrieve flow, decline/history flow, retry, revision, and AI on/off/unavailable scenarios.
- [ ] Add configuration reference and troubleshooting for Docker availability, ports, persistent storage, failed downloads, model readiness, and insufficient runtime resources.
- [ ] Explain normal shutdown/restart and separately document any explicitly destructive reset. Never erase existing evaluator data automatically.
- [ ] Create docs/production-notes.md describing real authentication/authorisation, audit protection/retention, backups, privacy controls, operational monitoring, policy/integration needs, and database migration/concurrency considerations.
- [ ] Ensure requirements, architecture, ADRs, and actual behaviour agree; retain explicit assumptions and superseded decision history.
- [ ] Summarise useful agentic development contributions, human review, corrections, actual AI evaluation results, and remaining model risks.
- [ ] Calculate actual recorded work time from the build log. State missing time honestly rather than estimating undocumented work as fact.
- [ ] Verify the source repository excludes credentials, .env files, live databases, downloaded weights, and irrelevant temporary artefacts.
- [ ] Prepare a concise walkthrough explaining design choices and next improvements. Sharing/pushing the repository remains subject to the user's instructions.

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

- [ ] The README alone supports a fresh evaluator-like setup and the documented core workflow.
- [ ] Startup/test commands and important demonstration scenarios have been executed and recorded.
- [ ] Bonus UI/AI capabilities and their verification limits are accurately labelled.
- [ ] Production limitations, assumptions, decision rationale, continuation guidance, and actual time are present.
- [ ] The repository is suitable to share under the user's direction without runtime artefacts or credentials.
- [ ] Final project status lists any remaining unmet criteria; no unfinished requirement is hidden by a Complete label.

## Decision record and final handoff

Use the phase ADR to explain core handover/release-readiness decisions based on actual evidence. Register it in the ADR index. Update this guide, [build log](../build-log.md), [AI usage](../ai-usage.md), and [project status](../project-status.md). Write the core handoff with supported commands, verified functionality, open issues, and optional Phase 09 as the next separately authorised phase. Phase 09 must refresh affected handover guidance after AI implementation.

Stop after the handover. Do not publish, push, deploy, or create a pull request solely because the documentation is complete.
