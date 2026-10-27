---
description: "Task list for: agent time budget, session issue backlog, benchmark"
---

# Tasks: Agent time budget, session issue backlog, benchmark

**Input**: Design documents from `/specs/010-agent-time-budget/` — [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/cli.md](contracts/cli.md), [quickstart.md](quickstart.md)

**Tests**: mandatory (factory override of "Tests are OPTIONAL"). Every implementation task is immediately preceded by a failing-test task naming the seam it targets from plan.md "Test seams"; a task covered by a plan exemption carries that exemption instead of a test task.

**Format**: `- [ ] [TaskID] [P?] [Story?] Description with file path`
- **[P]**: parallelizable (different files, no dependencies on incomplete tasks)
- **[Story]**: `[US1]`..`[US4]` in user-story phases only; Setup, Foundational and Polish carry none
- Seam names match plan.md "Test seams" exactly; red proof per `references/engineering.md` (ENG-2) goes in each task's commit body.

## Phase 1: Setup

**Purpose**: behaviour source of truth first (constitution I).

- [X] T001 Record the "Time budget, issues, improvement backlog, benchmark" behaviour section in `DESIGN.md` first — Exempt: `DESIGN.md` - documentation only, no executable behavior.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: schema v5 and the shared issue append path every story writes through.

**⚠️ CRITICAL**: no user story work begins until this phase is complete.

