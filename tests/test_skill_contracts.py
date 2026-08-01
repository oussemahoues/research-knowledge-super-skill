from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


class SkillContractTests(unittest.TestCase):
    def test_stage_skills_are_operational_not_stubs(self) -> None:
        required_any = {
            "inputs": ("## Inputs", "## Required inputs"),
            "procedure": ("## Procedure",),
            "output": ("## Output contract", "## Output"),
            "recovery": ("## Failure recovery", "## Edge cases"),
            "completion": ("## Completion checklist",),
        }
        for skill_dir in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
            path = skill_dir / "SKILL.md"
            self.assertTrue(path.is_file(), skill_dir.name)
            text = path.read_text(encoding="utf-8")
            with self.subTest(skill=skill_dir.name):
                self.assertGreaterEqual(len(text.splitlines()), 70, "skill is too short to be operational")
                for label, headings in required_any.items():
                    self.assertTrue(any(h in text for h in headings), f"missing {label} contract")
                self.assertRegex(text, r"(?s)^---\nname: [a-z0-9-]+\ndescription: .+?\n---")

    def test_descriptions_have_trigger_and_boundary_language(self) -> None:
        for path in sorted(SKILLS.glob("*/SKILL.md")):
            text = path.read_text(encoding="utf-8")
            frontmatter = text.split("---", 2)[1]
            with self.subTest(skill=path.parent.name):
                self.assertIn("This skill should be used when", frontmatter)
                self.assertIn("Do not", frontmatter)

    def test_runtime_and_references_are_reachable(self) -> None:
        orchestrator = (SKILLS / "running-evidence-research" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("scripts/researchctl.py", orchestrator)
        self.assertIn("references/architecture.md", orchestrator)
        self.assertIn("references/security.md", orchestrator)
        self.assertIn("references/evaluation.md", orchestrator)

    def test_no_placeholder_language(self) -> None:
        forbidden = re.compile(r"\b(TODO|TBD|placeholder|fill this in|coming soon)\b", re.I)
        for path in sorted(SKILLS.glob("*/SKILL.md")):
            with self.subTest(skill=path.parent.name):
                self.assertIsNone(forbidden.search(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
