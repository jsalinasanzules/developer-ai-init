# SPEC-009 — Validation and Conformance

## Requirements
- VAL-001: Validate JSON files against versioned schemas.
- VAL-002: Validate task IDs, statuses, required fields, dependencies, and acyclic task graph.
- VAL-003: Validate internal links/references where practical.
- VAL-004: Detect secret-like values in canonical memory and generated files without printing secrets.
- VAL-005: Validate adapter manifests and generated-path collision behavior.
- VAL-006: Provide a fresh-session continuity scenario.
- VAL-007: Report warnings separately from blocking errors.
- VAL-008: Validation MUST be runnable locally without a hosted service.

## Acceptance criteria
A documented validation command/approach and conformance scenarios exist; errors are actionable and do not mutate project state.
