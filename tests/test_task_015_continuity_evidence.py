import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/reviews/task-015-evidence"
FIXTURE = EVIDENCE / "fixture"


class Task015ContinuityEvidenceTests(unittest.TestCase):
    def test_ac_01_fresh_session_reconstructs_persisted_context(self):
        transcript = (EVIDENCE / "producer-session.txt").read_text(encoding="utf-8")
        packet_start = transcript.index("## Startup context packet")
        packet_end = transcript.index("## Bounded execution", packet_start)
        packet = transcript[packet_start:packet_end]

        self.assertLess(
            transcript.index("→ Read .blueprint/memory/CURRENT_STATE.md"),
            packet_start,
        )
        for expected in (
            "Continuity Test Project",
            "Goal:** TASK-900",
            "Constraints (binding",
            "production stack explicitly unknown",
            "Active task:",
            "dependency TASK-001 (`done`)",
            "Blockers/pending at startup",
            "ADR-900",
            "Sources:",
            "Next action (startup):",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, packet)

    def test_ac_02_dependency_bounded_work_and_persistent_status_are_verified(self):
        blueprint = FIXTURE / ".blueprint"
        registry = json.loads(
            (blueprint / "tasks/registry.json").read_text(encoding="utf-8")
        )
        statuses = {task["id"]: task["status"] for task in registry["tasks"]}
        self.assertEqual(statuses["TASK-001"], "done")
        self.assertEqual(statuses["TASK-900"], "in_review")
        self.assertEqual(
            (FIXTURE / "evidence/prerequisite.txt").read_text(encoding="utf-8"),
            "SYNTHETIC-DEPENDENCY-VERIFIED\n",
        )
        self.assertEqual(
            (FIXTURE / "evidence/continuity.txt").read_text(encoding="utf-8"),
            "CONTINUITY-015-OK\n",
        )
        self.assertIn(
            "- Status: in_review",
            (blueprint / "tasks/items/TASK-900.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "TASK-900",
            (blueprint / "memory/CURRENT_STATE.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "in_review",
            (blueprint / "tasks/backlog.md").read_text(encoding="utf-8"),
        )

    def test_ac_03_handoff_and_git_claims_are_independently_verified(self):
        handoff = (
            FIXTURE / ".blueprint/handoffs/2026-11-05-task-900.md"
        ).read_text(encoding="utf-8")
        session = (
            FIXTURE / ".blueprint/sessions/2026-11-05-task-900.md"
        ).read_text(encoding="utf-8")
        review = (
            ROOT
            / "docs/reviews/2026-11-05-task-015-clean-manager-review-followup.md"
        ).read_text(encoding="utf-8")
        git_status = (
            EVIDENCE / "fixture-git-status.txt"
        ).read_text(encoding="utf-8")

        self.assertIn("Exact next action", handoff)
        self.assertIn("pending", handoff)
        self.assertIn("## No commits yet on main", git_status)
        self.assertIn("fatal: Needed a single revision", git_status)
        self.assertIn("No subagent delegation", session)
        self.assertIn("Task: TASK-015", review)
        self.assertIn("Reviewer role: MANAGER: Architecture", review)
        self.assertIn("Decision: APPROVED", review)
        self.assertIn("Independent review: YES", review)
        self.assertIn("git status --porcelain=v1 -b", review)
        self.assertIn("git rev-parse --verify HEAD", review)
        self.assertIn("AC-03", review)

    def test_ac_04_negative_recovery_fixtures_remain_unchanged(self):
        before = json.loads(
            (EVIDENCE / "negative-inventories-before.json").read_text(
                encoding="utf-8"
            )
        )
        after = json.loads(
            (EVIDENCE / "negative-inventories-after.json").read_text(
                encoding="utf-8"
            )
        )

        for scenario in ("missing", "mismatch"):
            with self.subTest(scenario=scenario):
                self.assertEqual(
                    before[scenario]["files"],
                    after[scenario]["files"],
                )
                self.assertEqual(before[scenario]["root"], after[scenario]["root"])


if __name__ == "__main__":
    unittest.main()
