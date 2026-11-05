import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs/architecture/project-discovery-and-initialization.md"
TEXT = SPEC.read_text(encoding="utf-8")
NORMALIZED = " ".join(TEXT.split())


def scenario(identifier):
    return next(
        line
        for line in TEXT.splitlines()
        if line.startswith("| " + identifier + " —")
    )


class InitializationSpecificationTests(unittest.TestCase):
    def test_greenfield_and_brownfield_scenarios_are_documented(self):
        preflight = TEXT.split("## 3. Preflight", 1)[1].split("## 4.", 1)[0]
        self.assertIn("Greenfield / empty", preflight)
        self.assertIn("Brownfield / existing", preflight)
        self.assertIn("Already initialized", preflight)
        self.assertIn("Needs reconciliation", preflight)
        self.assertIn("INIT-S01", scenario("INIT-S01"))
        self.assertIn("INIT-S02", scenario("INIT-S02"))
        self.assertIn("pyproject.toml", scenario("INIT-S02"))

    def test_unknowns_remain_explicit_and_unconfirmed_facts_are_not_generated(self):
        evidence = TEXT.split("## 2. Terms", 1)[1].split("## 3.", 1)[0]
        self.assertRegex(evidence, r"\| Unknown \|.*\| Preserve as unknown")
        self.assertIn("not filled from a model's preference", NORMALIZED)
        self.assertIn("initialization.unknowns", NORMALIZED)
        self.assertIn("INIT-S03", scenario("INIT-S03"))
        self.assertIn("unknown", scenario("INIT-S01").lower())

    def test_schema_required_fields_and_scope_have_canonical_owners(self):
        schema = json.loads((ROOT / "schemas/project.schema.json").read_text(encoding="utf-8"))
        schema_text = " ".join(TEXT.split())
        required_scalars = ("project.name", "project.slug", "project.description",
                            "project.status", "purpose.summary")
        for field in required_scalars:
            self.assertIn(field, schema_text)
        project_layout = (ROOT / "docs/architecture/target-project-layout.md").read_text(encoding="utf-8")
        project_config_row = next(
            line for line in project_layout.splitlines()
            if line.startswith("| `.blueprint/config/project.json`")
        )
        self.assertNotIn("goals, scope,", project_config_row.lower())
        self.assertIn("scope and narrative project context belong in `project_context.md`",
                      project_config_row.lower())
        self.assertIn(".blueprint/memory/PROJECT_CONTEXT.md", schema_text)
        self.assertIn("confirmed no applicable values", schema_text)
        self.assertIn("specific field in `initialization.unknowns`", schema_text)
        self.assertEqual(schema["properties"]["project"]["required"],
                         ["name", "slug", "description", "status"])

    def test_confirmed_purpose_maps_to_required_description_and_summary(self):
        interview = TEXT.split("## 4. Interview and draft model", 1)[1].split("## 5.", 1)[0]
        normalized = " ".join(interview.split())
        self.assertIn("By default, after the user confirms that sentence, use its exact text for both required scalar fields", normalized)
        self.assertIn("If the user wants those fields to differ, ask for and confirm each value separately", normalized)
        self.assertIn("Never infer either value or generate a placeholder", normalized)
        self.assertIn("INIT-S08", scenario("INIT-S08"))
        self.assertIn("use the confirmed sentence verbatim", scenario("INIT-S08").lower())

    def test_initialization_status_matches_r_proj_02(self):
        interview = TEXT.split("## 4. Interview and draft model", 1)[1].split("## 5.", 1)[0]
        normalized = " ".join(interview.split())
        self.assertIn('Use `initialization.status: "complete"` only when `initialization.unknowns` is empty', normalized)
        self.assertIn('Use `initialization.status: "partial"` only when the unknowns array is non-empty', normalized)
        self.assertIn("every remaining unknown is non-blocking", normalized)
        self.assertIn('This flow does not write `initialization.status: "pending"` to `project.json`', normalized)
        self.assertIn('Use `"complete"` only when `initialization.unknowns` is empty, as required by R-PROJ-02', normalized)
        status_scenario = scenario("INIT-S09").lower()
        self.assertIn("persist `partial`", status_scenario)
        self.assertIn("persist `complete` with an empty unknowns array", status_scenario)
        self.assertIn("any blocking unknown prevents writes", status_scenario)

    def test_generation_requires_user_summary_confirmation(self):
        summary = TEXT.split("## 5. Summary", 1)[1].split("## 6.", 1)[0]
        self.assertIn("Only an explicit", summary)
        self.assertIn("Before constructing any file-write plan", summary)
        self.assertIn("summary confirmation and write-plan approval are separate", NORMALIZED.lower())
        self.assertIn("INIT-S05", scenario("INIT-S05"))
        self.assertIn("do not write", scenario("INIT-S05").lower())

    def test_collision_preview_exercises_each_outcome_and_conflict_blocks_writes(self):
        preview = TEXT.split("## 6. Destination inventory", 1)[1].split("## 7.", 1)[0]
        for outcome in ("CREATE", "MERGE", "SKIP", "CONFLICT"):
            self.assertIn(f"| `{outcome}` |", preview)
        self.assertIn("exact relative path", " ".join(preview.split()))
        self.assertIn("unapproved conflict blocks every write", " ".join(preview.split()))
        self.assertRegex(scenario("INIT-S04"), r"CREATE.*SKIP.*MERGE.*CONFLICT")
        self.assertIn("conflict blocks all writes", scenario("INIT-S04"))
        normalized_preview = " ".join(preview.split())
        self.assertIn("The preview names each path", normalized_preview)
        self.assertIn("Show the proposed result/diff", normalized_preview)

    def test_cancel_incomplete_answers_and_resume_preserve_the_target(self):
        state_flow = TEXT.split("## 7. State flow", 1)[1].split("## 8.", 1)[0]
        self.assertIn("Incomplete answers", state_flow)
        self.assertIn("Pause/resume in the same available session", state_flow)
        self.assertIn("Resume after a session is lost", state_flow)
        self.assertIn("Cancel:", state_flow)
        self.assertIn("INIT-S03", scenario("INIT-S03"))
        self.assertIn("INIT-S07", scenario("INIT-S07"))
        self.assertIn("leave the target unchanged", scenario("INIT-S07"))

    def test_scenario_ids_are_unique_and_acceptance_map_covers_four_criteria(self):
        identifiers = re.findall(r"^\| (INIT-S\d{2}) —", TEXT, re.MULTILINE)
        self.assertEqual(len(identifiers), len(set(identifiers)))
        mapping = TEXT.split("### Acceptance-criterion mapping", 1)[1].split("## 9.", 1)[0]
        mapping_rows = [
            line for line in mapping.splitlines()
            if line.startswith("| ") and not re.fullmatch(r"\|[-| ]+\|?", line)
        ]
        self.assertEqual(len(mapping_rows), 5)
        self.assertIn("Existing and empty project flows", mapping)
        self.assertIn("Unknowns are explicit", mapping)
        self.assertIn("User confirms summary", mapping)
        self.assertIn("Collision preview", mapping)


if __name__ == "__main__":
    unittest.main()
