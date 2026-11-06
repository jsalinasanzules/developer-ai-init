/**
 * Runtime observations from OpenCode events, kept in memory only.
 *
 * This module deliberately does not read or write Blueprint canonical records.
 * Events are treated as observations: incomplete input remains incomplete and
 * unknown rather than being repaired by inference.
 */

export type ObservationStatus = "pending" | "running" | "completed" | "failed" | "interrupted" | "idle" | "unknown"
export type ObservationToolStatus = "streaming" | "running" | "completed" | "failed" | "unknown"

export interface ObservationIssue {
  code: string
  message: string
}

export interface ObservedInvocation {
  key: string
  sessionID: string
  messageID: string
  toolCallID: string
  name: string
  description?: string
  agent?: string
  status: ObservationToolStatus
  startedAt?: number
  endedAt?: number
  input?: Record<string, unknown>
  text?: string
}

export interface ObservedAttempt {
  sessionID: string
  status: "running" | "completed" | "failed" | "interrupted"
  startedAt?: number
  endedAt?: number
  error?: string
  reason?: string
}

export interface ObservedSession {
  id: string
  parentID?: string
  agent?: string
  title?: string
  status: ObservationStatus
  createdAt?: number
  updatedAt?: number
  attempts: ObservedAttempt[]
}

export interface ObservedActivity {
  id: string
  at: number
  kind: string
  text: string
  sessionID?: string
  messageID?: string
  toolCallID?: string
}

export interface ObservationState {
  sessions: Record<string, ObservedSession>
  invocations: Record<string, ObservedInvocation>
  activity: ObservedActivity[]
  issues: ObservationIssue[]
  stale: boolean
  disconnected: boolean
  generatedAt: number
  /** RFC-style map protected from duplicate event ids. */
  seenEventIds: Record<string, true>
  /** Monotonically increasing local order for events with no usable timestamp. */
  fallbackSequence: number
}

type RuntimeEvent = {
  id?: unknown
  created?: unknown
  type?: unknown
  data?: unknown
  details?: unknown
}

export function createObservationState(now = Date.now()): ObservationState {
  return {
    sessions: {},
    invocations: {},
    activity: [],
    issues: [],
    stale: false,
    disconnected: false,
    generatedAt: now,
    seenEventIds: {},
    fallbackSequence: 0,
  }
}

const asRecord = (value: unknown): Record<string, unknown> | undefined =>
  value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : undefined

const asString = (value: unknown): string | undefined =>
  typeof value === "string" && value.trim().length > 0 ? value : undefined

const asNumber = (value: unknown): number | undefined =>
  typeof value === "number" && Number.isFinite(value) ? value : undefined

const issue = (state: ObservationState, code: string, message: string) => {
  if (!state.issues.some((entry) => entry.code === code && entry.message === message)) {
    state.issues.push({ code, message })
  }
}

const appendActivity = (
  state: ObservationState,
  at: number,
  kind: string,
  text: string,
  scope: { sessionID?: string; messageID?: string; toolCallID?: string } = {},
) => {
  const id = `${scope.sessionID ?? "unknown"}:${scope.messageID ?? "none"}:${scope.toolCallID ?? "none"}:${state.fallbackSequence++}`
  state.activity.push({ id, at, kind, text, ...scope })
  state.activity.sort((a, b) => a.at - b.at || a.id.localeCompare(b.id))
  if (state.activity.length > 100) state.activity = state.activity.slice(-100)
}

const upsertSession = (state: ObservationState, event: RuntimeEvent, data: Record<string, unknown>): ObservedSession | undefined => {
  const id = asString(data.sessionID)
  if (!id) {
    issue(state, "missing-session-id", "event omitted data.sessionID")
    return undefined
  }
  const at = asNumber(event.created)
  const existing = state.sessions[id]
  const session: ObservedSession = existing ?? {
    id,
    status: "unknown",
    attempts: [],
  }
  const parentID = asString(data.parentID)
  const agent = asString(data.agent)
  const title = asString(data.title) ?? (existing?.title)
  if (parentID) session.parentID = parentID
  else if (data.parentID !== undefined && data.parentID !== null) issue(state, "invalid-parent-id", `session ${id} has non-string parentID`)
  if (agent) session.agent = agent
  if (title) session.title = title
  if (at !== undefined) {
    session.createdAt ??= at
    session.updatedAt = at
  } else if (!existing) {
    session.createdAt = undefined
  }
  state.sessions[id] = session
  return session
}

