/**
 * Blueprint monitor — OpenCode TUI plugin part (TASK-021, ADR-008).
 *
 * Renders a provider-neutral observability snapshot plus an in-memory,
 * read-only view of runtime events OpenCode actually emits. Neither view ever
 * writes canonical records or creates a second source of truth. Contract:
 * docs/architecture/observability.md (v1.0.0). Runtime events are volatile
 * observations and cannot prove approval, review, or task completion.
 */

import { Plugin, usePlugin } from "@opencode/plugin/tui"
import { For, Show, createSignal, onCleanup } from "solid-js"
import type { Snapshot } from "./blueprint"
import { readSnapshot, resolveRoot } from "./blueprint"
import { readConfiguredHierarchy } from "./configured-hierarchy"
import {
  applyRuntimeEvent,
  createObservationState,
  findInvocationLinks,
  findUnobservedParents,
  markRuntimeDisconnected,
  type ObservationState,
} from "./runtime-observations"

const POLL_MS = 1000

let preservedRuntimeState = createObservationState()

function snapshotObservation(state: ObservationState): ObservationState {
  // Give Solid a new top-level reference so every render applies immediately.
  return {
    ...state,
    sessions: { ...state.sessions },
    invocations: { ...state.invocations },
    issues: [...state.issues],
    activity: [...state.activity],
    seenEventIds: { ...state.seenEventIds },
  }
}

function initialSnapshot(directory: string | undefined): Snapshot {
  if (!directory) {
    return {
      contract_version: "1.0.0",
      read_at: "",
      layout: { kind: "uninitialized", root: "", paths: {} },
      freshness: {},
      issues: [{ record: "root", severity: "error", message: "no location available" }],
    }
  }
  try {
    return readSnapshot(directory)
  } catch (e) {
    return {
      contract_version: "1.0.0",
      read_at: "",
      layout: { kind: "uninitialized", root: resolveRootFor(directory), paths: {} },
      freshness: {},
      error: String(e),
      issues: [{ record: "monitor", severity: "error", message: String(e) }],
    }
  }
}

function resolveRootFor(dir: string): string {
  // best-effort only; the real resolution lives in blueprint.ts
  return dir
}

