"""Command implementations for the factory CLI.

Read commands (`runs`, `show`, `validate`) live here; write commands join as
their tasks land. Everything mechanical routes through `state` (and, from
T015, `lock`); this module adds only discovery, digests and CLI errors.
"""

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from factory_cli import state

LARGE = ("relay", "timeline", "ledger", "history")  # summarized, never dumped whole


class CLIError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def die(code, message):
    raise CLIError(code, message)


def git(repo, *args):
    try:
        out = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    except OSError:
        die(2, "git not runnable")
    if out.returncode != 0:
        die(2, out.stderr.strip() or f"git {' '.join(args)} failed")
    return out.stdout


def main_repo(cwd):
    try:
        out = subprocess.run(
            [
                "git",
                "-C",
                str(cwd),
                "rev-parse",
                "--path-format=absolute",
                "--git-common-dir",
            ],
            capture_output=True,
            text=True,
        )
    except OSError:
        die(2, "git not runnable")
    if out.returncode != 0:
        die(2, f"not a git repository: {cwd}")
    return str(Path(out.stdout.strip()).resolve().parent)


def fmt_dur(ms):
    s = max(int(ms or 0), 0) // 1000
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h}h {m}m" if h else (f"{m}m {s}s" if m else f"{s}s")


def last_activity(state_dict):
    candidates = []
    for key in ("history", "timeline"):
        entries = state_dict.get(key)
        if isinstance(entries, list) and entries and isinstance(entries[-1], dict):
            if entries[-1].get("at"):
                candidates.append(entries[-1]["at"])
    if state_dict.get("started_at"):
        candidates.append(state_dict["started_at"])
    return max(candidates) if candidates else None


def rounds_of(relay):
    if not isinstance(relay, dict):
        return []
    if isinstance(relay.get("rounds"), list):
        return [r for r in relay["rounds"] if isinstance(r, dict)]
    if relay.get("questions"):  # version 1: one batch at the top of relay
        return [
            {"questions": relay["questions"], "answers": relay.get("answers") or {}}
        ]
    return []


def relay_digest(relay):
    rounds = rounds_of(relay)
    if not rounds:
        return None
    last = rounds[-1]
    questions = last.get("questions") or []
    answers = last.get("answers") or {}
    unanswered = []
    for position, q in enumerate(questions, 1):
        if isinstance(q, dict):
            if q.get("id") in answers:
                continue
            entry = {"position": position, **q}
        else:  # legacy string question
            entry = {"position": position, "text": str(q)}
        unanswered.append(entry)
    return {
        "stage": relay.get("stage"),
        "rounds": len(rounds),
        "total": len(questions),
        "answered": len(questions) - len(unanswered),
        "unanswered": unanswered,
    }


def veto_list(state_dict):
    """SC-004: every auto-accepted answer and every gate override, any stage."""
    decisions = state_dict.get("decisions") or []
    return [
        d
        for d in decisions
        if isinstance(d, dict) and (d.get("auto") or d.get("kind") == "gate-override")
    ]


def totals_sentence(state_dict):
    start = state.parse_iso(state_dict.get("started_at"))
    if not start:
        return None
    end = state.parse_iso(state_dict.get("ended_at")) or datetime.now(timezone.utc)
    wall_ms = (end - start).total_seconds() * 1000
    timeline = [e for e in state_dict.get("timeline") or [] if isinstance(e, dict)]
    closed = [e for e in timeline if isinstance(e.get("latency_ms"), (int, float))]
    human_ms = sum(e["latency_ms"] for e in closed)
    ledger = [e for e in state_dict.get("ledger") or [] if isinstance(e, dict)]
    agent_ms = sum(
        e["duration_ms"]
        for e in ledger
        if isinstance(e.get("duration_ms"), (int, float))
    )
    overhead_ms = max(wall_ms - human_ms - agent_ms, 0)
    return (
        f"Run took {fmt_dur(wall_ms)}: {fmt_dur(human_ms)} you ({len(closed)} waits), "
        f"{fmt_dur(agent_ms)} agents ({len(ledger)} spawns), {fmt_dur(overhead_ms)} overhead."
    )


def digest(state_dict, state_path, source):
    out = {k: v for k, v in state_dict.items() if k not in LARGE}
    out["relay"] = relay_digest(state_dict.get("relay"))
    timeline = [e for e in state_dict.get("timeline") or [] if isinstance(e, dict)]
    closed = sum(1 for e in timeline if e.get("latency_ms") is not None)
    out["waits"] = {
        "total": len(timeline),
        "open": len(timeline) - closed,
        "human_ms": sum(
            e["latency_ms"]
            for e in timeline
            if isinstance(e.get("latency_ms"), (int, float))
        ),
    }
    ledger = [e for e in state_dict.get("ledger") or [] if isinstance(e, dict)]
    out["spawns"] = {
        "total": len(ledger),
        "agent_ms": sum(
            e["duration_ms"]
            for e in ledger
            if isinstance(e.get("duration_ms"), (int, float))
        ),
    }
    out["decisions"] = veto_list(state_dict)
    out["history_tail"] = (state_dict.get("history") or [])[-3:]
    out["totals_sentence"] = totals_sentence(state_dict)
    analyze = state_dict.get("analyze")
    if isinstance(analyze, dict) and isinstance(analyze.get("pending_clarify"), list):
        out["analyze"] = {**analyze, "pending_clarify": len(analyze["pending_clarify"])}
    out["state_path"] = str(state_path)
    out["source"] = source
    return out


def worktree_states(repo):
    for block in git(repo, "worktree", "list", "--porcelain").split("\n\n"):
        for line in block.splitlines():
            if line.startswith("worktree "):
                worktree = line[len("worktree ") :]
                for path in sorted(Path(worktree).glob("specs/*/factory/state.json")):
                    yield worktree, path
                break


