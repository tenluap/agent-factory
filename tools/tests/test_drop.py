"""End-of-run drop exercised through the public CLI."""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

from tests import Sandbox, fixture

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core/skills/factory/bin"))
from factory_cli import commands, improvements, totals


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

    def test_archive_contains_all_bytes_except_lock(self):
        (self.folder / "untracked").write_bytes(b"untracked\x00")
        (self.folder / "lock.json").write_text("stale lock")
        expected = {
            str(p.relative_to(self.folder)): p.read_bytes()
            for p in self.folder.rglob("*")
            if p.is_file() and p.name != "lock.json"
        }
        result = self.box.cli("drop", cwd=self.wt)
        self.assertEqual(result.returncode, 0, result.stderr)
        archive = Path(json.loads(result.stdout)["archive"])
        self.assertEqual(
            archive,
            self.box.home
            / "archive"
            / improvements.backlog_name(self.box.repo, "011-drop")[:-5],
        )
        self.assertEqual(
            {
                str(p.relative_to(archive)): p.read_bytes()
                for p in archive.rglob("*")
                if p.is_file()
            },
            expected,
        )

    def test_copy_failure_removes_partial_archive(self):
        before = self.box.git("rev-parse", "HEAD", cwd=self.wt)

        def broken_copy(src, dest, **kwargs):
            Path(dest).mkdir()
            (Path(dest) / "partial").write_text("partial")
            raise OSError("copy broke")

        with (
            mock.patch.dict(os.environ, FACTORY_HOME=str(self.box.home)),
            mock.patch.object(commands.shutil, "copytree", side_effect=broken_copy),
        ):
            with self.assertRaises(commands.CLIError) as error:
                commands.cmd_drop(str(self.box.repo), self.wt)
        self.assertEqual(error.exception.code, 1)
        self.assertIn("copy broke", str(error.exception))
        self.assertEqual(self.box.git("rev-parse", "HEAD", cwd=self.wt), before)
        self.assertTrue((self.folder / "state.json").exists())
        self.assertTrue(self.box.git("ls-files", "specs/011-drop/factory", cwd=self.wt))
        self.assertEqual(list((self.box.home / "archive").glob("*")), [])

    def test_verification_failure_names_file_and_removes_partial_archive(self):
        before = self.box.git("rev-parse", "HEAD", cwd=self.wt)
        with (
            mock.patch.dict(os.environ, FACTORY_HOME=str(self.box.home)),
            mock.patch("filecmp.cmp", return_value=False),
        ):
            with self.assertRaises(commands.CLIError) as error:
                commands.cmd_drop(str(self.box.repo), self.wt)
        self.assertEqual(error.exception.code, 1)
        self.assertIn("brief.md", str(error.exception))
        self.assertEqual(self.box.git("rev-parse", "HEAD", cwd=self.wt), before)
        self.assertTrue((self.folder / "state.json").exists())
        self.assertTrue(self.box.git("ls-files", "specs/011-drop/factory", cwd=self.wt))
        self.assertEqual(list((self.box.home / "archive").glob("*")), [])

    def test_commit_failure_restores_run_and_removes_archive(self):
        before = self.box.git("rev-parse", "HEAD", cwd=self.wt)
        hook = self.box.repo / ".git/hooks/pre-commit"
        hook.write_text("#!/bin/sh\necho commit-failure >&2\nexit 1\n")
        hook.chmod(0o755)
        result = self.box.cli("drop", cwd=self.wt)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("commit-failure", result.stderr)
        self.assertEqual(self.box.git("rev-parse", "HEAD", cwd=self.wt), before)
        self.assertEqual(self.box.git("status", "--porcelain", cwd=self.wt), "")
        self.assertTrue((self.folder / "state.json").exists())
        self.assertEqual(list((self.box.home / "archive").glob("*")), [])
