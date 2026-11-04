---
description: "Task list for 022-adopt-spec"
---

# Tasks: Adopt a spec started outside factory

**Input**: `specs/022-adopt-spec/` (spec.md, plan.md, research.md D1-D11, data-model.md, contracts/cli.md, quickstart.md)

**Tests**: Required (engineering.md). Each behaviour-changing task is one commit unit: failing test (red proof `Red: <test> failed as expected`), implementation, passing check, committed together with its checkbox. Runner: `python3 -m unittest discover -s tools` (existing). Seams and failure paths: plan.md "Test seams", scope confirmed Q2 2026-11-04 (snapshot `factory/relay/plan-Q2.md`). Tests go in new `tools/tests/test_adopt.py` (reason in plan.md) using `Sandbox` from `tools/tests/__init__.py`; CLI tests run `bin/factory` through `Sandbox.cli`. The adoption's pending file is `Sandbox.pending_run("adopt-<branch>", state)`, i.e. `<home>/pending/<repo-name>-adopt-<branch>.json`. "Unchanged" means `git status --porcelain`, `git for-each-ref` (including `refs/remotes/origin/*`), `git worktree list --porcelain`, the repo files and `<home>/pending/` are byte-identical before and after. Base fixture: branch `007-x` adding `specs/007-x/spec.md`, main checkout back on the default branch.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallel-safe; **[Story]**: US1-US6 from spec.md

## Phase 1: Setup (Design First)

- [x] T001 Update `DESIGN.md`: "Flow" gains `/factory adopt <branch|spec_dir> [--stage <s>]` (dry-run before any pending file, pending adoption grill under `<repo-name>-adopt-<branch>`, write and rollback; research.md D1, D7); "State and resume" gains the three shapes and resolution order (D2), refusal order (D5), entry-stage inference and `--stage` vocabulary (D6), the `adopted` block and event, the sole-pending rule (D4), `resume`'s hint (D9); "Review" and "Approver" gain `adopted_base` and the pre-adoption boundary, pre-adoption tasks in analyze and the disclosure line (D10, D11); "Validation plan" gains "Adoption validation": one fixture adoption per shape checking SC-001..SC-005 after merge (quickstart.md). Add the `/factory adopt` usage line and one sentence to `README.md` "Usage". `CONTEXT.md` "Adoption" (four terms) and `docs/adr/0017-adopted-runs-enter-at-most-at-analyze.md` already exist: edit only statements this design contradicts. Exempt: `DESIGN.md`, `README.md`, `CONTEXT.md`, `docs/adr/0017-adopted-runs-enter-at-most-at-analyze.md` - documentation only (constitution I: lands before core edits). Done: each item in `DESIGN.md` and README; CONTEXT.md and ADR 0017 match plan.md (FR-023).

## Phase 2: Foundational - state schema (blocks the write)

- [x] T002 [US1][US5] Validate the `adopted` block and event in `core/skills/factory/bin/factory_cli/state.py`; tests in `tools/tests/test_adopt.py`.
  - Seam: `factory_cli.state.validate_state`. Failure paths: non-object `adopted`; `source.shape` off-vocabulary; missing `source.branch` or `source.spec_dir`; `inferred_stage` or `chosen_stage` outside `specify|plan|tasks|analyze`; `base_commit` not 40 lowercase hex; an `adopted` history entry without the `adopted` block.
  - Red: write tests first: an adopted state at stage `analyze` with one `{stage: analyze, event: adopted, commit: null}` entry and no `complete` entries validates clean (FR-017); a state without `adopted` and the existing fixtures validate clean (FR-016, SC-004); each failure path yields one problem naming its location (uppercase hex and a 39-character sha both rejected). Run; adopted-state and failure-path tests fail.
  - Implement: `ADOPT_SHAPES = ("branch", "remote-branch", "default-branch")`, `ADOPT_STAGES = ("specify", "plan", "tasks", "analyze")`, `adopted` appended to `HISTORY_EVENTS`, `_check_adopted` called from `validate_state` per data-model.md; no version bump; no rule on `complete` entries before the chosen stage.
  - Pass: runner green.
  - Done: every case asserted and passing; `tools/tests/test_state.py` unchanged and green.

