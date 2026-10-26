"""Shared test helpers: throwaway git repos, fixture runs and CLI invocations.

Everything lives under tempfile; a Sandbox is fully hermetic (its own
FACTORY_HOME), so tests never touch a real run or the user's checkout.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FACTORY = REPO_ROOT / "core" / "skills" / "factory" / "bin" / "factory"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def fixture(name):
    return json.loads((FIXTURES / name).read_text())


class Sandbox:
    """A throwaway git repo with its own FACTORY_HOME for pending files."""

    def __init__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="factory-test-"))
        self.repo = self.dir / "repo"
        self.home = self.dir / "home"
        (self.home / "pending").mkdir(parents=True)
        self.git("init", "-q", str(self.repo))
        self.git("config", "user.email", "factory@example.com")
        self.git("config", "user.name", "Factory Test")
        (self.repo / "README.md").write_text("fixture\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "initial")

    def git(self, *args, cwd=None):
        base = cwd or (self.repo if self.repo.exists() else self.dir)
        out = subprocess.run(
            ["git", *args], cwd=str(base), check=True, capture_output=True, text=True
        )
        return out.stdout

    def worktree_run(self, branch, state, worktree=None, commit=True):
        """A worktree on `branch` carrying specs/<branch>/factory/state.json.

        The state's recorded paths are rewritten to the sandbox so discovery
        and `show` treat it as the run's real home (pass `worktree` to record
        a stale home instead).
        """
        wt = worktree or self.dir / f"wt-{branch}"
        self.git("worktree", "add", "-q", "-b", branch, str(wt))
        folder = wt / "specs" / branch / "factory"
        folder.mkdir(parents=True)
        placed = dict(
            state,
            branch=branch,
            repo=str(self.repo),
            worktree=str(wt),
            spec_dir=f"specs/{branch}",
        )
        (folder / "state.json").write_text(json.dumps(placed, indent=2) + "\n")
        if commit:
            self.git("add", "-A", cwd=wt)
            self.git("commit", "-q", "-m", f"factory: start {branch}", cwd=wt)
        return wt

    def pending_run(self, name, state):
        path = self.home / "pending" / f"{self.repo.name}-{name}.json"
        path.write_text(json.dumps(dict(state, repo=str(self.repo)), indent=2) + "\n")
        return path

    def corrupt_worktree_state(self, branch, mutate):
        """Edit a worktree's state.json by hand (the tests' stand-in for drift)."""
        path = self.dir / f"wt-{branch}" / "specs" / branch / "factory" / "state.json"
        state = json.loads(path.read_text())
        mutate(state)
        path.write_text(json.dumps(state, indent=2) + "\n")
        return path

    def cli(self, *args, cwd=None):
        """Run bin/factory as a process over the sandbox."""
        env = dict(os.environ, FACTORY_HOME=str(self.home))
        return subprocess.run(
            [sys.executable, str(FACTORY), *args],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(cwd or self.repo),
        )

    def close(self):
        subprocess.run(
            ["git", "worktree", "prune"], cwd=str(self.repo), capture_output=True
        )
        shutil.rmtree(self.dir, ignore_errors=True)
