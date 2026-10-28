# Specification Analysis Report — 011-drop-factory-folder, pass 1

Artifacts: `spec.md` (1544 words), `plan.md` (947), `tasks.md` (1299), `contracts/cli.md`, `data-model.md`, `research.md`, `quickstart.md`. Constitution 1.0.0.

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| C1 | Constitution | CRITICAL | tasks.md T013; plan.md Constitution Check III ("build gate checks drift") | Constitution "Development Workflow" says the dist gate MUST be `test -z "$(git status --porcelain -- dist/)"` and that a bare `git diff --exit-code -- dist/` "is not the gate". T013 names `git diff --exit-code -- dist/`. `quickstart.md` step 2 already uses the correct gate, so T013 contradicts both. | Change T013 to run the build then `test -z "$(git status --porcelain -- dist/)"` (as in quickstart.md step 2); state the same gate in plan.md Constitution Check III. |
| H1 | Inconsistency | HIGH | spec.md FR-009, SC-001; SKILL.md §9 step 5 and "Done when"; tasks.md T009 | SKILL.md §9 step 5 `NOTIFY`s the run totals (state.md "Totals") and the stage is "Done when the PR URL is in state". FR-009/T009 put `factory drop` before that, and the drop deletes `specs/<branch>/factory/state.json` from disk, so the totals read (and any later state read in the PR stage) no longer finds the run. No artifact addresses where step 5 and the done check read state after the drop. | Decide the order explicitly: either run `factory drop` + final push after the totals `NOTIFY` (step 5), or have the orchestrator read totals before the drop. Update FR-009, T009 and the §9 "Done when" line (e.g. PR URL recorded in the archived state and shown to the user). |
| H2 | Inconsistency | HIGH | spec.md Edge Cases ("second push fails" vs "Resume after the drop"); tasks.md T009 | Edge case 3 says a failed final push is recovered by "resume of the `pr` stage repeats only the push". Edge case 4 (and state.md "Discovery": runs with `pr-open` are skipped; `commands.py:291,410`) says the run is not discoverable after the drop — it already is not once `pr-open` is set. So no resume path exists; the recovery claim is unsupported and T009 tells SKILL.md to document it. | Replace the resume claim with a reachable recovery: e.g. the orchestrator retries the final push once in the same turn and, on failure, `NOTIFY`s the user to run `git push` from the worktree (the drop commit is local and complete). Align spec edge case 3 and T009. |
| M1 | Inconsistency | MEDIUM | spec.md US2 Independent Test, FR-005, SC-002, Key Entities "Run archive" ("byte-identical copy"); plan.md Design step 4; tasks.md T005(a) | Spec requires every file of the folder, identical; plan/tasks exclude `lock.json` from the copy and the verification (the drop's own lock lives in the folder). Spec never mentions the exclusion, so SC-002 as written fails by design. | Add to spec FR-003/FR-005 and "Run archive": the run's `lock.json` is excluded from the copy and the comparison. |
| L1 | Coverage | LOW | spec.md SC-004; tasks.md | SC-004 "under 5 seconds" has no task asserting it. Proportionate: a run folder is tens of small files. | Either add a loose timing assertion to the T003 success test or note in plan "Quality constraints" that SC-004 is verified by the manual quickstart run. |

No ENG-10 findings: plan "New files, abstractions, dependencies" gives a reason for every new item (dependencies: none). No word-budget findings: all three artifacts are under budget.

## Seam check (factory override)

| Implementation task | Seam | Test task immediately before | Result |
|---------------------|------|------------------------------|--------|
| T004 | `factory drop` | T003 | ok |
| T006 | `factory drop` | T005 | ok |
| T008 | `factory drop` | T007 | ok |

Plan-exempt tasks excluded: T001, T002, T009, T010, T011, T012, T013. Every seam named in tasks is listed in plan "Test seams"; plan carries a matching `Confirmed:` line.

## Coverage summary

| Requirement | Tasks | Note |
|-------------|-------|------|
| FR-001 | T007, T008 | lock refusal |
| FR-002 | T004, T007 | |
| FR-003 | T004, T005 | see M1 |
| FR-004 | T007, T008 | |
| FR-005 | T005, T006 | see M1 |
| FR-006 | T003, T004 | |
| FR-007 | T003, T004 | |
| FR-008 | T003 | |
| FR-009 | T009 | see H1, H2 |
| FR-010 | T013 (existing suite) | |
| FR-011 | T004 (no flag) | |
| FR-012 | T007 | |
| FR-013 | T001 | |
| FR-014 | T010, T011 | |
| FR-015 | T012 | |
| FR-016 | T003, T005, T007 | |
| SC-001..003 | T003, T005, T007 | |
| SC-004 | — | L1 |
| SC-005 | T013 | see C1 |

Unmapped tasks: none.

## Constitution alignment

- I Design First: T001 precedes core tasks. Pass.
- II Harness-Neutral Core: T009 uses `SHELL:`. Pass.
- III Generated Dist: T012 renders and commits. Gate wording: C1.
- IV Stateless Agents: pass. V Simplicity: reuse stated, reasons given. Pass.

## Metrics

- Requirements: 16 FR + 5 SC; with ≥1 task: 20/21 (95%).
- Tasks: 13. Ambiguity count: 0. Duplication count: 0.
- Critical: 1, High: 2, Medium: 1, Low: 1.
