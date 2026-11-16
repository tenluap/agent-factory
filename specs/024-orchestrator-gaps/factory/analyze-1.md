# Specification Analysis Report — 024-orchestrator-gaps, pass 1

Artifacts: `spec.md` (2671 words), `plan.md` (1568), `tasks.md` (1899), `contracts/cli.md`, `research.md`, `quickstart.md`, constitution 2.0.0. Code facts checked against the worktree: `commands.py` (`cmd_checkpoint`, `cmd_answer`, `overrun_issue`, `successor`), `budget.py`, `state.STAGES`, `SKILL.md` step 7/8, `references/design-code-mapping.md` §5, `references/state.md`.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| F1 | Inconsistency | HIGH (blocking) | plan.md:42, plan.md:119 (S2(c)); tasks.md:55-57 (T004); contracts/cli.md (`answer`); spec.md FR-009 | The plan and T004 make the qid/stage pattern refusal unconditional (T004 red step: `answer '../x' A` and `--stage 'a/b'` exit 1 with no `requires_user` question). `contracts/cli.md` limits it to "with a record due", and FR-009 requires answers without `requires_user` to behave exactly as today. T004 as written breaks FR-009. | Pick one rule. Recommended: the contract rule (refuse only when a record is due), so FR-009 holds; reword S2(c) and the T004 red step to use a `requires_user: true` question. Rewording a declared failure path changes the confirmed scope, so remediation must raise a fresh `requires_user` scope confirmation. |
| F2 | Inconsistency | HIGH (blocking) | plan.md:107, plan.md:112 (decision 7); tasks.md:105 (T010); research.md:13; `core/skills/factory/references/design-code-mapping.md:102` (§5); `references/state.md:154` | Plan decision 7 and T010 require active design runs to run `checkpoint fix` while `review.pending_design_fix` is still set, then clear it. `design-code-mapping.md` §5 says "After a completed attempt clear the pending marker before verification/re-review". An orchestrator following §5 clears the reservation first; `checkpoint fix` then sees no reservation and increments a second time (FR-003 defeated, the cap fires after one design fix). No task edits §5 or `state.md:154`; FR-019 names only state.md and SKILL.md. | Extend T010 (or add a documentation task) to amend `design-code-mapping.md` §5 and `state.md` "Schema" reservation text to the new order (checkpoint `fix`, then clear). Add `design-code-mapping.md` to FR-019 and the plan's Source Code tree. |
| F3 | Underspecification | MEDIUM | tasks.md:105 (T010); plan.md:112; quickstart.md:7; `commands.successor` | `successor("fix")` is `approver`, so a default `checkpoint fix` moves the run to `approver` mid-loop. Quickstart uses `checkpoint fix --next review` and `checkpoint review --next fix`, but neither plan decision 7 nor T010 tells SKILL.md step 7 which `--next` to pass (to `review` for the next round; `review` to `approver` when the verdict is clean or the cap is reached). | Add the `--next` targets to plan decision 7 and T010's Done condition. |
| F4 | Coverage gap | MEDIUM | spec.md:90 (Edge Cases, approver fix); FR-002; plan.md:107; tasks.md:42-47, 105 | Edge case: an approver-requested fix "is checkpointed as a `fix` stage too" and increments `fix_rounds`. FR-002/decision 2 increment only when the stored stage is `fix`; at the approver the stored stage is `approver`, so the increment needs `checkpoint approver --next fix` first. No task tests this path or documents it in SKILL.md step 8. | Either specify the step-8 sequence (`checkpoint approver --next fix`, fixer, `checkpoint fix --next review`) in T010 with a T003 test, or drop the edge case's counting claim. |
| F5 | Coverage gap | LOW | contracts/cli.md (`budget`: "Both flags given: exit 2"); tasks.md:87 (T007), 94 (T008) | The contract refuses `--round` together with `--full` (exit 2); no red step tests it. | Add the combined-flags case to the T007 red step (and T008 for `ledger-add`). |
| F6 | Coverage gap | LOW | contracts/cli.md (`answer`: result adds `"record": "<path>"`); tasks.md:63 (T005) | The contract's `record` result field is not asserted in T005. | Assert `record` in the T005 explicit-answer test. |
| F7 | Underspecification | LOW | plan.md:93-100; constitution V | New CLI flags (`--question`, `--round`, `--full`) and result fields (`review`, `full`, `record`, `unchanged`) are introduced; the plan says "New config key and flags have stated reasons below" but the list states reasons only for the config key, `REVIEWER_ROLES` and the renderer. Reasons are implied by FR-004/FR-005/FR-013 but not stated as lines. | Add one reason line per flag/result field, citing its FR. |
| F8 | Coverage gap | LOW | spec.md SC-002; tasks.md T003, T010 | SC-002 (cap stops automatic fixing after two rounds) is orchestrator behaviour; T003 proves only the counter values. Acceptable as documentation coverage, but no task names SC-002. | Cite SC-002 in T003's Done (counter reaches 2) and T010's Done (step 7 cap reads checkpoint `review.fix_rounds`). |

