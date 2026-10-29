# Python engineering guidelines

These standards apply to implementation in every phase. Read them with [AGENTS.md](../AGENTS.md), the active phase guide, and [requirements](requirements.md).

## Design principles

### KISS: keep the solution understandable

Prefer clear functions and small classes with explicit inputs and outputs. Keep one deployable application codebase with a small number of runtime services. Add an abstraction when it removes real complexity, creates a useful testing boundary, or expresses an important business concept. Do not create empty layers to satisfy a diagram.

### SOLID: apply the principles proportionally

- **Single responsibility:** API code handles HTTP, business services enforce rules, persistence manages storage, the UI presents information, and the LLM adapter handles model communication.
- **Open/closed:** use a small configurable model adapter or policy function when a real variation exists. Avoid frameworks for hypothetical future variations.
- **Liskov substitution:** a test double and a live adapter must obey the same return/error contract. Do not make the fake hide failures that the live provider can produce.
- **Interface segregation:** expose the operations a caller needs. Avoid a large generic interface for unrelated database and AI operations.
- **Dependency inversion:** business behaviour should be testable with explicit dependencies for storage, time, or the model boundary. FastAPI dependency injection can supply sessions and acting users.

### DRY: share authoritative rules

Keep status transitions, permission checks, settings definitions, and response contracts in one authoritative implementation. Reuse them through services, not copy/paste in UI handlers. Similar-looking code with different responsibilities does not automatically require a shared abstraction.

## Appropriate Python patterns

| Need | Suitable starting point |
| --- | --- |
| Business operation | A focused service function/class with explicit dependencies |
| Input/output contract | Pydantic models |
| External model integration | A small adapter; a Protocol if substitution materially helps |
| Isolated application setup | An application factory where useful |
| Database resource lifetime | Context managers and injected sessions |
| Several genuine behaviours | A small strategy function/interface backed by observed requirements |

Use a repository wrapper only if it improves query ownership or testing. SQLAlchemy sessions already supply useful persistence behaviour; avoid a generic CRUD repository hierarchy. Avoid global mutable service locators or singleton database sessions. Do not add decorators, factories, inheritance trees, or an agent framework solely to demonstrate a pattern.

## Python code quality

- Choose a supported Python baseline during Phase 01 and use it consistently in development, CI, and containers. Python 3.12 is the planning baseline, subject to a documented dependency compatibility check.
- Use standard naming, descriptive modules, small functions, and type hints at public boundaries. Use docstrings for non-obvious contracts and rationale rather than narrating each line.
- Use pathlib for filesystem paths and timezone-aware UTC timestamps. Store rates as integer basis points or Decimal when arithmetic is necessary.
- Use narrow, meaningful exceptions. Translate expected domain failures into stable API errors. Preserve unexpected error details in server logs without exposing internals in responses.
- Never swallow failures through broad exception handling that returns a fabricated success.
- Use context managers for resources. Avoid mutable default arguments and accidental shared state between requests/tests.
- Keep I/O bounded. Use async only where it helps, and do not block the event loop with synchronous model or database work.
- Separate transport models from persistence details where the boundary warrants it. Avoid unnecessary duplicate domain/entity classes.
- Pin resolved dependencies with one documented resolver/lock workflow. Use pyproject.toml for project/tool configuration as appropriate. Do not maintain conflicting dependency sources.
- Establish formatting/lint commands in Phase 01; Ruff is the proposed initial tool. Add type checking if it gives useful signal rather than cosmetic workload.

## Configuration

Use Pydantic Settings as the central definition of environment configuration. Validate types, accepted modes, bounds, and necessary paths at startup. Inject settings into tests; do not make test configuration depend on a developer's actual environment.

Include an .env.example with safe defaults. Environment values override defaults; document precedence. Exclude actual .env files and credentials from Git. Redact sensitive values if reporting settings. Container service addresses differ from host-local addresses.

AI settings must distinguish deployment permission, runtime readiness, and the user's session toggle. `LLM_MODE=auto` permits discovery, not automatic assessment. A profile starting Ollama must not be assumed to change the API's settings automatically.

