"""Lock seam tests: the `factory_cli.lock` lifecycle (FR-005).

Live locks refuse with the owner reported; a lock is stale only on its
recorded host when the owner process is gone; takeover is explicit via
`lock take`, recording `taken_over` and the previous lock; a pending run's
lock lives beside its pending file.
"""

import ast
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

CORE_BIN = Path(__file__).resolve().parents[2] / "core" / "skills" / "factory" / "bin"
sys.path.insert(0, str(CORE_BIN))

from factory_cli import lock  # noqa: E402

HOST = socket.gethostname()


def dead_pid():
    proc = subprocess.Popen(["sleep", "30"])
    proc.terminate()
    proc.wait()
    return proc.pid


class LockPathTests(unittest.TestCase):
    def test_worktree_lock_beside_state_as_lock_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            guard = Path(tmp) / "specs" / "001-x" / "factory" / "state.json"
            self.assertEqual(lock.lock_path_for(guard), guard.parent / "lock.json")

    def test_pending_lock_beside_the_pending_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            guard = Path(tmp) / "pending" / "repo-001-x.json"
            self.assertEqual(
                lock.lock_path_for(guard),
                Path(tmp) / "pending" / "repo-001-x.lock.json",
            )


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.guard = Path(self.tmp.name) / "state.json"
        self.lock_path = lock.lock_path_for(self.guard)

    def test_acquire_writes_owner_host_harness_and_time(self):
        info = lock.acquire(self.guard, harness="opencode")
        self.assertEqual(info["owner_pid"], os.getpid())
        self.assertEqual(info["host"], HOST)
        self.assertEqual(info["harness"], "opencode")
        self.assertFalse(info["taken_over"])
        on_disk = json.loads(self.lock_path.read_text())
        self.assertEqual(on_disk["owner_pid"], os.getpid())
        lock.release(self.guard)
        self.assertFalse(self.lock_path.exists(), "release removes the lock")

    def test_live_lock_refuses_with_owner_reported(self):
        lock.acquire(self.guard, harness="opencode")
        with self.assertRaises(lock.LockHeld) as caught:
            lock.acquire(self.guard, harness="claude-code")
        message = str(caught.exception)
        self.assertIn(str(os.getpid()), message, "the owner PID is reported")
        self.assertIn(HOST, message, "the owner host is reported")
        self.assertIn("opencode", message, "the owner harness is reported")
        lock.release(self.guard)

    def test_stale_only_on_recorded_host_with_owner_gone(self):
        gone = dead_pid()
        self.lock_path.write_text(
            json.dumps(
                {
                    "owner_pid": gone,
                    "host": HOST,
                    "harness": "opencode",
                    "at": "2026-10-20T10:00:00Z",
                }
            )
        )
        info = lock.acquire(self.guard, harness="claude-code")
        self.assertEqual(
            info["owner_pid"], os.getpid(), "a stale lock on its own host is replaced"
        )
        lock.release(self.guard)

        self.lock_path.write_text(
            json.dumps(
                {
                    "owner_pid": gone,
                    "host": "some-other-host",
                    "harness": "opencode",
                    "at": "2026-10-20T10:00:00Z",
                }
            )
        )
        with self.assertRaises(lock.LockHeld):
            (
                lock.acquire(self.guard, harness="claude-code"),
                "a dead owner on another host is never automatically stale",
            )

        self.lock_path.write_text(
            json.dumps(
                {
                    "owner_pid": os.getpid(),
                    "host": HOST,
                    "harness": "opencode",
                    "at": "2026-10-20T10:00:00Z",
                }
            )
        )
        with self.assertRaises(lock.LockHeld):
            lock.acquire(self.guard, harness="claude-code"), "a live owner refuses"

    def test_take_is_explicit_and_records_previous(self):
        lock.acquire(self.guard, harness="opencode")
        with self.assertRaises(lock.LockHeld):
            (
                lock.take(self.guard, harness="claude-code"),
                "without --force a live lock refuses",
            )
        taken = lock.take(self.guard, harness="claude-code", force=True)
        self.assertTrue(taken["taken_over"])
        self.assertEqual(taken["previous"]["harness"], "opencode")
        self.assertEqual(taken["previous"]["owner_pid"], os.getpid())
        self.assertEqual(json.loads(self.lock_path.read_text())["taken_over"], True)
        lock.release(self.guard)

        gone = dead_pid()
        self.lock_path.write_text(
            json.dumps(
                {
                    "owner_pid": gone,
                    "host": HOST,
                    "harness": "opencode",
                    "at": "2026-10-20T10:00:00Z",
                }
            )
        )
        taken = lock.take(self.guard, harness="claude-code")  # stale: no force needed
        self.assertTrue(taken["taken_over"])
        self.assertEqual(taken["previous"]["owner_pid"], gone)
        lock.release(self.guard)

    def test_acquire_refuses_an_unreadable_lock_file(self):
        self.lock_path.write_text("{not json")
        with self.assertRaises(lock.LockHeld):
            lock.acquire(self.guard, harness="claude-code")

    def test_acquire_between_read_and_write_loses_to_an_interleaved_owner(self):
        """The create is exclusive: a racer parked after its read, before its
        write, must lose to an acquirer completing inside that window — never
        overwrite it. `_now` is patched only to hold the window open."""
        original_now = lock._now
        in_window = threading.Event()
        close_window = threading.Event()

        def slow_now():
            in_window.set()
            close_window.wait(5)
            return original_now()

        outcome = {}

        def racer():
            try:
                lock.acquire(self.guard, harness="slow")
                outcome["racer"] = "won"
            except lock.LockHeld:
                outcome["racer"] = "held"

        lock._now = slow_now
        thread = threading.Thread(target=racer)
        thread.start()
        try:
            self.assertTrue(in_window.wait(5), "the racer reached the write window")
            lock._now = original_now  # only the racer stays in the window
            lock.acquire(self.guard, harness="main")
            close_window.set()
            thread.join(5)
            lock.release(self.guard)
        finally:
            lock._now = original_now
            close_window.set()
            thread.join(5)
            self.lock_path.unlink(missing_ok=True)
        self.assertEqual(
            outcome.get("racer"),
            "held",
            "a racer that loses the create race reports LockHeld",
        )

    def test_stale_clear_never_deletes_a_lock_swapped_in_after_the_comparison(self):
        """The takeover's unlink must survive a racer's fresh lock that lands
        after our comparison read: the clear re-checks that the file on disk
        is still the stale lock just observed (same device and inode)."""
        gone = dead_pid()
        self.lock_path.write_text(
            json.dumps(
                {
                    "owner_pid": gone,
                    "host": HOST,
                    "harness": "opencode",
                    "at": "2026-10-20T10:00:00Z",
                }
            )
        )
        fresh = {
            "owner_pid": os.getpid(),
            "host": HOST,
            "harness": "claude-code",
            "at": "2026-10-20T10:00:01Z",
        }
        original_read = lock.read
        calls = {"n": 0}

        def racing_read(p):
            calls["n"] += 1
            if calls["n"] != 2:
                return original_read(p)
            observed = self.lock_path.read_text()  # the comparison sees the stale lock
            # a racer's takeover lands: its own stale clear plus exclusive create
            self.lock_path.unlink()
            self.lock_path.write_text(json.dumps(fresh))
            return json.loads(observed)

        lock.read = racing_read
        try:
            with self.assertRaises(lock.LockHeld):
                lock.acquire(self.guard, harness="claude-code")
        finally:
            lock.read = original_read
        self.assertEqual(
            json.loads(self.lock_path.read_text()),
            fresh,
            "the fresh lock a racer swapped in after the comparison survives",
        )

    def test_create_failure_never_unlinks_a_lock_swapped_in_behind_it(self):
        """_create's failed write removes the file only when it still holds
        the JSON this call wrote; a lock swapped in since the create stays."""
        fresh = {
            "owner_pid": os.getpid(),
            "host": HOST,
            "harness": "claude-code",
            "at": "2026-10-20T10:00:01Z",
        }
        original_dumps = json.dumps

        def exploding_dumps(obj, **kwargs):
            self.lock_path.write_text(original_dumps(fresh))  # a racer's lock lands
            raise ValueError("simulated write failure")

        lock.json.dumps = exploding_dumps
        try:
            with self.assertRaises(ValueError):
                lock.acquire(self.guard, harness="claude-code")
        finally:
            lock.json.dumps = original_dumps
        self.assertEqual(
            json.loads(self.lock_path.read_text()),
            fresh,
            "the lock swapped in behind the failed create survives",
        )


