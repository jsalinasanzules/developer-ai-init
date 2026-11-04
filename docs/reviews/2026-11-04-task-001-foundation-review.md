# TASK-001 — Foundation and OpenCode Review

- Date: 2026-11-04
- Owner role: ORCHESTRATOR
- Status: review complete, awaiting user approval on material decisions
- Specs reviewed: SPEC-001 through SPEC-009
- Repository state at review: branch `main`, working tree clean before review edits
- Reviewer environment: OpenCode `v2.2.5` (observed with `opencode --version`)

## 1. Executive summary

The foundation is coherent and directionally sound. Vision, architecture, specifications, task registry, backlog, templates, and development memory agree on the core model:

- Git-native, project-owned Markdown/JSON memory is canonical.
- No database or hosted memory service is required.
- Authority is `USER → ORCHESTRATOR → MANAGERS → SPECIALISTS`.
- The Orchestrator is the only user-facing role.
- OpenCode is the first adapter, but the core remains provider-neutral.
- Material decisions and destructive actions require explicit user approval.

No blocking contradiction was found in the normative specifications. Several documentation records were stale or internally imprecise; those non-material issues were corrected during this review (see §3).

Two material provider decisions remain open and require user approval before TASK-009:

1. Which OpenCode generation baseline to target: V2-native, V1-first, or dual-generation.
2. How to represent the three-level hierarchy given OpenCode's default subagent depth of 1.

A third decision, the initializer/validator implementation stack, can be deferred until TASK-012/TASK-013 without blocking TASK-002 through TASK-008.

## 2. Method and evidence

### 2.1 Repository checks

| Check | Command | Result |
| --- | --- | --- |
| Working tree before review | `git status --short` | Clean |
| JSON syntax | Python `json.load` over all `*.json` | Pass: `tasks/registry.json` valid |
| Markdown relative links | Python link scan over all `*.md` | Pass: 0 broken relative links |
| Registry dependencies | Python graph scan | Pass: all dependency IDs exist, no cycles |
| Registry ↔ task files | Python metadata comparison | Pass: statuses, specs, and dependencies match for all 18 tasks |
| Git history | `git log --oneline -10` | Foundation and all 18 task briefs committed |
| File tree | `find` excluding `.git` | All referenced foundation files present |

### 2.2 OpenCode sources consulted (2026-11-04)

Official documentation only:

- https://opencode.ai/docs/ — OpenCode 1 documentation entry point; page states OpenCode 2 is now available.
- https://opencode.ai/docs/agents/ — V1 agent types, `.opencode/agents/`, V1 frontmatter fields.
- https://opencode.ai/docs/config/ — V1 configuration locations and schema.
- https://opencode.ai/docs/commands/ — V1 `.opencode/commands/` and `command` config.
- https://opencode.ai/docs/skills/ — V1 `.opencode/skills/<name>/SKILL.md` requirements.
- https://opencode.ai/docs/rules/ — V1 `AGENTS.md` discovery and `instructions`.
- https://opencode.ai/v2/docs/ — OpenCode 2 documentation entry point.
- https://opencode.ai/v2/docs/config — V2 `opencode.json(c)`, `.opencode/opencode.json(c)`, `agents`, `permissions`, `commands`.
- https://opencode.ai/v2/docs/agents — V2 agent modes, Markdown agents, `permissions`, `system`, subagent behavior.
- https://opencode.ai/v2/docs/skills — V2 skill discovery, IDs, frontmatter, precedence.
- https://opencode.ai/v2/docs/commands — V2 Markdown/JSON commands, `subagent`, arguments.
- https://opencode.ai/v2/docs/instructions — V2 `AGENTS.md` discovery and `instructions`.
- https://opencode.ai/v2/docs/migrate-v1 — V1→V2 compatibility, breaking changes, unsupported fields.

Local observation: `opencode --version` → `opencode v2.2.5`.

## 3. Foundation consistency findings

### 3.1 Corrected during this review

| ID | Finding | Resolution |
| --- | --- | --- |
| F-01 | `README.md` described the repository as still at the foundation stage and said architecture/specs "will be added", although they already exist. | Status and navigation updated to reflect the actual baseline. |
| F-02 | `memory/CURRENT_STATE.md` said remaining scaffold files were still being added. | Replaced with the verified current state and TASK-001 review status. |
| F-03 | `tasks/TASK-TEMPLATE.md` had no explicit blocker field, although SPEC-005 (`TASK-007`) and `docs/architecture/task-lifecycle.md` require blocked tasks to name blocker, owner, and next action. | Added a `## Blockers` section. |
| F-04 | `specs/README.md` claimed every spec contains purpose, scope, requirements, acceptance criteria, dependencies, and open questions. SPEC-003, 005, 006, 007, 008, and 009 use compact forms and omit some of those headings. | Wording corrected: sections are required where applicable; compact specs may omit empty sections. |
| F-05 | `docs/architecture/provider-adapters.md` said OpenCode conventions are inspected "during TASK-009", while TASK-001 also requires current-documentation validation. | Clarified that TASK-001 records the baseline and TASK-009 must revalidate before implementation. |
| F-06 | `tasks/README.md` referred to task Markdown files "when created", although all 18 exist. | Wording corrected. |
| F-07 | The historical foundation handoff says `.gitignore` was not created because of an HTTP 422. The file exists and is committed. | Historical handoff left unchanged as a record; noted here and in the new handoff. |

