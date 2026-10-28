"""Command implementations for the factory CLI.

Read commands (`runs`, `show`, `validate`) live here; write commands join as
their tasks land. Everything mechanical routes through `state` (and, from
T015, `lock`); this module adds only discovery, digests and CLI errors.
"""

import filecmp
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from factory_cli import budget, checks, improvements, lock, state, totals

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


def digest(state_dict, state_path, source):
    out = {k: v for k, v in state_dict.items() if k not in LARGE}
    out["relay"] = relay_digest(state_dict.get("relay"))
    timeline = [e for e in state_dict.get("timeline") or [] if isinstance(e, dict)]
    closed = sum(1 for e in timeline if e.get("latency_ms") is not None)
    # FR-015: counts only — the elapsed aggregates are the union totals
    out["waits"] = {"total": len(timeline), "open": len(timeline) - closed}
    ledger = [e for e in state_dict.get("ledger") or [] if isinstance(e, dict)]
    out["spawns"] = {"total": len(ledger)}
    out["totals"] = totals.compute(state_dict)
    out["decisions"] = veto_list(state_dict)
    out["history_tail"] = (state_dict.get("history") or [])[-3:]
    out["totals_sentence"] = totals.sentence(totals.compute(state_dict))
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
    repo_real = os.path.realpath(repo)
    for path in sorted((factory_home() / "pending").glob("*.json")):
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
        # FR-017: resume refuses both ended statuses, so runs lists neither
        if loaded.get("status") in ("pr-open", "aborted"):
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


def factory_home():
    """The harness-neutral factory home (${FACTORY_HOME:-~/.factory})."""
    return Path(os.environ.get("FACTORY_HOME", "~/.factory")).expanduser()


def read_config():
    """The user's ${FACTORY_HOME}/config.json, {} when missing or malformed."""
    try:
        return json.loads((factory_home() / "config.json").read_text())
    except (OSError, ValueError):
        return {}


def cmd_budget(role):
    """The role's resolved budget and derived deadline (FR-001); a missing or
    malformed config falls back to the default and never fails."""
    seconds = budget.resolve(role, read_config())
    return {
        "role": role,
        "seconds": seconds,
        "deadline": budget.deadline_for(seconds),
    }


def cmd_improvements():
    """Every ready-or-claimed backlog in the factory home (FR-013)."""
    return improvements.list_backlogs(factory_home())


def cmd_improvements_claim(repo, name):
    """Claim one backlog (FR-012), refusing a source run that has not ended."""
    runs = [
        (r[1].get("branch") or r[0].stem, r[1].get("status"))
        for r in deduped(find_runs(repo))
        if not isinstance(r, dict)
    ]
    try:
        return improvements.claim(factory_home(), name, source_runs=runs)
    except improvements.ClaimError as e:
        die(1, str(e))


# ---------------------------------------------------------------- writers ---
# The single writer (FR-001): every mutation stamps its own time, is
# validated by state.write_state, lands atomically, and commits on worktree
# runs. Lock refusal lands with the lock module (T015); declared-file staging
# with T026; gate checks with T017.


def now_iso():
    return state.iso(datetime.now(timezone.utc))


