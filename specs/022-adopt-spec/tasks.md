---
description: "Task list for 022-adopt-spec"
---

# Tasks: Adopt a spec started outside factory

**Input**: `specs/022-adopt-spec/` (spec.md, plan.md)

**Tests**: Required (engineering.md). Each behaviour-changing task is one commit unit: failing test (red proof), implementation, passing check, committed together. Runner: `python3 -m unittest discover -s tools` (existing). Seams and failure paths: plan.md "Test seams" (scope confirmed: Q1 accepted 2026-11-04, snapshot `factory/relay/plan-Q1.md`). New tests go in `tools/tests/test_adopt.py` (new file, reason in plan.md) using the `Sandbox` in `tools/tests/__init__.py` (throwaway repo plus its own `FACTORY_HOME`, pending files under `<home>/pending/`); CLI tests run `core/skills/factory/bin/factory` as a subprocess. "Unchanged" below means `git status --porcelain`, `git for-each-ref`, `git worktree list --porcelain`, the files under the repo and `<home>/pending/` are byte-identical before and after.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallel-safe (different files, no dependency)
- **[Story]**: US1-US6 from spec.md

## Phase 1: Setup

- [ ] T001 Update `DESIGN.md` (flow, state, review, validation plan): `/factory adopt <branch|spec_dir> [--stage <s>]`, dry-run before any pending file, adoption grill in pending state, the write's steps and rollback (plan.md "Decisions"), the three source shapes and resolution order, refusal order, entry-stage inference and the `--stage` vocabulary, the `adopted` block and history event, `adopted_base` to `spec-conformance` and `review-judge` (ENG-2 only after `base_commit`), approver and retro disclosure, `resume`'s hint; validation-plan entry naming one fixture adoption per shape that checks SC-001..SC-005. Update `README.md` "Usage" with `/factory adopt <branch|spec_dir> [--stage <s>]` and a one-line description. Add **Adopted run** (plus **Source**, **Adoption report**, **Base commit**) to `CONTEXT.md`. Write `docs/adr/0017-adopted-runs-enter-at-most-at-analyze.md` (entry-stage ceiling, Q5/Q8; pre-adoption ENG-2 boundary, Q9; explicit verb, Q1). Exempt: `DESIGN.md`, `README.md`, `CONTEXT.md`, `docs/adr/0017-adopted-runs-enter-at-most-at-analyze.md` - documentation only (constitution I: lands before core edits). Done: every item above named in `DESIGN.md`; the README line, four `CONTEXT.md` terms and ADR 0017 present (FR-023).

## Phase 2: Foundational - state schema (blocks every write task)

- [ ] T002 [US1][US5] Validate the `adopted` block and event in `core/skills/factory/bin/factory_cli/state.py`: `ADOPT_SHAPES = ("branch", "remote-branch", "default-branch")`, `ADOPT_STAGES = ("specify", "plan", "tasks", "analyze")`, `adopted` added to `HISTORY_EVENTS`, `_check_adopted` called from `validate_state`; tests in new `tools/tests/test_adopt.py`.
  - Seam: `factory_cli.state.validate_state`. Failure paths: non-object `adopted`; `source.shape` off-vocabulary; missing `source.branch` or `source.spec_dir`; `inferred_stage` or `chosen_stage` outside `specify|plan|tasks|analyze`; `base_commit` not 40 lowercase hex; an `adopted` history entry without the `adopted` block.
  - Red: tests first: a valid adopted state at stage `analyze` with one `adopted` history entry and no `complete` entries validates clean (FR-017); a state without `adopted` and the existing fixtures validate clean (FR-016, SC-004); each failure path above yields one problem naming its location (uppercase hex and a 39-character sha both rejected). Run; the adopted-state and failure-path tests fail.
  - Implement: `_check_adopted` per plan.md "Data model"; the history check requires the block when an `adopted` entry exists. No version bump; no rule on `complete` entries before the chosen stage.
  - Pass: runner green.
  - Done: every listed case asserted and passing; `tools/tests/test_state.py` unchanged and green.

## Phase 3: User Story 2 - Safe preview and refusals (P1)