No CRITICAL findings: every constitution principle is respected (I: T001 first; II: neutral-verb checks in T009/T010; III: T011 checks `git ls-files -- dist/`; IV: state on disk; V: existing writers extended).

No ENG-10 finding: the plan states a reason for each new file and abstraction and records "Dependencies: none".

No word-budget finding: spec.md 2671/3000, plan.md 1568/2000, tasks.md 1899/2500.

## Confirmed test scope check

| Task | Seam | Failure paths claimed | Declared in plan | Ordered red/implement/pass | Status |
|------|------|-----------------------|------------------|-----------------------------|--------|
| T002 | S1 | S1(b) | yes | yes | OK |
| T003 | S1 | S1(a), S1(c), S1(d) | yes | yes | OK (see F2, F4) |
| T004 | S2 | S2(b), S2(c) | yes | yes | S2(c) conflicts with FR-009 (F1) |
| T005 | S2 | S2(a), S2(d) | yes | yes | OK |
| T006 | S4 | S4(a), S4(b) | yes | yes | OK |
| T007 | S3 | S3(a), S3(b) | yes | yes | OK |
| T008 | S4 | S4(a), S4(b) re-asserted | yes | yes | OK |
| T001, T009, T010 | — | — | plan `Exempt:` lines | exempt | excluded |
| T011 | — | — | verification only, no file change | n/a | excluded |

All declared failure paths (S1a-d, S2a-d, S3a-b, S4a-b) are claimed by at least one task. Confirmation: `plan.md:130` `Confirmed: 2026-11-04 - Q1 accepted (cruise override)` lists the complete current seam-to-failure-path scope; `state.json` decisions hold plan Q1 with `cruise_override: true`. Current and complete. Resolving F1 by rewording S2(c) invalidates it and needs a fresh confirmation.

## Coverage summary

| Requirement | Has task? | Task IDs | Notes |
|-------------|-----------|----------|-------|
| FR-001 | yes | T002 | |
| FR-002 | yes | T003 | approver path F4 |
| FR-003 | yes | T003 | doc conflict F2 |
| FR-004 | yes | T002, T003 | |
| FR-005 | yes | T004 | |
| FR-006 | yes | T005 | |
| FR-007 | yes | T005 | |
| FR-008 | yes | T005 | |
| FR-009 | yes | T005 | violated by T004 red step (F1) |
| FR-010 | yes | T010 | |
| FR-011 | yes | T006 | |
| FR-012 | yes | T006, T008 | |
| FR-013 | yes | T007 | |
| FR-014 | yes | T007 | |
| FR-015 | yes | T007 | |
| FR-016 | yes | T008 | |
| FR-017 | yes | T007 | |
| FR-018 | yes | T010 | |
| FR-019 | yes | T001, T009, T010 | misses design-code-mapping.md (F2) |
| FR-020 | yes | T009, T010, T011 | |
| FR-021 | yes | T002-T008, T011 | |
| SC-001 | yes | T003 | |
| SC-002 | partial | T003, T010 | F8 |
| SC-003 | yes | T005 | |
| SC-004 | yes | T006 | |
| SC-005 | yes | T008 | |
| SC-006 | yes | T011 | |

**Unmapped tasks:** none.

## Metrics

- Total requirements: 21 FR + 6 SC = 27
- Total tasks: 11
- Coverage: 27/27 with at least one task (100%; SC-002 partial)
- Ambiguity count: 0
- Duplication count: 0
- Critical issues: 0
- Severity counts: critical 0, high 2, medium 2, low 4

## Next actions

- Resolve F1 and F2 before implementation (both HIGH, blocking). F1 needs a fresh test-scope confirmation if S2(c) is reworded.
- F3, F4 MEDIUM: targeted edits to plan decision 7 and T010 (plus a T003 test for F4, or narrow the edge case).
- F5-F8 LOW: targeted edits to T003, T005, T007, T008 and the plan's reason list.