def cmd_drop(repo, cwd):
    matches = [
        run
        for run in deduped(find_runs(repo))
        if not isinstance(run, dict)
        and run[2]["source"] == "worktree"
        and os.path.realpath(run[2]["worktree"]) == os.path.realpath(cwd)
    ]
    if not matches:
        die(1, f"no run to drop from {cwd}")
    path, loaded, identity, worktree = matches[0]
    if loaded.get("status") != "pr-open":
        die(1, f"run is {loaded.get('status')}; drop needs pr-open")
    target = (
        factory_home()
        / "archive"
        / improvements.backlog_name(repo, loaded["branch"])[:-5]
    )
    try:
        lock.acquire(path, loaded.get("harness") or "unknown")
    except lock.LockHeld as e:
        die(1, str(e))
    try:
        if target.exists():
            die(1, f"archive {target} already exists; refusing to overwrite")
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
        try:
            shutil.copytree(
                path.parent, tmp, ignore=shutil.ignore_patterns("lock.json")
            )
            pending = [filecmp.dircmp(path.parent, tmp, ignore=["lock.json"])]
            problems = []
            while pending:
                comparison = pending.pop()
                problems.extend(
                    str(Path(comparison.left) / name)
                    for name in comparison.left_only
                    + comparison.right_only
                    + comparison.funny_files
                )
                for name in comparison.common_files:
                    left, right = (
                        Path(comparison.left) / name,
                        Path(comparison.right) / name,
                    )
                    if not filecmp.cmp(left, right, shallow=False):
                        problems.append(str(left))
                pending.extend(comparison.subdirs.values())
            if problems:
                raise OSError(", ".join(problems))
            os.rename(tmp, target)
        except OSError as e:
            shutil.rmtree(tmp, ignore_errors=True)
            die(1, f"archive copy failed: {e}")
    finally:
        lock.release(path)
    folder = f"{identity['spec_dir']}/factory"
    try:
        git(worktree, "rm", "-r", "-q", "--", folder)
        git(worktree, "commit", "-q", "-m", "factory: drop run artifacts", "--", folder)
    except CLIError as e:
        git(worktree, "reset", "-q", "HEAD", "--", folder)
        git(worktree, "checkout", "-q", "HEAD", "--", folder)
        shutil.rmtree(target, ignore_errors=True)
        die(1, str(e))
    shutil.rmtree(path.parent, ignore_errors=True)
    return {
        "dropped": folder,
        "archive": str(target),
        "design": None,
        "commit": git(worktree, "rev-parse", "--short", "HEAD").strip(),
        "pr_url": loaded.get("pr_url"),
        "totals_sentence": totals.sentence(totals.compute(loaded)),
        "dropped_at": now_iso(),
    }


def resolve_target(repo, cwd):
    """The one run this session writes: the worktree run whose home is `cwd`,
    else the repo's single pending run. Ended runs are never writable."""
    cwd_real = os.path.realpath(str(cwd))
    worktree_matches = []
    for run in deduped(find_runs(repo)):
        if isinstance(run, dict):
            continue
        path, loaded, identity, _ = run
        if loaded.get("status") in ("pr-open", "aborted"):
            continue
        if (
            identity["source"] == "worktree"
            and os.path.realpath(identity["worktree"] or "") == cwd_real
        ):
            worktree_matches.append((path, loaded, "worktree", identity["worktree"]))
    if len(worktree_matches) > 1:
        die(3, f"several runs claim {cwd}")
    if worktree_matches:
        return worktree_matches[0]
    pending = [
        (path, loaded, "pending", None)
        for run in deduped(find_runs(repo))
        if not isinstance(run, dict)
        for path, loaded, identity, _ in [run]
        if identity["source"] == "pending"
    ]
    if len(pending) > 1:
        die(3, f"several pending runs of {repo}; name one")
    if not pending:
        die(1, f"no run to write from {cwd} in {repo}")
    if pending[0][1].get("status") in ("pr-open", "aborted"):
        # FR-009: the ended-status skip applies to pending selection too —
        # an ended pending run is as unwritable as an ended worktree run
        die(
            1,
            f"run is {pending[0][1].get('status')} and has ended; it is not writable",
        )
    return pending[0]


def write_run(path, loaded, mutate):
    try:
        return state.write_state(path, loaded, mutate=mutate)
    except lock.LockHeld as e:
        die(1, str(e))
    except state.StateError as e:
        die(1, str(e))


def commit_worktree(worktree, message, spec_dir=None, extra=()):
    """Stage spec_dir (plus the checkpoint's declared extras) and commit.
    Undeclared changes are never staged (FR-017)."""
    if not worktree:
        return None
    add = [path for path in ([spec_dir] if spec_dir else []) if path] + list(extra)
    if add:
        git(worktree, "add", "--", *add)
    git(worktree, "commit", "-q", "-m", message)
    return git(worktree, "rev-parse", "--short", "HEAD").strip()


def successor(stage):
    order = state.STAGES
    return (
        order[order.index(stage) + 1]
        if stage in order and order.index(stage) + 1 < len(order)
        else None
    )


