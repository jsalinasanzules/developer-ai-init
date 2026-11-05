---
description: Create or update a Blueprint handoff for cross-session continuation
agent: orchestrator
---

Create or refresh a Blueprint handoff for this work.

1. Read `.blueprint/memory/CURRENT_STATE.md`, `.blueprint/tasks/registry.json`, the
   active task brief, and recent `.blueprint/sessions/` and `.blueprint/handoffs/`
   records to determine what a fresh session genuinely needs.
2. Write a handoff at `.blueprint/handoffs/YYYY-MM-DD-<slug>.md` containing:
   repository state (branch, commit, working-tree status); active task (ID, title,
   status, specs, dependencies); completed work (verified outcomes only); files
   changed and purpose; verification evidence (commands and observed results, plus
   checks explicitly NOT run); acceptance-criterion evidence table; decisions and
   approvals (ADR IDs, approved scope, pending approvals); risks and blockers; memory
   updates; exact next action (one concrete step); and a cold-start checklist.
3. Every claim must be verifiable against current files and Git. Do not include
   conversation-history claims and do not include secrets.
4. Historical handoffs are append-only: create a new file rather than rewriting one.
5. Update `.blueprint/memory/CURRENT_STATE.md` to name the latest handoff and the
   exact next action, then report the handoff path to the user.

$ARGUMENTS
