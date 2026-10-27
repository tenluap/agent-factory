"""Issue-add writer seam tests: the shared issue append path (FR-008).

One record per event through `factory issue-add`, the closed kind/cause
vocabularies with named refusals, the `--partial-return` mark rules, and
the stall rule result over every marked record.
"""

import json
import subprocess
import unittest
from pathlib import Path

from tests import Sandbox, fixture

V4 = fixture("state-v4.json")


class IssueAddTests(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.wt = self.box.worktree_run("030-issues", V4)
        self.state_path = self.wt / "specs" / "030-issues" / "factory" / "state.json"

    def add(self, *args):
        return self.box.cli("issue-add", *args, cwd=self.wt)

    def issues(self):
        return json.loads(self.state_path.read_text())["issues"]

    def test_appends_one_record_per_event(self):
        out = self.add(
            "overrun",
            "implement",
            "code-build",
            "--detail",
            "red loop",
            "--duration-ms",
            "341000",
            "--cause",
            "test-loop",
            "--commit",
            "abc1234",
            "--partial-return",
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        out = self.add(
            "agent-failure",
            "implement",
            "code-build",
            "--detail",
            "crashed",
            "--duration-ms",
            "5000",
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        issues = self.issues()
        self.assertEqual(len(issues), 2, "one record per event")
        self.assertEqual(issues[0]["kind"], "overrun")
        self.assertEqual(issues[0]["stage"], "implement")
        self.assertEqual(issues[0]["role"], "code-build")
        self.assertEqual(issues[0]["cause"], "test-loop")
        self.assertEqual(issues[0]["detail"], "red loop")
        self.assertEqual(issues[0]["duration_ms"], 341000)
        self.assertEqual(issues[0]["commit"], "abc1234")
        self.assertIs(issues[0]["partial_return"], True)
        self.assertIs(issues[1]["cause"], None)
        self.assertIs(issues[1]["partial_return"], False)
        for field in ("at", "detail"):
            self.assertTrue(issues[0][field], field)

    def test_commit_defaults_to_worktree_head(self):
        head = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(self.wt),
            capture_output=True,
            text=True,
        ).stdout.strip()
        out = self.add(
            "halt",
            "implement",
            "orchestrator",
            "--detail",
            "stalled",
            "--duration-ms",
            "10",
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(self.issues()[0]["commit"], head)

    def test_cause_optional_and_stored_null_for_other_kinds(self):
        out = self.add(
            "agent-failure",
            "implement",
            "code-build",
            "--detail",
            "crashed",
            "--duration-ms",
            "5",
            "--cause",
            "test-loop",
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIs(self.issues()[0]["cause"], None)

    def test_refusals_name_the_problem(self):
        cases = [
            (
                (
                    "crash",
                    "implement",
                    "code-build",
                    "--detail",
                    "d",
                    "--duration-ms",
                    "1",
                ),
                "kind",
            ),
            (
                (
                    "overrun",
                    "implement",
                    "code-build",
                    "--detail",
                    "d",
                    "--duration-ms",
                    "1",
                ),
                "cause",
            ),
            (
                (
                    "overrun",
                    "implement",
                    "code-build",
                    "--detail",
                    "d",
                    "--duration-ms",
                    "1",
                    "--cause",
                    "slow",
                ),
                "cause",
            ),
            (
                (
                    "retry",
                    "implement",
                    "code-build",
                    "--detail",
                    "d",
                    "--duration-ms",
                    "later",
                ),
                "--duration-ms",
            ),
        ]
        for args, needle in cases:
            out = self.add(*args)
            self.assertEqual(out.returncode, 1, f"{args}: {out.stderr}")
            self.assertIn(needle, out.stderr)
            self.assertEqual(self.issues(), [], "a refused add appends nothing")

    def test_partial_return_refused_off_the_marked_shapes(self):
        cases = [
            (
                "halt",
                "code-build",
                "the partial_return mark is accepted only for overrun/retry "
                "of the file-writing roles",
            ),
            (
                "overrun",
                "review-judge",
                "the partial_return mark is accepted only for overrun/retry "
                "of the file-writing roles",
            ),
        ]
        for kind, role, needle in cases:
            out = self.add(
                kind,
                "implement",
                role,
                "--detail",
                "d",
                "--duration-ms",
                "1",
                "--cause",
                "other",
                "--partial-return",
            )
            self.assertEqual(out.returncode, 1, f"{kind}/{role}: {out.stderr}")
            self.assertIn(needle, out.stderr)


class StallRuleTests(unittest.TestCase):
    """The stall rule result over every marked partial-return record."""

    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.wt = self.box.worktree_run("031-stalls", V4)
        self.state_path = self.wt / "specs" / "031-stalls" / "factory" / "state.json"

    def add(self, *extra, kind="overrun", commit="aaa0001", marked=True):
        args = [
            "issue-add",
            kind,
            "implement",
            "code-build",
            "--detail",
            "d",
            "--duration-ms",
            "1000",
            "--commit",
            commit,
        ]
        if kind == "overrun":
            args += ["--cause", "other"]
        if marked:
            args += ["--partial-return"]
        return self.box.cli(*args, *extra, cwd=self.wt)

    def result(self, out):
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)

    def test_counts_trailing_marked_records_and_halts_at_three(self):
        first = self.result(self.add())
        self.assertEqual(first["stalls"]["consecutive_no_commit"], 1)
        self.assertIs(first["stalls"]["halt"], False)
        second = self.result(self.add())
        self.assertEqual(second["stalls"]["consecutive_no_commit"], 2)
        self.assertEqual(second["stalls"]["cap"], 3)
        third = self.result(self.add())
        self.assertEqual(third["stalls"]["consecutive_no_commit"], 3)
        self.assertIs(third["stalls"]["halt"], True)

    def test_a_new_commit_resets_the_count(self):
        self.result(self.add())
        self.result(self.add())
        fresh = self.result(self.add(commit="bbb0002"))
        self.assertEqual(fresh["stalls"]["consecutive_no_commit"], 1)
        self.assertIs(fresh["stalls"]["halt"], False)

    def test_unmarked_records_never_count(self):
        self.result(self.add())
        failed_retry = self.result(self.add(kind="retry", marked=False))
        self.assertNotIn("stalls", failed_retry, "an unmarked record does not count")
        again = self.result(self.add())
        self.assertEqual(
            again["stalls"]["consecutive_no_commit"],
            2,
            "the unmarked retry adds nothing",
        )

    def test_records_of_other_stages_do_not_break_the_trailing_count(self):
        self.result(self.add())
        self.result(
            self.add("ledger-noise", kind="retry", marked=False),
        )
        # a marked record of another stage in between the implement records
        other = self.box.cli(
            "issue-add",
            "overrun",
            "review",
            "code-build",
            "--detail",
            "d",
            "--duration-ms",
            "1000",
            "--cause",
            "other",
            "--commit",
            "aaa0001",
            cwd=self.wt,
        )
        self.assertEqual(other.returncode, 0, other.stderr)
        latest = self.result(self.add())
        self.assertEqual(latest["stalls"]["consecutive_no_commit"], 2)


if __name__ == "__main__":
    unittest.main()
