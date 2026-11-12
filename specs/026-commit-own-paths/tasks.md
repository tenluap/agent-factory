# Tasks: Commit only what the run wrote

**Input**: `specs/026-commit-own-paths/` — [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [quickstart.md](quickstart.md)

**Tests**: required (engineering.md commit units; this overrides SpecKit's "tests are optional"). Every behaviour-changing task is one checkbox and one commit: failing test, implementation, passing check, mapped seam and failure path from plan.md "Test seams", red proof and done condition.

**Commit rule for every task**: stage by explicit path only (`git add -- <paths>`); never `git add -A`, `git add .` or `git commit -a`. Commit body carries the `Red:` line (engineering.md "Red proof") unless the task is plan-exempt.

**Out of scope**: the tests already failing on base 0c3bf71, as listed in `factory/verify-baseline.md` (8 locally, 7 on CI). No task repairs, skips or edits them. "No new failures" means no failure beyond that list.

**Format**: `- [ ] [ID] [P?] [Story] [AC-n] Description`

## Phase 1: Setup

None. Test runner exists (`python3 -m unittest discover -s tools`); no new dependency.

## Phase 2: Foundational (design first, constitution principle I)

- [x] T001 [AC-1] [AC-3] [AC-4] [AC-5] Update `DESIGN.md` before any core edit.
  - Exempt: `DESIGN.md` - documentation only; behaviour it describes is tested through the plan's seams (plan.md "Test seams").
  - Edit: in the "Declared-file checkpoints" bullet, state that every state CLI writer command and `adopt` commit with exactly their declared pathspec (as `drop` does), and that an unrelated staged change is left out of the commit and stays staged. Add that code-build, design-to-code and fixer stage by explicit path, never `git add -A`, `git add .` or `git commit -a`, and that code-build claims uncommitted work only for paths its resumed task names. In "Approver", add the "📂 Uncommitted local changes the run didn't make" list from `git status --porcelain`, shown only when non-empty, never committed or discarded by the run.
  - Commit: `git add -- DESIGN.md specs/026-commit-own-paths/tasks.md`; `factory(implement): T001 Record commit-own-paths behaviour in DESIGN.md`. No `Red:` line (exempt).
  - Done when: `DESIGN.md` names the writer/adopt pathspec rule, role explicit-path staging, code-build resume path-match rule and the approver heading.

## Phase 3: User Story 1 — State CLI commits contain only their declared paths (P1)

**Goal**: checkpoint, resume, adopt and every writer through `commit_worktree` commit with exactly their declared pathspec; an unrelated staged change is neither committed nor unstaged.

**Independent test**: `python3 -m unittest tools.tests.test_commands tools.tests.test_adopt`.

- [ ] T002 [US1] [AC-1] [AC-2] Commit `commit_worktree` with its declared pathspec in `core/skills/factory/bin/factory_cli/commands.py`.
  - Seams and failure paths (plan.md): `factory checkpoint` -> `unrelated-staged-deletion`; `factory resume` (worktree) -> `unrelated-staged-deletion`; `commands.commit_worktree` -> `no-declared-paths`.
  - 1. Failing tests in `tools/tests/test_commands.py`:
    - checkpoint: commit `pnpm-lock.yaml` in the run worktree, stage its deletion (`git rm pnpm-lock.yaml`), run `checkpoint`; assert `git show --name-only --format= HEAD` does not list `pnpm-lock.yaml` and `git diff --cached --name-status` still shows `D	pnpm-lock.yaml`.
    - resume: same staged deletion, run `resume <name>` against the worktree run; same two assertions on the `factory: resume <name>` commit.
    - `commit_worktree(worktree, msg, spec_dir=None, extra=())` with a staged change: returns `None`, HEAD unchanged, change still staged.
    - Run `python3 -m unittest tools.tests.test_commands`; observe the three new tests fail (deletion swept into the commit; helper commits without a pathspec).
  - 2. Implement: in `commit_worktree`, return `None` when the declared list is empty; otherwise `git add -- <paths>` then `git commit -q -m <message> -- <paths>`. Update the docstring. No other call site changes.
  - 3. Passing check: `python3 -m unittest tools.tests.test_commands` green; full `python3 -m unittest discover -s tools` shows no failure beyond the base failures in `factory/verify-baseline.md`.
  - Red proof: `Red: <checkpoint test name> failed as expected` (plus one line each for the resume and no-declared-paths tests).
  - Commit: `git add -- core/skills/factory/bin/factory_cli/commands.py tools/tests/test_commands.py specs/026-commit-own-paths/tasks.md`; `factory(implement): T002 Commit writer state with its declared pathspec`.
  - Done when: checkpoint and resume commits omit the staged `pnpm-lock.yaml` deletion and it stays staged; `commit_worktree` with no declared path makes no commit.

- [ ] T003 [P] [US1] [AC-1] [AC-2] Commit adopt's run folder with its pathspec in `core/skills/factory/bin/factory_cli/adopt.py` (`_commit_run`).
  - Seam and failure path (plan.md): `factory adopt` write (through `_commit_run`) -> `unrelated-staged-deletion`.
  - 1. Failing test in `tools/tests/test_adopt.py`: `adopt` refuses a dirty checkout and creates a fresh worktree, so inject inside the adopt write path: patch `adopt._record_worktree_run` (runs after `_add_worktree`, before `_commit_run`) with a wrapper that calls the original, then commits `pnpm-lock.yaml` in the new worktree and stages its deletion (`git rm pnpm-lock.yaml`); run `adopt` (no `--dry-run`); assert the `factory: adopt <branch>` commit does not list `pnpm-lock.yaml` and `git diff --cached --name-status` still shows `D	pnpm-lock.yaml`. Run `python3 -m unittest tools.tests.test_adopt`; observe it fail.
  - 2. Implement: `commands.git(str(worktree), "commit", "-q", "-m", f"factory: adopt {report['branch']}", "--", f"{report['spec_dir']}/factory")`.
  - 3. Passing check: `python3 -m unittest tools.tests.test_adopt` green; full suite no new failures.
  - Red proof: `Red: <adopt test name> failed as expected`.
  - Commit: `git add -- core/skills/factory/bin/factory_cli/adopt.py tools/tests/test_adopt.py specs/026-commit-own-paths/tasks.md`; `factory(implement): T003 Commit adopt with its declared pathspec`.
  - Done when: the adopt commit omits the staged deletion and it stays staged.

## Phase 4: User Story 2 — Code-writing roles stage by explicit path (P1)

**Goal**: code-build, design-to-code and fixer stage only by explicit path.

**Independent test**: `python3 -m unittest tools.tests.test_commit_scope`.

- [ ] T004 [US2] [AC-3] Add the explicit-path staging sentence to `core/roles/code-build.md` (step 3 commit item), `core/roles/design-to-code.md` (step 4 commit-unit text) and `core/roles/fixer.md` (step 5), with the new contract test file `tools/tests/test_commit_scope.py`.
  - Seam and failure path (plan.md): prose contract `commit_scope_gaps` -> `marker-removed`.
  - 1. Failing test: create `tools/tests/test_commit_scope.py` with `commit_scope_gaps(texts)` returning the missing markers, modelled on `tools/tests/test_pr_publication.py`. Markers for each of the three roles: explicit-path staging (`git add -- <path>`), and each forbidden bulk form (`git add -A`, `git add .`, `git commit -a`). Tests: real core text has no staging gap; each mutated copy with one marker removed reports exactly that gap. Run `python3 -m unittest tools.tests.test_commit_scope`; observe the real-text test fail.
  - 2. Implement: one sentence per role at the named commit step: stage by explicit path (`git add -- <path>...`), never `git add -A`, `git add .` or `git commit -a`.
  - 3. Passing check: `python3 -m unittest tools.tests.test_commit_scope` green; full suite no new failures; `commands.build` (render five harnesses, `dist/` untracked, `bash -n install.sh`) exits 0.
  - Red proof: `Red: <real-text staging test name> failed as expected`.
  - Commit: `git add -- core/roles/code-build.md core/roles/design-to-code.md core/roles/fixer.md tools/tests/test_commit_scope.py specs/026-commit-own-paths/tasks.md`; `factory(implement): T004 Require explicit-path staging in code-writing roles`.
  - Done when: all three role files carry the sentence and the contract test reports no gap.

## Phase 5: User Story 3 — code-build claims only its own interrupted work (P2)

**Goal**: code-build's Work step 1 claims only paths the resumed task names.

**Independent test**: `python3 -m unittest tools.tests.test_commit_scope`.

- [ ] T005 [US3] [AC-4] Rewrite Work step 1 of `core/roles/code-build.md`. Depends on T004 (same role file and test file).
  - Seam and failure path (plan.md): prose contract `commit_scope_gaps` -> `marker-removed`.
  - 1. Failing test: extend `commit_scope_gaps` in `tools/tests/test_commit_scope.py` with code-build step-1 markers: the resume path-match rule (interrupted work only when the resumed task names its path) and the leave-untouched rule (no stage, commit, stash or discard of any other uncommitted change). Add real-text and one-marker-removed tests. Observe the real-text test fail.
  - 2. Implement: replace step 1 only: `cd <worktree> && git status`; an uncommitted change is interrupted work only when the task being resumed names its path; finish or discard only those paths; leave every other uncommitted change untouched (never stage, commit, stash or discard it).
  - 3. Passing check: `python3 -m unittest tools.tests.test_commit_scope` green; full suite no new failures; `commands.build` exits 0.
  - Red proof: `Red: <real-text resume-rule test name> failed as expected`.
  - Commit: `git add -- core/roles/code-build.md tools/tests/test_commit_scope.py specs/026-commit-own-paths/tasks.md`; `factory(implement): T005 Limit code-build resume to paths its task names`.
  - Done when: step 1 carries both rules and the contract test reports no gap.

## Phase 6: User Story 4 — The approver lists uncommitted local changes (P2)

**Goal**: the approver shows every `git status --porcelain` path under the fixed heading and the run leaves them alone.

**Independent test**: `python3 -m unittest tools.tests.test_commit_scope`.

- [ ] T006 [US4] [AC-5] Add the uncommitted-paths item to "## 8. Approver" in `core/skills/factory/SKILL.md`. Depends on T004 (same test file).
  - Seam and failure path (plan.md): prose contract `commit_scope_gaps` -> `marker-removed`.
  - 1. Failing test: extend `commit_scope_gaps` with approver markers read from the "## 8. Approver" section only: `git status --porcelain`, the exact heading "📂 Uncommitted local changes the run didn't make", and the no-commit/no-discard rule. Add real-text and one-marker-removed tests. Observe the real-text test fail.
  - 2. Implement: one item in the approver show-list: run `git status --porcelain` in the worktree; when it reports any path, list every reported path under "📂 Uncommitted local changes the run didn't make"; the run neither commits nor discards them. No other approver change.
  - 3. Passing check: `python3 -m unittest tools.tests.test_commit_scope` green; full suite no new failures; `commands.build` exits 0.
  - Red proof: `Red: <real-text approver test name> failed as expected`.
  - Commit: `git add -- core/skills/factory/SKILL.md tools/tests/test_commit_scope.py specs/026-commit-own-paths/tasks.md`; `factory(implement): T006 List uncommitted local changes at the approver`.
  - Done when: the approver section carries the item and the contract test reports no gap.

## Phase 7: Verification

- [ ] T007 [AC-1] [AC-2] [AC-3] [AC-4] [AC-5] Run quickstart.md steps 1-4: `python3 -m unittest discover -s tools` (no failure beyond the base failures in `factory/verify-baseline.md`, SC-005) and `commands.build` (exit 0). Verification only: no file change, no commit beyond ticking this box (`git add -- specs/026-commit-own-paths/tasks.md`; `factory(implement): T007 Verify suite and build`). Done when both commands meet their expected result.

## Dependencies

- T001 first (principle I).
- T002 and T003 (US1) touch disjoint files; either order.
- T004 then T005 and T006 (shared `tools/tests/test_commit_scope.py`; T005 also shares `core/roles/code-build.md`).
- US1 (T002-T003) and US2-US4 (T004-T006) are independent after T001.
- T007 last.

## Parallel opportunities

- After T001, T002, T003 and the prose chain (T004, then T005, T006) touch disjoint files and can run in parallel.
- T005 and T006 both extend `tools/tests/test_commit_scope.py`; run them in sequence.

## Implementation strategy

MVP: T001-T003 (User Story 1, AC-1/AC-2), the data-integrity fix. Then T004-T006 for the prose rules, then T007.
