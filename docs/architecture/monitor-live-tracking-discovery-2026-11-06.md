# TASK-021 — Live-tracking technical discovery (OpenCode 2.2.5)

- Date: 2026-11-06
- Status: discovery complete; implementation pending Orchestrator/user approval
- Scope: OpenCode `v2.2.5` TUI plugin API and observable event semantics
- Repository: `developer-ai-init` — no `blueprint-demo` access performed

## Conclusion

A provider-safe, read-only live view is possible for the events OpenCode explicitly emits and for session-family metadata exposed by the TUI plugin API. It is **not** possible to promise a complete, durable delegation history or reliable `TASK-NNN` association from the public event stream alone.

The safe implementation is an adapter-only, in-memory observation layer inside the optional OpenCode monitor. It must:

- keep canonical Blueprint records untouched;
- show configured hierarchy separately from runtime sessions actually observed;
- represent unordered, incomplete, lost, or disconnected event streams as unknown/incomplete rather than repairing them by inference;
- never infer review, approval, task completion, or a delegation edge from a session ending or from temporal adjacency.

No change to `docs/architecture/observability.md` or the canonical contract is required for this design.

## Sources checked

1. OpenCode TUI plugin documentation (v2): <https://opencode.ai/v2/docs/build/plugins/cli>
2. OpenCode Server plugin documentation (v2): <https://opencode.ai/v2/docs/build/plugins/server>
3. OpenCode HTTP API reference: <https://opencode.ai/v2/docs/api> and its OpenAPI JSON payload (`/v2/openapi.json`)
4. Local installed runtime: `/Users/joseph/.opencode/bin/opencode` — `opencode --version` reports `opencode v2.2.5`
5. Existing monitor implementation and contract (`adapters/opencode/monitor/`, `docs/architecture/observability.md` v1.0.0)

The local runtime was used only to confirm the declared version and event-name strings. No user data or private session logs were inspected, and no global OpenCode configuration was modified.

## Official TUI APIs relevant to this task

According to the v2 TUI plugin documentation:

| Capability | Documented API | Relevant fields/constraints |
| --- | --- | --- |
| typed event subscription | `context.data.on("event.type", handler)` | Returns unsubscribe function. The example uses `permission.asked`. |
| all-events subscription | `context.data.listen(handler)` | Returns unsubscribe function. Handler receives `{ details }`; event details are server events. |
| cleanup | `return () => unsubscribe()` | Required for lifecycle cleanup. |
| list sessions | `context.data.session.list()` | Exposes loaded session list. |
| get session | `context.data.session.get(sessionID)` | Returns current session information or may be absent. |
| hierarchy helpers | `context.data.session.root(sessionID)`, `.family(sessionID)` | Returns session-tree references; safe for displaying known hierarchy. |
| sync / invalidate | `context.data.session.sync`, `.invalidate` | Explicit refresh; should not be polled aggressively. |
| messages | `context.data.session.message.sync(sessionID)` / `.list(sessionID)` / `.get(sessionID, messageID)` | Can expose message history, including tool parts, when the server returns it. |
| location and storage | `context.location`, `context.storage`, `context.app` | Storage is plugin-local and not a canonical Blueprint store. It must not be used to duplicate canonical state. |
| slot rendering | `context.ui.slot({ append: "sidebar.content", render })` | This is already the monitor integration. |

The same docs state that a slow event consumer can overflow/fail the stream and that events during disconnection are missed. Therefore completeness cannot be claimed.

## Official event schemas relevant to delegation

The OpenAPI reference defines `Session.Info` with:

- `id`
- `parentID` (optional)
- `agent` (optional)
- `fork` (optional, for forks only)
- `time.created`, `time.updated`
- optional `title`, `outcome` (`succeeded|failed|interrupted`)
- location/project/model/tokens metadata

The following public events carry the fields needed for a conservative observation layer:

