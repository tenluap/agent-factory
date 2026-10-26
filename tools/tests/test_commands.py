"""CLI seam tests: the `bin/factory` command surface, driven as a process.

Covers `runs`, `show` and `validate` exit codes and digests (contracts/cli.md),
`show`'s approver veto list (SC-004), and the 005/006 replay (SC-002).
"""

import json
import unittest
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
        self.assertIn(
            {
                "stage": "plan",
                "question": "Q5",
                "answer": "B",
                "auto": True,
                "at": "2026-10-22T14:05:00Z",
                "kind": "answer",
            },
            after["decisions"],
            "settled relay answers move into decisions (FR-008)",
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
        self.assertEqual((after["stage"], after["version"]), ("tasks", 4))


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
        out = self.box.cli("checkpoint", "plan", "--files", "core/declared.txt", cwd=self.wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        report = json.loads(out.stdout)
        self.assertEqual(report["undeclared"], ["scratch.txt"],
                         "every other dirty path is reported, not committed")
        self.assertEqual(self.committed(),
                         ["core/declared.txt", f"specs/{self.branch}/factory/state.json"])
        self.assertEqual(self.dirty(), ["scratch.txt"])

    def test_checkpoint_envelope_reads_the_declared_list(self):
        envelope = {"status": "done", "stage": "plan", "summary": "s",
                    "files": ["docs/changed.md"]}
        (self.wt / "docs").mkdir()
        (self.wt / "docs" / "changed.md").write_text("x\n")
        (self.wt / "envelope.md").write_text("prose\n```json\n" + json.dumps(envelope) + "\n```\n")
        out = self.box.cli("checkpoint", "plan", "--envelope", "envelope.md", cwd=self.wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("docs/changed.md", json.loads(out.stdout)["declared"])
        self.assertEqual(self.committed(),
                         ["docs/changed.md", f"specs/{self.branch}/factory/state.json"])
        self.assertNotIn("envelope.md", self.committed())

    def test_checkpoint_refuses_an_envelope_without_files(self):
        (self.wt / "envelope.md").write_text("```json\n{\"status\": \"done\"}\n```")
        out = self.box.cli("checkpoint", "plan", "--envelope", "envelope.md", cwd=self.wt)
        self.assertEqual(out.returncode, 1)
        self.assertIn("files", out.stderr)

    def test_checkpoint_refuses_a_declared_path_that_does_not_exist(self):
        out = self.box.cli("checkpoint", "plan", "--files", "nope/missing.txt", cwd=self.wt)
        self.assertEqual(out.returncode, 1)
        self.assertIn("missing.txt", out.stderr)
