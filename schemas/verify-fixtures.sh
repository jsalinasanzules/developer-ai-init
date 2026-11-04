#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

AJV=(npx --yes ajv-cli)

pass=0
fail=0

run_valid() {
  local schema="$1" data="$2"
  echo "VALID   $data"
  if "${AJV[@]}" test -s "$schema" -d "$data" --valid --spec=draft2019 >/dev/null 2>&1; then
    pass=$((pass + 1))
  else
    echo "  FAILED: expected valid" >&2
    fail=$((fail + 1))
  fi
}

run_invalid() {
  local schema="$1" data="$2"
  echo "INVALID $data"
  if "${AJV[@]}" test -s "$schema" -d "$data" --invalid --spec=draft2019 >/dev/null 2>&1; then
    pass=$((pass + 1))
  else
    echo "  FAILED: expected invalid" >&2
    fail=$((fail + 1))
  fi
}

run_valid schemas/project.schema.json schemas/fixtures/valid/project.json
run_valid schemas/agents.schema.json schemas/fixtures/valid/agents.json
run_valid schemas/memory-metadata.schema.json schemas/fixtures/valid/memory-metadata.json
run_valid schemas/task-registry.schema.json schemas/fixtures/valid/task-registry.json
run_valid schemas/manifest.schema.json schemas/fixtures/valid/manifest.json

run_invalid schemas/project.schema.json schemas/fixtures/invalid/project-invalid-slug.json
run_invalid schemas/project.schema.json schemas/fixtures/invalid/project-missing-schema-version.json
run_invalid schemas/agents.schema.json schemas/fixtures/invalid/agents-invalid-delegation.json
run_invalid schemas/agents.schema.json schemas/fixtures/invalid/agents-missing-orchestrator.json
run_invalid schemas/memory-metadata.schema.json schemas/fixtures/invalid/memory-invalid-class.json
run_invalid schemas/memory-metadata.schema.json schemas/fixtures/invalid/memory-missing-last-updated.json
run_invalid schemas/task-registry.schema.json schemas/fixtures/invalid/task-registry-invalid-status.json
run_invalid schemas/task-registry.schema.json schemas/fixtures/invalid/task-registry-blocked-without-blocker.json
run_invalid schemas/manifest.schema.json schemas/fixtures/invalid/manifest-invalid-hash.json
run_invalid schemas/manifest.schema.json schemas/fixtures/invalid/manifest-path-traversal.json

echo
echo "Fixtures: $pass passed, $fail failed"
if [ "$fail" -ne 0 ]; then
  exit 1
fi
