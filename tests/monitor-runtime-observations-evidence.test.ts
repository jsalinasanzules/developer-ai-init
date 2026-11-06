/**
 * TASK-021 named behavioural references for the completion gate.
 *
 * Each `test_*` test below exercises one acceptance criterion with
 * deterministic fixtures. They re-assert the behavioural contracts already
 * implemented in `adapters/opencode/monitor/src/runtime-observations.ts`
 * and `adapters/opencode/monitor/src/configured-hierarchy.ts`; the canonical
 * test suite lives in `tests/monitor-runtime-observations.test.ts`.
 *
 * Run with `bun test tests/test_monitor_runtime_observations.ts`.
 */

import { describe, expect, test } from "bun:test"
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { join } from "node:path"
import { readFileSync as fsRead } from "node:fs"
import { resolveRoot } from "../adapters/opencode/monitor/src/blueprint"
import { readConfiguredHierarchy } from "../adapters/opencode/monitor/src/configured-hierarchy"
import {
  applyRuntimeEvent,
  createObservationState,
  findInvocationLinks,
  findUnobservedParents,
  markRuntimeDisconnected,
} from "../adapters/opencode/monitor/src/runtime-observations"

const event = (id: string, created: number, type: string, data?: Record<string, unknown>) =>
  ({ id, created, type, data })

