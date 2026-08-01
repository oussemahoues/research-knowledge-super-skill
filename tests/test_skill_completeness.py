from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


class SkillCompletenessTests(unittest.TestCase):
    def test_stage_skills_are_operational_not_stubs(self) -> None:
        failures: list[str] = []
        for skill_dir in sorted(path for path in SKILLS.iterdir() if path.is_dir()):
            path = skill_dir / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            lines = text.splitlines()
            if len(lines) < 70:
                failures.append(f"{skill_dir.name}: only {len(lines)} lines")
            for heading in ("## Inputs", "## Procedure", "## Output contract", "## Completion checklist"):
                if heading not in text:
                    failures.append(f"{skill_dir.name}: missing {heading}")
            if "## Failure recovery" not in text and "## Edge cases" not in text:
                failures.append(f"{skill_dir.name}: missing failure recovery or edge cases")
            if not re.search(r"```json\n\{", text):
                failures.append(f"{skill_dir.name}: missing concrete JSON contract example")
            description = text.split("---", 2)[1] if text.startswith("---") else ""
            if "This skill should be used when" not in description:
                failures.append(f"{skill_dir.name}: trigger description is not third-person/assertive")
            if "Do not" not in description:
                failures.append(f"{skill_dir.name}: trigger description lacks scope boundary")
        self.assertEqual([], failures, "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
