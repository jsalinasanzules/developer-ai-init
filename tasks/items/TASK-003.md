# TASK-003 — Define JSON schemas for project, agent, task, and memory metadata

## Metadata
- Status: done
- Priority: high
- Owner role: MANAGER: Architecture
- Specs: SPEC-001, SPEC-002, SPEC-005
- Dependencies: TASK-002
- Created: 2026-11-04
- Updated: 2026-11-04

## Objective
Define versioned machine-readable contracts for project config, agent roles, task registry entries, and memory metadata.

## Scope
Draft schemas and representative valid/invalid fixtures.

## Out of scope
Do not select validation runtime/tooling without documenting tradeoffs and approval if material.

## Acceptance criteria
- [x] Schemas are versioned.
- [x] Required fields and enums are explicit.
- [x] Cross-reference rules are documented separately where JSON Schema cannot express them.
- [x] Example fixtures cover valid and invalid cases.

## Verification plan
Validate fixtures with a documented JSON Schema validator; record version and output.

## Risks and open questions
None recorded.

## Blockers
None recorded.

## Execution log
- 2026-11-04: Re-read SPEC-001, SPEC-002, SPEC-005, and the target-project layout.
- 2026-11-04: Added five versioned draft 2019-09 schemas under `schemas/`: manifest, project, agents, memory metadata, task registry.
- 2026-11-04: Added ten invalid fixtures targeting specific schema failures and five valid fixtures.
- 2026-11-04: Documented versioning policy, cross-reference/semantic rules, and fixture expectations in `schemas/README.md`.
- 2026-11-04: Verified fixtures with `ajv-cli` (draft 2019-09): 15 passed, 0 failed.
- 2026-11-04: Validated the live `tasks/registry.json` against `task-registry.schema.json`: valid.

## Completion evidence
- Schemas: `schemas/*.schema.json` with `$id` and `schema_version` `1.0.0`.
- Explicit required fields and enums: each schema's `required` and `enum` declarations.
- Cross-reference rules: `schemas/README.md` §Cross-reference and semantic rules (R-TASK, R-ROLE, R-PROJ, R-MEM, R-MAN, R-GLOBAL).
- Fixtures: `schemas/fixtures/valid/` and `schemas/fixtures/invalid/`.
- Verification command: `./schemas/verify-fixtures.sh`.
- Observed output: `Fixtures: 15 passed, 0 failed` (ajv-cli, draft 2019-09).
- Live registry check: `tasks/registry.json valid`.

## Next action
None. TASK-003 is done; TASK-004 and TASK-006 are eligible, subject to priority and the single-task rule.
