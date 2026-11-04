# Specification Analysis Report — 019-analyze-remediation-targets (pass 2)

This is the recheck after full-chain repair cycle 1 (`factory/remediation-1.md`, decision LOOP1). The previous report is `factory/analyze-1-full.md`, and the baseline `factory/analyze-1.md` is unchanged. Artifacts: `spec.md` (2991 words), `plan.md` (1988 words) and `tasks.md` (2375 words). All three are within budget (3000 / 2000 / 2500). The constitution is version 2.0.0. Code facts were checked against the worktree: `factory_cli/commands.py` (`cmd_checkpoint`, `cmd_analyze_record`), `checks.py` (`gate_violation`, `_decisions`), `core/skills/factory/SKILL.md` step 5, `core/roles/spec-builder.md`, `tools/tests/test_gates.py` and `factory/relay-plan-1.json`.

## Previous findings (analyze-1-full.md)

| ID | Status | Evidence |
|----|--------|----------|
| H1 | Resolved | T005's Red step asserts no USAGE text. T008 states "USAGE is updated in Implement and not asserted". The tasks header's "No task tests a path outside it" now holds. |
| M1 | Resolved | Escalation now happens at most once per run, keyed on a `-full.md` entry in `analyze.reports`. This is stated in spec FR-013, plan "Orchestrator (SKILL.md step 5)", T001 and T009. |
| M2 | Resolved | FR-024 (3), plan item 3 and T009 now key on "no stored and no derivable baseline". A derivable baseline falls through to (4). |
| M3 | Resolved, with a new defect (see I1) | FR-019, plan "Remediate role" and T011 now apply the draft's `DESIGN.md` changes and declare both files in the envelope. |
| L1 | Resolved | The safety argument now covers escalation records (plan "Remediate gate", spec Assumptions, T001). |
| L2 | Resolved | T013 reads "Not behaviour-changing: runs the test and build commands only". |

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| I1 | Inconsistency (generic role vs. this repo's governance) | MEDIUM | spec.md FR-018 ("any implied `DESIGN.md` changes"), FR-019 ("listing `.specify/memory/constitution.md` and `DESIGN.md` in its envelope `files`"); plan.md "Remediate role"; tasks.md T011; `commands.py:871-874` (`cmd_checkpoint`: "declared files do not exist in the worktree") | The M3 fix takes a clause from this repository's own constitution Governance section ("committed together with any `DESIGN.md` change they imply") and writes it into `core/roles/spec-builder.md`. That role runs in every consuming repository, and many of those have no `DESIGN.md`. FR-019 says to list `DESIGN.md` in the envelope `files` unconditionally. `cmd_checkpoint` exits 1 when any declared file is missing from the worktree. In such a repository, an approved amendment therefore cannot be checkpointed, and the run stalls on `checkpoint remediate`. | Generalise this in FR-018, FR-019, plan "Remediate role" and T011. The draft records the changes the amendment implies for other files under the repository's governance, for example `DESIGN.md` here. The approved remediate applies those changes. It lists the constitution plus each file it actually changed in the envelope `files`. It never declares a file that does not exist. |
| C1 | Coverage gap (success criterion vs. tests) | MEDIUM | spec.md SC-005 ("byte-identical after every declined, unanswered or hash-mismatched amendment in tests"), FR-023 ("every amendment approval path"), US4 "Independent Test" (decline, edited draft, approved apply, recheck); tasks.md T008, T001 (validation entry); plan.md "Test seams" (`amendment-check`), "Validation" | The only amendment seam is `bin/factory amendment-check`, which covers a missing draft and a hash mismatch. The declined and aborted paths, and the approved apply-then-recheck path, are role prose (T011). No task tests them and no validation entry covers them. The new `DESIGN.md` "Analyze acceptance targets validation" entry (T001) checks the baseline, the cycle cap and the exhaustion question, but not the amendment flow. So SC-005 and FR-023 claim test coverage the plan cannot produce. SC-005's "unanswered" also contradicts US4 scenario 2, which dropped that branch in the baseline fix L5. | Reword SC-005 and FR-023 to cover only what tests can check: a missing or hash-mismatched draft leaves the constitution byte-identical. Add the amendment flow (draft written, constitution unchanged on decline, approved draft applied and then rechecked) to T001's validation entry. This adds no seam or failure path, so the Q1 confirmation stays current. `spec.md` has 9 words of headroom, so trim while rewording. |
| L1 | Underspecification (legacy fresh baseline) | LOW | plan.md "Orchestrator" item 3; tasks.md T009; spec.md FR-012; `commands.py` `cmd_analyze_record` (reports deduplicated) | Nothing names the report file for "re-run analysis as a fresh baseline". The legacy runs that reach this branch never had `analyze.pass` incremented, so the re-analysis writes `factory/analyze-<pass>.md`. That can overwrite a report already in `analyze.reports`, and because `analyze-record` deduplicates the list, the overwritten evidence disappears without a trace. | Name the fresh-baseline report distinctly in plan item 3 and T009, for example `factory/analyze-<n>-baseline.md`. This is prose only. |

## Coverage Summary

| Requirement | Has Task? | Task IDs | Notes |
|---|---|---|---|
| FR-001 | Yes | T005 | |
| FR-002 | Yes | T005 | |
| FR-003 | Yes | T005, T007 | Escalation via a later record and no `checkpoint remediate` |
| FR-004 | Yes | T004 | |
| FR-005 | Yes | T004 | |
| FR-006 | Yes | T004 | |
| FR-007 | Yes | T004, T009 | Gate check is defensive (clarify Q4) |
| FR-008 | Yes | T004 | |
| FR-009 | Yes | T004 | |
| FR-010 | Yes | T004, T005 | |
| FR-011 | Yes | T004, T009 | |
| FR-012 | Yes | T005, T009 | L1 |
| FR-013 | Yes | T001, T005, T009, T011 | The at-most-once rule is prose only |
| FR-014 | Yes | T006, T007, T009 | |
| FR-015 | Yes | T011 | Existing rule kept |
| FR-016 | Yes | T006, T009 | |
| FR-017 | Yes | T004, T007 | |
| FR-018 | Yes | T008, T011 | I1 |
| FR-019 | Yes | T008, T011 | I1 |
| FR-020 | Prose only | T011 | C1 |
| FR-021 | Yes | T007, T009 | |
| FR-022 | Yes | T001, T002, T009-T012 | |
| FR-023 | Partial | T003-T008 | C1 (amendment approval paths) |
| FR-024 | Yes | T001, T009 | |
| SC-001 | Yes | T004 | |
| SC-002 | Yes | T004, T007 | |
| SC-003 | Yes | T006 | |
| SC-004 | Yes | T005, T007 | |
| SC-005 | Partial | T008 | C1 |
| SC-006 | Yes | T013 | |

## Test-seam check (engineering.md)

- T003-T008 each carry a mapped declared seam and ordered Red / Implement / Pass steps with an observable Done. Every failure path they require appears in plan.md "Test seams". No test asserts USAGE text.
- T001, T002 and T009-T012 are plan-exempt (documentation only) and are excluded. T013 is not behaviour-changing.
- Confirmation: `Confirmed: 2026-11-04 - Q1 accepted` lists the same seven seams and failure paths as the current declarations. The snapshot is `factory/relay-plan-1.json`, with a non-auto plan Q1 decision, and clarify Q1 = A kept that scope. Remediation 1 changed no seam or failure path, so the confirmation is current.
- ENG-10: every new file (ADR 0014), abstraction (`analyze.baseline`, `checks.analyze_baseline`, `amendment-check`, `--fresh-baseline`) and dependency (none) has a stated reason. There is no ENG-10 finding.
- Word budgets: `spec.md` 2991/3000, `plan.md` 1988/2000 and `tasks.md` 2375/2500 are all within budget. There is no budget finding.

## Constitution Alignment Issues

There are no CRITICAL violations. Principles I-V pass: T001 lands first, the core prose uses neutral verbs, `dist/` stays untracked, state lives in `state.json`, and every new field and command has a reason. The Governance coupling with `DESIGN.md` is correct for this repository; I1 concerns only how the generic role carries it to consuming repositories.

## Unmapped Tasks

None.

## Metrics

- Total requirements: 24 FR + 6 SC = 30
- Total tasks: 13
- Coverage (requirements with at least one task): 30/30 = 100%. FR-020 is prose only, and FR-023 and SC-005 are partial (C1).
- Ambiguity count: 0
- Duplication count: 0
- Critical issues: 0
- Severity: CRITICAL 0, HIGH 0, MEDIUM 2, LOW 1 (total 3)

## Next Actions

- No finding blocks implementation, and there is no HIGH or CRITICAL.
- I1, C1 and L1 are targeted in-place edits: spec.md FR-018, FR-019, FR-023 and SC-005; plan.md "Remediate role" and "Orchestrator" item 3; tasks.md T001, T009 and T011. None of them changes a declared seam or failure path.
