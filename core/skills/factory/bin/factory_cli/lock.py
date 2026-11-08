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


def _write_text(path, text):
    """UTF-8 with LF endings on every OS (Path.write_text has no newline
    argument before Python 3.10)."""
    with open(path, "w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


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
    """Liveness judgment (FR-012): a PID the OS probe cannot evaluate —
    wrong type, zero, negative, out of range — counts as live; only a
    proven-gone owner frees the lock."""
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return True
    if os.name == "nt":
        return _alive_windows(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except (OverflowError, OSError):
        return True
    return True


def _alive_windows(pid):
    """Windows probe: os.kill(pid, 0) there calls TerminateProcess and would
    kill the owner, so ask the OS for the process's exit code instead. Only a
    PID the OS reports as nonexistent, or a process that has exited, is gone."""
    import ctypes
    from ctypes import wintypes

    if pid > 0xFFFFFFFF:
        return True
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    process_query_limited_information = 0x1000
    error_invalid_parameter = 87  # no process has this PID
    still_active = 259
    handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
    if not handle:
        return ctypes.get_last_error() != error_invalid_parameter
    try:
        code = wintypes.DWORD()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
            return True
        return code.value == still_active
    finally:
        kernel32.CloseHandle(handle)


def _live(info):
    """Live unless on its recorded host with the owner process gone."""
    if info.get("host") == socket.gethostname() and not _alive(info.get("owner_pid")):
        return False
    return True


def read(path):
    try:
        loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return loaded if isinstance(loaded, dict) else None


def _write(path, info):
    path = Path(path)
    text = json.dumps(info, indent=2) + "\n"
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        _write_text(tmp, text)
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def _identity(path):
    """(st_dev, st_ino) of the file at path, or None when it is absent."""
    try:
        st = os.stat(path)
    except OSError:
        return None
    return (st.st_dev, st.st_ino)


def _create(path, info):
    """Create the lock file exclusively; FileExistsError when one exists.

    A failed write removes the file only when it still holds the JSON this
    call wrote, so a lock swapped in since the create is never deleted.
    """
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(info, indent=2) + "\n")
    except BaseException:
        if read(path) == info:
            Path(path).unlink(missing_ok=True)
        raise


def acquire(state_path, harness):
    """Take the run's lock for a write; LockHeld under a live foreign lock.

    Creation is O_CREAT|O_EXCL, so racers that both see no lock never both
    win, and an unreadable lock file is refused (its owner is unknown; only
    `take --force` clears it). A stale lock (own host, owner gone) is
    replaced, keeping it as `previous`; the replacement unlinks only a lock
    that still holds the stale contents just re-read and is still the same
    file on disk (same device and inode), so a racer's fresh lock is never
    deleted. Two racers stealing the same stale lock can still both replace
    it; fcntl.flock is the upgrade if that ever matters.
    """
    path = lock_path_for(state_path)
    for _ in range(3):
        existing = read(path)
        if existing and _live(existing):
            raise LockHeld(existing)
        stale_id = _identity(path) if existing else None
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
            if (
                existing
                and not _live(existing)
                and read(path) == existing
                and _identity(path) == stale_id
            ):
                path.unlink(missing_ok=True)  # clear the stale lock we observed
    raise LockHeld(
        read(path) or {"owner_pid": "?", "host": "?", "harness": "?", "at": "?"}
    )


def release(state_path):
    """Remove the lock only if this process still owns it. The unlink is
    identity-checked (FR-014): the file is removed only when it is still the
    same file (st_dev, st_ino) whose contents said so — a lock swapped in by
    another owner inside the window is left in place."""
    path = lock_path_for(state_path)
    identity = _identity(path)
    info = read(path)
    if (
        info
        and info.get("owner_pid") == os.getpid()
        and info.get("host") == socket.gethostname()
    ):
        if _identity(path) != identity:
            return  # replaced since the read; not ours to remove
        path.unlink(missing_ok=True)


def take(state_path, harness, force=False):
    """The only explicit takeover. Force is evaluated before liveness
    (FR-013): a failing probe never blocks --force. Without --force it
    refuses a live lock."""
    path = lock_path_for(state_path)
    existing = read(path)
    if not force and existing and _live(existing):
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
