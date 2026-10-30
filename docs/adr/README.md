# Architecture decision records

ADRs explain a consequential choice, its alternatives, and its trade-offs. Create at least one primary record per phase, plus additional records for distinct decisions that need their own explanation.

Keep each record concise: date, phase/milestone, status and implementation scope, contributor, actual human acceptance (or not recorded), related requirements, context, options, decision and rationale, consequences, rejected alternatives and revisit conditions, production follow-ups, and references/supersession. Link to observed verification evidence and its limits rather than copying test logs. Distinguish assignment requirements from exercise assumptions and unverified proposals from implemented behavior.

ADR 0001 records the completed Phase 01 foundation and verification. Its status is Implemented; human acceptance is not recorded. Planning proposals for later phases remain in [requirements](../requirements.md) and [architecture](../architecture.md).

ADR 0002 records the completed Phase 02 resource/configuration foundation, SQLite transaction behavior, business/idempotency models, atomic operations, initial migration, seed data, and readiness.

## Primary phase records

Reserve these names for the primary phase records. Create the file during the phase and replace its status below with a link and the actual status.

| Phase | Expected primary ADR | Current state |
| --- | --- | --- |
| 01 | [0001-foundation-config-logging.md](0001-foundation-config-logging.md) | Implemented; Phase 01 complete |
| 02 | [0002-database-and-seed-data.md](0002-database-and-seed-data.md) | Implemented; Phase 02 complete |
| 03 | [0003-business-rules-and-api.md](0003-business-rules-and-api.md) | Implemented; Phase 03 complete |
| 04 | [0004-user-interface.md](0004-user-interface.md) | Superseded by ADR 0009; Phase 04 workflow complete |
| 05 | [0005-containerisation.md](0005-containerisation.md) | Implemented; Phase 05 complete |
| 06 | `0006-ui-and-database-hardening.md` | Not created |
| 07 | `0007-testing-evaluation-and-ci.md` | Not created |
| 08 | `0008-documentation-and-handover.md` | Not created |
| 09 | `0011-local-llm-integration.md` | Deferred; not created (0009/0010 already exist) |

Additional ADRs use the next free number after the primary phase records and identify their phase in the record. Numbering is an index, not a substitute for the actual creation date.

## Additional decisions

| ADR | Current state |
| --- | --- |
| [0009 - Single-process HTML UI](0009-single-process-html-ui.md) | Implemented; Phase 04 architecture update |
| [0010 - Versioned request context](0010-versioned-request-context.md) | Implemented; Phase 04 structured-context extension |

## Status meanings

- **Proposed:** an option or plan is documented but not established in implementation.
- **Implemented:** code/configuration uses the choice; reference verification and remaining limits. This does not imply human sign-off.
- **Accepted:** a human has explicitly accepted the decision; record who/when and whether implementation is complete separately.
- **Superseded:** a later ADR replaces the decision; link both records and preserve the earlier rationale.

Update the relevant record if evidence changes its conclusion. Preserve earlier decisions rather than deleting inconvenient history. Do not manufacture a decision merely to fill the phase slot: explain a meaningful choice made in that phase, including continuation or release decisions where appropriate.