def pending_states(repo):
    home = Path(os.environ.get("FACTORY_HOME", "~/.factory")).expanduser()
    repo_real = os.path.realpath(repo)
    for path in sorted((home / "pending").glob("*.json")):
        loaded, error = state.read_state(path)
        if error:
            print(
                f"factory: skipping unreadable pending file {path}: {error}",
                file=sys.stderr,
            )
            continue
        repo_field = loaded.get("repo")
        if repo_field and os.path.realpath(repo_field) == repo_real:
            yield path, loaded


def find_runs(repo):
    """Every visible copy of every run: a (state_path, state, identity, worktree)
    tuple, or a plain dict for an unreadable worktree state. A run's state rides
    along as a copy into every later worktree branched after it."""
    runs = []
    for worktree, path in worktree_states(repo):
        loaded, error = state.read_state(path)
        if error:
            runs.append(
                {
                    "source": "worktree",
                    "state_path": str(path),
                    "status": "unreadable",
                    "error": error,
                }
            )
            continue
        runs.append(
            (
                path,
                loaded,
                {
                    "source": "worktree",
                    "branch": loaded.get("branch") or path.parents[1].name,
                    "worktree": worktree,  # where this copy was found, not the state's recorded home
                    "spec_dir": loaded.get("spec_dir")
                    or f"specs/{path.parents[1].name}",
                },
                worktree,
            )
        )
    for path, loaded in pending_states(repo):
        runs.append(
            (
                path,
                loaded,
                {"source": "pending", "branch": None, "name": path.stem},
                None,
            )
        )
    return runs


def is_authoritative(run):
    path, loaded, identity, worktree = run
    return bool(
        worktree
        and loaded.get("worktree")
        and os.path.realpath(loaded["worktree"]) == os.path.realpath(worktree)
    )


def deduped(runs):
    """One entry per run: copies sharing a branch collapse onto the copy in the
    worktree the state itself names, else the first seen."""
    picked, order, out = {}, [], []
    for run in runs:
        if isinstance(run, dict):
            out.append(run)
            continue
        key = (run[2]["source"], run[2].get("branch") or run[0].stem)
        if key not in picked:
            order.append(key)
            picked[key] = run
        elif is_authoritative(run) and not is_authoritative(picked[key]):
            picked[key] = run
    return out + [picked[key] for key in order]


def find_matches(repo, name):
    """Every deduped run matching `<name>`: (path, state, source) triples."""
    name = name[:-5] if name.endswith(".json") else name
    matches = []
    for run in deduped(find_runs(repo)):
        if isinstance(run, dict):
            continue
        path, loaded, identity, _ = run
        if identity["source"] == "worktree":
            if name in (loaded.get("branch"), path.parents[1].name):
                matches.append((path, loaded, "worktree"))
        elif name == identity["name"] or identity["name"].endswith(f"-{name}"):
            matches.append((path, loaded, "pending"))
    return matches


def one_run(repo, name):
    """The single run matching `<name>`, refusing none/ambiguous/gone homes."""
    matches = find_matches(repo, name)
    if not matches:
        known = (
            ", ".join(
                sorted(
                    filter(
                        None,
                        (
                            r[1].get("branch") or r[0].stem
                            for r in deduped(find_runs(repo))
                            if not isinstance(r, dict)
                        ),
                    )
                )
            )
            or "none found"
        )
        die(1, f"no run '{name}' in {repo} (runs: {known})")
    if len(matches) > 1:
        listed = ", ".join(str(p) for p, _, _ in matches)
        die(3, f"'{name}' matches several runs: {listed}")
    return matches[0]


def cmd_runs(repo):
    entries = []
    for run in deduped(find_runs(repo)):
        if isinstance(run, dict):  # unreadable worktree state
            entries.append(
                {
                    **run,
                    "violations": [{"location": "state.json", "reason": run["error"]}],
                }
            )
            continue
        path, loaded, identity, _ = run
        violations = state.validate_state(loaded)
        if loaded.get("status") == "pr-open":
            continue
        entries.append(
            {
                **identity,
                "stage": loaded.get("stage"),
                "status": loaded.get("status"),
                "halt_reason": loaded.get("halt_reason"),
                "mode": loaded.get("mode"),
                "feature": loaded.get("feature"),
                "last_activity": last_activity(loaded),
                "state_path": str(path),
                "violations": violations,
            }
        )
    entries.sort(key=lambda e: e.get("last_activity") or "", reverse=True)
    return {"repo": repo, "runs": entries}


def cmd_show(repo, name):
    path, loaded, source = one_run(repo, name)
    home = loaded.get("worktree")
    if source == "worktree" and home and not os.path.isdir(home):
        die(
            4,
            f"run '{name}' records worktree {home}, which no longer exists "
            f"(state found at {path})",
        )
    return digest(loaded, path, source)


def cmd_validate(repo, name=None, all_runs=False):
    """Violations for one run or, with --all, every run; empty list means clean."""
    violations = []
    if all_runs:
        for run in deduped(find_runs(repo)):
            if isinstance(run, dict):
                violations.append(
                    {
                        "run": run.get("state_path"),
                        "location": "state.json",
                        "reason": run["error"],
                    }
                )
                continue
            path, loaded, _, _ = run
            violations.extend(
                {"run": loaded.get("branch") or path.stem, **v}
                for v in state.validate_state(loaded)
            )
        return violations
    if not name:
        die(5, "validate needs a run name or --all")
    _, loaded, _ = one_run(repo, name)
    return state.validate_state(loaded)
