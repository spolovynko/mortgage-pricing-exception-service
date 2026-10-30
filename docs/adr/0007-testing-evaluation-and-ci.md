# ADR 0007: Core integration testing and CI

- Date: 2026-10-30. Phase: 07, Core validation. Status: Implemented; human acceptance not recorded.
- Contributor: Codex. Related requirements: AC-01–07 and core portion of AC-10.
- Context: Business and persistence guarantees already had focused tests. UI retry/stale flows and repeatable container persistence needed direct evidence; routine automation must work without model services.
- Decision: Keep deterministic Python/Node checks in ordinary CI using locked dependencies. Keep Docker smoke separate. Use uniquely named Compose projects and synthetic seed records; preserve named volumes so restart persistence can be observed. Cover create, reviewer approval, history and same-key replay across cached-image recreation.
- Alternatives: Put Docker builds in every CI run (more resource intensive); remove smoke volumes after execution (loses restart evidence); duplicate existing backend tests (adds little coverage). Rejected for cost, evidence quality and redundancy.
- Consequences: The smoke runner explicitly leaves its unique volume after bringing down its service/network. CI tests require package installation access, while test execution needs no external model, paid API or private service. Hosted CI is configured but not observed.
- Limits/revisit: No AI quality, model, judge, production authentication, second-host, offline first-build or exhaustive accessibility claim. AI criteria remain deferred to Phase 09. Revisit CI triggers/runners after hosted execution.
- Verification: Exact commands and observations are in the [Phase 07 build entry](../build-log.md#2026-10-30---phase-07-core-integration-testing-and-ci).