## Phase 3: User Story 2 - Safe preview and refusals (P1)

- [x] T003 [US2][US1][US4] Add `inspect(repo, src, base)` and the dry-run report to new `core/skills/factory/bin/factory_cli/adopt.py`; `adopt` dispatch, `--stage`/`--dry-run` parsing and USAGE line in `core/skills/factory/bin/factory_cli/cli.py`; tests in `tools/tests/test_adopt.py`.
  - Seam: `bin/factory adopt <src> --dry-run`. Failure paths: `--stage implement` or an unknown value exits 5.
  - Red: write tests first: `adopt 007-x --dry-run` exits 0 printing the contracts/cli.md JSON: `shape: branch`, `branch`, `spec_dir: specs/007-x`, `base`, `artifacts`, `dirty: []`, `worktree` = `<repo>/../<repo-name>-factory/007-x`, `pending` = `<repo-name>-adopt-007-x`, `refusal: null`; inferred stage `plan` for `spec.md` only, `tasks` with `plan.md`, `analyze` with `tasks.md` holding checked boxes (FR-008); two `[NEEDS CLARIFICATION: ...]` lines both listed in `needs_clarification`; `adopt specs/007-x --dry-run` resolves the same; repo unchanged (SC-002); `--stage implement` and `--stage bogus` exit 5, repo unchanged (FR-009). Run; fails (unknown command).
  - Implement: D2 steps 1 and 3 (local branch, spec dir with its own branch); artifacts and markers from the ref (`git ls-tree`, `git show <ref>:<path>`); `<src>` checked with `git check-ref-format --branch`, passed as argv only; dry-run `base` per D3; `--stage` validated in `cli.py` before any read.
  - Pass: runner green.
  - Done: every case asserted and passing; no dry-run writes anything.

- [x] T004 [US2] Add the refusals to `inspect` in `core/skills/factory/bin/factory_cli/adopt.py`; tests in `tools/tests/test_adopt.py`.
  - Seam: `bin/factory adopt <src> --dry-run`. Failure paths: dirty spec file or dirty source-branch checkout exits 1 naming every dirty path; existing `factory/state.json` exits 1 naming `resume`; missing `spec.md` exits 1; branch checked out in the main checkout or another worktree exits 1 with the switch hint; existing worktree path exits 1 naming it; another pending file of the repo exits 1 naming it with the resume/prune hint; no matching source exits 1; several matching spec dirs exit 3 listing them; every refusal leaves the repo unchanged.
  - Red: write tests first, one per failure path, each asserting exit code, the report's `refusal` naming the cause, and repo unchanged: a modified spec file in the main checkout plus an untracked file in a worktree on `007-x`, both listed; clean committed `specs/007-x/factory/state.json` names `resume 007-x`, `dirty: []`; branch adding only `plan.md` names `spec.md`; `007-x` checked out in the main checkout, then in a `git worktree add` checkout, each named with the switch hint; pre-created worktree path named; pending `<repo-name>-other.json` named with the resume/prune hint, while the adoption's own `<repo-name>-adopt-007-x.json` alone refuses nothing; `adopt nope` and `adopt ../x` exit 1; local branches `007-x` and `008-x`: `adopt x` exits 3 listing both. Run; fail.
  - Implement: D5 order; dirty paths from the main checkout's `git status --porcelain -- <spec_dir>` plus every checkout holding the branch (`git worktree list --porcelain`); pending files from `find_runs`; the `-<name>` suffix match reuses `find_matches`'s rule, not a copy.
  - Pass: runner green.
  - Done: every failure path asserted and passing.

## Phase 4: User Story 3 - Other source shapes, preview (P2)

