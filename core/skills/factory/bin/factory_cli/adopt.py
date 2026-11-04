"""Adopt a spec factory did not start (spec 022): source inspection and the dry-run report.

`inspect` is the one read-only resolution of a source: shape, spec dir, artifacts,
dirty paths, inferred stage and refusal, all from git refs. It never fetches,
checks out or writes; the write re-runs it under the pending lock (D7).
"""

import posixpath
import subprocess
from pathlib import Path

from factory_cli import commands, lock, state

NEEDS_CLARIFICATION = "[NEEDS CLARIFICATION"
NO_BASE = (
    "no base ref resolves (origin/HEAD unset, no origin/main or origin/master); "
    "set origin/HEAD with `git remote set-head origin -a`"
)


def _try(repo, *args):
    """Stdout of a git probe, or None when git exits non-zero (an absent ref or path)."""
    out = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else None


def default_base(repo):
    """The `base` a dry run reports (D3): the first existing of origin's default branch, origin/main,
    origin/master, and main when the repo has no origin; None when none exists, so the caller refuses by name."""
    candidates = []
    head = _try(repo, "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD")
    if head:
        candidates.append(head.strip())
    candidates += ["refs/remotes/origin/main", "refs/remotes/origin/master"]
    if _try(repo, "config", "--get", "remote.origin.url") is None:
        candidates.append("refs/heads/main")
    for ref in candidates:
        if _try(repo, "show-ref", "--verify", "--quiet", ref) is not None:
            return ref.removeprefix("refs/remotes/").removeprefix("refs/heads/")
    return None


def _checkouts(repo):
    """(path, branch) for every checkout of the repo; branch is None when detached."""
    found = []
    for block in commands.git(repo, "worktree", "list", "--porcelain").split("\n\n"):
        path = branch = None
        for line in block.splitlines():
            if line.startswith("worktree "):
                path = line[len("worktree ") :]
            elif line.startswith("branch refs/heads/"):
                branch = line[len("branch refs/heads/") :]
        if path:
            found.append((path, branch))
    return found


