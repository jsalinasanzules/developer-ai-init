# OpenCode Adapter

- Status: baseline implementation for TASK-009
- Version: 0.1.0
- Provider ID: `opencode`
- Verified against: OpenCode **V2**, `v2.2.5` (local observation); official docs inspected **2026-11-04**
- Specs: SPEC-006, SPEC-007 · Decisions: ADR-004, ADR-006, ADR-007, ADR-008

## 1. Dated documentation inspection record

| Source (opencode.ai/v2/docs) | Inspected | Findings used by this adapter |
| --- | --- | --- |
| `agents/` | 2026-11-04 | Markdown agents in `.opencode/agents/<name>.md`; frontmatter `description`, `mode` (`primary`/`subagent`/`all`), `model`, `permissions`, `steps`, `hidden`, `disabled`; body becomes the system prompt. V1 frontmatter fields are deprecated. Markdown agent bodies replace `system`; JSON agents use `system`. |
| `config/` | 2026-11-04 | `opencode.json(c)` or `.opencode/opencode.json(c)`; `$schema: https://opencode.ai/config.json`; `default_agent`; configuration precedence; `experimental.subagent_depth` (default `1`) controls whether subagents can spawn subagents. |
| `commands/` | 2026-11-04 | Project commands in `.opencode/commands/*.md`; body is the prompt; `agent` selects the executing agent; `subagent: true` runs in a child session. |
| `skills/` | 2026-11-04 | `.opencode/skills/<id>/SKILL.md`; sheet loads via `skill` tool; used where visible; not required by this adapter baseline. |
| `permissions/` (referenced from agents/config pages) | 2026-11-04 | Ordered rules `action/resource/effect`; `edit`, `shell`, `subagent`, `read` actions; last matching rule wins. |

Local verification: `opencode --version` → `opencode v2.2.5` (observed 2026-11-04 in the Blueprint development environment).

If `opencode --version` reports a different major/minor version, re-run the compatibility checks in §9 before trusting behavior claims.

## 2. Adapter manifest

| Field | Value |
| --- | --- |
| Provider ID | `opencode` |
| Adapter version | `0.2.0` |
| Supported blueprint versions | schema `1.0.0` (see `schemas/*.schema.json`) |
| OpenCode baseline | V2 (≥ 2.2.x verified); V1 not supported by these templates |
| Role mapping | §3 |
| Generated paths | §4 |
| Required capabilities | `agents` (Markdown), `commands` (Markdown), `AGENTS.md`/`instructions`, `permissions` |
| Optional capabilities | `experimental.subagent_depth: 2` (nested Manager→Specialist), `experimental.todo`, skills |
| Limitations | §5 |
| Conformance status | §9 |

## 3. Role mapping

| Blueprint role | OpenCode construct | Mode | Notes |
| --- | --- | --- | --- |
| USER | Human operator | — | Never addressed by subagents. |
| ORCHESTRATOR | `orchestrator` agent + root project instructions (`AGENTS.md`) | `primary`, `default_agent` | Only role that talks to the user; owns canonical writes and consolidations. |
| MANAGER: Architecture / Engineering / Quality / Delivery | `manager-architecture`, `manager-engineering`, `manager-quality`, `manager-delivery` | `subagent` | Read/review-oriented; edits denied by default; return reports and proposals. |
| SPECIALIST | `specialist` agent + `specialist-*` naming in delegations | `subagent` | Scoped execution with edit permission; must not ask the user. |

### Hierarchy and depth (ADR-007)

- OpenCode defaults `experimental.subagent_depth` to `1`: a subagent cannot launch another subagent. With depth 1, the Orchestrator delegates both Manager reviews and Specialist work, and passes the Specialist return to the Manager subagent for review. This is the **sequential fallback** and the default posture.
- Optionally, the user may set `experimental.subagent_depth: 2` in project config to let a Manager subagent launch Specialist subagents. That key is experimental and may change; the adapter templates include it only as a commented-out, opt-in block.
- The Orchestrator remains the only user-facing role in both modes; subagent permissions restrict what each agent may do (§6).

## 4. Generated paths (installed into a target project)

```text
<target-project>/
├── AGENTS.md                                  # from AGENTS-TARGET.md (merge policy in §7)
├── opencode.jsonc                             # from opencode.jsonc (merge/ask policy in §7)
└── .opencode/
    ├── agents/
    │   ├── orchestrator.md
    │   ├── manager-architecture.md
    │   ├── manager-engineering.md
    │   ├── manager-quality.md
    │   ├── manager-delivery.md
    │   └── specialist.md
    └── commands/
        ├── blueprint-startup.md
        ├── blueprint-next.md
        ├── blueprint-task.md
        ├── blueprint-handoff.md
        └── blueprint-consolidate.md
```