- [ ] T003 [US2][US1] Add `inspect(repo, src, base)` and the dry-run report to new `core/skills/factory/bin/factory_cli/adopt.py`; `adopt` dispatch, `--stage`/`--dry-run` parsing and USAGE line in `core/skills/factory/bin/factory_cli/cli.py`; tests in `tools/tests/test_adopt.py`.
  - Seam: `bin/factory adopt <src> --dry-run`. Failure paths: `--stage implement` or an unknown value exits 5.
  - Red: tests first, fixture = feature branch `007-x` adding `specs/007-x/spec.md`, main checkout back on the default branch: `adopt 007-x --dry-run` exits 0 and prints JSON with `shape: branch`, `branch`, `spec_dir: specs/007-x`, `base`, `artifacts`, `dirty: []`, `worktree` = `<repo>/../<repo-name>-factory/007-x`, `refusal: null`; inferred stage `plan` for `spec.md` only, `tasks` with `plan.md`, `analyze` with `tasks.md` holding checked boxes (FR-008); `spec.md` with two `[NEEDS CLARIFICATION: ...]` lines lists both in `needs_clarification`; `adopt specs/007-x --dry-run` resolves the same; repo unchanged afterwards (SC-002); `--stage implement` and `--stage bogus` exit 5 with nothing read or written. Run; fails (unknown command).
  - Implement: resolution order and spec-dir discovery per plan.md "Source resolution" (local branch only here); artifacts and markers read from the ref (`git ls-tree`, `git show <ref>:<path>`); `<src>` validated with `git check-ref-format --branch` and passed as argv elements only; dry-run base from `refs/remotes/origin/HEAD`, else `main`; `--stage` validated in `cli.py` before any read.
  - Pass: runner green.
  - Done: every listed case asserted and passing; nothing written by any dry-run.

- [ ] T004 [US2] Add the refusals to `inspect` in `core/skills/factory/bin/factory_cli/adopt.py`; tests in `tools/tests/test_adopt.py`.
  - Seam: `bin/factory adopt <src> --dry-run`. Failure paths: dirty spec file or dirty source-branch checkout exits 1 naming every dirty path; existing `factory/state.json` exits 1 naming `resume`; missing `spec.md` exits 1; branch checked out in the main checkout or another worktree exits 1 with the switch hint; existing worktree path exits 1 naming it; no matching source exits 1; several matching spec dirs exit 3 listing them; every refusal leaves the repo unchanged.
  - Red: tests first, one per failure path, each asserting exit code, the report (still printed on exit 1) naming the cause, and the repo unchanged: two dirty paths (one modified spec file in the main checkout, one untracked file in a worktree on the source branch) both listed; committed `specs/007-x/factory/state.json` names `resume 007-x`; branch adding only `plan.md` names `spec.md`; branch checked out in the main checkout, then in a `git worktree add` checkout, each names the checkout and the switch hint; pre-created worktree path named; `adopt nope` exits 1; two spec dirs matching by the `NNN-` suffix rule exit 3 listing both; dirty paths still listed when the state-exists refusal also applies. Run; fail (no refusals yet).
  - Implement: refusal order per plan.md "Refusal order"; dirty paths from `git status --porcelain` of the main checkout limited to the spec dir plus every checkout holding the source branch (`git worktree list --porcelain`); the `NNN-` matching reuses `find_matches`'s rule rather than a copy.
  - Pass: runner green.
  - Done: every failure path asserted and passing.

## Phase 4: User Story 3 - Other source shapes, preview (P2)

- [ ] T005 [US3] Resolve `remote-branch` and `default-branch` shapes in `inspect` (`core/skills/factory/bin/factory_cli/adopt.py`); tests in `tools/tests/test_adopt.py`.
  - Seam: `bin/factory adopt <src> --dry-run`. Failure paths: none beyond T003/T004 (covered there).
  - Red: tests first, fixtures with a bare `origin` remote in the sandbox: branch only on `origin` reports `shape: remote-branch`; spec dir committed on the default branch with no own branch reports `shape: default-branch`, `branch` = dir name; same dir plus a local branch of that name reports `shape: branch` (spec edge case); branch `feat-y` holding `specs/009-renamed/` reports `spec_dir: specs/009-renamed` (FR-004); a branch both local and on `origin` (diverged) reports the local branch's artifacts; no fetch happens (`git for-each-ref refs/remotes` unchanged); repo unchanged. Run; fail.
  - Implement: steps 2-3 of plan.md "Source resolution"; spec dir from `specs/<branch>/` on the ref, else the single `specs/*/` dir from `git diff --name-only <base>...<ref> -- specs/`.
  - Pass: runner green.
  - Done: every listed case asserted and passing.

