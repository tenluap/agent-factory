---
description: "Task list for 024-orchestrator-gaps"
---

# Tasks: Close Orchestrator Bookkeeping Gaps

**Input**: `specs/024-orchestrator-gaps/` (spec.md, plan.md, research.md, data-model.md, contracts/cli.md, quickstart.md)

**Tests**: Required (engineering.md). Each behaviour-changing task is one commit unit: failing test (red proof), implementation, passing check, committed together. Runner: `python3 -m unittest discover -s tools` (existing). Seams and failure paths: plan.md "Test seams" (scope confirmed by the plan's `Confirmed:` line, remediate Q1). Tests drive the CLI through `Sandbox.cli` in `tools/tests`. CLI code lives in `core/skills/factory/bin/factory_cli/`. Build: `export FACTORY_HOME="$(mktemp -d)"; for h in claude-code opencode codex copilot zcode; do python3 tools/render.py "$h" || exit 1; done; bash -n install.sh` (renders into a temp `FACTORY_HOME`; `dist/` is never committed).

No design context: every task is a non-UI code or documentation task; none carries `[UI]`.

Each commit body carries `Red: <test name> failed as expected` and a `New: <symbol> - <reason>` line per new function (engineering.md).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallel-safe (different files, no dependency)
- **[Story]**: US1-US4 from spec.md

## Phase 1: Setup

- [x] T001 Record the four behaviour changes in `DESIGN.md` before any code (FR-019, Constitution I): State CLI / review loop - `checkpoint review` derives `review.round` from `factory/reviews/round-<n>/verdict.json` (never decreases), `checkpoint fix` increments `review.fix_rounds` once per fix stage with the `remediate` stage-guard idempotency (ADR 0006) and skips a legacy reservation in `review.pending_design_fix` whose `attempt` equals the counter; design reservations no longer pre-increment (cleared, then `checkpoint fix --next review` counts the attempt); both checkpoints return `review: {round, fix_rounds}`; relay - `answer --question '<json>'` and the immutable record `<spec_dir>/factory/relay/<stage>-<qid>.md` for `requires_user` questions, committed with the answer; "Overrun detection and recording" - detected detail `<role> ran <excess>s past its <seconds>s budget (<total>s total) without a self-report`, excess rounded up; "Time budget" - `budget.review_full_s` (default 600, never below the normal budget) for reviewer roles on round 1 or `--full`, delta rounds and non-reviewers unchanged, `review-judge` excluded.
  - Exempt: `DESIGN.md` - documentation only.
  - Done: each of the four changes named in `DESIGN.md`; `git diff --stat` touches only `DESIGN.md`.

## Phase 2: Foundational

None: every unit extends an existing command and test module.

## Phase 3: User Story 1 - Review and fix counters written by the CLI (P1) - MVP

**Goal**: `review.round` and `review.fix_rounds` need no hand edit.
**Independent test**: `python3 -m unittest tools.tests.test_commands -v` passes the new checkpoint tests.

- [x] T002 [US1] `checkpoint review` derives `review.round` and returns the `review` object, in `core/skills/factory/bin/factory_cli/commands.py` `cmd_checkpoint`; tests in `tools/tests/test_commands.py` (new class `ReviewCounterTests`).
  - Seam: S1 `factory checkpoint review|fix`. Failure path: S1(b) no `round-<n>/verdict.json` present leaves `review.round` unchanged.
  - Red: tests first: run at stage `review` with `reviews/round-1/verdict.json` and `round-2/verdict.json` written under `<worktree>/<spec_dir>/factory/` gives `review.round == 2` and result `review == {"round": 2, "fix_rounds": 0}`; stored round 3 with only `round-2` stays 3; no verdict folder (S1(b)) keeps the stored value; `round-x` folders ignored. Run; fails on the missing derivation.
  - Implement: when `stage == "review"` and the run has a worktree, inside `mutate` set `review.round = max(current, highest n)` over `round-<n>/verdict.json` (integer `n` only); add `"review": {"round", "fix_rounds"}` to the result for `review` and `fix`, including the commit-failure return (FR-001, FR-004).
  - Pass: runner green.
  - Done: tests pass; a fixture with no `reviews/` folder keeps every existing checkpoint test green.

- [x] T003 [US1] `checkpoint fix` increments `review.fix_rounds` with stage-guard idempotency, in `commands.py` `cmd_checkpoint`; tests in `ReviewCounterTests` (depends on T002).
  - Seam: S1. Failure paths: S1(a) commit failure after the state write, then retry, increments once; S1(c) `review.pending_design_fix` `{attempt: n}` equal to the counter skips the increment; S1(d) repeated `checkpoint fix` after the stage moved on skips the increment.
  - Red: tests first: run at stage `fix`, `checkpoint fix` gives `fix_rounds` 1 and result `review.fix_rounds == 1`; S1(a) reuse the `CheckpointCommitFailureTests` commit-failure injection, then retry: still 1; S1(c) reservation with `attempt == fix_rounds` leaves it unchanged; S1(d) second `checkpoint fix` with stage `review` leaves it unchanged; two review rounds plus two fix rounds end at round 2 / fix_rounds 2 (SC-001; the value the SC-002 cap reads). Run; increments are missing.
  - Implement: inside `mutate`, beside the `remediate` guard: when `stage == "fix" and s["stage"] == "fix"`, increment unless `pending_design_fix` is a dict whose `attempt` equals the current counter (FR-002, FR-003).
  - Pass: runner green.
  - Done: tests pass; `fix_rounds` reaches 2 after two fix rounds (SC-002 cap input); existing `test_bench.py` still reads the counters.

## Phase 4: User Story 2 - Relay records rendered by the CLI (P2)

**Goal**: `requires_user` answers leave one immutable record, committed with the answer.
**Independent test**: new `RelayRecordTests` in `tools/tests/test_commands.py` pass.

- [x] T004 [US2] `answer --question '<json>'` stores the full question, in `core/skills/factory/bin/factory_cli/cli.py` (new flag) and `commands.py` `cmd_answer`; tests in `tools/tests/test_commands.py` (new class `RelayRecordTests`).
  - Seam: S2 `factory answer [--question]`. Failure paths: S2(b) malformed `--question` JSON or `id` not equal to `<qid>` exits 1, nothing written; S2(c) qid or stage outside `[A-Za-z0-9_-]+` exits 1 only when a record is due (`requires_user: true` question on a worktree run).
  - Red: tests first: open round storing `{"id": "R2-Q1"}` only, `answer R2-Q1 A --question '<full json>'` stores the full question and the answer; absent id appends it to the open round; S2(b) `--question '{'` and `--question '{"id":"Q9"}'` each exit 1 with `state.json` bytes and `git log` unchanged; S2(c) on a worktree run, `answer '../x' A --question '{"id":"../x","requires_user":true}'` and a `requires_user: true` answer with `--stage 'a/b'` each exit 1 with `state.json` bytes, `git log` and the absence of `relay/` unchanged; the same unsafe qid on a question without `requires_user` is answered as today (FR-009). Run; flag unknown.
  - Implement: parse and validate before any `write_run`; replace an id-only stored question, never a full one (FR-005); qid/stage pattern check before any write, applied only when a record is due.
  - Pass: runner green.
  - Done: tests pass; `answer` without `--question` tests unchanged and green.

- [x] T005 [US2] Render the relay record for `requires_user` answers, in `commands.py` (new `render_relay_record`, called only by `cmd_answer`); tests in `RelayRecordTests` (depends on T004).
  - Seam: S2. Failure paths: S2(a) existing record with a different answer exits 1 naming the path, state and files unchanged; S2(d) pending run without worktree stores the answer and writes no record.
  - Red: tests first: worktree run, `requires_user: true` question answered explicitly writes `<spec_dir>/factory/relay/<stage>-<qid>.md` with stage, qid, title, text, every option (id, label, description), answer, time and origin (`explicit`; `auto`; `cruise_override` under cruise), the result's `record` field equals that path, and the latest commit contains both `state.json` and the record (FR-007); identical re-answer returns `{"answered": qid, "unchanged": true}` with no new commit; S2(a) different answer exits 1, stderr names the path, record bytes and `state.json` unchanged; S2(d) pending run stores the answer, no `relay/` dir; question without `requires_user` writes no record (FR-009). Run; no record.
  - Implement: existence/answer check before the state write; render after the state write and before `commit_worktree` (which stages `spec_dir`); never overwrite (FR-006, FR-008).
  - Pass: runner green.
  - Done: tests pass; SC-003 holds in the test fixture.

## Phase 5: User Story 3 - Detected overrun states the real excess (P3)

**Goal**: detected detail names excess, budget and total.
**Independent test**: `OverrunDetectionTests` in `tools/tests/test_budget.py` pass.

- [x] T006 [US3] Fix the detected-overrun wording in `commands.py` `overrun_issue`; tests in `tools/tests/test_budget.py` `OverrunDetectionTests`.
  - Seam: S4 `factory ledger-add [--round n | --full]` overrun detection. Failure paths: S4(a) duration 1 ms over budget rounds excess up to 1 s; S4(b) self-reported overrun keeps its detail unchanged.
  - Red: tests first: 319000 ms on a 300 s budget gives `spec-conformance ran 19s past its 300s budget (319s total) without a self-report` (SC-004); S4(a) 300001 ms gives `ran 1s past its 300s budget (301s total)`; S4(b) self-report detail stored verbatim. Run; old wording fails.
  - Implement: `excess = ceil((duration_ms - seconds*1000)/1000)`, `total = ceil(duration_ms/1000)` (FR-011, FR-012).
  - Pass: runner green.
  - Done: tests pass.

## Phase 6: User Story 4 - Round-1 reviewers get a larger budget (P3)

**Goal**: full-diff reviewer spawns resolve `review_full_s` (default 600) for both budget read and overrun detection.
**Independent test**: `ResolutionTests`, `BudgetCommandTests` and `OverrunDetectionTests` pass.

- [x] T007 [US4] `budget <role> [--round n | --full]`, in `core/skills/factory/bin/factory_cli/budget.py` (`REVIEWER_ROLES`, `resolve(role, config, full=False)`), `commands.py` `cmd_budget` and `cli.py`; tests in `tools/tests/test_budget.py`.
  - Seam: S3 `factory budget <role> [--round n | --full]`. Failure paths: S3(a) missing or malformed `review_full_s` / config falls back to 600 without failure; S3(b) non-positive or non-integer `--round` exits 2.
  - Red: tests first: `budget spec-conformance --round 1` gives 600 and `"full": true`; `--full` same; `--round 2` gives 300 and `"full": false`; `review_full_s: 900` gives 900; role override 1200 with `--round 1` gives 1200 (never below normal); `review-judge --round 1` and `code-build --full` resolve as today (FR-014, FR-015); S3(a) `review_full_s` of `"x"`, `0`, `-5`, absent, and a non-dict config each give 600, exit 0; S3(b) `--round 0`, `--round -1`, `--round x` exit 2; `--round 1 --full` together exits 2 (contract). Run; flags unknown.
  - Implement: `REVIEWER_ROLES` = the five reviewer roles; `resolve` returns `max(normal, review_full_s if positive int else 600)` when `full` and role is a reviewer; `--round 1` or `--full` set `full`; output adds `"full"` (FR-013, FR-017).
  - Pass: runner green.
  - Done: tests pass; existing `budget <role>` tests unchanged.

- [x] T008 [US4] `ledger-add [--round n | --full]` compares reviewer spawns to the budget they were given, in `cli.py`, `commands.py` `cmd_ledger_add` and `overrun_issue`; tests in `OverrunDetectionTests` (depends on T006, T007).
  - Seam: S4. Failure paths: S4(a) and S4(b) re-asserted under the round-1 budget.
  - Red: tests first: `security-reviewer` 590 s with `--round 1` and no config records no issue (SC-005); 601000 ms with `--round 1` records `ran 1s past its 600s budget (601s total)`; 310 s with `--round 2` records an overrun on 300 s; self-report with `--full` stored unchanged; `--round 0` and `--round 1 --full` each exit 2. Run; flags unknown.
  - Implement: pass `full` through to the shared `budget.resolve` call in `overrun_issue` (FR-016).
  - Pass: runner green.
  - Done: tests pass.

## Phase 7: Polish & documentation

- [x] T009 [P] Document the CLI changes in `core/skills/factory/references/state.md`: "Checkpoint" (review round derivation, fix counter with stage guard and design reservation, `review` result object), "CLI" (`budget <role> [--round <n>|--full]` with `"full"` and `review_full_s` resolution; `ledger-add ... [--round <n>|--full]`; `answer <qid> '<answer>' [--question '<json>'] ...` with the relay record, its no-op and exit-1 refusals, and the qid/stage pattern), "Schema" (`budget.review_full_s` config key; `review.round` / `review.fix_rounds` written by `checkpoint`; the reservation sentence at state.md:154 restated as: reservation stores `attempt` = counter + 1 without incrementing, cleared after the attempt, then `checkpoint fix --next review` counts it); "Resume" step for `verify`/`review`/`fix` (state.md:238): design branch - clear the completed reservation, then `checkpoint fix --next review`, then verify/re-review; ordinary branch - on resume at stored stage `fix` with no reservation (a fix round ran or was interrupted before it was counted), re-run verify, then `checkpoint fix --next review` (one increment; the stage guard makes a repeat safe), then re-review, so the cap counts that round (FR-002, FR-019, SC-002). Amend `core/skills/factory/references/design-code-mapping.md` §5 to the same order: drop "increment it" before the reservation, store `attempt` as the next counter value, and after a completed attempt clear the pending marker, then run `checkpoint fix --next review` (one increment) before verification/re-review; a legacy reservation whose `attempt` equals the counter is not counted again (FR-003).
  - Exempt: `core/skills/factory/references/state.md`, `core/skills/factory/references/design-code-mapping.md` §5 - documentation only.
  - Done: each flag and rule above appears, including the ordinary `fix` resume running `checkpoint fix --next review` before re-review; `git grep -n 'increment it, save' core/skills/factory/references/design-code-mapping.md` prints nothing; neutral verbs only, no harness names (FR-020).

- [x] T010 [P] Update `core/skills/factory/SKILL.md` step 7 and the "Time budget"/"Cost ledger" policies: pass `--round <n>` (or `--full` on an escalated re-run) to `budget` before each reviewer spawn and to `ledger-add` after it (FR-018); replace "increment `review.fix_rounds`" with `checkpoint fix --next review` after each fix round (never the default successor, which is `approver`), `checkpoint review --next fix` when the verdict needs another round and `checkpoint review --next approver` when it is clean or the cap is reached, and the checkpoint's `review.fix_rounds` result as the cap read (SC-002); for active design runs follow design-code-mapping.md §5: replace "reserve/persist that increment" with persisting `review.pending_design_fix` (`attempt` = counter + 1) and `stage: fix` before spawning, without incrementing; clear the reservation after the attempt, then `checkpoint fix --next review`; document the review-stage relay path: verdict-raised `requires_user` question stored with a round-unique id such as `R2-Q1`, answered through `answer <qid> '<answer>' --question '<json>'`, cited by `<spec_dir>/factory/relay/<stage>-<qid>.md`, and under cruise answered only with `--cruise-override` (FR-010).
  - Exempt: `core/skills/factory/SKILL.md` step 7 - documentation only.
  - Done: `git grep -n 'increment `review.fix_rounds`' core/` prints nothing; `--round`, `relay/`, `checkpoint fix --next review` and the `review.fix_rounds` cap read appear in step 7 (SC-002).

- [x] T011 Final verification (depends on T001-T010): run the build command, `python3 -m unittest discover -s tools`, and `test -z "$(git ls-files -- dist/)"` (FR-020, FR-021, SC-006). Walk `quickstart.md`.
  - Exempt: verification only, no file change.
  - Done: all three commands exit 0.

## Dependencies & Execution Order

- T001 first (Constitution I).
- US1: T002 then T003. US2: T004 then T005. US3: T006. US4: T007 then T008 (T008 also after T006).
- Stories are independent of each other after T001; T009/T010 after the code they document; T011 last.

## Parallel Example

After T001: T002, T004, T006 touch different functions but share `commands.py`; run them sequentially in one worktree, or in parallel only on separate branches. T009 and T010 are parallel (different files).

## Implementation Strategy

MVP = T001-T003 (counters, fix-round cap reliable). Then US2, US3, US4 in order; docs; verification.

## Fix round 1

These repairs supersede T001/T009/T010's original reservation and resume order; the checked entries above record the work originally completed, not the current contract. Scope extension and acceptance are recorded in plan.md.

- [x] F001 Fix identical answer retry after a failed commit; test the injected failure and committed retry at S2.
- [x] F002 Add the S1 design-reservation checkpoint writer and atomic count/clear, including legacy resume; document fixer completion, verification, checkpoint, then re-review for both design and ordinary resumes.
- [x] F003 Pass full question JSON through every relay answer path; test a protected plan-stage answer and its record at S2.
- [x] F004 Cover an unsafe stage with no record due at S2(c).
- [x] F005 Run the required build and full test suite for the fix round (five harness renders and shell syntax passed; 641 tests passed; no tracked `dist/` files).
