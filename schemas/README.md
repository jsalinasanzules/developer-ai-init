# JSON Schemas

Versioned machine-readable contracts for the blueprint. These schemas are installed into a target project under `.blueprint/schemas/`.

## Version

- Schema version: **1.0.0**
- JSON Schema dialect: **draft 2019-09**
- Instance `schema_version` and `$id` carry the same version.
- A consumer MUST select the schema matching the instance's declared version. An unknown version is a blocking error, not something to guess.

## Schema index

| Schema | Instance path | Purpose |
| --- | --- | --- |
| `manifest.schema.json` | `.blueprint/manifest.json` | Installed blueprint version, file inventory, install hashes, migrations. |
| `project.schema.json` | `.blueprint/config/project.json` | Project identity, purpose, stack, constraints, provider preferences, initialization completeness. |
| `agents.schema.json` | `.blueprint/config/agents.json` | Logical roles, authority chain, delegation mode, approval policy. |
| `memory-metadata.schema.json` | `.blueprint/memory/metadata.json` | Record paths, ownership, classes, last-update metadata, optional derived pointers. |
| `task-registry.schema.json` | `.blueprint/tasks/registry.json` | Task status, priority, owner role, specs, dependencies, blockers. |

Task briefs (`tasks/items/TASK-*.md`), decisions, sessions, and handoffs remain Markdown; they are governed by templates and cross-reference rules, not JSON Schema.

## Versioning policy

Use Semantic Versioning for the schema contract:

- **MAJOR** — removes or renames a required field, changes a type, changes enum meaning, or otherwise invalidates existing valid instances.
- **MINOR** — adds an optional field or a new schema while preserving existing instances.
- **PATCH** — clarifies descriptions, patterns, or documentation without changing accepted instances.

Because schemas use `additionalProperties: false`, adding a field requires a version bump. A new version is published as a new `$id`; old schemas are retained for migration. Do not reinterpret an existing version in place.

## Cross-reference and semantic rules

JSON Schema validates shape. The following rules require a separate validator or review step because JSON Schema alone cannot enforce them or cannot express them without awkward duplication.

### Task registry

- **R-TASK-01:** Task IDs are unique; registry IDs match `tasks/items/TASK-<NNN>.md` files.
- **R-TASK-02:** Every dependency ID exists, no task depends on itself, and the graph is acyclic.
- **R-TASK-03:** Status transitions follow `proposed → ready → in_progress → in_review → done`, with `blocked` and `cancelled` handled as documented in the task lifecycle.
- **R-TASK-04:** A `done` task has evidence for every acceptance criterion in its Markdown brief. The registry cannot prove this.
- **R-TASK-05:** A `blocked` task has `blocked.reason`, `blocked.responsible_role`, and `blocked.next_action`; a non-blocked task does not carry a blocker object.
- **R-TASK-06:** Every `SPEC-*` reference resolves to an existing specification.
- **R-TASK-07:** `owner_role` maps to a configured role in `agents.json` or to `ORCHESTRATOR`/`USER`.
- **R-TASK-08:** `backlog.md` is synchronized with the registry; the registry wins on conflict.
- **R-TASK-09:** Registry title, status, specs, owner role, and dependencies agree with the task brief.

### Agent roles

- **R-ROLE-01:** Role IDs are unique across orchestrator, managers, and specialists.
- **R-ROLE-02:** Exactly one orchestrator exists and its `kind` is `orchestrator`.
- **R-ROLE-03:** The orchestrator has no `reports_to`; every manager reports to the orchestrator; every specialist reports to a manager.
- **R-ROLE-04:** Every `reports_to` and `can_delegate_to` reference resolves to an existing role.
- **R-ROLE-05:** Delegation references are acyclic and consistent with `delegation.mode` and `delegation.max_depth`.
- **R-ROLE-06:** Specialists do not approve material product, architecture, security, or privacy decisions.

### Project and memory metadata

- **R-PROJ-01:** `project.slug` equals `memory-metadata.project_id`.
- **R-PROJ-02:** `initialization.status` is `complete` only when `unknowns` is empty; otherwise unknowns remain explicit.
- **R-MEM-01:** Every memory record path exists and is inside `.blueprint/`.
- **R-MEM-02:** Record class matches the target layout classification.
- **R-MEM-03:** Derived paths live under `.blueprint/derived/` and remain rebuildable.
- **R-MEM-04:** `last_task` references an existing task when present.

### Manifest and upgrades

- **R-MAN-01:** Every manifest path is relative to `.blueprint/`, contains no `..`, and exists.
- **R-MAN-02:** SHA-256 values match the install-time file content; mismatches identify user modification.
- **R-MAN-03:** The file inventory covers every installed blueprint-managed file.
- **R-MAN-04:** `blueprint_version` and `schema_version` are known to the upgrader; unknown versions stop the upgrade.
- **R-MAN-05:** Migration entries are ordered and do not skip a required intermediate version.

### Global

- **R-GLOBAL-01:** Dates are ISO 8601; `updated_at` is not earlier than `created_at` where both exist.
- **R-GLOBAL-02:** No secrets, credentials, tokens, private keys, or unnecessary sensitive personal data.
- **R-GLOBAL-03:** Blocking errors are reported separately from warnings; validation never mutates project state.

These rules belong to the validation task (TASK-014) and must be implemented or explicitly reviewed there.

## Fixtures

`fixtures/valid/` contains one valid instance per schema. `fixtures/invalid/` contains targeted invalid instances:

| Fixture | Expected failure |
| --- | --- |
| `project-invalid-slug.json` | Slug pattern. |
| `project-missing-schema-version.json` | Missing required version. |
| `agents-invalid-delegation.json` | Invalid delegation mode and depth. |
| `agents-missing-orchestrator.json` | Missing required orchestrator. |
| `memory-invalid-class.json` | Invalid record class. |
| `memory-missing-last-updated.json` | Missing required record field. |
| `task-registry-invalid-status.json` | Invalid status enum. |
| `task-registry-blocked-without-blocker.json` | Blocked status without blocker details. |
| `manifest-invalid-hash.json` | Invalid SHA-256 format. |
| `manifest-path-traversal.json` | Path outside `.blueprint/`. |

## Verification

The schemas were verified with `ajv-cli` using draft 2019-09. This is a test tool for this repository, not a decision about the product's validation runtime (MD-003 remains deferred).

```bash
./schemas/verify-fixtures.sh
```

Equivalent single check:

```bash
npx --yes ajv-cli test \
  -s schemas/project.schema.json \
  -d schemas/fixtures/valid/project.json \
  --valid --spec=draft2019
```

Expected result: every valid fixture passes; every invalid fixture fails for the reason listed above. The script exits non-zero if any expectation is violated.
