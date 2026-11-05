# TASK-020 — Correct TASK-011 adapter regeneration and completion evidence

## Metadata
- Status: done
- Priority: critical
- Owner role: MANAGER: Quality
- Specs: SPEC-005, SPEC-006, SPEC-007, SPEC-009
- Dependencies: TASK-006, TASK-009
- Created: 2026-11-05
- Updated: 2026-11-05

## Objective
Implement the missing safe OpenCode adapter regeneration behavior and prevent
the official task workflow from transitioning `in_review` to `done` without
verified acceptance evidence.

## Context
TASK-011's historical `done` transition is preserved. Its original acceptance
evidence was insufficient, as documented in
`docs/reviews/2026-11-05-task-011-acceptance-audit.md`. This corrective task
does not rewrite TASK-011's lifecycle history.

## Scope
- Add a manifest-driven OpenCode template generator with non-mutating preview,
  merge/skip/conflict classification, collision checks, and exact-path
  overwrite approval.
- Add behavioral conformance scenarios for empty targets, existing config,
  managed-file updates, user-content preservation, conflicts, and repeat runs.
- Add a task completion command that validates acceptance evidence, passing
  verification results, an independent Manager review, and canonical record
  agreement before synchronizing a task to `done` in this source repository.
- Update the OpenCode task workflow and lifecycle documentation to require the
  evidence gate without imposing its implementation runtime on generated projects.
- Synchronize records affected by TASK-011's invalid historical evidence.
- Keep Python tooling internal to this source repository; generated adapter files
  must not require Python.

## Out of scope
- Do not alter TASK-011's historical `done` status or erase its recorded events.
- Do not change `.opencode/` or the existing monitor edits.
- Do not start TASK-012 or other backlog work.
- Do not commit or push.

## Acceptance criteria
- [x] Adapter regeneration previews concrete create, merge, skip, and conflict outcomes without writing; all destination paths are checked before any write.
- [x] Managed Markdown updates preserve user content outside the managed region and are idempotent; compatible OpenCode JSONC configuration merges without losing user settings.
- [x] A conflicting destination is left untouched unless its exact relative path has explicit overwrite approval; an unapproved conflict prevents the whole plan from writing.
- [x] Behavioral conformance tests cover empty install, compatible existing config, conflicting config, managed-file merge, skip, overwrite approval, and repeated generation.
- [x] The completion command refuses `in_review` → `done` unless every checked criterion maps to concrete test evidence, verification results pass, an independent Manager review is approved, and task/registry/backlog/current-state records agree.
- [x] Negative tests prove missing criteria evidence, failed/missing tests, missing or rejected Manager review, and canonical-record mismatches block completion without changing files.
- [x] Generated adapter files contain no Python helper or Python invocation, preserving runtime-neutral target projects.

## Verification plan
- Run the focused OpenCode regeneration and task lifecycle unit tests.
- Run the existing OpenCode adapter and observability snapshot verifiers.
- Exercise the completion command against valid and invalid temporary project
  fixtures; compare file contents before and after each rejected transition.
- Have a Manager independently review the resulting implementation and observed
  test output.

## Risks and open questions
None. The historical completion correction and implementation scope were
authorized by the user.

## Blockers
None.

## Execution log
- 2026-11-05: Recovery started from the inspected dirty working tree. TASK-011
  remains historically `done`; the audit correction and TASK-020 were added
  without altering the pre-existing `.opencode/` symlink or monitor edits.
- 2026-11-05: Implemented manifest-driven preview and regeneration, evidence
  completion gate, runtime-boundary docs, and behavioral/negative tests.
- 2026-11-05: Focused suite passed 21/21; adapter and monitor snapshot
  verification both returned `RESULT: PASS`; see
  `../../docs/reviews/2026-11-05-task-020-verification.md`.
- 2026-11-05: Transitioned to `in_review` with all seven criteria checked and
  mapped to named behavioral tests; independent Manager review is pending.
- 2026-11-05: Independent MANAGER: Quality review requested changes: an
  approved directory collision could cause partial writes; named-test
  absence lacked a dedicated negative case; and the snapshot assertion
  expected an `in_review` task to be active contrary to the selection
  protocol. Returned to `in_progress`; review:
  `../../docs/reviews/2026-11-05-task-020-manager-review-1.md`.
- 2026-11-05: Directory targets can no longer be approved for overwrite;
  added a no-partial-write regression test and a missing-named-test negative
  case. Corrected the snapshot assertion to follow the documented
  in_progress/ready active-task selection contract without changing monitor
  behavior. All checks now pass; requesting final independent review.
- 2026-11-05: Final independent MANAGER: Quality review approved all seven
  criteria and the recorded verification evidence; see
  `../../docs/reviews/2026-11-05-task-020-manager-review.md`.
- 2026-11-05: A non-mutating completion-gate check exposed two integration
  mismatches: the evidence table needed criterion text plus a linked test
  module, and the backlog matcher needed to accept existing priority and
  dependency suffixes. Corrected both and their fixtures; reopened the task
  for supplemental review of the gate integration.
