# TASK-014 — Implement validation for schemas, task graph, references, and secrets

## Metadata
- Status: done
- Priority: high
- Owner role: MANAGER: Quality
- Specs: SPEC-009, SPEC-002, SPEC-005
- Dependencies: TASK-003, TASK-006, TASK-011, TASK-020
- Created: 2026-11-04
- Updated: 2026-11-05

## Objective
Implement local validation for canonical records and adapter artifacts.

## Scope
Implement a read-only, offline validator for the source repository's canonical
records, JSON/JSONC adapter configuration, schemas, references, dependency
graph, record synchronization, and secret-like values. Use Python 3.9+ with
the pinned `jsonschema` dependency approved in ADR-011. Reject remote schema
references; generated projects must not acquire Python files or requirements.

## Out of scope
Do not print detected secret values or mutate project files during validation.

## Acceptance criteria
- [x] JSON and JSONC files are parsed without mutation; invalid Draft 2019-09 schemas and schema-invalid instances report actionable file and field paths without exposing values.
- [x] Registry semantics validate required fields/types, unique task IDs, existing task/spec references, and an acyclic dependency graph.
- [x] Registry and task briefs agree on title, status, owner, specifications, and dependencies; the backlog contains every task once with matching status; CURRENT_STATE matches the active task.
- [x] Secret-like values in the documented canonical and adapter-template scan scope are reported with file/field locations and pattern labels only; diagnostic output never contains the matched value.
- [x] Adapter manifest sources and destinations are checked safely and without network access.
- [x] The complete validation command works offline, reports errors separately from warnings, and does not modify project files.

## Verification plan
Run positive and negative tests for valid/invalid schemas and instances,
malformed JSON/JSONC, missing references, duplicate IDs, dependency cycles,
canonical-record drift, secret redaction, adapter manifest paths, offline
execution, and read-only behavior. Run fixture verification, the full Python
suite, existing adapter/role/memory/observability verifiers, and
`git diff --check`.

## Risks and open questions
- Secret detection is heuristic and may produce false positives or miss novel
  credential formats. Diagnostics must never print values; findings require
  human review.
- Only local `$ref` values are permitted to guarantee offline validation.
- `jsonschema` is a source-repository validation dependency and must be
  provisioned before offline use; it is not installed into generated projects.

## Blockers
None recorded.

## Execution log
- 2026-11-05: Verified dependencies TASK-003, TASK-006, TASK-011, and TASK-020 are `done`. User approved Python 3.9+ with a pinned `jsonschema` dependency for offline-capable Draft 2019-09 validation; recorded ADR-011 and transitioned `proposed → ready → in_progress`.
- 2026-11-05: Reconciled the stale TASK-013 completion-gate text in CURRENT_STATE while selecting TASK-014 as active. Preserved pre-existing monitor and `.opencode/` changes.
- 2026-11-05: Implemented the read-only offline validator, schema/fixture checks, task graph and record consistency checks, JSONC adapter validation, safe manifest path checks, and redacted secret scanning. Added focused behavioral tests and source-only documentation.
- 2026-11-05: Resolved the memory fixture schema mapping and aligned active-task validation with the official `in_review` completion-gate state. Updated the observability regression's latest-ADR expectation to ADR-011; no monitor implementation files were changed.
- 2026-11-05: Focused validation tests passed 14/14; full Python suite passed 67/67; fixture, complete Blueprint, adapter, role, memory, observability, and whitespace verifiers passed. Independent MANAGER: Quality review approved; see `../../docs/reviews/2026-11-05-task-014-manager-review.md`. Verification evidence: `../../docs/reviews/2026-11-05-task-014-verification.md`.

## Completion evidence

