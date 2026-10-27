# Specification Analysis Report — pass 1

Feature: `008-install-models-advisories` · Artifacts: `spec.md`, `plan.md`, `tasks.md` (+ `research.md`, `data-model.md`, `quickstart.md`, `contracts/cli-delta.md`, `factory/brief.md`) · Constitution: `.specify/memory/constitution.md` (v1.0.0)

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| C1 | Constitution | CRITICAL | `quickstart.md` "Gates" block (also the run's `build` command in `factory/state.json`) | The quickstart labels `git diff --exit-code -- dist/` the **build gate**. The constitution's Development Workflow states that form "cannot see untracked additions and is not the gate"; the mandated gate is `test -z "$(git status --porcelain -- dist/)"`. `plan.md` (Constitution Check III) and `tasks.md` (Build gate) use the correct porcelain check, so the artifact set carries two conflicting definitions of a NON-NEGOTIABLE gate, and T039 closes the run "with the build gate and quickstart.md S1–S5" — i.e. against the wrong one. The run's configured `build` command has the same weak form, so a new untracked file under `dist/` would pass it. | Replace the quickstart's gate command with `test -z "$(git status --porcelain -- dist/)"` (the S1 expectation already uses that form); the run's `build` command should be aligned by the orchestrator to the constitution's gate. Do not weaken plan/tasks wording. |
| A1 | Ambiguity | MEDIUM | `spec.md` FR-015 heading + Assumptions bullet 2; `factory/brief.md`; `quickstart.md` S4 | "FR-015" names two different requirements in one run: 007's FR-015 (the install-model pipeline blocker, delivered here as FR-001–FR-006) and this spec's own FR-015 (digest union totals). The Assumptions bullet "The settled FR-015 decision (per-user render …)" uses the unqualified id for 007's requirement, so a reader traces it to the wrong rule. | Qualify every reference to 007's id as "007 FR-015" (the FR-006 heading already does); keep bare "FR-015" for this spec's requirement only. |
| I1 | Inconsistency | LOW | `tasks.md` T038 vs `plan.md` "Project Structure" | T038 puts the `tools/tests/replay.py` import assertions in `tools/tests/test_state.py`, which plan.md assigns solely to the relay-round rule, while the `replay.py` defect-detector seam names no test module. | Name the test module for the replay seam in plan.md's structure (or move T038's assertions beside `test_render_models.py`/its own module) so file and seam agree. |
| I2 | Inconsistency | LOW | `tasks.md` T040 | T040 carries two changes: the `resume <run>` row (FR-020) and aligning the `runs` wording with the aborted-run skip (FR-017 behaviour), but cites only FR-020. | Cite FR-017 alongside FR-020 on T040's wording half. |
| S1 | Style | LOW | `spec.md` User Story 5, "Why this priority" | Typo: "the007 plan". | "the 007 plan". |

