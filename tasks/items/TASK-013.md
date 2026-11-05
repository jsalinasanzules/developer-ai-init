# TASK-013 — Implement blueprint generation with collision detection and approval

## Metadata
- Status: done
- Priority: high
- Owner role: MANAGER: Engineering
- Specs: SPEC-001, SPEC-008
- Dependencies: TASK-003, TASK-009, TASK-012, TASK-020
- Created: 2026-11-04
- Updated: 2026-11-05

## Objective
Implement the initializer that creates canonical memory, tasks, specs, and selected adapter configuration.

## Scope
Implement a source-repository-only Python 3.9+ standard-library generator that
consumes confirmed project data, generates the canonical `.blueprint/` tree,
and optionally plans provider-native adapter files. Keep generated projects
free of Python helpers and runtime requirements. The Orchestrator retains
TASK-012's interview and user-approval responsibilities.

## Out of scope
Do not silently replace files or force a specific stack into target projects.

## Acceptance criteria
- [x] Generates the agreed canonical `.blueprint/` tree from confirmed input and selected adapters without copying this repository's development state.
- [x] Previews every destination as `CREATE`, `MERGE`, `SKIP`, or `CONFLICT` without writes; summary confirmation, full-plan approval, and exact-path conflict overwrite approval remain distinct.
- [x] Preserves user-owned and unknown files; unsafe paths, symlinks, unsupported existing manifests, and unresolved conflicts block writes; no approved overwrite can affect an unapproved path.
- [x] Records Blueprint/schema versions and managed-file hashes in a final manifest written only after generated content is applied and verified.
- [x] Greenfield and brownfield generation are idempotent; a second unchanged run reports `SKIP`.
- [x] Generated project contents contain no Python helper, invocation, or Python runtime requirement.

## Verification plan
Use temporary greenfield and brownfield targets. Exercise every preview
outcome; approved and unapproved exact-path conflicts; user-content
preservation; unknown/versioned manifest handling; path/symlink containment;
manifest hashes and seal ordering; failure reporting; unchanged reruns; and
absence of Python helpers/invocations in generated contents. Run focused tests,
the complete Python suite, OpenCode adapter and observability verifiers, and
`git diff --check`.

## Risks and open questions
- Blueprint release `0.1.0` is now defined once in `blueprint/catalog.json`; schema version `1.0.0` remains sourced from the schemas. Future template/behavior changes require an explicit Blueprint version increment.
- Multi-file writes are not a filesystem-wide transaction. The generator revalidates the preview, reports exact partial results, and writes the manifest last without destructive rollback.
- Standalone distribution for hosts without Python is outside the approved source-only tooling decision.

## Blockers
None recorded.

## Execution log
- 2026-11-05: User approved Python 3.9+ standard-library tooling for TASK-013, explicitly limited to Developer AI Init; generated projects must not need Python.
- 2026-11-05: Verified dependencies TASK-003, TASK-009, TASK-012, and TASK-020 are all `done`; no other task is `in_progress`. Recorded ADR-010 and transitioned `proposed → ready → in_progress`.
- 2026-11-05: Began a catalog-driven, provider-neutral generator design based on TASK-012's confirmed-input and approval gates and TASK-020's safe-regeneration behavior.
- 2026-11-05: Implemented the catalog-driven source-only generator, canonical templates, optional selected-adapter planning, summary/plan/exact-path approval gates, safe atomic writes, and manifest-last verification.
- 2026-11-05: Added behavioral coverage for all four outcomes, greenfield/brownfield idempotence, approvals, unknown/versioned manifests, symlinks, partial failures, version/hash sealing, and the no-Python target boundary.
- 2026-11-05: Independent Manager review requested changes because Windows junctions/reparse points were not rejected in the path-based write fallback. The finding and its original scope are recorded in `../../docs/reviews/2026-11-05-task-013-manager-review.md`.
- 2026-11-05: Added `lstat`-based reparse-point detection to planning and the path-based write fallback, with regression coverage simulating `FILE_ATTRIBUTE_REPARSE_POINT`. Focused generation tests passed 21/21; full Python suite passed 53 tests, and adapter, role, memory, observability, compilation, and whitespace checks passed. Evidence: `../../docs/reviews/2026-11-05-task-013-verification.md`.
- 2026-11-05: Independent follow-up review approved the corrected reparse-point handling. Approval is recorded in `../../docs/reviews/2026-11-05-task-013-manager-review-follow-up.md`; run the lifecycle completion gate before any `done` transition.