def settled_answers(relay, fallback_stage, now):
    """Every settled answer of the stage's relay, as decision records (FR-008).

    Stamped with the checkpoint's own `now`: decisions are validated
    non-decreasing, so keeping each answer's original time could place a
    migrated record before an existing decision and refuse every retry.
    """
    migrated = []
    for one_round in rounds_of(relay):
        for qid, answer in (one_round.get("answers") or {}).items():
            if isinstance(answer, dict):
                migrated.append(
                    {
                        "stage": fallback_stage,
                        "question": qid,
                        "answer": answer.get("answer"),
                        "auto": bool(answer.get("auto")),
                        "at": now,
                        "kind": "answer",
                    }
                )
            else:  # legacy version 2 string answer
                migrated.append(
                    {
                        "stage": fallback_stage,
                        "question": qid,
                        "answer": str(answer),
                        "auto": False,
                        "at": now,
                        "kind": "answer",
                    }
                )
    return migrated


def read_envelope(path):
    """Read a role's final fenced block or a bare JSON file."""
    try:
        text = Path(path).read_text()
    except OSError as e:
        die(1, f"cannot read {path}: {e}")
    block, error = checks.extract_block(text)
    if error:
        try:
            block = json.loads(text)
        except ValueError:
            die(1, f"{path}: {error}")
    return block


def declared_from_envelope(path):
    """The envelope's `files` list, from a role output or a bare JSON file (FR-017)."""
    block = read_envelope(path)
    files = block.get("files") if isinstance(block, dict) else None
    if not isinstance(files, list) or not all(isinstance(f, str) and f for f in files):
        die(1, f"{path}: the envelope carries no list of declared files in `files`")
    return files


def dirty_paths(worktree):
    status = git(worktree, "status", "--porcelain", "--untracked-files=all")
    return [line[3:].strip().strip('"') for line in status.splitlines() if line.strip()]


def cmd_checkpoint(repo, cwd, stage, next_stage=None, files=None, envelope=None):
    if stage not in state.STAGES:
        die(
            1,
            f"'{stage}' is off-vocabulary; expected one of: {', '.join(state.STAGES)}",
        )
    if next_stage is not None and next_stage not in state.STAGES:
        die(1, f"next stage '{next_stage}' is off-vocabulary")
    path, loaded, source, worktree = resolve_target(repo, cwd)
    now = now_iso()
    target = next_stage or successor(stage)
    # Every refusal point passes before the state write, so a refused
    # checkpoint leaves the stage, history, relay and worktree untouched.
    declared = list(files or [])
    if envelope:
        declared = declared + declared_from_envelope(envelope)
    if worktree:
        missing = [f for f in declared if not (Path(worktree) / f).exists()]
        if missing:
            die(1, f"declared files do not exist in the worktree: {', '.join(missing)}")

    def mutate(s):
        if target:
            violation = checks.gate_violation(s, target)
            if violation:
                die(1, f"gate refusal into '{target}': {violation}")
        permitted = checks.permitting_decision(s, target) if target else None
        relay = s.get("relay")
        relay_stage = (
            relay.get("stage")
            if isinstance(relay, dict) and relay.get("stage")
            else s.get("stage")
        )
        decisions = s.get("decisions") or []
        if isinstance(relay, dict):
            decisions = decisions + settled_answers(relay, relay_stage, now)
        s["decisions"] = decisions
        s["relay"] = None
        history = s.get("history") or []
        pending = history[-1] if history else None
        if pending and pending.get("stage") == stage and pending.get("commit") is None:
            # FR-011: a retry of a stage whose commit never landed reuses the
            # pending entry instead of appending a second one
            pending["at"] = now
        else:
            entry = {
                "at": now,
                "stage": stage,
                "event": permitted["kind"] if permitted else "complete",
                "commit": None,
                "harness": s.get("harness"),
            }
            if permitted:
                entry["decision"] = permitted["question"]
            history = history + [entry]
        s["history"] = history
        if target:
            s["stage"] = target
        return s

    updated = write_run(path, loaded, mutate)
    undeclared = []
    commit = None
    if worktree:
        spec_prefix = (updated.get("spec_dir") or "").rstrip("/") + "/"
        dirty = dirty_paths(worktree)
        in_spec = [p for p in dirty if p.startswith(spec_prefix)]
        undeclared = [p for p in dirty if p not in declared and p not in in_spec]
        try:
            commit = commit_worktree(
                worktree,
                f"factory: {stage} complete",
                spec_dir=updated.get("spec_dir"),
                extra=declared,
            )
        except CLIError as e:
            reason = str(e)
            print(f"factory: state written, commit failed: {reason}", file=sys.stderr)
            return {
                "checkpointed": stage,
                "stage": updated["stage"],
                "commit": None,
                "commit_error": reason,
                "declared": declared,
                "undeclared": undeclared,
                "source": source,
            }
        # FR-011: a retried checkpoint fills the reused pending entry with the
        # commit that finally landed (a fresh checkpoint appends a new entry)
        reused = len(updated.get("history") or []) == len(loaded.get("history") or [])
        if commit and reused and updated.get("history"):

            def stamp(s):
                trailing = s.get("history") or []
                if trailing and trailing[-1].get("stage") == stage:
                    trailing[-1]["commit"] = commit
                return s

            write_run(path, updated, stamp)
    return {
        "checkpointed": stage,
        "stage": updated["stage"],
        "commit": commit,
        "declared": declared,
        "undeclared": undeclared,
        "source": source,
    }


