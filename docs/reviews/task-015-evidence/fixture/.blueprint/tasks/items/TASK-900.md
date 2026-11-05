# TASK-900 — Write the continuity evidence artifact

## Metadata
- Status: in_review
- Priority: high
- Owner role: ORCHESTRATOR
- Specs: SPEC-900
- Dependencies: TASK-001
- Created: 2026-11-05
- Updated: 2026-11-05

## Objective
Demonstrate that a fresh session can continue this bounded unit using only persisted project files.

## Context
Read PROJECT_CONTEXT.md, CURRENT_STATE.md, registry, this brief, SPEC-900, DECISIONS.md, and the startup/task/handoff command protocols. Preserve the explicit unknown about the production technology stack.

## Scope
Create one exact evidence marker, record observed verification, transition to in_review, synchronize registry/backlog/current state, and create a handoff for a fresh reviewer. Also inspect the two read-only negative-recovery fixtures named in SPEC-900; report each as blocked when startup integrity checks fail and make no writes to either fixture.

## Out of scope
Production changes, secrets, commits, pushes, changing the unknown, and marking work done before independent review.

## Acceptance criteria
- [ ] AC-01: Complete dependency TASK-001 is independently verified from its brief and evidence file before work proceeds.
- [ ] AC-02: `evidence/continuity.txt` contains exactly `CONTINUITY-015-OK` on one line, verified by a command run in this fixture.
- [ ] AC-03: Registry, brief, backlog, and CURRENT_STATE consistently record the task as `in_review` with observed evidence.
- [ ] AC-04: A handoff records the observed Git state, evidence, remaining review, and exact next action for a fresh session.
- [ ] AC-05: Missing-record and canonical-state-mismatch negative fixtures are both reported as blocking, not repaired by guessing, and unchanged by the producer.

## Verification plan
Use `grep -Fx` for both markers; compare task status across canonical records; inspect handoff claims against files and Git; compare negative fixture file inventories before and after the read-only startup checks.

## Risks and open questions
Production technology stack remains explicitly unknown and is out of scope.

## Blockers
Independent Manager review pending (fresh reviewer). Negative fixtures `../task-015-negative-missing` and `../task-015-negative-mismatch` remain blocking on their own startups; left unchanged.

## Execution log
Seeded as the only in-progress synthetic task for the clean fresh-session test. Producer (2026-11-05): verified TASK-001 marker via `grep -Fx`, wrote `evidence/continuity.txt` with exact marker `CONTINUITY-015-OK`, verified via `grep -Fx` (exit 0, one line), synchronized registry/brief/backlog/CURRENT_STATE to `in_review`, created `.blueprint/handoffs/2026-11-05-task-900.md` and `.blueprint/sessions/2026-11-05-task-900.md`. Negative fixtures inspected read-only and reported blocking; no writes to either fixture. No commit, no delegation, no config change.

## Completion evidence
| Criterion | Evidence |
| --- | --- |
| AC-01 | TASK-001 `done` in registry/brief; `grep -Fx SYNTHETIC-DEPENDENCY-VERIFIED evidence/prerequisite.txt` matched, exit 0 (observed 2026-11-05). |
| AC-02 | `evidence/continuity.txt` is exactly `CONTINUITY-015-OK` on one line; `grep -Fx CONTINUITY-015-OK evidence/continuity.txt` matched, exit 0, `wc -l` = 1 (observed). |
| AC-03 | Registry, brief TASK-900, backlog, and CURRENT_STATE consistently record `in_review` with observed evidence in `.blueprint/handoffs/2026-11-05-task-900.md`. |
| AC-04 | Handoff `.blueprint/handoffs/2026-11-05-task-900.md` records Git state (branch `main`, no commits, untracked-tree status), evidence, pending Manager review, and exact next action; session record `.blueprint/sessions/2026-11-05-task-900.md` created. Not marked `done`. |
| AC-05 | `../task-015-negative-missing`: missing `.blueprint/memory/CURRENT_STATE.md` — blocking, unchanged. `../task-015-negative-mismatch`: registry `in_progress` vs brief `ready` — blocking, unchanged. Inventories before/after identical; no writes. |

## Next action
Fresh Manager reviewer reviews handoff `2026-11-05-task-900.md` and reruns verifications; do not mark done without review evidence.
