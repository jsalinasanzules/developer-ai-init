# Provider-Neutral Observability Contract

- Status: accepted design baseline for TASK-019 (ADR-008)
- Date: 2026-11-04
- Contract version: 1.0.0
- Specs: SPEC-006, SPEC-007 · Related: SPEC-002, SPEC-005
- Applies to: every project whose canonical state follows either the `.blueprint/`
  target layout (Context B) or this repository's root development layout
  `memory/`, `tasks/`, `specs/`, `handoffs/` (Context A).

## 1. Purpose

Define, provider-neutrally, what a monitor may read, in what shape, with what freshness and failure semantics, so that provider adapters can implement user-facing observability UIs (starting with the OpenCode TUI sidebar) without duplicating, owning, or mutating canonical state.

## 2. Principles

1. **Read-only presentation.** Monitors never write canonical records, sessions, tasks, or approvals. Writes belong to the Orchestrator/steward workflows.
2. **No second source of truth.** The monitor does not persist task, approval, agent, or memory state anywhere authoritative. Any cache is derived, rebuildable, and lives under `derived/`.
3. **Resolve, don't assume.** The canonical root is resolved per project, not hardcoded; Context A and Context B layouts differ and both must work from one implementation.
4. **Degraded, not broken.** Missing or unparsable records produce a degraded snapshot with reasons; they never fabricate values.
5. **Freshness is explicit.** Every snapshot carries read timestamps and record mtimes/commit info so staleness is visible.
6. **Provider-neutral contract, adapter-native UI.** This document defines the contract; adapters define rendering and integration.

## 3. Canonical root resolution

From the current OpenCode/project working directory, walk upward, one directory at a time:

