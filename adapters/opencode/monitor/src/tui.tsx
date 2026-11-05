import { Plugin, usePlugin } from "@opencode/plugin/tui"
import { Show, createSignal, onCleanup } from "solid-js"
import type { Snapshot } from "./blueprint"
import { readSnapshot } from "./blueprint"

const POLL_MS = 1000

function initialSnapshot(directory: string | undefined): Snapshot {
  if (!directory) return {
    contract_version: "1.0.0", read_at: "",
    layout: { kind: "uninitialized", root: "", paths: {} },
    freshness: {},
    issues: [{ record: "root", severity: "error", message: "no location available" }],
  }
  try { return readSnapshot(directory) }
  catch (e) {
    return {
      contract_version: "1.0.0", read_at: "",
      layout: { kind: "uninitialized", root: directory, paths: {} },
      freshness: {}, error: String(e),
      issues: [{ record: "monitor", severity: "error", message: String(e) }],
    }
  }
}

function Mon() {
  const context = usePlugin()
  const directory = (context as { location?: { directory?: string } }).location?.directory
  const [snap, setSnap] = createSignal<Snapshot>(initialSnapshot(directory))
  const read = () => {
    if (!directory) return
    try { setSnap(readSnapshot(directory)) }
    catch (e) {
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
      get layout() { return snap().layout },
      get active() { return (snap().active_task ?? null) as
        | { id?: string; title?: string; status?: string; owner_role?: string; evidence?: unknown } | null },
      get issues() { return snap().issues ?? [] },
      get error() { return snap().error },
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
        if (!h.length) return "none"
        return h.length > 1 ? `${h[0].path.split("/").pop()} +${h.length - 1}` : h[0].path.split("/").pop()
      },
      get age() {
        for (const v of Object.values(snap().freshness ?? {}) as Array<{age_seconds?: number}>) {
          if (typeof v?.age_seconds === "number") return v.age_seconds < 90 ? "<2m" : v.age_seconds < 3600 ? `${Math.round(v.age_seconds / 60)}m` : ">1h"
        }
        return ""
      },
      get evidence() {
        const e = s.active?.evidence
        if (e && typeof e === "object" && "criteria_total" in e) {
          const c = e as {criteria_total:number; criteria_evidenced:number}
          return `${c.criteria_evidenced}/${c.criteria_total}`
        }
        return ""
      },
    }
  }

  return <box title="Blueprint Monitor">
    <Show when={s.layout.kind !== "uninitialized"} fallback={<text fg={context.theme.text.muted}>not a Blueprint project</text>}>
      <box>
        <text fg={context.theme.text.base}>◈ Blueprint</text>
        <text fg={context.theme.text.muted}>{s.layout.kind}</text>
        <Show when={s.active}>
          <text fg={context.theme.text.base}>▶ {s.active!.id} {(s.active!.title ?? "").slice(0, 26)}</text>
          <text fg={context.theme.text.muted}>{s.active!.status}{s.evidence ? ` ${s.evidence}` : ""}</text>
        </Show>
        <Show when={!s.active}><text fg={context.theme.text.muted}>no active task</text></Show>
        <text fg={context.theme.text.muted}>blockers: {s.blockers}</text>
        <text fg={context.theme.text.muted}>pending: {s.approvals}</text>
        <text fg={context.theme.text.muted}>ADR: {s.decisions}</text>
        <text fg={context.theme.text.muted}>handoff: {s.handoff}</text>
        <Show when={s.age}><text fg={context.theme.text.muted}>state: {s.age}</text></Show>
        <Show when={s.issues.length > 0}><text fg={context.theme.text.muted}>issues: {s.issues.length}</text></Show>
        <Show when={s.error}><text fg={context.theme.text.muted}>error: {s.error?.slice(0, 30)}</text></Show>
      </box>
    </Show>
  </box>
}

export default Plugin.define({
  id: "developer-ai-init-monitor",
  setup(context) {
    // storage.store returns a reactive proxy object, not a callable accessor.
    const [hidden, setHidden] = context.storage.store("sidebar-hidden", { initial: { hidden: false } })
    const unregister = context.ui.slot({
      append: "sidebar.content",
      render: () => <Show when={!hidden.hidden}><Mon /></Show>,
    })
    context.keymap.layer(() => ({
      mode: "global", priority: 10,
      commands: [{
        id: "blueprint.monitor",
        title: "Toggle Blueprint monitor sidebar",
        group: "Blueprint",
        palette: true,
        slash: { name: "monitor" },
        run: async () => {
          await setHidden((draft) => { draft.hidden = !draft.hidden })
        },
      }],
      bindings: [],
    }))
    return () => unregister()
  },
})
