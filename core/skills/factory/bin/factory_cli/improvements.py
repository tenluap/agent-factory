"""Run-end improvement backlog: export, listing and claim (FR-011..FR-013).

The backlog file `${FACTORY_HOME}/improvements/<repo-name>-<branch>.json` is
the structural gate on improvement work: the writer creates it once, at its
run's end (`pr-open`/`aborted`), and nothing creates it any other way. The
only later transition is `claim` stamping `claimed`.
"""

import hashlib
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from factory_cli import lock, state, totals


def _write_text(path, text):
    """UTF-8 with LF endings on every OS (Path.write_text has no newline
    argument before Python 3.10)."""
    with open(path, "w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)

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


def _entry_name(run_state, kind, key):
    """`<repo-name>-<branch>.<repo-hash>.<kind>.<key>` with `:` as `.`: one
    entry per run and signal key (retro and feedback entries)."""
    repo_hash = hashlib.sha256(str(run_state.get("repo")).encode()).hexdigest()[:12]
    return (
        backlog_name(run_state.get("repo"), run_state.get("branch"))[:-5]
        + "."
        + repo_hash
        + f".{kind}."
        + key.replace(":", ".")
    )


def factory_sha(factory_dir=FACTORY_DIR):
    """The factory version: best-effort `git -C <F> rev-parse HEAD`, else null
    when the install is not in a git tree."""
    try:
        out = subprocess.run(
            ["git", "-C", str(factory_dir), "rev-parse", "HEAD"],
            capture_output=True,
            text=True, encoding="utf-8", errors="replace",
        )
    except OSError:
        return None
    return out.stdout.strip() if out.returncode == 0 and out.stdout.strip() else None


def _write_atomic(path, body):
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        _write_text(tmp, json.dumps(body, indent=2, ensure_ascii=False) + "\n")
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def _acquire_home_lock(directory, harness):
    deadline = time.monotonic() + 5
    while True:
        try:
            lock.acquire(directory, harness=harness)
            return
        except lock.LockHeld:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise
            time.sleep(min(0.1, remaining))


def add(home, run_state, candidates, now=None):
    """Write retro candidates and preserve completed writes on I/O failure."""
    directory = Path(home) / "improvements"
    result = {"written": [], "skipped": [], "dropped": []}
    acquired = False
    try:
        _acquire_home_lock(directory, "improvements")
        acquired = True
        directory.mkdir(parents=True, exist_ok=True)
        own = {}
        own_paths = {}
        covered = {}
        for path in sorted(directory.glob("*.json")):
            try:
                entry = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(entry, dict) or entry.get("kind") != "retro":
                continue
            run = entry.get("run")
            if not isinstance(run, dict):
                continue
            key = entry.get("signal_key")
            if not isinstance(key, str):
                continue
            if all(run.get(k) == run_state.get(k) for k in ("repo", "branch")):
                own[key] = entry
                own_paths[key] = path
            elif entry.get("status") == "ready":
                covered.setdefault(key, entry.get("name") or path.stem)
        seen = set()
        valid = []
        for candidate in candidates:
            key = candidate.get("signal_key", "") if isinstance(candidate, dict) else ""
            if not isinstance(key, str) or not re.fullmatch(
                r"(?:analyze-escalation|fixer-recurring|judge-rejection|in-est-outlier|halt-cluster):[a-z0-9][a-z0-9-]{0,63}",
                key,
            ):
                result["dropped"].append({"signal_key": key, "reason": "invalid key"})
                continue
            evidence = candidate.get("evidence")
            feature = candidate.get("suggested_feature")
            rank = candidate.get("rank")
            if (
                not isinstance(evidence, str)
                or not evidence.strip()
                or len(evidence) > 2000
            ):
                reason = "invalid evidence"
            elif (
                not isinstance(feature, str)
                or not feature.strip()
                or len(feature) > 500
                or feature.splitlines() != [feature]
            ):
                reason = "invalid suggested_feature"
            elif not isinstance(rank, int) or isinstance(rank, bool) or rank <= 0:
                reason = "invalid rank"
            else:
                reason = None
            if reason:
                result["dropped"].append({"signal_key": key, "reason": reason})
                continue
            if key in seen:
                result["skipped"].append({"signal_key": key, "reason": "duplicate"})
                continue
            seen.add(key)
            valid.append(candidate)
        for candidate in sorted(valid, key=lambda item: item["rank"]):
            key = candidate["signal_key"]
            if key in own and own[key].get("status") == "claimed":
                result["skipped"].append({"signal_key": key, "reason": "claimed"})
                continue
            if key in covered:
                result["skipped"].append(
                    {"signal_key": key, "covered_by": covered[key]}
                )
                continue
            if key not in own and len(own) >= 3:
                result["dropped"].append({"signal_key": key, "reason": "cap"})
                continue
            name = _entry_name(run_state, "retro", key)
            path = own_paths.get(key, directory / f"{name}.json")
            name = path.stem
            if key not in own and path.exists():
                raise OSError(
                    f"refusing to replace a backlog owned by another run: {path}"
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
            _write_atomic(path, body)
            own[key] = body
            result["written"].append(name)
    except (OSError, lock.LockHeld) as e:
        raise AddError(e, result) from e
    finally:
        if acquired:
            lock.release(directory)
    return result


def add_feedback(home, run, items, now=None):
    """Write or extend the feedback entries of one run (seam S2).

    `items` are `{signal_key, evidence, suggested_feature}`; `evidence` is one
    link, and an empty link is never stored. One entry per run and key: a
    `ready` entry gains only new non-empty links and keeps its stored fields;
    a `claimed` entry is reported and left byte-identical. Any other file at
    the entry name (unreadable, foreign or not ready) is refused, not replaced.
    Returns `{created, updated, claimed}` lists of entry names.
    """
    directory = Path(home) / "improvements"
    result = {"created": [], "updated": [], "claimed": []}
    acquired = False
    try:
        _acquire_home_lock(directory, "improvements")
        acquired = True
        directory.mkdir(parents=True, exist_ok=True)
        own = {}
        for path in sorted(directory.glob("*.json")):
            try:
                entry = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(entry, dict) or entry.get("kind") != "feedback":
                continue
            stored_run = entry.get("run")
            if isinstance(stored_run, dict) and all(
                stored_run.get(k) == run.get(k) for k in ("repo", "branch")
            ):
                own[entry.get("signal_key")] = (path, entry)
        for item in items:
            key = item["signal_key"]
            link = item.get("evidence") or ""
            if key in own:
                path, body = own[key]
                if body.get("status") == "claimed":
                    result["claimed"].append(path.stem)
                    continue
                if body.get("status") != "ready" or not isinstance(
                    body.get("evidence"), list
                ):
                    raise OSError(f"refusing to replace a feedback entry: {path}")
                if link and link not in body["evidence"]:
                    body["evidence"].append(link)
                    _write_atomic(path, body)
                    result["updated"].append(path.stem)
                continue
            path = directory / f"{_entry_name(run, 'feedback', key)}.json"
            if path.exists():
                raise OSError(
                    f"refusing to replace a file not owned by this run: {path}"
                )
            body = {
                "name": path.stem,
                "kind": "feedback",
                "run": {k: run.get(k) for k in ("repo", "branch", "spec_dir")},
                "signal_key": key,
                "evidence": [link] if link else [],
                "suggested_feature": item.get("suggested_feature"),
                "factory_sha": factory_sha(),
                "status": "ready",
                "exported_at": now or state.iso(datetime.now(timezone.utc)),
                "claimed_at": None,
            }
            _write_atomic(path, body)
            own[key] = (path, body)
            result["created"].append(path.stem)
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
            body = json.loads(path.read_text(encoding="utf-8"))
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
                "kind": body.get("kind", "run-export"),
                "signal_key": body.get("signal_key"),
                "issues_by_kind": counts,
                "suggested_feature": body.get("suggested_feature")
                or (
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
    acquired = False
    try:
        _acquire_home_lock(directory, "improvements")
        acquired = True
        if not path.is_file():
            raise ClaimError(f"no improvement backlog named '{name}'")
        try:
            body = json.loads(path.read_text(encoding="utf-8"))
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
        _write_atomic(path, body)
        return {
            "claimed": body.get("name") or path.stem,
            "status": "claimed",
            "claimed_at": now,
        }
    except (OSError, lock.LockHeld) as e:
        raise ClaimError(f"cannot claim '{name}': {e}") from e
    finally:
        if acquired:
            lock.release(directory)
