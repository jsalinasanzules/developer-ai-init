# Delegation, Return, and Review Payloads

Copy these structures when delegating or reporting. The normative definitions are in `docs/architecture/agent-hierarchy.md` §4–§5.

## Delegation

```markdown
## Delegation — <delegation-id>
- From: ORCHESTRATOR | MANAGER: <domain>
- To: MANAGER: <domain> | SPECIALIST: <role>
- Task: TASK-NNN
- Objective: <one sentence, observable outcome>
- Context references: <specs, decisions, task brief, files, prior reports>
- Allowed scope: <paths/areas the role may change>
- Forbidden changes: <paths/areas/decisions out of scope>
- Dependencies: <task IDs and status, or `none`>
- Constraints: <approvals, conventions, time/tool limits>
- Expected artifacts: <files, reports, evidence>
- Acceptance criteria: <observable checklist>
- Return format: <report format reference>
- Escalation: <what must be escalated and to whom>
- Deadline/stop condition (optional): <when to stop and report>
```

## Specialist return

```markdown
## Specialist Return — <delegation-id>
- Role / task:
- Objective restated:
- Status: complete | partial | blocked
- Changes: <files and purpose>
- Verification: <commands and observed output>
- Acceptance criteria: <criterion -> evidence>
- Risks / open questions:
- Proposed memory updates: <MUP references or `none`>
- Scope deviations: <none or explicit>
- Next action:
```

## Manager report

```markdown
## Manager Report — <delegation-id>
- Domain / task:
- Units reviewed: <specialist return IDs>
- Review decision: accepted | revise | rejected
- Evidence checked: <specific artifacts/commands>
- Consolidated changes:
- Conflicts / risks:
- Scope deviations:
- Proposed memory updates:
- Recommendation to Orchestrator:
- Next action:
```
