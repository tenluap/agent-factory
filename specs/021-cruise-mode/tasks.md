---
description: "Task list for 021-cruise-mode"
---

# Tasks: Cruise mode

**Input**: `specs/021-cruise-mode/` (spec.md, plan.md)

**Tests**: Required (engineering.md). Each behaviour-changing task is one commit unit: failing test (red proof), implementation, passing check, committed together. Runner: `python3 -m unittest discover -s tools` (existing). Seams and failure paths: plan.md "Test seams" (scope confirmed: Q1 accepted 2026-11-04). All new tests go in `tools/tests/test_cruise.py` (new file, reason in plan.md); CLI tests run `core/skills/factory/bin/factory` as a subprocess against temp repos and states, as `tools/tests/test_models.py` and `tools/tests/test_state.py` do.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallel-safe (different files, no dependency)
- **[Story]**: US1-US6 from spec.md

## Phase 1: Setup

- [ ] T001 Update `DESIGN.md` ("Modes", "Interactive steps", "Approver", "Validation plan"): `mode.cruise` (opt-in `--cruise`/`--no-cruise`, last wins, implies fast, `--no-fast` conflict exits 5), `cruise_override` marker shape and invariants, `factory mode`, `resume` mode flags, `answer`/`decisions-add --cruise-override` with the cruise-only guard, `pr` gate ignoring marked records, approver veto-list grouping, notify only on real waits, per-adapter `no_prompt_launch`; setup-offer records at `grill` (`setup-speckit`, `setup-commands`, `intake`) and `review` (`setup-impeccable`), `STAGES` unchanged; missing or stale seam at implement or fix still halts (ENG-4); validation-plan entry naming one cruise fixture run of a tiny feature that checks SC-001 (no `questions` timeline entry left waiting before the approver entry), SC-002 (`git ls-remote` shows no branch and no PR exists before the user's Approve) and SC-003 (every cruise-made override sits in the veto list's cruise-override group); cites ADR 0014. Also update `README.md` "Usage" and "Flags": a `/factory <feature> --cruise` line, a `/factory resume <branch> --cruise` example, `--cruise` and `--no-cruise` table rows (implies fast, `--no-fast` conflict, stops at the approver, never publishes without Approve), and the `--fast` row's "Never automated" note pointing to cruise (FR-022). `CONTEXT.md` (cruise mode, cruise override, veto list, no-prompt launch option; amended protected question and seam confirmation) and ADR 0014 were written at grill-with-docs (FR-022): check only, no rewrite. Exempt: `DESIGN.md`, `README.md` - documentation only (constitution I: lands before core/adapter edits). Done: every item above named in `DESIGN.md`; the validation-plan entry names the fixture run and SC-001..SC-003 checks; `README.md` lists both flags and the resume example; the four terms present in `CONTEXT.md`; ADR 0014 present.

## Phase 2: Foundational - state schema (blocks every CLI task)

