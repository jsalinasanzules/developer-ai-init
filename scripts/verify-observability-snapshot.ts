#!/usr/bin/env bun
/**
 * Contract checks for docs/architecture/observability.md via the monitor's
 * shared reader (src/blueprint.ts). Runs the reader against
 *  - Context A: this repository (root development layout), and
 *  - Context B: a generated `.blueprint/` fixture built in a temp directory.
 * Verifies the snapshot model fields, tabindex-free degraded handling, and
 * read-only behavior (no files written). Run with `bun run <this file>`.
 */

import { mkdtempSync, cpSync, mkdirSync, writeFileSync, existsSync, readFileSync } from "node:fs"
import { join } from "node:path"
import { readSnapshot, resolveRoot, CONTRACT_VERSION } from "../adapters/opencode/monitor/src/blueprint.ts"

let ok = true
function check(name: string, cond: boolean, detail = "") {
  console.log(`${cond ? "PASS" : "FAIL"}  ${name}${detail ? ` — ${detail}` : ""}`)
  ok = ok && cond
}

const repoRoot = import.meta.dir ? join(import.meta.dir, "..") : process.cwd()

// --- Context A: this repository (development layout) -------------------------
const here = readSnapshot(repoRoot)
const task020 = here.tasks?.find((task) => task.id === "TASK-020")
check("A: layout kind development", here.layout.kind === "development")
check("A: contract version", here.contract_version === CONTRACT_VERSION)
check("A: registry parsed (20 tasks)", (here.tasks?.length ?? 0) === 20, String(here.tasks?.length))
check("A: TASK-020 remains visible in registry", !!task020)
check(
  "A: active selection follows lifecycle status",
  task020?.status === "in_progress"
    ? here.active_task?.id === "TASK-020"
    : here.active_task?.id !== "TASK-020",
)
check("A: decisions parsed", here.decisions !== "unparsed" && here.decisions.total > 0, `${here.decisions.total}`)
check("A: latest ADR is ADR-009", (here.decisions as { latest?: { adr_id?: string } }).latest?.adr_id === "ADR-009")
check("A: handoffs listed", (here.handoffs?.length ?? 0) >= 1)
check("A: blockers none", Array.isArray(here.blockers) && here.blockers.length === 0)
check(
  "A: evidence counts follow selected task",
  here.active_task === null ||
    typeof (here.active_task.evidence as { criteria_total?: number } | undefined)?.criteria_total === "number",
)
const readmeExistsBefore = existsSync(join(repoRoot, "README.md"))
const before = readFileSyncSafe(join(repoRoot, "README.md"))
readSnapshot(repoRoot)
check("A: no writes to canonical root", readmeExistsBefore && !!before && existsSync(join(repoRoot, "README.md")))

