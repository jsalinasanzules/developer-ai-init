# TASK-010 — Add OpenCode startup, task, and handoff workflows

## Metadata
- Status: blocked
- Priority: high
- Owner role: MANAGER: Engineering
- Specs: SPEC-002, SPEC-005, SPEC-007
- Dependencies: TASK-004, TASK-006, TASK-009
- Created: 2026-11-04
- Updated: 2026-11-04

## Objective
Provide provider-native entry points for startup memory loading, task execution, memory consolidation, and handoff.

## Scope
Implement commands/skills/prompts supported by verified OpenCode capabilities.

## Out of scope
Do not create unsupported command mechanisms or bypass approval gates.

## Acceptance criteria
- [ ] Fresh session loads mandatory memory records.
- [ ] Agent identifies one eligible task and checks dependencies.
- [ ] Task completion updates records with evidence.
- [ ] Handoff can be produced and consumed.

## Verification plan
Perform cold-start test in a new OpenCode session using only repository files.

## Risks and open questions
None recorded.

## Blockers
- Reason: The OpenCode 2.2.5 cold-start workflow could not reach a model: both available free-model attempts were rejected because the free usage limit was reached. Do not incur paid model usage without user approval.
- Responsible role: USER
- Next action: Authorize one isolated run with an authenticated paid model, or run the cold-start workflows in the user's OpenCode session and report observed results.

## Execution log
- 2026-11-04: Began after verifying TASK-004, TASK-006, and TASK-009 are `done`; no other task is `in_progress`. OpenCode v2.2.5 is available. Existing startup, next, task, handoff, and consolidation command templates will be validated in an isolated generated project before making any implementation changes.
- 2026-11-04: Updated the OpenCode startup, task-selection, and task-execution templates to require the canonical startup read order, integrity/version stops, dependency completion evidence, lifecycle synchronization, and evidence-backed completion. Updated target `AGENTS.md` startup instructions and added structural workflow checks to `scripts/verify-opencode-adapter.py`.
- 2026-11-04: `python3 scripts/verify-opencode-adapter.py` → `RESULT: PASS`. In an isolated generated project, `opencode debug config` resolved `opencode.jsonc` and `.opencode/`; `opencode debug agents` discovered all six Blueprint agents. Live startup attempts via `opencode run --standalone --agent orchestrator --model opencode/glm-5.3-flash-free ...` and `... --model opencode/mimo-v2.6-flash-free ...` both returned `Free usage limit reached` before the model executed. No paid model was used. The four live workflow acceptance criteria therefore remain unverified; TASK-010 is blocked pending user approval or user-provided runtime evidence.

## Completion evidence
| Criterion | Evidence |
| --- | --- |
| Fresh session loads mandatory memory records. | `blueprint-startup.md` now specifies the required ordered read set and integrity stops; structural validator passes. Live model-backed startup was attempted but blocked by the free usage limit. |
| Agent identifies one eligible task and checks dependencies. | `blueprint-next.md` verifies status, dependency briefs, checked criteria, and completion evidence; structural validator passes. Live selection was not observed because model execution was blocked. |
| Task completion updates records with evidence. | `blueprint-task.md` specifies lifecycle transitions and synchronized record updates with criterion-to-evidence mapping; structural validator passes. Live execution was not observed because model execution was blocked. |
| Handoff can be produced and consumed. | `blueprint-handoff.md` specifies required handoff contents and state update; `blueprint-startup.md` verifies a named handoff against files and Git; structural validator passes. Live production/consumption was not observed because model execution was blocked. |

## Next action
Resume live cold-start verification after an authorized model is available or Joseph reports results from a user-run session; then update evidence and task status.
