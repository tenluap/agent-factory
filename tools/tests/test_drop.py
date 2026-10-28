"""End-of-run drop exercised through the public CLI."""

import json
import sys
import unittest
from pathlib import Path

from tests import Sandbox, fixture

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core/skills/factory/bin"))
from factory_cli import totals


class DropTests(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()
        self.addCleanup(self.box.close)
        run = fixture("state-v4.json")
        run.update(
            status="pr-open",
            pr_url="https://example.com/pr/1",
            ended_at="2026-10-23T12:00:00Z",
        )
        self.wt = self.box.worktree_run("011-drop", run)
        self.folder = self.wt / "specs/011-drop/factory"
        (self.folder / "brief.md").write_text("brief\n")
        (self.folder / "nested").mkdir()
        (self.folder / "nested/file").write_text("nested\n")
        self.box.git("add", "-A", cwd=self.wt)
        self.box.git("commit", "-qm", "add run files", cwd=self.wt)

    def test_drop_commits_only_run_deletions_and_returns_summary(self):
        state = json.loads((self.folder / "state.json").read_text())
        remote = self.box.dir / "remote.git"
        self.box.git("init", "--bare", "-q", str(remote))
        self.box.git("remote", "add", "origin", str(remote), cwd=self.wt)
        self.box.git("push", "-q", "origin", "HEAD", cwd=self.wt)
        refs = self.box.git("show-ref", cwd=remote)
        result = self.box.cli("drop", cwd=self.wt)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(
            self.box.git("log", "-1", "--format=%s", cwd=self.wt).strip(),
            "factory: drop run artifacts",
        )
        changes = self.box.git(
            "show", "--format=", "--name-status", "HEAD", cwd=self.wt
        ).splitlines()
        self.assertTrue(changes)
        self.assertTrue(
            all(line.startswith("D\tspecs/011-drop/factory/") for line in changes),
            changes,
        )
        self.assertFalse(self.folder.exists())
        self.assertEqual(
            self.box.git(
                "ls-tree", "-r", "HEAD", "--", "specs/011-drop/factory", cwd=self.wt
            ),
            "",
        )
        self.assertEqual(self.box.git("show-ref", cwd=remote), refs)
        self.assertEqual(data["dropped"], "specs/011-drop/factory")
        self.assertTrue(data["archive"])
        self.assertIsNone(data["design"])
        self.assertEqual(
            data["commit"],
            self.box.git("rev-parse", "--short", "HEAD", cwd=self.wt).strip(),
        )
        self.assertEqual(data["pr_url"], state["pr_url"])
        self.assertEqual(
            data["totals_sentence"], totals.sentence(totals.compute(state))
        )
        self.assertTrue(data["dropped_at"])
