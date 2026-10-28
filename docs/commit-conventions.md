# Commit message conventions

Use this format when creating an authorised commit:

```text
[AREA][ACTION][MILESTONE] Short imperative description
```

Example:

```text
[LOGGING][ADD][MVP1] Add structured request logging
```

Use uppercase tags, no spaces between bracketed tags, and one space before the description. Start the description with a verb. Aim for a subject around 72 characters; favour clarity over an arbitrary hard limit. Avoid vague subjects such as "updates" or "fix stuff".

## Area tags

| Tag | Responsibility |
| --- | --- |
| CONFIG | Environment configuration and settings validation |
| LOGGING | Operational logging and correlation identifiers |
| DOMAIN | Business rules, status transitions, revisions |
| API | HTTP endpoints, transport schemas, responses |
| AUTH | Identity and permission checks |
| DB | Models, migrations, storage, seed data |
| UI | Streamlit screens and interactions |
| LLM | Model adapter, prompts, AI assessments and evaluation |
| DOCKER | Dockerfile, Compose, runtime/model bootstrap, volumes |
| TEST | Changes primarily to automated tests |
| CI | Automated repository validation |
| DOCS | Requirements, guides, ADRs, build records, handoffs |
| DEPS | Dependency additions, removals, and upgrades |

Choose the primary area affected. An API bug fix containing a regression test uses API rather than an additional TEST tag. Split unrelated changes rather than stacking many area tags.

## Action tags

| Tag | Meaning |
| --- | --- |
| ADD | Introduce a capability, record, or file |
| UPDATE | Change existing behaviour, configuration, or documentation |
| FIX | Correct incorrect behaviour |
| REFACTOR | Change structure while preserving intended behaviour |
| REMOVE | Remove obsolete functionality or files |

For a test-only addition use TEST + ADD. For dependency removal use DEPS + REMOVE. Keep the vocabulary consistent rather than adding synonyms for the same action.

## Milestones

| Tag | Target delivery | Main phases |
| --- | --- | --- |
| MVP1 | Working approval API, persistence, configuration, logging, core tests | 01-03 |
| MVP2 | Human workflow through the containerised UI | 04-05 |
| MVP3 | Optional local AI, quality evidence, and final handover | 06-08 |

Use the milestone the work supports. A later fix to an API during MVP3 can use MVP3. Milestones are delivery labels, not claims that a version is production-ready. Put phase numbers in the body when useful.

## Examples

```text
[DOCS][ADD][MVP1] Add phase guides and engineering standards
[CONFIG][ADD][MVP1] Validate environment settings at startup
[DB][ADD][MVP1] Create request version and decision tables
[DOMAIN][ADD][MVP1] Require fresh review for revised terms
[AUTH][FIX][MVP1] Reject self-review attempts
[API][FIX][MVP1] Reject decisions for outdated versions
[TEST][ADD][MVP1] Cover competing reviewer decisions
[UI][ADD][MVP2] Add pending request review screen
[DOCKER][ADD][MVP2] Share one image across API and UI services
[LLM][ADD][MVP3] Validate structured assessment responses
[DOCKER][ADD][MVP3] Cache the optional local model
[CI][ADD][MVP3] Run core checks without model downloads
[DOCS][UPDATE][MVP3] Record evaluation results and limitations
```

## Optional body

Explain the reason, a meaningful trade-off, and actual verification. Do not claim checks ran unless their results were inspected.

```text
[API][FIX][MVP1] Reject decisions for outdated request versions

Require the reviewed version to match the current pending version.
This prevents approval of terms changed after the reviewer opened them.

Phase: 03
ADR: docs/adr/0003-business-rules-and-api.md
Verification: stale-version and competing-decision tests pass.
```

The body above is an illustrative format, not a claim about existing files or passed tests. A commit convention does not itself authorise creating commits, pushing, or changing a remote repository.
