/**
 * Blueprint monitor — canonical-root resolution and observability snapshot.
 *
 * Implements the contract in docs/architecture/observability.md (v1.0.0).
 * READ-ONLY: this module never writes canonical records. Path resolution
 * supports both layouts: `.blueprint/` (generated projects) and the root
 * development layout (`memory/`, `tasks/`, …, as used by this repository).
 */

import { existsSync, readdirSync, readFileSync, statSync } from "node:fs"
import { dirname, join } from "node:path"

export type LayoutKind = "blueprint" | "development" | "uninitialized"

export interface Layout {
  kind: LayoutKind
  root: string
  paths: Partial<{
    registry: string
    current_state: string
    project_context: string
    decisions: string
    metadata: string
    manifest: string
    handoffs_dir: string
    sessions_dir: string
    config_dir: string
  }>
}

export interface TaskMirror {
  id: string
  title?: string
  status: string
  priority?: string
  owner_role?: string
  specs?: string[]
  dependencies?: string[]
  next_action?: string
}

export interface EvidenceCounts {
  criteria_total: number
  criteria_evidenced: number
  criteria_pending: number
}

export interface BlockerLike {
  source_task?: string
  summary: string
  recorded_at?: string
}

export interface Snapshot {
  contract_version: string
  read_at: string
  layout: Layout
  project?: { name?: string; slug?: string }
  tasks?: TaskMirror[] | null
  active_task?: Record<string, unknown> | null
  blockers?: BlockerLike[] | "unparsed"
  pending_approvals?: BlockerLike[] | "unparsed"
  decisions?: { total: number; latest?: { adr_id: string; title?: string; status?: string; date?: string } } | "unparsed"
  handoffs?: Array<{ path: string; recorded_at?: string; title?: string }>
  sessions?: Array<{ path: string; recorded_at?: string; title?: string }>
  freshness: Record<string, { mtime?: string; age_seconds?: number; stale?: boolean; present?: boolean } | string>
  issues: Array<{ record: string; severity: "warning" | "error"; message: string }>
  error?: string
}

export const CONTRACT_VERSION = "1.0.0"
export const STALE_SECONDS_DEFAULT = 3600

const REGISTRY_FILE = "registry.json"
const STATE_FILE = "CURRENT_STATE.md"
const CONTEXT_FILE = "PROJECT_CONTEXT.md"
const DECISIONS_FILE = "DECISIONS.md"
const METADATA_FILE = "metadata.json"
const MANIFEST_FILE = "manifest.json"

/** Resolve the canonical root from the current directory upward (§3). */
export function resolveRoot(startDir: string): Layout {
  let cur = startDir
  for (;;) {
    const bp = join(cur, ".blueprint")
    if (existsSync(join(bp, "tasks", REGISTRY_FILE))) {
      return {
        kind: "blueprint",
        root: bp,
        paths: {
          registry: join(bp, "tasks", REGISTRY_FILE),
          current_state: join(bp, "memory", STATE_FILE),
          project_context: join(bp, "memory", CONTEXT_FILE),
          decisions: join(bp, "memory", DECISIONS_FILE),
          metadata: join(bp, "memory", METADATA_FILE),
          manifest: join(bp, MANIFEST_FILE),
          handoffs_dir: join(bp, "handoffs"),
          sessions_dir: join(bp, "sessions"),
          config_dir: join(bp, "config"),
        },
      }
    }
    const devRegistry = join(cur, "tasks", REGISTRY_FILE)
    const devState = join(cur, "memory", STATE_FILE)
    if (existsSync(devRegistry) && existsSync(devState) && existsSync(join(cur, "specs"))) {
      return {
        kind: "development",
        root: cur,
        paths: {
          registry: devRegistry,
          current_state: devState,
          project_context: join(cur, "memory", CONTEXT_FILE),
          decisions: join(cur, "memory", DECISIONS_FILE),
          metadata: join(cur, "memory", METADATA_FILE),
          manifest: undefined as never,
          handoffs_dir: join(cur, "handoffs"),
          sessions_dir: join(cur, "sessions"),
          config_dir: undefined as never,
        },
      }
    }
    const parent = dirname(cur)
    if (parent === cur) {
      return { kind: "uninitialized", root: startDir, paths: {} }
    }
    cur = parent
  }
}

