"""Text contract for commit scope (spec 026): code-writing roles stage by
explicit path.

`commit_scope_gaps` checks the real core text and, through mutated copies,
proves each element fails on its own: every copy with one marker removed must
report exactly that marker.
"""

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROLES = REPO / "core" / "roles"
STAGING_ROLES = ("code-build", "design-to-code", "fixer")
STAGING_MARKERS = (
    "git add -- <path>",
    "git add -A",
    "git add .",
    "git commit -a",
)


RESUME_MARKERS = (
    "only when the task being resumed names its path",
    "never stage, commit, stash or discard it",
)


def resume_step(code_build_text):
    """code-build's Work step 1 line."""
    return next(
        (line for line in code_build_text.splitlines() if line.startswith("1. ")), ""
    )


SKILL = REPO / "core" / "skills" / "factory" / "SKILL.md"
APPROVER_MARKERS = (
    "git status --porcelain",
    "📂 Uncommitted local changes the run didn't make",
    "neither commits nor discards them",
)


def approver_section(skill_text):
    """SKILL.md text from `## 8. Approver` up to the next `## ` heading."""
    match = re.search(r"^## 8\. Approver\n(.*?)(?=^## )", skill_text, re.S | re.M)
    return match.group(1) if match else ""


def approver_gaps(skill_text):
    """Missing approver markers as `approver: <marker>`."""
    section = approver_section(skill_text)
    return [f"approver: {m}" for m in APPROVER_MARKERS if m not in section]


def commit_scope_gaps(texts):
    """Missing markers as `<role>: <marker>`, in contract order.

    `texts` maps a role name to its file text; the `skill` key holds SKILL.md."""
    gaps = []
    for role in STAGING_ROLES:
        for marker in STAGING_MARKERS:
            if marker not in texts[role]:
                gaps.append(f"{role}: {marker}")
    step = resume_step(texts["code-build"])
    for marker in RESUME_MARKERS:
        if marker not in step:
            gaps.append(f"code-build step 1: {marker}")
    return gaps + approver_gaps(texts["skill"])


def real_texts():
    texts = {
        role: (ROLES / f"{role}.md").read_text(encoding="utf-8")
        for role in STAGING_ROLES
    }
    texts["skill"] = SKILL.read_text(encoding="utf-8")
    return texts


class CommitScopeContractTests(unittest.TestCase):
    def setUp(self):
        self.texts = real_texts()

    def test_real_core_text_has_no_staging_gap(self):
        self.assertEqual(commit_scope_gaps(self.texts), [])

    def test_each_removed_staging_marker_reports_exactly_that_gap(self):
        for role in STAGING_ROLES:
            for marker in STAGING_MARKERS:
                with self.subTest(role=role, marker=marker):
                    mutated = dict(self.texts)
                    mutated[role] = mutated[role].replace(marker, "")
                    self.assertEqual(commit_scope_gaps(mutated), [f"{role}: {marker}"])

    def test_real_core_text_has_no_resume_gap(self):
        gaps = [g for g in commit_scope_gaps(self.texts) if "step 1" in g]
        self.assertEqual(gaps, [])

    def test_each_removed_resume_marker_reports_exactly_that_gap(self):
        for marker in RESUME_MARKERS:
            with self.subTest(marker=marker):
                mutated = dict(self.texts)
                mutated["code-build"] = mutated["code-build"].replace(marker, "")
                self.assertEqual(
                    commit_scope_gaps(mutated), [f"code-build step 1: {marker}"]
                )

    def test_real_core_text_has_no_approver_gap(self):
        self.assertEqual(approver_gaps(self.texts["skill"]), [])

    def test_each_removed_approver_marker_reports_exactly_that_gap(self):
        for marker in APPROVER_MARKERS:
            with self.subTest(marker=marker):
                mutated = dict(self.texts)
                mutated["skill"] = mutated["skill"].replace(marker, "")
                self.assertEqual(commit_scope_gaps(mutated), [f"approver: {marker}"])


if __name__ == "__main__":
    unittest.main()
