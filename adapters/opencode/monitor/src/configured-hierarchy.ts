/**
 * Configured Blueprint hierarchy reader for optional UI display.
 *
 * Read-only file parsing only. The configured hierarchy is not treated as an
 * observation of runtime sessions. Development roots commonly have no
 * machine-readable agents.json; absence is reported explicitly.
 */
import { readFileSync } from "node:fs"
import type { Layout } from "./blueprint"

export interface ConfiguredRole {
  id: string
  title: string
  kind: "orchestrator" | "manager" | "specialist"
  reports_to?: string
  can_delegate_to: string[]
}

export interface ConfiguredHierarchy {
  source: "config/agents.json" | "unavailable"
  authority?: string[]
  delegation?: { mode?: string; max_depth?: number; fallback?: string }
  orchestrator?: ConfiguredRole
  managers: ConfiguredRole[]
  specialists: ConfiguredRole[]
  issues: string[]
}

const absent: ConfiguredHierarchy = {
  source: "unavailable",
  managers: [],
  specialists: [],
  issues: ["no .blueprint/config/agents.json found"],
}

const isRecord = (v: unknown): v is Record<string, unknown> =>
  !!v && typeof v === "object" && !Array.isArray(v)

const roleFrom = (value: unknown): ConfiguredRole | undefined => {
  if (!isRecord(value)) return undefined
  const id = typeof value.id === "string" ? value.id : undefined
  const title = typeof value.title === "string" ? value.title : undefined
  const kind = value.kind
  if (!id || !title || (kind !== "orchestrator" && kind !== "manager" && kind !== "specialist")) return undefined
  const reportsTo = typeof value.reports_to === "string" ? value.reports_to : undefined
  const delegates = Array.isArray(value.can_delegate_to)
    ? value.can_delegate_to.filter((item): item is string => typeof item === "string")
    : []
  return { id, title, kind, reports_to: reportsTo, can_delegate_to: delegates }
}

export function readConfiguredHierarchy(layout: Layout): ConfiguredHierarchy {
  const path = layout.paths.config_dir ? `${layout.paths.config_dir}/agents.json` : undefined
  if (!path || layout.kind !== "blueprint") return { ...absent, managers: [], specialists: [] }
  let parsed: unknown
  try {
    parsed = JSON.parse(readFileSync(path, "utf8"))
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    return {
      ...absent,
      issues: [`config/agents.json unreadable: ${message}`],
      managers: [],
      specialists: [],
    }
  }
  if (!isRecord(parsed)) {
    return { ...absent, issues: ["config/agents.json is not an object"], managers: [], specialists: [] }
  }
  const roles = isRecord(parsed.roles) ? parsed.roles : undefined
  const expectedAuthority = ["USER", "ORCHESTRATOR", "MANAGERS", "SPECIALISTS"]
  const authority = Array.isArray(parsed.authority) && parsed.authority.every((v) => typeof v === "string")
    ? (parsed.authority as string[])
    : undefined
  const authorityIssues =
    authority && authority.length === expectedAuthority.length && authority.every((value, index) => value === expectedAuthority[index])
      ? []
      : ["authority chain does not match USER → ORCHESTRATOR → MANAGERS → SPECIALISTS"]
  const delegationRaw = isRecord(parsed.delegation) ? parsed.delegation : undefined
  const delegation = delegationRaw
    ? {
        mode: typeof delegationRaw.mode === "string" ? delegationRaw.mode : undefined,
        max_depth: typeof delegationRaw.max_depth === "number" && Number.isInteger(delegationRaw.max_depth) ? delegationRaw.max_depth : undefined,
        fallback: typeof delegationRaw.fallback === "string" ? delegationRaw.fallback : undefined,
      }
    : undefined

  const orchestrator = roleFrom(roles?.orchestrator)
  const managers = Array.isArray(roles?.managers) ? roles.managers.map(roleFrom).filter((r): r is ConfiguredRole => !!r) : []
  const specialists = Array.isArray(roles?.specialists) ? roles.specialists.map(roleFrom).filter((r): r is ConfiguredRole => !!r) : []
  const issues: string[] = [...authorityIssues]
  if (!orchestrator) issues.push("orchestrator role missing or invalid")
  if (managers.length === 0) issues.push("managers list missing or invalid")
  if (specialists.length === 0) issues.push("specialists list missing or invalid")
  if (roles && Array.isArray(roles.managers) && managers.length !== roles.managers.length) issues.push("some manager roles are invalid")
  if (roles && Array.isArray(roles.specialists) && specialists.length !== roles.specialists.length) issues.push("some specialist roles are invalid")

  return {
    source: "config/agents.json",
    authority,
    delegation,
    orchestrator,
    managers,
    specialists,
    issues,
  }
}
