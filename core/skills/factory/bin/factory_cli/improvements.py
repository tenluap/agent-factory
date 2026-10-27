"""Run-end improvement backlog: export, listing and claim (FR-011..FR-013).

The backlog file `${FACTORY_HOME}/improvements/<repo-name>-<branch>.json` is
the structural gate on improvement work: the writer creates it once, at its
run's end (`pr-open`/`aborted`), and nothing creates it any other way. The
only later transition is `claim` stamping `claimed`.
"""

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from factory_cli import state, totals

FACTORY_DIR = Path(__file__).resolve().parents[2]


def backlog_name(repo, branch):
    """`<repo-name>-<branch>.json` — one name per ended run."""
    return f"{Path(repo).name}-{branch}.json"


def factory_sha(factory_dir=FACTORY_DIR):
    """The factory version: best-effort `git -C <F> rev-parse HEAD`, else null
    when the install is not in a git tree."""
    try:
        out = subprocess.run(
            ["git", "-C", str(factory_dir), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    return out.stdout.strip() if out.returncode == 0 and out.stdout.strip() else None


def export(home, run_state, now=None):
    """Write the run-end backlog atomically (temp + `os.replace`); returns the
    file path. A zero-issue run exports too — the file's existence is the
    gate, so it must exist for every ended run."""
    name = backlog_name(run_state.get("repo"), run_state.get("branch"))
    directory = Path(home) / "improvements"
    directory.mkdir(parents=True, exist_ok=True)
    body = {
        "name": name[: -len(".json")],
        "run": {
            "branch": run_state.get("branch"),
            "spec_dir": run_state.get("spec_dir"),
            "worktree": run_state.get("worktree"),
            "status": run_state.get("status"),
            "ended_at": run_state.get("ended_at"),
        },
        "issues": run_state.get("issues") or [],
        "totals": totals.compute(run_state),
        "factory_sha": factory_sha(),
        "status": "ready",
        "exported_at": now or state.iso(datetime.now(timezone.utc)),
        "claimed_at": None,
    }
    path = directory / name
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n")
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    return path
