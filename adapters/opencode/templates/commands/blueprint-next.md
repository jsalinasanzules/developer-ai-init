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
4. For every dependency, verify the registry status is `done` and its matching task
   brief has all acceptance criteria checked with corresponding completion evidence.
   A missing brief or missing evidence means the dependency is not satisfied.
5. Verify the selected task brief exists and its status matches the registry entry; report
   any mismatch as a blocking integrity error.
6. Confirm scope, exclusions, acceptance criteria, verification plan, and linked specs
   are readable. If a dependency, brief, criterion evidence, or spec is missing, stop
   and report.
7. Report the selected task, each dependency and its evidence, and the proposed first
   action. Wait for user confirmation before marking it `in_progress`.

$ARGUMENTS
