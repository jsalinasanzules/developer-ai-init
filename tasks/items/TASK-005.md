# TASK-005 — Define decision log, conflict detection, and approval workflow

## Metadata
- Status: done
- Priority: high
- Owner role: MANAGER: Architecture
- Specs: SPEC-004, SPEC-002
- Dependencies: TASK-004
- Created: 2026-11-04
- Updated: 2026-11-04

## Objective
Formalize how the Orchestrator detects instruction conflicts and requests user decisions.

## Scope
Define conflict categories, severity, response format, approval record, expiry/reconsideration, and decision supersession.

## Out of scope
Do not resolve existing unresolved decisions on behalf of the user.

## Acceptance criteria
- [x] Conflict sources and impacts are shown.
- [x] Material decisions pause execution.
- [x] Approval is explicit and attributable to user intent.
- [x] Decisions are persisted with rationale and consequences.

## Verification plan
Test scenarios for conflicting specs, ambiguous user request, security-impacting change, and destructive action.

## Execution log
- 2026-11-04: Re-read SPEC-004, SPEC-002, ADR-005, the memory protocol, and the agent hierarchy.
- 2026-11-04: Defined conflict types, S0–S3 severity, detection triggers, the conflict/approval packet, the approval workflow, attribution rules, decision format, expiry/reconsideration, and supersession in `docs/architecture/decision-and-approval-protocol.md`.
- 2026-11-04: Added scenario tests for conflicting specs, ambiguity, security impact, destructive action, and an ordinary S3 decision.
- 2026-11-04: Linked the protocol from `memory/DECISIONS.md`, the README, and the agent hierarchy escalation path.

## Completion evidence
- Sources, impacts, options, recommendation, and one-question approval packet: §5 of [decision-and-approval-protocol.md](../../docs/architecture/decision-and-approval-protocol.md).
- Material decision pause behavior: §3.2 and §6.
- Explicit attribution: §6.1 and the `Approval` field in §7.
- Persisted rationale/consequences: §7; expiry and supersession: §8.
- Required scenario coverage: §10.1–§10.4, plus an ordinary S3 case in §10.5.
- Link and JSON checks run after the documentation changes.

## Next action
None. TASK-005 is done; TASK-006 and TASK-007 are eligible.
