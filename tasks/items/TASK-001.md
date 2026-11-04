# TASK-001 — Review foundation and approve core architecture

## Metadata
- Status: done
- Priority: critical
- Owner role: ORCHESTRATOR
- Specs: SPEC-001, SPEC-002, SPEC-003, SPEC-004, SPEC-005, SPEC-006
- Dependencies: None
- Created: 2026-11-04
- Updated: 2026-11-04

## Objective
Review the foundation scaffold, validate consistency across vision/architecture/specs, inspect current official OpenCode capabilities, and identify material unresolved decisions.

## Scope
Review repository files and Git state; compare requirements for contradictions; inspect current OpenCode official docs without implementing adapter.

## Out of scope
Do not implement later tasks or choose unresolved architecture decisions without user approval.

## Acceptance criteria
- [x] Foundation docs and specs are internally consistent.
- [x] OpenCode capability findings cite current official sources.
- [x] Conflicts, risks, and material decisions are listed for the user.
- [x] TASK-001 review report and memory updates are committed.

## Verification plan
Document review findings, run link/reference checks where available, and record exact source URLs and date for provider research.

## Risks and open questions
None recorded.

## Blockers
None recorded.

## Execution log
- 2026-11-04: Read AGENTS.md, README, all architecture docs, all nine specs, memory records, registry, backlog, templates, task briefs, and the prior handoff.
- 2026-11-04: Verified registry JSON, dependency graph, task-file metadata, and relative Markdown links with local scripts.
- 2026-11-04: Inspected official OpenCode V1 and V2 documentation; observed local `opencode v2.2.5`.
- 2026-11-04: Corrected stale README/current-state statements, added the missing blocker field to the task template, aligned spec/README wording, and created the review report.
- 2026-11-04: Recorded MD-001 (OpenCode baseline) and MD-002 (hierarchy delegation) as approval gates.
- 2026-11-04: User approved MD-001 as V2-native first and MD-002 as depth-2 opt-in with sequential fallback. Recorded ADR-006 and ADR-007; marked TASK-001 done.

## Completion evidence
- Foundation consistency, OpenCode findings, risks, and decisions: [docs/reviews/2026-11-04-task-001-foundation-review.md](../../docs/reviews/2026-11-04-task-001-foundation-review.md).
- JSON/link/dependency checks: reported in §2.1 and §8 of the review.
- Official sources and access date: §2.2 of the review (2026-11-04).
- Local provider version: `opencode --version` → `opencode v2.2.5`.
- User approvals: MD-001 = V2-native first; MD-002 = depth-2 opt-in with sequential fallback.
- Approved decisions: `memory/DECISIONS.md` ADR-006 and ADR-007.

## Next action
None. TASK-001 is done; TASK-002 is the next eligible task.