def _resolve(repo, src, base):
    """(shape, branch, ref) for `src` (D2), or None when nothing matches.

    In order: a local branch named `src`; origin's branch named `src` (as held, never
    fetched); a local branch matching the spec-dir name (a `specs/` prefix is dropped);
    a spec dir on `base` matching it, whose branch is named after the dir. Matching is
    `commands.name_matches`; several matches in one step exit 3 (ambiguous).
    """
    if _try(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{src}") is not None:
        return "branch", src, f"refs/heads/{src}"
    if _try(repo, "show-ref", "--verify", "--quiet", f"refs/remotes/origin/{src}") is not None:
        return "remote-branch", src, f"refs/remotes/origin/{src}"
    name = src.removeprefix("specs/")
    branches = commands.git(
        repo, "for-each-ref", "--format=%(refname:lstrip=2)", "refs/heads/"
    ).splitlines()
    matches = sorted(b for b in branches if commands.name_matches(b, name))
    if len(matches) > 1:
        commands.die(3, f"'{src}' matches several branches: {', '.join(matches)}")
    if matches:
        return "branch", matches[0], f"refs/heads/{matches[0]}"
    dirs = [d for d in _entries(repo, base, "specs") if commands.name_matches(d, name)]
    if len(dirs) > 1:
        commands.die(3, f"'{src}' matches several spec dirs on {base}: {', '.join(dirs)}")
    if dirs:
        return "default-branch", dirs[0], base
    return None


def _unmatched(repo, src, base):
    """Why `src` matched nothing. A spec dir only on the local default branch gets its own reason (clarify Q2)."""
    name = src.removeprefix("specs/")
    local = base.removeprefix("origin/")
    if _try(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{local}") is not None and any(
        commands.name_matches(d, name) for d in _entries(repo, f"refs/heads/{local}", "specs")
    ):
        return f"spec dir is on local '{local}' but not on '{base}'; push it or create its branch first"
    return f"no branch or spec dir matches '{src}'"


def _spec_dir(repo, ref, branch, base):
    """The branch's spec dir (D2): `specs/<branch>` when present, else the one `specs/` dir it adds over base."""
    own = f"specs/{branch}"
    if _entries(repo, ref, own):
        return own
    added = commands.git(repo, "diff", "--name-only", f"{base}...{ref}", "--", "specs/")
    dirs = sorted({"/".join(path.split("/")[:2]) for path in added.splitlines() if path.count("/") >= 2})
    if len(dirs) > 1:
        commands.die(3, f"'{branch}' adds several spec dirs: {', '.join(dirs)}")
    return dirs[0] if dirs else own


def _entries(repo, ref, directory):
    """Names directly inside `directory` at `ref`; empty when the directory is absent."""
    listing = commands.git(repo, "ls-tree", "--name-only", ref, "--", f"{directory}/")
    return sorted(posixpath.basename(line) for line in listing.splitlines())


def _stage(artifacts):
    """The entry stage the artifacts imply (FR-008, D6)."""
    if "tasks.md" in artifacts:
        return "analyze"
    if "plan.md" in artifacts:
        return "tasks"
    return "plan"


def _dirty(repo, spec_dir, branch):
    """Uncommitted paths (D5): the spec dir in the main checkout, and every checkout of `branch`."""
    dirty = {p for p in commands.dirty_paths(repo) if p.startswith(f"{spec_dir}/")}
    for path, held in _checkouts(repo):
        if held == branch:
            dirty.update(commands.dirty_paths(path))
    return sorted(dirty)


def _markers(repo, ref, spec_dir):
    """The `[NEEDS CLARIFICATION` lines of the spec at `ref`, stripped; empty without spec.md."""
    text = _try(repo, "show", f"{ref}:{spec_dir}/spec.md")
    if text is None:
        return []
    return [line.strip() for line in text.splitlines() if NEEDS_CLARIFICATION in line]


def _no_link(worktree, path):
    """Refuse a symlink on the way to `path` in the checkout: the write never follows one (SEC-1)."""
    current = worktree
    for part in path.relative_to(worktree).parts:
        current = current / part
        if current.is_symlink():
            commands.die(1, f"{current.relative_to(worktree)} is a symlink in the checkout; refusing to write through it")


def _factory_problem(repo, ref, spec_dir):
    """Why `<spec_dir>/factory` at `ref` cannot take the adopted files, or None (SEC-1).

    The folder must be absent or a real directory, and hold no symlink anywhere under it."""
    folder = f"{spec_dir}/factory"
    links = [
        line.split("\t", 1)[1]
        for line in commands.git(repo, "ls-tree", "-r", ref, "--", folder).splitlines()
        if line.startswith("120000 ")
    ]
    if links:
        return f"{links[0]} is a symlink on the branch; adopt never writes through links"
    entry = commands.git(repo, "ls-tree", ref, "--", folder).split()
    if entry and entry[1] != "tree":
        return f"{folder} is not a directory on the branch"
    return None


def _refusal(repo, report, ref):
    """The first refusal reason in D5's order, or None; `dirty` already lists every path."""
    branch, spec_dir = report["branch"], report["spec_dir"]
    own = f"{report['pending']}.json"
    others = [path.name for path, _ in commands.pending_states(repo) if path.name != own]
    if others:
        return f"another pending run '{others[0]}' exists for this repo; resume it or prune it first"
    if report["dirty"]:
        return "uncommitted changes: " + ", ".join(report["dirty"])
    state_path = f"{ref}:{spec_dir}/factory/state.json"
    if _try(repo, "cat-file", "-e", state_path) is not None:
        return f"{spec_dir} already has factory/state.json; resume it with `resume {branch}`"
    if "spec.md" not in report["artifacts"]:
        return f"spec.md is required; {spec_dir} has none on '{branch}'"
    problem = _factory_problem(repo, ref, spec_dir)
    if problem:
        return problem
    for path, held in _checkouts(repo):
        if held == branch:
            return f"'{branch}' is checked out at {path}; switch that checkout away from it first"
    if Path(report["worktree"]).exists():
        return f"worktree path {report['worktree']} already exists"
    return None


def inspect(repo, src, base):
    """The adoption report for `src` (contracts/cli.md); `refusal` is set when refused."""
    report = {
        "source": src,
        "shape": None,
        "branch": None,
        "spec_dir": None,
        "base": base,
        "artifacts": [],
        "dirty": [],
        "inferred_stage": None,
        "needs_clarification": [],
        "worktree": None,
        "pending": None,
        "refusal": None,
    }
    if _try(repo, "check-ref-format", "--branch", src) is None:
        report["refusal"] = f"'{src}' is not a valid branch name"
        return report
    if base is None:
        report["refusal"] = NO_BASE
        return report
    if _try(repo, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}") is None:
        report["refusal"] = f"base '{base}' does not resolve"
        return report
    found = _resolve(repo, src, base)
    if found is None:
        report["refusal"] = _unmatched(repo, src, base)
        return report
    shape, branch, ref = found
    spec_dir = _spec_dir(repo, ref, branch, base)
    artifacts = _entries(repo, ref, spec_dir)
    name = Path(repo).name
    report.update(
        shape=shape,
        branch=branch,
        spec_dir=spec_dir,
        artifacts=artifacts,
        dirty=_dirty(repo, spec_dir, branch),
        inferred_stage=_stage(artifacts),
        needs_clarification=_markers(repo, ref, spec_dir),
        worktree=str(Path(repo).parent / f"{name}-factory" / branch),
        pending=f"{name}-adopt-{branch}",
    )
    report["refusal"] = _refusal(repo, report, ref)
    return report


def write(repo, src, stage=None):
    """Adopt `src` into a worktree run (D7): the pending adoption's lock is held for the whole write.

    Refusals before the worktree exists exit 1 with nothing written; the pending file,
    brief and profile are removed only after the adoption commit lands.
    """
    probe = inspect(repo, src, default_base(repo))
    if probe["branch"] is None:
        commands.die(1, probe["refusal"])
    name = probe["pending"]
    pending = commands.factory_home() / "pending" / f"{name}.json"
    if not pending.exists():
        commands.die(1, f"no pending adoption '{name}'; start it with adopt {src}")
    try:
        lock.acquire(pending, harness="unknown")
    except lock.LockHeld as e:
        commands.die(1, str(e))
    try:
        loaded, error = state.read_state(pending)
        if error:
            commands.die(1, f"pending adoption '{name}' is unreadable: {error}")
        if loaded.get("status") in ("aborted", "pr-open"):
            commands.die(1, f"pending adoption '{name}' is {loaded['status']} and has ended")
        report = inspect(repo, src, loaded.get("base") or probe["base"])
        if report["refusal"]:
            commands.die(1, report["refusal"])
        return _adopt_worktree(repo, report, loaded, pending, stage)
    finally:
        lock.release(pending)


def _adopt_worktree(repo, report, loaded, pending, stage):
    """D7 steps 3-6: the worktree for the source shape, then its state and adoption commit.

    Failures before the commit lands roll back: the worktree, and the branch only when this write
    creates it (FR-013). After the commit only the pending cleanup can fail; that is reported and not rolled back.
    """
    worktree = Path(report["worktree"])
    created = _created_branch(repo, report)
    try:
        _add_worktree(repo, report, worktree)
        sha, summary = _record_worktree_run(worktree, report, loaded, pending, stage)
    except (commands.CLIError, state.StateError, OSError) as e:
        leftovers = _rollback(repo, worktree, created)
        if leftovers:
            commands.die(1, f"adopt failed: {e}; rollback left {'; '.join(leftovers)}")
        commands.die(1, f"adopt failed and was rolled back: {e}")
    try:
        _clear_pending(pending)
    except OSError as e:
        commands.die(1, f"committed {sha}; pending cleanup failed: {e}")
    return summary


def _created_branch(repo, report):
    """The branch this write creates (remote-branch, default-branch) when it does not exist yet, else None."""
    branch = report["branch"]
    if report["shape"] == "branch" or _try(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}") is not None:
        return None
    return branch


def _add_worktree(repo, report, worktree):
    """D7 step 3: the worktree for the source shape."""
    branch, shape = report["branch"], report["shape"]
    if shape == "remote-branch":
        commands.git(repo, "worktree", "add", "--track", "-b", branch, str(worktree), f"origin/{branch}")
    elif shape == "default-branch":
        commands.git(repo, "worktree", "add", "-b", branch, str(worktree), report["base"])
    else:
        commands.git(repo, "worktree", "add", str(worktree), branch)


def _record_worktree_run(worktree, report, loaded, pending, stage):
    """D7 steps 4-5: the adopted state, the sidecars and the one adoption commit.

    Returns (short sha, resume digest); the digest is built before the commit so nothing after it can fail."""
    branch, spec_dir = report["branch"], report["spec_dir"]
    chosen = stage or report["inferred_stage"]
    base_commit = commands.git(str(worktree), "rev-parse", "HEAD").strip()
    run = dict(
        loaded,
        worktree=str(worktree),
        branch=branch,
        spec_dir=spec_dir,
        stage=chosen,
        status="running",
        adopted={
            "source": {"shape": report["shape"], "branch": branch, "spec_dir": spec_dir},
            "inferred_stage": report["inferred_stage"],
            "chosen_stage": chosen,
            "base_commit": base_commit,
        },
        history=list(loaded.get("history") or [])
        + [
            {
                "at": commands.now_iso(),
                "stage": chosen,
                "event": "adopted",
                "commit": None,
                "harness": loaded.get("harness"),
            }
        ],
    )
    folder = worktree / spec_dir / "factory"
    _no_link(worktree, folder)
    folder.mkdir(parents=True, exist_ok=True)
    state_path = folder / "state.json"
    _no_link(worktree, state_path)
    written = state.write_state(state_path, run)
    for suffix, target in ((".brief.md", "brief.md"), (".profile.md", "profile.md")):
        sidecar = pending.with_name(pending.name.replace(".json", suffix))
        if sidecar.exists():
            _no_link(worktree, folder / target)
            (folder / target).write_text(sidecar.read_text())
    summary = commands.digest(written, state_path, "worktree")
    sha = commands.commit_worktree(str(worktree), f"factory: adopt {branch}", spec_dir=f"{spec_dir}/factory")
    return sha, summary


def _clear_pending(pending):
    """D7 step 6: delete the pending JSON, brief and profile once the adoption commit has landed."""
    pending.unlink()
    for suffix in (".brief.md", ".profile.md"):
        pending.with_name(pending.name.replace(".json", suffix)).unlink(missing_ok=True)


def _rollback(repo, worktree, created_branch):
    """Remove the worktree a failed write added, and the branch too when the write created it.

    Returns what git left behind, named with its stderr; empty when clean. The pending files are the caller's to keep (FR-013).
    """
    leftovers = []
    removed = subprocess.run(
        ["git", "-C", repo, "worktree", "remove", "--force", str(worktree)],
        capture_output=True,
        text=True,
    )
    if removed.returncode != 0 and worktree.exists():
        leftovers.append(f"worktree {worktree} ({removed.stderr.strip()})")
    if created_branch and _try(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{created_branch}") is not None:
        deleted = subprocess.run(
            ["git", "-C", repo, "branch", "-D", created_branch], capture_output=True, text=True
        )
        if deleted.returncode != 0:
            leftovers.append(f"branch {created_branch} ({deleted.stderr.strip()})")
    return leftovers
