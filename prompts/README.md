# Provider-Neutral Role Prompt Templates

These templates implement the role contracts in `docs/architecture/agent-hierarchy.md`. They are source artifacts for adapters, not canonical target-project memory.

## Files

| File | Role |
| --- | --- |
| `orchestrator.md` | Sole user-facing role: startup, classification, planning, delegation, validation, approval, consolidation. |
| `manager.md` | Domain coordination, decomposition, specialist review, reporting. |
| `specialist.md` | Bounded execution and evidence-backed return. |
| `delegation-payload.md` | Copyable delegation, return, and review structures. |

## Rules

- Keep authority boundaries intact when translating to a provider format.
- Do not embed project facts or secrets in templates; load them from `.blueprint/`.
- If a provider cannot run nested agents, use the sequential fallback in `agent-hierarchy.md` §8.
- Adapters may change wording and structure but must preserve the invariants B-01–B-10.