def cmd_analyze_record(repo, cwd, envelope):
    """Persist a validated analysis result without bypassing transition gates."""
    path, loaded, source, worktree = resolve_target(repo, cwd)
    block = read_envelope(envelope)
    problems = checks.block_problems(block, "envelope")
    if problems:
        die(1, f"invalid analysis envelope: {problems}")
    if block.get("stage") != "analyze" or block.get("status") != "done":
        die(1, "analyze-record requires a completed analyze envelope")
    result = block.get("analyze")
    if not isinstance(result, dict):
        die(1, "analysis envelope must carry analyze counts and report")
    for severity in ("critical", "high", "medium", "low"):
        value = result.get(severity)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            die(1, f"analyze.{severity} must be a non-negative integer")
    report = result.get("report")
    if not worktree or not isinstance(report, str) or not report:
        die(1, "analyze-record requires a worktree and report path")
    relative = Path(report)
    if relative.is_absolute() or ".." in relative.parts:
        die(1, "analysis report must be relative to the spec directory or worktree")
    spec_dir = Path(loaded["spec_dir"])
    root = (Path(worktree) / spec_dir).resolve()
    candidate = (
        Path(worktree) / relative
        if relative.is_relative_to(spec_dir)
        else root / relative
    )
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        die(1, "analysis report must exist inside the run's spec directory")
    normalized = str(resolved.relative_to(root))
    counts = {k: result[k] for k in ("critical", "high", "medium", "low")}
    recorded_at = now_iso()

    def mutate(s):
        analyze = dict(s.get("analyze") or {})
        reports = list(analyze.get("reports") or [])
        if normalized not in reports:
            reports.append(normalized)
        analyze["reports"] = reports
        analyze["result"] = {**counts, "report": normalized, "at": recorded_at}
        s["analyze"] = analyze
        return s

    write_run(path, loaded, mutate)
    commit_worktree(worktree, "factory: analyze-record", loaded.get("spec_dir"))
    return {
        "recorded": normalized,
        "counts": counts,
    }


def append_issue(state_dict, record):
    """The single issue append path (FR-008): one record per event onto the
    append-only `issues` list. Returns the record now in the list."""
    issues = state_dict.get("issues") or []
    record = dict(record)
    issues.append(record)
    state_dict["issues"] = issues
    return record


def stall_rule(state_dict, stage, cap=3):
    """The stall rule result over every record marked `partial_return: true`
    of `stage` (FR-004): trailing marked records sharing one `commit`; any
    new commit resets the count. Records of other stages never break the
    chain, and unmarked records (failure-policy retries, post-hoc
    detections) add nothing."""
    trailing, commit = 0, None
    for entry in reversed(state_dict.get("issues") or []):
        if not isinstance(entry, dict) or entry.get("stage") != stage:
            continue
        if not entry.get("partial_return"):
            continue
        if commit is None:
            commit = entry.get("commit")
        elif entry.get("commit") != commit:
            break
        trailing += 1
    return {
        "stage": stage,
        "consecutive_no_commit": trailing,
        "cap": cap,
        "halt": trailing >= cap,
    }