All provider templates live in `adapters/opencode/templates/`; the manifest
maps generated provider files to those sources. The full project initializer
remains TASK-013. The source-repository Python completion helper is deliberately
not copied into generated projects.

## 5. Limitations

- `experimental.subagent_depth` is experimental; behavior may change or disappear.
- No native construct maps a Manager to a *coordinating* process at depth 1; Manager review is report-based unless depth 2 is enabled.
- The primary agent selection is per session; enabling `/blueprint-*` commands does not force the session to `orchestrator` except where the command sets `agent`.
- OpenCode reloads config automatically but the adapter does not rely on hot reload for correctness.
- Skills exist but are not required; this baseline does not install skills, so nothing depends on skill discovery.

## 6. Permissions model

- **orchestrator:** may `edit` anywhere in the project; may launch `manager-*` and `specialist` subagents; `shell` unrestricted except user-configured overrides.
- **manager-*:** `edit` and `shell` denied (review/research only); `subagent` denied unless the user opts into depth 2, in which case only `specialist` is allowed. This enforces "managers review, specialists execute."
- **specialist:** `edit` allowed inside the project; `subagent` denied; must return evidence and proposals.

Permissions are a safety net; the role contracts in the agent bodies remain the primary boundary.

## 7. Collision and preservation policy (ADAPT-005 / OC-007)

Before installing anything, the adapter generator detects, classifies, and
reports every destination before writing:

| Existing path | Action without approval | With explicit approval |
| --- | --- | --- |
| Absent | Create. | — |
| `AGENTS.md` present | Append a marked managed section; preserve content outside that section. | Replace only the named conflicting file. |
| `opencode.json(c)` present | Merge missing, non-conflicting top-level adapter keys while preserving existing keys and comments. | Replace only the named conflicting file. |
| `.opencode/agents/*` name collision | Merge a previously generated managed body; an unmarked or user-edited collision is a conflict. | Replace only the named conflicting file. |
| `.opencode/commands/*` name collision | Same as above. | Same. |
| Unknown `.opencode/` content | Preserve untouched; list in the conformance report. | — |

Run `python3 scripts/regenerate_opencode_adapter.py --target <project> --dry-run`
to inspect `CREATE`, `MERGE`, `SKIP`, and `CONFLICT` results without writes.
Compatible JSONC merges retain user values. Managed Markdown blocks include a
content hash: upstream changes update an unmodified block, while edits inside
that block become conflicts. Any unapproved conflict prevents every planned
write. An exact `--approve-overwrite <relative-path>` is required to replace a
conflict; approving one path does not approve any other path. Re-running an
unchanged installation reports `SKIP` and is idempotent.

## 8. Canonical memory remains authoritative (ADAPT-003)

- Nothing outside `.blueprint/` is canonical for tasks, memory, decisions, or approvals.
- `AGENTS.md`, `opencode.jsonc`, agents, and commands reference `.blueprint/...` paths; they never copy task or decision content.
- The adapter triggers writes through commands that instruct the Orchestrator role to follow the memory/task protocols.

## 9. Conformance report (ADAPT-006)

| Core scenario | Status | Mechanism / evidence |
| --- | --- | --- |
| Fresh-session context loading | Implemented | `AGENTS.md` startup directive + `/blueprint-startup` command. |
| Task selection honoring dependencies | Implemented | `/blueprint-next` command (registry-authoritative rules). |
| Task execution workflow | Implemented | `/blueprint-task TASK-NNN` command. |
| Handoff workflow | Implemented | `/blueprint-handoff` command. |
| Memory consolidation | Implemented | `/blueprint-consolidate` command (proposal review → owner write). |
| Orchestrator sole user-facing role | Implemented | Agent bodies + `default_agent` + permissions. |
| Manager review / specialist execution boundary | Implemented | Distinct agent files with permission rules. |
| Sequential fallback (depth 1) | Supported by default | Documented in §3. |
| Nested delegation (depth 2) | Optional, experimental | Commented `experimental` block in `opencode.jsonc`. |
| Collision-safe adapter regeneration | Implemented | `scripts/regenerate_opencode_adapter.py`; behavioral scenarios in `tests/test_opencode_regeneration.py`. |
| Reproducible adapter generation (ADAPT-007) | Implemented | `adapters/opencode/manifest.json` maps managed targets to source templates; repeat runs skip unchanged files. |
| Evidence-gated completion in this repository | Implemented | `scripts/task_lifecycle.py` reruns recorded checks, validates evidence/review/canonical agreement, and synchronizes `done`; it is not installed in target projects. |
| Target runtime portability | Preserved | Generated adapter paths contain no Python files or Python invocations; target projects do not inherit an internal Blueprint runtime requirement. |
| Fresh-session resume verified live | Verified (TASK-010) | The Crouton Alpha Free OpenCode 2.2.5 run verified cold start, dependency-based selection, evidence-backed completion, and handoff production/consumption; see `docs/reviews/2026-11-04-task-010-verification.md`. |