### 3.2 Open items, not contradictions

| ID | Item | Owner task |
| --- | --- | --- |
| O-01 | The target-project tree in `docs/architecture/memory-model.md` does not show individual task files or a schema directory. Ownership and exact layout are intentionally unresolved. | TASK-002 |
| O-02 | JSON schemas, schema versioning, and validation tooling are not defined. | TASK-003 / TASK-014 |
| O-03 | Adapter manifest fields are described as "proposed", not yet a versioned schema. | TASK-003 / TASK-009 |
| O-04 | Initializer/validator implementation language and distribution are undecided. | TASK-012 / TASK-013 |
| O-05 | OpenCode V1 versus V2 generation baseline is undecided. | Material decision MD-001 |
| O-06 | True three-level delegation exceeds OpenCode's default subagent depth. | Material decision MD-002 |

### 3.3 Scope statement

TASK-001 did not implement adapter files, schemas, or initializer code. The corrections above only remove stale or inaccurate statements and align templates with already-approved requirements.

## 4. OpenCode capability findings

### 4.1 Version landscape

OpenCode 1 and OpenCode 2 share the `opencode` command and are not installed side by side by default. V2 is current and is the version installed in this environment (`v2.2.5`). The V1 documentation remains online and is still the default `/docs/` path, while V2 lives under `/v2/docs/`.

V2 is intended to read supported V1 configuration and existing `.opencode/` files without rewriting them. Native V2 configuration uses different shapes:

| Concern | V1 | V2 |
| --- | --- | --- |
| Agent map key | `agent` | `agents` |
| Agent prompt | `prompt` (JSON) | `system` (JSON); Markdown body for files |
| Permissions | `permission` object | ordered `permissions` array |
| Commands key | `command` | `commands` |
| Delegated command | `subtask` | `subagent` (`subtask` accepted as legacy) |
| Project config | `opencode.json(c)` | `opencode.json(c)` or `.opencode/opencode.json(c)` |
| Subagent depth | top-level `subagent_depth` | `experimental.subagent_depth`; top-level is ignored in V2 |
| Instruction files | `AGENTS.md` plus `CLAUDE.md` fallback | `AGENTS.md` only |

### 4.2 Portable constructs

Across both versions, the following project-local paths are supported:

- `.opencode/agents/<name>.md`
- `.opencode/commands/<name>.md`
- `.opencode/skills/<skill-id>/SKILL.md`
- root `AGENTS.md`

Markdown commands and skills are the most portable adapter surface. Agent Markdown frontmatter is less portable: V1 frontmatter is deprecated but translated by V2, while V2-native `permissions`/`system` files are not understood by V1. A file that mixes both formats is read as V2 and its V1 fields are ignored.

### 4.3 Hierarchy mapping

| Core role | OpenCode construct | Constraints |
| --- | --- | --- |
| Orchestrator | Primary agent (`mode: primary`) | Only primary agent exposed to the user; can launch subagents subject to permissions. |
| Manager | Subagent (`mode: subagent`) | Can review specialist output only if it can launch specialists or if delegation is sequenced by the Orchestrator. |
| Specialist | Subagent (`mode: subagent`) | Runs in a fresh child session; returns evidence to its parent. |

Critical constraint: OpenCode's default subagent depth is `1`, meaning a primary agent can launch subagents, but those subagents cannot launch further subagents. In V2 the setting is `experimental.subagent_depth: 2`; in V1 it is top-level `subagent_depth: 2`. True `ORCHESTRATOR → MANAGER → SPECIALIST` delegation therefore requires either:

- enabling depth 2 (experimental in V2), or
- having the Orchestrator launch specialists directly while managers remain logical reviewers, or
- using the documented sequential single-agent fallback.

This must be decided before TASK-008/TASK-009 and recorded in the adapter documentation and decision log.

### 4.4 Security and permissions

