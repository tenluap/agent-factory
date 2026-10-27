"""Run-end backlog export seam tests (FR-011).

`factory set-status pr-open|aborted` exports
`${FACTORY_HOME}/improvements/<repo-name>-<branch>.json` atomically; the file
never exists before its run ends, and a zero-issue run exports too.
"""

import json
import re
import sys
import unittest
from pathlib import Path

CORE_BIN = Path(__file__).resolve().parents[2] / "core" / "skills" / "factory" / "bin"
sys.path.insert(0, str(CORE_BIN))

from factory_cli import totals  # noqa: E402

from tests import Sandbox, fixture  # noqa: E402


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.branch = "050-backlogs"
        self.wt = self.box.worktree_run(self.branch, fixture("state-v5.json"))
        self.state_path = self.wt / "specs" / self.branch / "factory" / "state.json"
        self.improvements = self.box.home / "improvements"
        self.backlog = self.improvements / f"{self.box.repo.name}-{self.branch}.json"

    def set_status(self, *args):
        return self.box.cli("set-status", *args, cwd=self.wt)

    def test_no_file_before_run_end(self):
        self.assertFalse(
            self.backlog.exists(), "no backlog file exists before its run ends"
        )

    def test_pr_open_exports_ready_backlog(self):
        out = self.set_status("pr-open", "--pr-url", "https://x/pr/1")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertTrue(self.backlog.exists(), "the export appears at run end")
        body = json.loads(self.backlog.read_text())
        self.assertEqual(body["name"], f"{self.box.repo.name}-{self.branch}")
        self.assertEqual(
            body["run"],
            {
                "branch": self.branch,
                "spec_dir": f"specs/{self.branch}",
                "worktree": str(self.wt),
                "status": "pr-open",
                "ended_at": json.loads(self.state_path.read_text())["ended_at"],
            },
        )
        state = json.loads(self.state_path.read_text())
        self.assertEqual(body["issues"], state["issues"], "issues[] verbatim")
        self.assertEqual(body["totals"], totals.compute(state))
        self.assertEqual(body["status"], "ready")
        self.assertIsNone(body["claimed_at"])
        self.assertRegex(body["exported_at"], r"^\d{4}-\d{2}-\d{2}T")
        sha = body["factory_sha"]
        self.assertTrue(
            sha is None or re.fullmatch(r"[0-9a-f]{7,40}", sha),
            f"factory_sha is best-effort, got {sha!r}",
        )

    def test_aborted_exports_too(self):
        out = self.set_status("aborted")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertTrue(self.backlog.exists())
        body = json.loads(self.backlog.read_text())
        self.assertEqual(body["run"]["status"], "aborted")
        self.assertEqual(body["status"], "ready")

    def test_zero_issue_run_exports_too(self):
        wt = self.box.worktree_run("051-empty", fixture("state-v4.json"))
        out = self.box.cli("set-status", "aborted", cwd=wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        empty = self.improvements / f"{self.box.repo.name}-051-empty.json"
        self.assertTrue(empty.exists(), "a zero-issue run exports too")
        self.assertEqual(json.loads(empty.read_text())["issues"], [])

    def test_export_is_atomic_no_debris(self):
        out = self.set_status("aborted")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(
            [p.name for p in self.improvements.iterdir()],
            [self.backlog.name],
            "the export leaves no temp files behind",
        )


class SurfaceTests(unittest.TestCase):
    """`factory improvements` listing and `claim` (FR-012, FR-013)."""

    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.branch = "050-backlogs"
        self.wt = self.box.worktree_run(self.branch, fixture("state-v5.json"))
        out = self.box.cli("set-status", "aborted", cwd=self.wt)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.name = f"{self.box.repo.name}-{self.branch}"
        self.backlog = self.box.home / "improvements" / f"{self.name}.json"

    def test_lists_kind_counts_and_suggested_feature(self):
        out = self.box.cli("improvements")
        self.assertEqual(out.returncode, 0, out.stderr)
        entries = json.loads(out.stdout)["improvements"]
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["name"], self.name)
        self.assertEqual(entry["run"], self.branch)
        self.assertEqual(entry["status"], "ready")
        self.assertEqual(
            entry["issues_by_kind"],
            {"overrun": 1, "retry": 1, "verify-fail": 1},
        )
        self.assertIn(self.branch, entry["suggested_feature"])
        self.assertIn("overrun", entry["suggested_feature"])

    def test_claim_stamps_claimed_once(self):
        out = self.box.cli("improvements", "claim", self.name)
        self.assertEqual(out.returncode, 0, out.stderr)
        body = json.loads(out.stdout)
        self.assertEqual(body["claimed"], self.name)
        self.assertEqual(body["status"], "claimed")
        on_disk = json.loads(self.backlog.read_text())
        self.assertEqual(on_disk["status"], "claimed")
        self.assertEqual(on_disk["claimed_at"], body["claimed_at"])
        again = self.box.cli("improvements", "claim", self.name)
        self.assertEqual(again.returncode, 1, "a second claim is refused")

    def test_claim_refuses_unknown_name(self):
        out = self.box.cli("improvements", "claim", "repo-999-none")
        self.assertEqual(out.returncode, 1)
        self.assertIn("repo-999-none", out.stderr)

    def test_claim_refuses_a_source_run_that_has_not_ended(self):
        self.box.worktree_run("052-running", fixture("state-v4.json"))
        manual = (
            self.box.home / "improvements" / f"{self.box.repo.name}-052-running.json"
        )
        manual.write_text(
            json.dumps(
                {
                    "name": f"{self.box.repo.name}-052-running",
                    "run": {"branch": "052-running", "status": "running"},
                    "issues": [],
                    "status": "ready",
                    "exported_at": "2026-10-27T00:00:00Z",
                    "claimed_at": None,
                }
            )
        )
        out = self.box.cli("improvements", "claim", f"{self.box.repo.name}-052-running")
        self.assertEqual(out.returncode, 1)
        self.assertIn("052-running", out.stderr, "the refusal names the run")


if __name__ == "__main__":
    unittest.main()
