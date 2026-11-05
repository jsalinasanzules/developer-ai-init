# TASK-009 — Implement OpenCode adapter using verified current conventions

## Metadata
- Status: done
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
- [x] Current official docs are referenced with inspection date.
- [x] Role mapping is implemented or limitations documented.
- [x] Canonical memory remains in .blueprint/.
- [x] Existing config collision is detected and preserved.

## Verification plan
Run OpenCode config validation/startup smoke test where available; record exact version and commands.

## Risks and open questions
None recorded.

## Blockers
None recorded.

## Execution log
- 2026-11-04: Re-read TASK-009, SPEC-006, SPEC-007, ADR-006/007/008, the adapter architecture doc, the target-project layout, and the TASK-001 capability baseline.
- 2026-11-04: Revalidated official OpenCode V2 docs (`/v2/docs/config`, `/agents`, `/commands`, `/skills`, plus the permissions guide referenced from those pages); findings recorded with inspection date in `adapters/opencode/README.md` §1.
- 2026-11-04: Implemented adapter templates: `opencode.jsonc`, `AGENTS-TARGET.md`, six agent files (orchestrator, four managers, specialist), five workflow commands (`blueprint-startup`, `-next`, `-task`, `-handoff`, `-consolidate`).
- 2026-11-04: Documented role mapping, permissions, collision/preservation policy, limitations, sequential fallback, conformance report, and dual-context monitor compatibility notes in `adapters/opencode/README.md`.
- 2026-11-04: Added `scripts/verify-opencode-adapter.py`; fixed two issues it found (invalid trailing comma in the JSONC template; missing explicit escalation wording in the specialist agent).
- 2026-11-04: Ran the OpenCode 2.2.5 discovery smoke test in a simulated target project (`opencode debug config`, `opencode debug agents`) and a live non-interactive run of `/blueprint-next` through the `orchestrator` agent against a minimal `.blueprint/`; observed correct discovery and protocol behavior.
- 2026-11-04: Recorded dual-context monitor compatibility notes (Context A root-memory repo vs Context B `.blueprint/` projects) without implementing TASK-019.

## Completion evidence
- Dated official docs: `adapters/opencode/README.md` §1 (sources, inspection date 2026-11-04, OpenCode 2.2.5).
- Role mapping implemented/limitations: §3 (including ADR-007 depth rules) and §5 limitations.
- Canonical memory in `.blueprint/`: §8 plus the canonical-path discipline check in `scripts/verify-opencode-adapter.py` → `RESULT: PASS`.
- Collision detection and preservation: §7 policy table; the install/merge mechanics are approved scope for TASK-013 and are tracked there.
- Observed checks:
  - `./scripts/verify-opencode-adapter.py` → `RESULT: PASS`
  - `opencode --version` → `opencode v2.2.5`
  - `opencode debug config` → resolved project `opencode.jsonc` (`default_agent: orchestrator`) + project `.opencode/` directory
  - `opencode debug agents` → 6 adapter agents discovered with correct modes
  - live `opencode run --agent orchestrator --model opencode/glm-5.3-flash-free /blueprint-next` → orchestrator read the canonical records, selected the eligible task, and paused correctly asking one question when the brief lacked criteria (full output in the smoke session; excerpts in README §10)

## Next action
None. TASK-009 is done; TASK-010 is eligible (depends TASK-004, TASK-006, TASK-009).
