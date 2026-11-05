---
description: Review proposed memory updates and consolidate them into canonical records
agent: orchestrator
---

Consolidate pending Blueprint memory proposals into canonical records.

1. Gather proposals from the active task brief's execution log, recent
   `.blueprint/sessions/` records, and any specialist or manager returns in this
   session that proposed durable facts.
2. For each proposal, identify the owning record using the ownership map
   (`.blueprint/memory/` records for context/state/architecture/decisions/
   conventions; `.blueprint/tasks/registry.json` for status; task briefs for task
   scope and evidence).
3. Validate: the proposal must carry evidence and the record's current content hash
   (read the file now). Reject stale bases by re-deriving the proposal against the
   current content.
4. Reconcile concurrent changes semantically, never by timestamp: merge disjoint
   facts, drop exact duplicates, and stop on conflicting values for the same fact.
   If the conflict is material, ask the user with sources, impacts, and options.
   Never use last-write-wins for decisions or task state, and never rewrite
   `DECISIONS.md`; supersede with a new ADR linked to the old one.
5. Write accepted changes to the owning record only, then synchronize projections
   (`.blueprint/memory/CURRENT_STATE.md`, `.blueprint/tasks/backlog.md`) and record
   provenance in the task brief or session record (who proposed, which task, what
   evidence, who reviewed, what replaced what).
6. No secrets in memory. Commit with a descriptive message.

Report what was applied, rejected, or escalated and why.

$ARGUMENTS