// ---------------------------------------------------------------------------
// parsing helpers (deliberately tolerant: degraded snapshots, never throwing)
// ---------------------------------------------------------------------------

function safeJson<T>(path?: string): { value: T | null; path?: string } {
  if (!path || !existsSync(path)) return { value: null }
  try {
    return { value: JSON.parse(readFileSync(path, "utf8")) as T }
  } catch (e) {
    return { value: null }
  }
}

function readFileSafe(path?: string): { text: string; mtime?: Date } {
  if (!path || !existsSync(path)) return { text: "" }
  try {
    return { text: readFileSync(path, "utf8"), mtime: statSync(path).mtime }
  } catch {
    return { text: "" }
  }
}

function section(text: string, headings: string[]): string | undefined {
  for (const h of headings) {
    const re = new RegExp(`^#{1,6}[ \\t]+${h}[ \\t]*$`, "im")
    const m = re.exec(text)
    if (!m) continue
    const after = text.slice(m.index + m[0].length)
    const next = /^#{1,6}[ \t]+/m.exec(after)
    return (next ? after.slice(0, next.index) : after).trim()
  }
  return undefined
}

function heading(value: string | undefined): string | undefined {
  if (!value) return undefined
  const m = /(?:^|\n)\*\*(.+?)\*\*/.exec(value)
  if (m) return m[1].replace(/\s+—.*$/, "").trim()
  const line = value.split("\n").map((s) => s.trim()).find((s) => s && !s.startsWith("-"))
  return line?.replace(/\*\*/g, "").trim()
}

function bulletLines(text: string): string[] {
  return (text ?? "")
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => l.startsWith("- "))
    .map((l) => l.slice(2).trim())
    .filter(Boolean)
}

function mtimes(paths: string[]): Record<string, { mtime?: string; age_seconds?: number; stale?: boolean }> {
  const out: Record<string, { mtime?: string; age_seconds?: number; stale?: boolean }> = {}
  for (const p of paths) {
    if (!p || !existsSync(p)) continue
    try {
      const m = statSync(p).mtime
      out[p] = {
        mtime: m.toISOString(),
        age_seconds: Math.round((Date.now() - m.getTime()) / 1000),
        stale: false,
      }
    } catch {
      /* degraded */
    }
  }
  return out
}