class LivenessTests(unittest.TestCase):
    """FR-012: an owner PID the OS probe cannot evaluate counts as live and
    never raises; only a proven-gone owner frees the lock."""

    def lock_info(self, owner_pid):
        return {
            "owner_pid": owner_pid,
            "host": HOST,
            "harness": "opencode",
            "at": "2026-10-23T12:00:00Z",
        }

    def test_unevaluable_pids_count_as_live_and_never_raise(self):
        for pid in (0, -1, -12345, 999999999999, "not-a-pid", None):
            with self.subTest(pid=pid):
                self.assertTrue(lock._alive(pid), "unevaluable means live")

    def test_unevaluable_owner_refuses_acquire(self):
        with tempfile.TemporaryDirectory() as tmp:
            guard = Path(tmp) / "state.json"
            lock.lock_path_for(guard).write_text(
                json.dumps(self.lock_info(999999999999))
            )
            with self.assertRaises(lock.LockHeld):
                lock.acquire(guard, harness="opencode")

    def test_a_gone_owner_is_still_stale(self):
        self.assertFalse(lock._alive(dead_pid()))


class ForceTakeoverTests(unittest.TestCase):
    """FR-013: --force is evaluated before liveness — a takeover with --force
    succeeds even when the holder's liveness cannot be judged; without it a
    live lock refuses with the owner reported."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.guard = Path(self.tmp.name) / "state.json"
        self.lock_path = lock.lock_path_for(self.guard)

    def write_lock(self, owner_pid):
        self.lock_path.write_text(
            json.dumps(
                {
                    "owner_pid": owner_pid,
                    "host": HOST,
                    "harness": "opencode",
                    "at": "2026-10-23T12:00:00Z",
                }
            )
        )

    def test_force_takes_over_when_liveness_cannot_be_judged(self):
        self.write_lock(999999999999)
        with mock.patch.object(lock, "_alive", side_effect=OverflowError):
            info = lock.take(self.guard, harness="opencode", force=True)
        self.assertTrue(info["taken_over"])
        self.assertEqual(lock.read(self.lock_path)["owner_pid"], os.getpid())

    def test_without_force_a_live_lock_refuses_with_owner_reported(self):
        self.write_lock(999999999999)
        with self.assertRaises(lock.LockHeld) as caught:
            lock.take(self.guard, harness="opencode")
        self.assertIn("999999999999", str(caught.exception))


class ReleaseIdentityTests(unittest.TestCase):
    """FR-014: release unlinks only the file whose identity (st_dev, st_ino)
    it just read — a lock replaced by another owner inside the release window
    is left in place."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.guard = Path(self.tmp.name) / "state.json"
        self.lock_path = lock.lock_path_for(self.guard)

    def own_lock(self):
        lock.acquire(self.guard, harness="opencode")
        return lock.read(self.lock_path)

    def test_release_removes_our_own_unchanged_lock(self):
        self.own_lock()
        lock.release(self.guard)
        self.assertIsNone(lock.read(self.lock_path), "our own lock is removed")

    def test_release_leaves_a_foreign_lock(self):
        info = self.own_lock()
        lock._write(self.lock_path, {**info, "owner_pid": 999999})
        lock.release(self.guard)
        self.assertIsNotNone(lock.read(self.lock_path), "a foreign lock stays")

    def test_release_never_unlinks_a_lock_swapped_in_after_its_read(self):
        self.own_lock()
        real_read = lock.read

        def read_then_swap(path):
            info = real_read(path)  # release reads our own lock...
            lock._write(path, {**info, "owner_pid": 999999})  # ...then a rival swaps in
            return info

        with mock.patch.object(lock, "read", side_effect=read_then_swap):
            lock.release(self.guard)
        self.assertIsNotNone(
            lock.read(self.lock_path), "the rival's lock is left in place"
        )
        self.assertEqual(lock.read(self.lock_path)["owner_pid"], 999999)