- [x] T005 [US3] Resolve `remote-branch` and `default-branch` shapes in `inspect` (`core/skills/factory/bin/factory_cli/adopt.py`); tests in `tools/tests/test_adopt.py`.
  - Seam: `bin/factory adopt <src> --dry-run`. Failure paths: spec dir on local default branch but not on `base` exits 1 with the "push it or create its branch first" reason; every refusal leaves the repo unchanged.
  - Red: write tests first with a bare `origin` remote: branch only on `origin` → `shape: remote-branch`; spec dir on `origin/<default>` with no own branch → `shape: default-branch`, `branch` = dir name; same dir plus a local branch of that name → `shape: branch`; branch `feat-y` holding `specs/009-renamed/` → `spec_dir: specs/009-renamed` (US3-3); branch local and on `origin`, diverged → local artifacts; remote moved ahead after the last fetch → `refs/remotes/origin/*` unchanged (no fetch, D3); spec dir committed on local default branch only → exit 1 with that reason (clarify Q2); repo unchanged throughout. Run; fail.
  - Implement: D2 steps 2-3; spec dir from `specs/<branch>/` on the ref, else the single dir from `git diff --name-only <base>...<ref> -- specs/` (several → exit 3).
  - Pass: runner green.
  - Done: every case asserted and passing.

## Phase 5: User Story 1 - Continue a SpecKit spec on its own branch (P1)

- [x] T006 [US1][US4] Add the adopt write for the `branch` shape to `core/skills/factory/bin/factory_cli/adopt.py` (D7 steps 1-6) and its dispatch in `core/skills/factory/bin/factory_cli/cli.py`; tests in `tools/tests/test_adopt.py`.
  - Seam: `bin/factory adopt <src> [--stage <stage>]` (write). Failure paths: a refusal arising after the dry-run (dirty file, existing state, another pending file) exits 1 with nothing written; no pending file `<repo-name>-adopt-<branch>` exits 1; an `aborted` adoption pending file exits 1; a live foreign lock exits 1.
  - Red: write tests first, fixture `spec.md`+`plan.md` on `007-x`, pending `adopt-007-x` with `base`, `default_branch`, `.brief.md`, `.profile.md`: `adopt 007-x` exits 0 printing the resume digest; worktree at the standard path on `007-x`, `git branch --list` unchanged (FR-005, FR-006, SC-003); `state.json` validates with `stage: tasks`, `status: running`, `adopted` = `{source: {shape: branch, branch: 007-x, spec_dir: specs/007-x}, inferred_stage: tasks, chosen_stage: tasks, base_commit}` and one `adopted` entry; a commit made on `007-x` after the dry-run is the recorded `base_commit` (edge case); `brief.md`, `profile.md` in `specs/007-x/factory/`; the three pending files gone; exactly one new commit `factory: adopt 007-x`, `--name-only` all under `specs/007-x/factory/` (FR-012, FR-014); `--stage plan` records `chosen_stage: plan`, `inferred_stage: tasks`, `stage: plan` (FR-009). Failure paths, each exit 1, repo unchanged, pending intact: file dirtied after the dry-run; `factory/state.json` committed after it; pending `<repo-name>-other.json` added after it; no pending file; pending `status: aborted`; lock held on the pending path by another live pid (FR-022). Run; fail.
  - Implement: `lock.acquire` on the pending path for the whole write; load and status-check pending; re-`inspect` against pending `base`; `git worktree add <path> <branch>`; `base_commit` = `git rev-parse <branch>`; `state.write_state`; copy brief and profile; `commit_worktree(..., spec_dir=<spec_dir>/factory)`; delete pending only after the commit.
  - Pass: runner green.
  - Done: every case asserted and passing.