## Phase 5: User Story 1 - Continue a SpecKit spec on its own branch (P1)

- [ ] T006 [US1][US4] Add the adopt write to `core/skills/factory/bin/factory_cli/adopt.py` (lock, pending match, re-inspection, `git worktree add`, `state.write_state`, brief/profile move, `commit_worktree`, pending delete, rollback) and its dispatch in `core/skills/factory/bin/factory_cli/cli.py`; tests in `tools/tests/test_adopt.py`.
  - Seam: `bin/factory adopt <src> [--stage <stage>]` (write). Failure paths: a refusal arising after the dry-run (dirty file, existing state) exits 1 with nothing written; no pending run, or a pending run whose `branch` differs, exits 1; a live foreign lock exits 1; a commit rejected by a `pre-commit` hook removes the worktree and any branch adopt created, keeps the pending files, exits 1.
  - Red: tests first, `branch` shape, pending file written into `<home>/pending/` with `branch: 007-x`, `spec_dir`, a brief and profile beside it: `adopt 007-x` exits 0 and prints the resume digest; worktree at the standard path on `007-x` and `git branch --list` unchanged (no new branch); `state.json` passes `validate_state` with `stage: tasks` for `spec.md`+`plan.md`, `status: running`, `adopted` = `{source: {shape: branch, ...}, inferred_stage: tasks, chosen_stage: tasks, base_commit: <pre-write HEAD of 007-x>}`, exactly one `adopted` history entry; `brief.md` and `profile.md` in `specs/007-x/factory/`; the three pending files gone; `git log` shows exactly one new commit `factory: adopt 007-x` whose `--name-only` paths are all under `specs/007-x/factory/` (FR-012, FR-014); `--stage plan` records `chosen_stage: plan`, `inferred_stage: tasks`, `stage: plan` (FR-009, US4). Failure paths, each asserting exit 1, repo unchanged and pending files intact: file dirtied after the dry-run; `factory/state.json` committed after the dry-run; no pending file; pending `branch: 008-other`; a live lock held on the pending path by another pid (`lock.acquire`); a `pre-commit` hook exiting 1 (worktree removed, `007-x` kept, pending intact). Run; fail.
  - Implement: steps 1-6 of plan.md "Write steps"; rollback in a `try`/`except` that runs `git worktree remove --force` and `git branch -D` only for a branch step 3 created; pending deleted only after the commit succeeds; the lock released on every path.
  - Pass: runner green.
  - Done: every listed case asserted and passing.

- [ ] T007 [US3] Create branches for `remote-branch` and `default-branch` in the adopt write (`core/skills/factory/bin/factory_cli/adopt.py`); tests in `tools/tests/test_adopt.py`.
  - Seam: `bin/factory adopt <src> [--stage <stage>]` (write). Failure paths: a commit rejected by a `pre-commit` hook removes the worktree and the branch adopt created, keeps the pending files, exits 1.
  - Red: tests first: remote-only `007-x` yields a local `007-x` whose upstream is `origin/007-x` (`git rev-parse --abbrev-ref 007-x@{upstream}`) and `adopted.source.shape: remote-branch`; default-branch spec dir yields a new branch `007-x` at `base` and `shape: default-branch`; each with the T006 state, file and single-commit assertions; with a rejecting `pre-commit` hook each shape exits 1, the created `007-x` branch and worktree are gone, the pending files intact (FR-013); no push happens (`git ls-remote origin` unchanged). Run; fail.
  - Implement: step 3's `--track -b` and `-b <base>` forms; rollback records that the branch was created.
  - Pass: runner green.
  - Done: every listed case asserted and passing.

## Phase 6: User Story 6 - Resume points to adopt (P3)