def cmd_issue_add(
    repo,
    cwd,
    kind,
    stage,
    role,
    detail,
    duration_ms,
    cause=None,
    commit=None,
    partial_return=False,
):
    """Append one issue (FR-008); a marked record reports the stall rule."""
    if kind not in state.ISSUE_KINDS:
        die(
            1,
            f"'{kind}' is off-vocabulary; expected one of: {', '.join(state.ISSUE_KINDS)}",
        )
    if stage not in state.STAGES:
        die(
            1,
            f"'{stage}' is off-vocabulary; expected one of: {', '.join(state.STAGES)}",
        )
    if kind == "overrun" and cause not in state.OVERRUN_CAUSES:
        die(
            1,
            f"overrun needs --cause from: {', '.join(state.OVERRUN_CAUSES)}"
            f" (got {cause!r})",
        )
    if kind != "overrun":
        cause = None  # stored null for kinds other than overrun
    if partial_return and (
        kind not in state.PARTIAL_RETURN_KINDS or role not in state.PARTIAL_RETURN_ROLES
    ):
        die(
            1,
            "the partial_return mark is accepted only for overrun/retry of "
            "the file-writing roles (spec-builder, code-build, fixer)",
        )
    path, loaded, source, worktree = resolve_target(repo, cwd)
    record = {
        "at": now_iso(),
        "kind": kind,
        "stage": stage,
        "role": role,
        "cause": cause,
        "detail": detail,
        "duration_ms": duration_ms,
        "commit": commit,
        "partial_return": bool(partial_return),
    }
    if record["commit"] is None and worktree:
        record["commit"] = worktree_work_commit(worktree)

    def mutate(s):
        append_issue(s, record)
        return s

    updated = write_run(path, loaded, mutate)
    commit_worktree(
        worktree, f"factory: issue-add {kind} {stage}", loaded.get("spec_dir")
    )
    result = {"added": {"kind": kind, "stage": stage, "role": role}}
    if record["partial_return"]:
        result["stalls"] = stall_rule(updated, stage)
    return result


def cmd_ledger_add(
    repo,
    cwd,
    stage,
    role,
    started_at=None,
    ended_at=None,
    in_est=0,
    out_est=0,
    reported=None,
    overrun=None,
    partial_return=False,
):
    path, loaded, source, worktree = resolve_target(repo, cwd)
    now = now_iso()
    start, end = started_at or now, ended_at or started_at or now
    duration = max(
        int((state.parse_iso(end) - state.parse_iso(start)).total_seconds() * 1000), 0
    )
    issue = overrun_issue(
        loaded, worktree, stage, role, duration, overrun, partial_return
    )

    def mutate(s):
        s["ledger"] = (s.get("ledger") or []) + [
            {
                "at": now,
                "stage": stage,
                "role": role,
                "harness": s.get("harness"),
                "in_est": in_est,
                "out_est": out_est,
                "reported": reported,
                "duration_ms": duration,
                "started_at": start,
                "ended_at": end,
            }
        ]
        if issue is not None:
            # self-report and detection meet in overrun_issue: one spawn,
            # one record (FR-006); every call is a distinct spawn
            append_issue(s, issue)
        return s

    updated = write_run(path, loaded, mutate)
    commit_worktree(worktree, f"factory: ledger-add {stage}", loaded.get("spec_dir"))
    result = {"added": {"stage": stage, "role": role, "duration_ms": duration}}
    if issue is not None:
        result["issue"] = issue
        if issue["partial_return"]:
            result["stalls"] = stall_rule(updated, stage)
    return result


