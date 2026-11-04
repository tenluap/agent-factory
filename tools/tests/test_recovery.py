"""Recovery seam tests: a run killed at each stage resumes through the CLI (SC-006).

No answered question is re-asked (answers live in `decisions`), no committed
task or stage is redone (history and checkboxes are the resume point), and no
duplicate branch, worktree or pull request appears.
"""

import json
import sys
import unittest
from pathlib import Path

CORE_BIN = Path(__file__).resolve().parents[2] / "core" / "skills" / "factory" / "bin"
sys.path.insert(0, str(CORE_BIN))

from factory_cli import state as state_mod  # noqa: E402
from tests import Sandbox, fixture  # noqa: E402

# the linear chain the suite drives; the flow's real successors (state.STAGES)
CHAIN = [s for s in state_mod.STAGES if s not in ("brainstorm", "pr", "retro")]


def started_state():
    s = fixture("state-v4.json")
    s.update(stage="grill", status="running")
    s["decisions"] = []  # the grill answer below is still in relay, not yet migrated
    s["history"] = [h for h in s["history"] if h["event"] == "complete"]
    s["relay"] = {
        "stage": "grill",
        "rounds": [
            {
                "questions": [{"id": "Q1", "text": "chain?", "recommended": "full"}],
                "answers": {
                    "Q1": {
                        "answer": "full",
                        "at": "2026-10-23T08:34:00Z",
                        "auto": False,
                    }
                },
            }
        ],
    }
    return s


class KillAndResumeTests(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.branch = "100-recover"
        self.wt = self.box.worktree_run(self.branch, started_state())

    def state(self, wt):
        return json.loads(
            (wt / "specs" / self.branch / "factory" / "state.json").read_text()
        )

    def build_to(self, box, wt, stage):
        """Drive the run to `stage` through the CLI, committing at each step,
        satisfying the gates the real flow satisfies on the way."""
        done = CHAIN[: CHAIN.index(stage) + 1]
        for done_stage in done:
            self.prepare(box, wt, done_stage)
            out = box.cli("checkpoint", done_stage, cwd=wt)
            self.assertEqual(out.returncode, 0, f"{done_stage}: {out.stderr}")
        return done

    def prepare(self, box, wt, stage):
        """The records the real flow produces before completing `stage`."""
        if stage == "analyze":  # a clean analysis result; its derived baseline passes the gate (ADR 0014)
            box.corrupt_worktree_state(
                self.branch,
                lambda s: s["analyze"].update(
                    result={
                        "critical": 0,
                        "high": 0,
                        "medium": 0,
                        "low": 0,
                        "report": "factory/analyze-1.md",
                        "at": "2026-10-23T09:00:00Z",
                    }
                ),
            )
        if stage == "verify":  # the verify pair precedes the ->review gate
            out = box.cli(
                "verify",
                "--pass",
                "--commands",
                '[{"command": "make test", "status": 0}]',
                cwd=wt,
            )
            self.assertEqual(out.returncode, 0, out.stderr)
        if stage == "approver":  # the approval precedes the ->pr gate
            out = box.cli(
                "decisions-add",
                "approver",
                "Q1",
                "Approve",
                "--kind",
                "approved",
                cwd=wt,
            )
            self.assertEqual(out.returncode, 0, out.stderr)

    def test_killed_run_resumes_at_every_stage(self):
        for stage in CHAIN:
            with self.subTest(stage=stage):
                box = Sandbox()
                self.addCleanup(box.close)
                wt = box.worktree_run(self.branch, started_state())
                done = self.build_to(box, wt, stage)
                before = {
                    "worktrees": len(
                        box.git("worktree", "list", "--porcelain").strip().split("\n\n")
                    ),
                    "branches": len(box.git("branch", "--list").splitlines()),
                    "history": len(self.state(wt)["history"]),
                    "decisions": len(self.state(wt)["decisions"]),
                    "stage": self.state(wt)["stage"],
                }
                # the run is "killed" here: a fresh session resumes through the CLI
                out = box.cli("resume", self.branch)
                self.assertEqual(out.returncode, 0, out.stderr)
                digest = json.loads(out.stdout)
                recorded = (
                    CHAIN[CHAIN.index(done[-1]) + 1] if done[-1] != CHAIN[-1] else "pr"
                )
                self.assertEqual(
                    digest["stage"],
                    recorded,
                    "the recorded stage is where resume restarts",
                )
                self.assertIsNone(
                    digest["relay"],
                    "the stage's answers moved to decisions; nothing to re-ask",
                )
                after = self.state(wt)
                self.assertEqual(len(after["history"]), before["history"] + 1)
                self.assertEqual(after["history"][-1]["event"], "resumed")
                self.assertEqual(
                    len(after["decisions"]),
                    before["decisions"],
                    "resume adds no decision records",
                )
                self.assertEqual(
                    after["stage"], before["stage"], "resume does not advance the stage"
                )
                migrated = [
                    d
                    for d in after["decisions"]
                    if d["question"] == "Q1" and d["kind"] == "answer"
                ]
                self.assertEqual(
                    len(migrated), 1, "the answered question is asked never again"
                )
                self.assertEqual(
                    len(
                        box.git("worktree", "list", "--porcelain").strip().split("\n\n")
                    ),
                    before["worktrees"],
                    "resume creates no worktree",
                )
                self.assertEqual(
                    len(box.git("branch", "--list").splitlines()),
                    before["branches"],
                    "resume creates no branch",
                )
                # and the run continues from there
                self.prepare(box, wt, recorded)
                out = box.cli("checkpoint", recorded, cwd=wt)
                self.assertEqual(out.returncode, 0, out.stderr)

    def test_resume_of_an_ended_run_is_refused(self):
        self.build_to(self.box, self.wt, "approver")
        out = self.box.cli(
            "set-status", "pr-open", "--pr-url", "https://x/pr/1", cwd=self.wt
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        out = self.box.cli("resume", self.branch)
        self.assertEqual(out.returncode, 1)
        self.assertIn("pr-open", out.stderr)

    def test_resumed_approval_records_one_pr_not_two(self):
        self.build_to(self.box, self.wt, "approver")
        self.box.cli("resume", self.branch)
        self.box.cli("checkpoint", "approver", cwd=self.wt)
        out = self.box.cli(
            "set-status", "pr-open", "--pr-url", "https://x/pr/9", cwd=self.wt
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        events = [h["event"] for h in self.state(self.wt)["history"]]
        self.assertEqual(events.count("pr-open"), 1, "no duplicate pull request record")
        self.assertEqual(events.count("resumed"), 1)


if __name__ == "__main__":
    unittest.main()