| Event | Relevant payload | What it proves | What it does **not** prove |
| --- | --- | --- | --- |
| `session.created` | `data.sessionID`, `data.parentID?`, `data.agent?`, `data.title?`, `data.created` via `created`, event `id` | A session exists; child link exists only when `parentID` is present. | Task assignment, approval, review, completion, or which pending tool created the child. |
| `session.forked` | `data.sessionID`, `data.parentID`, boundary/instructions | A fork relationship exists. | Delegation or approval; forks may be arbitrary branches. |
| `session.agent.selected` | `sessionID`, `agent`, optional `previous` | Agent selection changed or was explicitly recorded. | Delegation authority or a TASK-NNN assignment. |
| `session.renamed` | `sessionID`, `title` | Display name changed. | Task completion or approval. |
| `session.execution.started` | `sessionID` | An execution attempt started. | Why it started or what task it belongs to. |
| `session.execution.succeeded` | `sessionID` | An execution attempt ended successfully. | User approval, review, merge, or task completion. |
| `session.execution.failed` | `sessionID`, `error` | An execution attempt failed. | Root cause beyond the structured error. |
| `session.execution.interrupted` | `sessionID`, `reason` (`user|shutdown|superseded|inactivity`) | An execution attempt was interrupted. | A rollback, review failure, or task cancellation. |
| `session.idle` | `sessionID` | Session reached idle. | Completion, approval, or readiness. |
| `session.status` | `sessionID`, `status` | Current session status is exposed as idle/retry/busy-like state. | Task state; exact status shape remains provider-specific. |
| `session.tool.input.started` | `sessionID`, `assistantMessageID`, `id`, `name` | A tool invocation began and the tool name is known. | Which child session will be created or which task it will affect. |
| `session.tool.input.ended` | same IDs, `text` | Input finished. | Execution succeeded. |
| `session.tool.called` | IDs plus object `input`, `executed` | Tool was invoked; full arguments are arbitrary and must be treated as untrusted objects. | That the invocation produced a child or changed anything. |
| `session.tool.progress` | IDs plus `metadata` | Progress metadata exists. | Completion. |
| `session.tool.success` | IDs, content, `metadata`, `executed` | Tool invocation completed successfully. | Acceptance of the delegated work or review approval. |
| `session.tool.failed` | IDs, content, `error`, `metadata`, `executed` | Tool invocation failed. | Why, beyond the structured error. |

Tool lifecycle events share `(sessionID, assistantMessageID, id)`; input events reveal `name`, output events reveal result/error. These two groups must be joined. Unmatched pairs are represented explicitly as incomplete, never as a fabricated tool result.

## Minimal event-to-observability mapping

No canonical schema field is added. Runtime observations remain an ephemeral adapter layer.

| Monitor concept | Source | Display rule |
| --- | --- | --- |
| Configured hierarchy | `.blueprint/config/agents.json` when present (Context B); no reliable machine-readable hierarchy in this repository's development root | Show roles and delegation mode from that file only. If absent: `configured hierarchy: unavailable`. |
| Runtime session | `session.created`, `session.agent.selected`, `execution.*`, `idle`, tool events | Show observed sessions only; mark unrelated sessions as uncorrelated. |
| Parent → child edge | `session.created.parentID` or explicit child/parent relationship from a matching tool event | Draw edge only when the IDs are present. Otherwise no edge. |
| Delegation edge | Parent's `subagent` invocation and an observed child session | Show `delegated` only if the parent call and child link can be correlated from available payloads; otherwise `observed child session; delegation unresolved`. |
| Work-item name | `session.tool.called.input.description` or a structurally present `title` from child/subagent payload | Show only when present; otherwise `unnamed`. |
| Target agent | event agent field or tool input `agent` | Show only if it matches observed event/payload; never from configured default alone. |
| Execution | `session.execution.*`, `session.tool.*` | Show phase and outcome as runtime facts; do not rewrite canonical status. |
| Review/approval | no public event proves either | Always `unobserved` unless canonical records state it; never from a runtime stop/idle. |
| TASK-NNN association | no public event field contains a reliable task reference | Show `task: uncorrelated` unless the actual delegation payload includes an explicit unambiguous task ID; even then display it as an explicitly recorded correlation, not a canonical assignment. |
| Activity feed | deduplicated, ordered event summaries | Keep newest events first; stable order by `(created, id)`; cap display to a compact window. |