def overrun_issue(loaded, worktree, stage, role, duration, overrun, partial_return):
    """The one issue a ledger-add records (FR-006), or None: the self-report
    wins; else a duration over the role's budget yields cause `unreported`;
    neither signal records nothing. `--partial-return` marks the spawn as a
    partial return, subject to the shared mark rules."""
    if partial_return and role not in state.PARTIAL_RETURN_ROLES:
        die(
            1,
            "the partial_return mark is accepted only for overrun/retry of "
            "the file-writing roles (spec-builder, code-build, fixer)",
        )
    cause = detail = None
    if overrun is not None:
        if not isinstance(overrun, dict):
            die(1, "--overrun needs a JSON object with cause and detail")
        cause = overrun.get("cause")
        detail = overrun.get("detail")
        if cause not in state.OVERRUN_CAUSES:
            die(
                1,
                f"--overrun cause {cause!r} is off-vocabulary; expected one "
                f"of: {', '.join(state.OVERRUN_CAUSES)}",
            )
        if not isinstance(detail, str) or not detail:
            die(1, "--overrun needs a non-empty detail")
    else:
        seconds = budget.resolve(role, read_config())
        if duration <= seconds * 1000:
            return None
        cause = "unreported"
        detail = (
            f"{role} ran {duration // 1000}s past its {seconds}s budget "
            "without a self-report"
        )
    record = {
        "at": now_iso(),
        "kind": "overrun",
        "stage": stage,
        "role": role,
        "cause": cause,
        "detail": detail,
        "duration_ms": duration,
        "commit": None,
        "partial_return": bool(partial_return),
    }
    if record["commit"] is None and worktree:
        record["commit"] = worktree_work_commit(worktree)
    return record


def cmd_wait_open(repo, cwd, kind, stage, summary):
    path, loaded, source, worktree = resolve_target(repo, cwd)
    now = now_iso()

    def mutate(s):
        s["timeline"] = (s.get("timeline") or []) + [
            {
                "at": now,
                "kind": kind,
                "stage": stage,
                "summary": summary,
                "answered_at": None,
                "latency_ms": None,
            }
        ]
        return s

    updated = write_run(path, loaded, mutate)
    commit_worktree(worktree, f"factory: wait-open {stage}", loaded.get("spec_dir"))
    return {"wait-id": len(updated["timeline"]) - 1}


def cmd_wait_close(repo, cwd, wait_id):
    path, loaded, source, worktree = resolve_target(repo, cwd)
    now = now_iso()

    def mutate(s):
        timeline = list(s.get("timeline") or [])
        if not 0 <= wait_id < len(timeline):
            die(1, f"no wait #{wait_id} (timeline has {len(timeline)} entries)")
        entry = dict(timeline[wait_id])
        if entry.get("answered_at"):
            die(1, f"wait #{wait_id} is already closed")
        answered = state.parse_iso(now)
        opened = state.parse_iso(entry.get("at"))
        entry["answered_at"] = now
        entry["latency_ms"] = (
            max(int((answered - opened).total_seconds() * 1000), 0) if opened else 0
        )
        timeline[wait_id] = entry
        s["timeline"] = timeline
        return s

    write_run(path, loaded, mutate)
    commit_worktree(worktree, "factory: wait-close", loaded.get("spec_dir"))
    return {"closed": wait_id}


def cmd_answer(repo, cwd, qid, answer, auto=False, stage=None):
    path, loaded, source, worktree = resolve_target(repo, cwd)
    now = now_iso()

    def mutate(s):
        relay = s.get("relay") if isinstance(s.get("relay"), dict) else {}
        rounds = rounds_of(relay) or [{"questions": [], "answers": {}}]
        last = dict(rounds[-1])
        questions = list(last.get("questions") or [])
        if not any(isinstance(q, dict) and q.get("id") == qid for q in questions):
            questions.append({"id": qid})
        last["questions"] = questions
        answers = dict(last.get("answers") or {})
        answers[qid] = {"answer": answer, "at": now, "auto": bool(auto)}
        last["answers"] = answers
        s["relay"] = {
            "stage": stage or relay.get("stage") or s.get("stage"),
            "rounds": rounds[:-1] + [last],
        }
        return s

    write_run(path, loaded, mutate)
    commit_worktree(worktree, f"factory: answer {qid}", loaded.get("spec_dir"))
    return {"answered": qid, "auto": bool(auto)}


def worktree_work_commit(worktree):
    """The worktree's latest non-`factory:` commit, or None without one.

    The writers' own `factory:` commits move HEAD on every call, so the stall
    rule (FR-004) keys on the last commit the work itself made."""
    if not worktree:
        return None
    out = git(
        worktree,
        "log",
        "-1",
        "--format=%h",
        "--grep=^factory:",
        "--invert-grep",
    ).strip()
    return out or None


