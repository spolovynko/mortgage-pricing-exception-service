# Architecture decision records

ADRs explain a consequential choice, its alternatives, and its trade-offs. Use the [template](template.md). Create at least one primary record per phase, plus additional records for distinct decisions that need their own explanation.

ADR 0001 records the completed Phase 01 foundation and verification. Its status is Implemented; human acceptance is not recorded. Planning proposals for later phases remain in [requirements](../requirements.md) and [architecture](../architecture.md).

## Primary phase records

Reserve these names for the primary phase records. Create the file during the phase and replace its status below with a link and the actual status.

| Phase | Expected primary ADR | Current state |
| --- | --- | --- |
| 01 | [0001-foundation-config-logging.md](0001-foundation-config-logging.md) | Implemented; Phase 01 complete |
| 02 | `0002-database-and-seed-data.md` | Not created |
| 03 | `0003-business-rules-and-api.md` | Not created |
| 04 | `0004-user-interface.md` | Not created |
| 05 | `0005-containerisation.md` | Not created |
| 06 | `0006-local-llm-integration.md` | Not created |
| 07 | `0007-testing-evaluation-and-ci.md` | Not created |
| 08 | `0008-documentation-and-handover.md` | Not created |

Additional ADRs use the next free number starting at 0009 and identify their phase in the record. Numbering is an index, not a substitute for the actual creation date.

## Status meanings

- **Proposed:** an option or plan is documented but not established in implementation.
- **Implemented:** code/configuration uses the choice; reference verification and remaining limits. This does not imply human sign-off.
- **Accepted:** a human has explicitly accepted the decision; record who/when and whether implementation is complete separately.
- **Superseded:** a later ADR replaces the decision; link both records and preserve the earlier rationale.

Update the relevant record if evidence changes its conclusion. Preserve earlier decisions rather than deleting inconvenient history. Do not manufacture a decision merely to fill the phase slot: explain a meaningful choice made in that phase, including continuation or release decisions where appropriate.
