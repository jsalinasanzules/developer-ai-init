# Blueprint Generation and Approval

- Status: implemented baseline for TASK-013
- Date: 2026-11-05
- Related: TASK-012, TASK-013, TASK-020, ADR-009, ADR-010

## Scope and runtime boundary

`scripts/build_blueprint.py` consumes confirmed project facts and plans a
canonical `.blueprint/` installation. It does not discover a repository,
interview the user, infer unknown facts, or make approval decisions. The
Orchestrator performs TASK-012's discovery and interview, prepares the confirmed
input, and obtains separate user confirmation of the summary, complete write
plan, and each exact conflict path.

The generator is Python 3.9+ standard-library tooling for this source
repository only. It is never copied into generated projects. The Blueprint
release version has one source of truth in [`blueprint/catalog.json`](../../blueprint/catalog.json);
schema versions are read from the canonical schemas.
Increment the catalog release version when changing a shipped Blueprint
template or its behavior; do not silently reinterpret an existing version.

## Confirmed input

Pass a UTF-8 JSON object containing exactly these fields:

```json
{
  "project": {
    "name": "Sample App",
    "slug": "sample-app",
    "description": "A user-confirmed one-sentence purpose.",
    "status": "new"
  },
  "purpose": {
    "summary": "A user-confirmed one-sentence purpose.",
    "users": [],
    "goals": [],
    "non_goals": []
  },
  "stack": [],
  "constraints": [],
  "providers": [],
  "initialization": {
    "status": "partial",
    "unknowns": ["Scope, domain, architecture, and conventions remain unknown and non-blocking."],
    "assumptions": []
  },
  "context": {
    "scope": "",
    "domain": "",
    "architecture": "",
    "conventions": ""
  },
  "selected_adapters": []
}
```

Every non-empty fact must be confirmed. Use empty strings only for the optional
narrative context that remains unknown. Required scalar project facts cannot
be blank. `complete` requires no unknowns; `partial` requires at least one
explicit, non-blocking unknown, consistent with TASK-012 and R-PROJ-02.
Blank narrative context is retained as unknown and therefore requires a
`partial` initialization; use explicit confirmed text such as "not applicable"
when the user has established that a field does not apply.
`selected_adapters` must be a subset of confirmed providers with adapter
manifests in this repository. Every selected adapter's destinations are
combined into the same plan, and case-colliding destinations block generation.

## Approval sequence

Run commands from the repository root. Replace the paths and hashes with the
values for the intended target:

1. **Review and confirm the exact summary.**

   ```sh
   python3 scripts/build_blueprint.py \
     --target /path/to/project \
     --input /path/to/confirmed-project.json \
     --show-summary
   ```

   The command prints the complete confirmed input and a
   `SUMMARY_SHA256`. It performs no writes. The Orchestrator asks the user to
   confirm this summary before continuing.

2. **Preview every operation.**

   ```sh
   python3 scripts/build_blueprint.py \
     --target /path/to/project \
     --input /path/to/confirmed-project.json \
     --confirm-summary SUMMARY_SHA256 \
     --dry-run
   ```

   Review the full path-by-path plan, diffs, unknown paths preserved, and
   `PLAN_SHA256`. `CREATE`, `MERGE`, `SKIP`, and `CONFLICT` are distinct
   outcomes. An unresolved conflict blocks the complete plan without writes.

3. **Resolve only explicitly approved conflicts, then preview again.**

   ```sh
   python3 scripts/build_blueprint.py \
     --target /path/to/project \
     --input /path/to/confirmed-project.json \
     --confirm-summary SUMMARY_SHA256 \
     --approve-overwrite .blueprint/config/project.json \
     --dry-run
   ```

   Repeat `--approve-overwrite` for each separately approved relative path.
   The approval applies to that regular file or exact missing managed path
   only; it cannot approve a directory, symlink, deletion, or other path.
   Review the revised plan and its new hash.

4. **Apply only the exact approved plan.**

   ```sh
   python3 scripts/build_blueprint.py \
     --target /path/to/project \
     --input /path/to/confirmed-project.json \
     --confirm-summary SUMMARY_SHA256 \
     --approve-overwrite .blueprint/config/project.json \
     --approve-plan PLAN_SHA256
   ```

   The user must have approved the displayed plan before the Orchestrator
   executes this command. Omit overwrite options unless the user approved
   those exact paths. If the summary, template, destination inventory, or
   approval set changes, the plan fingerprint changes and the old approval is
   rejected.

## Collision and failure behavior

- An empty project with no `.git` metadata or meaningful files is greenfield;
  existing files make it brownfield. A supported manifest is already
  initialized. An absent, malformed, or unsupported manifest under an existing
  `.blueprint/` blocks writes for reconciliation.
- Existing files equal to the desired bytes are `SKIP`. Previously managed,
  unchanged files can be `MERGE`d. A user-modified or untracked file at a
  destination is `CONFLICT`; it remains untouched without exact-path approval.
- Missing files recorded in the manifest require exact-path approval before
  recreation. Symlinks, Windows reparse points (including junctions), and
  non-regular destinations cannot be approved or traversed.
- Unknown `.blueprint/` files and manifest inventory records are preserved and
  reported. Provider-native files are planned by the existing adapter
  generator and participate in the same whole-plan approval gate.
- All planned destinations are revalidated before writing. Each file is
  atomically replaced from a same-directory temporary file; no-follow
  directory handles are used where supported, with symlink and reparse-point
  checks on every destination ancestor otherwise.
  Generated content is checked against its planned hashes before
  `manifest.json` is written last.
  A partial failure reports completed and pending paths; it does not attempt
  destructive rollback.
- The final manifest records the approving role, date, summary fingerprint,
  plan fingerprint, and exact overwrite paths.
- The current generator supports the installed Blueprint/schema versions only;
  it does not perform migrations. Unsupported versions must be reconciled or
  handled by a future, explicitly versioned migration.
- Re-running with unchanged input and destinations yields `SKIP` for every
  destination and does not rewrite the manifest.

## Generated ownership boundary

The generator installs the canonical tree documented in
[`target-project-layout.md`](target-project-layout.md), seeded only from the
confirmed input and shipped templates. It does not copy this repository's
tasks, specs, decisions, development memory, or scripts. Provider-native files
are generated only for explicitly selected adapters. No generated path,
content, instruction, or command invokes or requires Python.
