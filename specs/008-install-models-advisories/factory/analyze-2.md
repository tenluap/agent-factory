# Specification Analysis Report — pass 2

Feature: `008-install-models-advisories` · Artifacts: `spec.md`, `plan.md`, `tasks.md` (+ `research.md`, `data-model.md`, `quickstart.md`, `contracts/cli-delta.md`, `factory/brief.md`) · Constitution: `.specify/memory/constitution.md` (v1.0.0)

IDs continue `analyze-1.md`'s numbering so each finding is traceable across passes.

## Pass-1 finding status

| Pass-1 ID | Status | Evidence |
|-----------|--------|----------|
| C1 (Constitution, CRITICAL) | **Resolved** | `quickstart.md` "Gates" now uses `test -z "$(git status --porcelain -- dist/)"` and states explicitly that `git diff --exit-code -- dist/` "cannot see untracked additions and is not the gate"; the run's `build` command in `factory/state.json` now ends `… && test -z "$(git status --porcelain -- dist/)"`. `plan.md` (Constitution Check III) and `tasks.md` (Build gate) were never weakened. |
| A1 (Ambiguity, MEDIUM) | **Partially resolved** | The FR group heading is now qualified ("resolves 007 FR-015", `spec.md` L120) and `spec.md` L90 reads "the 007 plan", but both Assumptions bullets still use bare "FR-015" for 007's requirement → re-reported as **A2**. |
| I1 (Inconsistency, LOW) | **Partially resolved** | `tasks.md` T038 now names `tools/tests/test_state.py` as the assertions' module and says why, but `plan.md`'s Project Structure still assigns that file solely to the relay-round rule and the `replay.py` seam still names no module there → re-reported as **I3**. |
| I2 (Inconsistency, LOW) | **Resolved** | T040 now cites FR-020 and FR-017 ("align the `runs` wording with the aborted-run skip (FR-017)"). |
| S1 (Style, LOW) | **Resolved** | Typo gone; `spec.md` L90 reads "the 007 plan". |

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| A2 | Ambiguity | MEDIUM | `spec.md` L193, L194 (Assumptions); against `spec.md` L145 (this spec's FR-015) and L120 | Both Assumptions bullets use bare "FR-015" for 007's install-model requirement ("the brief's decisions enumerate only FR-015…", "The settled FR-015 decision…"), while this spec's own FR-015 is the digest union-totals rule. Only the FR group heading is qualified. A reader tracing the assumption lands on the wrong requirement. (A1 residue.) | Qualify both as "007 FR-015", matching L120; keep bare "FR-015" for this spec's requirement only. |
| I3 | Inconsistency | LOW | `plan.md` L61 (Project Structure) vs `tasks.md` T038 | `plan.md`'s structure comment for `tools/tests/test_state.py` reads only "exactly-one-open-relay-round rule", although T038 places the `replay.py` import assertions there; the `tools/tests/replay.py` defect-detector seam names no test module in the plan. (I1 residue — T038's parenthetical documents the placement at task level, but plan.md's file map still disagrees.) | Extend the comment (e.g. "exactly-one-open-relay-round rule; `replay.py` import-vocabulary assertions") or move T038's assertions beside the render test module. |
| I4 | Inconsistency | LOW | `plan.md` L92 (Quality constraints — Error and resource limits) vs `spec.md` SC-001/SC-002 | The refusal-path list ends with "malformed `config.json` aborting the install" and cites (SC-002, SC-003), but SC-002 enumerates exactly five paths and omits the config-parse abort, which SC-001 owns. | Cite SC-001 for the config-parse item (keep SC-002/SC-003 for the five refusal paths), or drop that item from the list. |

No duplication findings. No task-to-requirement or requirement-to-task gaps. No ENG-10 findings: every row of plan.md's "New files, abstractions, dependencies" table states a reason, and the table correctly reports no new source file and no new dependency.

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 | yes | T003, T004, T007, T008, T009, T010, T011, T012 | per-user render, home policy, linking, uninstall |
| FR-002 | yes | T001, T002, T007, T008 | canonical purity + `git status --porcelain -- dist/` assertion |
| FR-003 | yes | T003, T004 | default-home resolver |
| FR-004 | yes | T005, T006, T007, T008 | write-free `--models` report |
| FR-005 | yes | T007, T008 | default-home case (`FACTORY_HOME` unset) |
| FR-006 | yes | T013 | Exempt (documentation) |
| FR-007 | yes | T014, T015 | exit 5 naming the value |
| FR-008 | yes | T024, T025 | `rebind` through `write_run` |
| FR-009 | yes | T016, T017 | ended pending run not writable |
| FR-010 | yes | T028, T029 | at most one open relay round, only as the last |
| FR-011 | yes | T026, T027 | commit failure report + retry idempotence |
| FR-012 | yes | T018, T019 | unevaluable PID counts as live |
| FR-013 | yes | T020, T021 | force before liveness |
| FR-014 | yes | T022, T023 | identity-checked release |
| FR-015 | yes | T032, T033 | union-only digest aggregates (this spec's FR-015; see A2) |
| FR-016 | yes | T030, T031 | open-run wall clock to now |
| FR-017 | yes | T034, T035 | aborted runs skipped |
| FR-018 | yes | T036, T037 | dead duplicate tests deleted |
| FR-019 | yes | T038, T039 | replay.py on shared vocabulary |
| FR-020 | yes | T040 | Exempt (documentation) |
| FR-021 | yes | T041 | Exempt (documentation) |
| FR-022 | yes | T042, T043 | malformed `config.json` aborts the install (clarified 2026-10-26; covered in SC-001, quickstart S1, research.md R-decision, data-model.md, contracts/cli-delta.md) |
| SC-001 | yes | T007–T012, T042, T043 | install-pipeline assertions incl. config-parse abort and home policy |
| SC-002 | yes | T014, T016, T018, T022, T026 (+ pairs) | one test per refusal path |
| SC-003 | yes | T018–T023 | lock behaviour end to end |
| SC-004 | yes | T030, T032 | digest tests keep human+agent ≤ wall clock |
| SC-005 | yes | T028, T029 | validation reports zero anomalies / names location |
| SC-006 | yes | T039 | full suite + build gate + quickstart S1–S5 |

## Factory gate checks (spec-stage overrides)

- **Seam/test-task structure**: 0 findings. 43 tasks = 20 failing-test / 20 implementation / 3 exempt documentation. Every implementation task is immediately preceded by its failing-test task and names a seam listed in plan.md's "Test seams" (`bin/factory` CLI command surface, `factory_cli.state` module API, `factory_cli.lock` lifecycle, `factory_cli.totals` interval unions, `tools/render.py` render output, `install.sh` install/uninstall flow, `tools/tests/replay.py` defect detectors); T013/T040/T041 carry their plan exemptions instead. `Confirmed: 2026-10-26 - Q1 accepted - seams: …` lists exactly those seven seams. The T042/T043 pair (FR-022) follows the same rule and runs inside US1 after T012 as its header states.
- **ENG-10 (new file / abstraction / dependency without stated reason)**: 0 findings; plan.md's reasons table is complete (6 rows, "New source files: none", "New dependencies: none").
- **Word budgets**: `spec.md` 2992/3000, `plan.md` 1664/2000, `tasks.md` 2426/2500 — all within budget, 0 findings. (Note: `spec.md` has 8 words of headroom; any remediation that adds prose to it must trim elsewhere.)

## Constitution Alignment Issues

None. Principles I–V and the Development Workflow are satisfied: behaviour and doc corrections are recorded with the code (I); all CLI fixes live under `core/`, harness specifics stay in `install.sh` (II); every `core/` task (T015, T017, T019, T021, T023, T025, T027, T029, T031, T033, T035) ends with the five-harness render and the porcelain gate, and the gate is the constitution's `test -z "$(git status --porcelain -- dist/)"` everywhere it appears (quickstart, plan, tasks, run command) (III); checkpoint retry idempotence lives in the state file's pending history entry (IV); the reasons table is complete (V). C1 from pass 1 is resolved in `quickstart.md` and the run's `build` command, never in the constitution.

## Unmapped Tasks

None.

## Metrics

- Total Requirements: 28 (22 FR + 6 SC)
- Total Tasks: 43 (20 failing-test, 20 implementation, 3 exempt documentation)
- Coverage: 100% (28/28 requirements with ≥1 task; 0 unmapped tasks)
- Ambiguity Count: 1 (A2)
- Duplication Count: 0
- Critical Issues Count: 0

## Next Actions

- No blocking findings: implementation may proceed.
- Fold **A2** (two one-word qualifications in `spec.md`'s Assumptions), **I3** (one comment line in `plan.md`'s structure) and **I4** (one SC citation in `plan.md`'s quality constraints) into the artifacts as one-line edits — all LOW/MEDIUM improvements, none a gate.