- [x] T007 [US1] Roll back a failed adopt write in `core/skills/factory/bin/factory_cli/adopt.py`; tests in `tools/tests/test_adopt.py`.
  - Seam: `bin/factory adopt <src> [--stage <stage>]` (write). Failure paths: a commit rejected by a `pre-commit` hook removes the worktree and any branch adopt created, keeps the pending files, exits 1.
  - Red: write tests first: with a `pre-commit` hook exiting 1, `adopt 007-x` exits 1 naming the cause; worktree path gone (`git worktree list` unchanged), `007-x` kept at its HEAD, no new commit, pending JSON, brief and profile intact (FR-013); hook removed, the retry reuses the same pending file and succeeds with one commit (FR-010 edge case). Run; fail.
  - Implement: `try`/`except` over steps 3-5 catching `CLIError`, `StateError`, `OSError`: `git worktree remove --force <path>`, `git branch -D` only for a branch the write created, lock released on every path, exit 1.
  - Pass: runner green.
  - Done: every case asserted and passing.

- [x] T008 [US3] Create branches for `remote-branch` and `default-branch` in the adopt write (`core/skills/factory/bin/factory_cli/adopt.py`); tests in `tools/tests/test_adopt.py`.
  - Seam: `bin/factory adopt <src> [--stage <stage>]` (write). Failure paths: a commit rejected by a `pre-commit` hook removes the worktree and any branch adopt created, keeps the pending files, exits 1.
  - Red: write tests first: remote-only `007-x` → local `007-x` with upstream `origin/007-x` (`git rev-parse --abbrev-ref 007-x@{upstream}`), `adopted.source.shape: remote-branch`; default-branch spec dir → new `007-x` at `base`, `shape: default-branch`; each with T006's state, file and single-commit assertions; with a rejecting `pre-commit` hook each exits 1, the created `007-x` branch and worktree gone, pending intact; `git ls-remote origin` unchanged (no push). Run; fail.
  - Implement: `git worktree add --track -b <branch> <path> origin/<branch>` and `git worktree add -b <branch> <path> <base>`; mark the branch as created for rollback.
  - Pass: runner green.
  - Done: every case asserted and passing.

## Phase 6: User Story 6 - Resume points to adopt (P3)

- [x] T009 [US6] Add an optional `hint` to `one_run` in `core/skills/factory/bin/factory_cli/commands.py`, passed only by `cmd_resume`; tests in `tools/tests/test_adopt.py`.
  - Seam: `bin/factory resume <run>`. Failure paths: no matching run exits 1 with "no run" and the `adopt <branch|spec_dir>` hint, creating no run, worktree or branch.
  - Red: write tests first: plain SpecKit branch `007-x`, no state: `resume 007-x` exits 1, stderr has `no run '007-x'` and `use adopt <branch|spec_dir>`, repo unchanged; `show nope` (another `one_run` caller) has no hint; a pending run still resumes (one `resumed` entry). Run; hint test fails.
  - Implement: `hint=None` keyword appended to the no-run message (D9).
  - Pass: runner green.
  - Done: every case asserted and passing; `tools/tests/test_commands.py` unchanged and green (FR-021).

## Phase 7: Orchestrator and role prose (US1, US2, US4, US5)

- [x] T010 [US1][US2][US4][US5] Edit `core/skills/factory/SKILL.md` per plan.md "Design": argument-hint gains `adopt <branch|spec_dir> [--stage <s>]`; step 0 routes `adopt` to `factory adopt <src> [--stage <s>] --dry-run`, non-zero shows the refusal or candidates and creates nothing (FR-001, FR-003); clean → reuse the report's `pending` file unless ended (ended: replace), else create it with `branch`, `spec_dir`, `feature` = spec title; preflight; adoption grill replacing steps 2-3 (summary, `needs_clarification` first, chain recommending `full` at `tasks`/`analyze`, entry stage with inferred recommended, same frontier and cruise rules) (FR-010); declined → `set-status aborted` (FR-011); confirmed → `brief.md`, `checkpoint grill --next worktree`, `factory adopt <src> --stage <chosen>` replacing step 4; failure keeps the pending run; continue under "Resume" (FR-018); step 7 passes `adopted_base` (FR-019); step 8 adoption line (FR-020). Exempt: `core/skills/factory/SKILL.md` - documentation only. Done: each FR cited by a prose step; `SHELL`/`ASK` only, no harness-specific invocation.

