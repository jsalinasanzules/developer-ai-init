---
description: Execute a Blueprint task under the delegation and evidence protocol
agent: orchestrator
---

Execute Blueprint task $ARGUMENTS under the project's task lifecycle.

1. Read the task brief `.blueprint/tasks/items/<TASK-ID>.md` and its linked specs from
   `.blueprint/specs/`. Confirm the task is `ready` (or `in_progress` for continuation)
   and dependencies are `done`. Stop on any mismatch and report.
2. Announce the plan: objective, allowed scope, forbidden changes, acceptance criteria,
   and how work will be delegated (Managers for review, Specialist for scoped
   execution; with subagent depth 1, pass the Specialist return back through a
   Manager review before proceeding).
3. Delegate with the full payload (objective, context, scope, exclusions, dependencies,
   constraints, artifacts, acceptance criteria, return format, escalation).
4. Review returned evidence before accepting: confirm commands were run and outputs
   observed; reject assertions. Specialists and Managers never write canonical
   records; their durable findings are proposals you review.
5. Apply accepted changes to the owning canonical record, synchronize projections
   (`CURRENT_STATE.md`, registry, backlog), and update the task brief's execution log
   and completion evidence.
6. Update task status only through valid lifecycle transitions
   (`ready → in_progress → in_review → done`); `done` requires evidence for every
   acceptance criterion. Record blockers with reason, responsible role, and next action.
7. If a material decision is required (architecture, security, privacy, scope,
   ownership, compatibility, destructive action), stop and ask the user one explicit
   question with sources, impacts, and options. Do not write the contested change.
8. Commit with a descriptive message. Never commit secrets.

Finish by summarizing: scope completed, files changed, verification evidence, and next
action.
