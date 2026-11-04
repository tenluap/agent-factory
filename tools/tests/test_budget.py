"""Budget seam tests: resolution order, deadline derivation, the
`factory budget <role>` read command (FR-001, FR-007); the ledger-add
overrun detection lives in the later tasks of this seam.
"""

import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

CORE_BIN = Path(__file__).resolve().parents[2] / "core" / "skills" / "factory" / "bin"
sys.path.insert(0, str(CORE_BIN))

from factory_cli import budget, state  # noqa: E402

from tests import Sandbox, fixture  # noqa: E402


class ResolutionTests(unittest.TestCase):
    def test_role_override_wins(self):
        config = {"budget": {"default_s": 120, "roles": {"code-build": 240}}}
        self.assertEqual(budget.resolve("code-build", config), 240)

    def test_default_when_the_role_has_no_entry(self):
        config = {"budget": {"default_s": 120, "roles": {"code-build": 240}}}
        self.assertEqual(budget.resolve("spec-builder", config), 120)

    def test_fallback_is_300_seconds(self):
        self.assertEqual(budget.resolve("code-build", {}), 300)
        self.assertEqual(budget.resolve("code-build", None), 300)

    def test_malformed_values_fall_back_per_entry(self):
        for bad in (0, -5, "240", 2.5, None, True):
            config = {"budget": {"roles": {"code-build": bad}, "default_s": 120}}
            self.assertEqual(budget.resolve("code-build", config), 120, repr(bad))
        self.assertEqual(
            budget.resolve("code-build", {"budget": {"default_s": "x", "roles": {}}}),
            300,
        )

    def test_budget_not_a_dict_never_fails(self):
        self.assertEqual(budget.resolve("code-build", {"budget": "nope"}), 300)

    def test_orchestrator_is_a_valid_role(self):
        config = {"budget": {"roles": {"orchestrator": 600}}}
        self.assertEqual(budget.resolve("orchestrator", config), 600)


class BudgetCommandTests(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.config = self.box.home / "config.json"

    def cli(self, *args):
        return self.box.cli("budget", *args)

    def test_reports_role_seconds_and_absolute_deadline(self):
        self.config.write_text(json.dumps({"budget": {"roles": {"code-build": 240}}}))
        out = self.cli("code-build")
        self.assertEqual(out.returncode, 0, out.stderr)
        body = json.loads(out.stdout)
        self.assertEqual(body["role"], "code-build")
        self.assertEqual(body["seconds"], 240)
        deadline = state.parse_iso(body["deadline"])
        self.assertIsNotNone(deadline, "deadline is an ISO-8601 UTC timestamp")
        now = datetime.now(timezone.utc)
        skew = abs((deadline - now).total_seconds() - 240)
        self.assertLess(skew, 5, "deadline is now + the role's seconds")

    def test_missing_or_malformed_config_never_fails(self):
        out = self.cli("code-build")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout)["seconds"], 300)
        self.config.write_text("{not json")
        out = self.cli("code-build")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout)["seconds"], 300)

    def test_orchestrator_budget_resolves(self):
        self.config.write_text(json.dumps({"budget": {"roles": {"orchestrator": 600}}}))
        out = self.cli("orchestrator")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout)["seconds"], 600)