No duplication findings. No task-to-requirement or requirement-to-task gaps. No ENG-10 findings: every row of plan.md's "New files, abstractions, dependencies" table states a reason, and the table correctly reports no new source file (`tools/tests/test_render_models.py` and `tools/tests/__init__.py` already exist) and no new dependency.

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 | yes | T003, T004, T007, T008, T011, T012 | per-user render + linking; uninstall identity-checked |
| FR-002 | yes | T001, T002, T007, T008 | canonical purity + `git status --porcelain -- dist/` assertion |
| FR-003 | yes | T003, T004 | default-home resolver |
| FR-004 | yes | T005, T006, T007, T008 | write-free `--models` report |
| FR-005 | yes | T007, T008 | default-home case (`FACTORY_HOME` unset) |
| FR-006 | yes | T013 | Exempt (documentation) |
| FR-007 | yes | T014, T015 | exit 5 naming the value |
| FR-008 | yes | T024, T025 | `rebind` through `write_run` |
| FR-009 | yes | T016, T017 | ended pending run not writable |
| FR-010 | yes | T028, T029 | exactly one open relay round |
| FR-011 | yes | T026, T027 | commit failure report + retry idempotence |
| FR-012 | yes | T018, T019 | unevaluable PID counts as live |
| FR-013 | yes | T020, T021 | force before liveness |
| FR-014 | yes | T022, T023 | identity-checked release |
| FR-015 | yes | T032, T033 | union-only digest aggregates (this spec's FR-015, see A1) |
| FR-016 | yes | T030, T031 | open-run wall clock to now |
| FR-017 | yes | T034, T035 | aborted runs skipped |
| FR-018 | yes | T036, T037 | dead duplicate tests deleted |
| FR-019 | yes | T038, T039 | replay.py on shared vocabulary |
| FR-020 | yes | T040 | Exempt (documentation) |
| FR-021 | yes | T041 | Exempt (documentation) |
| SC-001 | yes | T007, T008 | install-pipeline assertions |
| SC-002 | yes | T014, T016, T018, T022, T026 (+ pairs) | one test per refusal path |
| SC-003 | yes | T018–T023 | lock behaviour end to end |
| SC-004 | yes | T030, T032 | digest tests keep human+agent ≤ wall clock |
| SC-005 | yes | T028, T029 | validation reports zero anomalies / names location |
| SC-006 | yes | T039 | full suite + build gate + quickstart S1–S5 |

## Factory gate checks (spec-stage overrides)

- **Seam/test-task structure**: 0 findings. Every implementation task names a seam listed in plan.md's "Test seams" (`bin/factory` CLI command surface, `factory_cli.state` module API, `factory_cli.lock` lifecycle, `factory_cli.totals` interval unions, `tools/render.py` render output, `install.sh` install/uninstall flow, `tools/tests/replay.py` defect detectors), each is immediately preceded by its failing-test task, and T013/T040/T041 carry their plan exemptions instead. `Confirmed: 2026-10-26 - Q1 accepted - seams: …` lists exactly the seven named seams.
- **ENG-10 (new file / abstraction / dependency without stated reason)**: 0 findings; plan.md's reasons table is complete.
- **Word budgets**: `spec.md` 2506/3000, `plan.md` 1419/2000, `tasks.md` 2148/2500 — all within budget, 0 findings.

## Constitution Alignment Issues

- **C1** (above): the quickstart's build-gate command contradicts the Development Workflow's mandated `test -z "$(git status --porcelain -- dist/)"` and endorses the form the constitution explicitly rejects. plan.md and tasks.md comply; the fix belongs in `quickstart.md` (and the run's `build` command), never in the constitution.
- Principles I–V otherwise satisfied: behaviour and doc corrections recorded (I); CLI changes stay under `core/`, harness specifics in `install.sh` (II); every `core/` task ends with the five-harness render and the porcelain gate (III); checkpoint retry idempotence lives in the state file's pending entry (IV); reasons table complete (V).

## Unmapped Tasks

None.

## Metrics

- Total Requirements: 27 (21 FR + 6 SC)
- Total Tasks: 41 (19 failing-test, 19 implementation, 3 exempt documentation)
- Coverage: 100% (27/27 requirements with ≥1 task; 0 unmapped tasks)
- Ambiguity Count: 1 (A1)
- Duplication Count: 0
- Critical Issues Count: 1 (C1)

## Next Actions

- Resolve **C1** before `/speckit-implement`: correct the `quickstart.md` gate command to the constitution's porcelain check (and align the run's `build` command); the artifacts' plan/tasks wording already matches the constitution and must not be "fixed" toward the weaker form.
- Fold **A1**'s id qualification and the two LOW wording fixes (**I1**, **I2**, **S1**) into `spec.md`/`tasks.md` as one-line edits.
- With C1 cleared, no other blocker: implementation may proceed (MEDIUM/LOW items are improvements, not gates).