- V2 allows `external_directory` access by default, unlike V1, which asks. The adapter should explicitly set `external_directory` to `ask` to preserve the safer baseline.
- V1 `tools` is deprecated in favor of permissions; V2 uses ordered permission rules with last-match-wins semantics.
- The adapter must never overwrite an existing `opencode.json(c)`, `.opencode/`, or `AGENTS.md`. It must detect, preview, merge with approval, or skip.

### 4.5 Memory integration

Canonical memory remains `.blueprint/`. OpenCode should load it through:

- a concise root `AGENTS.md` (or a generated block appended with approval),
- `instructions` entries pointing at stable `.blueprint/` startup files where the provider supports them,
- custom commands and skills that implement startup, task execution, memory consolidation, and handoff.

Provider-native files are pointers and workflows, never the sole source of project knowledge.

## 5. Risks

| ID | Risk | Impact | Mitigation |
| --- | --- | --- | --- |
| R-01 | V1 and V2 have materially different native schemas. | A dual-target adapter may generate files that only one version reads correctly. | Choose a primary baseline; document the secondary compatibility path and test it. |
| R-02 | Subagent depth 2 is experimental in V2. | True hierarchical delegation may change or break. | Keep a sequential fallback and document the limitation. |
| R-03 | Generated `AGENTS.md` or `opencode.json` can collide with user-owned configuration. | Data loss or broken user setup. | Preview, merge, require approval, and never overwrite silently. |
| R-04 | V2's default external-directory permission is more permissive than V1. | Unintended filesystem access. | Set explicit `external_directory: ask` rules. |
| R-05 | Stale documentation can mislead a fresh session. | Wrong next action or false completion claims. | This review's corrections plus future current-state updates. |
| R-06 | Implementation stack is undecided. | Blocks initializer and validator tasks. | Decide before TASK-012/TASK-013. |

## 6. Material decisions requiring approval

### MD-001 — OpenCode generation baseline

- Option A (recommended): **V2-native first.** Generate V2-native agents/commands/config, document V1 limitations, and keep Markdown commands/skills in a portable subset where practical.
  - Rationale: V2 is current, installed locally, and the documentation marks V1 as legacy. V2 reads supported V1 configuration, so migration from V1 remains possible.
  - Consequence: V2-native agent permissions are not usable by V1; conformance claims must be V2-scoped.
- Option B: **V1-first.** Generate V1-compatible files that V2 translates.
  - Rationale: maximises immediate compatibility with existing V1 setups.
  - Consequence: uses deprecated V1 frontmatter; V2 may warn, and future V1 removal would force a migration.
- Option C: **Dual generation.** Generate separate V1 and V2 variants with a manifest.
  - Rationale: explicit support for both.
  - Consequence: more files, more tests, and a larger conformance matrix; not recommended for the first adapter.

### MD-002 — Hierarchy delegation strategy

- Option A (recommended): **Enable depth 2 as an opt-in adapter setting**, document it as experimental in V2, and provide the sequential fallback when unavailable.
  - Rationale: preserves the approved MANAGER layer as a real coordinator/reviewer.
- Option B: **Flatten delegation.** Orchestrator launches specialists directly; managers are logical review roles implemented through prompts or commands.
  - Rationale: works with default depth 1 and avoids experimental settings.
  - Consequence: weakens the manager/ specialist separation at runtime.
- Option C: **Sequential only.** One agent activates roles in order.
  - Rationale: maximum provider portability.
  - Consequence: no concurrent isolation; slower and less faithful to the hierarchy.

### MD-003 — Initializer/validator implementation stack (deferred)

Not required to start TASK-002. It must be decided before TASK-012/TASK-013. Candidate directions:

- Node.js ESM with minimal runtime dependencies (best alignment with the OpenCode ecosystem, built-in JSON support).
- Python 3 standard library CLI (broad availability, no build step, custom validation code).
- POSIX shell only (maximum portability, weak structured validation and testing).

## 7. Recommended next steps

1. Obtain approval for MD-001 and MD-002.
2. Mark TASK-001 `done` and record the approved decisions in `memory/DECISIONS.md`.
3. Start TASK-002 (target-project directory and file ownership) with the approved provider baseline as context.
4. Revalidate the OpenCode baseline again during TASK-009, as required by SPEC-007.

## 8. Verification appendix

| Check | Result |
| --- | --- |
| `tasks/registry.json` parses as JSON | Pass |
| All task dependency IDs exist | Pass |
| Dependency graph is acyclic | Pass |
| All 18 task files exist | Pass |
| Registry and task-file status/spec/dependency metadata agree | Pass |
| All relative Markdown links resolve | Pass |
| Official OpenCode sources cited with access date | Pass |
| Local OpenCode version observed | `v2.2.5` |
| Adapter implementation performed | No — out of scope for TASK-001 |