const parseObjectish = (value: unknown, onIssue?: (code: string, message: string) => void): Record<string, unknown> | undefined => {
  if (asRecord(value)) return asRecord(value)
  if (typeof value !== "string") return undefined
  const text = value.trim()
  if (!text.startsWith("{")) return undefined
  try {
    const parsed = JSON.parse(text) as unknown
    return asRecord(parsed)
  } catch {
    onIssue?.("unparseable-tool-input", "tool input text could not be parsed as an object")
    return undefined
  }
}

const updateInvocationFromInput = (
  inv: ObservedInvocation,
  session: ObservedSession | undefined,
  at: number | undefined,
  name?: string,
  input?: Record<string, unknown>,
) => {
  if (name) inv.name = name
  if (input) {
    inv.input = input
    inv.description = asString(input.description) ?? asString(input.title)
    inv.agent = asString(input.agent) ?? asString(input.role)
  }
  if (at !== undefined) inv.startedAt ??= at
  if (session && at !== undefined) session.updatedAt = at
}

export function applyRuntimeEvent(state: ObservationState, candidate: RuntimeEvent | { details?: unknown }): ObservationState {
  const event = (asRecord((candidate as RuntimeEvent).details) ?? asRecord(candidate)) as RuntimeEvent | undefined
  if (!event) {
    issue(state, "unreadable-event", "event payload was not an object")
    state.fallbackSequence += 1
    return state
  }
  const type = asString(event.type)
  if (!type) {
    issue(state, "missing-event-type", "event omitted type")
    state.fallbackSequence += 1
    return state
  }
  const eventID = asString(event.id)
  if (eventID && state.seenEventIds[eventID]) return state
  if (eventID) state.seenEventIds[eventID] = true
  const at = asNumber(event.created) ?? Date.now()
  state.generatedAt = Math.max(state.generatedAt, at)

  if (type === "session.created" || type === "session.forked") {
    const d = asRecord(event.data)
    if (!d) { issue(state, "invalid-session-event", `${type} omitted data`); return state }
    const session = upsertSession(state, event, d)
    // Important: session.created can arrive late. It is metadata, not a
    // completion or reset signal—a late create must not erase an already
    // observed terminal outcome.
    if (session) {
      appendActivity(state, at, type === "session.created" ? "session.created" : "session.forked", `observed ${session.agent ?? "session"} ${session.id.slice(0, 12)}`, { sessionID: session.id })
    }
    return state
  }

  if (type === "session.agent.selected") {
    const d = asRecord(event.data); if (!d) return state
    const session = upsertSession(state, event, d)
    if (session) { session.agent = asString(d.agent) ?? session.agent; appendActivity(state, at, "session.agent.selected", `agent ${session.agent}`, { sessionID: session.id }) }
    return state
  }

  if (type === "session.renamed") {
    const d = asRecord(event.data); if (!d) return state
    const session = upsertSession(state, event, d)
    const title = asString(d.title)
    if (session && title) { session.title = title; appendActivity(state, at, "session.renamed", `renamed ${title}`, { sessionID: session.id }) }
    return state
  }

  const execution = /^session\.execution\.(started|succeeded|failed|interrupted)$/.exec(type)
  if (execution) {
    const phase = execution[1]
    const d = asRecord(event.data)
    if (!d) { issue(state, "invalid-execution-event", `${type} omitted data`); return state }
    const session = upsertSession(state, event, d)
    const sessionID = asString(d.sessionID)
    if (!session || !sessionID) return state
  if (phase === "started") {
      const stale = session.attempts.some(
        (attempt) => attempt.endedAt !== undefined && at !== undefined && attempt.endedAt > at,
      )
      if (stale) {
        appendActivity(state, at, type, "late execution started ignored", { sessionID: session.id })
      } else {
        session.status = "running"
        session.attempts.push({ sessionID, status: "running", startedAt: at })
        appendActivity(state, at, type, `execution started`, { sessionID })
      }
    } else {
      const result = phase === "succeeded" ? "completed" : phase === "failed" ? "failed" : "interrupted"
      // Finish the newest unfinished attempt. An unmatched terminal event is
      // retained as an unknown-start attempt rather than attaching to an
      // earlier already-terminal attempt.
      let target = [...session.attempts].reverse().find((attempt) => attempt.status === "running")
      if (!target) {
        target = { sessionID, status: result, endedAt: at }
        session.attempts.push(target)
      } else if (target.startedAt !== undefined && at < target.startedAt) {
        // Do not create an attempt whose end precedes its own start. Retain
        // the event as a separate unknown-start attempt and record the
        // ordering anomaly for the operator.
        issue(state, "out-of-order-terminal", `${type} ended at ${at} before attempt start ${target.startedAt} on session ${sessionID}`)
        target = { sessionID, status: result, endedAt: at }
        session.attempts.push(target)
      } else {
        target.status = result
        target.endedAt = at
      }
      const error = asString(asRecord(d.error)?.message) ?? asString(d.error)
      const reason = asString(d.reason)
      if (error) target.error = error
      if (reason) target.reason = reason
      session.status = result
      appendActivity(state, at, type, reason ? `execution ${result} (${reason})` : `execution ${result}${error ? `: ${error}` : ""}`, { sessionID })
    }
    return state
  }

  if (type === "session.status" || type === "session.idle") {
    const d = asRecord(event.data); if (!d) return state
    const session = upsertSession(state, event, d); if (!session) return state
    const terminal: ObservationStatus[] = ["completed", "failed", "interrupted"]
    session.status = type === "session.idle" && !terminal.includes(session.status) ? "idle" : session.status
    appendActivity(state, at, type, type === "session.idle" ? "session idle" : "session status update", { sessionID: session.id })
    return state
  }

  const inputStart = /^session\.tool\.input\.(started|ended)$/.exec(type)
  if (inputStart) {
    const phase = inputStart[1]
    const d = asRecord(event.data)
    if (!d) return state
    const sessionID = asString(d.sessionID), messageID = asString(d.assistantMessageID), toolCallID = asString(d.id)
    if (!sessionID || !messageID || !toolCallID) { issue(state, "invalid-tool-event", `${type} missing identifiers`); return state }
    const key = `${sessionID}/${messageID}/${toolCallID}`
    const inv = state.invocations[key] ?? { key, sessionID, messageID, toolCallID, name: "unknown-tool", status: "streaming" }
    const session = upsertSession(state, event, d)
    if (phase === "started") {
      updateInvocationFromInput(inv, session, at, asString(d.name))
      inv.status = "streaming"
      state.invocations[key] = inv
      appendActivity(state, at, type, `tool ${inv.name} input started`, { sessionID, messageID, toolCallID })
    } else {
      const text = asString(d.text)
      const parsed = parseObjectish(text, (code, message) => issue(state, code, message))
      inv.text = text ?? inv.text
      const input = parsed ?? inv.input
      if (input) updateInvocationFromInput(inv, session, at, undefined, input)
      state.invocations[key] = inv
      appendActivity(state, at, type, `tool ${inv.name} input ended`, { sessionID, messageID, toolCallID })
    }
    return state
  }

  if (type === "session.tool.called" || type === "session.tool.progress" || type === "session.tool.success" || type === "session.tool.failed") {
    const d = asRecord(event.data)
    if (!d) return state
    const sessionID = asString(d.sessionID), messageID = asString(d.assistantMessageID), toolCallID = asString(d.id)
    if (!sessionID || !messageID || !toolCallID) { issue(state, "invalid-tool-event", `${type} missing identifiers`); return state }
    const key = `${sessionID}/${messageID}/${toolCallID}`
    const inv = state.invocations[key] ?? { key, sessionID, messageID, toolCallID, name: "unknown-tool", status: "streaming" }
    const session = upsertSession(state, event, d)
    const input = asRecord(d.input)
    if (input) updateInvocationFromInput(inv, session, at, inv.name, input)
    const rawMetadata = asRecord(d.metadata)
    if (rawMetadata && asString(rawMetadata.agent) && !inv.agent) inv.agent = asString(rawMetadata.agent)
    if (type === "session.tool.called") { inv.status = "running"; appendActivity(state, at, type, `tool ${inv.name} called`, { sessionID, messageID, toolCallID }) }
    else if (type === "session.tool.progress") { if (inv.status !== "failed" && inv.status !== "completed") inv.status = "running"; if (!state.issues.some((i) => i.code === "runtime-progress")) issue(state, "runtime-progress", "tool progress events received but no terminal result observed yet") }
    else if (type === "session.tool.success") { inv.status = "completed"; inv.endedAt = at; if (session) session.updatedAt = at; appendActivity(state, at, type, `tool ${inv.name} completed`, { sessionID, messageID, toolCallID }) }
    else { inv.status = "failed"; inv.endedAt = at; if (session) session.updatedAt = at; appendActivity(state, at, type, `tool ${inv.name} failed`, { sessionID, messageID, toolCallID }) }
    state.invocations[key] = inv
    return state
  }

  if (type === "session.deleted") {
    const d = asRecord(event.data); const sessionID = d ? asString(d.sessionID) : undefined
    if (sessionID && state.sessions[sessionID]) issue(state, "session-deleted", `session ${sessionID} was deleted while still observed`)
    appendActivity(state, at, type, "session deleted", { sessionID })
    return state
  }

  appendActivity(state, at, type, `unsupported event ${type}`, { sessionID: asString(asRecord(event.data)?.sessionID) })
  return state
}

