"""Run-lock lifecycle (FR-005, R4).

One lock guards one run: `lock.json` beside the worktree state, or
`<pending-name>.lock.json` beside a pending file. The lock records owner PID,
host, harness and time. It is live unless it sits on its recorded host with
the owner process gone — on any other host it is never stale automatically.
Only `take` (the CLI's `lock take [--force]`) takes a lock explicitly, and it
records `taken_over` with the previous lock for audit.
"""

import json
import os
import socket
import tempfile
from datetime import datetime, timezone
from pathlib import Path


class LockHeld(Exception):
    """A live lock refuses the operation; the message reports the owner."""

    def __init__(self, info):
        self.info = info
        super().__init__(
            "run locked by PID {owner} on {host} (harness {harness}, since {at}) "
            "- `factory lock take <run> --force` is the only takeover".format(
                owner=info.get("owner_pid"),
                host=info.get("host"),
                harness=info.get("harness"),
                at=info.get("at"),
            )
        )


def lock_path_for(state_path):
    """The lock guarding this state file: `lock.json` beside a worktree state,
    `<name>.lock.json` beside a pending file."""
    state_path = Path(state_path)
    if state_path.name == "state.json":
        return state_path.parent / "lock.json"
    return state_path.with_suffix(".lock.json")


def _now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _alive(pid):
    if not isinstance(pid, int):
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _live(info):
    """Live unless on its recorded host with the owner process gone."""
    if info.get("host") == socket.gethostname() and not _alive(info.get("owner_pid")):
        return False
    return True


def read(path):
    try:
        loaded = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None
    return loaded if isinstance(loaded, dict) else None


def _write(path, info):
    path = Path(path)
    text = json.dumps(info, indent=2) + "\n"
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_text(text)
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def _create(path, info):
    """Create the lock file exclusively; FileExistsError when one exists."""
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(json.dumps(info, indent=2) + "\n")
    except BaseException:
        Path(path).unlink(missing_ok=True)
        raise


def acquire(state_path, harness):
    """Take the run's lock for a write; LockHeld under a live foreign lock.

    Creation is O_CREAT|O_EXCL, so racers that both see no lock never both
    win, and an unreadable lock file is refused (its owner is unknown; only
    `take --force` clears it). A stale lock (own host, owner gone) is
    replaced, keeping it as `previous`; the replacement unlinks only a lock
    still identical to the stale one just re-read, so a racer never deletes
    a lock it did not observe.

    # ponytail: two racers stealing the same stale lock can still both
    # replace it; fcntl.flock is the upgrade if that ever matters.
    """
    path = lock_path_for(state_path)
    for _ in range(3):
        existing = read(path)
        if existing and _live(existing):
            raise LockHeld(existing)
        info = {
            "owner_pid": os.getpid(),
            "host": socket.gethostname(),
            "harness": harness,
            "at": _now(),
            "taken_over": False,
            "previous": existing if existing else None,
        }
        try:
            _create(path, info)
            return info
        except FileExistsError:
            if existing and not _live(existing) and read(path) == existing:
                path.unlink(missing_ok=True)  # clear the stale lock we observed
    raise LockHeld(
        read(path) or {"owner_pid": "?", "host": "?", "harness": "?", "at": "?"}
    )


def release(state_path):
    """Remove the lock only if this process still owns it."""
    path = lock_path_for(state_path)
    info = read(path)
    if (
        info
        and info.get("owner_pid") == os.getpid()
        and info.get("host") == socket.gethostname()
    ):
        path.unlink(missing_ok=True)


def take(state_path, harness, force=False):
    """The only explicit takeover. Without --force it refuses a live lock."""
    path = lock_path_for(state_path)
    existing = read(path)
    if existing and _live(existing) and not force:
        raise LockHeld(existing)
    info = {
        "owner_pid": os.getpid(),
        "host": socket.gethostname(),
        "harness": harness,
        "at": _now(),
        "taken_over": True,
        "previous": existing if existing else None,
    }
    _write(path, info)
    return info