## 10. Verification evidence (TASK-009)

All commands were observed during verification on 2026-11-04 in the simulated target project `/private/var/folders/pg/…/T/opencode/task-009-smoke` (generated from `templates/` plus a minimal `.blueprint/`):

- `./scripts/verify-opencode-adapter.py` → `RESULT: PASS` (template structure, frontmatter shape, no V1 deprecated fields, canonical-path discipline, JSONC validity, no secrets).
- `opencode --version` → `opencode v2.2.5`.
- `opencode debug config` → resolved sources: project `opencode.jsonc` with `$schema", "default_agent": "orchestrator", "instructions": []` and the project `.opencode/` directory, alongside the global directory.
- `opencode debug agents` → all six adapter agents discovered with correct modes: `orchestrator` (primary) plus `manager-architecture`, `manager-engineering`, `manager-quality`, `manager-delivery`, `specialist` (subagents).
- `opencode run --agent orchestrator --model opencode/glm-5.3-flash-free /blueprint-next` → the command expanded and the orchestrator ran against the smoke project's canonical records: read `registry.json`, `config/project.json`, `memory/CURRENT_STATE.md`, linked `SPEC-001-test.md`, and the `TASK-002` brief; selected `TASK-002` (dependency `TASK-001` done, ties satisfied); and correctly refused to execute the undetailed task, reporting a blocker naming the missing acceptance criteria/spec and asking one question. This demonstrates fresh-session context loading, dependency-honoring selection, and the pause-before-material-action boundary on `v2.2.5`.
- TASK-010 later verified fresh-session loading, task selection, evidence-backed completion, and handoff production/consumption live; see `docs/reviews/2026-11-04-task-010-verification.md`.
- V1 behavior claims from earlier reviews are **not** reused; every field in the templates comes from the V2 pages listed in §1.

## 11. Observability/monitor compatibility notes (informational; TASK-019 owns the contract)

The observability contract now lives in `docs/architecture/observability.md` (ADR-008, TASK-019) and the monitor implementation in `adapters/opencode/monitor/`. Adapter-facing notes:

- Canonical state the monitor will read: tasks (`registry.json`), current state (`CURRENT_STATE.md`), decisions, blockers, approvals, handoffs — all under `.blueprint/`.
- **Context B (generated projects):** the adapter templates operate from the project root with `.blueprint/` present; a monitor can resolve canonical paths by locating `.blueprint/` from the OpenCode working directory upward, the same resolution the startup command performs.
- **Context A (this Blueprint repository):** development memory lives at root `memory/`, `tasks/`, `specs/`, `handoffs/` with **no** `.blueprint/`. A monitor must not be forced to copy or migrate that data; the resolution rule must be "nearest canonical root," documenting the layout variant per project (implemented in the shared monitor reader, `adapters/opencode/monitor/src/blueprint.ts`).
- Adapter constraints the monitor can rely on: the adapter never embeds task/decision content in `AGENTS.md`, agents, or commands; it only references canonical paths. So a monitor reading `.blueprint/` (or the documented root-memory equivalent) sees complete canonical state.
- The monitor is an **optional** OpenCode TUI plugin; the adapter templates and workflows are fully usable without it (`adapters/opencode/monitor/README.md` documents install/not-install and degradation).

## 12. What this task deliberately does not do

- No full canonical Blueprint initializer (TASK-013) and no full validation harness (TASK-014).
- No general overwrite approval UI; approval is an exact-path CLI option.
- No additional monitor implementation is in scope; TASK-019 owns the optional Blueprint state monitor, which is distinct from live tool-execution monitoring.
- No skills or plugins installed by default.
