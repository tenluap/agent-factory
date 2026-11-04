"""Adopt a spec factory did not start (spec 022): source inspection and the dry-run report.

`inspect` is the one read-only resolution of a source: shape, spec dir, artifacts,
dirty paths, inferred stage and refusal, all from git refs. It never fetches,
checks out or writes; the write re-runs it under the pending lock (D7).
"""

import posixpath
import subprocess
from pathlib import Path

from factory_cli import commands

NEEDS_CLARIFICATION = "[NEEDS CLARIFICATION"


def _try(repo, *args):
    """Stdout of a git probe, or None when git exits non-zero (an absent ref or path)."""
    out = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else None


def default_base(repo):
    """The `base` a dry run reports (D3): origin's default branch, else origin/main, else main."""
    head = _try(repo, "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD")
    if head:
        return head.strip().removeprefix("refs/remotes/")
    if _try(repo, "show-ref", "--verify", "--quiet", "refs/remotes/origin/main") is not None:
        return "origin/main"
    return "main"


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


def _resolve(repo, src):
    """(shape, branch) for `src` (D2 steps 1 and 3), or None when no local branch matches.

    A `specs/` prefix names the spec dir, and its last segment names the branch.
    """
    for name in (src, src.removeprefix("specs/")):
        if _try(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{name}") is not None:
            return "branch", name
    return None


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
    found = _resolve(repo, src)
    if found is None:
        report["refusal"] = f"no branch or spec dir matches '{src}'"
        return report
    shape, branch = found
    spec_dir = f"specs/{branch}"
    ref = f"refs/heads/{branch}"
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
    return report
