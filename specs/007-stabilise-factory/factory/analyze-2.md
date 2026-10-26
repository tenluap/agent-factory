# Specification Analysis Report — pass 2

Feature: `007-stabilise-factory` | Artifacts: `spec.md`, `plan.md`, `tasks.md` (+ `contracts/cli.md`, `data-model.md`, `research.md`, `quickstart.md`) | Constitution: `.specify/memory/constitution.md` v1.0.0 | Loop pass over `factory/remediation-1.md`

## Pass 1 remediation check

| Pass-1 finding | Held? | Evidence |
|---|---|---|
| I1 (HIGH, `pr` gate / gate-override writer) | yes | `decisions-add --kind answer\|approved\|gate-override` in contracts/cli.md "Write commands"; data-model decision `kind` vocabulary; `checkpoint` writes `complete` or `approved`/`gate-override` carrying `decision: <qid>` (contracts, data-model transition record + rule 6); FR-006 names the approval record and the gate-decision history event; T016 asserts the accepting side, T017 names the writers; quickstart §4 shows the flow. |
| G1 (MEDIUM, SC-004 veto completeness) | yes | T004 names `show`'s approver veto list and the completeness assertion (every `auto: true` answer of every stage before `pr`), SC-004 cited. |
| G2 (MEDIUM, FR-011 later-worktree copies) | yes | T002 fixture list names "state copies in later worktrees". |
| I2 (MEDIUM, stale version range) | yes | spec.md Quality and Verification Constraints reads "state versions 1–4 readable". |
| I3 (MEDIUM, verify-record naming) | yes | Key Entities, FR-006's pointer and the clarification line all read `verify-pass`/`verify-fail`; research R3 matches. |
| S1 (MEDIUM non-blocking, ENG-10) | yes | plan.md reason table gains `conformance/golden-run-results.md` - file - records FR-013's per-adapter golden-run results; T036's `Exempt:` line and the plan exemption name it. |