- [ ] T002 [US4][US1] Validate `mode.cruise` and `cruise_override` in `core/skills/factory/bin/factory_cli/state.py` (`validate_state`, `_check_decisions`, `_check_round`); tests in new `tools/tests/test_cruise.py`.
  - Seam: `factory_cli.state.validate_state`. Failure paths: non-boolean `mode.cruise`; `cruise: true` with `fast: false`; non-boolean `cruise_override` on a decision or relay answer; marker with `auto: false`; marker on kind `approved` or at stage `approver`.
  - Red: write tests first: a pre-feature state (no `cruise`, no marker) and the existing fixtures validate clean (FR-004, SC-004); `mode.cruise: true, fast: true` valid; decision `{kind: answer, auto: true, cruise_override: true}` valid; decision `{kind: gate-override, stage: analyze, auto: true, cruise_override: true}` valid; relay answer with `auto: true, cruise_override: true` valid; each failure path above yields a problem naming its location (only these; the existing "a gate decision is never auto" coverage stays in `tools/tests/test_state.py`). Run; the failure-path tests fail.
  - Implement: boolean check on `mode.cruise`; `cruise` requires `fast`; marker boolean when present, `true` requires `auto: true`, rejected on kind `approved` or at stage `approver`; a marked `gate-override` is exempt from "a gate decision is never auto" (the `analyze`-only rule is T006's `decisions-add` guard, clarify Q1). No version bump.
  - Pass: runner green.
  - Done: every listed case asserted and passing; existing state tests unchanged.

## Phase 3: User Story 4 - Turning cruise on and off (P2, needed by every other story)

- [ ] T003 [US4] Add `resolve_mode(base, flags)` to `core/skills/factory/bin/factory_cli/state.py`, `cmd_mode` to `core/skills/factory/bin/factory_cli/commands.py`, `mode` dispatch and USAGE line to `core/skills/factory/bin/factory_cli/cli.py`; tests in `tools/tests/test_cruise.py`.
  - Seam: `bin/factory mode [flags...]`. Failure paths: `--cruise` with `--no-fast` in either order exits 5 naming the conflict; unknown flag exits 5.
  - Red: tests first: no flags prints `{"chain": "lite", "fast": true, "cruise": false}`; `--cruise` gives `fast: true, cruise: true`; `--no-fast --cruise --no-cruise` gives `fast: false, cruise: false` (pairs last-wins); `--cruise --no-cruise` and `--no-cruise --cruise` resolve to the last; `--no-cruise` alone leaves `fast` unchanged; `--full` / `--lite` set `chain`; `--cruise --no-fast`, `--no-fast --cruise` and `--no-fast --fast --cruise` (presence rule: `--no-fast` anywhere conflicts even when `fast` ends on, FR-003) exit 5 with stderr naming both `--cruise` and `--no-fast`; `--bogus` exits 5; the command writes no file (temp `FACTORY_HOME` and repo unchanged). Run; fails (unknown command).
  - Implement: `resolve_mode` applies flags in argv order, sets `fast` true when `cruise` ends on, raises on cruise-on plus `--no-fast`; `cmd_mode` uses the default base and prints JSON; the conflict reuses the usage exit 5 path.
  - Pass: runner green.
  - Done: output and exit codes match the tests; nothing written.

- [ ] T004 [US4] Accept mode flags on `resume` in `core/skills/factory/bin/factory_cli/cli.py` and `cmd_resume` in `core/skills/factory/bin/factory_cli/commands.py`, through `state.resolve_mode`; tests in `tools/tests/test_cruise.py`.
  - Seam: `bin/factory resume <run> [mode flags]`. Failure paths: `--no-fast` with cruise on from a flag exits 5, state and HEAD unchanged, no `resumed` entry; `--no-fast` with cruise stored on and no `--no-cruise` exits 5 likewise.
  - Red: tests first on a halted run fixture: `resume <run> --cruise` stores `mode.cruise: true, fast: true` and appends one `resumed` entry in the same commit; a stored state without `cruise` resumed with no flags reads as off and stays valid (US4 scenario 7); `--no-cruise` on a cruise run sets `cruise: false`, keeps `fast`; `--no-cruise --no-fast` on a cruise run sets both off; `--cruise --no-fast` exits 5; a cruise-stored run resumed with `--no-fast` exits 5; for both failures `state.json` bytes, `git rev-parse HEAD` and the `history` length are unchanged. Run; fails (resume rejects flags).
  - Implement: parse `--lite|--full|--fast|--no-fast|--cruise|--no-cruise` after `<run>`; base = stored mode with absent `cruise` read as false; resolve before any write; mode and `resumed` entry in one `write_run` mutation.
  - Pass: runner green.
  - Done: every listed case asserted and passing; existing resume tests unchanged.

## Phase 4: User Stories 1, 3, 5 - Recording cruise overrides (P1)

- [ ] T005 [US1][US3] Add `--cruise-override` to `answer` in `core/skills/factory/bin/factory_cli/cli.py` and `cmd_answer` in `core/skills/factory/bin/factory_cli/commands.py`; `settled_answers` carries the marker into `decisions`; tests in `tools/tests/test_cruise.py`.
  - Seam: `bin/factory answer <qid> <answer> --cruise-override`. Failure paths: run without `mode.cruise: true` refused with exit 1, state unchanged.
  - Red: tests first: on a cruise run with an open round holding a `requires_user` question, `answer Q1 A --cruise-override` stores `{auto: true, cruise_override: true}`; `checkpoint` migrates it into `decisions` with the marker kept and kind `answer`; `show` lists it in the veto list with the marker; an ordinary `--auto` answer carries no marker; on a run with `mode.cruise` false or absent the command exits 1, stderr names cruise mode, `state.json` bytes and HEAD unchanged. Run; fails (unknown flag).
  - Implement: guard reads the target run's `mode.cruise` before `write_run`; the marker implies `auto`; `settled_answers` copies `cruise_override` when true.
  - Pass: runner green.
  - Done: every listed case asserted and passing.

- [ ] T006 [US1][US5] Add `--cruise-override` to `decisions-add` in `core/skills/factory/bin/factory_cli/cli.py` and `cmd_decisions_add` in `core/skills/factory/bin/factory_cli/commands.py`; tests in `tools/tests/test_cruise.py`.
  - Seam: `bin/factory decisions-add ... --cruise-override`. Failure paths: run without `mode.cruise: true` refused; `--kind approved` with the marker refused; `--kind gate-override` with the marker at a stage other than `analyze` refused.
  - Red: tests first on a cruise run: `decisions-add grill intake delivery --cruise-override` records kind `answer`, `auto: true`, `cruise_override: true`; `decisions-add analyze analyze-exhaustion 'proceed to implement' --kind gate-override --cruise-override` records it and `checkpoint analyze --next implement` then succeeds (FR-011); each failure path exits 1 with a message naming the reason and leaves `state.json` bytes and HEAD unchanged; without the flag `decisions-add` behaves as today. Run; fails (unknown flag).
  - Implement: the same two-line cruise guard as T005, inline in `cmd_decisions_add` (no shared helper, plan "Writer guard"); refuse marker with `approved` and with `gate-override` outside `analyze` before writing; marked records get `auto: true`.
  - Pass: runner green.
  - Done: every listed case asserted and passing.

## Phase 5: User Story 2 - Publishing needs the user's Approve (P1)

- [ ] T007 [US2] Make the `pr` approver candidates used by both `gate_violation` and `permitting_decision` in `core/skills/factory/bin/factory_cli/checks.py` ignore records carrying `cruise_override`; tests in `tools/tests/test_cruise.py`.
  - Seam: `factory_cli.checks.gate_violation` into `pr`. Failure paths: a record carrying `cruise_override` at `approver` never permits `pr`.
  - Red: tests first on hand-built state dicts (bypassing `validate_state`, so a forged record is reachable): a user `approved` record (`auto: false`, no marker) permits `pr`; an `approved` or `gate-override` record at `approver` with `cruise_override: true` makes `gate_violation(state, "pr")` return a violation. Assertions go through `gate_violation` into `pr` only (clarify Q1; the implement gate is covered by T006). Run; the forged-record test fails.
  - Implement: filter marked records out of the `approver` candidates once; `gate_violation` and `permitting_decision` for `pr` both use that filtered list.
  - Pass: runner green.
  - Done: every listed case asserted and passing; `tools/tests/test_gates.py` unchanged and green (FR-015, FR-016, SC-002).

## Phase 6: Orchestrator and reference prose (all stories)

- [ ] T008 [US1][US2][US3][US4][US5][US6] Edit `core/skills/factory/SKILL.md` per plan.md "Design (orchestrator prose)": argument hint lists `--cruise | --no-cruise` (FR-022); step 0 parses flags via `factory mode`, exit 5 names the conflict and creates nothing, otherwise its printed JSON is written unchanged as the new pending state's `mode` at creation (FR-005's creation path) and step 3's `mode` record keeps `cruise`; resume passes mode flags; ambiguous intake under cruise records `decisions-add grill intake 'delivery' --cruise-override`; preflight discloses the adapter's no-prompt launch once per start or resume without waiting (FR-020) and accepts setup offers with fixed ids `setup-speckit`, `setup-commands` at stage `grill` and `setup-impeccable` at stage `review` (FR-013), a failing setup command halts; grill and brainstorm self-answered with `--auto`, visual companion skipped (FR-006); analyze exhaustion auto-proceeds with the `analyze-exhaustion` gate-override (FR-011); halts, hard stops (including a missing or stale test seam reported by code-build or fixer, ENG-4) and `--stop-at` unchanged (FR-012, FR-014); approver shows two veto-list groups, empty group stated, unresolved analyze report shown, never auto-answered (FR-015..FR-018); `NOTIFY` only on real waits, batch notice a log line (FR-019). Exempt: `core/skills/factory/SKILL.md` - documentation only. Done: each FR above cited by a prose step; no harness-specific option named in core.

