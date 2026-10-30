# Production considerations

This service is a demonstration, not a production lending system. Its policies are exercise defaults. Before any real use, an organisation would need to design, approve, implement, and independently review the following controls.

## Identity and authorization

Replace `DEMO_IDENTITY_MODE=header` and caller-selected demo identities with the organisation’s identity provider, protected sessions or tokens, and a defined role and ownership model. Enforce authorization server-side for every read and write, including reviewer separation, least privilege, service-to-service access, and administrative operations. Add security review, session expiry, credential rotation, and access monitoring. Never treat the demo identity header as proof of a user’s identity.

## Policy and integrations

Define approved pricing policy, eligibility criteria, discount bounds, evidence requirements, escalation paths, and exception authorities with accountable business owners. The current validation limits are technical exercise constraints, not bank policy. Integrations with loan origination, customer, pricing, identity, and document systems need explicit ownership, data contracts, failure handling, idempotency, reconciliation, and access controls. No external competitor offer is verified by this application.

## Audit, privacy, and retention

The application preserves version and decision history and rejects ordinary application-level edits to immutable records. That does not make a local SQLite file tamper-proof: an operator with database or host access can alter or replace it. Define a lawful data inventory, purpose limitation, minimization, retention/deletion schedule, access review, and incident process. Keep borrower identifiers and unnecessary personal data out of reasons and logs. Protect audit evidence independently from application administrators, for example with access-separated append-only export or a managed audit service, and test its integrity and retrieval.

## Backups and recovery

Define encrypted, access-controlled backups, retention, recovery-point and recovery-time objectives, off-host storage, key ownership, and restore drills. Monitor backup success and test restored copies against integrity and application-level checks. A named Compose volume is persistence on one Docker host; it is not a backup. `docker compose down --volumes` deletes that demo volume.

## Monitoring and operations

The current JSON logs and `/health` and `/ready` endpoints support local diagnostics. Production operations need centralized protected logs, metrics and alerts for availability, request failures, database lock/contention, latency, capacity, migration status, backup health, and security events. Establish on-call ownership, incident response, patching, vulnerability scanning, and an operational change process. Review log retention and access because even minimized logs can contain operational identifiers.

## Database migrations and concurrency

The current container startup applies Alembic migrations and seeds a single SQLite database before serving. SQLite serializes writes and has a bounded busy timeout; lock timeouts return an error and are not automatically retried. This single-container design is not a multi-instance concurrency guarantee. Before scaling or adopting production workloads, choose and test a managed database and explicit migration process, assess transaction and isolation behavior, add concurrency/load tests, define safe rollout and rollback procedures, and confirm that audit and idempotency guarantees survive migration. PostgreSQL URLs are accepted by settings, but the container startup contract requires writable file-backed SQLite; PostgreSQL deployment is not established by that setting alone.

## AI and decision controls

Optional local LLM integration, model lifecycle, evaluation, and judge calibration are deferred to Phase 09. No AI control or generated assessment is present in the current UI or core Compose workflow. Any future assessment must remain distinct from a human decision, reference the exact request version, disclose uncertainty and evidence limits, and never approve, decline, or authorize pricing on its own.