Note: remediation-1.md claims T016's approval-side test asserts the veto-list completeness property at the gate; T016 as written does not. The property is nevertheless explicitly tested in T004, so G1's requirement ("in T004 **or** T016's approval test") is met — log wording only, no artifact defect.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| I4 | Inconsistency | MEDIUM | spec.md FR-003 (history vocabulary), Key Entities "Transition record"; data-model.md "Transition record", "State transitions"; contracts/cli.md "Write commands"; tasks.md T006, T007 | Two history events of FR-003's closed vocabulary have no writer. `checkpoint` writes `complete`/`approved`/`gate-override`, `verify` writes `verify-pass`/`verify-fail`, T033 adds `resumed` — but nothing writes `aborted` or `pr-open`, and no task exercises them. The end-of-run commands only touch `status`/`ended_at` (`set-status`: "record a status change"), while the data model lists `approver → aborted` and the run reaching `pr-open` among the transitions a transition record should prove. As written, two vocabulary values are unproducible, and research R5's parenthetical ("both non-`complete` events of FR-003's vocabulary have a writer") overstates the coverage. No gate becomes unsatisfiable (FR-019's stale rule reads `status`, not history), so this is not the pass-1 I1 class of failure. | Name the writer in `contracts/cli.md` (natural home: `set-status`'s `aborted`/`pr-open` forms appending their history entry with `ended_at`) and mirror in `data-model.md` and research R2/R5, with the test named in T006's `set-status` coverage; or narrow FR-003's list to the events that have writers. |
| G3 | Coverage | MEDIUM | spec.md FR-006 ("in the approver's veto list"); data-model.md "Decision record"; quickstart.md §4; tasks.md T004, T016 | A gate-override decision entry's membership in the approver's veto list is untested. FR-006 requires it and data-model defines the veto list as "every `auto: true` entry plus every `gate-override` entry", but T004's completeness assertion covers only `auto: true` answers (SC-004) and T016 covers only the gate satisfaction and history-entry references. | Extend T004's veto-list assertion (or T016's accepting side) to also assert every `gate-override` entry appears in the veto list. |
| W1 | Inconsistency | LOW | spec.md Clarifications (gate-override line), FR-006, FR-008 (decision-record field lists); Key Entities "Transition record" | The spec's summary field lists omit the two fields remediation-1 added to the machine contract: decision records are listed as "(stage, question ID, answer, auto=false, time)" without `kind` (the discriminator that separates `approved` from `gate-override` and that FR-006's gate names), and Key Entities' transition record lists "event, time, commit, harness" without the optional `decision` reference FR-006's last sentence requires. A second, incomplete reading survives in the requirements source (pass-1 I3's class). | Add `kind` to the decision-record field lists (or point them at `data-model.md`) and `decision` to the Transition record bullet — one-line edits, no behaviour change. |
| W2 | Underspecification | LOW | data-model.md validation rule 6 | Rule 6 says a history entry's `decision` "names an existing decision question ID", but question IDs are unique only within a stage (`protocol.md`; this run alone has a `grill-with-docs` Q1 and a `plan` Q1), and decision entries carry both `stage` and `question`. Matching by question ID alone can resolve to more than one decision, so the reference is ambiguous across stages. | Scope the rule to the same stage: "names a decision entry's question ID in the entry's own stage" (and say so in the `decision` field description). |

## Coverage Summary

| Requirement | Has task? | Task IDs | Notes |
|---|---|---|---|
| FR-001 | yes | T002/T003, T006/T007 | single writer, atomic stamped writes |
| FR-002 | yes | T012 | halt-with-message path, documentation-only (orchestrator prose) |
| FR-003 | partial | T002/T003, T005, T033 | closed vocabularies incl. `resumed`; `aborted`/`pr-open` events have no writer (I4) |
| FR-004 | yes | T002/T003 | non-decreasing timestamps, exactly-once entries |
| FR-005 | yes | T014/T015 | lock beside state file or pending file |
| FR-006 | partial | T016/T017 | writer + refusing and accepting sides now covered; gate-override veto-list membership untested (G3) |
| FR-007 | yes | T018/T019 | envelope/report/verdict shapes |
| FR-008 | yes | T004, T007 | decisions migration + veto-list completeness (pass-1 G1 fixed) |
| FR-009 | yes | T008/T009 | interval unions |
| FR-010 | yes | T042/T043 | reported vs estimates |
| FR-011 | yes | T002, T027, T038 | later-worktree state copies named (pass-1 G2 fixed) |
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
| FR-022 | yes | T002/T003 | versions 1–4, upgrade-on-write (I2 fixed) |
| FR-023 | yes | milestone ordering, build gate on every code task | one PR, render-and-fail-on-drift |
| FR-024 | yes | T001, T010, T011, T046 | DESIGN.md-first and deliberate corrections |
| SC-001 | yes | T006 | every mutating command exercised |
| SC-002 | yes | T004 | 005/006 replay with defect manifest |
| SC-003 | yes | T008 | unions within wall clock |
| SC-004 | yes | T004 | completeness assertion named (pass-1 G1 fixed) |
| SC-005 | yes | T014, T016, T018 | one test per refusal |
| SC-006 | yes | T032 | kill-and-resume per stage |
| SC-007 | yes | T020 | CI full suite + drift gate |
| SC-008 | yes | T022, T025 | declared files, no personal models |

## Task/seam contract (factory override)

- Every non-exempt implementation task (T003, T005, T007, T009, T015, T017, T019, T023, T026, T028, T033, T035, T039, T041, T043) names a seam that plan.md "Test seams" lists and is immediately preceded by a failing-test task naming that seam (T002→T003, T004→T005, T006→T007, T008→T009, T014→T015, T016→T017, T018→T019, T022→T023, T025→T026, T027→T028, T032→T033, T034→T035, T038→T039, T040→T041, T042→T043). **No finding.**
- All 16 exempt tasks carry `Exempt: <part> - <reason>` matching a plan exemption (T036's line now includes `conformance/golden-run-results.md`, matching the plan's exemption and reason table). **No finding.**
- Plan "Test seams" lists 8 seams and `Confirmed: 2026-10-25 - Q1 accepted - seams: ...` names exactly those 8; remediation added `decisions-add` to the `bin/factory` seam's command list without adding, removing or renaming a seam, so the confirmation still stands. **No finding.**

## ENG-10 simplicity check (factory override)

plan.md "New files, abstractions, dependencies" states a reason for every new file, abstraction and dependency, including the remediation-added `conformance/golden-run-results.md` row. No unreasoned introduction. **No finding.**

## Word budgets (factory override)

`wc -w`: spec.md 2997 / 3000, plan.md 1660 / 2000, tasks.md 2496 / 2500. No artifact over budget. **No finding.**

## Constitution Alignment Issues

None. Design First is carried by FR-024 and the `DESIGN.md` tasks (T001, T010, T013, T021, T031, T037, T046); new core code is harness-neutral (Principle II); every code task ends in the render + porcelain drift gate (Principle III); new records live in `state.json`/`lock.json` (Principle IV); the plan states a reason per new file, abstraction and dependency (Principle V). I4 is a spec/contract completeness gap, not a constitution conflict.

## Unmapped Tasks

None. Every task maps to at least one FR/SC or to a plan-declared exemption.

## Metrics

- Total requirements: 24 FR + 8 SC (32 keys) | Total tasks: 46 (15 test tasks, 15 implementation tasks, 16 plan-exempt tasks)
- Coverage %: 32/32 keys with task coverage (100%); 2 partial at clause level (FR-003 vocabulary writers, FR-006 veto-list membership)
- Ambiguity count: 1 (W2) | Duplication count: 0 | Constitution violations: 0
- Critical: 0 | High: 0 | Medium: 2 | Low: 2 (W1, W2 are wording/precision fixes; I4 and G3 are MEDIUM blocking-for-remediation like pass 1's G/I findings)
- Word budgets (`wc -w`): spec.md 2997 / 3000, plan.md 1660 / 2000, tasks.md 2496 / 2500 — no finding

## Next Actions

- Fix I4 before `/speckit-implement`: decide which command records the run-ending history events (or narrow FR-003's vocabulary) and name its test; as written, T003's closed-vocabulary implementation contains two values no command can ever produce.
- Give the gate-override veto-list membership (G3) one assertion in T004 or T016.
- One-line precision edits W1 (spec field lists gain `kind` and `decision`) and W2 (rule 6 scoped to the entry's stage).
- No finding needs a user decision: I4's two routes both follow existing intent (state.md ties `ended_at` to `pr-open`/`aborted`; `set-status` is the only writer of those statuses).
