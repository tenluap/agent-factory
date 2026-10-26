# Specification Analysis Report — pass 1

Feature: `007-stabilise-factory` | Artifacts: `spec.md`, `plan.md`, `tasks.md` (+ `contracts/cli.md`, `data-model.md`, `research.md`) | Constitution: `.specify/memory/constitution.md` v1.0.0

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| I1 | Inconsistency | HIGH | spec.md FR-006, Key Entities "Verify record"/"Transition record"; data-model.md "Transition record", gate table; contracts/cli.md "Write commands"; tasks.md T016, T017 | The `pr` gate and the gate-override record have no writer path. FR-003's closed vocabulary contains `approved` and `gate-override` history events and FR-006 requires "a recorded approval decision" before publishing a PR, but no CLI write command writes either: `checkpoint` appends `complete` only, `verify` writes `verify-pass`/`verify-fail`, `decisions-add` accepts only `--kind answer\|gate-override` (so an approval is not a writable decision kind), and `set-status` records status only. R5 additionally requires the overriding transition to get a `gate-override` history entry, which nothing writes. The `pr` gate is therefore unsatisfiable as specified, and no task adds the missing writer (T016 tests the refusal side only). | Name the writer in `contracts/cli.md` (e.g. `decisions-add --kind approved` or `checkpoint --event approved\|gate-override`) and mirror it in `data-model.md`; extend T017 (or add a task) so the approval and override records are written and tested on the accepting side, not only refused. |
| G1 | Coverage | MEDIUM | spec.md FR-008, SC-004, US2 scenario 3; contracts/cli.md `show`; tasks.md T004, T005, T007 | SC-004 ("every auto-accepted answer of every stage appears in the approver's veto list before publication") is only inferably covered. `show`'s `decisions` field is the intended veto list and T007 moves relay answers into `decisions`, but no task names the approver veto list and no test asserts the completeness property (every `auto: true` answer of every stage is listed before the `pr` gate). | Name the veto-list output and its completeness assertion in T004 (or T016's approval test) so SC-004 has an explicit check. |
| G2 | Coverage | MEDIUM | spec.md FR-011 | FR-011 lists fixture coverage over "state copies in later worktrees"; no task names that case. T002 covers accepted versions and legacy relay shapes, T027 covers missing worktrees and ambiguous names, T038 covers pending runs. | Add the case to T002's fixture list (a state file copied into a later worktree) or drop it from FR-011 if it is not a real scenario. |
| I2 | Inconsistency | MEDIUM | spec.md:215 (Quality and Verification Constraints) vs spec.md FR-022, plan.md Summary/Compatibility, data-model.md | The compatibility line says "state versions 1–3 readable" while the schema bumps to version 4 and readers must accept 1–4 (FR-022, plan, data-model, T002). The stale count contradicts the requirement it summarises. | Change the line to "state versions 1–4 readable" (or "1 through the current version"). |
| I3 | Inconsistency | MEDIUM | spec.md FR-003 vs spec.md Key Entities "Verify record"; research.md R3; data-model.md "Verify record" | Key Entities calls the verify record "a `verify` history entry", but FR-003's closed vocabulary has no bare `verify` event — only `verify-pass` and `verify-fail`. R3 and `data-model.md` settle the reading as the pair, but the spec keeps both wordings, so a second reading survives in the source of requirements. | Reword the Key Entities bullet to "a `verify-pass`/`verify-fail` history entry" (and FR-006's "(Key Entities)" pointer) so one term names one concept. |
| S1 | Simplicity (ENG-10) | MEDIUM (non-blocking) | plan.md "New files, abstractions, dependencies"; tasks.md T036; data-model.md "Conformance fixture and golden-run result" | New file `conformance/golden-run-results.md` (T036) has no stated reason in the plan's reason table, which lists only `conformance/fixture-repo/` and `conformance/golden-run/<harness>.md`. | Add one row to the plan table (`conformance/golden-run-results.md` - file - records FR-013's per-adapter golden-run results). |

## Coverage Summary