describe("TASK-021 named evidence tests", () => {
  test("test_child_session_linked_only_with_parent_id", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("e1", 1, "session.created", { sessionID: "child", parentID: "parent", agent: "manager-quality" }))
    expect(s.sessions.child.parentID).toBe("parent")
    applyRuntimeEvent(s, event("e2", 2, "session.created", { sessionID: "orphan", agent: "build" }))
    expect(s.sessions.orphan.parentID).toBeUndefined()
  })

  test("test_delegation_links_require_invocation_evidence", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("a", 1, "session.tool.input.started", { sessionID: "parent", assistantMessageID: "m1", id: "call1", name: "subagent" }))
    applyRuntimeEvent(s, event("b", 2, "session.tool.called", { sessionID: "parent", assistantMessageID: "m1", id: "call1", input: { agent: "manager-quality", description: "Review" }, executed: true }))
    applyRuntimeEvent(s, event("c", 3, "session.created", { sessionID: "child", parentID: "parent", agent: "manager-quality", title: "Review" }))
    expect(findInvocationLinks(s)[0]?.certainty).toBe("explicit")
    // Without a matching child the parent stays unobserved rather than linked.
    const s2 = createObservationState(0)
    applyRuntimeEvent(s2, event("a", 1, "session.tool.called", { sessionID: "parent", assistantMessageID: "m1", id: "call1", input: { agent: "specialist" }, executed: true }))
    expect(findInvocationLinks(s2)).toHaveLength(0)
  })

  test("test_session_end_does_not_imply_approval", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("a", 1, "session.execution.started", { sessionID: "ses1" }))
    applyRuntimeEvent(s, event("b", 2, "session.execution.succeeded", { sessionID: "ses1" }))
    expect(s.sessions.ses1.status).toBe("completed")
    expect(JSON.stringify(s)).not.toContain("approved")
    expect(JSON.stringify(s)).not.toContain("reviewed")
  })

  test("test_activity_feed_stable_ordering_and_cap", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("z-id", 10, "session.execution.started", { sessionID: "ses1" }))
    applyRuntimeEvent(s, event("a-id", 10, "session.execution.started", { sessionID: "ses2" }))
    applyRuntimeEvent(s, event("m-id", 5, "session.execution.started", { sessionID: "ses3" }))
    // Stable chronological ordering by event timestamp.
    expect(s.activity.map((a) => a.at)).toEqual([5, 10, 10])
    for (let i = 0; i < 120; i += 1) {
      applyRuntimeEvent(s, event(`bulk-${i}`, 1000 + i, "session.execution.started", { sessionID: "bulk" }))
    }
    expect(s.activity.length).toBeLessThanOrEqual(100)
    expect(s.activity.at(-1)?.at).toBe(1119)
  })

  test("test_parallel_and_malformed_payloads_do_not_crash", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("p1", 1, "session.tool.input.started", { sessionID: "parent", assistantMessageID: "m1", id: "call-a", name: "subagent" }))
    applyRuntimeEvent(s, event("p2", 2, "session.tool.input.started", { sessionID: "parent", assistantMessageID: "m1", id: "call-b", name: "subagent" }))
    applyRuntimeEvent(s, event("p3", 3, "session.tool.called", { sessionID: "parent", assistantMessageID: "m1", id: "call-a", input: { agent: "specialist", description: "W" }, executed: true }))
    applyRuntimeEvent(s, event("p4", 4, "session.tool.called", { sessionID: "parent", assistantMessageID: "m1", id: "call-b", input: { agent: "specialist", description: "W" }, executed: true }))
    applyRuntimeEvent(s, event("c1", 5, "session.created", { sessionID: "child-a", parentID: "parent", agent: "specialist", title: "W" }))
    applyRuntimeEvent(s, event("c2", 6, "session.created", { sessionID: "child-b", parentID: "parent", agent: "specialist", title: "W" }))
    const links = findInvocationLinks(s)
    expect(links.every((l) => l.certainty === "ambiguous")).toBe(true)
    const s2 = createObservationState(0)
    applyRuntimeEvent(s2, { id: "bad", created: 1, type: "session.created" } as never)
    applyRuntimeEvent(s2, { nope: true } as never)
    expect(s2.issues.length).toBeGreaterThan(0)
  })

  test("test_disconnect_stays_incomplete", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("a", 1, "session.execution.started", { sessionID: "ses1" }))
    markRuntimeDisconnected(s, "listener unavailable")
    expect(s.disconnected).toBe(true)
    expect(s.sessions.ses1.status).toBe("running")
  })

  test("test_configured_hierarchy_from_agents_file", () => {
    const base = mkdtempSync(join(tmpdir(), "hier-"))
    mkdirSync(join(base, ".blueprint", "tasks", ), { recursive: true })
    mkdirSync(join(base, ".blueprint", "config"), { recursive: true })
    writeFileSync(join(base, ".blueprint", "tasks", "registry.json"), JSON.stringify({ tasks: [] }))
    writeFileSync(join(base, ".blueprint", "config", "agents.json"), JSON.stringify({
      authority: ["USER", "ORCHESTRATOR", "MANAGERS", "SPECIALISTS"],
      roles: {
        orchestrator: { id: "orchestrator", title: "Orchestrator", kind: "orchestrator" },
        managers: [{ id: "manager-quality", title: "Manager Quality", kind: "manager" }],
        specialists: [{ id: "specialist-a", title: "Specialist", kind: "specialist" }],
      },
    }))
    const layout = resolveRoot(base)
    expect(layout.kind).toBe("blueprint")
    const h = readConfiguredHierarchy(layout)
    expect(h.source).toBe("config/agents.json")
    expect(h.orchestrator?.id).toBe("orchestrator")
    expect(h.managers.map((m) => m.id)).toEqual(["manager-quality"])
    expect(h.specialists.map((s) => s.id)).toEqual(["specialist-a"])
  })

  test("test_configured_hierarchy_missing_is_unavailable", () => {
    const base = mkdtempSync(join(tmpdir(), "hier-missing-"))
    const layout = resolveRoot(base)
    const h = readConfiguredHierarchy(layout)
    expect(h.source).toBe("unavailable")
    expect(h.managers).toEqual([])
    expect(h.specialists).toEqual([])
    expect(h.issues.length).toBeGreaterThan(0)
  })

  test("test_runtime_state_never_writes_canonical_records", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("a", 1, "session.created", { sessionID: "ses1", title: "T" }))
    expect(s).not.toHaveProperty("tasks")
    expect(s).not.toHaveProperty("approvals")
    expect(s).not.toHaveProperty("registry")
  })

  test("test_sidebar_renders_honest_runtime_labels", () => {
    const src = fsRead(new URL("../adapters/opencode/monitor/src/tui.tsx", import.meta.url), "utf8")
    expect(src).toContain("observed runtime:")
    expect(src).toContain("review: unobserved")
    expect(src).toContain("approval: unobserved")
    expect(src).toContain("parent unobserved")
    expect(src).toContain("configured hierarchy")
    expect(src).toContain("recent runtime activity")
    // Single sidebar slot: no duplicate monitor competing for the same slot.
    expect(src.match(/append: "sidebar.content"/g)?.length ?? 0).toBe(1)
  })

  test("test_unobserved_parent_reported", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("child", 1, "session.created", { sessionID: "child", parentID: "missing", agent: "specialist" }))
    expect(findUnobservedParents(s)).toEqual([{ sessionID: "child", parentID: "missing" }])
  })
})