- [ ] T008 [US6] Add an optional `hint` to `one_run` in `core/skills/factory/bin/factory_cli/commands.py`, passed only by `cmd_resume`; tests in `tools/tests/test_adopt.py`.
  - Seam: `bin/factory resume <run>`. Failure paths: no matching run exits 1 with "no run" and the `adopt <branch|spec_dir>` hint, creating no run, worktree or branch.
  - Red: tests first: a plain SpecKit branch `007-x` with no state: `resume 007-x` exits 1, stderr contains `no run` and `use adopt <branch|spec_dir>`, repo unchanged; `show nope` (another `one_run` caller) carries no hint; an existing pending run resumes as before (one `resumed` entry). Run; the hint test fails.
  - Implement: `hint=None` keyword appended to the no-run message.
  - Pass: runner green.
  - Done: every listed case asserted and passing; `tools/tests/test_commands.py` unchanged and green (FR-021).

## Phase 7: Orchestrator and reference prose (US1, US2, US4, US5)

- [ ] T009 [US1][US2][US4][US5] Edit `core/skills/factory/SKILL.md` per plan.md "Design (orchestrator prose)": argument-hint gains `adopt <branch|spec_dir> [--stage <s>]`; step 0 routes `adopt` to `factory adopt <src> --dry-run`, a non-zero exit shows the refusal or candidates and creates nothing (FR-001, FR-003); pending reuse by `branch` in `factory runs`, else new pending with `branch`, `spec_dir`, `feature` = spec title; preflight; adoption grill replacing steps 2-3 (summary from `spec.md`, `needs_clarification` first, chain, entry stage with the inferred stage recommended, same frontier and cruise rules) (FR-010); declined → `set-status aborted` (FR-011); confirmed → `brief.md`, `checkpoint grill --next worktree`, `factory adopt <src> --stage <chosen>` replacing step 4, failure leaves the pending run for retry, then continue under "Resume" (FR-018); step 7 passes `adopted_base` when `adopted` exists (FR-019); step 8 adds the adoption line (FR-020). Exempt: `core/skills/factory/SKILL.md` - documentation only. Done: each FR above cited by a prose step; core uses `SHELL`/`ASK`, no harness-specific invocation.

- [ ] T010 [P] [US1] Edit `core/skills/factory/references/state.md`: the `adopted` block and its validation, the `adopted` history event and its only writer, the CLI lines `adopt <src> [--stage <stage>] [--dry-run]` with exit codes, the adopted run's state location, `resume`'s hint. Exempt: `references/state.md` - documentation only. Done: schema, event and command documented.

- [ ] T011 [P] [US5] Edit `core/roles/spec-conformance.md` (check `Red:` lines on `<adopted_base>..HEAD` only, list `<base>..<adopted_base>` commits as pre-adoption, never blocking for ENG-2), `core/roles/review-judge.md` (never confirm an ENG-2 finding against a pre-adoption commit; whole `base...HEAD` still reviewed) and `core/roles/retro.md` (summary states the run was adopted, source and chosen stage). Exempt: the three role files - documentation only. Done: each file states its rule (FR-019, FR-020, SC-005).

## Phase 8: Polish and verification

- [ ] T012 Build and neutrality check: run the build command (render all five harnesses into a temp `FACTORY_HOME`, `bash -n install.sh`); `git diff --stat origin/main -- tools/render.py install.sh` is empty; `test -z "$(git ls-files -- dist/)"` passes (constitution III) (FR-023, SC-006). Exempt: verification only. Done: build exits 0; both checks pass.

- [ ] T013 Final verification: `python3 -m unittest discover -s tools`. Exempt: verification only. Done: all tests pass, or any failure is shown to be pre-existing on `origin/main` and recorded here; zero new failures (SC-004).

## Dependencies

- T001 first (constitution I).
- T002 before T006-T007 (the write validates `adopted`).
- T003 → T004 → T005 (same module, growing `inspect`); T006 after T004 (re-inspection uses the refusals); T007 after T005 and T006.
- T008 after T002 only (separate function in `commands.py`).
- T009 after T003-T008 (prose calls the new command). T010, T011 parallel with each other and T009.
- T012, T013 last.

## Parallel execution

- T002-T008 share `tools/tests/test_adopt.py` and the CLI modules: run sequentially.
- T010 and T011 together: one per file group.

## Implementation Strategy

MVP = T001-T004 and T006: schema, safe preview with every refusal, and the `branch`-shape write with rollback (US1, US2, the SpecKit default). Then the other shapes (T005, T007), the resume hint (T008), the prose (T009-T011), and verification (T012-T013).
