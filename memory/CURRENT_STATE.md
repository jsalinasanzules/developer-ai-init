# Current State

- Date: 2026-11-04
- Stage: foundation baseline reviewed; awaiting two material provider decisions before adapter work.
- Repository: `jsalinasanzules/developer-ai-init`, public, default branch `main`.
- Personal GitHub read/write access verified.
- The foundation, nine specifications, eighteen task briefs, memory records, templates, and registry are committed.
- TASK-001 review is complete and recorded in `docs/reviews/2026-11-04-task-001-foundation-review.md`.

## Active task
**TASK-001 — Review foundation and approve core architecture**
- Status: `in_review`
- Review evidence: `docs/reviews/2026-11-04-task-001-foundation-review.md`
- Next action: user approval for MD-001 and MD-002.

## Pending approvals
- **MD-001 — OpenCode generation baseline:** recommend V2-native first, with documented V1 limitations and portable Markdown commands/skills where practical.
- **MD-002 — Hierarchy delegation:** recommend enabling depth 2 as an opt-in adapter setting, documented as experimental in OpenCode V2, with a sequential fallback.
- **MD-003 — Initializer/validator implementation stack:** deferred until TASK-012/TASK-013; no approval needed to start TASK-002.

## Verified constraints
- No mandatory database.
- Canonical memory remains provider-independent and Git-native.
- Do not implement every phase automatically.
- Ask about conflicts and material decisions.
- Done requires observable verification evidence.
- OpenCode 1 and OpenCode 2 share the `opencode` command; this environment runs `v2.2.5`.
- OpenCode's default subagent depth is `1`; true Orchestrator → Manager → Specialist delegation requires depth `2` (experimental in V2) or a documented fallback.

## Blockers
None technical. Progress past TASK-001 requires the MD-001 and MD-002 approvals recorded above.

## Next
After approval: record the decisions, mark TASK-001 `done`, and start TASK-002 (target-project directory and file ownership).
