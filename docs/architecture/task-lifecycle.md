# Task Lifecycle

## Statuses
- `proposed`: captured but not ready for execution.
- `ready`: dependencies and scope are sufficiently clear.
- `in_progress`: actively being executed.
- `blocked`: cannot proceed; blocker and owner/action recorded.
- `in_review`: implementation is complete but evidence/review is pending.
- `done`: acceptance criteria verified with recorded evidence.
- `cancelled`: intentionally stopped with rationale.

## Lifecycle
```text
proposed → ready → in_progress → in_review → done
                 ↘ blocked ↗
proposed / ready / in_progress → cancelled
```

A task may return to `in_progress` if review finds a gap. A blocked task returns to a suitable active status only after its blocker is resolved.

## Required task fields
ID, title, status, priority, specification references, owner role, dependencies, scope, exclusions, acceptance criteria, verification plan, created/updated dates, blocker, evidence, and next action.

## Completion rule
A task is not done because code was written or an agent says it is done. Every acceptance criterion must have observable evidence (test output, command result, review artifact, or verified behavior). If evidence is unavailable, use `in_review` or `blocked`.

## Handoffs
A handoff identifies the exact active task, repository state/commit if known, completed work, files changed, checks run, unresolved questions, risks, and the next action. The receiving LLM must re-read repository state rather than trust the handoff blindly.
