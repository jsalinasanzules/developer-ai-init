# TASK-012 — Specify project discovery and interactive initialization

## Metadata
- Status: done
- Priority: high
- Owner role: MANAGER: Architecture
- Specs: SPEC-008, SPEC-001
- Dependencies: TASK-001, TASK-002
- Created: 2026-11-04
- Updated: 2026-11-05

## Objective
Define how the blueprint discovers an existing/new project and gathers missing requirements before generating files.

## Scope
Specify discovery inventory, interview sequence, assumptions, confirmation summary, and approval points.

## Out of scope
Do not assume project stack or user requirements from repository contents alone.

## Acceptance criteria
- [x] Existing and empty project flows are covered.
- [x] Unknowns are explicit, not fabricated.
- [x] User confirms summary before generation.
- [x] Collision preview is part of the flow.

## Verification plan
Run the documented greenfield, brownfield, partial/resume, collision, and
approval-gate scenarios against the initialization protocol checks. Run the
repository Python tests and existing adapter and observability regression
verifiers. These checks verify the design contract, not an initializer runtime.

## Risks and open questions
None recorded.

## Blockers
None recorded.

## Execution log
- 2026-11-05: Rechecked dependencies TASK-001 and TASK-002; both are `done`.
  Re-read SPEC-008 and SPEC-001.
- 2026-11-05: User approved the proposal and authorized transition to `ready`.
  No TASK-012 implementation began in this recovery.
- 2026-11-05: Revalidated dependencies and canonical status, then transitioned
  `ready → in_progress` to specify discovery and initialization flows.
- 2026-11-05: Added the discovery, interview, confirmation, preview, approval,
  cancellation, and resume protocol with seven concrete scenarios.
- 2026-11-05: Added executable checks for the four acceptance criteria and
  lifecycle edge cases; the full Python suite and existing regression
  verifiers passed. See the verification report.
- 2026-11-05: Final scenario assertion needed refinement; TASK-012 remains
  `in_progress` until the corrected check and regression suite pass.
- 2026-11-05: Corrected the assertion, reran the six scenario checks and all
  29 Python tests successfully before adding the schema-mapping follow-up test.
- 2026-11-05: MANAGER: Architecture requested changes: map scope/success facts
  to canonical owners and define schema-required fields versus unknowns and
  confirmed-empty arrays. Findings recorded in the first review artifact.
- 2026-11-05: Resolved the schema-mapping findings, added a focused schema
  contract test, and reran all 30 Python tests plus the adapter and snapshot
  verifiers successfully; transitioned to `in_review` for focused independent
  follow-up review.
- 2026-11-05: Follow-up MANAGER: Architecture review requested clarification
  for mapping the purpose answer to both required scalar fields and alignment
  with schema rule R-PROJ-02. Findings recorded in the second review artifact.
- 2026-11-05: Returned `in_review → in_progress` after the follow-up findings;
  made purpose-field and schema-status rules explicit, and added concrete
  contract scenarios/tests for both. Final independent review is pending.
- 2026-11-05: Focused TASK-012 tests passed 9/9; full Python suite passed
  32/32; adapter and observability verifiers returned `RESULT: PASS`; diff
  hygiene and JSON parsing passed. Updated the verification report and mapped
  AC-02 to the new purpose/status tests.
- 2026-11-05: All four criteria and evidence are complete; transitioned to
  `in_review` for final independent MANAGER: Architecture review.
- 2026-11-05: The first evidence-gate check found that `Verification results`
  was nested under `Completion evidence`, so the gate could not parse either
  table. Promoted it to the required top-level section without changing its
  contents; rerunning the non-mutating check.
- 2026-11-05: The non-mutating gate passed and reran all five recorded checks.
  Final independent MANAGER: Architecture review approved. The evidence-gated
  completion command synchronized TASK-012 to `done` across the canonical
  records; TASK-013 remains unstarted pending user approval.

## Completion evidence

| Criterion | Criterion text | Evidence |
| --- | --- | --- |
| AC-01 | Existing and empty project flows are covered. | `test_greenfield_and_brownfield_scenarios_are_documented` in [test_initialization_spec.py](../../tests/test_initialization_spec.py) checks greenfield, brownfield, initialized, and reconciliation flows and their concrete scenarios; see [verification report](../../docs/reviews/2026-11-05-task-012-verification.md). |
| AC-02 | Unknowns are explicit, not fabricated. | `test_unknowns_remain_explicit_and_unconfirmed_facts_are_not_generated`, `test_schema_required_fields_and_scope_have_canonical_owners`, `test_confirmed_purpose_maps_to_required_description_and_summary`, and `test_initialization_status_matches_r_proj_02` in [test_initialization_spec.py](../../tests/test_initialization_spec.py) verify explicit unknown handling, canonical schema owners, required purpose fields, and the `partial`/`complete` contract in INIT-S08–S09; see [verification report](../../docs/reviews/2026-11-05-task-012-verification.md). |
| AC-03 | User confirms summary before generation. | `test_generation_requires_user_summary_confirmation` in [test_initialization_spec.py](../../tests/test_initialization_spec.py) checks the explicit summary gate, separate plan approval, and no-write scenario; see [verification report](../../docs/reviews/2026-11-05-task-012-verification.md). |
| AC-04 | Collision preview is part of the flow. | `test_collision_preview_exercises_each_outcome_and_conflict_blocks_writes` in [test_initialization_spec.py](../../tests/test_initialization_spec.py) checks `CREATE`, `MERGE`, `SKIP`, `CONFLICT`, exact-path approval, and all-or-nothing conflict behavior; see [verification report](../../docs/reviews/2026-11-05-task-012-verification.md). |

## Verification results

| Check | Command | Result | Evidence |
| --- | --- | --- | --- |
| TASK-012 contract tests | `python3 -m unittest discover -s tests -p 'test_initialization_spec.py' -v` | PASS | [verification report](../../docs/reviews/2026-11-05-task-012-verification.md) |
| Python tests | `python3 -m unittest discover -s tests -p 'test_*.py' -v` | PASS | [verification report](../../docs/reviews/2026-11-05-task-012-verification.md) |
| OpenCode adapter regression | `python3 scripts/verify-opencode-adapter.py` | PASS | [verification report](../../docs/reviews/2026-11-05-task-012-verification.md) |
| Observability snapshot regression | `bun run scripts/verify-observability-snapshot.ts` | PASS | [verification report](../../docs/reviews/2026-11-05-task-012-verification.md) |
| Diff whitespace validation | `git diff --check` | PASS | [verification report](../../docs/reviews/2026-11-05-task-012-verification.md) |

## Manager review

Initial independent MANAGER: Architecture review requested changes; see
[review 1](../../docs/reviews/2026-11-05-task-012-manager-review-1.md).
The first follow-up identified two additional schema semantics; see
[review 2](../../docs/reviews/2026-11-05-task-012-manager-review-2.md).
Both sets of findings have been addressed. Final independent MANAGER:
Architecture review is approved:
`docs/reviews/2026-11-05-task-012-manager-review-3.md`.

## Next action
Present TASK-013 for user approval; do not start TASK-013 or TASK-014 until approved.
