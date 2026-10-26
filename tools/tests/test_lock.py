"""Lock seam tests: the `factory_cli.lock` lifecycle (FR-005).

Live locks refuse with the owner reported; a lock is stale only on its
recorded host when the owner process is gone; takeover is explicit via
`lock take`, recording `taken_over` and the previous lock; a pending run's
lock lives beside its pending file.
"""

import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
