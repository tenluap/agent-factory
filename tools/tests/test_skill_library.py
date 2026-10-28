"""Skill library layout and installer contracts."""

import re
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SKILLS = ("grilling", "domain-modeling", "pr", "ponytail", "tdd", "brainstorming")


class SkillLibraryLayoutTests(unittest.TestCase):
    def test_required_skills_have_matching_names_licenses_and_provenance(self):
        sources = (REPO / "skills/SOURCES.md").read_text()
        for name in SKILLS:
            with self.subTest(name=name):
                folder = REPO / "skills" / name
                text = (folder / "SKILL.md").read_text()
                self.assertRegex(
                    text,
                    rf"(?ms)^---\s*\n.*?^name:\s*['\"]?{re.escape(name)}['\"]?\s*$.*?^---\s*$",
                )
                self.assertTrue((folder / "LICENSE").is_file())
                self.assertRegex(
                    sources,
                    rf"(?m)^\|\s*{re.escape(name)}\s*\|\s*https://[^|]+\|\s*[^|]+\|\s*[0-9a-f]{{40}}\s*\|\s*MIT\s*\|",
                )
