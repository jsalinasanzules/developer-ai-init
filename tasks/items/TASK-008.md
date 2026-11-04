# TASK-008 — Specify Orchestrator, Manager, and Specialist contracts

## Metadata
- Status: done
- Priority: high
- Owner role: MANAGER: Architecture
- Specs: SPEC-003, SPEC-004
- Dependencies: TASK-001, TASK-005
- Created: 2026-11-04
- Updated: 2026-11-04

## Objective
Define role responsibilities, prompt contracts, delegation payload, review criteria, and escalation routes.

## Scope
Create role descriptions and reusable prompt templates.

## Out of scope
Do not assume every provider supports parallel subagents.

## Acceptance criteria
- [x] Orchestrator remains sole user-facing role.
- [x] Manager and Specialist boundaries are testable.
- [x] Delegations include scope, constraints, dependencies, outputs, acceptance criteria.
- [x] Sequential fallback is documented.

## Verification plan
Review sample delegated task end-to-end and ensure no authority boundary is violated.

## Risks and open questions
None recorded.

## Blockers
None recorded.

## Execution log
- 2026-11-04: Re-read SPEC-003, SPEC-004, the decision/approval protocol, the memory consolidation protocol, and the existing hierarchy summary.
- 2026-11-04: Expanded `docs/architecture/agent-hierarchy.md` with testable invariants (B-01–B-10), full role contracts, delegation/return/review payloads, escalation routes, sequential fallback, provider mapping boundaries, and an end-to-end sample.
- 2026-11-04: Added provider-neutral prompt templates under `prompts/` for the Orchestrator, Manager, Specialist, and payloads.
- 2026-11-04: Added `scripts/verify-role-contracts.py` and ran it; all structural and boundary checks pass.

## Completion evidence
- Sole user-facing Orchestrator: B-01; role prohibitions; escalation table; `prompts/orchestrator.md`.
- Testable Manager/Specialist boundaries: B-02–B-06 and B-10; §5.3 review criteria; `prompts/manager.md`, `prompts/specialist.md`.
- Complete delegation payload: §4 fields and rules; `prompts/delegation-payload.md`.
- Sequential fallback: §8 sequence, rules, and capability matrix; §11 sample.
- Provider-neutral mapping: §9; SPEC-003 AGENT-007/AGENT-008.
- Observed checks:
  - `./scripts/verify-role-contracts.py` → `RESULT: PASS` (33/33 checks).
  - `./scripts/verify-memory-consolidation.py` → `RESULT: PASS` (regression).
  - `./schemas/verify-fixtures.sh` → `Fixtures: 15 passed, 0 failed`.

## Next action
None. TASK-008 is done; TASK-009 is now eligible.