class LockCliTests(unittest.TestCase):
    def setUp(self):
        from tests import Sandbox, fixture

        self.box = Sandbox()
        self.addCleanup(self.box.close)
        self.branch = "060-lock"
        self.wt = self.box.worktree_run(self.branch, fixture("state-v4.json"))
        from pathlib import Path as _P

        self.guard = self.wt / "specs" / self.branch / "factory" / "state.json"
        self.lock_path = lock.lock_path_for(self.guard)

    def test_lock_take_cli_refuses_live_and_takes_with_force(self):
        lock.acquire(self.guard, harness="opencode")
        out = self.box.cli("lock", "take", self.branch)
        self.assertEqual(out.returncode, 1, out.stderr)
        self.assertIn("locked by PID", out.stderr)
        out = self.box.cli("lock", "take", self.branch, "--force")
        self.assertEqual(out.returncode, 0, out.stderr)
        on_disk = json.loads(self.lock_path.read_text())
        self.assertTrue(on_disk["taken_over"])
        self.assertEqual(on_disk["previous"]["harness"], "opencode")

    def test_writers_refuse_under_a_live_foreign_lock(self):
        holder = subprocess.Popen(["sleep", "30"])
        try:
            self.lock_path.write_text(
                json.dumps(
                    {
                        "owner_pid": holder.pid,
                        "host": HOST,
                        "harness": "opencode",
                        "at": "2026-10-20T10:00:00Z",
                    }
                )
            )
            out = self.box.cli("checkpoint", "implement", cwd=self.wt)
            self.assertEqual(out.returncode, 1)
            self.assertIn("locked by PID", out.stderr)
        finally:
            holder.terminate()
            holder.wait()
            self.lock_path.unlink(missing_ok=True)


