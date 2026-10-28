# AI development and evaluation record

Maintain this record throughout development. Explain useful agentic contributions and how their output was checked. Product AI features do not replace evidence of AI-assisted engineering.

## Contribution entry template

```text
Date and phase:
Task given to the assistant/agent:
Context and tools it used:
Output/change produced:
Human review actually performed:
Suggestions accepted, corrected, or rejected:
Independent checks and observed results:
Remaining risks or verification gaps:
Related files, ADR, build-log entry, and commit if present:
```

State who actually reviewed something. An assistant's own review is not human review. Generated tests and their implementation can share the same mistaken assumption, so validate them against the written acceptance examples.

## 2026-10-28 - Requirements discussion and scaffold generation

- Task: translate the supplied assignment and the user's choices into a phase-by-phase Python implementation scaffold.
- Contribution: the assistant read the assignment, explained the workflow, researched relevant official documentation, and drafted the project documents. The user selected the repository name, requested optional local AI and automated setup, chose one shared Dockerfile, and requested phase/ADR/build/commit guidance.
- Corrections during planning: pricing-exception approval was distinguished from mortgage credit approval; the original two-Dockerfile proposal was changed to a shared image used by separate service containers.
- Generated artefacts: the Markdown scaffold described in README.md.
- Human review: the user steered the planning choices. Review/acceptance of these final generated documents is not yet recorded.
- Verification: see the actual scaffold-validation entry in the build log once completed. No application behaviour, judge accuracy, or model performance has been validated by this planning work.
- Remaining gaps: all implementation phases, real test results, local-model resource measurements, and human-labelled AI evaluation are outstanding.

## Product AI evidence to add in Phases 06-07

Record the actual runtime image/version, model name and digest, quantisation, prompt/checklist/rubric versions, input/output limits, sampling settings, hardware, and evaluation date.

Keep the live review assistant and offline LLM judge distinct. Define what the judge grades and compare it with human-labelled cases. Report false passes, unsupported statements, repeated-run variability, and latency. Label synthetic data, fakes, fixtures, and live outputs accurately.

If the model cannot be downloaded or tested, record that limitation. Do not substitute invented scores, claim a fixture is live inference, or mark the live-model criteria complete.