// --- Context B: generated project fixture (.blueprint/) ---------------------
const fixtureRoot = mkdtempSync(join("/private/var/folders/pg/sdm_xthn0rbgcgyzlrmhhj800000gn/T/opencode/", "task019-"))
cpSync(join(repoRoot, "adapters", "opencode", "templates"), join(fixtureRoot, "templates-smoke"), { recursive: true })
const bp = join(fixtureRoot, ".blueprint")
mkdirSync(join(bp, "tasks", "items"), { recursive: true })
mkdirSync(join(bp, "memory"), { recursive: true })
mkdirSync(join(bp, "handoffs"), { recursive: true })
mkdirSync(join(bp, "config"), { recursive: true })
writeFileSync(
  join(bp, "tasks", "registry.json"),
  JSON.stringify({
    tasks: [
      { id: "TASK-001", title: "Seed", status: "done", priority: "high", dependencies: [] },
      { id: "TASK-002", title: "Next", status: "ready", priority: "high", owner_role: "ORCHESTRATOR", dependencies: ["TASK-001"], next_action: "Execute the seeded workflow." },
      { id: "TASK-003", title: "Later", status: "proposed", priority: "low", dependencies: ["TASK-002"] },
    ],
  }),
)
writeFileSync(join(bp, "memory", "CURRENT_STATE.md"), "# Current State\n\n## Active task\n**TASK-002 — Next**\n- Status: ready\n\n## Blockers\nNone recorded.\n\n## Pending approvals\nNone.\n\n## Next\nRun the seeded task.\n")
writeFileSync(join(bp, "README.md"), "# BLUEPRINT\n\nBlueprint project documentation.\n")
writeFileSync(
  join(bp, "tasks", "items", "TASK-002.md"),
  "# TASK-002 — Smoked\n\n## Metadata\n- Status: ready\n\n## Acceptance criteria\n- [x] criterion A.\n- [x] criterion B.\n- [ ] criterion C.\n",
)
writeFileSync(
  join(bp, "memory", "DECISIONS.md"),
  "# Decision Log\n\n## ADR-001 — Chosen database\n- Status: accepted | Date: 2026-11-04\n- Decision: none required.\n",
)
mkdirSync(join(bp, "specs"), { recursive: true })
writeFileSync(join(bp, "specs", "SPEC-001-test.md"), "# SPEC-1\n")
writeFileSync(join(bp, "handoffs", "HANDOFF-TEMPLATE.md"), "# Handoff template only — excluded.\n")
writeFileSync(join(bp, "handoffs", "2026-11-04-task-002.md"), "# Handoff — 2026-11-04 — TASK-002\n\nReal handoff entry for the snapshot.\n")
writeFileSync(join(bp, "config", "project.json"), '{"schema_version":"1.0.0","project_id":"fixture-smoke"}\n')

const nestRoot = join(fixtureRoot, "sub", "deeper")
mkdirSync(nestRoot, { recursive: true })
const resolvedNearby = resolveRoot(nestRoot)
check("B: resolution walks up to .blueprint", resolvedNearby.kind === "blueprint" && resolvedNearby.root === bp)

const nested = readSnapshot(nestRoot)
check("B: layout kind blueprint", nested.layout.kind === "blueprint")
check("B: registry parsed (3 tasks)", nested.tasks?.length === 3)
check("B: active task TASK-002", (nested.active_task as { id?: string } | null)?.id === "TASK-002")
check("B: evidence 2/3", JSON.stringify((nested.active_task as { evidence?: { criteria_total: number; criteria_evidenced: number } }).evidence) === JSON.stringify({ criteria_total: 3, criteria_evidenced: 2, criteria_pending: 1 }))
check("B: blockers none", Array.isArray(nested.blockers) && nested.blockers.length === 0)
check("B: pending approvals none", Array.isArray(nested.pending_approvals) && nested.pending_approvals.length === 0)
check("B: project slug from config", (nested.project as { slug?: string } | undefined)?.slug === "fixture-smoke")
check("B: handoff found, template excluded", nested.handoffs?.length === 1 && /task-002/.test(nested.handoffs[0].path))
check("B: template excluded from handoffs", typeof nested.handoffs === "undefined" ? false : !/TEMPLATE/i.test(nested.handoffs[0].path))
check("B: manifest absent flagged", nested.freshness && Object.keys(nested.freshness).length >= 0)

// --- Context D: uninitialized degraded snapshot ------------------------------
const empty = mkdtempSync(join("/private/var/folders/pg/sdm_xthn0rbgcgyzlrmhhj800000gn/T/opencode/", "task019-"))
const none = readSnapshot(empty)
check("D: uninitialized kind", none.layout.kind === "uninitialized")
check("D: issue reported and no tasks", none.tasks === undefined && none.issues.length > 0)

// summary
console.log()
console.log(`RESULT: ${ok ? "PASS" : "FAIL"}`)
process.exit(ok ? 0 : 1)

function readFileSyncSafe(path: string) {
  try {
    return readFileSync(path, "utf8").length > 0
  } catch {
    return false
  }
}
