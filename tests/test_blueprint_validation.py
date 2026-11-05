from __future__ import annotations

import json
import pathlib
import re
import shutil
import socket
import tempfile
import unittest
import urllib.request
from unittest import mock

from scripts import validate_blueprint as validator


ROOT = pathlib.Path(__file__).resolve().parents[1]
COPY_PATHS = (
    "AGENTS.md",
    "README.md",
    "memory",
    "tasks",
    "specs",
    "schemas",
    "adapters/opencode/manifest.json",
    "adapters/opencode/templates",
)


def _snapshot(root: pathlib.Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


class BlueprintValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)
        for relative in COPY_PATHS:
            source = ROOT / relative
            destination = self.root / relative
            if source.is_dir():
                shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)

    def load_registry(self):
        path = self.root / "tasks/registry.json"
        return path, json.loads(path.read_text(encoding="utf-8"))

    def save_registry(self, path, registry):
        path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")

    def task_brief(self, task_id):
        return self.root / "tasks/items" / f"{task_id}.md"

    def errors(self, report):
        return [issue for issue in report.issues if issue.severity == "ERROR"]

    def test_repository_fixture_is_valid_and_validation_is_read_only(self):
        before = _snapshot(self.root)
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")), \
             mock.patch.object(urllib.request, "urlopen", side_effect=AssertionError("network used")):
            report = validator.validate(self.root)
        self.assertEqual(self.errors(report), [])
        self.assertEqual(_snapshot(self.root), before)

    def test_invalid_schema_reports_schema_location_without_schema_value(self):
        path = self.root / "schemas/project.schema.json"
        schema = json.loads(path.read_text(encoding="utf-8"))
        schema["properties"]["project"]["properties"]["slug"]["type"] = "not-a-json-schema-type"
        path.write_text(json.dumps(schema), encoding="utf-8")

        report = validator.Report()
        validator.validate_schemas_and_fixtures(self.root, report, fixtures_only=True)
        rendered = "\n".join(map(str, self.errors(report)))
        self.assertIn("schemas/project.schema.json", rendered)
        self.assertIn("schema validation failed", rendered)
        self.assertNotIn("not-a-json-schema-type", rendered)

    def test_invalid_instance_reports_file_and_field_without_value(self):
        path = self.root / "schemas/fixtures/valid/project.json"
        instance = json.loads(path.read_text(encoding="utf-8"))
        instance["project"]["slug"] = "VERY_PRIVATE_VALUE_0123456789"
        path.write_text(json.dumps(instance), encoding="utf-8")

        report = validator.Report()
        validator.validate_schemas_and_fixtures(self.root, report, fixtures_only=True)
        rendered = "\n".join(map(str, self.errors(report)))
        self.assertIn("schemas/fixtures/valid/project.json", rendered)
        self.assertIn("/project/slug", rendered)
        self.assertNotIn("VERY_PRIVATE_VALUE_0123456789", rendered)

    def test_missing_required_field_is_named_without_printing_instance_values(self):
        path = self.root / "schemas/fixtures/valid/project.json"
        instance = json.loads(path.read_text(encoding="utf-8"))
        instance.pop("schema_version")
        instance["private_context"] = "never print this content"
        path.write_text(json.dumps(instance), encoding="utf-8")

        report = validator.Report()
        validator.validate_schemas_and_fixtures(self.root, report, fixtures_only=True)
        rendered = "\n".join(map(str, self.errors(report)))
        self.assertIn("<missing:schema_version>", rendered)
        self.assertNotIn("never print this content", rendered)

    def test_missing_task_and_spec_references_are_reported(self):
        registry_path, registry = self.load_registry()
        task = registry["tasks"][0]
        task["dependencies"] = ["TASK-999"]
        task["specs"] = ["SPEC-999"]
        self.save_registry(registry_path, registry)
        brief = self.task_brief(task["id"])
        text = brief.read_text(encoding="utf-8")
        text = text.replace("- Specs: SPEC-001, SPEC-002, SPEC-003, SPEC-004, SPEC-005, SPEC-006",
                            "- Specs: SPEC-999")
        text = text.replace("- Dependencies: None", "- Dependencies: TASK-999")
        brief.write_text(text, encoding="utf-8")

        rendered = "\n".join(map(str, self.errors(validator.validate(self.root))))
        self.assertIn("referenced task does not exist", rendered)
        self.assertIn("referenced specification does not exist", rendered)

    def test_dependency_cycle_is_detected(self):
        registry_path, registry = self.load_registry()
        first, second = registry["tasks"][:2]
        first["dependencies"] = [second["id"]]
        self.save_registry(registry_path, registry)
        brief = self.task_brief(first["id"])
        brief.write_text(
            brief.read_text(encoding="utf-8").replace("- Dependencies: None", f"- Dependencies: {second['id']}"),
            encoding="utf-8",
        )

        rendered = "\n".join(map(str, self.errors(validator.validate(self.root))))
        self.assertIn("dependency graph contains a cycle", rendered)

    def test_duplicate_task_ids_are_rejected(self):
        registry_path, registry = self.load_registry()
        registry["tasks"][1]["id"] = registry["tasks"][0]["id"]
        self.save_registry(registry_path, registry)
        rendered = "\n".join(map(str, self.errors(validator.validate(self.root))))
        self.assertIn("task ID is duplicated", rendered)

    def test_backlog_and_current_state_drift_are_reported(self):
        backlog = self.root / "tasks/backlog.md"
        text = backlog.read_text(encoding="utf-8")
        text = re.sub(
            r"(?m)^- \[ \] \*\*TASK-014\*\* \([^)]+\)",
            "- [x] **TASK-014** (done)",
            text,
        )
        backlog.write_text(text, encoding="utf-8")
        state = self.root / "memory/CURRENT_STATE.md"
        state.write_text(state.read_text(encoding="utf-8").replace("TASK-014", "TASK-999"),
                         encoding="utf-8")

        rendered = "\n".join(map(str, self.errors(validator.validate(self.root))))
        self.assertIn("status does not match the task registry", rendered)
        self.assertIn("does not identify the registry's active task", rendered)

    def test_in_review_task_remains_the_active_task(self):
        registry_path, registry = self.load_registry()
        task = next(item for item in registry["tasks"] if item["id"] == "TASK-014")
        task["status"] = "in_review"
        self.save_registry(registry_path, registry)

        brief = self.task_brief("TASK-014")
        brief.write_text(
            brief.read_text(encoding="utf-8").replace("- Status: in_progress", "- Status: in_review"),
            encoding="utf-8",
        )
        backlog = self.root / "tasks/backlog.md"
        backlog.write_text(
            backlog.read_text(encoding="utf-8").replace(
                "**TASK-014** (in_progress)", "**TASK-014** (in_review)"
            ),
            encoding="utf-8",
        )
        state = self.root / "memory/CURRENT_STATE.md"
        state.write_text(
            state.read_text(encoding="utf-8").replace(
                "- Status: `in_progress`", "- Status: `in_review`"
            ),
            encoding="utf-8",
        )

        self.assertEqual(self.errors(validator.validate(self.root)), [])

    def test_jsonc_syntax_errors_are_actionable(self):
        path = self.root / "adapters/opencode/templates/opencode.jsonc"
        path.write_text('{"default_agent": "orchestrator", /* broken */', encoding="utf-8")
        rendered = "\n".join(map(str, self.errors(validator.validate(self.root))))
        self.assertIn("invalid JSONC syntax", rendered)
        self.assertIn("opencode.jsonc", rendered)
        self.assertNotIn("orchestrator", rendered)

    def test_external_schema_reference_is_rejected_without_fetching(self):
        schema_path = self.root / "schemas/project.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        schema["$ref"] = "https://example.invalid/schema.json"
        schema_path.write_text(json.dumps(schema), encoding="utf-8")
        report = validator.Report()
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            schemas = validator.validate_schemas_and_fixtures(self.root, report, fixtures_only=True)
        self.assertNotIn("project.schema.json", schemas)
        rendered = "\n".join(map(str, report.issues))
        self.assertIn("non-local schema references are blocked", rendered)
        self.assertNotIn("example.invalid", rendered)

    def test_malformed_json_is_reported_with_location_only(self):
        path = self.root / "schemas/fixtures/valid/project.json"
        path.write_text('{"api_key":"never print this secret"', encoding="utf-8")
        report = validator.Report()
        validator.validate_schemas_and_fixtures(self.root, report, fixtures_only=True)
        rendered = "\n".join(map(str, self.errors(report)))
        self.assertIn("invalid JSON syntax", rendered)
        self.assertIn("line 1", rendered)
        self.assertNotIn("never print this secret", rendered)

    def test_secret_diagnostics_redact_values(self):
        secret = "sk-supersecret-value-that-must-not-leak"
        path = self.root / "memory/PROJECT_CONTEXT.md"
        path.write_text(f'api_key: "{secret}"\n', encoding="utf-8")

        report = validator.Report()
        validator._scan_secrets(self.root, report)
        rendered = "\n".join(map(str, self.errors(report)))
        self.assertIn("memory/PROJECT_CONTEXT.md", rendered)
        self.assertIn("credential field", rendered)
        self.assertIn("value redacted", rendered)
        self.assertNotIn(secret, rendered)

    def test_adapter_manifest_rejects_unsafe_and_duplicate_destinations(self):
        path = self.root / "adapters/opencode/manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["generated_files"][0]["target"] = "../escape"
        manifest["generated_files"][1]["target"] = manifest["generated_files"][0]["target"]
        path.write_text(json.dumps(manifest), encoding="utf-8")

        rendered = "\n".join(map(str, self.errors(validator.validate(self.root))))
        self.assertIn("target must be a safe relative path", rendered)
        self.assertNotIn("../escape", rendered)


if __name__ == "__main__":
    unittest.main()