## Logging, errors, and audit history

Use a consistent structured schema: timestamp, level, event, correlation_id, relevant actor/request/version identifiers, outcome, and duration. Correlation IDs trace technical operations and are distinct from domain IDs. Validate/bound caller-supplied tracing values.

Write logs to stdout/stderr in containers and configure bounded retention in Compose. Log useful failures once at an appropriate boundary rather than repeatedly logging and rethrowing every exception. Default to metadata rather than raw reasons, complete prompts, secrets, or personal data.

Operational logs are not the business audit trail. Persist history events with the business change in the same transaction. Preserve submitted terms and decisions through the application API, and describe the limits of local SQLite history honestly.

## Database integrity

Enforce important uniqueness/relationship constraints in the database. Enable required SQLite behaviour, including foreign-key checks, and document the transaction configuration. Use file-backed, isolated test databases for realistic competing-connection tests.

Treat create plus idempotency plus history as one atomic operation. Treat decision plus history and current-version checks as one atomic operation. A check followed by an unprotected write is not adequate concurrency handling.

Use migrations rather than resetting existing data after a schema change. Seed missing fictional records repeatably. Never erase an evaluator's existing database just to simplify startup.

Do not hold a write transaction open during a model call. Capture the requested version, call the model outside the transaction, and recheck how the result relates to the current version before presenting/persisting it.

## API and UI

Validate input at the API boundary and enforce business rules server-side. Distinguish missing resources, invalid input, permission failures, stale versions, and conflicting operations through documented errors.

Do not let the UI write directly to storage or invoke the model server. Preserve idempotency keys during retries. Rendering, filtering, refreshing, or changing a preference must not initiate business writes or inference; explicit actions initiate writes. The assistance toggle is local to the current browser session.

Simulated identity must be clearly identified and configured. Hiding a button does not enforce a permission. Prevent self-review and stale decisions in the backend.

## AI integration and evaluation

Use a narrow task and a written checklist. Treat request text as untrusted data, including instructions embedded in reasons. Supply only needed fields. The model has no approval-writing tool or permission.

Request structured output, validate it, and distinguish schema validity from factual correctness. Bound input/output, timeouts, retries, and concurrency. Use model/prompt/checklist versions and exact request-version references in assessment metadata. Low temperature does not guarantee repeatability or truth.

Use human-labelled examples to evaluate the actual quantised model. Assess unsupported claims, omissions, evidence references, adversarial input, and repeated-run inconsistency. Keep LLM-judge calibration separate from the business decision path. Do not rely only on an LLM evaluating its own outputs.

Ordinary tests use explicit fakes. Live evaluations run separately with the real local model and record hardware, model digest, settings, latency, and results. Label fixtures and cached examples; never display them as live inference.

## Containers

Use one application Dockerfile and one Compose file. Configure one core application container running one Uvicorn process for UI and API; a future model-init job may reuse the image with a different command. Pin the tested base/runtime images; keep future model weights in a named volume. Minimise image contents with .dockerignore and use an appropriate non-root application user with verified volume permissions.

Keep core readiness independent of optional AI. Use health checks for actual service readiness, not fixed sleeps. Default to CPU-capable execution. Publish only necessary demonstration ports on host loopback.

## Testing and delivery

Test observable behaviour, particularly permissions, version fidelity, duplicate handling, competing writes, transaction integrity, model failures, and persistence. Add regression tests for meaningful defects. Avoid tests that merely repeat implementation details or assert cosmetic formatting without a user need.

Keep tests deterministic and isolated from network/model downloads unless explicitly marked integration/live evaluation. Mock at external boundaries and use the real database where storage guarantees matter. Run relevant checks after changes; record exact results and known gaps.

Follow [commit conventions](commit-conventions.md) when commits are authorised. Keep a coherent change per commit. Maintain ADRs, build records, AI-use evidence, and handoffs as described in AGENTS.md. Do not mark a phase complete until its actual evidence supports the acceptance criteria.
