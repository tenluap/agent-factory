"""Text contract for PR publication (SKILL.md step 9, state.md Resume `pr`).

`pr_contract_gaps` checks the real core text and, through mutated copies,
proves each element fails on its own: every injected copy must report exactly
the one element whose marker was removed (or whose forbidden line was added).
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "core" / "skills" / "factory" / "SKILL.md"
STATE = REPO / "core" / "skills" / "factory" / "references" / "state.md"


def pr_section(skill_text):
    """SKILL.md text from `## 9. PR` up to the next `## ` heading."""
    match = re.search(r"^## 9\. PR\n(.*?)(?=^## )", skill_text, re.S | re.M)
    return match.group(1) if match else ""


LOOKUP = "gh pr list --head <branch> --state open --json url,assignees"
AFTER_ERROR_LITERALS = ("gh pr create", "error", "Branch PR lookup", "retry")


def pr_contract_gaps(skill_text, state_text):
    """Names of missing PR publication elements, in contract order."""
    section = pr_section(skill_text)
    lines = section.splitlines()
    gaps = []
    if not any(
        "gh pr create" in line and "--assignee @me" in line for line in lines
    ):
        gaps.append("self-assign")
    create_at = section.find("gh pr create")
    lookup_at = section.find(LOOKUP)
    if not 0 <= lookup_at < create_at:
        gaps.append("lookup-before-create")
    if not any(
        all(literal in line for literal in AFTER_ERROR_LITERALS) for line in lines
    ):
        gaps.append("lookup-after-error")
    if re.search(r"\bASK\b", section):
        gaps.append("no-ask")
    return gaps


def with_section(skill_text, transform):
    """Return skill_text with only its step 9 section transformed."""
    section = pr_section(skill_text)
    return skill_text.replace(section, transform(section), 1)


class PrPublicationContractTests(unittest.TestCase):
    def setUp(self):
        self.skill = SKILL.read_text(encoding="utf-8")
        self.state = STATE.read_text(encoding="utf-8")

    def test_real_core_text_has_no_gaps(self):
        self.assertEqual(pr_contract_gaps(self.skill, self.state), [])

    def test_creation_without_self_assign_reports_self_assign(self):
        mutated = with_section(self.skill, lambda s: s.replace(" --assignee @me", ""))
        self.assertEqual(pr_contract_gaps(mutated, self.state), ["self-assign"])

    def test_lookup_command_removed_reports_lookup_before_create(self):
        mutated = with_section(self.skill, lambda s: s.replace(LOOKUP, ""))
        self.assertEqual(
            pr_contract_gaps(mutated, self.state), ["lookup-before-create"]
        )

    def test_after_error_sentence_removed_reports_lookup_after_error(self):
        mutated = with_section(
            self.skill,
            lambda s: "".join(
                line
                for line in s.splitlines(keepends=True)
                if "After a `gh pr create` error" not in line
            ),
        )
        self.assertEqual(pr_contract_gaps(mutated, self.state), ["lookup-after-error"])

    def test_ask_line_in_section_reports_no_ask(self):
        mutated = with_section(
            self.skill,
            lambda s: s + "ASK: ask the user for a GitHub username.\n",
        )
        self.assertEqual(pr_contract_gaps(mutated, self.state), ["no-ask"])


if __name__ == "__main__":
    unittest.main()
