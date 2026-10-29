"""End-of-run drop exercised through the public CLI."""

import json
import os
import socket
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

    def test_drop_ignores_inherited_orphan_and_wrong_branch(self):
        original = json.loads((self.folder / "state.json").read_text())
        for name, home in (
            ("001-orphan", str(self.box.dir / "gone")),
            ("002-wrong-branch", str(self.wt)),
        ):
            other = self.wt / "specs" / name / "factory"
            other.mkdir(parents=True)
            (other / "state.json").write_text(
                json.dumps(
                    dict(
                        original,
                        branch=original["branch"] if name == "001-orphan" else name,
                        worktree=home,
                        spec_dir=f"specs/{name}",
                    )
                )
            )
        self.box.git("add", "-A", cwd=self.wt)
        self.box.git("commit", "-qm", "inherited runs", cwd=self.wt)
        orphan = self.wt / "specs/001-orphan/factory/state.json"
        orphan_bytes = orphan.read_bytes()
        result = self.box.cli("drop", cwd=self.wt)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["dropped"], "specs/011-drop/factory")
        self.assertEqual(orphan.read_bytes(), orphan_bytes)
        self.assertTrue(
            (self.wt / "specs/002-wrong-branch/factory/state.json").exists()
        )

    def test_drop_refuses_multiple_authoritative_matches(self):
        duplicate = self.wt / "specs/duplicate/factory"
        duplicate.mkdir(parents=True)
        (duplicate / "state.json").write_bytes(
            (self.folder / "state.json").read_bytes()
        )
        self.box.git("add", "-A", cwd=self.wt)
        self.box.git("commit", "-qm", "duplicate state", cwd=self.wt)
        head = self.box.git("rev-parse", "HEAD", cwd=self.wt)
        result = self.box.cli("drop", cwd=self.wt)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("several", result.stderr)
        self.assertEqual(self.box.git("rev-parse", "HEAD", cwd=self.wt), head)

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
        (self.folder / "lock.json").write_text(
            json.dumps(
                {
                    "owner_pid": 99999999,
                    "host": socket.gethostname(),
                    "harness": "test",
                    "at": "now",
                }
            )
        )
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

    def test_nested_lock_is_archived_and_verified(self):
        nested_lock = self.folder / "nested/lock.json"
        nested_lock.write_bytes(b"important nested lock")
        compare = commands.filecmp.cmp

        with (
            mock.patch.dict(os.environ, FACTORY_HOME=str(self.box.home)),
            mock.patch.object(
                commands.filecmp,
                "cmp",
                side_effect=lambda left, right, shallow: False
                if Path(left).name == "lock.json"
                else compare(left, right, shallow=shallow),
            ),
        ):
            with self.assertRaises(commands.CLIError) as error:
                commands.cmd_drop(str(self.box.repo), self.wt)
        self.assertIn("lock.json", str(error.exception))
        self.assertTrue(nested_lock.exists())
        result = self.box.cli("drop", cwd=self.wt)
        self.assertEqual(result.returncode, 0, result.stderr)
        archive = Path(json.loads(result.stdout)["archive"])
        self.assertEqual(
            (archive / "nested/lock.json").read_bytes(), b"important nested lock"
        )
        self.assertFalse((archive / "lock.json").exists())

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

    def test_dirty_run_folder_refused_without_losing_changes(self):
        file = self.folder / "brief.md"
        for staged in (False, True):
            with self.subTest(staged=staged):
                file.write_text("valuable change\n")
                if staged:
                    self.box.git("add", str(file), cwd=self.wt)
                head = self.box.git("rev-parse", "HEAD", cwd=self.wt)
                dirty = self.box.git("status", "--porcelain", cwd=self.wt)
                result = self.box.cli("drop", cwd=self.wt)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("brief.md", result.stderr)
                self.assertEqual(file.read_text(), "valuable change\n")
                self.assertEqual(self.box.git("rev-parse", "HEAD", cwd=self.wt), head)
                self.assertEqual(
                    self.box.git("status", "--porcelain", cwd=self.wt), dirty
                )
                self.assertFalse((self.box.home / "archive").exists())
                self.box.git("reset", "-q", "HEAD", "--", str(file), cwd=self.wt)
                self.box.git("checkout", "--", str(file), cwd=self.wt)

    def test_refuses_each_non_pr_open_status_without_changes(self):
        state_path = self.folder / "state.json"
        state = json.loads(state_path.read_text())
        for status in ("running", "waiting_user", "paused", "halted", "aborted"):
            with self.subTest(status=status):
                state["status"] = status
                state_path.write_text(json.dumps(state))
                head = self.box.git("rev-parse", "HEAD", cwd=self.wt)
                dirty = self.box.git("status", "--porcelain", cwd=self.wt)
                result = self.box.cli("drop", cwd=self.wt)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(status, result.stderr)
                self.assertEqual(self.box.git("rev-parse", "HEAD", cwd=self.wt), head)
                self.assertEqual(
                    self.box.git("status", "--porcelain", cwd=self.wt), dirty
                )
                self.assertFalse((self.box.home / "archive").exists())

    def test_archive_collision_refuses_without_changes(self):
        target = self.box.home / "archive" / "repo-011-drop"
        target.mkdir(parents=True)
        (target / "keep").write_bytes(b"keep")
        head = self.box.git("rev-parse", "HEAD", cwd=self.wt)
        dirty = self.box.git("status", "--porcelain", cwd=self.wt)
        result = self.box.cli("drop", cwd=self.wt)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(str(target), result.stderr)
        self.assertEqual((target / "keep").read_bytes(), b"keep")
        self.assertEqual(self.box.git("rev-parse", "HEAD", cwd=self.wt), head)
        self.assertEqual(self.box.git("status", "--porcelain", cwd=self.wt), dirty)
        self.assertEqual(list(target.parent.iterdir()), [target])

    def test_live_lock_refuses_without_changes(self):
        (self.folder / "lock.json").write_text(
            json.dumps(
                {
                    "owner_pid": os.getpid(),
                    "host": socket.gethostname(),
                    "harness": "test",
                    "at": "now",
                }
            )
        )
        head = self.box.git("rev-parse", "HEAD", cwd=self.wt)
        dirty = self.box.git("status", "--porcelain", cwd=self.wt)
        result = self.box.cli("drop", cwd=self.wt)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(str(os.getpid()), result.stderr)
        self.assertEqual(self.box.git("rev-parse", "HEAD", cwd=self.wt), head)
        self.assertEqual(self.box.git("status", "--porcelain", cwd=self.wt), dirty)
        self.assertFalse((self.box.home / "archive").exists())

    def test_second_drop_refuses_without_changes(self):
        first = self.box.cli("drop", cwd=self.wt)
        self.assertEqual(first.returncode, 0, first.stderr)
        head = self.box.git("rev-parse", "HEAD", cwd=self.wt)
        dirty = self.box.git("status", "--porcelain", cwd=self.wt)
        entries = list((self.box.home / "archive").iterdir())
        result = self.box.cli("drop", cwd=self.wt)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("no run to drop", result.stderr)
        self.assertEqual(self.box.git("rev-parse", "HEAD", cwd=self.wt), head)
        self.assertEqual(self.box.git("status", "--porcelain", cwd=self.wt), dirty)
        self.assertEqual(list((self.box.home / "archive").iterdir()), entries)

    def prepare_design(self, with_map=True):
        design = self.folder / "design"
        (design / "nested").mkdir(parents=True)
        (design / "nested/evidence.json").write_bytes(b'{"evidence": true}\n')
        (design / "context.json").write_bytes(b"context\x00bytes")
        map_path = self.wt / "docs/design-code-map.json"
        if with_map:
            map_path.parent.mkdir(parents=True, exist_ok=True)
            map_path.write_bytes(
                b'{\n "a": "specs/011-drop/factory/design/context.json",\n'
                b' "b": "specs/011-drop/factory/design/nested/evidence.json",\n'
                b' "other": "specs/other/factory/design/x"\n}\n'
            )
        self.box.git("add", "-A", cwd=self.wt)
        self.box.git("commit", "-qm", "add design evidence", cwd=self.wt)
        return design, map_path

    def test_design_evidence_moves_and_rewrites_map_in_drop_commit(self):
        design, map_path = self.prepare_design()
        expected = {
            str(p.relative_to(design)): p.read_bytes()
            for p in design.rglob("*")
            if p.is_file()
        }
        original_map = map_path.read_bytes()
        old_head = self.box.git("rev-parse", "HEAD", cwd=self.wt).strip()
        result = self.box.cli("drop", cwd=self.wt)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        target = self.wt / "docs/design/011-drop"
        self.assertEqual(data["design"], "docs/design/011-drop")
        self.assertEqual(
            {
                str(p.relative_to(target)): p.read_bytes()
                for p in target.rglob("*")
                if p.is_file()
            },
            expected,
        )
        archive = Path(data["archive"]) / "design"
        self.assertEqual(
            {
                str(p.relative_to(archive)): p.read_bytes()
                for p in archive.rglob("*")
                if p.is_file()
            },
            expected,
        )
        self.assertEqual(
            map_path.read_bytes(),
            original_map.replace(
                b'"specs/011-drop/factory/design/', b'"docs/design/011-drop/'
            ),
        )
        self.assertEqual(
            self.box.git("log", "-1", "--format=%s", cwd=self.wt).strip(),
            "factory: drop run artifacts",
        )
        self.assertEqual(
            self.box.git("rev-parse", "HEAD^", cwd=self.wt).strip(), old_head
        )
        paths = self.box.git(
            "diff", "--no-renames", "--name-only", "HEAD^", "HEAD", cwd=self.wt
        ).splitlines()
        self.assertTrue(
            all(
                p.startswith("specs/011-drop/factory/")
                or p.startswith("docs/design/011-drop/")
                or p == "docs/design-code-map.json"
                for p in paths
            ),
            paths,
        )
        self.assertFalse(self.folder.exists())

    def test_figma_and_image_evidence_move_and_map_rewritten(self):
        design, map_path = self.prepare_design()
        (design / "figma.json").write_text('{"node": "frame"}\n')
        (design / "reference.png").write_bytes(b"image evidence")
        paths = ["figma.json", "reference.png"]
        original = {"sources": [f"specs/011-drop/factory/design/{p}" for p in paths]}
        map_path.write_text(json.dumps(original))
        self.box.git("add", "-A", cwd=self.wt)
        self.box.git("commit", "-qm", "add source evidence", cwd=self.wt)

        result = self.box.cli("drop", cwd=self.wt)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(map_path.read_text()),
            {"sources": [f"docs/design/011-drop/{p}" for p in paths]},
        )
        for name in paths:
            self.assertTrue((self.wt / "docs/design/011-drop" / name).is_file())

    def test_drop_reports_missing_evidence_and_leaves_map_unchanged(self):
        _, map_path = self.prepare_design()
        missing = "specs/011-drop/factory/design/missing.json"
        map_path.write_text(json.dumps({"evidence": missing}))
        self.box.git("add", "-A", cwd=self.wt)
        self.box.git("commit", "-qm", "reference missing evidence", cwd=self.wt)
        original = map_path.read_bytes()

        result = self.box.cli("drop", cwd=self.wt)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(missing, result.stderr)
        self.assertEqual(map_path.read_bytes(), original)
        self.assertTrue(self.folder.is_dir())
        self.assertFalse((self.wt / "docs/design/011-drop").exists())

    def test_drop_rejects_traversal_evidence(self):
        _, map_path = self.prepare_design()
        reference = "specs/011-drop/factory/design/../brief.md"
        map_path.write_text(json.dumps({"evidence": reference}))
        self.box.git("add", "-A", cwd=self.wt)
        self.box.git("commit", "-qm", "reference traversal evidence", cwd=self.wt)
        original = map_path.read_bytes()

        result = self.box.cli("drop", cwd=self.wt)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(reference, result.stderr)
        self.assertEqual(map_path.read_bytes(), original)
        self.assertTrue(self.folder.is_dir())
        self.assertFalse((self.wt / "docs/design/011-drop").exists())

    def test_drop_rejects_symlink_escaping_design(self):
        design, map_path = self.prepare_design()
        (design / "escape").symlink_to("../brief.md")
        reference = "specs/011-drop/factory/design/escape"
        map_path.write_text(json.dumps({"evidence": reference}))
        self.box.git("add", "-A", cwd=self.wt)
        self.box.git("commit", "-qm", "reference symlink evidence", cwd=self.wt)
        original = map_path.read_bytes()

        result = self.box.cli("drop", cwd=self.wt)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(reference, result.stderr)
        self.assertEqual(map_path.read_bytes(), original)
        self.assertTrue(self.folder.is_dir())
        self.assertFalse((self.wt / "docs/design/011-drop").exists())

    def test_dirty_map_refused_without_losing_changes(self):
        _, map_path = self.prepare_design()
        for staged in (False, True):
            with self.subTest(staged=staged):
                map_path.write_text('{"valuable": true}\n')
                if staged:
                    self.box.git("add", str(map_path), cwd=self.wt)
                head = self.box.git("rev-parse", "HEAD", cwd=self.wt)
                dirty = self.box.git("status", "--porcelain", cwd=self.wt)
                result = self.box.cli("drop", cwd=self.wt)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("design-code-map.json", result.stderr)
                self.assertEqual(map_path.read_text(), '{"valuable": true}\n')
                self.assertEqual(self.box.git("rev-parse", "HEAD", cwd=self.wt), head)
                self.assertEqual(
                    self.box.git("status", "--porcelain", cwd=self.wt), dirty
                )
                self.assertFalse((self.box.home / "archive").exists())
                self.box.git("reset", "-q", "HEAD", "--", str(map_path), cwd=self.wt)
                self.box.git("checkout", "--", str(map_path), cwd=self.wt)

    def test_untracked_map_refused_without_changes(self):
        _, map_path = self.prepare_design(with_map=False)
        map_path.parent.mkdir(parents=True, exist_ok=True)
        original = b'{"path": "specs/011-drop/factory/design/context.json"}\n'
        map_path.write_bytes(original)
        archive = self.box.home / "archive"
        archive.mkdir()
        (archive / "keep").write_bytes(b"existing archive")
        head = self.box.git("rev-parse", "HEAD", cwd=self.wt)
        dirty = self.box.git("status", "--porcelain", cwd=self.wt)

        result = self.box.cli("drop", cwd=self.wt)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("design-code-map.json", result.stderr)
        self.assertEqual(map_path.read_bytes(), original)
        self.assertEqual(self.box.git("rev-parse", "HEAD", cwd=self.wt), head)
        self.assertEqual(self.box.git("status", "--porcelain", cwd=self.wt), dirty)
        self.assertEqual(list(archive.iterdir()), [archive / "keep"])
        self.assertEqual((archive / "keep").read_bytes(), b"existing archive")

    def test_design_moves_without_creating_map(self):
        self.prepare_design(with_map=False)
        result = self.box.cli("drop", cwd=self.wt)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["design"], "docs/design/011-drop")
        self.assertTrue((self.wt / "docs/design/011-drop/context.json").exists())
        self.assertFalse((self.wt / "docs/design-code-map.json").exists())

    def test_untracked_design_file_is_not_committed(self):
        design, _ = self.prepare_design()
        (design / "private.txt").write_text("private\n")
        result = self.box.cli("drop", cwd=self.wt)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(
            (Path(data["archive"]) / "design/private.txt").read_text(), "private\n"
        )
        committed = self.box.git("ls-tree", "-r", "--name-only", "HEAD", cwd=self.wt)
        self.assertNotIn("docs/design/011-drop/private.txt", committed)

    def test_design_collision_refuses_without_changes(self):
        self.prepare_design()
        target = self.wt / "docs/design/011-drop"
        target.mkdir(parents=True)
        (target / "keep").write_text("keep")
        head = self.box.git("rev-parse", "HEAD", cwd=self.wt)
        dirty = self.box.git("status", "--porcelain", cwd=self.wt)
        result = self.box.cli("drop", cwd=self.wt)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(str(target), result.stderr)
        self.assertEqual(self.box.git("rev-parse", "HEAD", cwd=self.wt), head)
        self.assertEqual(self.box.git("status", "--porcelain", cwd=self.wt), dirty)
        self.assertFalse((self.box.home / "archive").exists())
        self.assertEqual((target / "keep").read_text(), "keep")

    def test_design_commit_failure_restores_run_map_and_target(self):
        design, map_path = self.prepare_design()
        expected_map = map_path.read_bytes()
        head = self.box.git("rev-parse", "HEAD", cwd=self.wt)
        dirty = self.box.git("status", "--porcelain", cwd=self.wt)
        hook = self.box.repo / ".git/hooks/pre-commit"
        hook.write_text("#!/bin/sh\necho design-commit-failure >&2\nexit 1\n")
        hook.chmod(0o755)
        result = self.box.cli("drop", cwd=self.wt)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("design-commit-failure", result.stderr)
        self.assertEqual(self.box.git("rev-parse", "HEAD", cwd=self.wt), head)
        self.assertEqual(self.box.git("status", "--porcelain", cwd=self.wt), dirty)
        self.assertEqual(map_path.read_bytes(), expected_map)
        self.assertTrue((design / "context.json").exists())
        self.assertFalse((self.wt / "docs/design/011-drop").exists())
        self.assertEqual(list((self.box.home / "archive").glob("*")), [])
