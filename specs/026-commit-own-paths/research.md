# Research: Commit only what the run wrote

## R1. How to commit only declared paths (AC-1, AC-2)

- Decision: pass the declared paths to `git commit` after `--`, as `cmd_drop` does (`commands.py`, `git(worktree, "commit", "-q", "-m", ..., "--", *paths)`).
- Rationale: with a pathspec, `git commit` runs in `--only` mode. It commits the working-tree state of those paths and leaves every other index entry unchanged, so an unrelated staged deletion is neither committed nor unstaged. The existing `git add -- <paths>` step stays so new untracked files under the declared paths are included.
- Alternatives considered: `git stash` of unrelated changes (touches user work, rejected by AC-4/AC-5 spirit); a temporary index via `GIT_INDEX_FILE` (new mechanism, more code); refusing to commit when unrelated changes are staged (blocks the run on user state).

## R2. No declared paths (open point from specify, FR-001)

- Decision: `commit_worktree` returns `None` and makes no commit when it has no declared path.
- Rationale: FR-001 forbids any factory commit without a pathspec. Returning `None` matches the helper's existing `if not worktree: return None` branch, adds no error, exit code or field, and every current caller passes `spec_dir` (`profile-record` passes `loaded.get("spec_dir")` unchanged; worktree-run state always carries `spec_dir`).
- Alternatives considered: exit with an error (new failure mode for writer commands); commit with an empty pathspec (violates FR-001).

## R3. Where the prose rules go (AC-3, AC-4, AC-5)

- Decision: one sentence at each role's commit step; rewrite only code-build Work step 1; one item in SKILL.md step 8 (brief Q3-Q5).
- Rationale: smallest edits that state each AC where the agent acts on it.
- Alternatives considered: an `engineering.md` rule (reviewers read it too; declined scope).

## R4. Verifying prose rules (FR-007)

- Decision: text-contract tests in a new `tools/tests/test_commit_scope.py`, with mutated copies proving each marker fails on its own, following run 023's `test_pr_publication.py`.
- Alternatives considered: live-harness run (brief Q6, declined).
