"""CLI seam tests: the `bin/factory` command surface, driven as a process.

Covers `runs`, `show` and `validate` exit codes and digests (contracts/cli.md),
`show`'s approver veto list (SC-004), and the 005/006 replay (SC-002).
"""

import json
import os
import shutil
import socket
import unittest
from pathlib import Path
from datetime import datetime, timezone

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

    def test_runs_skips_aborted_runs_too(self):
        # FR-017: resume refuses an aborted run, so runs must not list it
        self.box.worktree_run(
            "013-aborted",
            v4_state(status="aborted", ended_at="2026-10-23T12:00:00Z"),
        )
        out = self.box.cli("runs")
        self.assertEqual(out.returncode, 0, out.stderr)
        branches = [r.get("branch") for r in json.loads(out.stdout)["runs"]]
        self.assertNotIn(
            "013-aborted", branches, "an aborted run never appears in runs"
        )


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

    def test_show_digest_aggregates_come_from_totals_alone(self):
        # FR-015: with overlapping spawns the summed parallel duplicates are
        # gone; the union totals are the only elapsed aggregates
        self.box.worktree_run(
            "025-overlap",
            v4_state(
                ledger=[
                    {
                        "at": "2026-10-23T10:00:00Z",
                        "stage": "implement",
                        "role": "code-build",
                        "harness": "opencode",
                        "started_at": "2026-10-23T10:00:00Z",
                        "ended_at": "2026-10-23T10:05:00Z",
                        "duration_ms": 300000,
                        "in_est": 0,
                        "out_est": 0,
                        "reported": None,
                    },
                    {
                        "at": "2026-10-23T10:01:00Z",
                        "stage": "review",
                        "role": "code-standards",
                        "harness": "opencode",
                        "started_at": "2026-10-23T10:01:00Z",
                        "ended_at": "2026-10-23T10:04:00Z",
                        "duration_ms": 180000,
                        "in_est": 0,
                        "out_est": 0,
                        "reported": None,
                    },
                ],
            ),
        )
        out = self.box.cli("show", "025-overlap")
        self.assertEqual(out.returncode, 0, out.stderr)
        digest = json.loads(out.stdout)
        self.assertNotIn("human_ms", digest["waits"], "the summed duplicate is gone")
        self.assertNotIn("agent_ms", digest["spawns"], "the summed duplicate is gone")
        self.assertEqual(
            digest["totals"]["agent_ms"],
            300000,
            "the union of the overlapping intervals, never their sum",
        )

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


class EndedPendingRunTests(unittest.TestCase):
    """FR-009: the ended-status skip applies to pending-run selection too;
    an ended pending run can never be mutated."""

    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.box.pending_run(
            "050-ended",
            v4_state(
                status="pr-open",
                pr_url="https://x/pr/9",
                ended_at="2026-10-23T12:00:00Z",
            ),
        )

    def test_write_to_ended_pending_run_is_refused_with_the_status_named(self):
        out = self.box.cli("ledger-add", "plan", "spec-builder")
        self.assertEqual(out.returncode, 1, out.stderr + out.stdout)
        message = out.stderr + out.stdout
        self.assertIn("pr-open", message, "the refusal names the ended status")
        self.assertNotIn("Traceback", message, "no traceback at the user")

    def test_aborted_pending_run_is_refused_too(self):
        box = Sandbox()
        self.addCleanup(box.close)
        box.pending_run(
            "051-aborted",
            v4_state(status="aborted", ended_at="2026-10-23T12:00:00Z"),
        )
        out = box.cli("ledger-add", "plan", "spec-builder")
        self.assertEqual(out.returncode, 1, out.stderr + out.stdout)
        self.assertIn("aborted", out.stderr + out.stdout)


