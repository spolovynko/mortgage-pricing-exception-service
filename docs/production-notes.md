# Production release requirements

The repository is a reviewable exercise release with production-style container hygiene. It is not approved for real lending deployment. The Compose configuration deliberately opts into fictional identities and seed data for reviewers; `APP_ENV=production` configures the process and does not turn demo identity headers into authentication.

## Implemented release controls

- One non-root application container and one Uvicorn process serve UI/API. Root filesystem is read-only; only named database storage and a private temporary filesystem are writable. Linux capabilities are dropped, privilege escalation disabled, logs bounded, and the host port bound to loopback.
- Bare-image defaults disable demo identities and automatic demo seeding. Compose explicitly enables both for the exercise.
- Locked Python dependencies, pinned container bases/runtime, additive migrations, health/readiness checks, server-side roles/ownership, exact-version decisions, transaction-bound history, and idempotent retry handling are implemented.
- Optional local model startup does not block the human workflow. AI advice is separately persisted, explicitly requested, bounded, checked, and followed by an independent human decision. Installed model digest and contract/settings versions participate in assessment cache identity.
- Operational logs omit prompt, reason and generated-text payloads. Saved reports retain model/digest, references, timing, and state. Application-preserved history is not protection against an administrator replacing the SQLite file.

## Go-live gates that are still open

1. **Identity:** replace caller-selected demo headers with organizational authentication, protected sessions/tokens, approved role mapping, least privilege, expiry, and access monitoring. Do not expose the Compose demo directly to a public network.
2. **Business policy:** have accountable owners define real pricing rules, evidence, discount authority, escalation, and system integrations. Current checks are exercise constraints. No external competitor offer is verified.
3. **AI acceptance:** obtain human-reviewed evaluation labels and independently review rationale faithfulness, errors, bias, and usefulness. Candidate-label agreement is not established accuracy, calibration, or legal compliance. Keep human decision authority and an explicit ability to bypass AI. Legal/compliance owners must assess applicable AI/data-protection obligations for the intended use.
4. **Data operations:** define privacy/retention controls, encrypted off-host backups, recovery objectives, a tested restore procedure, independent audit protection, capacity monitoring, and incident ownership. A Docker volume is persistence, not a backup.
5. **Deployment security:** review network/TLS termination, trusted proxies, secrets management, dependency/image scanning, patch ownership, resource limits, rollout/rollback procedures, and load/concurrency behavior. Hosted CI and an independent second-machine deployment require their own recorded evidence.
6. **Redistribution:** choose and approve the repository's license and notices; no repository license grant is supplied. Check the selected model/runtime licenses and redistribution terms separately.

## Supported deployment boundary

The implemented storage is one file-backed SQLite database with one app process. SQLite serializes writes and a bounded busy timeout returns errors rather than promising unlimited throughput. PostgreSQL URLs are recognized by settings but no PostgreSQL persistence/deployment support is implemented. Multiple application replicas, managed-database migration, and a production migration/backup operator workflow require separate design and checks.

Container startup migrates storage and seeds only when `SEED_DEMO_DATA=true`. For a real rollout, use a controlled, backed-up migration procedure; do not use automatic demo seeding. Stop traffic before maintenance, keep deployment artifacts/locks, verify `/ready`, perform a smoke check, and preserve decision history. See [installation](installation.md), [operations](troubleshooting.md), [ADR 0011](adr/0011-local-llm-integration.md), and the current [release evidence](build-log.md).
