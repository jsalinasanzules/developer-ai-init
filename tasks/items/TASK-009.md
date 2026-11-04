# TASK-009 — Implement OpenCode adapter using verified current conventions

## Metadata
- Status: proposed
- Priority: high
- Owner role: MANAGER: Engineering
- Specs: SPEC-006, SPEC-007
- Dependencies: TASK-002, TASK-008
- Created: 2026-11-04
- Updated: 2026-11-04

## Objective
Map provider-neutral roles and workflows to current OpenCode-supported configuration.

## Scope
Inspect official docs; implement adapter manifest, agent definitions, and non-destructive configuration integration.

## Out of scope
Do not assume config paths/schema; do not overwrite existing OpenCode config.

## Acceptance criteria
- [ ] Current official docs are referenced with inspection date.
- [ ] Role mapping is implemented or limitations documented.
- [ ] Canonical memory remains in .blueprint/.
- [ ] Existing config collision is detected and preserved.

## Verification plan
Run OpenCode config validation/startup smoke test where available; record exact version and commands.

## Risks and open questions
None recorded.

## Blockers
None recorded.

## Execution log
No execution recorded yet.

## Completion evidence
Pending.

## Next action
Wait until all dependencies are verified done; then re-read the linked specs and confirm scope.
