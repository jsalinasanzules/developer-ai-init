# TASK-010 — Add OpenCode startup, task, and handoff workflows

## Metadata
- Status: done
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
- [x] Fresh session loads mandatory memory records.
- [x] Agent identifies one eligible task and checks dependencies.
- [x] Task completion updates records with evidence.
- [x] Handoff can be produced and consumed.

## Verification plan
Perform cold-start test in a new OpenCode session using only repository files.

## Risks and open questions
None recorded.

## Blockers
- **Resolved 2026-11-04 (historical context — no longer active):** The OpenCode 2.2.5 cold-start workflow could not reach a model: both available free-model attempts were rejected because the free usage limit was reached. The blocker was cleared by live verification using `crouton-alpha-free`. Management note: do not incur paid model usage without user approval.
- Responsible role: USER
- Next action: None. Verification complete (see report below); TASK-010 is done.

## Execution log
- 2026-11-04: Began after verifying TASK-004, TASK-006, and TASK-009 are `done`; no other task is `in_progress`. OpenCode v2.2.5 is available. Existing startup, next, task, handoff, and consolidation command templates will be validated in an isolated generated project before making any implementation changes.
- 2026-11-04: Updated the OpenCode startup, task-selection, and task-execution templates to require the canonical startup read order, integrity/version stops, dependency completion evidence, lifecycle synchronization, and evidence-backed completion. Updated target `AGENTS.md` startup instructions and added structural workflow checks to `scripts/verify-opencode-adapter.py`.
- 2026-11-04: `python3 scripts/verify-opencode-adapter.py` → `RESULT: PASS`. In an isolated generated project, `opencode debug config` resolved `opencode.jsonc` and `.opencode/`; `opencode debug agents` discovered all six Blueprint agents. Live startup attempts via `opencode run --standalone --agent orchestrator --model opencode/glm-5.3-flash-free ...` and `... --model opencode/mimo-v2.6-flash-free ...` both returned `Free usage limit reached` before the model executed. No paid model was used. The four live workflow acceptance criteria therefore remained unverified; TASK-010 is blocked pending user approval or user-provided runtime evidence.
- 2026-11-04: Live verification completed with `opencode/crouton-alpha-free` (no paid models) in the isolated verification project. All four acceptance criteria passed and were audited (see `docs/reviews/2026-11-04-task-010-verification.md` and `docs/reviews/task-010-evidence/`). Lifecycle completion was re-run strictly per protocol after audit caught a single-commit `done` jump; TASK-900 transition commits `06bdd19`/`1d53129`/`9795b73`/`2bad731` persist the intermediate states in the isolated project. Blocker from the previous line is historical; TASK-010 is done (Joseph explicitly authorized finalization).

## Completion evidence
| Criterion | Evidence |
| --- | --- |
| Fresh session loads mandatory memory records. | Live `/blueprint-startup` run read 11 records in order; 27/27 manifest SHA-256 verified `OVERALL PASS`; context packet produced. Report: `docs/reviews/2026-11-04-task-010-verification.md` §1; session log: `docs/reviews/task-010-evidence/01-cold-start.txt`. |
| Agent identifies one eligible task and checks dependencies. | Live `/blueprint-next` selected TASK-012 after verifying TASK-001/TASK-002 `done`+evidenced; TASK-011 explicitly rejected while TASK-010 is `blocked`. Report §2; log: `docs/reviews/task-010-evidence/02-task-selection.txt`. |
| Task completion updates records with evidence. | Negative path rejected and preserved (CONDITIONAL GO); positive path re-run strictly per lifecycle protocol with four persisted transitions: proposed→ready `06bdd19`, ready→in_progress `1d53129`, in_progress→in_review `9795b73`, in_review→done `2bad731`, all in the isolated project; C1 evidence bytes `LIFECYCLE-TEST-OK\n` verified. Report §3; log: `docs/reviews/task-010-evidence/03-lifecycle-full-log.txt`. |
| Handoff can be produced and consumed. | Handoff produced per template in the isolated project and consumed by a genuinely new session, which verified claims against files/Git and confirmed continuation from files alone. Report §4; handoff: `docs/reviews/task-010-evidence/handoff-2026-11-04-task-010-verify.md`; consumption: `docs/reviews/task-010-evidence/04-handoff-consumption.txt`. |

Structural validator: `python3 scripts/verify-opencode-adapter.py` → `RESULT: PASS` (re-run at completion; see Git commit for this task).

## Next action
None. TASK-010 is done (all four acceptance criteria verified live; see `docs/reviews/2026-11-04-task-010-verification.md`).