- 2026-11-05: The corrected non-mutating completion-gate check passed,
  including reruns of all three recorded verification commands. All seven
  criteria are complete again; supplemental Manager review is pending.
- 2026-11-05: Supplemental independent MANAGER: Quality review approved the
  evidence-table/backlog integration, snapshot selection assertions, and
  gate-check result; see
  `../../docs/reviews/2026-11-05-task-020-gate-review.md`.
- 2026-11-05: The evidence-gated completion command reran the 23 focused tests
  and both verifiers, then synchronized TASK-020 to `done` across the task
  brief, registry, backlog, and current state. TASK-012 remains proposed and
  awaits user approval.

## Completion evidence

| Criterion | Acceptance criterion | Behavioral evidence |
| --- | --- | --- |
| AC-01 | Adapter regeneration previews concrete create, merge, skip, and conflict outcomes without writing; all destination paths are checked before any write. | `test_cli_dry_run_reports_create_merge_skip_and_conflict` in [test_opencode_regeneration.py](../../tests/test_opencode_regeneration.py) asserts concrete outcomes; `test_cli_dry_run_reports_plan_without_creating_files` asserts dry-run leaves the destination unchanged; `test_approved_directory_conflict_is_rejected_before_any_write` verifies all writes are blocked for an unresolvable approved collision. |
| AC-02 | Managed Markdown updates preserve user content outside the managed region and are idempotent; compatible OpenCode JSONC configuration merges without losing user settings. | `test_user_edits_inside_managed_region_conflict_but_approved_update_preserves_outside` and `test_existing_markdown_and_compatible_jsonc_merge_without_losing_user_content` in [test_opencode_regeneration.py](../../tests/test_opencode_regeneration.py) verify preservation and merging; `test_clean_install_is_idempotent` verifies repeat runs. |
| AC-03 | A conflicting destination is left untouched unless its exact relative path has explicit overwrite approval; an unapproved conflict prevents the whole plan from writing. | `test_unapproved_conflict_prevents_every_write`, `test_approved_directory_conflict_is_rejected_before_any_write`, and `test_exact_path_approval_overwrites_only_the_approved_conflict` in [test_opencode_regeneration.py](../../tests/test_opencode_regeneration.py) verify all-or-nothing conflict handling and exact-path approval. |
| AC-04 | Behavioral conformance tests cover empty install, compatible existing config, conflicting config, managed-file merge, skip, overwrite approval, and repeated generation. | `test_empty_target_dry_run_creates_without_writing`, `test_existing_markdown_and_compatible_jsonc_merge_without_losing_user_content`, `test_cli_dry_run_reports_create_merge_skip_and_conflict`, and `test_clean_install_is_idempotent` in [test_opencode_regeneration.py](../../tests/test_opencode_regeneration.py) cover install, merge, conflict, skip, approval, and repeat generation scenarios. |
| AC-05 | The completion command refuses `in_review` → `done` unless every checked criterion maps to concrete test evidence, verification results pass, an independent Manager review is approved, and task/registry/backlog/current-state records agree. | `test_valid_evidence_passes_gate_and_synchronizes_all_records` in [test_task_lifecycle.py](../../tests/test_task_lifecycle.py) verifies accepted evidence and synchronized status; `test_check_command_runs_tests_before_authorizing_transition` verifies recorded checks execute. |
| AC-06 | Negative tests prove missing criteria evidence, failed/missing tests, missing or rejected Manager review, and canonical-record mismatches block completion without changing files. | `test_missing_criterion_evidence_blocks_completion`, `test_missing_named_test_evidence_blocks_completion`, `test_failed_or_missing_test_report_blocks_completion`, `test_missing_manager_review_blocks_completion`, `test_rejected_or_wrong_role_review_blocks_completion`, and `test_registry_task_backlog_and_current_state_mismatches_block_completion` in [test_task_lifecycle.py](../../tests/test_task_lifecycle.py) verify rejection without record writes. |
| AC-07 | Generated adapter files contain no Python helper or Python invocation, preserving runtime-neutral target projects. | `test_generated_adapter_files_do_not_require_python` in [test_opencode_regeneration.py](../../tests/test_opencode_regeneration.py) verifies generated targets contain neither Python helper files nor Python invocations. |

## Next action
Present TASK-012 proposal for user approval; do not start until approved.

## Verification results

| Check | Command | Result | Output |
| --- | --- | --- | --- |
| Focused behavioral tests | `python3 -m unittest discover -s tests -p 'test_*.py' -v` | PASS | [verification report](../../docs/reviews/2026-11-05-task-020-verification.md) |
| OpenCode adapter verifier | `python3 scripts/verify-opencode-adapter.py` | PASS | [verification report](../../docs/reviews/2026-11-05-task-020-verification.md) |
| Observability snapshot regression | `bun run scripts/verify-observability-snapshot.ts` | PASS | [verification report](../../docs/reviews/2026-11-05-task-020-verification.md) |

## Manager review

Supplemental independent MANAGER: Quality approval of the final gate
integration: `docs/reviews/2026-11-05-task-020-gate-review.md`. The full
implementation review is recorded in
`docs/reviews/2026-11-05-task-020-manager-review.md`; the first review and
resolution are preserved in the execution log.