export function markRuntimeDisconnected(state: ObservationState, message = "runtime observation interrupted"): ObservationState {
  state.disconnected = true
  issue(state, "runtime-disconnected", message)
  return state
}

export function findInvocationLinks(state: ObservationState) {
  const parentCalls = Object.values(state.invocations).filter((inv) => inv.name === "subagent")
  const links: Array<{ invocation: ObservedInvocation; child: ObservedSession; certainty: "explicit" | "candidate" | "ambiguous" }> = []
  for (const call of parentCalls) {
    const possible = Object.values(state.sessions).filter(
      (session) => session.parentID === call.sessionID && (!call.agent || !session.agent || session.agent === call.agent),
    )
    for (const child of possible) {
      const unresolved = parentCalls.filter(
        (candidate) =>
          candidate.sessionID === call.sessionID &&
          (!child.agent || !candidate.agent || candidate.agent === child.agent),
      )
      const exact = unresolved.filter(
        (candidate) => child.title && candidate.description && child.title === candidate.description,
      )
      const certainty =
        exact.length === 1
          ? "explicit"
          : exact.length > 1 || unresolved.length > 1 || possible.length > 1
            ? "ambiguous"
            : "candidate"
      links.push({ invocation: call, child, certainty })
    }
  }
  return links
}

/** Return child sessions whose `parentID` was referenced but never observed. */
export function findUnobservedParents(state: ObservationState): Array<{ sessionID: string; parentID: string }> {
  const out: Array<{ sessionID: string; parentID: string }> = []
  for (const session of Object.values(state.sessions)) {
    if (session.parentID && !state.sessions[session.parentID]) {
      out.push({ sessionID: session.id, parentID: session.parentID })
    }
  }
  return out.sort((a, b) => a.sessionID.localeCompare(b.sessionID))
}