function listMarkdown(dir?: string, max = 5): Array<{ path: string; recorded_at?: string; title?: string }> {
  if (!dir || !existsSync(dir)) return []
  try {
    const files = readdirSync(dir)
      .filter((f) => f.endsWith(".md") && !f.includes("TEMPLATE"))
      .sort()
      .reverse()
    return files.slice(0, max).map((f) => {
      const p = join(dir, f)
      const { text } = readFileSafe(p)
      return { path: p, title: (text.split("\n")[0] ?? "").replace(/^#\s*/, "") || f, recorded_at: undefined }
    })
  } catch {
    return []
  }
}

function parseRegistry(layout: Layout, issues: Snapshot["issues"]): { tasks: TaskMirror[] | null } {
  const { value } = safeJson<Record<string, unknown>>(layout.paths.registry)
  const tasksRaw = (value as { tasks?: unknown[] })?.tasks ?? (value as unknown[] | undefined)
  if (!Array.isArray(tasksRaw)) {
    if (layout.paths.registry && existsSync(layout.paths.registry!)) {
      issues.push({ record: "registry", severity: "error", message: "registry.json present but no tasks array found" })
    } else {
      issues.push({ record: "registry", severity: "error", message: "registry.json missing from canonical root" })
    }
    return { tasks: null }
  }
  const tasks = tasksRaw
    .filter((t): t is Record<string, unknown> => !!t && typeof t === "object")
    .map((t) => ({
      id: String(t["id"] ?? "?"),
      title: t["title"] as string | undefined,
      status: String(t["status"] ?? "unknown"),
      priority: t["priority"] as string | undefined,
      owner_role: (t["owner_role"] as string | undefined) ?? (t["owner"] as string | undefined),
      specs: t["specs"] as string[] | undefined ?? (t["spec_refs"] as string[] | undefined),
      dependencies: t["dependencies"] as string[] | undefined,
      next_action: (t["next_action"] as string | undefined) ?? (t["next-action"] as string | undefined),
    }))
  return { tasks }
}

function selectActive(tasks: TaskMirror[] | null, layout: Layout, issues: Snapshot["issues"]) {
  const state = readFileSafe(layout.paths.current_state)
  const activeSection = section(state.text, ["Active task"])
  let id: string | undefined | "unparsed"
  let narrative_status: string | undefined
  if (activeSection === undefined) {
    id = "unparsed"
    if (state.text) issues.push({ record: "current_state", severity: "warning", message: "no '## Active task' section found" })
  } else {
    id = /TASK-\d{3}/.exec(activeSection)?.[0]
    narrative_status = /status\s*[:=]\s*([a-z_]+)/i.exec(activeSection)?.[1]?.toLowerCase()
  }

  const inProgress = (tasks ?? ([] as TaskMirror[])).filter((t) => t.status === "in_progress")
  if (inProgress.length > 1) {
    issues.push({
      record: "registry",
      severity: "warning",
      message: `multiple tasks in_progress: ${inProgress.map((t) => t.id).join(", ")}`,
    })
  }
  const selected =
    // prefer registry-authoritative selection: in_progress, else highest-priority ready
    inProgress[0] ??
    (tasks ?? [])
      .filter((t) => t.status === "ready")
      .filter((t) => (t.dependencies ?? []).every((d) => (tasks ?? []).find((x) => x.id === d)?.status === "done"))
      .sort(
        (a, b) =>
          ["critical", "high", "medium", "low"].indexOf(a.priority ?? "low") -
            ["critical", "high", "medium", "low"].indexOf(b.priority ?? "low") || (a.id < b.id ? -1 : 1),
      )[0]

  // evidence counts from the brief's Acceptance criteria section
  let evidence: EvidenceCounts | "unparsed" | undefined
  if (selected) {
    let briefPath: string | undefined
    if (layout.kind === "blueprint") briefPath = join(layout.root, "tasks", "items", `${selected.id}.md`)
    else briefPath = join(layout.root, "tasks", "items", `${selected.id}.md`)
    const brief = readFileSafe(briefPath)
    if (brief.text) {
      const sec = section(brief.text, ["Acceptance criteria"])
      if (sec === undefined) evidence = "unparsed"
      else {
        const total = (sec.match(/^[-*][ \t]+\[[ x]?\]/gm) ?? []).length || bulletLines(sec).length
        const done = (sec.match(/\[x\]/g) ?? []).length
        evidence = { criteria_total: total, criteria_evidenced: done, criteria_pending: Math.max(0, total - done) }
      }
    } else {
      evidence = "unparsed"
    }
  }

  if (selected && narrative_status && narrative_status !== selected.status) {
    issues.push({
      record: "current_state",
      severity: "warning",
      message: `CURRENT_STATE.md says "${selected.id}: ${narrative_status}" but registry says ${selected.status}; registry is authoritative`,
    })
  }

  const nextAction = section(state.text, ["Next"])
  if (selected && id === "unparsed" ) {
    issues.push({ record: "current_state", severity: "warning", message: "active task section present but no TASK-NNN id readable" })
  }
  const active = selected
    ? {
        id: selected.id,
        title: selected.title,
        status: selected.status,
        owner_role: selected.owner_role,
        in_progress: selected.status === "in_progress",
        narrative_confirms_registry: narrative_status ? narrative_status === selected.status : undefined,
        evidence,
        next_action: selected.next_action,
      }
    : id === "unparsed" ? null : null
  return { active, next_action: nextAction ? nextAction.split("\n")[0] : undefined, blockers: undefined as unknown, pending: undefined as unknown }
}

function parseStateFlags(layout: Layout, issues: Snapshot["issues"]) {
  const state = readFileSafe(layout.paths.current_state)
  if (!state.text && layout.paths.current_state) {
    issues.push({ record: "current_state", severity: "error", message: "CURRENT_STATE.md missing from canonical root" })
  }
  const blockersSection = section(state.text, ["Blockers", "Risks and blockers"])
  const approvalsSection = section(state.text, ["Pending approvals"])
  const hasNone = (s?: string) => !!s && /none/i.test(s.split("\n")[0] ?? "")
  const blockers: BlockerLike[] | "unparsed" =
    blockersSection === undefined ? "unparsed" : hasNone(blockersSection) ? [] : bulletLines(blockersSection).map((l) => ({ summary: l }))
  const pending_approvals: BlockerLike[] | "unparsed" =
    approvalsSection === undefined ? "unparsed" : hasNone(approvalsSection) ? [] : bulletLines(approvalsSection).map((l) => ({ summary: l }))
  if (!state.text && layout.paths.current_state) {
    // keep as unparsed rather than null
  }
  return { blockers, pending_approvals, state_mtime: state.mtime }
}

function parseDecisions(layout: Layout, issues: Snapshot["issues"]): Snapshot["decisions"] {
  const { text } = readFileSafe(layout.paths.decisions)
  if (!text) return "unparsed"
  const re = /^## (ADR-\d+)\s*—\s*(.+)$/gm
  const matches = [...text.matchAll(re)]
  if (matches.length === 0) {
    issues.push({ record: "decisions", severity: "warning", message: "DECISIONS.md present but no '## ADR-NNN' headings found" })
    return { total: 0 }
  }
  const latestHead = matches[matches.length - 1]
  const tail = text.slice(latestHead.index!)
  const next = /^##\s/m.exec(tail.slice(4))
  const body = next ? tail.slice(0, next.index) : tail
  const status = /status\s*:\s*([^\n|]+)/i.exec(body)?.[1]?.trim()
  return {
    total: matches.length,
    latest: {
      adr_id: latestHead[1],
      title: latestHead[2].split(/[|\n]/)[0].trim(),
      status: status?.split("|")[0]?.trim(),
      date: /date\s*:\s*(\d{4}-\d{2}-\d{2})/i.exec(body)?.[1],
    },
  }
}

/** Build an observability snapshot (READ-ONLY). */
export function readSnapshot(dir: string, opts: { staleSeconds?: number } = {}): Snapshot {
  const issues: Snapshot["issues"] = []
  const layout = resolveRoot(dir)
  const read_at = new Date().toISOString()
  if (layout.kind === "uninitialized") {
    return {
      contract_version: CONTRACT_VERSION,
      read_at,
      layout,
      freshness: {},
      issues: [{ record: "root", severity: "error", message: "no .blueprint/ and no development-layout markers found" }],
    }
  }

  const registry = parseRegistry(layout, issues)
  const stateFlags = parseStateFlags(layout, issues)
  const activeInfo = selectActive(registry.tasks, layout, issues)
  const decisions = parseDecisions(layout, issues)

  const project = safeJson<{ id?: string; name?: string; project_id?: string; title?: string; slug?: string }>(
    join(layout.paths.config_dir ?? layout.root, "project.json"),
  )
  const manifest = existsSync(layout.paths.manifest ?? "")
  return {
    contract_version: CONTRACT_VERSION,
    read_at,
    layout,
    project: project.value
      ? {
          name: project.value.name ?? project.value.title,
          slug: project.value.project_id ?? project.value.id ?? project.value.slug,
        }
      : undefined,
    tasks: registry.tasks,
    active_task: activeInfo.active,
    blockers: stateFlags.blockers,
    pending_approvals: stateFlags.pending_approvals,
    decisions,
    handoffs: listMarkdown(layout.paths.handoffs_dir),
    sessions: listMarkdown(layout.paths.sessions_dir),
    freshness: {
      ...mtimes(
        [
          layout.paths.registry,
          layout.paths.current_state,
          layout.paths.decisions,
          layout.paths.manifest,
        ].filter(Boolean as unknown as (p?: string) => p is string),
      ),
      manifest: manifest ? "present" : (layout.kind === "development" ? "none (development layout)" : "absent"),
    },
    issues,
  }
}
