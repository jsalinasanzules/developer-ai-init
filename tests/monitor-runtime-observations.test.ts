/**
 * Deterministic TASK-021 monitor observation tests.
 *
 * Run with `bun test tests/monitor-runtime-observations.test.ts`.
 * No network, no user data, no canonical files are read or written.
 */
import { describe, expect, test } from "bun:test"
import {
  applyRuntimeEvent,
  createObservationState,
  findInvocationLinks,
  findUnobservedParents,
  markRuntimeDisconnected,
} from "../adapters/opencode/monitor/src/runtime-observations"

const event = (id: string, created: number, type: string, data?: Record<string, unknown>) =>
  ({ id, created, type, data })

describe("runtime observation mapping", () => {
  test("keeps a child session linked only when parentID is present", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("e1", 1, "session.created", { sessionID: "parent", agent: "build", title: "Root" }))
    applyRuntimeEvent(s, event("e2", 2, "session.created", { sessionID: "child", parentID: "parent", agent: "manager-quality", title: "Review work" }))
    expect(s.sessions.child.parentID).toBe("parent")
    expect(s.sessions.child.title).toBe("Review work")
  })

  test("does not associate an arbitrary session with a task", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("e1", 1, "session.created", { sessionID: "ses1", agent: "build", title: "Implement monitor" }))
    expect(JSON.stringify(s)).not.toContain("TASK-021")
    expect(s.sessions.ses1.id).toBe("ses1")
  })

  test("tracks a delegation from tool input through completion", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("a", 1, "session.tool.input.started", { sessionID: "parent", assistantMessageID: "m1", id: "call1", name: "subagent" }))
    applyRuntimeEvent(s, event("b", 2, "session.tool.called", {
      sessionID: "parent",
      assistantMessageID: "m1",
      id: "call1",
      input: { agent: "manager-quality", description: "Review TASK-021", prompt: "Review only" },
      executed: true,
    }))
    expect(s.invocations["parent/m1/call1"].status).toBe("running")
    expect(s.invocations["parent/m1/call1"].description).toBe("Review TASK-021")
    applyRuntimeEvent(s, event("c", 3, "session.tool.success", { sessionID: "parent", assistantMessageID: "m1", id: "call1", content: [{ type: "text", text: "done" }], executed: true }))
    expect(s.invocations["parent/m1/call1"].status).toBe("completed")
  })

  test("duplicate event ids are ignored", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("same", 1, "session.execution.started", { sessionID: "ses1" }))
    applyRuntimeEvent(s, event("same", 999, "session.execution.failed", { sessionID: "ses1", error: { message: "late" } }))
    applyRuntimeEvent(s, event("same", 3, "session.execution.failed", { sessionID: "ses1", error: { message: "duplicate" } }))
    expect(s.sessions.ses1.status).toBe("running")
    expect(s.activity).toHaveLength(1)
  })

  test("a terminal event earlier than the newest attempt start creates an unknown-start attempt", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("start-a", 1, "session.execution.started", { sessionID: "ses1" }))
    applyRuntimeEvent(s, event("start-b", 5, "session.execution.started", { sessionID: "ses1" }))
    applyRuntimeEvent(s, event("end-early", 2, "session.execution.failed", { sessionID: "ses1", error: { message: "boom" } }))
    expect(s.sessions.ses1.attempts).toHaveLength(3)
    expect(s.sessions.ses1.attempts.map((a) => a.status)).toEqual(["running", "running", "failed"])
    expect(s.issues.some((i) => i.code === "out-of-order-terminal")).toBe(true)
  })

  test("late session.created does not erase a terminal observation", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("start", 1, "session.execution.started", { sessionID: "ses1", agent: "build" }))
    applyRuntimeEvent(s, event("end", 2, "session.execution.succeeded", { sessionID: "ses1" }))
    applyRuntimeEvent(s, event("created-late", 3, "session.created", { sessionID: "ses1", agent: "build" }))
    expect(s.sessions.ses1.status).toBe("completed")
  })

  test("late session.idle does not overwrite a terminal observation", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("start", 1, "session.execution.started", { sessionID: "ses1" }))
    applyRuntimeEvent(s, event("end", 2, "session.execution.succeeded", { sessionID: "ses1" }))
    applyRuntimeEvent(s, event("idle", 3, "session.idle", { sessionID: "ses1" }))
    expect(s.sessions.ses1.status).toBe("completed")
  })

  test("exact delegation stays explicit after the tool call succeeds", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("a", 1, "session.tool.input.started", { sessionID: "parent", assistantMessageID: "m1", id: "call1", name: "subagent" }))
    applyRuntimeEvent(s, event("b", 2, "session.tool.called", { sessionID: "parent", assistantMessageID: "m1", id: "call1", input: { agent: "manager-quality", description: "Review TASK-021" }, executed: true }))
    applyRuntimeEvent(s, event("c", 3, "session.tool.success", { sessionID: "parent", assistantMessageID: "m1", id: "call1", content: [{ type: "text", text: "done" }], executed: true }))
    applyRuntimeEvent(s, event("d", 4, "session.created", { sessionID: "child", parentID: "parent", agent: "manager-quality", title: "Review TASK-021" }))
    expect(findInvocationLinks(s)[0]?.certainty).toBe("explicit")
  })

  test("unobserved parent reference is reported instead of hidden", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("child", 1, "session.created", { sessionID: "child", parentID: "missing-parent", agent: "specialist" }))
    expect(findUnobservedParents(s)).toEqual([{ sessionID: "child", parentID: "missing-parent" }])
  })

  test("unparseable tool input text is recorded without throwing", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("a", 1, "session.tool.input.started", { sessionID: "parent", assistantMessageID: "m1", id: "call1", name: "subagent" }))
    applyRuntimeEvent(s, event("b", 2, "session.tool.input.ended", { sessionID: "parent", assistantMessageID: "m1", id: "call1", text: "{not json" }))
    expect(s.issues.some((i) => i.code === "unparseable-tool-input")).toBe(true)
    expect(s.invocations["parent/m1/call1"].text).toBe("{not json")
  })

  test("renaming, selecting an agent, and deletion are recorded honestly", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("a", 1, "session.created", { sessionID: "ses1", agent: "build", title: "Original" }))
    applyRuntimeEvent(s, event("b", 2, "session.agent.selected", { sessionID: "ses1", agent: "specialist" }))
    applyRuntimeEvent(s, event("c", 3, "session.renamed", { sessionID: "ses1", title: "Renamed" }))
    applyRuntimeEvent(s, event("d", 4, "session.deleted", { sessionID: "ses1" }))
    expect(s.sessions.ses1.agent).toBe("specialist")
    expect(s.sessions.ses1.title).toBe("Renamed")
    expect(s.issues.some((i) => i.code === "session-deleted")).toBe(true)
  })

  test("a late started event does not downgrade a terminal attempt", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("cancel", 20, "session.execution.interrupted", { sessionID: "ses1", reason: "user" }))
    applyRuntimeEvent(s, event("late-start", 10, "session.execution.started", { sessionID: "ses1" }))
    const attempts = s.sessions.ses1.attempts
    expect(attempts.at(-1)?.status).toBe("interrupted")
    expect(attempts.at(-1)?.startedAt).toBeUndefined()
  })

  test("out-of-order terminal events attach to the newest open attempt", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("start-a", 1, "session.execution.started", { sessionID: "ses1" }))
    applyRuntimeEvent(s, event("end-b", 3, "session.execution.succeeded", { sessionID: "ses1" }))
    applyRuntimeEvent(s, event("start-c", 4, "session.execution.started", { sessionID: "ses1" }))
    applyRuntimeEvent(s, event("end-c", 5, "session.execution.failed", { sessionID: "ses1", error: { message: "boom" } }))
    expect(s.sessions.ses1.attempts.map((a) => a.status)).toEqual(["completed", "failed"])
    expect(s.sessions.ses1.status).toBe("failed")
  })

  test("a single unambiguous delegation with a matching child gets an explicit link", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("a", 1, "session.tool.input.started", { sessionID: "parent", assistantMessageID: "m1", id: "call1", name: "subagent" }))
    applyRuntimeEvent(s, event("b", 2, "session.tool.called", { sessionID: "parent", assistantMessageID: "m1", id: "call1", input: { agent: "manager-quality", description: "Review TASK-021" }, executed: true }))
    applyRuntimeEvent(s, event("c", 3, "session.created", { sessionID: "child", parentID: "parent", agent: "manager-quality", title: "Review TASK-021" }))
    const links = findInvocationLinks(s)
    expect(links).toHaveLength(1)
    expect(links[0].certainty).toBe("explicit")
  })

  test("parallel identical subagent calls remain unresolved rather than being merged", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("p1", 1, "session.tool.input.started", { sessionID: "parent", assistantMessageID: "m1", id: "call-a", name: "subagent" }))
    applyRuntimeEvent(s, event("p2", 2, "session.tool.input.started", { sessionID: "parent", assistantMessageID: "m1", id: "call-b", name: "subagent" }))
    applyRuntimeEvent(s, event("p3", 3, "session.tool.called", { sessionID: "parent", assistantMessageID: "m1", id: "call-a", input: { agent: "manager-quality", description: "Check" }, executed: true }))
    applyRuntimeEvent(s, event("p4", 4, "session.tool.called", { sessionID: "parent", assistantMessageID: "m1", id: "call-b", input: { agent: "manager-quality", description: "Check" }, executed: true }))
    applyRuntimeEvent(s, event("c1", 5, "session.created", { sessionID: "child-a", parentID: "parent", agent: "manager-quality", title: "Check" }))
    applyRuntimeEvent(s, event("c2", 6, "session.created", { sessionID: "child-b", parentID: "parent", agent: "manager-quality", title: "Check" }))
    const links = findInvocationLinks(s)
    expect(links).toHaveLength(4)
    expect(new Set(links.map((link) => link.certainty))).toEqual(new Set(["ambiguous"]))
    expect(new Set(links.map((link) => link.invocation.key)).size).toBe(2)
    expect(new Set(links.map((link) => link.child.id)).size).toBe(2)
  })

  test("parallel calls with a single observed child make the link unresolved", () => {
    const s = createObservationState(0)
    for (const id of ["call-a", "call-b"]) {
      applyRuntimeEvent(s, event(`start-${id}`, 1, "session.tool.input.started", { sessionID: "parent", assistantMessageID: "m1", id, name: "subagent" }))
      applyRuntimeEvent(s, event(`call-${id}`, 2, "session.tool.called", { sessionID: "parent", assistantMessageID: "m1", id, input: { agent: "specialist", description: "Different work" }, executed: true }))
    }
    applyRuntimeEvent(s, event("child-a", 3, "session.created", { sessionID: "child-a", parentID: "parent", agent: "specialist", title: "Unrelated title" }))
    const links = findInvocationLinks(s)
    expect(links).toHaveLength(2)
    expect(links.every((link) => link.certainty === "ambiguous")).toBe(true)
  })

  test("missing or malformed payloads are accepted as unknown and do not throw", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, { id: "bad1", created: 1, type: "session.created" })
    applyRuntimeEvent(s, { id: "bad2", created: 2, type: "session.tool.called", data: { sessionID: "parent" } })
    applyRuntimeEvent(s, { nope: true } as never)
    expect(s.issues.length).toBeGreaterThan(0)
    expect(s.invocations["parent/unknown/unknown"]).toBeUndefined()
  })

  test("failure and interruption are terminal runtime observations, not approvals", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("a", 1, "session.execution.started", { sessionID: "ses1" }))
    applyRuntimeEvent(s, event("b", 2, "session.tool.failed", { sessionID: "ses1", assistantMessageID: "m1", id: "call1", executed: true, error: { name: "Error", message: "blocked" } }))
    applyRuntimeEvent(s, event("c", 3, "session.execution.interrupted", { sessionID: "ses1", reason: "superseded" }))
    expect(s.sessions.ses1.status).toBe("interrupted")
    expect(s.sessions.ses1.attempts.at(-1)?.reason).toBe("superseded")
    expect(JSON.stringify(s)).not.toContain("approved")
  })

  test("unsupported event types are retained as activity without implying relationships", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("u1", 1, "vcs.branch.updated", { sessionID: "ignored" }))
    expect(s.activity.at(-1)?.kind).toBe("vcs.branch.updated")
    expect(Object.keys(s.sessions)).toHaveLength(0)
  })

  test("disconnect marks observations incomplete instead of synthesizing completion", () => {
    const s = createObservationState(0)
    applyRuntimeEvent(s, event("a", 1, "session.execution.started", { sessionID: "ses1" }))
    markRuntimeDisconnected(s, "listener crashed")
    expect(s.disconnected).toBe(true)
    expect(s.issues.some((i) => i.code === "runtime-disconnected")).toBe(true)
    expect(s.sessions.ses1.status).toBe("running")
  })
})