def cmd_set_status(repo, cwd, status, halt_reason=None, pr_url=None):
    if status not in state.STATUSES:
        die(
            1,
            f"'{status}' is off-vocabulary; expected one of: {', '.join(state.STATUSES)}",
        )
    path, loaded, source, worktree = resolve_target(repo, cwd)
    now = now_iso()
    if status == "halted" and not halt_reason:
        die(1, "set-status halted needs --halt-reason")
    if status == "pr-open" and not pr_url:
        die(1, "set-status pr-open needs --pr-url")
    issue = None
    if status == "halted":
        issue = {
            "at": now,
            "kind": "halt",
            "stage": loaded.get("stage"),
            "role": "orchestrator",
            "cause": None,
            "detail": halt_reason,
            "duration_ms": 0,
            "commit": worktree_work_commit(worktree),
            "partial_return": False,
        }

    def mutate(s):
        s["status"] = status
        if status == "halted":
            s["halt_reason"] = halt_reason
            append_issue(s, issue)
        if status == "pr-open":
            s["pr_url"] = pr_url
        if status in ("pr-open", "aborted"):
            s["ended_at"] = now
            s["history"] = (s.get("history") or []) + [
                {
                    "at": now,
                    "stage": "pr" if status == "pr-open" else s.get("stage"),
                    "event": status,
                    "commit": None,
                    "harness": s.get("harness"),
                }
            ]
        return s

    updated = write_run(path, loaded, mutate)
    commit_worktree(worktree, f"factory: set-status {status}", loaded.get("spec_dir"))
    result = {"status": status}
    if status in ("pr-open", "aborted"):
        # FR-011: the structural gate — the backlog file exists only from here
        result["improvements"] = str(improvements.export(factory_home(), updated))
    return result


def cmd_decisions_add(repo, cwd, stage, qid, answer, kind="answer"):
    if kind not in state.DECISION_KINDS:
        die(
            1,
            f"'{kind}' is off-vocabulary; expected one of: {', '.join(state.DECISION_KINDS)}",
        )
    path, loaded, source, worktree = resolve_target(repo, cwd)
    now = now_iso()

    def mutate(s):
        s["decisions"] = (s.get("decisions") or []) + [
            {
                "stage": stage,
                "question": qid,
                "answer": answer,
                "auto": False,
                "at": now,
                "kind": kind,
            }
        ]
        return s

    write_run(path, loaded, mutate)
    commit_worktree(worktree, f"factory: decisions-add {qid}", loaded.get("spec_dir"))
    return {"added": {"stage": stage, "question": qid, "kind": kind}}


def cmd_lock_take(repo, name, force=False):
    """Explicit takeover of a run's lock (FR-005); refuses a live lock unless --force."""
    path, loaded, source = one_run(repo, name)
    try:
        info = lock.take(path, harness=loaded.get("harness") or "unknown", force=force)
    except lock.LockHeld as e:
        die(1, str(e))
    return {
        "taken": name,
        "lock_path": str(lock.lock_path_for(path)),
        "taken_over": info["taken_over"],
        "previous_owner": info["previous"],
    }


def cmd_verify(repo, cwd, passed, commands_payload):
    """The verify record (FR-006, R3): the review gate reads the latest one."""
    path, loaded, source, worktree = resolve_target(repo, cwd)
    now = now_iso()
    event = "verify-pass" if passed else "verify-fail"
    issue = None
    if not passed:
        failing = [c for c, st in commands_payload if st]
        issue = {
            "at": now,
            "kind": "verify-fail",
            "stage": loaded.get("stage"),
            "role": "orchestrator",
            "cause": None,
            "detail": ", ".join(failing or [c for c, _ in commands_payload]),
            "duration_ms": 0,
            "commit": worktree_work_commit(worktree),
            "partial_return": False,
        }

    def mutate(s):
        if issue is not None:
            append_issue(s, issue)
        s["history"] = (s.get("history") or []) + [
            {
                "at": now,
                "stage": s.get("stage"),
                "event": event,
                "commit": None,
                "harness": s.get("harness"),
                "commands": [
                    {"command": c, "status": st} for c, st in commands_payload
                ],
            }
        ]
        return s

    write_run(path, loaded, mutate)
    commit_worktree(worktree, f"factory: {event}", loaded.get("spec_dir"))
    return {"verified": event, "commands": commands_payload}


