from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

from scripts.task_lifecycle import complete_task, validate_completion


TASK_ID = "TASK-999"
TITLE = "Exercise the task completion evidence gate"
COMMAND = "python3 -m unittest discover -s tests -p test_task_lifecycle.py"


class TaskLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)
        (self.root / "tasks/items").mkdir(parents=True)
        (self.root / "memory").mkdir()
        (self.root / "tests").mkdir()
        (self.root / "docs/reviews").mkdir(parents=True)
        (self.root / "tests/test_task_lifecycle.py").write_text(
            "import unittest\n"
            "class PassingTest(unittest.TestCase):\n"
            "    def test_missing_test_evidence_blocks_completion(self):\n"
            "        self.assertTrue(True)\n",
            encoding="utf-8",
        )
        self.report = self.root / "docs/reviews/TASK-999-verification.md"
        self.report.write_text(
            f"Command: `{COMMAND}`\n\nRESULT: PASS\n",
            encoding="utf-8",
        )
        self.review = self.root / "docs/reviews/TASK-999-manager-review.md"
        self.review.write_text(
            "Task: TASK-999\n"
            "Reviewer role: MANAGER: Quality\n"
            "Decision: APPROVED\n"
            "Independent review: YES\n"
            "Reviewed acceptance evidence and passing tests.\n",
            encoding="utf-8",
        )
        self.registry_path = self.root / "tasks/registry.json"
        self.registry_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "updated_at": "2026-11-05",
                    "tasks": [
                        {
                            "id": TASK_ID,
                            "title": TITLE,
                            "status": "in_review",
                            "priority": "high",
                            "specs": ["SPEC-009"],
                            "owner_role": "MANAGER: Quality",
                            "dependencies": ["TASK-006"],
                            "next_action": "Complete after review.",
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        task = f"""# {TASK_ID} — {TITLE}

## Metadata
- Status: in_review
- Priority: high
- Owner role: MANAGER: Quality
- Specs: SPEC-009
- Dependencies: TASK-006
- Created: 2026-11-05
- Updated: 2026-11-05

## Acceptance criteria
- [x] Completion evidence maps to a passing behavioral test.

## Completion evidence
| Criterion | Criterion text | Evidence |
| --- | --- | --- |
| AC-01 | Completion evidence maps to a passing behavioral test. | `test_missing_test_evidence_blocks_completion` passes in [the test](../../tests/test_task_lifecycle.py). |

## Verification results
| Check | Command | Result | Output |
| --- | --- | --- | --- |
| Focused suite | `{COMMAND}` | PASS | [verification report](../../docs/reviews/TASK-999-verification.md) |

## Manager review
- Review artifact: `docs/reviews/TASK-999-manager-review.md`

## Next action
Wait for completion gate.
"""
        self.task_path = self.root / "tasks/items/TASK-999.md"
        self.task_path.write_text(task, encoding="utf-8")
        (self.root / "tasks/backlog.md").write_text(
            f"- [ ] **{TASK_ID}** (in_review, critical): {TITLE}. Depends on TASK-006, TASK-009.\n",
            encoding="utf-8",
        )
        (self.root / "memory/CURRENT_STATE.md").write_text(
            f"## Active task\n**{TASK_ID} — {TITLE}**\n- Status: `in_review`\n\n"
            "## Completed recently\nNo recent completions.\n\n"
            "## Next\nWait for gate.\n",
            encoding="utf-8",
        )

    def test_valid_evidence_passes_gate_and_synchronizes_all_records(self):
        errors = validate_completion(self.root, TASK_ID, self.review)
        self.assertEqual(errors, [])
        complete_task(self.root, TASK_ID, self.review, "Present next task for approval.", "2026-11-05")

        registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
        self.assertEqual(registry["tasks"][0]["status"], "done")
        self.assertIn("- Status: done", self.task_path.read_text(encoding="utf-8"))
        self.assertIn(f"- [x] **{TASK_ID}** (done):", (self.root / "tasks/backlog.md").read_text(encoding="utf-8"))
        state = (self.root / "memory/CURRENT_STATE.md").read_text(encoding="utf-8")
        self.assertIn(f"None. {TASK_ID} is complete", state)
        self.assertIn(f"**{TASK_ID}** (`done`)", state)
        self.assertIn("Present next task for approval.", state)

    def test_check_command_runs_tests_before_authorizing_transition(self):
        repository = pathlib.Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [
                sys.executable,
                str(repository / "scripts/task_lifecycle.py"),
                "check",
                TASK_ID,
                "--root",
                str(self.root),
                "--review",
                str(self.review),
            ],
            cwd=repository,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("TEST OUTPUT:", result.stdout)
        self.assertIn("completion gate accepted", result.stdout)

    def test_failed_executable_test_blocks_completion_without_record_changes(self):
        test_file = self.root / "tests/test_task_lifecycle.py"
        test_file.write_text(
            "import unittest\n"
            "class FailingTest(unittest.TestCase):\n"
            "    def test_missing_test_evidence_blocks_completion(self):\n"
            "        self.fail('expected failure')\n",
            encoding="utf-8",
        )
        paths = [
            self.registry_path,
            self.task_path,
            self.root / "tasks/backlog.md",
            self.root / "memory/CURRENT_STATE.md",
        ]
        before = {path: path.read_bytes() for path in paths}
        with self.assertRaisesRegex(ValueError, "exited 1"):
            complete_task(self.root, TASK_ID, self.review, "No transition.", "2026-11-05")
        self.assertEqual({path: path.read_bytes() for path in paths}, before)

    def _assert_rejected_without_writes(self, mutation, expected):
        paths = [
            self.registry_path,
            self.task_path,
            self.root / "tasks/backlog.md",
            self.root / "memory/CURRENT_STATE.md",
        ]
        mutation()
        before = {path: path.read_bytes() for path in paths}
        errors = validate_completion(self.root, TASK_ID, self.review)
        self.assertTrue(any(expected in error for error in errors), errors)
        with self.assertRaises(ValueError):
            complete_task(self.root, TASK_ID, self.review, "Invalid transition.", "2026-11-05")
        self.assertEqual({path: path.read_bytes() for path in paths}, before)

    def test_incomplete_criterion_blocks_completion(self):
        self._assert_rejected_without_writes(
            lambda: self.task_path.write_text(
                self.task_path.read_text(encoding="utf-8").replace("[x] Completion", "[ ] Completion"),
                encoding="utf-8",
            ),
            "every acceptance criterion",
        )

    def test_missing_criterion_evidence_blocks_completion(self):
        self._assert_rejected_without_writes(
            lambda: self.task_path.write_text(
                self.task_path.read_text(encoding="utf-8").replace(
                    "| AC-01 | Completion evidence maps to a passing behavioral test. | `test_missing_test_evidence_blocks_completion` passes in [the test](../../tests/test_task_lifecycle.py). |",
                    "",
                ),
                encoding="utf-8",
            ),
            "exactly one row per acceptance criterion",
        )

    def test_missing_named_test_evidence_blocks_completion(self):
        def mutate():
            text = self.task_path.read_text(encoding="utf-8").replace(
                "test_missing_test_evidence_blocks_completion",
                "test_missing_from_test_module",
            )
            self.task_path.write_text(text, encoding="utf-8")

        self._assert_rejected_without_writes(
            mutate,
            "concrete, named behavioral test",
        )

    def test_failed_or_missing_test_report_blocks_completion(self):
        self._assert_rejected_without_writes(
            lambda: self.report.write_text(f"Command: `{COMMAND}`\n\nRESULT: FAIL\n", encoding="utf-8"),
            "does not prove PASS",
        )

    def test_missing_manager_review_blocks_completion(self):
        self._assert_rejected_without_writes(
            lambda: self.review.unlink(),
            "Manager review artifact",
        )

    def test_rejected_or_wrong_role_review_blocks_completion(self):
        self._assert_rejected_without_writes(
            lambda: self.review.write_text(
                "Task: TASK-999\n"
                "Reviewer role: MANAGER: Engineering\n"
                "Decision: REJECTED\n"
                "Independent review: YES\n",
                encoding="utf-8",
            ),
            "appropriate Manager role",
        )

    def test_registry_task_backlog_and_current_state_mismatches_block_completion(self):
        def mutate():
            registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
            registry["tasks"][0]["status"] = "done"
            self.registry_path.write_text(json.dumps(registry), encoding="utf-8")

        self._assert_rejected_without_writes(mutate, "must both be in_review")

    def test_backlog_mismatch_blocks_completion(self):
        self._assert_rejected_without_writes(
            lambda: (self.root / "tasks/backlog.md").write_text(
                f"- [x] **{TASK_ID}** (done): {TITLE}.\n",
                encoding="utf-8",
            ),
            "backlog projection",
        )

    def test_current_state_mismatch_blocks_completion(self):
        state_path = self.root / "memory/CURRENT_STATE.md"
        self._assert_rejected_without_writes(
            lambda: state_path.write_text(
                "## Active task\nNone.\n\n## Next\nWait.\n",
                encoding="utf-8",
            ),
            "CURRENT_STATE",
        )


if __name__ == "__main__":
    unittest.main()
