"""CLI seam tests: the `bin/factory` command surface, driven as a process.

Covers `runs`, `show` and `validate` exit codes and digests (contracts/cli.md),
`show`'s approver veto list (SC-004), and the 005/006 replay (SC-002).
"""

import json
import unittest

from tests import Sandbox, fixture
from tests import replay


def v4_state(**overrides):
    state = fixture("state-v4.json")
    state.update(overrides)
    return state


def veto_entries(decisions):
    """The approver's veto list: every auto-accepted answer, every override."""
    return [d for d in decisions if d.get("auto") or d.get("kind") == "gate-override"]


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.box.worktree_run("010-alpha", v4_state())
        self.box.pending_run("011-beta", fixture("state-v1.json"))

    def test_runs_lists_worktree_and_pending_runs(self):
        out = self.box.cli("runs")
        self.assertEqual(out.returncode, 0, out.stderr)
        runs = json.loads(out.stdout)["runs"]
        sources = {(r.get("source"), r.get("branch") or r.get("name")) for r in runs}
        self.assertIn(("worktree", "010-alpha"), sources)
        self.assertIn(("pending", "repo-011-beta"), sources)

    def test_runs_reports_validation_violations_instead_of_hiding(self):
        self.box.corrupt_worktree_state(
            "010-alpha", lambda s: s["history"][0].__setitem__("event", "bogus-event")
        )
        out = self.box.cli("runs")
        self.assertEqual(out.returncode, 0, out.stderr)
        entry = next(
            r for r in json.loads(out.stdout)["runs"] if r.get("branch") == "010-alpha"
        )
        self.assertTrue(
            any("bogus-event" in v.get("reason", "") for v in entry["violations"])
        )

    def test_runs_skips_ended_runs(self):
        self.box.worktree_run(
            "012-done",
            v4_state(
                status="pr-open",
                pr_url="https://x/pr/1",
                ended_at="2026-10-23T12:00:00Z",
            ),
        )
        out = self.box.cli("runs")
        branches = [r.get("branch") for r in json.loads(out.stdout)["runs"]]
        self.assertNotIn("012-done", branches)


class ShowTests(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.box.worktree_run("020-gamma", v4_state())

    def test_show_digest_fields_and_exit_zero(self):
        out = self.box.cli("show", "020-gamma")
        self.assertEqual(out.returncode, 0, out.stderr)
        digest = json.loads(out.stdout)
        for field in (
            "stage",
            "status",
            "mode",
            "history_tail",
            "waits",
            "spawns",
            "totals_sentence",
            "relay",
            "state_path",
        ):
            self.assertIn(field, digest, field)

    def test_show_unknown_run_exits_one(self):
        out = self.box.cli("show", "999-none")
        self.assertEqual(out.returncode, 1)
        self.assertIn("999-none", out.stderr)

    def test_show_ambiguous_name_exits_three(self):
        self.box.pending_run("020-gamma", fixture("state-v1.json"))
        out = self.box.cli("show", "020-gamma")
        self.assertEqual(out.returncode, 3)
        self.assertIn("several", out.stderr)

    def test_show_missing_recorded_worktree_exits_four(self):
        self.box.worktree_run(
            "021-delta", v4_state(), worktree=self.box.dir / "gone-021"
        )
        state_path = (
            self.box.dir / "gone-021" / "specs" / "021-delta" / "factory" / "state.json"
        )
        state = json.loads(state_path.read_text())
        state["worktree"] = str(self.box.dir / "deleted-021")
        state_path.write_text(json.dumps(state, indent=2))
        out = self.box.cli("show", "021-delta")
        self.assertEqual(out.returncode, 4)
        self.assertIn("no longer exists", out.stderr)

    def test_show_veto_list_names_auto_answers_and_gate_overrides(self):
        decisions = fixture("state-v4.json")["decisions"] + [
            {
                "stage": "plan",
                "question": "Q7",
                "answer": "B",
                "auto": True,
                "at": "2026-10-23T09:30:00Z",
                "kind": "answer",
            },
            {
                "stage": "implement",
                "question": "Q9",
                "answer": "override: proceed",
                "auto": False,
                "at": "2026-10-23T09:40:00Z",
                "kind": "gate-override",
            },
        ]
        self.box.corrupt_worktree_state(
            "020-gamma", lambda s: s.__setitem__("decisions", decisions)
        )
        out = self.box.cli("show", "020-gamma")
        self.assertEqual(out.returncode, 0, out.stderr)
        listed = json.loads(out.stdout)["decisions"]
        self.assertEqual(listed, veto_entries(decisions))
        self.assertTrue(any(d["question"] == "Q7" and d["auto"] for d in listed))
        self.assertTrue(
            any(
                d["kind"] == "gate-override" and d["stage"] == "implement"
                for d in listed
            )
        )
        self.assertFalse(
            any(
                d["question"] == "Q1" and d["kind"] == "answer" and not d["auto"]
                for d in listed
            ),
            "plain answers are not veto entries",
        )

    def test_show_veto_list_covers_every_stage_before_pr(self):
        decisions = [
            {
                "stage": "grill",
                "question": "Q1",
                "answer": "lite",
                "auto": True,
                "at": "2026-10-23T08:34:00Z",
                "kind": "answer",
            },
            {
                "stage": "review",
                "question": "Q3",
                "answer": "ship it",
                "auto": True,
                "at": "2026-10-23T09:20:00Z",
                "kind": "answer",
            },
        ]
        self.box.corrupt_worktree_state(
            "020-gamma", lambda s: s.__setitem__("decisions", decisions)
        )
        listed = json.loads(self.box.cli("show", "020-gamma").stdout)["decisions"]
        self.assertEqual({d["stage"] for d in listed}, {"grill", "review"})


class ValidateTests(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.box.worktree_run("030-epsilon", v4_state())

    def test_validate_clean_run_exits_zero(self):
        out = self.box.cli("validate", "030-epsilon")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout), [])

    def test_validate_reports_violations_with_location(self):
        self.box.corrupt_worktree_state(
            "030-epsilon",
            lambda s: (
                s["history"][1].__setitem__("event", "round-1-complete"),
                s["timeline"][0].__setitem__("kind", "approval"),
            ),
        )
        out = self.box.cli("validate", "030-epsilon")
        self.assertEqual(out.returncode, 1)
        violations = json.loads(out.stdout)
        locations = {v["location"] for v in violations}
        self.assertIn("history[1].event", locations)
        self.assertIn("timeline[0].kind", locations)
        self.assertTrue(all(v.get("reason") for v in violations))

    def test_validate_all_checks_every_run(self):
        self.box.worktree_run("031-zeta", fixture("state-v3.json"))
        out = self.box.cli("validate", "--all")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(json.loads(out.stdout), [])


class UsageTests(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)

    def test_unknown_command_exits_five(self):
        out = self.box.cli("frobnicate")
        self.assertEqual(out.returncode, 5, f"stderr: {out.stderr}")

    def test_missing_argument_exits_five(self):
        self.assertEqual(self.box.cli("show").returncode, 5)
        self.assertEqual(self.box.cli("runs", "--repo").returncode, 5)


class ReplayTests(unittest.TestCase):
    def test_replay_reports_every_core_defect_with_no_false_pass(self):
        ok, lines = replay.check()
        self.assertTrue(ok, "\n".join(lines))

    def test_replay_cli_exits_zero(self):
        import subprocess
        import sys
        from tests import REPO_ROOT

        out = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools" / "tests" / "replay.py")],
            capture_output=True,
            text=True,
        )
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)


if __name__ == "__main__":
    unittest.main()