class RetroEndedRunTests(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.wt = self.box.worktree_run(
            "052-retro",
            v4_state(
                status="pr-open",
                pr_url="https://x/pr/9",
                ended_at="2026-10-23T12:00:00Z",
            ),
        )
        self.path = self.wt / "specs/052-retro/factory/state.json"

    def test_retro_ledger_on_pr_open(self):
        out = self.box.cli("ledger-add", "retro", "retro", cwd=self.wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(
            json.loads(self.path.read_text())["ledger"][-1]["stage"], "retro"
        )

    def test_retro_issue_on_pr_open(self):
        out = self.box.cli(
            "issue-add",
            "retry",
            "retro",
            "retro",
            "--detail",
            "failed",
            "--duration-ms",
            "1",
            cwd=self.wt,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        issue = json.loads(self.path.read_text())["issues"][-1]
        self.assertEqual((issue["kind"], issue["stage"]), ("retry", "retro"))

    def test_other_stage_on_pr_open_is_refused_unchanged(self):
        before = self.path.read_bytes()
        out = self.box.cli("ledger-add", "plan", "spec-builder", cwd=self.wt)
        self.assertEqual(out.returncode, 1, out.stderr)
        self.assertEqual(self.path.read_bytes(), before)

    def test_retro_writes_on_aborted_are_refused_unchanged(self):
        data = json.loads(self.path.read_text())
        data["status"] = "aborted"
        self.path.write_text(json.dumps(data))
        before = self.path.read_bytes()
        for args in (
            ("ledger-add", "retro", "retro"),
            (
                "issue-add",
                "retry",
                "retro",
                "retro",
                "--detail",
                "failed",
                "--duration-ms",
                "1",
            ),
        ):
            with self.subTest(args=args):
                out = self.box.cli(*args, cwd=self.wt)
                self.assertEqual(out.returncode, 1, out.stderr)
                self.assertEqual(self.path.read_bytes(), before)


class LedgerTimestampTests(unittest.TestCase):
    """FR-007: a malformed --started-at/--ended-at is a usage refusal (exit 5)
    naming the offending value, never a traceback; the value never reaches the
    duration arithmetic."""

    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.wt = self.box.worktree_run("030-ledger", v4_state())

    def run_ledger_add(self, *extra):
        return self.box.cli("ledger-add", "plan", "spec-builder", *extra, cwd=self.wt)

    def assert_usage_refusal(self, out, value):
        self.assertEqual(out.returncode, 5, out.stderr + out.stdout)
        message = out.stderr + out.stdout
        self.assertIn(value, message, "the message names the offending value")
        self.assertNotIn("Traceback", message, "no traceback at the user")

    def test_malformed_started_at_exits_five(self):
        self.assert_usage_refusal(
            self.run_ledger_add("--started-at", "yesterday"), "yesterday"
        )

    def test_malformed_ended_at_exits_five(self):
        self.assert_usage_refusal(
            self.run_ledger_add("--ended-at", "soon-ish"), "soon-ish"
        )

    def test_empty_timestamp_exits_five(self):
        out = self.run_ledger_add("--started-at", "")
        self.assertEqual(out.returncode, 5, out.stderr + out.stdout)
        self.assertNotIn("Traceback", out.stderr + out.stdout)

    def test_missing_flag_value_exits_five(self):
        self.assertEqual(self.run_ledger_add("--started-at").returncode, 5)

    def test_good_start_with_bad_end_exits_five(self):
        self.assert_usage_refusal(
            self.run_ledger_add(
                "--started-at", "2026-10-22T14:00:00Z", "--ended-at", "later"
            ),
            "later",
        )


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


def writer_state():
    """A running v3-shaped state with an open relay round, ready to upgrade."""
    s = fixture("state-v3.json")
    s["stage"] = "plan"
    s["relay"] = {
        "stage": "plan",
        "rounds": [
            {
                "questions": [{"id": "Q5", "text": "Pick one", "recommended": "B"}],
                "answers": {
                    "Q5": {"answer": "B", "at": "2026-10-22T14:05:00Z", "auto": True}
                },
            }
        ],
    }
    s["decisions"] = [
        {
            "stage": "grill",
            "question": "Q1",
            "answer": "full",
            "auto": False,
            "at": "2026-10-22T14:04:00Z",
            "kind": "answer",
        }
    ]
    return s


class WriterTests(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.wt = self.box.worktree_run("040-writer", writer_state())
        self.state_path = self.wt / "specs" / "040-writer" / "factory" / "state.json"

    def load(self):
        return json.loads(self.state_path.read_text())

    def recent(self, stamp):
        return (
            abs(
                replay.parse_iso(stamp).timestamp()
                - datetime.now(timezone.utc).timestamp()
            )
            < 120
        )

    def committed_clean(self):
        status = self.box.git("status", "--porcelain", cwd=self.wt).strip()
        return status == ""

    def test_checkpoint_stamps_appends_migrates_and_commits(self):
        before = self.load()
        out = self.box.cli("checkpoint", "plan", cwd=self.wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        after = self.load()
        self.assertEqual(
            after["stage"], "tasks", "linear successor becomes the next stage"
        )
        entry = after["history"][-1]
        self.assertEqual((entry["stage"], entry["event"]), ("plan", "complete"))
        self.assertTrue(self.recent(entry["at"]), "the writer stamps its own time")
        self.assertEqual(entry["harness"], before["harness"])
        migrated = next(d for d in after["decisions"] if d["question"] == "Q5")
        self.assertEqual(
            (migrated["answer"], migrated["auto"], migrated["kind"]),
            ("B", True, "answer"),
            "settled relay answers move into decisions (FR-008)",
        )
        self.assertTrue(
            self.recent(migrated["at"]),
            "the migration stamps the checkpoint's own time",
        )
        self.assertIsNone(after["relay"], "relay is cleared after its answers move")
        self.assertEqual(
            after["decisions"][0], before["decisions"][0], "decisions are append-only"
        )
        last = self.box.git("log", "-1", "--format=%s", cwd=self.wt).strip()
        self.assertEqual(last, "factory: plan complete")
        self.assertTrue(
            self.committed_clean(), "the checkpoint commits the state write"
        )

    def test_checkpoint_migrates_answers_older_than_existing_decisions(self):
        self.box.corrupt_worktree_state(
            "040-writer",
            lambda s: s["decisions"].append(
                {
                    "stage": "plan",
                    "question": "Q9",
                    "answer": "a later decision",
                    "auto": False,
                    "at": "2026-10-23T09:00:00Z",
                    "kind": "answer",
                }
            ),
        )
        out = self.box.cli("checkpoint", "plan", cwd=self.wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        decisions = self.load()["decisions"]
        stamps = [replay.parse_iso(d["at"]) for d in decisions]
        self.assertEqual(
            stamps, sorted(stamps), "decisions stay non-decreasing after migration"
        )
        migrated = next(d for d in decisions if d["question"] == "Q5")
        self.assertEqual(
            (migrated["answer"], migrated["auto"], migrated["kind"]),
            ("B", True, "answer"),
            "the settled answer still moves into decisions (FR-008)",
        )

    def test_checkpoint_next_flag_serves_non_linear_flows(self):
        out = self.box.cli("checkpoint", "analyze", "--next", "analyze", cwd=self.wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(
            self.load()["stage"],
            "analyze",
            "the analyze loop re-enters without leaving the writer",
        )

    def test_checkpoint_refuses_invalid_state_untouched(self):
        self.box.corrupt_worktree_state(
            "040-writer", lambda s: s["history"][1].__setitem__("event", "bogus")
        )
        before = self.state_path.read_text()
        out = self.box.cli("checkpoint", "plan", cwd=self.wt)
        self.assertEqual(out.returncode, 1)
        self.assertIn("bogus", out.stderr)
        self.assertEqual(
            self.state_path.read_text(), before, "a refused write changes nothing"
        )

    def test_ledger_add_appends_interval_and_commits(self):
        out = self.box.cli(
            "ledger-add",
            "plan",
            "spec-builder",
            "--started-at",
            "2026-10-22T14:00:00Z",
            "--ended-at",
            "2026-10-22T14:01:00Z",
            "--in-est",
            "100",
            "--out-est",
            "50",
            cwd=self.wt,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        entry = self.load()["ledger"][-1]
        self.assertEqual((entry["stage"], entry["role"]), ("plan", "spec-builder"))
        self.assertEqual(
            (entry["started_at"], entry["ended_at"]),
            ("2026-10-22T14:00:00Z", "2026-10-22T14:01:00Z"),
        )
        self.assertEqual(
            entry["duration_ms"], 60000, "duration derives from the interval"
        )
        self.assertEqual(
            (entry["in_est"], entry["out_est"], entry["reported"]), (100, 50, None)
        )
        self.assertTrue(self.recent(entry["at"]))
        self.assertTrue(self.committed_clean())

    def test_ledger_add_refuses_invalid_state(self):
        self.box.corrupt_worktree_state(
            "040-writer", lambda s: s.__setitem__("status", "finished")
        )
        before = self.state_path.read_text()
        out = self.box.cli("ledger-add", "plan", "spec-builder", cwd=self.wt)
        self.assertEqual(out.returncode, 1)
        self.assertEqual(self.state_path.read_text(), before)

    def test_wait_open_and_close(self):
        out = self.box.cli(
            "wait-open", "questions", "plan", "Round 1 (1 question)", cwd=self.wt
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        wait_id = json.loads(out.stdout)["wait-id"]
        entry = self.load()["timeline"][-1]
        self.assertEqual(
            (entry["kind"], entry["stage"], entry["summary"]),
            ("questions", "plan", "Round 1 (1 question)"),
        )
        self.assertIsNone(entry["answered_at"])
        self.assertTrue(self.recent(entry["at"]))
        out = self.box.cli("wait-close", str(wait_id), cwd=self.wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        closed = self.load()["timeline"][-1]
        self.assertIsNotNone(closed["answered_at"])
        self.assertGreaterEqual(closed["latency_ms"], 0)
        self.assertEqual(self.box.cli("wait-close", "99", cwd=self.wt).returncode, 1)

    def test_answer_writes_into_open_round(self):
        self.box.corrupt_worktree_state(
            "040-writer",
            lambda s: s["relay"]["rounds"][0]["questions"].append(
                {"id": "Q6", "text": "More"}
            ),
        )
        out = self.box.cli("answer", "Q6", "custom answer", cwd=self.wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        answer = self.load()["relay"]["rounds"][0]["answers"]["Q6"]
        self.assertEqual(answer["answer"], "custom answer")
        self.assertFalse(answer["auto"])
        self.assertTrue(self.recent(answer["at"]))
        out = self.box.cli("answer", "Q7", "fast!", "--auto", cwd=self.wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertTrue(self.load()["relay"]["rounds"][0]["answers"]["Q7"]["auto"])

    def test_set_status_records_history_and_end(self):
        out = self.box.cli(
            "set-status", "pr-open", "--pr-url", "https://x/pr/9", cwd=self.wt
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        after = self.load()
        self.assertEqual(after["status"], "pr-open")
        self.assertEqual(after["pr_url"], "https://x/pr/9")
        self.assertIsNotNone(after["ended_at"])
        self.assertEqual(
            (after["history"][-1]["event"], after["history"][-1]["stage"]),
            ("pr-open", "pr"),
        )
        self.assertTrue(self.committed_clean())

    def test_set_status_aborted_appends_its_history_entry(self):
        out = self.box.cli("set-status", "aborted", cwd=self.wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        after = self.load()
        self.assertEqual(after["status"], "aborted")
        self.assertIsNotNone(after["ended_at"])
        self.assertEqual(
            (after["history"][-1]["event"], after["history"][-1]["stage"]),
            ("aborted", "plan"),
        )

    def test_set_status_halted_carries_reason_without_history(self):
        out = self.box.cli(
            "set-status", "halted", "--halt-reason", "red build", cwd=self.wt
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        after = self.load()
        self.assertEqual(
            (after["status"], after["halt_reason"]), ("halted", "red build")
        )
        self.assertIsNone(after["ended_at"])
        self.assertEqual(
            after["history"][-1]["event"], "complete", "halt writes no history event"
        )

    def test_decisions_add_appends_record(self):
        out = self.box.cli(
            "decisions-add",
            "approver",
            "Q1",
            "Approve",
            "--kind",
            "approved",
            cwd=self.wt,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        entry = self.load()["decisions"][-1]
        self.assertEqual(
            (entry["stage"], entry["question"], entry["answer"], entry["kind"]),
            ("approver", "Q1", "Approve", "approved"),
        )
        self.assertIs(entry["auto"], False, "gate decisions are never auto")
        self.assertTrue(self.recent(entry["at"]))
        out = self.box.cli("decisions-add", "plan", "Q5", "B", cwd=self.wt)
        self.assertEqual(
            self.load()["decisions"][-1]["kind"], "answer", "default kind is answer"
        )

    def test_writers_refuse_without_a_single_target(self):
        out = self.box.cli(
            "checkpoint", "plan"
        )  # cwd is the repo root, not the worktree
        self.assertEqual(out.returncode, 1)
        self.assertIn("no run", out.stderr)
        self.box.pending_run("050-a", writer_state())
        self.box.pending_run("051-b", writer_state())
        out = self.box.cli("checkpoint", "plan")
        self.assertEqual(
            out.returncode, 3, "two pending runs of this repo are ambiguous"
        )

    def test_checkpoint_on_pending_run_writes_without_commit(self):
        self.box.pending_run("052-pend", writer_state())
        out = self.box.cli("checkpoint", "plan")
        self.assertEqual(out.returncode, 0, out.stderr)
        path = self.box.home / "pending" / "repo-052-pend.json"
        after = json.loads(path.read_text())
        self.assertEqual((after["stage"], after["version"]), ("tasks", 5))


class CheckpointStagingTests(unittest.TestCase):
    """Declared-file checkpoints (SC-008, FR-017): the spec directory plus
    exactly the declared list is committed; everything else is reported."""

    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.branch = "080-stage"
        self.wt = self.box.worktree_run(self.branch, writer_state())
        self.state_path = self.wt / "specs" / self.branch / "factory" / "state.json"

    def dirty(self):
        out = self.box.git("status", "--porcelain", cwd=self.wt)
        return sorted(line[3:].strip() for line in out.splitlines() if line.strip())

    def committed(self):
        out = self.box.git("show", "--name-only", "--format=", "HEAD", cwd=self.wt)
        return sorted(line for line in out.splitlines() if line.strip())

    def test_checkpoint_commits_only_spec_dir_plus_declared(self):
        (self.wt / "core").mkdir()
        (self.wt / "core" / "declared.txt").write_text("declared change\n")
        (self.wt / "scratch.txt").write_text("undeclared\n")
        out = self.box.cli(
            "checkpoint", "plan", "--files", "core/declared.txt", cwd=self.wt
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        report = json.loads(out.stdout)
        self.assertEqual(
            report["undeclared"],
            ["scratch.txt"],
            "every other dirty path is reported, not committed",
        )
        self.assertEqual(
            self.committed(),
            ["core/declared.txt", f"specs/{self.branch}/factory/state.json"],
        )
        self.assertEqual(self.dirty(), ["scratch.txt"])

    def test_checkpoint_envelope_reads_the_declared_list(self):
        envelope = {
            "status": "done",
            "stage": "plan",
            "summary": "s",
            "files": ["docs/changed.md"],
        }
        (self.wt / "docs").mkdir()
        (self.wt / "docs" / "changed.md").write_text("x\n")
        (self.wt / "envelope.md").write_text(
            "prose\n```json\n" + json.dumps(envelope) + "\n```\n"
        )
        out = self.box.cli(
            "checkpoint", "plan", "--envelope", "envelope.md", cwd=self.wt
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("docs/changed.md", json.loads(out.stdout)["declared"])
        self.assertEqual(
            self.committed(),
            ["docs/changed.md", f"specs/{self.branch}/factory/state.json"],
        )
        self.assertNotIn("envelope.md", self.committed())

    def test_checkpoint_refuses_an_envelope_without_files(self):
        (self.wt / "envelope.md").write_text('```json\n{"status": "done"}\n```')
        out = self.box.cli(
            "checkpoint", "plan", "--envelope", "envelope.md", cwd=self.wt
        )
        self.assertEqual(out.returncode, 1)
        self.assertIn("files", out.stderr)

    def test_checkpoint_refuses_a_declared_path_that_does_not_exist(self):
        before = self.state_path.read_text()
        out = self.box.cli(
            "checkpoint", "plan", "--files", "nope/missing.txt", cwd=self.wt
        )
        self.assertEqual(out.returncode, 1)
        self.assertIn("missing.txt", out.stderr)
        self.assertEqual(
            self.state_path.read_text(),
            before,
            "a refused checkpoint leaves the state untouched",
        )

    def test_checkpoint_envelope_accepts_bare_json(self):
        envelope = {
            "status": "done",
            "stage": "plan",
            "summary": "s",
            "files": ["docs/bare.md"],
        }
        (self.wt / "docs").mkdir()
        (self.wt / "docs" / "bare.md").write_text("x\n")
        path = self.box.write_temp("envelope.json", json.dumps(envelope))
        out = self.box.cli("checkpoint", "plan", "--envelope", path, cwd=self.wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("docs/bare.md", json.loads(out.stdout)["declared"])


class ReviewCounterTests(unittest.TestCase):
    def test_design_reservation_set_and_cleared_by_checkpoints(self):
        box = Sandbox()
        self.addCleanup(box.close)
        run = v4_state(stage="review")
        wt = box.worktree_run("076-design", run)
        root = wt / "specs/076-design/factory"
        verdict = "specs/076-design/factory/reviews/round-1/verdict.json"
        (wt / verdict).parent.mkdir(parents=True)
        (wt / verdict).write_text("{}")
        review = box.cli(
            "checkpoint", "review", "--next", "fix", "--design-fix", verdict, cwd=wt
        )
        self.assertEqual(review.returncode, 0, review.stderr)
        saved = json.loads((root / "state.json").read_text())
        self.assertEqual(saved["stage"], "fix")
        self.assertEqual(saved["review"]["fix_rounds"], 0)
        self.assertEqual(
            saved["review"]["pending_design_fix"],
            {
                "attempt": 1,
                "round": 1,
                "verdict": verdict,
            },
        )
        fix = box.cli("checkpoint", "fix", "--next", "review", cwd=wt)
        self.assertEqual(fix.returncode, 0, fix.stderr)
        saved = json.loads((root / "state.json").read_text())
        self.assertEqual(saved["review"]["fix_rounds"], 1)
        self.assertNotIn("pending_design_fix", saved["review"])
        self.assertEqual(saved["stage"], "review")

    def test_legacy_design_resume_checkpoint_clears_without_recount(self):
        box = Sandbox()
        self.addCleanup(box.close)
        run = v4_state(stage="fix")
        run["review"].update(
            {
                "fix_rounds": 1,
                "pending_design_fix": {
                    "attempt": 1,
                    "round": 1,
                    "verdict": "verdict.json",
                },
            }
        )
        wt = box.worktree_run("077-legacy", run)
        out = box.cli("checkpoint", "fix", "--next", "review", cwd=wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        saved = json.loads((wt / "specs/077-legacy/factory/state.json").read_text())
        self.assertEqual(saved["review"]["fix_rounds"], 1)
        self.assertNotIn("pending_design_fix", saved["review"])
        self.assertEqual(saved["stage"], "review")

    def test_fix_counts_once_and_respects_legacy_reservation(self):
        for reservation, expected in ((None, 1), ({"attempt": 0}, 0)):
            with self.subTest(reservation=reservation):
                box = Sandbox()
                self.addCleanup(box.close)
                run = v4_state(stage="fix")
                run["review"]["fix_rounds"] = 0
                if reservation:
                    run["review"]["pending_design_fix"] = reservation
                wt = box.worktree_run("072-fix", run)
                gitdir = box.repo / ".git/worktrees/wt-072-fix"
                (gitdir / "index.lock").write_text("")
                first = box.cli("checkpoint", "fix", "--next", "review", cwd=wt)
                self.assertEqual(first.returncode, 1, first.stderr)
                self.assertEqual(
                    json.loads(first.stdout)["review"]["fix_rounds"], expected
                )
                (gitdir / "index.lock").unlink()
                second = box.cli("checkpoint", "fix", "--next", "review", cwd=wt)
                self.assertEqual(second.returncode, 0, second.stderr)
                self.assertEqual(
                    json.loads(second.stdout)["review"]["fix_rounds"], expected
                )
                third = box.cli("checkpoint", "fix", "--next", "review", cwd=wt)
                self.assertEqual(third.returncode, 0, third.stderr)
                self.assertEqual(
                    json.loads(third.stdout)["review"]["fix_rounds"], expected
                )

    def test_two_review_and_fix_rounds(self):
        box = Sandbox()
        self.addCleanup(box.close)
        run = v4_state(stage="review")
        run["review"]["round"] = 0
        wt = box.worktree_run("073-rounds", run)
        root = wt / "specs/073-rounds/factory/reviews"
        for n in (1, 2):
            verdict = root / f"round-{n}" / "verdict.json"
            verdict.parent.mkdir(parents=True)
            verdict.write_text("{}")
            review = box.cli("checkpoint", "review", "--next", "fix", cwd=wt)
            self.assertEqual(review.returncode, 0, review.stderr)
            fix = box.cli("checkpoint", "fix", "--next", "review", cwd=wt)
            self.assertEqual(fix.returncode, 0, fix.stderr)
            self.assertEqual(
                json.loads(fix.stdout)["review"], {"round": n, "fix_rounds": n}
            )

    def test_review_round_uses_highest_verdict_without_decreasing(self):
        for current, folders, expected in (
            (0, ("1", "2", "x"), 2),
            (3, ("2",), 3),
            (2, (), 2),
        ):
            with self.subTest(current=current, folders=folders):
                box = Sandbox()
                self.addCleanup(box.close)
                run = v4_state(stage="review")
                run["review"]["round"] = current
                wt = box.worktree_run("071-review", run)
                root = wt / "specs/071-review/factory"
                for suffix in folders:
                    verdict = root / "reviews" / f"round-{suffix}" / "verdict.json"
                    verdict.parent.mkdir(parents=True)
                    verdict.write_text("{}")
                out = box.cli("checkpoint", "review", "--next", "fix", cwd=wt)
                self.assertEqual(out.returncode, 0, out.stderr)
                self.assertEqual(
                    json.loads(out.stdout)["review"],
                    {"round": expected, "fix_rounds": 0},
                )
                self.assertEqual(
                    json.loads((root / "state.json").read_text())["review"]["round"],
                    expected,
                )


class RelayRecordTests(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        run = v4_state(stage="review")
        run["relay"] = {
            "stage": "review",
            "rounds": [{"questions": [{"id": "R2-Q1"}], "answers": {}}],
        }
        self.wt = self.box.worktree_run("074-relay", run)
        self.root = self.wt / "specs/074-relay/factory"
        self.path = self.root / "state.json"

    def test_failed_answer_commit_is_completed_by_identical_retry(self):
        question = json.dumps({"id": "R2-Q1", "requires_user": True})
        gitdir = self.box.repo / ".git/worktrees/wt-074-relay"
        lock = gitdir / "index.lock"
        lock.write_text("")
        first = self.box.cli(
            "answer", "R2-Q1", "A", "--question", question, cwd=self.wt
        )
        self.assertNotEqual(first.returncode, 0)
        record = "specs/074-relay/factory/relay/review-R2-Q1.md"
        self.assertTrue((self.wt / record).exists())
        self.assertEqual(
            json.loads(self.path.read_text())["relay"]["rounds"][-1]["answers"][
                "R2-Q1"
            ]["answer"],
            "A",
        )
        lock.unlink()
        retry = self.box.cli(
            "answer", "R2-Q1", "A", "--question", question, cwd=self.wt
        )
        self.assertEqual(retry.returncode, 0, retry.stderr)
        committed = self.box.git(
            "show", "--format=", "--name-only", "HEAD", cwd=self.wt
        )
        self.assertIn(record, committed)
        self.assertIn("specs/074-relay/factory/state.json", committed)
        self.assertEqual(self.box.git("status", "--porcelain", cwd=self.wt), "")

    def test_question_replaces_stub_and_appends_missing(self):
        for qid in ("R2-Q1", "R2-Q2"):
            question = {"id": qid, "title": "Choose", "text": "Context"}
            out = self.box.cli(
                "answer", qid, "A", "--question", json.dumps(question), cwd=self.wt
            )
            self.assertEqual(out.returncode, 0, out.stderr)
            round_ = json.loads(self.path.read_text())["relay"]["rounds"][-1]
            self.assertIn(question, round_["questions"])
            self.assertEqual(round_["answers"][qid]["answer"], "A")
        changed = {"id": "R2-Q1", "title": "Replacement"}
        out = self.box.cli(
            "answer", "R2-Q1", "B", "--question", json.dumps(changed), cwd=self.wt
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn(
            {"id": "R2-Q1", "title": "Choose", "text": "Context"},
            json.loads(self.path.read_text())["relay"]["rounds"][-1]["questions"],
        )

    def test_invalid_question_and_unsafe_record_paths_refused_before_write(self):
        cases = [
            ("Q1", "{", ()),
            ("Q1", '{"id":"Q9"}', ()),
            ("../x", '{"id":"../x","requires_user":true}', ()),
            ("Q1", '{"id":"Q1","requires_user":true}', ("--stage", "a/b")),
        ]
        for qid, question, flags in cases:
            with self.subTest(qid=qid, question=question, flags=flags):
                before = self.path.read_bytes()
                head = self.box.git("rev-parse", "HEAD", cwd=self.wt)
                out = self.box.cli(
                    "answer", qid, "A", "--question", question, *flags, cwd=self.wt
                )
                self.assertEqual(out.returncode, 1, out.stderr)
                self.assertEqual(self.path.read_bytes(), before)
                self.assertEqual(self.box.git("rev-parse", "HEAD", cwd=self.wt), head)
                self.assertFalse((self.root / "relay").exists())
        out = self.box.cli(
            "answer", "../x", "A", "--question", '{"id":"../x"}', cwd=self.wt
        )
        self.assertEqual(out.returncode, 0, out.stderr)

    def test_unsafe_stage_without_protected_question_stores_answer(self):
        out = self.box.cli(
            "answer",
            "Q1",
            "A",
            "--stage",
            "a/b",
            "--question",
            '{"id":"Q1"}',
            cwd=self.wt,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        relay = json.loads(self.path.read_text())["relay"]
        self.assertEqual(relay["stage"], "a/b")
        self.assertEqual(relay["rounds"][-1]["answers"]["Q1"]["answer"], "A")
        self.assertFalse((self.root / "relay").exists())

    def test_plan_protected_answer_with_full_question_creates_record(self):
        question = {"id": "Q1", "title": "Confirm test scope", "requires_user": True}
        out = self.box.cli(
            "answer",
            "Q1",
            "A",
            "--stage",
            "plan",
            "--question",
            json.dumps(question),
            cwd=self.wt,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        name = "specs/074-relay/factory/relay/plan-Q1.md"
        self.assertEqual(json.loads(out.stdout)["record"], name)
        self.assertIn("Confirm test scope", (self.wt / name).read_text())
        self.assertEqual(
            json.loads(self.path.read_text())["relay"]["rounds"][-1]["answers"]["Q1"][
                "answer"
            ],
            "A",
        )

    def test_protected_answer_record_is_immutable_and_committed(self):
        question = {
            "id": "R2-Q1",
            "requires_user": True,
            "title": "Choose",
            "text": "Context",
            "options": [
                {"id": "A", "label": "Allow", "description": "Proceed"},
                {"id": "B", "label": "Block", "description": "Stop"},
            ],
        }
        out = self.box.cli(
            "answer", "R2-Q1", "A", "--question", json.dumps(question), cwd=self.wt
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        name = "specs/074-relay/factory/relay/review-R2-Q1.md"
        self.assertEqual(json.loads(out.stdout)["record"], name)
        record = self.wt / name
        text = record.read_text()
        for item in (
            "review",
            "R2-Q1",
            "Choose",
            "Context",
            "Allow",
            "Proceed",
            "Block",
            "Stop",
            "- Answer: A",
            "- Origin: explicit",
            "- Answered at:",
        ):
            self.assertIn(item, text)
        committed = self.box.git(
            "show", "--format=", "--name-only", "HEAD", cwd=self.wt
        )
        self.assertIn(name, committed)
        self.assertIn("specs/074-relay/factory/state.json", committed)
        before, head = (
            self.path.read_bytes(),
            self.box.git("rev-parse", "HEAD", cwd=self.wt),
        )
        again = self.box.cli(
            "answer", "R2-Q1", "A", "--question", json.dumps(question), cwd=self.wt
        )
        self.assertEqual(
            json.loads(again.stdout), {"answered": "R2-Q1", "unchanged": True}
        )
        refused = self.box.cli(
            "answer", "R2-Q1", "B", "--question", json.dumps(question), cwd=self.wt
        )
        self.assertEqual(refused.returncode, 1)
        self.assertIn(name, refused.stderr)
        self.assertEqual(record.read_text(), text)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.box.git("rev-parse", "HEAD", cwd=self.wt), head)

    def test_multiline_protected_answer_is_compared_exactly(self):
        question = json.dumps({"id": "R2-Q1", "requires_user": True})
        answer = 'A\n- Origin: explicit\n- Answer JSON: "B"\nrest'
        first = self.box.cli(
            "answer", "R2-Q1", answer, "--question", question, cwd=self.wt
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        record = self.wt / json.loads(first.stdout)["record"]
        before, state, head = (
            record.read_bytes(),
            self.path.read_bytes(),
            self.box.git("rev-parse", "HEAD", cwd=self.wt),
        )
        same = self.box.cli("answer", "R2-Q1", answer, cwd=self.wt)
        self.assertEqual(same.returncode, 0, same.stderr)
        self.assertEqual(
            json.loads(same.stdout), {"answered": "R2-Q1", "unchanged": True}
        )
        different = self.box.cli("answer", "R2-Q1", "A", cwd=self.wt)
        self.assertEqual(different.returncode, 1, different.stderr)
        self.assertIn(str(record.relative_to(self.wt)), different.stderr)
        self.assertEqual(record.read_bytes(), before)
        self.assertEqual(self.path.read_bytes(), state)
        self.assertEqual(self.box.git("rev-parse", "HEAD", cwd=self.wt), head)

    def test_legacy_records_are_not_guessed_when_ambiguous(self):
        question = json.dumps({"id": "R2-Q1", "requires_user": True})
        first = self.box.cli(
            "answer", "R2-Q1", "A", "--question", question, cwd=self.wt
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        record = self.wt / json.loads(first.stdout)["record"]
        legacy = record.read_text().replace('- Answer JSON: "A"\n', "")
        record.write_text(legacy)
        self.box.git("add", "--", str(record.relative_to(self.wt)), cwd=self.wt)
        self.box.git("commit", "-m", "record legacy answer", cwd=self.wt)
        same = self.box.cli("answer", "R2-Q1", "A", cwd=self.wt)
        self.assertEqual(same.returncode, 0, same.stderr)
        self.assertTrue(json.loads(same.stdout)["unchanged"])
        ambiguous = legacy.replace("- Answer: A\n", "- Answer: A\n- Origin: spoof\n")
        record.write_text(ambiguous)
        refused = self.box.cli("answer", "R2-Q1", "A", cwd=self.wt)
        self.assertEqual(refused.returncode, 1, refused.stderr)
        self.assertIn("ambiguous legacy answer", refused.stderr)
        self.assertEqual(record.read_text(), ambiguous)

    def test_record_origins_and_pending_run(self):
        self.box.corrupt_worktree_state(
            "074-relay", lambda s: s["mode"].__setitem__("cruise", True)
        )
        for qid, flags, origin in (
            ("R2-Q2", ("--auto",), "auto"),
            ("R2-Q3", ("--cruise-override",), "cruise_override"),
        ):
            q = json.dumps({"id": qid, "requires_user": True})
            out = self.box.cli("answer", qid, "A", "--question", q, *flags, cwd=self.wt)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn(
                f"- Origin: {origin}",
                (self.wt / json.loads(out.stdout)["record"]).read_text(),
            )
        box = Sandbox()
        self.addCleanup(box.close)
        run = v4_state(stage="review", worktree=None)
        pending = box.pending_run("075-pending", run)
        out = box.cli(
            "answer",
            "Q1",
            "A",
            "--question",
            '{"id":"Q1","requires_user":true}',
            cwd=box.repo,
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn("record", json.loads(out.stdout))
        self.assertEqual(
            json.loads(pending.read_text())["relay"]["rounds"][-1]["answers"]["Q1"][
                "answer"
            ],
            "A",
        )
        self.assertFalse((box.repo / "specs/075-pending/factory/relay").exists())


class CheckpointCommitFailureTests(unittest.TestCase):
    """FR-011: a checkpoint whose git commit fails after the state write
    exits 1 with 'state written, commit failed: <reason>', its JSON carrying
    commit: null and commit_error; a retry of the same stage reuses the
    pending history entry instead of appending a second one."""

    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.branch = "070-ckpt"
        self.wt = self.box.worktree_run(self.branch, v4_state())
        self.state_path = self.wt / "specs" / self.branch / "factory" / "state.json"
        self.gitdir = self.box.repo / ".git" / "worktrees" / f"wt-{self.branch}"

    def block_git(self):
        (self.gitdir / "index.lock").write_text("")

    def unblock_git(self):
        (self.gitdir / "index.lock").unlink()

    def history(self):
        return json.loads(self.state_path.read_text())["history"]

    def test_failed_commit_is_reported_without_a_traceback(self):
        self.block_git()
        out = self.box.cli("checkpoint", "plan", cwd=self.wt)
        message = out.stderr + out.stdout
        self.assertEqual(out.returncode, 1, message)
        self.assertIn("state written, commit failed", message)
        self.assertNotIn("Traceback", message, "no traceback at the user")
        result = json.loads(out.stdout)
        self.assertIsNone(result["commit"], "the failed commit is named null")
        self.assertIn("commit_error", result)
        self.assertEqual(self.history()[-1]["stage"], "plan", "the state was written")

    def test_retry_reuses_the_pending_history_entry(self):
        self.block_git()
        first = self.box.cli("checkpoint", "plan", cwd=self.wt)
        self.assertEqual(first.returncode, 1, first.stderr + first.stdout)
        self.unblock_git()
        second = self.box.cli("checkpoint", "plan", cwd=self.wt)
        self.assertEqual(second.returncode, 0, second.stderr + second.stdout)
        entries = [e for e in self.history() if e["stage"] == "plan"]
        self.assertEqual(len(entries), 1, "the retry does not duplicate history")
        self.assertIsNotNone(
            entries[-1]["commit"], "the reused entry carries the retry's commit"
        )


class RebindTests(unittest.TestCase):
    """rebind <run> --worktree <path>: validate branch, rewrite stored paths (FR-012)."""

    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.branch = "090-move"
        self.wt_old = self.box.worktree_run(self.branch, fixture("state-v4.json"))

    def moved_worktree(self):
        """Move the worktree directory and let git repair its bookkeeping."""
        wt_new = self.box.dir / "wt-moved"
        shutil.move(str(self.wt_old), str(wt_new))
        self.box.git("worktree", "repair", str(wt_new))
        return wt_new

    def state_path(self, wt):
        return wt / "specs" / self.branch / "factory" / "state.json"

    def test_rebind_rewrites_worktree_and_reports(self):
        wt_new = self.moved_worktree()
        out = self.box.cli(
            "rebind", self.branch, "--worktree", str(wt_new), cwd=self.box.repo
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        report = json.loads(out.stdout)
        self.assertEqual(Path(report["worktree"]).resolve(), wt_new.resolve())
        state = json.loads(self.state_path(wt_new).read_text())
        self.assertEqual(
            Path(state["worktree"]).resolve(),
            wt_new.resolve(),
            "the recorded home is rewritten",
        )
        self.assertEqual(Path(state["repo"]).resolve(), self.box.repo.resolve())

    def test_rebind_refuses_an_ended_run_and_leaves_its_state_unchanged(self):
        # FR-009: an ended run's stored paths are never rewritten
        for status in ("pr-open", "aborted"):
            with self.subTest(status=status):
                branch = f"091-{status}"
                wt = self.box.worktree_run(
                    branch,
                    v4_state(
                        branch=branch, status=status, ended_at="2026-10-23T12:00:00Z"
                    ),
                )
                path = wt / "specs" / branch / "factory" / "state.json"
                before = path.read_text()
                out = self.box.cli(
                    "rebind", branch, "--worktree", str(wt), cwd=self.box.repo
                )
                self.assertEqual(out.returncode, 1, out.stderr + out.stdout)
                self.assertIn(status, out.stderr, "the refusal names the status")
                self.assertEqual(path.read_text(), before, "the state is unchanged")

    def test_rebind_refuses_a_missing_worktree_with_exit_four(self):
        out = self.box.cli(
            "rebind",
            self.branch,
            "--worktree",
            str(self.box.dir / "gone"),
            cwd=self.box.repo,
        )
        self.assertEqual(out.returncode, 4)
        self.assertIn("gone", out.stderr)

    def test_rebind_refuses_a_target_on_another_branch(self):
        other = self.box.dir / "wt-other"
        self.box.git("worktree", "add", "-q", "-b", "099-other", str(other))
        out = self.box.cli(
            "rebind", self.branch, "--worktree", str(other), cwd=self.box.repo
        )
        self.assertEqual(out.returncode, 1)
        self.assertIn(self.branch, out.stderr, "the refusal names the recorded branch")

    def test_rebind_refuses_an_ambiguous_run_with_exit_three(self):
        wt_new = self.moved_worktree()
        self.box.pending_run(self.branch, fixture("state-v1.json"))
        out = self.box.cli(
            "rebind", self.branch, "--worktree", str(wt_new), cwd=self.box.repo
        )
        self.assertEqual(out.returncode, 3)

    def test_rebind_under_a_live_lock_refuses_without_a_traceback(self):
        # FR-008: the rewrite goes through the single writer, so a competing
        # lock is refused by name instead of written over or crashing
        wt_new = self.moved_worktree()
        guard = self.state_path(wt_new).parent / "lock.json"
        guard.write_text(
            json.dumps(
                {
                    "owner_pid": os.getpid(),
                    "host": socket.gethostname(),
                    "harness": "opencode",
                    "at": "2026-10-23T12:00:00Z",
                }
            )
        )
        out = self.box.cli(
            "rebind", self.branch, "--worktree", str(wt_new), cwd=self.box.repo
        )
        message = out.stderr + out.stdout
        self.assertEqual(out.returncode, 1, message)
        self.assertIn("locked by", message, "the writer's refusal reports the owner")
        self.assertNotIn("Traceback", message, "no traceback at the user")


class PruneTests(unittest.TestCase):
    """prune previews stale pending files and deletes only with --delete (FR-019)."""

    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)

    def pending(self, name, state):
        return self.box.pending_run(name, state)

    def with_worktree_state(self, name, state):
        path = self.pending(name, state)
        wt = self.box.dir / f"moved-{name}"
        folder = wt / "specs" / name / "factory"
        folder.mkdir(parents=True)
        (folder / "state.json").write_text(json.dumps(dict(state, worktree=str(wt))))
        return path

    def test_stale_when_the_run_has_a_worktree_state(self):
        path = self.with_worktree_state("110-a", fixture("state-v4.json"))
        out = self.box.cli("prune", "--dry-run")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn(str(path), out.stdout)
        self.assertTrue(path.exists(), "a dry run deletes nothing")

    def test_stale_when_the_pending_run_ended(self):
        pr = self.pending("111-b", fixture("state-v4.json"))
        aborted = self.pending("112-b2", fixture("state-v1.json"))
        s = json.loads(aborted.read_text())
        s["status"] = "aborted"
        s["ended_at"] = "2026-10-24T00:00:00Z"
        aborted.write_text(json.dumps(s))
        pr_state = json.loads(pr.read_text())
        pr_state["status"] = "pr-open"
        pr_state["ended_at"] = "2026-10-24T00:00:00Z"
        pr.write_text(json.dumps(pr_state))
        out = self.box.cli("prune", "--dry-run")
        self.assertIn(str(pr), out.stdout)
        self.assertIn(str(aborted), out.stdout)

    def test_a_run_whose_only_state_is_the_pending_file_is_never_stale(self):
        path = self.pending("113-c", fixture("state-v1.json"))
        out = self.box.cli("prune", "--dry-run")
        self.assertNotIn(str(path), out.stdout)
        out = self.box.cli("prune", "--delete")
        self.assertTrue(path.exists(), "--delete never removes a run's only state")

    def test_delete_is_the_only_deleting_form(self):
        stale = self.with_worktree_state("114-d", fixture("state-v4.json"))
        keep = self.pending("115-e", fixture("state-v1.json"))
        for args in ((), ("--dry-run",)):
            out = self.box.cli("prune", *args)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertTrue(stale.exists(), f"prune {args} deletes nothing")
            self.assertIn(
                str(stale), out.stdout, f"prune {args} still lists the candidate"
            )
        out = self.box.cli("prune", "--delete")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertFalse(stale.exists(), "--delete removes the stale pending file")
        self.assertTrue(keep.exists())


if __name__ == "__main__":
    unittest.main()
