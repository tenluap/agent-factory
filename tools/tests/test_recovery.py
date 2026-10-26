"""Recovery seam tests: a run killed at each stage resumes through the CLI (SC-006).

No answered question is re-asked (answers live in `decisions`), no committed
task or stage is redone (history and checkboxes are the resume point), and no
duplicate branch, worktree or pull request appears.
"""

import json
import unittest

from tests import Sandbox, fixture


def started_state():
    s = fixture("state-v4.json")
    s.update(stage="grill", status="running")
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
    STAGES = [
        "grill",
        "specify",
        "plan",
        "tasks",
        "analyze",
        "implement",
        "review",
        "approver",
    ]

    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.branch = "100-recover"
        self.wt = self.box.worktree_run(self.branch, started_state())

    def build_to(self, stage):
        """Drive the run to `stage` through the CLI, committing at each step."""
        done = self.STAGES[: self.STAGES.index(stage) + 1]
        for done_stage in done:
            out = self.box.cli("checkpoint", done_stage, cwd=self.wt)
            self.assertEqual(out.returncode, 0, f"{done_stage}: {out.stderr}")
        return done

    def snapshot(self):
        return {
            "worktrees": len(
                self.box.git("worktree", "list", "--porcelain", cwd=self.box.repo)
                .strip()
                .split("\n\n")
            ),
            "branches": len(
                self.box.git("branch", "--list", cwd=self.box.repo).splitlines()
            ),
        }

    def load(self):
        return json.loads(
            (self.wt / "specs" / self.branch / "factory" / "state.json").read_text()
        )

    def test_killed_run_resumes_at_every_stage(self):
        for stage in self.STAGES:
            with self.subTest(stage=stage):
                box = Sandbox()
                self.addCleanup(box.close)
                wt = box.worktree_run(self.branch, started_state())
                done = self.STAGES[: self.STAGES.index(stage) + 1]
                for done_stage in done:
                    out = box.cli("checkpoint", done_stage, cwd=wt)
                    self.assertEqual(out.returncode, 0, out.stderr)
                before = {
                    "worktrees": len(
                        box.git("worktree", "list", "--porcelain").strip().split("\n\n")
                    ),
                    "branches": len(box.git("branch", "--list").splitlines()),
                    "history": len(
                        json.loads(
                            (
                                wt / "specs" / self.branch / "factory" / "state.json"
                            ).read_text()
                        )["history"]
                    ),
                    "decisions": len(
                        json.loads(
                            (
                                wt / "specs" / self.branch / "factory" / "state.json"
                            ).read_text()
                        )["decisions"]
                    ),
                }
                # the run is "killed" here: a fresh session resumes through the CLI
                out = box.cli("resume", self.branch)
                self.assertEqual(out.returncode, 0, out.stderr)
                digest = json.loads(out.stdout)
                self.assertEqual(
                    digest["stage"],
                    done[-1],
                    "the recorded stage is where resume restarts",
                )
                self.assertEqual(
                    digest["relay"]["unanswered"],
                    [],
                    "no answered question is re-asked",
                )
                state = json.loads(
                    (wt / "specs" / self.branch / "factory" / "state.json").read_text()
                )
                self.assertEqual(len(state["history"]), before["history"] + 1)
                self.assertEqual(state["history"][-1]["event"], "resumed")
                self.assertEqual(
                    len(state["decisions"]),
                    before["decisions"],
                    "resume adds no decision records",
                )
                self.assertEqual(
                    state["stage"], done[-1], "resume does not advance the stage"
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
                out = box.cli("checkpoint", stage, cwd=wt)
                self.assertEqual(out.returncode, 0, out.stderr)

    def test_resume_of_an_ended_run_is_refused(self):
        self.build_to("approver")
        out = self.box.cli(
            "set-status", "pr-open", "--pr-url", "https://x/pr/1", cwd=self.wt
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        out = self.box.cli("resume", self.branch)
        self.assertEqual(out.returncode, 1)
        self.assertIn("pr-open", out.stderr)

    def test_resumed_approval_records_one_pr_not_two(self):
        self.build_to("approver")
        self.box.cli("resume", self.branch)
        self.box.cli(
            "decisions-add",
            "approver",
            "Q1",
            "Approve",
            "--kind",
            "approved",
            cwd=self.wt,
        )
        self.box.cli("checkpoint", "approver", cwd=self.wt)
        out = self.box.cli(
            "set-status", "pr-open", "--pr-url", "https://x/pr/9", cwd=self.wt
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        events = [h["event"] for h in self.load()["history"]]
        self.assertEqual(events.count("pr-open"), 1, "no duplicate pull request record")
        self.assertEqual(events.count("resumed"), 1)


if __name__ == "__main__":
    unittest.main()