- [x] T011 [P] [US1] Edit `core/skills/factory/references/state.md`: `adopted` block and validation, `adopted` event and its only writer, pending adoption name `<repo-name>-adopt-<branch>` and sole-pending rule, CLI line `adopt <src> [--stage <stage>] [--dry-run]` with exit codes 0/1/3/5, `resume`'s hint. Exempt: `references/state.md` - documentation only. Done: schema, event, pending name and command documented.

- [x] T012 [P] [US4][US5] Edit `core/roles/spec-builder.md`: `specify`, `plan` and `tasks` edit an existing `spec.md`, `plan.md` or `tasks.md` in place when state has `adopted` (FR-024); `analyze` reads `git show <adopted.base_commit>:<spec_dir>/tasks.md`, excludes task IDs checked there from the blocking test-scope check and lists them under "Pre-adoption tasks"; renumbered or new tasks get the full check (FR-025). Exempt: `core/roles/spec-builder.md` - documentation only. Done: both rules stated in their stage bullets.

- [x] T013 [P] [US5] Edit `core/roles/spec-conformance.md` (ENG-2 `Red:` lines on `<adopted_base>..HEAD` only; ENG-1 commit evidence skipped for tasks checked at `<adopted_base>`), `core/roles/code-standards.md` (ENG-3 on `<adopted_base>..HEAD` only), `core/roles/review-judge.md` (confirms none against pre-adoption work) and `core/roles/retro.md` (states adoption, source, chosen stage). Reviewers still review all of `base...HEAD`, listing earlier commits and skipped tasks as pre-adoption. Exempt: the four role files - documentation only. Done: each rule stated (FR-019, FR-020, SC-005).

## Phase 8: Polish and verification

- [x] T014 Build and neutrality check: run the build command (five harnesses into a temp `FACTORY_HOME`, `bash -n install.sh`); `git diff --stat origin/main -- tools/render.py install.sh` empty; `test -z "$(git ls-files -- dist/)"` (constitution III; FR-023, SC-006). Exempt: verification only. Done: build exits 0; both checks pass.

- [ ] T015 Final verification: `python3 -m unittest discover -s tools`. Exempt: verification only. Done: all tests pass, or any failure is shown pre-existing on `origin/main` and recorded here; zero new failures (SC-004).

## Dependencies

- T001 first (constitution I).
- T002 before T006-T008 (the write validates `adopted`).
- T003 → T004 → T005 (growing `inspect`); T006 after T004 (re-inspection); T007 after T006; T008 after T005 and T007.
- T009 after T002 (separate function in `commands.py`).
- T010 after T003-T009 (prose calls the new command); T011-T013 parallel with each other and T010.
- T002-T009 share `tools/tests/test_adopt.py` and the CLI modules: sequential.
- T014, T015 last.

## Implementation Strategy

MVP = T001-T004, T006, T007: schema, safe preview with every refusal, and the `branch`-shape write with rollback (US1, US2, the SpecKit default). Then other shapes (T005, T008), the resume hint (T009), prose (T010-T013), verification (T014-T015).

## Coverage

| Requirement | Tasks |
|---|---|
| FR-001, FR-010, FR-011, FR-018 | T010 |
| FR-002, FR-003, FR-006 | T003, T006 |
| FR-004, FR-005 | T003, T005, T006, T008 |
| FR-007 | T004, T005, T006 |
| FR-008, FR-009 | T003, T006 |
| FR-012, FR-014 | T006 |
| FR-013 | T007, T008 |
| FR-015, FR-016, FR-017 | T002, T006 |
| FR-019, FR-020 | T010, T013 |
| FR-021 | T009 |
| FR-022 | T006 |
| FR-023 | T001, T010-T014 |
| FR-024, FR-025 | T012 |
| SC-001..SC-006 | T003-T009, T001 (validation plan), T014, T015 |