## Completion evidence

| Criterion | Criterion text | Behavioral evidence |
| --- | --- | --- |
| AC-01 | Generates the agreed canonical `.blueprint/` tree from confirmed input and selected adapters without copying this repository's development state. | `test_greenfield_plan_is_non_mutating_and_covers_canonical_tree`, `test_brownfield_classification_preserves_existing_project_files`, `test_generated_tree_uses_confirmed_values_without_source_development_state`, and `test_selected_opencode_adapter_is_planned_and_generated_separately` in [the generation tests](../../tests/test_blueprint_generation.py). |
| AC-02 | Previews every destination as `CREATE`, `MERGE`, `SKIP`, or `CONFLICT` without writes; summary confirmation, full-plan approval, and exact-path conflict overwrite approval remain distinct. | `test_cli_requires_summary_confirmation_then_exact_plan_approval`, `test_all_outcomes_and_exact_path_overwrite_are_enforced`, and `test_adapter_conflict_uses_exact_path_approval_in_the_combined_plan` in [the generation tests](../../tests/test_blueprint_generation.py). |
| AC-03 | Preserves user-owned and unknown files; unsafe paths, symlinks, unsupported existing manifests, and unresolved conflicts block writes; no approved overwrite can affect an unapproved path. | `test_untracked_files_and_manifest_paths_are_preserved_and_reported`, `test_unknown_manifest_records_are_preserved_but_missing_ones_block`, `test_unsupported_or_malformed_manifest_blocks_before_writes`, `test_symlink_collision_is_not_overwritable`, `test_windows_reparse_point_ancestor_blocks_planning_and_fallback_write`, `test_unsafe_relative_paths_are_rejected`, and the exact-path tests in [the generation tests](../../tests/test_blueprint_generation.py). |
| AC-04 | Records Blueprint/schema versions and managed-file hashes in a final manifest written only after generated content is applied and verified. | `test_generated_manifest_hashes_and_schema_versions_are_sealed_last` and `test_unknown_manifest_records_are_preserved_but_missing_ones_block` in [the generation tests](../../tests/test_blueprint_generation.py). |
| AC-05 | Greenfield and brownfield generation are idempotent; a second unchanged run reports `SKIP`. | `test_brownfield_classification_preserves_existing_project_files`, `test_unchanged_regeneration_is_idempotent_even_after_date_change`, and `test_second_run_reports_only_skip_and_manifest_is_not_rewritten` in [the generation tests](../../tests/test_blueprint_generation.py). |
| AC-06 | Generated project contents contain no Python helper, invocation, or Python runtime requirement. | `test_generated_project_has_no_python_runtime_or_blueprint_source_files` in [the generation tests](../../tests/test_blueprint_generation.py). |

## Verification results

| Check | Command | Result | Output |
| --- | --- | --- | --- |
| Full Python test suite | `python3 -m unittest discover -s tests -v` | PASS | [verification report](../../docs/reviews/2026-11-05-task-013-verification.md) |
| OpenCode adapter verifier | `python3 scripts/verify-opencode-adapter.py` | PASS | [verification report](../../docs/reviews/2026-11-05-task-013-verification.md) |
| Role contract verifier | `python3 scripts/verify-role-contracts.py` | PASS | [verification report](../../docs/reviews/2026-11-05-task-013-verification.md) |
| Memory consolidation verifier | `python3 scripts/verify-memory-consolidation.py` | PASS | [verification report](../../docs/reviews/2026-11-05-task-013-verification.md) |
| Observability snapshot regression | `bun run scripts/verify-observability-snapshot.ts` | PASS | [verification report](../../docs/reviews/2026-11-05-task-013-verification.md) |
| Python compilation | `python3 -m py_compile scripts/build_blueprint.py tests/test_blueprint_generation.py` | PASS | [verification report](../../docs/reviews/2026-11-05-task-013-verification.md) |
| Whitespace validation | `git diff --check` | PASS | [verification report](../../docs/reviews/2026-11-05-task-013-verification.md) |

## Manager review

The follow-up review approved the corrected implementation. See
`docs/reviews/2026-11-05-task-013-manager-review-follow-up.md`; the first
review and its finding are recorded in
`docs/reviews/2026-11-05-task-013-manager-review.md`. The repository
completion gate accepted the evidence and synchronized TASK-013 as `done`.

## Next action
Present TASK-014 for user approval; do not start TASK-014.