| Criterion | Acceptance criterion | Behavioral evidence |
| --- | --- | --- |
| AC-01 | JSON and JSONC files are parsed without mutation; invalid Draft 2019-09 schemas and schema-invalid instances report actionable file and field paths without exposing values. | `test_invalid_schema_reports_schema_location_without_schema_value`, `test_invalid_instance_reports_file_and_field_without_value`, `test_missing_required_field_is_named_without_printing_instance_values`, and `test_jsonc_syntax_errors_are_actionable` in [the validator tests](../../tests/test_blueprint_validation.py). |
| AC-02 | Registry semantics validate required fields/types, unique task IDs, existing task/spec references, and an acyclic dependency graph. | `test_missing_required_field_is_named_without_printing_instance_values`, `test_duplicate_task_ids_are_rejected`, `test_missing_task_and_spec_references_are_reported`, and `test_dependency_cycle_is_detected` in [the validator tests](../../tests/test_blueprint_validation.py). |
| AC-03 | Registry and task briefs agree on title, status, owner, specifications, and dependencies; the backlog contains every task once with matching status; CURRENT_STATE matches the active task. | `test_backlog_and_current_state_drift_are_reported` and `test_in_review_task_remains_the_active_task` in [the validator tests](../../tests/test_blueprint_validation.py). |
| AC-04 | Secret-like values in the documented canonical and adapter-template scan scope are reported with file/field locations and pattern labels only; diagnostic output never contains the matched value. | `test_secret_diagnostics_redact_values` in [the validator tests](../../tests/test_blueprint_validation.py). |
| AC-05 | Adapter manifest sources and destinations are checked safely and without network access. | `test_adapter_manifest_rejects_unsafe_and_duplicate_destinations` and `test_external_schema_reference_is_rejected_without_fetching` in [the validator tests](../../tests/test_blueprint_validation.py). |
| AC-06 | The complete validation command works offline, reports errors separately from warnings, and does not modify project files. | `test_repository_fixture_is_valid_and_validation_is_read_only` and `test_external_schema_reference_is_rejected_without_fetching` in [the validator tests](../../tests/test_blueprint_validation.py); the complete command and fixture verifier report `0` errors and `0` warnings in the [verification report](../../docs/reviews/2026-11-05-task-014-verification.md). |

## Next action
Present TASK-015 proposal for user approval; do not start until approved.

## Verification results

| Check | Command | Result | Output |
| --- | --- | --- | --- |
| Focused validation tests | `python3 -B -m unittest discover -s tests -p 'test_blueprint_validation.py' -v` | PASS | [verification report](../../docs/reviews/2026-11-05-task-014-verification.md) |
| Full Python test suite | `python3 -B -m unittest discover -s tests -v` | PASS | [verification report](../../docs/reviews/2026-11-05-task-014-verification.md) |
| Schema fixture validation | `./schemas/verify-fixtures.sh` | PASS | [verification report](../../docs/reviews/2026-11-05-task-014-verification.md) |
| Complete offline Blueprint validation | `python3 -B scripts/validate_blueprint.py --root .` | PASS | [verification report](../../docs/reviews/2026-11-05-task-014-verification.md) |
| OpenCode adapter verifier | `python3 -B scripts/verify-opencode-adapter.py` | PASS | [verification report](../../docs/reviews/2026-11-05-task-014-verification.md) |
| Role contract verifier | `python3 -B scripts/verify-role-contracts.py` | PASS | [verification report](../../docs/reviews/2026-11-05-task-014-verification.md) |
| Memory consolidation verifier | `python3 -B scripts/verify-memory-consolidation.py` | PASS | [verification report](../../docs/reviews/2026-11-05-task-014-verification.md) |
| Observability snapshot regression | `bun run scripts/verify-observability-snapshot.ts` | PASS | [verification report](../../docs/reviews/2026-11-05-task-014-verification.md) |
| Whitespace validation | `git diff --check` | PASS | [verification report](../../docs/reviews/2026-11-05-task-014-verification.md) |

## Manager review

Independent MANAGER: Quality review approved the implementation and evidence.
See `docs/reviews/2026-11-05-task-014-manager-review.md`.