class OverrunDetectionTests(unittest.TestCase):
    """`factory ledger-add`'s overrun detection (FR-006): --overrun self-report
    wins, a duration over the role's budget yields cause `unreported`, and an
    overrun both self-reported and detected is recorded exactly once."""

    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.config = self.box.home / "config.json"
        self.config.write_text(json.dumps({"budget": {"roles": {"code-build": 100}}}))
        self.wt = self.box.worktree_run("040-overruns", fixture("state-v4.json"))
        self.state_path = self.wt / "specs" / "040-overruns" / "factory" / "state.json"

    def ledger_add(self, *extra, role="code-build", overrun=None, marked=False):
        args = [
            "ledger-add",
            "implement",
            role,
            "--started-at",
            "2026-10-23T10:00:00Z",
            "--ended-at",
            "2026-10-23T10:03:20Z",
        ]
        if overrun is not None:
            args += ["--overrun", json.dumps(overrun)]
        if marked:
            args += ["--partial-return"]
        return self.box.cli(*args, *extra, cwd=self.wt)

    def issues(self):
        return json.loads(self.state_path.read_text()).get("issues") or []

    def test_self_report_wins_over_detection(self):
        out = self.ledger_add(
            overrun={"cause": "test-loop", "detail": "red loop 41s past"}
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        issues = self.issues()
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["kind"], "overrun")
        self.assertEqual(issues[0]["cause"], "test-loop")
        self.assertEqual(issues[0]["detail"], "red loop 41s past")
        self.assertEqual(issues[0]["duration_ms"], 200000)
        self.assertIs(issues[0]["partial_return"], False)

    def test_detected_detail_reports_rounded_excess_and_total(self):
        for end, expected in (
            ("2026-10-23T10:05:19Z", "19s past its 300s budget (319s total)"),
            ("2026-10-23T10:05:00.001Z", "1s past its 300s budget (301s total)"),
        ):
            out = self.box.cli(
                "ledger-add",
                "review",
                "spec-conformance",
                "--started-at",
                "2026-10-23T10:00:00Z",
                "--ended-at",
                end,
                cwd=self.wt,
            )
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertEqual(
                self.issues()[-1]["detail"],
                f"spec-conformance ran {expected} without a self-report",
            )

    def test_detection_yields_unreported(self):
        out = self.ledger_add()
        self.assertEqual(out.returncode, 0, out.stderr)
        issues = self.issues()
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["cause"], "unreported")
        self.assertEqual(issues[0]["role"], "code-build")
        self.assertTrue(issues[0]["detail"], "the detail names the detected overrun")

    def test_no_issue_when_neither_signal_holds(self):
        out = self.box.cli(
            "ledger-add",
            "implement",
            "code-build",
            "--started-at",
            "2026-10-23T10:00:00Z",
            "--ended-at",
            "2026-10-23T10:01:30Z",  # 90s: over nothing else, under the 100s budget
            cwd=self.wt,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(self.issues(), [])

    def test_both_signals_record_exactly_one_issue(self):
        out = self.ledger_add(overrun={"cause": "tool-slow", "detail": "slow tool"})
        self.assertEqual(out.returncode, 0, out.stderr)
        issues = self.issues()
        self.assertEqual(len(issues), 1, "self-report and detection record once")
        self.assertEqual(issues[0]["cause"], "tool-slow")

    def test_partial_return_stamps_only_when_passed(self):
        out = self.ledger_add(overrun={"cause": "other", "detail": "d"}, marked=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIs(self.issues()[0]["partial_return"], True)
        result = json.loads(out.stdout)
        self.assertIn("stalls", result, "a marked record reports the stall rule")
        unmarked = self.ledger_add(overrun={"cause": "other", "detail": "d"})
        self.assertIs(json.loads(unmarked.stdout)["issue"]["partial_return"], False)

    def stalls_of(self, out):
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)["stalls"]

    def partial_stop(self):
        return self.ledger_add(
            overrun={"cause": "test-loop", "detail": "deadline"}, marked=True
        )

    def test_repeat_partial_returns_without_commit_halt_on_the_third(self):
        self.assertEqual(
            self.stalls_of(self.partial_stop())["consecutive_no_commit"], 1
        )
        self.assertEqual(
            self.stalls_of(self.partial_stop())["consecutive_no_commit"], 2
        )
        third = self.stalls_of(self.partial_stop())
        self.assertEqual(third["consecutive_no_commit"], 3)
        self.assertIs(third["halt"], True)
        self.assertEqual(len(self.issues()), 3, "one record per spawn, none dropped")

    def test_a_work_commit_between_partial_returns_resets_the_count(self):
        self.partial_stop()
        self.partial_stop()
        (self.wt / "work.txt").write_text("progress")
        self.box.git("add", "work.txt", cwd=self.wt)
        self.box.git("commit", "-q", "-m", "T001: progress", cwd=self.wt)
        fresh = self.stalls_of(self.partial_stop())
        self.assertEqual(fresh["consecutive_no_commit"], 1)
        self.assertIs(fresh["halt"], False)


if __name__ == "__main__":
    unittest.main()
