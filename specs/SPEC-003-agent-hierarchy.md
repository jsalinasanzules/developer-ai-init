# SPEC-003 — Agent Hierarchy and Roles

## Model
`USER → ORCHESTRATOR → MANAGERS → SPECIALISTS`.

## Requirements
- AGENT-001: The Orchestrator MUST be the only user-facing agent.
- AGENT-002: The Orchestrator MUST retain accountability for delegated work.
- AGENT-003: Managers MUST coordinate bounded domains and review specialist results.
- AGENT-004: Specialists MUST receive explicit scope, context, constraints, and acceptance criteria.
- AGENT-005: Specialists MUST report evidence, risks, and proposed memory changes.
- AGENT-006: Specialists MUST NOT independently approve material product/architecture/security decisions.
- AGENT-007: Roles MUST remain logical and portable; adapters may map them to native constructs.
- AGENT-008: The baseline MUST support sequential execution when provider delegation is unavailable.

## Acceptance criteria
Role responsibilities, delegation payload, escalation path, and provider mapping boundaries are documented.