| Order | Test | Resolved layout |
| --- | --- | --- |
| 1 | An ancestor contains `.blueprint/` | `blueprint@<that-directory>` (Context B). Read `.blueprint/…` paths. |
| 2 | An ancestor (candidate root) contains all of `tasks/registry.json`, `memory/CURRENT_STATE.md`, `specs/` | `development@<that-directory>` (Context A, this repository's layout). Read root-equivalent paths. |
| 3 | Neither | `uninitialized`. The monitor shows a "not a Blueprint project" degraded snapshot and must not invent paths. |

Additional rules:

- The nearest ancestor wins (same rule as the memory protocol §3.1).
- The resolved layout kind, root path, and per-record paths are part of every snapshot.
- If multiple roots could match, the nearest wins and the monitor reports the observation. The monitor must not migrate or copy either layout to the other.
- Path mapping per layout:

| Concern | Context B (`blueprint`) | Context A (`development`) |
| --- | --- | --- |
| Task registry | `.blueprint/tasks/registry.json` | `tasks/registry.json` |
| Task briefs | `.blueprint/tasks/items/TASK-<NNN>.md` | `tasks/items/TASK-<NNN>.md` |
| Current state | `.blueprint/memory/CURRENT_STATE.md` | `memory/CURRENT_STATE.md` |
| Project context | `.blueprint/memory/PROJECT_CONTEXT.md` | `memory/PROJECT_CONTEXT.md` |
| Decisions | `.blueprint/memory/DECISIONS.md` | `memory/DECISIONS.md` |
| Metadata | `.blueprint/memory/metadata.json` | `memory/metadata.json` (when present) |
| Config | `.blueprint/config/*.json` | optional; absent → omit fields |
| Handoffs | `.blueprint/handoffs/*.md` | `handoffs/*.md` |
| Sessions | `.blueprint/sessions/*.md` | `sessions/*.md` |
| Manifest | `.blueprint/manifest.json` | absent → `manifest: none` |

## 4. Snapshot model

The unit of observation is an **Observability Snapshot** (JSON-able):

```jsonc
{
  "contract_version": "1.0.0",
  "read_at": "2026-11-04T12:00:00Z",
  "layout": {
    "kind": "blueprint | development | uninitialized",
    "root": "<absolute path>",
    "paths": { "registry": "...", "current_state": "...", "decisions": "...", "handoffs_glob": "...", "metadata": "..." }
  },
  "project": { "name": "...", "slug": "..." },            // optional; absent when unknown
  "tasks": [                                               // mirrors registry.json verbatim
    { "id": "TASK-009", "title": "...", "status": "done", "priority": "high",
      "owner_role": "...", "spec_refs": [...], "dependencies": [...],
      "next_action": "..." }
  ],
  "active_task": {                                         // null when none resolved
    "id": "TASK-010", "title": "...", "status": "ready",
    "owner_role": "...", "in_progress": false,
    "evidence": { "criteria_total": 4, "criteria_evidenced": 4, "criteria_pending": 0 } | "unparsed"
  },
  "blockers": [ { "source_task": "TASK-010", "summary": "...", "recorded_at": "..." } ] | "unparsed",
  "pending_approvals": [ ... same shape ... ] | "unparsed",
  "decisions": { "total": 8, "latest": { "adr_id": "ADR-008", "title": "...", "status": "accepted", "date": "..." } },
  "handoffs": [ { "path": "...", "recorded_at": "...", "title": "..." } ],   // newest first, max 5
  "sessions": [ { "path": "...", "recorded_at": "...", "title": "..." } ],   // newest first, max 5
  "freshness": {
    "registry": { "mtime": "...", "age_seconds": 0, "stale": false },
    "current_state": { "mtime": "...", "age_seconds": 0, "stale": false },
    "manifest": "present | absent",
    "git_head_optional": "…"
  },
  "issues": [ { "record": "registry", "severity": "warning | error", "message": "..." } ]
}
```

Semantic rules:

- `tasks` is a verbatim mirror of the registry; the monitor computes nothing over task state except display ordering.
- `active_task` follows the memory protocol §3.4 selection rules (an `in_progress` task; else highest-priority `ready` with all dependencies `done`, ties by lowest ID). If selection is ambiguous (multiple `in_progress`), report `issues` and set `active_task: null`.
- Field names `spec_refs`/`dependencies`/`next_action` mirror the task-registry schema's `specs`/`dependencies`/`next_action`; renaming in the snapshot is prohibited (contract v1.0.0).
- `evidence.criteria_*` are counts of `- [ ]`/- [x]` checkboxes in the active brief's Acceptance criteria section and the checked ones; the brief's Completion evidence table is not parsed (display links the path instead).
- `blockers`/`pending_approvals` derive from `CURRENT_STATE.md` (Blockers / Pending approvals sections) plus blocked tasks in the registry. When the narrative cannot be parsed, the value is the literal `"unparsed"` with an issue recorded — never an empty list masquerading as truth.
- `freshness.stale` is `true` when `age_seconds` exceeds the adapter-configured threshold (default: 3600 s). It is advisory only.
- Contract version bumps: additive fields = minor; changed semantics/renames = major (monitor shows a contract-mismatch degraded note).

## 5. Ownership and prohibition map

| Fact | Owning record (source of truth) | Monitor display |
| --- | --- | --- |
| Task status/priority/deps | `registry.json` | verbatim mirror |
| Task scope/evidence | task brief | counts + link |
| Active work/blockers/next action | `CURRENT_STATE.md` | displayed verbatim |
| Approvals | `DECISIONS.md` (accepted/pending) + `CURRENT_STATE.md` | listed, never edited |
| Roles/delegation | `config/agents.json` (B) or role docs (A) | summary only |
| Handoff continuity | `handoffs/*.md` | list + date |
| fresh Git state | local Git (optional) | optional indicator |

The monitor MUST NOT: write any of these records; create sessions, tasks, approvals, or handoffs; maintain a mirroring store; or reinterpret a blocked task as its own state.

## 6. Update and consistency semantics

1. **Init:** produce one snapshot on start.
2. **Refresh triggers:** adapter-native user request, session/agent events (when the provider exposes them), or a bounded poll (default ≤ 1 Hz) that first compares file mtimes and re-reads only changed records.
3. **Consistency rule:** after any read, if two records disagree (e.g., registry says `done`, brief has pending criteria), keep both values and record an `issue` with severity `warning`; never silently choose.
4. **Partial reads:** one record failing to parse keeps the previous value in `deep-fallback` form: the snapshot still renders with `issues` naming the failing record. A fully failing read (no canonical root) yields the `uninitialized` degraded snapshot.
5. **Caching:** at most one in-memory snapshot + stored snapshot for degraded mode (memory storage). No disk cache outside `derived/`. Rebuilding never recreates canonical state.
6. **Security:** the monitor reads files under the resolved root only — never unrelated paths. No network access is needed or permitted by the contract. Scan for credentials is unnecessary because the monitor never copies content beyond what it displays.

## 7. Adapter interface

An adapter implementing this contract must expose, at minimum:

1. `resolveRoot(dir) → layout` (per §3, shared implementation, adapter-agnostic).
2. `readSnapshot() → Snapshot` (per §4).
3. A renderer that displays, at minimum: active task (ID/title/status/owner), selection-relevant statuses of ready/blocked tasks, blockers, pending approvals, latest ADR, latest handoff, and freshness plus `issues`.
4. Degraded mode: last good snapshot + `read_at` + issue list, explicitly labeled stale.
5. Configurability for both contexts without code changes (layout kinds come from §3).

Conformance (SPEC-006 ADAPT-006) requires the adapter report to state which §4 fields are displayed, which refresh triggers are supported, and how degradation is presented.

## 8. Degraded modes

| Condition | Behavior |
| --- | --- |
| No canonical root | `uninitialized` snapshot; UI shows "not a Blueprint project", no state invented. |
| Sealed/unknown manifest (B) | Display a warning; do not block reads (record mtimes still work). |
| Registry unparsable | `tasks: null` in the snapshot + `issue` error; previous good values remain visible, labeled with `read_at`. |
| Current state unparsable | treat active task/blockers/nextAction as `unparsed` + `warning`; registry still shows. |
| Snapshot load timeout | show last snapshot + "stale since <time>". |

## 9. OpenCode implementation pointers (adapter scope)

- A TUI plugin adds a `sidebar.content` slot rendering the monitor from §7; a slash command toggles it; refresh uses mtime-based re-read triggered by server events (`session.execution.*`, `permission.*`) or a bounded poll.
- The monitor reads the local filesystem only; no extra server, database, or network.
- The monitor must stay active only when the resolved root yields a layout; otherwise omit the slot content entirely (no "empty panel" noise).

## 10. Acceptance evidence for TASK-019

| Criterion | Evidence |
| --- | --- |
| Provider-neutral contract and ownership model documented | this document §2, §4, §5. |
| Required fields and lifecycle/update semantics defined | §4 snapshot model, §6 semantics. |
| OpenCode plugin arch + sidebar verified against official docs and a minimal v2.2.5 spike | `adapters/opencode/monitor/` implementation; spike record `docs/architecture/monitor-spike-2026-11-04.md` — observed on v2.2.5: server part loads (`msg="loading plugin" … entrypoint=…/src/index.ts` + watcher subscribe), TUI part reaches `stage=setup plugin=developer-ai-init-monitor` completed, no monitor/plugin errors. Interactive sidebar visual render captured separately (pending user confirmation; headless pty could not capture sidebar text). |
| Installation and upgrade behavior is optional, reproducible, versioned, and non-destructive | monitor `README.md` §Install (copy into `.opencode/plugins/`, no extra config, `/monitor` toggle); plugin version 0.1.0; adapter collision policy applies. |
| Degraded mode shows last persisted state + freshness with explicit issue labels | §8; verified in `scripts/verify-observability-snapshot.ts` (uninitialized degraded snapshot, no-write proof, unparsable-record `issues` paths) → RESULT: PASS 23/23. |
| Core workflows remain usable with the monitor off | monitor is an independent optional plugin; adapter commands run unchanged without it (TASK-009 evidence: `opencode run /blueprint-next` in the smoke project without the monitor installed). |
| Both canonical contexts served by one implementation | Context A (this repo, development layout) and Context B (`.blueprint/` fixture) both verified by the same reader in `scripts/verify-observability-snapshot.ts`; no duplicated monitor. |
