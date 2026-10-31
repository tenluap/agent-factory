"""Run-end improvement backlog: export, listing and claim (FR-011..FR-013).

The backlog file `${FACTORY_HOME}/improvements/<repo-name>-<branch>.json` is
the structural gate on improvement work: the writer creates it once, at its
run's end (`pr-open`/`aborted`), and nothing creates it any other way. The
only later transition is `claim` stamping `claimed`.
"""

import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from factory_cli import lock, state, totals

FACTORY_DIR = Path(__file__).resolve().parents[2]


class ClaimError(Exception):
    """A refused claim, with the reason (exit 1, never a traceback)."""


class AddError(Exception):
    def __init__(self, error, result):
        super().__init__(str(error))
        self.result = result


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


def _write_atomic(path, body):
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n")
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def add(home, run_state, candidates, now=None):
    """Write retro candidates and preserve completed writes on I/O failure."""
    directory = Path(home) / "improvements"
    result = {"written": [], "skipped": [], "dropped": []}
    acquired = False
    try:
        deadline = time.monotonic() + 5
        while True:
            try:
                lock.acquire(directory, harness="improvements")
                acquired = True
                break
            except lock.LockHeld:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise
                time.sleep(min(0.1, remaining))
        directory.mkdir(parents=True, exist_ok=True)
        for candidate in candidates:
            key = candidate.get("signal_key", "") if isinstance(candidate, dict) else ""
            # Never derive a path from an unsafe key, even before full validation.
            if not isinstance(key, str) or not re.fullmatch(
                r"[a-z0-9-]+:[a-z0-9][a-z0-9-]{0,63}", key
            ):
                result["dropped"].append({"signal_key": key, "reason": "invalid key"})
                continue
            name = (
                backlog_name(run_state.get("repo"), run_state.get("branch"))[:-5]
                + ".retro."
                + key.replace(":", ".")
            )
            body = {
                "name": name,
                "kind": "retro",
                "run": {k: run_state.get(k) for k in ("repo", "branch", "spec_dir")},
                "signal_key": key,
                "evidence": candidate.get("evidence"),
                "suggested_feature": candidate.get("suggested_feature"),
                "rank": candidate.get("rank"),
                "factory_sha": factory_sha(),
                "status": "ready",
                "exported_at": now or state.iso(datetime.now(timezone.utc)),
                "claimed_at": None,
            }
            path = directory / f"{name}.json"
            _write_atomic(path, body)
            result["written"].append(name)
    except (OSError, lock.LockHeld) as e:
        raise AddError(e, result) from e
    finally:
        if acquired:
            lock.release(directory)
    return result


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
    _write_atomic(path, body)
    return path


def list_backlogs(home):
    """Every `${FACTORY_HOME}/improvements/*.json` with its kind counts and a
    suggested feature text for the user (FR-013); never started automatically."""
    entries = []
    for path in sorted((Path(home) / "improvements").glob("*.json")):
        try:
            body = json.loads(path.read_text())
        except (OSError, ValueError):
            continue  # skip an unreadable file, never crash the listing
        if not isinstance(body, dict):
            continue
        counts = {}
        causes = {}
        for issue in body.get("issues") or []:
            kind = issue.get("kind") if isinstance(issue, dict) else None
            counts[kind or "unknown"] = counts.get(kind or "unknown", 0) + 1
            cause = issue.get("cause") if isinstance(issue, dict) else None
            if cause:
                causes[cause] = causes.get(cause, 0) + 1
        run = (body.get("run") or {}).get("branch") or body.get("name") or path.stem
        summary = (
            ", ".join(f"{count} {kind}(s)" for kind, count in sorted(counts.items()))
            or "no recorded issues"
        )
        if causes:
            summary += "; causes: " + ", ".join(
                f"{count} {cause}" for cause, count in sorted(causes.items())
            )
        entries.append(
            {
                "name": body.get("name") or path.stem,
                "run": run,
                "status": body.get("status"),
                "issues_by_kind": counts,
                "suggested_feature": (
                    f"Improve the factory from the recorded issues of run "
                    f"{run}: {summary}."
                ),
            }
        )
    return {"improvements": entries}


def claim(home, name, source_runs=()):
    """Stamp `claimed`/`claimed_at` once (FR-012); the only transition a
    backlog file ever takes after `ready`. `source_runs` carries
    (branch-or-name, status) of the repo's discoverable runs so a claim on a
    not-yet-ended source run is refused, naming that run."""
    filename = name if name.endswith(".json") else f"{name}.json"
    directory = (Path(home) / "improvements").resolve()
    path = directory / filename
    if Path(filename).name != filename or path.resolve().parent != directory:
        raise ClaimError(f"invalid improvement backlog name '{name}'")
    if not path.is_file():
        raise ClaimError(f"no improvement backlog named '{name}'")
    try:
        body = json.loads(path.read_text())
    except (OSError, ValueError) as e:
        raise ClaimError(f"cannot read {path}: {e}") from e
    status = body.get("status") if isinstance(body, dict) else None
    if status != "ready":
        raise ClaimError(f"'{name}' is {status!r}, not ready; it cannot be claimed")
    branch = (body.get("run") or {}).get("branch")
    for run_name, run_status in source_runs:
        if run_name == branch and run_status not in ("pr-open", "aborted"):
            raise ClaimError(
                f"the source run '{branch}' has not ended ({run_status}); "
                "its backlog cannot be claimed yet"
            )
    now = state.iso(datetime.now(timezone.utc))
    body["status"] = "claimed"
    body["claimed_at"] = now
    try:
        _write_atomic(path, body)
    except OSError as e:
        raise ClaimError(f"cannot claim '{name}': {e}") from e
    return {
        "claimed": body.get("name") or path.stem,
        "status": "claimed",
        "claimed_at": now,
    }