## Correlation algorithm

1. Maintain an in-memory observation map keyed by session ID.
2. Deduplicate by event `id` (server events include one) to survive delivery duplicates.
3. If a child event has `parentID`, link it to the parent when the parent was observed; if the parent was not observed, mark the edge `parent: <id> (unobserved)` rather than inventing a name.
4. Join tool events on `(sessionID, assistantMessageID, id)`.
5. For a child created after a pending `subagent` tool invocation, link them only when the tool payload or child session includes an explicit matching identifier; otherwise retain two facts:
   - parent has an invocation of the delegation tool;
   - a child session exists with an agent/title.
   Do not assert a one-to-one assignment when multiple pending calls match.
6. On arrival order: update parent/child labels, status, and feed. A terminal state must not be overwritten by a late `started` event from an earlier execution attempt; keep attempt-level outcomes separate.
7. On disconnect/error: stop updating runtime state, keep visible values with an explicit `runtime observation interrupted` marker, and require user action before claiming completeness.

## Ordering, duplicates, and partial payloads

- **Duplicates:** event `id` is used as the primary identity. For events without a usable ID, no dedupe is invented; a stale count may be shown as an issue.
- **Out-of-order:** lifecycle events are applied to the relevant attempt, not to a global status scalar. Late `started` events do not clear a terminal outcome; the event is shown with its original timestamp.
- **Missing/partial fields:** validate presence before use; unknown values become explicit unknowns.
- **Parallel delegations:** each invocation/child relationship is keyed independently. Two same-agent parallel delegations must remain separate; no merge by agent or description.
- **Lost events:** no synthetic completion. If an expected end is absent, show `status: unknown/incomplete`, not completed/failed.
- **Session end/idle:** never maps to review or approval.

## Limits and unsupported assumptions

The following are unsupported by the public contract and must not be assumed:

1. There is no guaranteed complete event log; reconnects may permanently omit events.
2. No task ID field exists on any documented event. Association from text is a presentation hint, not truth.
3. No approval or review event is documented. `permission.asked/replied` is not approval of a task.
4. `Subagent` tool internals and `Job.Subagent` are not a stable public contract for the monitor. The documented TUI surface exposes sessions/messages/jobs only partially; internal metadata must not be required.
5. `session.idle` and `session.status` do not distinguish idle after success/failure/interruption by themselves.
6. Events during the initial plugin load are missed unless explicitly fetched; current session list can show known sessions but not absent history.
7. Parent/child does not imply a valid review or approval chain; only the direct relationship is recorded.
8. Task owner in `registry.json` does not prove which runtime agent ran/reviewed it.

## Proposed acceptance proof strategy

- deterministic tests for malformed/unknown event payloads;
- duplicate event IDs;
- missing/late/out-of-order execution sequences;
- no task-association assertion unless an explicit payload marker exists;
- parallel same-agent subagents;
- interruption and failure;
- parent absent and parent observed cases;
- configured hierarchy absent/present;
- canonical files unchanged before/after monitor reads;
- degraded mode still renders existing snapshot;
- runtime check only with a low-cost, approved local invocation, or document as not executed if the free model limit prevents it.

## Proposed UX scope

- `Observed runtime` section separate from canonical task summary.
- Configured hierarchy (if available) shown as a static list.
- Up to five newest observed activity rows.
- Details shown only when a session row is expanded; no per-agent checklist.
- Counts for observed running/completed/failed/interrupted sessions; unknown when event stream was interrupted.
- Complete snapshot mode preserved when live events are unavailable.

## Approval requested

Implement the smallest adapter-only extension with **no observability contract change** and no persisted mirror; add focused deterministic tests; then run runtime verification. If any implementation step requires changing the contract, the task must stop for separate approval.
