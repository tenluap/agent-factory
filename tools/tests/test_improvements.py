"""Run-end backlog export seam tests (FR-011).

`factory set-status pr-open|aborted` exports
`${FACTORY_HOME}/improvements/<repo-name>-<branch>.json` atomically; the file
never exists before its run ends, and a zero-issue run exports too.
"""

import json
import re
import sys
import time
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
        self.assertIn("test-loop", entry["suggested_feature"])

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

    def test_claim_cannot_escape_improvements_directory(self):
        outside = self.box.home / "outside.json"
        original = json.dumps({"status": "ready", "run": {}})
        outside.write_text(original)
        out = self.box.cli("improvements", "claim", "../outside")
        self.assertEqual(out.returncode, 1, out.stderr)
        self.assertEqual(outside.read_text(), original)

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


class RetroAddTests(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.branch = "053-retro"
        self.wt = self.box.worktree_run(self.branch, fixture("state-v5.json"))
        self.candidate = {
            "signal_key": "halt-cluster:implement",
            "rank": 1,
            "evidence": "two halts",
            "suggested_feature": "Improve recovery",
        }
        self.source = self.box.write_temp(
            "retro.md",
            "earlier\n```json\n{}\n```\n```json\n"
            + json.dumps({"retro": {"candidates": [self.candidate]}})
            + "\n```\n",
        )
        self.directory = self.box.home / "improvements"
        self.name = f"{self.box.repo.name}-{self.branch}.retro.halt-cluster.implement"

    def invoke(self):
        return self.box.cli(
            "improvements",
            "add",
            "--from",
            self.source,
            "--run",
            self.branch,
            cwd=self.wt,
        )

    def test_add_writes_and_replaces_retro_entry(self):
        ended = self.box.cli(
            "set-status", "pr-open", "--pr-url", "https://x/pr/1", cwd=self.wt
        )
        self.assertEqual(ended.returncode, 0, ended.stderr)
        out = self.invoke()
        self.assertEqual(out.returncode, 0, out.stderr)
        result = json.loads(out.stdout)
        self.assertEqual(len(result["written"]), 1)
        self.assertEqual(result["skipped"], [])
        self.assertEqual(result["dropped"], [])
        path = self.directory / (self.name + ".json")
        body = json.loads(path.read_text())
        self.assertEqual(body["name"], self.name)
        self.assertEqual(body["kind"], "retro")
        self.assertEqual(
            body["run"],
            {
                "repo": str(self.box.repo),
                "branch": self.branch,
                "spec_dir": f"specs/{self.branch}",
            },
        )
        for key, value in self.candidate.items():
            self.assertEqual(body[key], value)
        self.assertEqual(body["status"], "ready")
        self.assertIsNone(body["claimed_at"])
        self.assertIn("factory_sha", body)
        self.assertRegex(body["exported_at"], r"^\d{4}-\d{2}-\d{2}T")
        again = self.invoke()
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(len(list(self.directory.glob("*.retro.*.json"))), 1)

    def test_add_waits_for_home_lock_then_reports_holder(self):
        ended = self.box.cli(
            "set-status", "pr-open", "--pr-url", "https://x/pr/1", cwd=self.wt
        )
        self.assertEqual(ended.returncode, 0, ended.stderr)
        lock_path = self.box.home / "improvements.lock.json"
        lock_path.write_text(
            json.dumps(
                {
                    "owner_pid": 12345,
                    "host": "other-host",
                    "harness": "holder",
                    "at": "now",
                }
            )
        )
        before = set(self.directory.iterdir())
        started = time.monotonic()
        out = self.invoke()
        elapsed = time.monotonic() - started
        self.assertEqual(out.returncode, 1, out.stderr)
        self.assertIn("holder", out.stderr)
        self.assertGreaterEqual(elapsed, 4.5)
        self.assertLess(elapsed, 7)
        self.assertEqual(set(self.directory.iterdir()), before)
        listed = self.box.cli("improvements")
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertNotIn("improvements.lock", listed.stdout)

    def test_lists_retro_and_run_export_and_claims_retro(self):
        ended = self.box.cli(
            "set-status", "pr-open", "--pr-url", "https://x/pr/1", cwd=self.wt
        )
        self.assertEqual(ended.returncode, 0, ended.stderr)
        added = self.invoke()
        self.assertEqual(added.returncode, 0, added.stderr)
        listed = self.box.cli("improvements")
        self.assertEqual(listed.returncode, 0, listed.stderr)
        entries = {e["name"]: e for e in json.loads(listed.stdout)["improvements"]}
        retro = entries[self.name]
        self.assertEqual(retro["kind"], "retro")
        self.assertEqual(retro["signal_key"], self.candidate["signal_key"])
        self.assertEqual(
            retro["suggested_feature"], self.candidate["suggested_feature"]
        )
        export = entries[f"{self.box.repo.name}-{self.branch}"]
        self.assertEqual(export["kind"], "run-export")
        self.assertIsNone(export["signal_key"])
        self.assertIn(self.branch, export["suggested_feature"])
        claimed = self.box.cli("improvements", "claim", self.name, cwd=self.wt)
        self.assertEqual(claimed.returncode, 0, claimed.stderr)
        self.assertEqual(json.loads(claimed.stdout)["status"], "claimed")

    def test_add_drops_malformed_candidates_and_skips_batch_duplicates(self):
        ended = self.box.cli(
            "set-status", "pr-open", "--pr-url", "https://x/pr/1", cwd=self.wt
        )
        self.assertEqual(ended.returncode, 0, ended.stderr)
        invalid = [
            {"signal_key": "unknown:thing"},
            {"signal_key": "halt-cluster:../bad"},
            {"evidence": ""},
            {"evidence": "x" * 2001},
            {"suggested_feature": ""},
            {"suggested_feature": "two\nlines"},
            {"suggested_feature": "x" * 501},
            {"rank": 0},
            {"rank": True},
        ]
        candidates = [dict(self.candidate, **change) for change in invalid]
        candidates += [self.candidate, self.candidate]
        Path(self.source).write_text(
            "```json\n" + json.dumps({"retro": {"candidates": candidates}}) + "\n```\n"
        )
        out = self.invoke()
        self.assertEqual(out.returncode, 0, out.stderr)
        result = json.loads(out.stdout)
        self.assertEqual(len(result["dropped"]), len(invalid))
        self.assertTrue(all(item.get("reason") for item in result["dropped"]))
        self.assertEqual(len(result["written"]), 1)
        self.assertEqual(len(result["skipped"]), 1)
        self.assertEqual(len(list(self.directory.glob("*.retro.*.json"))), 1)

    def test_add_caps_counting_own_run_and_rewrites_ready(self):
        ended = self.box.cli(
            "set-status", "pr-open", "--pr-url", "https://x/pr/1", cwd=self.wt
        )
        self.assertEqual(ended.returncode, 0, ended.stderr)
        initial = [self.candidate, dict(self.candidate, signal_key="halt-cluster:plan")]
        Path(self.source).write_text(
            "```json\n" + json.dumps({"retro": {"candidates": initial}}) + "\n```\n"
        )
        self.assertEqual(self.invoke().returncode, 0)
        candidates = [
            dict(self.candidate, signal_key="halt-cluster:review", rank=3),
            dict(self.candidate, signal_key="halt-cluster:pr", rank=1),
            dict(self.candidate, signal_key="halt-cluster:specify", rank=2),
            dict(self.candidate, suggested_feature="Updated recovery", rank=4),
        ]
        Path(self.source).write_text(
            "```json\n" + json.dumps({"retro": {"candidates": candidates}}) + "\n```\n"
        )
        out = self.invoke()
        self.assertEqual(out.returncode, 0, out.stderr)
        result = json.loads(out.stdout)
        self.assertEqual(len(result["written"]), 2)
        self.assertTrue(
            any(name.endswith(".halt-cluster.pr") for name in result["written"])
        )
        self.assertEqual(
            {x["signal_key"] for x in result["dropped"]},
            {"halt-cluster:review", "halt-cluster:specify"},
        )
        self.assertTrue(all(x["reason"] == "cap" for x in result["dropped"]))
        self.assertEqual(len(list(self.directory.glob("*.retro.*.json"))), 3)
        self.assertEqual(
            json.loads((self.directory / (self.name + ".json")).read_text())[
                "suggested_feature"
            ],
            "Updated recovery",
        )

    def test_add_skips_other_ready_and_own_claimed(self):
        ended = self.box.cli(
            "set-status", "pr-open", "--pr-url", "https://x/pr/1", cwd=self.wt
        )
        self.assertEqual(ended.returncode, 0, ended.stderr)
        self.assertEqual(self.invoke().returncode, 0)
        claimed = self.box.cli("improvements", "claim", self.name, cwd=self.wt)
        self.assertEqual(claimed.returncode, 0, claimed.stderr)
        own_path = self.directory / (self.name + ".json")
        original = own_path.read_bytes()
        other_key = "judge-rejection:reviewer"
        other_name = "other-run.retro.judge-rejection.reviewer"
        (self.directory / (other_name + ".json")).write_text(
            json.dumps(
                {
                    "name": other_name,
                    "kind": "retro",
                    "run": {"repo": str(self.box.repo), "branch": "other"},
                    "signal_key": other_key,
                    "status": "ready",
                }
            )
        )
        candidates = [self.candidate, dict(self.candidate, signal_key=other_key)]
        Path(self.source).write_text(
            "```json\n" + json.dumps({"retro": {"candidates": candidates}}) + "\n```\n"
        )
        out = self.invoke()
        self.assertEqual(out.returncode, 0, out.stderr)
        result = json.loads(out.stdout)
        skipped = {x["signal_key"]: x for x in result["skipped"]}
        self.assertEqual(skipped[self.candidate["signal_key"]]["reason"], "claimed")
        self.assertEqual(skipped[other_key]["covered_by"], other_name)
        self.assertEqual(result["written"], [])
        self.assertEqual(own_path.read_bytes(), original)

    def test_add_refuses_non_ended_run(self):
        out = self.invoke()
        self.assertEqual(out.returncode, 1, out.stderr)
        self.assertFalse(self.directory.exists())

    def test_add_refuses_bad_envelopes(self):
        out = self.box.cli(
            "set-status", "pr-open", "--pr-url", "https://x/pr/1", cwd=self.wt
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        for text in ("no block", "```json\n{bad}\n```", '```json\n{"retro": {}}\n```'):
            Path(self.source).write_text(text)
            result = self.invoke()
            self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(list(self.directory.glob("*.retro.*.json")), [])

    def test_add_unwritable_directory_reports_path_without_temp(self):
        out = self.box.cli(
            "set-status", "pr-open", "--pr-url", "https://x/pr/1", cwd=self.wt
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        for path in self.directory.iterdir():
            path.unlink()
        self.directory.rmdir()
        self.directory.write_text("not a directory")
        result = self.invoke()
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(str(self.directory), result.stderr)
        self.assertEqual(list(self.box.home.glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
