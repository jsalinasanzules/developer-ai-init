# SPEC-007 — OpenCode Adapter

## Purpose
Make OpenCode the first provider integration without coupling the core blueprint to OpenCode.

## Requirements
- OC-001: Inspect current official OpenCode documentation and supported configuration formats before implementation.
- OC-002: Map Orchestrator, Manager, and Specialist responsibilities to supported OpenCode constructs.
- OC-003: Provide a startup instruction that loads canonical `.blueprint/` memory.
- OC-004: Provide task execution and handoff workflows using supported commands/skills/configuration.
- OC-005: Preserve the Orchestrator as the sole user-facing role by explicit instructions and routing conventions.
- OC-006: Document any unsupported hierarchy behavior and safe sequential fallback.
- OC-007: Do not overwrite existing OpenCode configuration without collision detection and approval.
- OC-008: Verify a fresh OpenCode session can resume from files alone.

## Implementation constraint
Do not assume config paths, schema keys, or agent capabilities. Verify against current official docs during implementation and cite/version the findings in adapter documentation.

## Acceptance criteria
A clean target project can install the adapter, load memory, identify a ready task, and produce a verified handoff without relying on prior chat.
