# TASK-012 initial independent Architecture Manager review

Date: 2026-11-05

Task: TASK-012  
Reviewer role: MANAGER: Architecture  
Independent review: YES  
Decision: CHANGES REQUESTED

## Acceptance criteria

- **AC-01 — PASS.** Greenfield, brownfield, already-initialized, and
  reconciliation flows are specified with concrete scenarios.
- **AC-02 — PARTIAL.** Unknowns, evidence, assumptions, and blocking questions
  are addressed, but their handling was not fully reconciled with
  schema-required fields.
- **AC-03 — PASS.** Summary confirmation and separate write-plan approval are
  explicit gates.
- **AC-04 — PASS.** All four preview outcomes, exact-path overwrite approval,
  and blocking all writes for unresolved conflicts are specified.

## Findings

1. `target-project-layout.md` described a `scope` property in `project.json`,
   but `schemas/project.schema.json` disallows additional properties and has no
   such field. The intake also collects scope and success criteria without
   identifying their canonical destination.
2. The required project identity/status and purpose-summary fields had no
   explicit unknown/blocking mapping. Array-valued fields needed to distinguish
   confirmed empty values from unresolved unknowns.
3. Cancellation, resumption, evidence sourcing, and TASK-020 conflict/approval
   protections were otherwise clearly specified. No runtime initializer is
   claimed; the tests check the documented design contract rather than runtime
   behavior.

## Verification reviewed

- Reviewed the TASK-012 task, linked specifications, initialization protocol,
  target layout, project schema, regeneration implementation, scenario tests,
  and verification report.
- `python3 -m unittest discover -s tests -p 'test_initialization_spec.py' -v`
  passed six static scenario-contract tests. Other recorded regression results
  were reviewed from the verification report, not independently rerun.

## Required resolution

- Map scope, architecture, conventions, and success criteria to existing
  canonical records without introducing unsupported schema fields.
- State which unknown required scalars block a schema-valid project config.
- Define how unknown array-valued data differs from confirmed-empty arrays.
