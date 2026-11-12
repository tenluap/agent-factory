# Brief: commit only what the run wrote

Feature 1 of `docs/scope-discipline-brief.md` (in the main checkout, not on `origin/main`). Every factory commit must contain only the paths the run wrote. The state CLI's writer commands and `adopt` commit with exactly their declared pathspec, the way `drop` already does, so an unrelated staged change is never swept into a factory commit. The code-writing roles (code-build, design-to-code, fixer) stage only by explicit path. code-build treats an uncommitted change as its own interrupted work only when the task it resumes names that path. The approver lists every uncommitted path in the worktree, and the run neither commits nor discards those paths.

## Story (verbatim)

Story: As a factory user, I want every factory commit to contain only the files the run wrote, so that a run never commits, deletes or absorbs work that is not its own.

## Acceptance criteria (verbatim, fixed for this run)

- AC-1 (story 1). Every state CLI command that commits (checkpoint, resume, adopt and the other writer commands) stages its declared paths and commits with exactly that pathspec, as `drop` already does.
- AC-2 (story 2). Given an unrelated staged change, such as a deleted pnpm-lock.yaml, when checkpoint, resume or adopt commits, then that change is not in the commit and is still staged afterwards.
- AC-3 (story 3). code-build, design-to-code and fixer stage files by explicit path, never with `git add -A`, `git add .` or `git commit -a`.
- AC-4 (story 4). code-build treats an uncommitted change as its interrupted work only when the task it resumes names that path; it neither commits nor discards any other uncommitted change.
- AC-5 (story 5). At the approver, every path `git status --porcelain` reports in the worktree is listed under "📂 Uncommitted local changes the run didn't make"; the run neither commits nor discards them.

Out of scope: any other approver change.

Do not reword these criteria. If an interpretation is needed, add a note under the criterion.

## Decisions

- Chain: **lite** (`specify`, `plan`, `tasks`, `analyze`). Intake: delivery. Cruise mode is on.
- Scope rule for every spec stage: recommend the narrowest option that satisfies AC-1..AC-5 as written. Leave out any behaviour, data, configuration or documentation the ACs do not need, and record it as declined scope.
- Q1 (AC-1): change the shared `commit_worktree` helper in `core/skills/factory/bin/factory_cli/commands.py` so that `git commit` gets the pathspec. This covers checkpoint, resume, rebind, models-record, profile-record, analyze-record, ledger-add, issue-add, wait-open, wait-close, answer, set-status, decisions-add and verify. Change adopt's `_commit_run` in `adopt.py` the same way, matching `drop`. No factory commit runs without a pathspec. Add no new abstraction.
- Q2 (AC-2): regression tests cover exactly the commands AC-2 names: checkpoint and resume in `tools/tests/test_commands.py`, adopt in `tools/tests/test_adopt.py`. Each test starts with an unrelated staged deletion (`pnpm-lock.yaml`). It checks that the deletion is absent from the commit and still staged afterwards. The other writer commands are covered through the shared helper, with no per-command tests.
- Q3 (AC-3): add one sentence at the commit step of each of `core/roles/code-build.md`, `design-to-code.md` and `fixer.md`: stage by explicit path (`git add -- <path>...`), never `git add -A`, `git add .` or `git commit -a`. The rule does not go in `engineering.md`.
- Q4 (AC-4): rewrite only Work step 1 of `core/roles/code-build.md`. An uncommitted change is interrupted work only when the task being resumed names its path. code-build finishes or discards only those paths. It leaves every other uncommitted change untouched: no stage, commit, stash or discard. No new envelope field.
- Q5 (AC-5): add one item to step 8 of `core/skills/factory/SKILL.md`. The orchestrator runs `git status --porcelain` in the worktree and lists every reported path under "📂 Uncommitted local changes the run didn't make". The section is shown only when it has paths. The run neither commits nor discards them. No new CLI command or field, and no other approver change.
- Q6: verify the prose rules (AC-3..AC-5) with text-contract tests under `tools/tests`, as run 023 did. No live-harness run.
- Q7: change only the docs the constitution requires. Update `DESIGN.md` (principle I, design first) where it describes writer commits, role staging and the approver screen. Fix any core reference line that would otherwise contradict the change. No ADR, no CONTEXT.md terms, no README change.
- Q8: the orchestrator's own `factory: start` commit (SKILL.md step 4.3) stays out of this run. AC-1 covers state CLI commands, and that commit runs in a fresh worktree.
- Verify baseline (user's decision): the tests already failing on the base commit are recorded once in `factory/verify-baseline.md`. On `origin/main` 0c3bf71, CI has 7 failures, in `test_render_models` and `test_skill_library`. Verify passes when the run adds no new failures. code-build and fixer get this list and must not repair, skip or edit those tests. The approver lists them.
- Commands: build renders all five harnesses with `tools/render.py`, checks that `dist/` is untracked, and runs `bash -n install.sh`. Test: `python3 -m unittest discover -s tools`. Both come from the CI checks in README/DESIGN.md. The repository has no CLAUDE.md or AGENTS.md, and the stack detector found no known stack.

## Declined scope (left out, follow-ups)

- Extending the AC-4 interrupted-work rule to design-to-code and fixer (Q4).
- A CLI command or `show` field for the uncommitted-path list (Q5).
- A pathspec on the orchestrator's own `factory: start` commit (Q8).
- A staging rule in `engineering.md` (Q3).
- An ADR, CONTEXT.md terms or README changes (Q7).
- Repairing the tests already failing on `origin/main` (verify baseline).