- [ ] T009 [P] [US1] Edit `core/skills/factory/references/protocol.md` relay step 2 and "Questions": under cruise fill every unanswered question with a usable recommendation, `requires_user` and `pending_clarify` origin via `answer --cruise-override`, the rest via `--auto`; no usable recommendation is shown and waited on (FR-010); cruise turned on by resume fills the open round, preserving answers; without cruise today's protections hold (FR-009); step 2's "(`mode.fast` true, except initial grilling)" gains "; under cruise initial grilling is self-answered too" (FR-006); "Notify once per auto-accepted batch" becomes a log line under cruise (FR-019); the closing initial-grilling paragraph's "the user confirms shared understanding" gains "or, under cruise, the orchestrator self-confirms" (FR-006). Exempt: `protocol.md` - documentation only. Done: step 2 states both modes, and those three statements carry their cruise wording.

- [ ] T010 [P] [US4] Edit `core/skills/factory/references/state.md`: `mode.cruise` (absent = off, requires `fast`), `cruise_override` on relay answers and decisions with its invariants, `pr` gate exclusion, CLI surface `mode [flags]`, `resume <run> [mode flags]`, `answer ... --cruise-override`, `decisions-add ... --cruise-override`. Exempt: `state.md` - documentation only. Done: schema and commands documented.