- [X] T002 [P] Failing test for seam: state schema v5 — `issues[]` validation (including the `partial_return` mark), read acceptance of schema 1–5, v5 upgrade on first write with additive shape (every v4 key keeps its name and shape, `issues[]` the only new top-level key), append-only — in the existing `tools/tests/test_state.py` (extended) with fixture `tools/tests/fixtures/state-v5.json`
- [X] T003 Implement schema v5 in `core/skills/factory/bin/factory_cli/state.py` — `VERSION` 5, issue record validation (closed kind/cause vocabularies naming the offending location; `partial_return` accepted only on `overrun`/`retry` of the file-writing roles), upgrade (seam: state schema v5) (depends: T002)
- [X] T004 [P] Failing test for seam: issue-add writer — the shared writer issue append path: one record per event, closed kinds `overrun|agent-failure|retry|halt|verify-fail`, cause required for `overrun`, stall rule result over every partial-return record (`--partial-return` marks a `partial` return's stop and counts whatever the stop reason; an unmarked record — a failure-policy retry, a post-hoc detection — never counts, and the mark is refused for never-stopped roles) — in `tools/tests/test_issues.py`
- [X] T005 Implement `factory issue-add <kind> <stage> <role> --detail --duration-ms [--cause] [--commit] [--partial-return]` and the shared `append_issue(...)` helper with stall counting keyed on `partial_return` (`stalls.consecutive_no_commit`, cap 3) in `core/skills/factory/bin/factory_cli/commands.py`, routed in `core/skills/factory/bin/factory_cli/cli.py` (seam: issue-add writer) (depends: T004, T003)

**Checkpoint**: foundation ready — user stories can begin.

---

## Phase 3: User Story 1 - Every spawned agent works inside a time budget (Priority: P1) 🎯 MVP

**Goal**: every spawn carries a deadline; a file-writing role past it commits the unit in flight and returns `partial` with an overrun report; a fresh spawn resumes; reviewers and the judge finish and are recorded post-hoc.

**Independent Test**: set a small budget for one file-writing role, run that stage, and observe the stopped return with its cause, the recorded overrun, and a continuation that resumes from committed progress.

- [X] T006 [P] [US1] Failing test for seam: budget check — resolution order `budget.roles[<role>]` positive integer → `budget.default_s` positive integer → 300, malformed/absent config never fails, `deadline` = now + seconds ISO UTC, `orchestrator` valid — in `tools/tests/test_budget.py`
- [X] T007 [US1] Implement budget resolution and deadline derivation in `core/skills/factory/bin/factory_cli/budget.py` and the `factory budget <role>` read command in `commands.py`/`cli.py` (seam: budget check) (depends: T006)
- [X] T008 [US1] Failing test for seam: budget check — `ledger-add` overrun detection: `--overrun` self-report wins, duration over budget alone yields cause `unreported`, no issue when neither holds, exactly one issue when both do — the recorded issue carries `partial_return` only when `--partial-return` is passed, false otherwise — in `tools/tests/test_budget.py` (depends: T004)
- [X] T009 [US1] Implement `factory ledger-add ... --overrun '<json>' [--partial-return]` and its single-issue detection/dedupe (the recorded issue carries the `partial_return` mark when the spawn returned `partial`) in `core/skills/factory/bin/factory_cli/commands.py` (seam: budget check) (depends: T008, T005, T007)
- [X] T010 [P] [US1] Failing test for seam: envelope partial/overrun shape — `overrun` is an object with a known cause and non-empty detail when present on a `partial` envelope — in the existing `tools/tests/test_envelope.py` (extended)
- [X] T011 [US1] Implement envelope `overrun` validation in `core/skills/factory/bin/factory_cli/checks.py` (seam: envelope partial/overrun shape) (depends: T010)
- [X] T012 [US1] Extend `core/skills/factory/references/protocol.md`: `partial` valid for all file-writing roles (spec-builder, code-build, fixer), `overrun: { "cause", "detail" }` with the closed cause list and the overshoot in `detail` — Exempt: `core/skills/factory/references/*.md` - agent instructions only, no executable behavior.
- [X] T013 [US1] Add "check the clock between units of work; past the deadline finish the unit in flight, commit, return `partial` with the overrun report" to `core/roles/spec-builder.md`, `core/roles/code-build.md`, `core/roles/fixer.md` — Exempt: `core/roles/*.md` - agent instructions only.
- [X] T014 [US1] Extend `core/skills/factory/SKILL.md`: run `factory budget <role>` before every SPAWN/SPAWN_PARALLEL and pass `deadline` in the inputs; re-spawn a `partial` with the same inputs, its stop recorded as exactly one issue marked `--partial-return` (`overrun` for a deadline stop — recorded by `ledger-add` from the self-report `--overrun` or `unreported` from detection; `retry` for any other stop reason — recorded by `issue-add`, which records only what `ledger-add` leaves unrecorded; a failure-policy retry records `retry` unmarked via `issue-add` and never counts); halt after three partial returns of one stage with no new commit, whatever the stop reason, never counting never-stopped roles' records; record orchestrator verify overruns without stopping anything — Exempt: `core/skills/factory/SKILL.md` - agent instructions only.

**Checkpoint**: US1 functional — deadlines bind spawns, overruns stop and resume correctly.

---

## Phase 4: User Story 2 - Everything that went wrong becomes a session issue (Priority: P2)

**Goal**: one issue record per overrun, agent failure, retry, halt and red verify, tagged and groupable.

**Independent Test**: drive each of the five event paths in the automated suite and assert exactly one issue record per event in the run state.

- [X] T015 [P] [US2] Failing test for seam: issue-add writer — the shared append path records `halt` (detail = `--halt-reason`) from `set-status halted` and `verify-fail` (detail = failing commands) from `verify --fail`, exactly once each — in `tools/tests/test_issues.py`
- [X] T016 [US2] Implement issue recording inside `cmd_set_status` (halted) and `cmd_verify` (--fail) in `core/skills/factory/bin/factory_cli/commands.py` via `append_issue(...)` (seam: issue-add writer) (depends: T015, T005)
- [X] T017 [US2] Document schema v5 `issues[]` (record shape, closed vocabularies, append-only) and the issue-recording commands in `core/skills/factory/references/state.md` — Exempt: `core/skills/factory/references/*.md` - agent instructions only.
- [X] T018 [US2] Extend the failure policy in `core/skills/factory/SKILL.md`: a failure-policy retry records `retry` unmarked (`partial_return: false` — not a partial return, never counted by the stall cap), a second failure of the same agent records `agent-failure`, both through `factory issue-add` — Exempt: `core/skills/factory/SKILL.md` - agent instructions only.

**Checkpoint**: US2 functional — every event path writes its issue once.

---

## Phase 5: User Story 3 - The improvement backlog exists only after its run is over (Priority: P2)

**Goal**: the run end is the structural gate: no backlog file before `pr-open`/`aborted`, a ready backlog after, claimable only then.

**Independent Test**: attempt to claim the backlog before and after ending the source run; assert refusal before, presence and claimability after.

- [X] T019 [P] [US3] Failing test for seam: run-end backlog export — no file before run end; atomic export at `pr-open`/`aborted` with `issues[]` verbatim, `totals.compute` output, `factory_sha` (best-effort, `null` allowed), `status: ready`, `exported_at`; zero-issue run exports too — in `tools/tests/test_improvements.py`
- [X] T020 [US3] Implement the backlog export in `core/skills/factory/bin/factory_cli/improvements.py` (temp + `os.replace`) and hook it into `cmd_set_status` for `pr-open|aborted` in `commands.py` (seam: run-end backlog export) (depends: T019, T003)
- [X] T021 [US3] Failing test for seam: backlog surface — `factory improvements` lists every `${FACTORY_HOME}/improvements/*.json` with kind counts and `suggested_feature`; `claim` refuses an unknown name, a non-`ready` status and a discoverable source run that has not ended (message names the run), and stamps `claimed`/`claimed_at` once — in `tools/tests/test_improvements.py` (depends: T020)
- [X] T022 [US3] Implement `factory improvements` and `factory improvements claim <name>` in `core/skills/factory/bin/factory_cli/improvements.py`, `commands.py`, `cli.py` (seam: backlog surface) (depends: T021)
- [X] T023 [US3] Route `/factory improve` in `core/skills/factory/SKILL.md` step 0 to `factory improvements`: show ready backlogs and their `suggested_feature`, stop; starting an improvement run stays manual — Exempt: `core/skills/factory/SKILL.md` - agent instructions only.

**Checkpoint**: US3 functional — the backlog gate is structural.

---

## Phase 6: User Story 4 - Factory versions can be benchmarked before and after (Priority: P3)

**Goal**: replay the same pre-settled fixture headlessly, score a recorded run, compare two scores.

**Independent Test**: score two recorded run states and assert the emitted metrics and the printed delta; assert a fixture run missing a pass condition scores a fail naming it.

- [X] T024 [P] [US4] Create the pre-settled fixture feature `conformance/bench/greet-001/{bench.json,brief.md,state-seed.json,overlay/}` (seed stage `worktree`, `mode.fast: true`, `stop_at: approver`; overlay carries the fixture build/test commands) — Exempt: `conformance/bench/**` - configuration/fixture data, exercised through the listed seams and the build gate.
- [ ] T025 [P] [US4] Failing test for seam: benchmark scorer and compare — every metric emitted (wall/agent/human time, spawns, overruns, issues by kind, token estimates, review/fix rounds), the four conditions `reached-approver`, `last-verify-green`, `no-blocking-findings`, `fixture-acceptance` resolve offline and an unmet one names itself, `compare` prints per-metric delta, the scorer never raises — in `tools/tests/test_bench.py` with fixtures `tools/tests/fixtures/{bench-pass/,bench-fail/}`
- [ ] T026 [US4] Implement `tools/bench.py` `run`/`score`/`compare` — state read through `factory_cli.state`/`totals`/`checks` (FR-017), harness map `claude-code`→`claude -p`, `opencode`→`opencode run`, anything else refused by name; `run` verified by the documented manual path, not the suite (seam: benchmark scorer and compare) (depends: T025, T020)
- [ ] T027 [US4] Document the manual benchmark fallback (run the factory on the fixture to the approver stop, then `score`) in `README.md` and `docs/` — Exempt: `README.md`, `docs/**` - documentation only.

**Checkpoint**: US4 functional — scores comparable across factory versions.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T028 Re-render every harness with the build command (`for h in claude-code opencode codex copilot zcode; do python3 tools/render.py "$h" || exit; done`), run the test command (`python3 -m unittest discover -s tools && bash -n install.sh && test -z "$(git status --porcelain -- dist/)"`) and quickstart §1–2, and leave `dist/` clean and committed — Exempt: `dist/**` - generated output, exercised through the build gate.
- [ ] T029 Apply the plan.md "Spec alignment follow-ups (spec.md wording)" to `specs/010-agent-time-budget/spec.md`: FR-008 adopts the design superset — signature `factory issue-add <kind> <stage> <role> --detail --duration-ms [--cause] [--commit] [--partial-return]`, record `{ at, kind, stage, role, cause, detail, duration_ms, commit, partial_return }`, `--cause` required only for `overrun`; FR-010 and US2 scenario 2 say `retry` records a non-deadline `partial` stop (e.g. low context) — marked `partial_return: true` — and a failure-policy retry — unmarked, never counting toward the stall cap — alike, while a deadline stop is recorded as `overrun` (FR-002), still marked when it is a `partial` return's stop — consistent with FR-004, which counts only `partial` returns; FR-011 and its assumption name the backlog file `<repo-name>-<branch>.json` and the exported sha `factory_sha`, and at first use in US3/SC-003/Key Entities write "the factory version (`factory_sha`)"; add the edge case: the export succeeds with `factory_sha: null` when the factory install is not in a git tree — Exempt: `specs/010-agent-time-budget/spec.md` - specification wording only, no executable behavior (plan.md assigns these follow-ups to the pass that owns `spec.md`).

---

## Dependencies & Execution Order

- **Phase 1 (Setup)**: no dependencies; T001 first (constitution I).
- **Phase 2 (Foundational)**: blocks all stories. T003 ← T002; T005 ← T004, T003.
- **US1 (P1)**: T007 ← T006; T009 ← T008, T005, T007; T011 ← T010; doc tasks T012–T014 follow their story's code.
- **US2 (P2)**: T016 ← T015, T005; independent of US1's budget work.
- **US3 (P2)**: T020 ← T019, T003; T022 ← T021, T020; independent of US1/US2 beyond schema v5.
- **US4 (P3)**: T026 ← T025, T020 (scorer reads exported/recorded state); depends on Foundational.
- **Polish**: T028 after all desired stories (rendered dist must include every change); T029 (spec.md wording follow-ups from plan.md) has no dependencies.

Story order P1 → P2 → P3; US2 and US3 can proceed in parallel with each other once Phase 2 is done.

## Parallel Opportunities

- T002 / T004 (different test files) together; T006 / T010 together; T015 / T019 / T025 across stories (different test files) once their phases are open; T024 alongside T025.
- Same-file test tasks (T006 vs T008; T019 vs T021) are sequential by design.

## Implementation Strategy

MVP first: Phase 1 → Phase 2 → US1 (deadline, stop, resume, recorded overrun), then validate it alone before US2–US4. Each task commits test and implementation together with its red proof (ENG-2/ENG-3); tasks beyond the plan's listed seams stop and report (ENG-4).
