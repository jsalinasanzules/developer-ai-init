from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import io
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from typing import Optional
from unittest import mock

from scripts import build_blueprint as generator


ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST_PATH = ".blueprint/manifest.json"
EXPECTED_CANONICAL_FILES = {
    ".blueprint/README.md",
    ".blueprint/config/project.json",
    ".blueprint/config/agents.json",
    ".blueprint/schemas/manifest.schema.json",
    ".blueprint/schemas/project.schema.json",
    ".blueprint/schemas/agents.schema.json",
    ".blueprint/schemas/memory-metadata.schema.json",
    ".blueprint/schemas/task-registry.schema.json",
    ".blueprint/memory/PROJECT_CONTEXT.md",
    ".blueprint/memory/CURRENT_STATE.md",
    ".blueprint/memory/ARCHITECTURE.md",
    ".blueprint/memory/DECISIONS.md",
    ".blueprint/memory/CONVENTIONS.md",
    ".blueprint/memory/metadata.json",
    ".blueprint/specs/README.md",
    ".blueprint/tasks/registry.json",
    ".blueprint/tasks/backlog.md",
    ".blueprint/tasks/TASK-TEMPLATE.md",
    ".blueprint/tasks/items/README.md",
    ".blueprint/sessions/README.md",
    ".blueprint/sessions/SESSION-TEMPLATE.md",
    ".blueprint/handoffs/README.md",
    ".blueprint/handoffs/HANDOFF-TEMPLATE.md",
}


def confirmed_input(with_opencode: bool = False) -> dict:
    providers = [{"id": "opencode", "role": "primary"}] if with_opencode else []
    return {
        "project": {
            "name": "Sample App",
            "slug": "sample-app",
            "description": "A confirmed sample project.",
            "status": "new",
        },
        "purpose": {
            "summary": "A confirmed sample project.",
            "users": [],
            "goals": [],
            "non_goals": [],
        },
        "stack": [],
        "constraints": [],
        "providers": providers,
        "initialization": {
            "status": "partial",
            "unknowns": ["Scope, domain, architecture, and conventions remain unknown and non-blocking."],
            "assumptions": [],
        },
        "context": {
            "scope": "",
            "domain": "",
            "architecture": "",
            "conventions": "",
        },
        "selected_adapters": ["opencode"] if with_opencode else [],
    }


BASELINE_BYTES = b"previous Blueprint-managed schema\n"


def valid_manifest(files: Optional[list[dict]] = None, blueprint_version: str = "0.1.0") -> dict:
    return {
        "manifest_version": "1.0.0",
        "schema_version": "1.0.0",
        "blueprint_version": blueprint_version,
        "installed_at": "2026-11-05",
        "files": files if files is not None else [
            {
                "path": ".blueprint/schemas/manifest.schema.json",
                "class": "blueprint-managed",
                "template_version": "0.1.0",
                "sha256": hashlib.sha256(BASELINE_BYTES).hexdigest(),
            }
        ],
        "migrations": [],
        "notes": "Test installation.",
    }


class BlueprintGenerationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)

    def build(self, data: Optional[dict] = None, approved: Optional[set[str]] = None):
        return generator.build_plan(self.root, data or confirmed_input(), approved)

    def write_manifest(self, value: Optional[dict] = None):
        path = self.root / MANIFEST_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        value = value or valid_manifest()
        for record in value["files"]:
            destination = self.root / record["path"]
            if not destination.exists() and record["sha256"] == hashlib.sha256(BASELINE_BYTES).hexdigest():
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(BASELINE_BYTES)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        return path

    def install(self, data: Optional[dict] = None) -> tuple[str, list[generator.PlannedFile]]:
        plan_hash, plan, _ = self.build(data)
        self.assertFalse(any(item.outcome == "CONFLICT" for item in plan))
        generator.apply_plan(self.root, plan)
        return plan_hash, plan

    def test_greenfield_plan_is_non_mutating_and_covers_canonical_tree(self):
        plan_hash, plan, unknown = self.build()
        catalog = generator._catalog()
        self.assertEqual({entry["target"] for entry in catalog["files"]}, EXPECTED_CANONICAL_FILES)
        expected = EXPECTED_CANONICAL_FILES | {MANIFEST_PATH}
        self.assertEqual({item.relative_target for item in plan}, expected)
        self.assertTrue(all(item.outcome == "CREATE" for item in plan))
        self.assertFalse(unknown)
        self.assertRegex(plan_hash, r"^[0-9a-f]{64}$")
        self.assertEqual(generator._classify(self.root)[0], "GREENFIELD")
        self.assertFalse((self.root / ".blueprint").exists())

    def test_brownfield_classification_preserves_existing_project_files(self):
        source = self.root / "src/application.txt"
        source.parent.mkdir()
        source.write_text("existing project code\n", encoding="utf-8")
        self.assertEqual(generator._classify(self.root)[0], "BROWNFIELD")
        _, plan, _ = self.build()
        self.assertTrue(all(item.outcome == "CREATE" for item in plan))
        generator.apply_plan(self.root, plan)
        self.assertEqual(source.read_text(encoding="utf-8"), "existing project code\n")
        _, second, _ = self.build()
        self.assertEqual({item.outcome for item in second}, {"SKIP"})
        generator.apply_plan(self.root, second)
        self.assertEqual(source.read_text(encoding="utf-8"), "existing project code\n")

    def test_cli_requires_summary_confirmation_then_exact_plan_approval(self):
        input_dir = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, input_dir)
        input_path = input_dir / "confirmed.json"
        input_path.write_text(json.dumps(confirmed_input()), encoding="utf-8")
        repository = ROOT
        script = repository / "scripts/build_blueprint.py"

        summary = subprocess.run(
            [sys.executable, str(script), "--target", str(self.root), "--input", str(input_path), "--show-summary"],
            cwd=repository,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(summary.returncode, 0, summary.stderr)
        summary_hash = re.search(r"SUMMARY_SHA256: ([0-9a-f]{64})", summary.stdout).group(1)
        self.assertFalse((self.root / ".blueprint").exists())

        preview = subprocess.run(
            [
                sys.executable, str(script), "--target", str(self.root), "--input", str(input_path),
                "--confirm-summary", summary_hash, "--dry-run",
            ],
            cwd=repository,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(preview.returncode, 0, preview.stderr)
        plan_hash = re.search(r"PLAN_SHA256: ([0-9a-f]{64})", preview.stdout).group(1)
        self.assertIn("CREATE", preview.stdout)
        self.assertFalse((self.root / ".blueprint").exists())

        rejected = subprocess.run(
            [
                sys.executable, str(script), "--target", str(self.root), "--input", str(input_path),
                "--confirm-summary", summary_hash, "--approve-plan", "0" * 64,
            ],
            cwd=repository,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("plan approval is stale", rejected.stderr)
        self.assertFalse((self.root / ".blueprint").exists())

        result = subprocess.run(
            [
                sys.executable, str(script), "--target", str(self.root), "--input", str(input_path),
                "--confirm-summary", summary_hash, "--approve-plan", plan_hash,
            ],
            cwd=repository,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / MANIFEST_PATH).is_file())
        self.assertIn("Generation complete", result.stdout)

    def test_generated_manifest_hashes_and_schema_versions_are_sealed_last(self):
        _, plan, _ = self.build()
        original_write = generator._write_atomic
        writes: list[str] = []

        def record_write(root, relative, content):
            writes.append(relative)
            return original_write(root, relative, content)

        with mock.patch.object(generator, "_write_atomic", side_effect=record_write):
            generator.apply_plan(self.root, plan)
        self.assertEqual(writes[-1], MANIFEST_PATH)
        manifest_path = self.root / MANIFEST_PATH
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        schema = json.loads((self.root / ".blueprint/schemas/manifest.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["blueprint_version"], "0.1.0")
        self.assertEqual(manifest["schema_version"], "1.0.0")
        self.assertEqual(manifest["manifest_version"], "1.0.0")
        self.assertEqual(manifest["schema_version"], schema["properties"]["schema_version"]["const"])
        self.assertEqual(manifest["files"], sorted(manifest["files"], key=lambda item: item["path"]))
        for record in manifest["files"]:
            content = (self.root / record["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(content).hexdigest(), record["sha256"])
        notes = manifest["notes"]
        self.assertIn("approved by USER via Orchestrator", notes)
        self.assertRegex(notes, r"summary_sha256=[0-9a-f]{64}")
        self.assertRegex(notes, r"plan_sha256=[0-9a-f]{64}")
        self.assertFalse(any(item.name.endswith(".py") for item in self.root.rglob("*") if item.is_file()))

    def test_generated_tree_uses_confirmed_values_without_source_development_state(self):
        data = confirmed_input()
        data["context"]["scope"] = "Build the confirmed sample experience."
        data["context"]["architecture"] = "Architecture is not yet specified."
        data["initialization"] = {
            "status": "partial",
            "unknowns": ["Deployment target is not confirmed."],
            "assumptions": [],
        }
        self.install(data)
        project = json.loads((self.root / ".blueprint/config/project.json").read_text(encoding="utf-8"))
        self.assertEqual(project["project"]["description"], "A confirmed sample project.")
        self.assertEqual(project["purpose"]["summary"], "A confirmed sample project.")
        self.assertEqual(project["initialization"]["unknowns"], ["Deployment target is not confirmed."])
        context = (self.root / ".blueprint/memory/PROJECT_CONTEXT.md").read_text(encoding="utf-8")
        architecture = (self.root / ".blueprint/memory/ARCHITECTURE.md").read_text(encoding="utf-8")
        self.assertIn("Build the confirmed sample experience.", context)
        self.assertIn("Deployment target is not confirmed.", context)
        self.assertIn("Architecture is not yet specified.", architecture)
        self.assertFalse((self.root / ".blueprint/tasks/items/TASK-013.md").exists())
        self.assertFalse((self.root / ".blueprint/memory/DECISIONS.md").read_text(encoding="utf-8").count("ADR-010"))

    def test_selected_opencode_adapter_is_planned_and_generated_separately(self):
        plan_hash, plan, _ = self.build(confirmed_input(with_opencode=True))
        self.assertTrue(plan_hash)
        adapter_paths = {item.relative_target for item in plan if item.relative_target.startswith(".opencode/")}
        self.assertEqual(len(adapter_paths), 11)
        self.assertIn("AGENTS.md", {item.relative_target for item in plan})
        self.assertIn("opencode.jsonc", {item.relative_target for item in plan})
        generator.apply_plan(self.root, plan)
        self.assertTrue((self.root / ".opencode/agents/orchestrator.md").is_file())
        self.assertFalse(any(item.name.endswith(".py") for item in self.root.rglob("*") if item.is_file()))

    def test_adapter_conflict_uses_exact_path_approval_in_the_combined_plan(self):
        config = self.root / "opencode.jsonc"
        config.write_text('{"default_agent": "user-agent"}\n', encoding="utf-8")
        user_agents = self.root / "AGENTS.md"
        user_agents.write_text("Keep these user instructions.\n", encoding="utf-8")

        _, plan, _ = self.build(confirmed_input(with_opencode=True))
        conflict = next(item for item in plan if item.relative_target == "opencode.jsonc")
        self.assertEqual(conflict.outcome, "CONFLICT")
        self.assertFalse(conflict.overwrite_approved)
        with self.assertRaisesRegex(generator.GenerationError, "unapproved conflicts"):
            generator.apply_plan(self.root, plan)
        self.assertEqual(config.read_text(encoding="utf-8"), '{"default_agent": "user-agent"}\n')
        self.assertFalse((self.root / ".blueprint/README.md").exists())

        _, approved, _ = self.build(
            confirmed_input(with_opencode=True),
            {"opencode.jsonc"},
        )
        self.assertTrue(next(item for item in approved if item.relative_target == "opencode.jsonc").overwrite_approved)
        generator.apply_plan(self.root, approved)
        self.assertIn('"default_agent": "orchestrator"', config.read_text(encoding="utf-8"))
        self.assertIn("Keep these user instructions.", user_agents.read_text(encoding="utf-8"))

    def test_all_outcomes_and_exact_path_overwrite_are_enforced(self):
        data = confirmed_input()
        catalog = generator._catalog()
        desired = {
            entry["target"]: generator._render(entry, self.root, data, generator._schema_versions())
            for entry in catalog["files"]
        }
        skip_path = ".blueprint/schemas/agents.schema.json"
        merge_path = ".blueprint/schemas/project.schema.json"
        conflict_a = ".blueprint/config/project.json"
        conflict_b = ".blueprint/memory/DECISIONS.md"
        for relative in (skip_path, merge_path, conflict_a, conflict_b):
            (self.root / relative).parent.mkdir(parents=True, exist_ok=True)
        (self.root / skip_path).write_bytes(desired[skip_path])
        merge_old = b'{"previous-template": true}\n'
        (self.root / merge_path).write_bytes(merge_old)
        (self.root / conflict_a).write_text("user-owned project data\n", encoding="utf-8")
        (self.root / conflict_b).write_text("user-owned decision history\n", encoding="utf-8")
        records = [
            {"path": skip_path, "class": "blueprint-managed", "template_version": "0.1.0",
             "sha256": hashlib.sha256(desired[skip_path]).hexdigest()},
            {"path": merge_path, "class": "blueprint-managed", "template_version": "0.1.0",
             "sha256": hashlib.sha256(merge_old).hexdigest()},
        ]
        self.write_manifest(valid_manifest(records))

        plan_hash, plan, unknown = self.build(data)
        outcomes = {item.relative_target: item.outcome for item in plan}
        self.assertEqual(outcomes[skip_path], "SKIP")
        self.assertEqual(outcomes[merge_path], "MERGE")
        self.assertEqual(outcomes[conflict_a], "CONFLICT")
        self.assertEqual(outcomes[conflict_b], "CONFLICT")
        self.assertIn("CREATE", {item.outcome for item in plan})
        preview = io.StringIO()
        with redirect_stdout(preview):
            generator._render_plan(plan_hash, plan, unknown)
        rendered = preview.getvalue()
        for outcome in ("CREATE", "MERGE", "SKIP", "CONFLICT"):
            self.assertIn(outcome, rendered)
        self.assertIn("user-owned project data", rendered)
        self.assertIn("--- a/.blueprint/config/project.json", rendered)
        with self.assertRaisesRegex(generator.GenerationError, "unapproved conflicts"):
            generator.apply_plan(self.root, plan)
        self.assertEqual((self.root / conflict_a).read_text(encoding="utf-8"), "user-owned project data\n")
        self.assertFalse((self.root / ".blueprint/memory/CURRENT_STATE.md").exists())

        _, partially_approved, _ = self.build(data, {conflict_a})
        self.assertTrue(next(item for item in partially_approved if item.relative_target == conflict_a).overwrite_approved)
        self.assertEqual(next(item for item in partially_approved if item.relative_target == conflict_b).outcome, "CONFLICT")
        with self.assertRaisesRegex(generator.GenerationError, "unapproved conflicts"):
            generator.apply_plan(self.root, partially_approved)
        self.assertEqual((self.root / conflict_b).read_text(encoding="utf-8"), "user-owned decision history\n")

        _, approved_plan, _ = self.build(data, {conflict_a, conflict_b})
        generator.apply_plan(self.root, approved_plan)
        self.assertNotEqual((self.root / conflict_a).read_text(encoding="utf-8"), "user-owned project data\n")
        self.assertNotEqual((self.root / conflict_b).read_text(encoding="utf-8"), "user-owned decision history\n")
        self.assertEqual(next(item for item in approved_plan if item.relative_target == skip_path).outcome, "SKIP")

    def test_untracked_files_and_manifest_paths_are_preserved_and_reported(self):
        self.write_manifest()
        custom = self.root / ".blueprint/custom/notes.md"
        custom.parent.mkdir(parents=True, exist_ok=True)
        custom.write_text("keep this unknown content\n", encoding="utf-8")
        _, plan, unknown = self.build()
        self.assertIn(".blueprint/custom/notes.md", unknown)
        generator.apply_plan(self.root, plan)
        self.assertEqual(custom.read_text(encoding="utf-8"), "keep this unknown content\n")

    def test_unknown_manifest_records_are_preserved_but_missing_ones_block(self):
        unknown = ".blueprint/legacy/guide.md"
        content = b"legacy user guide\n"
        path = self.root / unknown
        path.parent.mkdir(parents=True)
        path.write_bytes(content)
        record = {
            "path": unknown,
            "class": "blueprint-managed",
            "template_version": "0.1.0",
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        self.write_manifest(valid_manifest([record]))
        _, plan, reported = self.build()
        self.assertIn(unknown, reported)
        generator.apply_plan(self.root, plan)
        manifest = json.loads((self.root / MANIFEST_PATH).read_text(encoding="utf-8"))
        self.assertIn(record, manifest["files"])
        self.assertEqual(path.read_bytes(), content)

        path.unlink()
        before = {
            entry.relative_to(self.root).as_posix(): entry.read_bytes()
            for entry in self.root.rglob("*") if entry.is_file()
        }
        with self.assertRaisesRegex(generator.GenerationError, "unknown manifest path is missing or unsafe"):
            self.build()
        after = {
            entry.relative_to(self.root).as_posix(): entry.read_bytes()
            for entry in self.root.rglob("*") if entry.is_file()
        }
        self.assertEqual(before, after)

    def test_missing_managed_file_requires_exact_recreation_approval(self):
        self.install()
        missing = ".blueprint/tasks/TASK-TEMPLATE.md"
        (self.root / missing).unlink()
        _, plan, _ = self.build()
        item = next(record for record in plan if record.relative_target == missing)
        self.assertEqual(item.outcome, "CONFLICT")
        with self.assertRaisesRegex(generator.GenerationError, "unapproved conflicts"):
            generator.apply_plan(self.root, plan)
        _, approved, _ = self.build(approved={missing})
        generator.apply_plan(self.root, approved)
        self.assertTrue((self.root / missing).is_file())

    def test_unsupported_or_malformed_manifest_blocks_before_writes(self):
        self.write_manifest(valid_manifest(blueprint_version="9.9.9"))
        with self.assertRaisesRegex(generator.GenerationError, "unsupported blueprint_version"):
            self.build()
        before = {path.relative_to(self.root) for path in self.root.rglob("*")}

        (self.root / ".blueprint/manifest.json").write_text("{ invalid", encoding="utf-8")
        with self.assertRaisesRegex(generator.GenerationError, "is invalid"):
            self.build()
        self.assertEqual({path.relative_to(self.root) for path in self.root.rglob("*")}, before)

    def test_symlink_collision_is_not_overwritable(self):
        self.write_manifest()
        outside = self.root / "outside.txt"
        outside.write_text("do not change\n", encoding="utf-8")
        destination = self.root / ".blueprint/config/project.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.symlink_to(outside)
        _, plan, _ = self.build()
        item = next(record for record in plan if record.relative_target == ".blueprint/config/project.json")
        self.assertEqual(item.outcome, "CONFLICT")
        self.assertFalse(item.overwrite_approved)
        with self.assertRaisesRegex(generator.GenerationError, "unapproved conflicts"):
            generator.apply_plan(self.root, plan)
        self.assertEqual(outside.read_text(encoding="utf-8"), "do not change\n")
        self.assertFalse((self.root / ".blueprint/config/agents.json").exists())

    def test_windows_reparse_point_ancestor_blocks_planning_and_fallback_write(self):
        self.write_manifest()
        reparse_directory = self.root / ".blueprint"
        original_lstat = pathlib.Path.lstat

        def lstat_with_reparse_point(path):
            if path == reparse_directory:
                return mock.Mock(st_mode=generator.stat.S_IFDIR, st_file_attributes=0x400)
            return original_lstat(path)

        with mock.patch.object(pathlib.Path, "lstat", new=lstat_with_reparse_point):
            self.assertTrue(generator._is_symlink_or_reparse_point(reparse_directory))
            self.assertEqual(
                generator._state(self.root, ".blueprint/config/project.json"),
                ("symlink", None),
            )
            with self.assertRaisesRegex(
                generator.GenerationError, "symlink or reparse point"
            ):
                generator._write_atomic_by_path(
                    self.root, ".blueprint/config/project.json", b"must not be written"
                )

        self.assertFalse((reparse_directory / "config/project.json").exists())

    def test_unchanged_regeneration_is_idempotent_even_after_date_change(self):
        with mock.patch.object(generator, "_today", return_value="2026-11-05"):
            self.install()
        before = {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in self.root.rglob("*") if path.is_file()
        }
        with mock.patch.object(generator, "_today", return_value="2026-11-06"):
            _, plan, unknown = self.build()
        self.assertFalse(unknown)
        self.assertEqual({item.outcome for item in plan}, {"SKIP"})
        generator.apply_plan(self.root, plan)
        after = {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in self.root.rglob("*") if path.is_file()
        }
        self.assertEqual(before, after)

    def test_portable_atomic_write_fallback_works_without_directory_fd_support(self):
        with mock.patch.object(generator, "HAS_DIR_FD", False):
            self.install()
            _, plan, _ = self.build()
            self.assertEqual({item.outcome for item in plan}, {"SKIP"})

    def test_stale_preview_and_partial_failure_do_not_seal_manifest(self):
        _, plan, _ = self.build()
        late_file = self.root / ".blueprint/config/project.json"
        late_file.parent.mkdir(parents=True, exist_ok=True)
        late_file.write_text("changed after preview\n", encoding="utf-8")
        with self.assertRaisesRegex(generator.GenerationError, "target changed after preview"):
            generator.apply_plan(self.root, plan)
        self.assertFalse((self.root / MANIFEST_PATH).exists())
        self.assertFalse((self.root / ".blueprint/README.md").exists())

        second_root = pathlib.Path(tempfile.mkdtemp(dir=self.temporary.name))
        self.addCleanup(shutil.rmtree, second_root)
        _, second_plan, _ = generator.build_plan(second_root, confirmed_input())
        original_write = generator._write_atomic
        writes = 0

        def fail_second(root, relative, content):
            nonlocal writes
            writes += 1
            if writes == 2:
                raise OSError("injected write failure")
            return original_write(root, relative, content)

        with mock.patch.object(generator, "_write_atomic", side_effect=fail_second):
            with self.assertRaisesRegex(generator.GenerationError, "completed=.*pending="):
                generator.apply_plan(second_root, second_plan)
        self.assertFalse((second_root / MANIFEST_PATH).exists())

    def test_second_run_reports_only_skip_and_manifest_is_not_rewritten(self):
        self.install()
        before = (self.root / MANIFEST_PATH).read_bytes()
        _, plan, _ = self.build()
        self.assertEqual({item.outcome for item in plan}, {"SKIP"})
        generator.apply_plan(self.root, plan)
        self.assertEqual((self.root / MANIFEST_PATH).read_bytes(), before)

    def test_input_rejects_pending_or_inconsistent_unknowns(self):
        data = confirmed_input()
        data["initialization"]["status"] = "pending"
        with self.assertRaisesRegex(generator.GenerationError, "cannot be generated"):
            self.build(data)
        data["initialization"] = {"status": "complete", "unknowns": ["Unknown"], "assumptions": []}
        with self.assertRaisesRegex(generator.GenerationError, "exactly when unknowns is empty"):
            self.build(data)

        data = confirmed_input()
        data["initialization"] = {"status": "complete", "unknowns": [], "assumptions": []}
        with self.assertRaisesRegex(generator.GenerationError, "context to be confirmed"):
            self.build(data)

    def test_unsafe_relative_paths_are_rejected(self):
        for value in ("../escape", ".blueprint/../../outside", "/absolute", r".blueprint\config\project.json"):
            with self.subTest(path=value), self.assertRaises(generator.GenerationError):
                generator._safe_relative(value)

    def test_generated_project_has_no_python_runtime_or_blueprint_source_files(self):
        self.install(confirmed_input(with_opencode=True))
        files = [path for path in self.root.rglob("*") if path.is_file()]
        self.assertFalse(any(path.suffix == ".py" for path in files))
        self.assertFalse(any(path.name == "build_blueprint.py" for path in files))
        for path in files:
            content = path.read_bytes().lower()
            self.assertNotIn(b"python3", content, path.as_posix())
            self.assertNotIn(b"task_lifecycle.py", content, path.as_posix())
        self.assertFalse((self.root / ".blueprint/tasks/items/TASK-013.md").exists())


if __name__ == "__main__":
    unittest.main()
