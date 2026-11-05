# TASK-011 Acceptance Audit Correction

- Date: 2026-11-05
- Subject: TASK-011 — Add adapter conformance and safe regeneration behavior
- Status: Historical `done` transition preserved; acceptance not demonstrated.

## Finding

The original TASK-011 completion evidence did not satisfy its functional
acceptance criteria. The changes cited by the task added manifest parsing and
presentation fields to the OpenCode Blueprint monitor. Those fields described
conformance and regeneration-safety declarations; they did not perform adapter
file generation, detect destination collisions before writes, preview concrete
create/merge/skip/conflict outcomes, obtain overwrite approval, or prove
idempotent regeneration.

The cited snapshot and adapter-structure checks verified presentation and
template shape, not those missing runtime behaviors. The source project also
had no adapter manifest at the location consumed by the monitor, so the monitor
could not supply operational evidence for the claimed generation behavior.

## Correction

This audit records the discrepancy without deleting or rewriting TASK-011's
historical `done` status or its original completion entry. Its original
acceptance claim must not be used as evidence that safe regeneration or adapter
conformance was implemented.

TASK-020 is the corrective task. It implements and behaviorally tests safe
OpenCode adapter regeneration and adds an executable completion gate with
negative tests. Downstream work that relied on TASK-011's missing functionality
also depends on TASK-020. TASK-011 remains `done` as a historical lifecycle
fact; TASK-020 is the authoritative evidence for the repaired behavior.

## Evidence basis

- The original TASK-011 brief and registry entry are preserved at
  `tasks/items/TASK-011.md` and `tasks/registry.json`.
- The existing monitor code reads and presents status; it does not write
  generated adapter files.
- The adapter's own README describes installation and regeneration mechanics
  as future initializer work; no generator or installed adapter manifest was
  present in the inspected repository state.
- The working tree contained uncommitted monitor and task-record changes at
  audit time. Those changes are not treated as independent behavior evidence.