| Requirement | Has task? | Task IDs | Notes |
|---|---|---|---|
| FR-001 | yes | T002/T003, T006/T007 | single writer, atomic stamped writes |
| FR-002 | yes | T012 | halt-with-message path, documentation-only (orchestrator prose) |
| FR-003 | yes | T002/T003, T005, T033 | closed vocabularies incl. `resumed` |
| FR-004 | yes | T002/T003 | non-decreasing timestamps, exactly-once entries |
| FR-005 | yes | T014/T015 | lock beside state file or pending file |
| FR-006 | partial | T016/T017 | refusal side tested; approval/override writer missing (I1) |
| FR-007 | yes | T018/T019 | envelope/report/verdict shapes |
| FR-008 | partial | T007 (T005) | decisions migration covered; veto-list completeness not named (G1) |
| FR-009 | yes | T008/T009 | interval unions |
| FR-010 | yes | T042/T043 | reported vs estimates |
| FR-011 | partial | T002, T027, T038 | "state copies in later worktrees" untested (G2) |
| FR-012 | yes | T027/T028, T030 | rebind + documented caveat |
| FR-013 | yes | T032/T033, T036 | fixture repo, checklists, kill-and-resume |
| FR-014 | yes | T034/T035 | static read-only conformance, codex disclosure |
| FR-015 | yes | T022–T024 | model policy + alignment test |
| FR-016 | yes | T029 | preflight guidance (documentation-only) |
| FR-017 | yes | T025/T026 | declared-file checkpoints |
| FR-018 | yes | T020 | CI workflow |
| FR-019 | yes | T038/T039 | prune preview-first |
| FR-020 | yes | T040/T041 | installer usage errors |
| FR-021 | yes | T044 | Pen rules in one reference |
| FR-022 | yes | T002/T003 | versions 1–4, upgrade-on-write (see I2) |
| FR-023 | yes | milestone ordering, build gate on every code task | one PR, render-and-fail-on-drift |
| FR-024 | yes | T001, T010, T011, T046 | DESIGN.md-first and deliberate corrections |
| SC-001 | yes | T006 | every mutating command exercised |
| SC-002 | yes | T004 | 005/006 replay with defect manifest |
| SC-003 | yes | T008 | unions within wall clock |
| SC-004 | partial | T005/T007 | see G1 |
| SC-005 | yes | T014, T016, T018 | one test per refusal |
| SC-006 | yes | T032 | kill-and-resume per stage |
| SC-007 | yes | T020 | CI full suite + drift gate |
| SC-008 | yes | T022, T025 | declared files, no personal models |

## Task/seam contract (factory override)

- Every non-exempt implementation task (T003, T005, T007, T009, T015, T017, T019, T023, T026, T028, T033, T035, T039, T041, T043) names a seam that plan.md "Test seams" lists and is immediately preceded by a failing-test task naming that seam. **No finding.**
- All 22 exempt tasks carry `Exempt: <part> - <reason>` matching a plan exemption. **No finding.**
- Plan "Test seams" lists 8 seams and the `Confirmed: 2026-10-25 - Q1 accepted` line names exactly those 8. **No finding.**

## Constitution Alignment Issues

None. Design First is carried by FR-024 and the `DESIGN.md` tasks (T001, T010, T013, T021, T031, T037, T046); new core code is harness-neutral (Principle II); every code task ends in the render + porcelain drift gate the constitution itself names (Principle III); new records live in `state.json`/`lock.json` (Principle IV); the plan states a reason per new file, abstraction and dependency except the one named in S1 (Principle V).

## Unmapped Tasks

None. Every task maps to at least one FR/SC or to a plan-declared exemption.

## Metrics

- Total requirements: 24 FR + 8 SC (32 keys) | Total tasks: 46 (15 test tasks, 15 implementation tasks, 16 plan-exempt tasks)
- Coverage %: 30/32 keys with explicit task coverage (93.75%); 2 partial (FR-006 approval writer, SC-004 veto completeness)
- Ambiguity count: 0 | Duplication count: 0 | Constitution violations: 0
- Critical: 0 | High: 1 | Medium: 4 | Low: 0 (S1 is MEDIUM non-blocking per ENG-10 policy)
- Word budgets (`wc -w`): spec.md 3000 / 3000 (exactly at budget, not over), plan.md 1640 / 2000, tasks.md 2497 / 2500. No artifact over budget — no finding.

## Next Actions

- Resolve I1 before `/speckit-implement`: as written, the `pr` gate can never be satisfied and T016 can only ever see refusals. It needs one decision (which command records an approval) that either the remediation can fix from `data-model.md`/`research.md` intent, or a clarify answer.
- Fix I2 and I3 in `spec.md` wording (one-line edits, no behaviour change).
- Give SC-004 and FR-011's "state copies in later worktrees" an explicit test home (G1, G2) or narrow the requirement text.
- Add the missing reason row for `conformance/golden-run-results.md` (S1).
