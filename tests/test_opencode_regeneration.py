from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

from scripts.regenerate_opencode_adapter import (
    ADAPTER,
    apply_plan,
    build_plan,
    parse_jsonc,
)


class OpenCodeRegenerationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)

    def plan(self, approved=None, manifest=None):
        return build_plan(
            self.root,
            set(approved or []),
            manifest or ADAPTER / "manifest.json",
        )

    def test_empty_target_dry_run_creates_without_writing(self):
        plan = self.plan()
        self.assertEqual(len(plan), 13)
        self.assertTrue(all(item.outcome == "create" for item in plan))
        self.assertFalse((self.root / "AGENTS.md").exists())
        self.assertFalse((self.root / ".opencode").exists())
        self.assertFalse(any(item.relative_target.endswith(".py") for item in plan))

    def test_cli_dry_run_reports_plan_without_creating_files(self):
        repository = pathlib.Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [
                sys.executable,
                str(repository / "scripts/regenerate_opencode_adapter.py"),
                "--target",
                str(self.root),
                "--dry-run",
            ],
            cwd=repository,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("CREATE", result.stdout)
        self.assertIn("Dry run complete", result.stdout)
        self.assertFalse((self.root / "AGENTS.md").exists())

    def test_cli_dry_run_reports_create_merge_skip_and_conflict(self):
        repository = pathlib.Path(__file__).resolve().parents[1]
        agents_path = self.root / "AGENTS.md"
        agents_path.write_text("User-authored root instructions.\n", encoding="utf-8")
        conflict_path = self.root / "opencode.jsonc"
        conflict_path.write_text('{"default_agent": "build"}\n', encoding="utf-8")
        baseline = self.plan()
        managed_agent = next(
            item.content for item in baseline
            if item.relative_target == ".opencode/agents/orchestrator.md"
        )
        managed_path = self.root / ".opencode/agents/orchestrator.md"
        managed_path.parent.mkdir(parents=True)
        managed_path.write_text(managed_agent, encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable,
                str(repository / "scripts/regenerate_opencode_adapter.py"),
                "--target",
                str(self.root),
                "--dry-run",
            ],
            cwd=repository,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        for outcome in ("CREATE", "MERGE", "SKIP", "CONFLICT"):
            self.assertIn(outcome, result.stdout)
        self.assertIn("No files written", result.stderr)
        self.assertFalse((self.root / ".opencode/commands/blueprint-startup.md").exists())
        self.assertEqual(conflict_path.read_text(encoding="utf-8"), '{"default_agent": "build"}\n')

    def test_generated_adapter_files_do_not_require_python(self):
        plan = self.plan()
        self.assertFalse(any(item.relative_target.endswith(".py") for item in plan))
        for item in plan:
            self.assertNotIn("python3", (item.content or "").lower())
            self.assertNotIn("task_lifecycle.py", item.relative_target)

    def test_clean_install_is_idempotent(self):
        first = self.plan()
        apply_plan(self.root, first)
        second = self.plan()
        self.assertEqual({item.outcome for item in second}, {"skip"})
        apply_plan(self.root, second)
        self.assertEqual(len(list(self.root.rglob("*"))), 16)

    def test_existing_markdown_and_compatible_jsonc_merge_without_losing_user_content(self):
        (self.root / "AGENTS.md").write_text("# User rules\nKeep this text.\n", encoding="utf-8")
        (self.root / "opencode.jsonc").write_text(
            '{\n  "$schema": "https://opencode.ai/config.json",\n'
            '  "instructions": ["user-instructions.md"], // user comment\n'
            '  "logLevel": "DEBUG"\n}\n',
            encoding="utf-8",
        )
        plan = self.plan()
        agents = next(item for item in plan if item.relative_target == "AGENTS.md")
        config = next(item for item in plan if item.relative_target == "opencode.jsonc")
        self.assertEqual(agents.outcome, "merge")
        self.assertEqual(config.outcome, "merge")
        apply_plan(self.root, plan)

        agents_text = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Keep this text.", agents_text)
        self.assertIn("Project Agent Instructions", agents_text)
        config = parse_jsonc((self.root / "opencode.jsonc").read_text(encoding="utf-8"))
        self.assertEqual(config["default_agent"], "orchestrator")
        self.assertEqual(config["instructions"], ["user-instructions.md"])
        self.assertEqual(config["logLevel"], "DEBUG")
        self.assertIn("// user comment", (self.root / "opencode.jsonc").read_text(encoding="utf-8"))
        self.assertEqual({item.outcome for item in self.plan()}, {"skip"})

    def test_unapproved_conflict_prevents_every_write(self):
        config_path = self.root / "opencode.jsonc"
        config_path.write_text('{"default_agent": "build", "custom": true}\n', encoding="utf-8")
        original = config_path.read_bytes()
        plan = self.plan()
        config = next(item for item in plan if item.relative_target == "opencode.jsonc")
        self.assertEqual(config.outcome, "conflict")
        with self.assertRaisesRegex(ValueError, "no files written"):
            apply_plan(self.root, plan)
        self.assertEqual(config_path.read_bytes(), original)
        self.assertFalse((self.root / "AGENTS.md").exists())
        self.assertFalse((self.root / ".opencode").exists())

    def test_approved_directory_conflict_is_rejected_before_any_write(self):
        conflict_path = self.root / "opencode.jsonc"
        conflict_path.mkdir()
        plan = self.plan(["opencode.jsonc"])
        config = next(item for item in plan if item.relative_target == "opencode.jsonc")
        self.assertEqual(config.outcome, "conflict")
        self.assertFalse(config.overwrite_approved)
        with self.assertRaisesRegex(ValueError, "no files written"):
            apply_plan(self.root, plan)
        self.assertTrue(conflict_path.is_dir())
        self.assertFalse((self.root / "AGENTS.md").exists())
        self.assertFalse((self.root / ".opencode").exists())

    def test_exact_path_approval_overwrites_only_the_approved_conflict(self):
        config_path = self.root / "opencode.jsonc"
        config_path.write_text('{"default_agent": "build", "custom": true}\n', encoding="utf-8")
        plan = self.plan(["opencode.jsonc"])
        config = next(item for item in plan if item.relative_target == "opencode.jsonc")
        self.assertEqual(config.outcome, "conflict")
        self.assertTrue(config.overwrite_approved)
        apply_plan(self.root, plan)
        self.assertEqual(parse_jsonc(config_path.read_text(encoding="utf-8"))["default_agent"], "orchestrator")
        self.assertTrue((self.root / "AGENTS.md").exists())

    def test_user_edits_inside_managed_region_conflict_but_approved_update_preserves_outside(self):
        source = self.root / "source/adapters/opencode"
        source.parent.mkdir(parents=True)
        shutil.copytree(ADAPTER, source)
        manifest = source / "manifest.json"
        apply_plan(self.root, self.plan(manifest=manifest))

        target = self.root / ".opencode/agents/orchestrator.md"
        text = target.read_text(encoding="utf-8")
        start = text.index("\n", text.index("BEGIN developer-ai-init managed content")) + 1
        text = text[:start] + "user edit inside managed section\n" + text[start:]
        text += "\nUser-owned note outside the managed section.\n"
        target.write_text(text, encoding="utf-8")
        template = source / "templates/agents/orchestrator.md"
        template.write_text(template.read_text(encoding="utf-8") + "\nUpdated upstream template.\n", encoding="utf-8")

        conflict_plan = build_plan(self.root, manifest_path=manifest)
        item = next(
            row for row in conflict_plan
            if row.relative_target == ".opencode/agents/orchestrator.md"
        )
        self.assertEqual(item.outcome, "conflict")
        approved_plan = build_plan(
            self.root,
            {".opencode/agents/orchestrator.md"},
            manifest_path=manifest,
        )
        apply_plan(self.root, approved_plan)
        updated = target.read_text(encoding="utf-8")
        self.assertIn("User-owned note outside the managed section.", updated)
        self.assertIn("Updated upstream template.", updated)
        self.assertNotIn("user edit inside managed section", updated)
        self.assertEqual(
            {row.outcome for row in build_plan(self.root, manifest_path=manifest)},
            {"skip"},
        )

    def test_symlink_collision_is_not_written(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "orchestrator.md").write_text("outside", encoding="utf-8")
        agents = self.root / ".opencode/agents"
        agents.parent.mkdir(parents=True)
        agents.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.plan()
        self.assertEqual((outside / "orchestrator.md").read_text(encoding="utf-8"), "outside")


if __name__ == "__main__":
    unittest.main()
