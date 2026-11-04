# SPEC-004 — Orchestration and Conflict Resolution

## Purpose
Define how user requests are classified, work is planned, conflicts are surfaced, and approvals are obtained.

## Requirements
- ORCH-001: The Orchestrator MUST load relevant persistent context before planning.
- ORCH-002: The Orchestrator MUST classify requests as project initialization, new task, continuation, change request, question, or incident.
- ORCH-003: Conflicting instructions MUST be identified and presented to the user with the source and impact of each interpretation.
- ORCH-004: Material decisions MUST pause execution until explicit user approval.
- ORCH-005: Ordinary implementation details may be decided within approved scope and documented conventions.
- ORCH-006: Destructive, irreversible, security-sensitive, privacy-sensitive, or scope-expanding actions MUST require approval.
- ORCH-007: The Orchestrator MUST validate delegated results against specs and acceptance criteria.
- ORCH-008: The Orchestrator MUST consolidate approved durable knowledge.

## Conflict response
State the conflicting statements, their sources, consequences of each option, a recommended option with rationale (if evidence supports one), and ask one explicit approval question. Do not proceed with the contested change before approval.
