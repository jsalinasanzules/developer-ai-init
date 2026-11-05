# Blueprint Validation

- Status: implemented baseline for TASK-014
- Date: 2026-11-05
- Related: SPEC-009, SPEC-002, SPEC-005, ADR-009, ADR-011

## Runtime and offline behavior

`scripts/validate_blueprint.py` is a read-only source-repository tool. It uses
Python 3.9+ and the pinned `jsonschema` package in
`requirements-validation.txt`; this dependency is not copied into generated
projects. Install the dependency before disconnecting from the network. The
validation command itself makes no network requests and fails closed on
non-local JSON Schema `$ref`/`$recursiveRef` values.

Run the complete source-project validation from the repository root:

```sh
python3 scripts/validate_blueprint.py --root .
```

Validate only schema definitions and their fixtures:

```sh
./schemas/verify-fixtures.sh
```

Exit code `0` means no blocking errors; `1` means validation findings; `2`
means the validation root could not be accessed. `ERROR` findings block
validation. `WARNING` findings are reported separately and do not change
project files.

## Validation coverage

- Schema files must parse as JSON, declare Draft 2019-09, pass the draft's
  meta-schema, and use only local references.
- Valid/invalid JSON fixtures are checked against the matching schema.
- The source task registry is checked against its schema and semantic rules:
  unique task IDs, existing task/spec references, no self-dependencies or
  dependency cycles, registry/brief agreement for title, status, owner,
  specifications, and dependencies, plus one backlog entry per task with the
  registry status. Backlog titles may be concise summaries; the registry and
  task briefs retain the authoritative full title.
- `CURRENT_STATE.md` must identify the registry's sole active task
  (`in_progress` or `in_review`) with its matching status, or say `None` if
  there is no active task.
- Adapter manifest sources must resolve to regular files inside the adapter;
  destination paths must be safe and unique. Manifest-declared JSONC files are
  parsed with the existing JSONC parser.
- Secret heuristics scan `AGENTS.md`, `README.md`, `memory/`, `tasks/`,
  `specs/`, `schemas/`, the OpenCode adapter manifest, and its shipped
  templates. `.git/`, `.opencode/`, adapter monitor source, and external
  symlink targets are not traversed.

Diagnostics identify a file and field/line plus a constraint or pattern
label. They never include schema instance values or matched secret material.
Secret detection is heuristic: it can miss unknown formats and may flag
non-secret values. Review findings without copying their contents into reports.

## Development and evidence

Install the approved dependency with:

```sh
python3 -m pip install -r requirements-validation.txt
```

Tests use local fixtures and temporary copies. They cover invalid schemas and
instances, malformed JSONC, missing references, duplicate IDs, dependency
cycles, canonical-record drift, adapter path safety, redacted secret
diagnostics, offline behavior, and no-mutation guarantees.