class TestModuleHygieneTests(unittest.TestCase):
    """FR-018: each lock behaviour is exercised exactly once — no test method
    is defined twice, and none is dead code after the runner's exit call."""

    def test_no_test_method_is_defined_twice_or_after_the_runner(self):
        tree = ast.parse(Path(__file__).read_text())
        names = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test")
        ]
        duplicates = {name for name in names if names.count(name) > 1}
        self.assertEqual(duplicates, set(), "every lock behaviour is defined once")
        guard_line = None
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.If)
                and isinstance(node.test, ast.Compare)
                and getattr(node.test.left, "id", "") == "__name__"
            ):
                guard_line = node.lineno
        self.assertIsNotNone(guard_line, "the module keeps its runner guard")
        after = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
            and node.name.startswith("test")
            and guard_line
            and node.lineno > guard_line
        ]
        self.assertEqual(after, [], "no test method lives after the runner's exit call")


if __name__ == "__main__":
    unittest.main()

    def test_lock_take_cli_refuses_live_and_takes_with_force(self):
        lock.acquire(self.guard, harness="opencode")
        out = self.box.cli("lock", "take", self.branch)
        self.assertEqual(out.returncode, 1, out.stderr)
        self.assertIn("locked by PID", out.stderr)
        out = self.box.cli("lock", "take", self.branch, "--force")
        self.assertEqual(out.returncode, 0, out.stderr)
        on_disk = json.loads(self.lock_path.read_text())
        self.assertTrue(on_disk["taken_over"])
        self.assertEqual(on_disk["previous"]["harness"], "opencode")

    def test_writers_refuse_under_a_live_foreign_lock(self):
        holder = subprocess.Popen(["sleep", "30"])
        try:
            self.lock_path.write_text(
                json.dumps(
                    {
                        "owner_pid": holder.pid,
                        "host": HOST,
                        "harness": "opencode",
                        "at": "2026-10-20T10:00:00Z",
                    }
                )
            )
            out = self.box.cli("checkpoint", "implement", cwd=self.wt)
            self.assertEqual(out.returncode, 1)
            self.assertIn("locked by PID", out.stderr)
        finally:
            holder.terminate()
            holder.wait()
            self.lock_path.unlink(missing_ok=True)