function Mon() {
  const context = usePlugin()
  const directory: string | undefined =
    (context as { location?: { directory?: string } }).location?.directory
  const [snap, setSnap] = createSignal<Snapshot>(initialSnapshot(directory))
  const configured = directory
    ? readConfiguredHierarchy(resolveRoot(directory))
    : { source: "unavailable" as const, managers: [], specialists: [], issues: ["no location available"] }
  const [observed, setObserved] = createSignal<ObservationState>(snapshotObservation(preservedRuntimeState))
  const recordRuntimeEvent = (candidate: unknown) => {
    preservedRuntimeState = applyRuntimeEvent(preservedRuntimeState, candidate as Parameters<typeof applyRuntimeEvent>[1])
    setObserved(snapshotObservation(preservedRuntimeState))
  }
  const recordRuntimeDisconnected = (message = "runtime event listener unavailable") => {
    preservedRuntimeState = markRuntimeDisconnected(preservedRuntimeState, message)
    setObserved(snapshotObservation(preservedRuntimeState))
  }
  // OpenCode v2.2.5 exposes data.listen in the TUI context. If the API is
  // absent or throws, keep the canonical snapshot working and mark runtime
  // observations unavailable instead of silently pretending an empty feed.
  let stopRuntimeListener: (() => void) | undefined
  try {
    const runtimeApi = (context as { data?: { listen?: (handler: (event: { details?: unknown }) => void) => () => void } }).data
    if (runtimeApi?.listen) {
      stopRuntimeListener = runtimeApi.listen((event) => {
        try {
          recordRuntimeEvent(event)
        } catch (error) {
          recordRuntimeDisconnected(error instanceof Error ? error.message : String(error))
        }
      })
    } else {
      recordRuntimeDisconnected("OpenCode context does not expose data.listen")
    }
  } catch (error) {
    recordRuntimeDisconnected(error instanceof Error ? error.message : String(error))
  }
  onCleanup(() => stopRuntimeListener?.())
  const read = () => {
    if (!directory) return
    try {
      setSnap(readSnapshot(directory))
    } catch (e) {
      const last = snap()
      setSnap({ ...last, read_at: last.read_at, error: String(e) })
    }
  }
  read()
  const timer = setInterval(read, POLL_MS)
  onCleanup(() => clearInterval(timer))

  const s = snapshotValue()
  function snapshotValue() {
    return {
      get layout() {
        return snap().layout
      },
      get active() {
        return (snap().active_task ?? null) as
          | { id?: string; title?: string; status?: string; owner_role?: string; evidence?: unknown }
          | null
      },
      get completed() {
        return (snap().last_completed_task ?? null) as
          | { id?: string; title?: string }
          | null
      },
      get issues() {
        return snap().issues ?? []
      },
      get error() {
        return snap().error
      },
      get blockers() {
        const b = snap().blockers
        if (b === "unparsed") return "unparsed"
        if (Array.isArray(b)) return b.length ? b.map((x) => x.summary).join("; ") : "none"
        return ""
      },
      get approvals() {
        const p = snap().pending_approvals
        if (p === "unparsed") return "unparsed"
        if (Array.isArray(p)) return p.length ? p.map((x) => x.summary).join("; ") : "none"
        return ""
      },
      get decisions() {
        const d = snap().decisions
        if (d === "unparsed") return "unparsed"
        if (d && typeof d === "object" && d.latest) return `${d.latest.adr_id} (${d.total})`
        return "none"
      },
      get handoff() {
        const h = snap().handoffs ?? []
        if (h.length === 0) return "none"
        return h.length > 1 ? `${(h[0].path.split("/").pop() ?? h[0].path)} +${h.length - 1}` : h[0].path.split("/").pop()
      },
      get age() {
        const reg = (snap().freshness ?? {}) as Record<string, { age_seconds?: number }>
        for (const v of Object.values(reg)) {
          if (v && typeof v === "object" && typeof v.age_seconds === "number") {
            return v.age_seconds < 90 ? "<2m" : v.age_seconds < 3600 ? `${Math.round(v.age_seconds / 60)}m` : ">1h"
          }
        }
        return ""
      },
      get evidence() {
        const e = s_activeEvidence()
        return e ?? ""
      },
      get configured() {
        return configured
      },
      get observation() {
        return observed()
      },
      get runtimeLinks() {
        return findInvocationLinks(observed())
      },
      get unobservedParents() {
        return findUnobservedParents(observed())
      },
    }
  }
  function s_activeEvidence(): string | undefined {
    const e = s_active?.evidence
    if (e && typeof e === "object" && "criteria_total" in (e as object)) {
      const c = e as { criteria_total: number; criteria_evidenced: number }
      return `${c.criteria_evidenced}/${c.criteria_total}`
    }
    return undefined
  }
  const s_active = () => s.active

  return (
    <box title="Blueprint Monitor">
      <Show
        when={s.layout.kind !== "uninitialized"}
        fallback={<text fg={context.theme.text.muted}>not a Blueprint project</text>}
      >
        <box>
          <text fg={context.theme.text.base}>◈ Blueprint</text>
          <text fg={context.theme.text.muted}>{s.layout.kind}</text>
          <Show when={s.configured.source !== "unavailable"}>
            <text fg={context.theme.text.muted}>configured hierarchy</text>
            <text fg={context.theme.text.muted}>
              USER → ORCHESTRATOR → MANAGERS → SPECIALISTS
            </text>
            <text fg={context.theme.text.muted}>
              {s.configured.orchestrator?.title ?? "orchestrator unavailable"}
              {s.configured.managers.length ? ` · ${s.configured.managers.length} manager${s.configured.managers.length === 1 ? "" : "s"}` : " · no managers configured"}
              {s.configured.specialists.length ? ` · ${s.configured.specialists.length} specialist${s.configured.specialists.length === 1 ? "" : "s"}` : ""}
            </text>
            <text fg={context.theme.text.muted}>
              roles: {[s.configured.orchestrator?.id, ...s.configured.managers.map((r) => r.id), ...s.configured.specialists.map((r) => r.id)].filter(Boolean).join(", ")}
            </text>
          </Show>
          <Show when={s.configured.source === "unavailable"}>
            <text fg={context.theme.text.muted}>configured hierarchy: unavailable</text>
          </Show>
          <Show when={s.configured.issues.length > 0}>
            <text fg={context.theme.text.muted}>configured: {s.configured.issues.length} warning{s.configured.issues.length === 1 ? "" : "s"}</text>
          </Show>
          <text fg={context.theme.text.muted}>
            observed runtime: {Object.keys(s.observation.sessions).length} session{Object.keys(s.observation.sessions).length === 1 ? "" : "s"}
            {s.observation.disconnected ? " · interrupted" : ""}
          </text>
          <Show when={s.runtimeLinks.length > 0}>
            <For each={s.runtimeLinks}>
              {(link) => (
                <text fg={context.theme.text.muted}>
                  ⇢ {link.invocation.agent ?? link.child.agent ?? "unknown"} ← {(link.invocation.description ?? "unnamed").slice(0, 28)} ({link.certainty})
                </text>
              )}
            </For>
          </Show>
          <Show when={s.runtimeLinks.length === 0 && Object.keys(s.observation.sessions).length > 0}>
            <text fg={context.theme.text.muted}>delegation edges: unresolved</text>
          </Show>
          <Show when={s.unobservedParents.length > 0}>
            <text fg={context.theme.text.muted}>parent unobserved: {s.unobservedParents.length} ({s.unobservedParents[0].parentID.slice(0, 12)})</text>
          </Show>
          <Show when={s.observation.issues.length > 0}>
            <text fg={context.theme.text.muted}>runtime issues: {s.observation.issues.length}</text>
          </Show>
          <Show when={Object.keys(s.observation.sessions).length > 0}>
            <text fg={context.theme.text.muted}>review: unobserved · approval: unobserved</text>
          </Show>
          <text fg={context.theme.text.muted}>recent runtime activity</text>
          <Show when={s.observation.activity.length > 0}
            fallback={<text fg={context.theme.text.muted}>none observed since monitor load</text>}
          >
            <For each={s.observation.activity.slice(-5)}>
              {(item) => (
                <text fg={context.theme.text.muted}>
                  {new Date(item.at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })} {item.text.slice(0, 48)}
                </text>
              )}
            </For>
          </Show>
          <Show when={s.active}>
            <text fg={context.theme.text.base}>
              ▶ {s.active!.id} {(s.active!.title ?? "").slice(0, 26)}
            </text>
            <text fg={context.theme.text.muted}>
              {s.active!.status}
              {s.evidence ? ` ${s.evidence}` : ""}
            </text>
          </Show>
          <Show when={!s.active && s.completed}>
            <text fg={context.theme.text.muted}>last completed: {s.completed!.id} {(s.completed!.title ?? "").slice(0, 26)}</text>
          </Show>
          <Show when={!s.active && !s.completed}>
            <text fg={context.theme.text.muted}>no active task</text>
          </Show>
          <text fg={context.theme.text.muted}>blockers: {s.blockers}</text>
          <text fg={context.theme.text.muted}>pending: {s.approvals}</text>
          <text fg={context.theme.text.muted}>ADR: {s.decisions}</text>
          <text fg={context.theme.text.muted}>handoff: {s.handoff ?? "none"}</text>
          <Show when={s.age}>
            <text fg={context.theme.text.muted}>updated: {s.age} ago</text>
          </Show>
          <Show when={s.issues.length > 0}>
            <text fg={context.theme.text.muted}>issues: {s.issues.length}</text>
          </Show>
          <Show when={s.error}>
            <text fg={context.theme.text.muted}>error: {s.error?.slice(0, 30)}</text>
          </Show>
        </box>
      </Show>
    </box>
  )
}

export default Plugin.define({
  id: "developer-ai-init-monitor",
  setup(context) {
    const [hidden, setHidden] = context.storage.store("sidebar-hidden", { initial: { hidden: false } })

    const unregister = context.ui.slot({
      append: "sidebar.content",
      render: () => (
        <Show when={!hidden.hidden}>
          <Mon />
        </Show>
      ),
    })

    context.keymap.layer(() => ({
      mode: "global",
      priority: 10,
      commands: [
        {
          id: "blueprint.monitor",
          title: "Toggle Blueprint monitor sidebar",
          group: "Blueprint",
          palette: true,
          slash: { name: "monitor" },
          run: async () => {
            await setHidden((draft) => {
              draft.hidden = !draft.hidden
            })
          },
        },
      ],
      bindings: [],
    }))

    return () => unregister()
  },
})