def cmd_envelope_check(path):
    """Validate a role output's final fenced json block (FR-007)."""
    try:
        text = Path(path).read_text()
    except OSError as e:
        die(1, f"cannot read {path}: {e}")
    block, error = checks.extract_block(text)
    if error:
        die(1, error)
    shape = checks.detect_shape(block)
    if shape is None:
        die(
            1,
            "the final fenced json block matches no role-output shape "
            "(envelope, reviewer report, judge verdict)",
        )
    problems = checks.block_problems(block, shape)
    if problems:
        die(
            1,
            "malformed "
            + shape
            + " block: "
            + "; ".join(f"{p['location']}: {p['reason']}" for p in problems),
        )
    return {"shape": shape, "problems": 0}


def cmd_rebind(repo, cwd, name, worktree):
    """Rewrite a moved run's stored paths (FR-012): the target must be a git
    worktree on the recorded branch; sharing ${FACTORY_HOME} alone never moves a run."""
    target = Path(worktree)
    if not target.is_dir():
        die(4, f"the run's worktree {target} does not exist")
    probe = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        die(4, f"{target} is not a git worktree")
    path, loaded, source = one_run(repo, name)
    if loaded.get("status") in ("pr-open", "aborted"):
        die(
            1,
            f"run '{name}' is {loaded.get('status')} and has ended; nothing to rebind",
        )
    branch = loaded.get("branch")
    if branch:
        current = git(str(target), "branch", "--show-current").strip()
        if current != branch:
            die(1, f"{target} is on branch '{current}'; the run records '{branch}'")
    rebound_worktree = str(target.resolve())
    rebound_repo = main_repo(target)

    def mutate(current):
        # applied to the state freshly read under the run's lock (FR-008)
        current["worktree"] = rebound_worktree
        current["repo"] = rebound_repo
        return current

    write_run(path, loaded, mutate)
    commit_worktree(
        str(target), f"factory: rebind {branch}", spec_dir=loaded.get("spec_dir")
    )
    return {
        "rebound": name,
        "worktree": rebound_worktree,
        "repo": rebound_repo,
        "previous_worktree": loaded.get("worktree"),
    }


def cmd_resume(repo, name):
    """Record the `resumed` history entry through the writer and return the
    resume digest: the recorded stage restarts from its beginning (FR-003)."""
    path, loaded, source = one_run(repo, name)
    if loaded.get("status") in ("pr-open", "aborted"):
        die(
            1,
            f"run '{name}' is {loaded.get('status')} and has ended; there is nothing to resume",
        )
    now = now_iso()

    def mutate(s):
        s["status"] = "running"
        s["halt_reason"] = None
        s["history"] = (s.get("history") or []) + [
            {
                "at": now,
                "stage": s.get("stage"),
                "event": "resumed",
                "commit": None,
                "harness": s.get("harness"),
            }
        ]
        return s

    updated = write_run(path, loaded, mutate)
    worktree = updated.get("worktree")
    if source == "worktree" and worktree:
        commit_worktree(
            worktree, f"factory: resume {name}", spec_dir=updated.get("spec_dir")
        )
    return digest(updated, path, source)


def stale_pending_files():
    """Stale pending files (FR-019): the run's state home has moved into a
    worktree (the pending state records one) or the run has ended
    (pr-open/aborted). A run whose only state is the pending file — no
    recorded worktree, still running — is never stale."""
    home = factory_home()
    stale = []
    for path in sorted((home / "pending").glob("*.json")):
        loaded, error = state.read_state(path)
        if error:
            continue  # never delete what cannot be read
        if loaded.get("worktree") or loaded.get("status") in ("pr-open", "aborted"):
            stale.append(path)
    return stale


def cmd_prune(delete=False):
    """Preview stale pending files; deletion only with --delete (FR-019)."""
    stale = [str(p) for p in stale_pending_files()]
    deleted = []
    if delete:
        for path in stale:
            Path(path).unlink()
            deleted.append(path)
    return {"stale": stale, "deleted": deleted}
