"""Text contract for commit scope (spec 026): code-writing roles stage by
explicit path.

`commit_scope_gaps` checks the real core text and, through mutated copies,
proves each element fails on its own: every copy with one marker removed must
report exactly that marker.
"""

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


def commit_scope_gaps(texts):
    """Missing markers as `<role>: <marker>`, in contract order.

    `texts` maps a role name to its file text."""
    gaps = []
    for role in STAGING_ROLES:
        for marker in STAGING_MARKERS:
            if marker not in texts[role]:
                gaps.append(f"{role}: {marker}")
    step = resume_step(texts["code-build"])
    for marker in RESUME_MARKERS:
        if marker not in step:
            gaps.append(f"code-build step 1: {marker}")
    return gaps


def real_texts():
    return {
        role: (ROLES / f"{role}.md").read_text(encoding="utf-8")
        for role in STAGING_ROLES
    }


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


if __name__ == "__main__":
    unittest.main()