- [ ] T011 [P] [US1] Edit `core/skills/factory/references/engineering.md` ("Confirmed test scope") and `core/skills/factory/references/design-code-mapping.md`: a cruise-override answer counts as recorded acceptance of that exact scope or exception and is listed at the approver; scope changes still invalidate it. Exempt: both files - documentation only. Done: both sections state the rule.

- [ ] T012 [P] [US1] Edit `core/roles/spec-builder.md` and `core/roles/spec-conformance.md`: Confirmed line form `Confirmed: <date> - <Qid> accepted (cruise override) - seams: ...; failure paths: ...` is valid acceptance when the answer carries `cruise_override`. Exempt: both files - documentation only. Done: both roles accept and name the form.

- [ ] T013 [P] [US5] Add one `no_prompt_launch` bullet to each of `adapters/claude-code/harness.md`, `adapters/codex/harness.md`, `adapters/copilot/harness.md`, `adapters/opencode/harness.md`, `adapters/zcode/harness.md`, each verified against that harness's documentation (`WEB_FETCH`) when written; unverifiable is written as "none documented" (FR-021). Exempt: `adapters/*/harness.md` - documentation only. Done: all five files carry the bullet; candidates from plan.md used only where verified.

## Phase 7: Polish and verification

- [ ] T014 Harness-neutrality and build check: `git grep -n -e bypassPermissions -e dangerously-bypass -e allow-all-tools -- core/` is empty; `git diff --stat origin/main -- tools/render.py install.sh` is empty; `test -z "$(git ls-files -- dist/)"` passes (constitution workflow gate: `dist/` untracked); run the build command (render all five harnesses into a temp `FACTORY_HOME`, `bash -n install.sh`) (FR-023, SC-006). Exempt: verification only. Done: build exits 0; all three checks pass.

- [ ] T015 Final verification: `python3 -m unittest discover -s tools`. Exempt: verification only. Done: all tests pass, or any failure is shown to be pre-existing on `origin/main` and recorded here; zero new failures (SC-004).

## Dependencies

- T001 first (constitution I).
- T002 before T003-T007 (writers validate the new fields).
- T003 before T004 (`resume` uses `resolve_mode`). T005 before T006 (same files). T007 after T002 only.
- T008 after T003-T006 (prose calls the new commands). T009-T013 parallel with each other and with T008 (separate files), after T006.
- T014, T015 last.

## Parallel execution

- T002-T007 share `tools/tests/test_cruise.py` and the CLI modules: run sequentially.
- T009, T010, T011, T012, T013 together: one per file group.

## Implementation Strategy

MVP = T001-T007: the state schema, mode resolution, override recording and the structural `pr` guard, all tested; this alone makes an automatic approval impossible. Then prose T008-T013 that drives cruise runs. Then T014-T015.
