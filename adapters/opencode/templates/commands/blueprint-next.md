---
description: Select the next eligible Blueprint task from the registry
agent: orchestrator
---

Select the next eligible task and report it. Do not start work yet.

1. Read `.blueprint/tasks/registry.json` (authoritative; `.blueprint/tasks/backlog.md`
   is only a projection).
2. If a task is `in_progress`, report it as the active task and its next action.
   If more than one is `in_progress`, stop and report the state conflict.
3. Otherwise select the highest-priority `ready` task whose dependencies are all
   `done`, ties broken by lowest task ID. Priority order: critical, high, medium, low.
4. Verify the matching brief in `.blueprint/tasks/items/` exists and that its status
   matches the registry; report any mismatch as a blocking integrity error.
5. Confirm scope, exclusions, acceptance criteria, verification plan, and linked specs
   are readable. If a dependency or spec is missing, stop and report.
6. Report the task, evidence that dependencies are done, and the proposed first action.
   Wait for user confirmation before marking it `in_progress`.

$ARGUMENTS
