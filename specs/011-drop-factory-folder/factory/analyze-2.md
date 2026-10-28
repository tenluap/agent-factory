# Specification Analysis Report — 011-drop-factory-folder, pass 2

Artifacts: `spec.md` (2125 words), `plan.md` (1281), `tasks.md` (1797), `contracts/cli.md`, `data-model.md`, `research.md`, `quickstart.md`. Constitution 1.0.0. Repository context: `CONTEXT.md`, `docs/adr/0008-run-artifacts-leave-the-branch-at-pr-open.md`, `DESIGN.md`, `core/skills/factory/SKILL.md` §9, `factory_cli` sources.

No remediation log exists for pass 1; the artifacts were revised by the clarify, grill-with-docs, plan and tasks stages that ran after it. Pass-1 findings were re-checked against the current artifacts:

| Pass-1 ID | Status | Evidence |
|-----------|--------|----------|
| C1 | Resolved | tasks.md T013 and plan.md Constitution Check III now name `test -z "$(git status --porcelain -- dist/)"`. |
| H1 | Resolved | spec Clarifications Q1, FR-007, FR-009: `factory drop` JSON carries `totals_sentence` and `pr_url`; step 9 `NOTIFY`s from it; "Done when" restated. T009 matches. |
| H2 | Resolved | spec Clarifications Q3, Edge Cases, FR-009: one in-turn retry, then `NOTIFY` a manual `git push`; no resume claim. T009, plan "Push failure" and ADR 0008 match. |
| M1 | Resolved | FR-003, FR-005, SC-002, "Run archive" exclude `lock.json`. |
| L1 | Resolved | plan Technical Context: SC-004 verified by quickstart step 3 (timed). |

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| D1 | Duplication / terminology | MEDIUM | tasks.md T002; plan.md Source Code (`CONTEXT.md` comment); CONTEXT.md lines 117-131 | T002 says to *add* "Run folder", "Run archive", "Drop commit" and "Permanent design evidence" to `CONTEXT.md` with the spec's Key Entities definitions. grill-with-docs already wrote "Run folder", "Run archive", "Drop" (not "Drop commit") and "Permanent design evidence" there, with different wording (e.g. CONTEXT "copy" vs spec "byte-identical copy"). Executing T002 as written duplicates glossary entries and introduces a second name for the drop ("Drop" vs "Drop commit"). | Reword T002 to: confirm the existing `CONTEXT.md` entries match spec Key Entities, add only what is missing (decide whether "Drop commit" is a separate term or covered by "Drop"), and align wording without duplicating headings. Update the plan's `CONTEXT.md` comment to match. |
| U1 | Underspecification | LOW | spec.md FR-017; plan.md Design step 7; DESIGN.md "Pen design references" ("`docs/design-code-map.json` (or its existing equivalent)") | DESIGN.md allows the canonical map to live at an existing equivalent path; FR-017 and the plan rewrite only `docs/design-code-map.json`. On a repository whose map lives elsewhere, the drop would move the evidence and leave the map pointing at removed paths, which the spec says must never happen (Edge Cases, Pen run). | State in FR-017 that the map path is `docs/design-code-map.json` (the drop rewrites no other file), or resolve the map path from the run's `design.map` state field when present. Either choice in one sentence; tests unchanged for the default path. |
| I1 | Inconsistency | LOW | spec.md Assumptions ("Chain is lite with fast mode on") | The run escalated to the full chain (orchestrator input: "full chain (escalated)"); the assumption is stale. It does not affect behaviour. | Change to "Chain is full (escalated from lite) with fast mode on", or drop the line since run mode is not a feature assumption. |

No ENG-10 findings: plan "New files, abstractions, dependencies" gives a reason for every new item (dependencies: none). No word-budget findings: `spec.md` 2125/3000, `plan.md` 1281/2000, `tasks.md` 1797/2500.

Verified against code (no finding): `set-status pr-open` commits the state (`commit_worktree`), so `git rm -r` in the drop meets no local modifications; `improvements claim` reads `deduped(find_runs(repo))` and only refuses a discoverable non-ended run, so a dropped run is claimable as the spec's edge case says; every helper the plan reuses (`git`, `find_runs`, `deduped`, `factory_home`, `lock.acquire/release`, `LockHeld`, `improvements.backlog_name`, `totals.compute/sentence`, `die`/`CLIError`) exists.

## Seam check (factory override)

| Implementation task | Seam | Test task immediately before | Result |
|---------------------|------|------------------------------|--------|
| T004 | `factory drop` | T003 | ok |
| T006 | `factory drop` | T005 | ok |
| T008 | `factory drop` | T007 | ok |
| T015 | `factory drop` | T014 | ok |

Plan-exempt tasks excluded: T001, T002, T009, T010, T011, T012, T016 (documentation, agent instructions, generated `dist/`); T013 is verification only. Every seam named in tasks is listed in plan "Test seams"; the plan's `Confirmed:` line lists exactly `factory drop`.

## Coverage summary

| Requirement | Has task? | Tasks | Note |
|-------------|-----------|-------|------|
| FR-001 | yes | T007, T008 | lock refusal, own timestamp (`dropped_at`) |
| FR-002 | yes | T004, T007 | |
| FR-003 | yes | T004, T005 | |
| FR-004 | yes | T007, T008 | |
| FR-005 | yes | T005, T006 | |
| FR-006 | yes | T003, T004, T014 | |
| FR-007 | yes | T003, T004 | |
| FR-008 | yes | T003 | |
| FR-009 | yes | T009 | |
| FR-010 | yes | T013 (existing suite) | |
| FR-011 | yes | T004 (no flag) | |
| FR-012 | yes | T007 | |
| FR-013 | yes | T001 | |
| FR-014 | yes | T010, T011 | |
| FR-015 | yes | T012 | |
| FR-016 | yes | T003, T005, T007, T014 | |
| FR-017 | yes | T014, T015, T016, T001 | see U1 |
| SC-001 | yes | T003, T014 | |
| SC-002 | yes | T005 | |
| SC-003 | yes | T005, T007, T014 | |
| SC-004 | yes | T003 (one commit); quickstart step 3 (timing) | |
| SC-005 | yes | T012, T013 | |

Unmapped tasks: none (T002 maps to the domain-model terms; see D1).

## Constitution alignment

- I Design First: T001 (DESIGN.md PR section, Factory home, Pen mapping, CLI surface) precedes core tasks. Pass.
- II Harness-Neutral Core: T009 uses `SHELL:`; no harness names. Pass.
- III Generated Dist: T012 renders five harnesses; T013 uses the porcelain gate. Pass.
- IV Stateless Agents: totals come from drop output on disk, not agent memory. Pass.
- V Simplicity and Reuse: reuses existing helpers; new items have reasons. Pass.

No constitution conflicts.

## Metrics

- Requirements: 17 FR + 5 SC = 22; with ≥1 task: 22/22 (100%).
- Tasks: 16. Ambiguity count: 0. Duplication count: 1 (D1).
- Critical: 0, High: 0, Medium: 1, Low: 2.

## Next actions

No CRITICAL or HIGH findings; implementation is not blocked. Remediate D1 (reword T002), U1 (one sentence in FR-017) and I1 (spec assumption) in place.
