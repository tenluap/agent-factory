# Specification Analysis Report — 019-analyze-remediation-targets (pass 1, escalated full-chain re-analysis)

This is the escalated re-analysis after lite-to-full escalation (decision ESC1). The baseline report `factory/analyze-1.md` is unchanged. Artifacts are the committed `spec.md` (2985 words), `plan.md` (1995 words) and `tasks.md` (2259 words). All three are within budget (3000 / 2000 / 2500), although `spec.md` has only 15 words of headroom. The constitution is version 2.0.0. Code facts below were checked against the worktree: `factory_cli/checks.py`, `commands.py`, `cli.py`, `state.py`, `tools/tests/`, `core/skills/factory/SKILL.md`, `core/roles/spec-builder.md`, `CONTEXT.md` and the `speckit-constitution` skill.

Every baseline finding (T1, I1, U1, I2, C1, I3, G1, U2, L1-L5) is resolved in the current artifacts by clarify Q1-Q5 and grill-with-docs Q1-Q5. None carries forward. The findings below are new.

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| H1 | Test scope (engineering.md "Confirmed test scope", ENG-4) | HIGH (blocking) | tasks.md T005 Red ("USAGE lists `--fresh-baseline`"); T008 Red ("USAGE lists the command"); tasks.md header ("No task tests a path outside it"); plan.md "Test seams" and "Confirmed:" line | Two tests assert USAGE text, and USAGE is reachable only in ways the plan does not declare. `cli.py:58` prints it on a usage refusal (exit 5), which is not a declared failure path for `bin/factory analyze-record` or `bin/factory amendment-check`. The other route is asserting the `factory_cli.cli.USAGE` constant, which is not a declared seam. This contradicts tasks.md's own statement that no task tests outside the confirmed scope. | Drop both USAGE assertions from the T005 and T008 Red and Done steps. Keep the USAGE edit in Implement. That changes no scope, and the Q1 confirmation stays current. Alternatively, declare a usage-refusal failure path for both seams; that invalidates Q1 and needs a fresh `requires_user` scope question. |
| M1 | Underspecification (loop bound) | MEDIUM | plan.md "Orchestrator (SKILL.md step 5)" ("lite with CRITICAL or HIGH escalates as today"); "Research" Skipped (no `mode.chain` writer); tasks.md T009, T001; spec.md FR-013, US3 "Why this priority", SC-003; state.json decision ESC1 | Escalation is keyed on `mode.chain` reading `lite`, and no CLI writer sets it to `full`. This run proves it: after ESC1, state still reads `lite`. A later recheck that again has CRITICAL or HIGH would escalate again. Each escalation consumes no cycle and never reaches the exhaustion question, so the 2-cycle cap and FR-016 can be bypassed indefinitely. | State that escalation happens at most once per run, detected from state (for example a recorded analyze escalation decision, or an `analyze-<n>-full.md` entry in `analyze.reports`). After that, CRITICAL or HIGH follows the repair-cycle rule. Carry this into plan step 5, T009 and T001. |
| M2 | Inconsistency (legacy path) | MEDIUM | spec.md FR-024 (3), US2 scenario 5, FR-010; plan.md "Orchestrator" item 3, "`analyze-record`" (`--fresh-baseline` refused when derivable); tasks.md T009 | The gate and the orchestrator test different conditions. The gate derives a baseline for a legacy run with exactly one report. The orchestrator's branch (3) fires on "no *stored* `analyze.baseline`". So a resumed legacy run (one report, nothing stored, targets unmet) is refused on targets but classified as "no baseline". The user is asked for a fresh baseline, and `analyze-record --fresh-baseline` is then refused because the baseline is derivable. That is a dead end that contradicts US2.5. FR-024's "analyze-record always stores a derivable baseline first" holds only after a new record. | Key branch (3) on "no stored and no derivable baseline" (`reports` length ≠ 1, or `result.report` names another report). A derivable baseline falls through to branch (4). Update FR-024, plan item 3 and T009. |
| M3 | Underspecification / constitution Governance | MEDIUM | spec.md FR-018, FR-019; plan.md "Remediate role"; tasks.md T011; constitution "Governance" ("committed together with any `DESIGN.md` change they imply"), Principle I; `commands.py` `commit_worktree` (stages spec_dir plus declared files only) | The draft records the `DESIGN.md` changes an amendment implies, but the apply step only runs `speckit-constitution`, which writes only `.specify/memory/constitution.md`. Nothing applies the implied `DESIGN.md` changes. Nothing tells remediate to declare `.specify/memory/constitution.md` and `DESIGN.md` in its envelope `files` either, so `checkpoint remediate` would leave them undeclared and uncommitted. The amendment could then land without its `DESIGN.md` change, or not land at all. | In FR-019, plan "Remediate role" and T011, state that the approved remediate also applies the draft's `DESIGN.md` changes, and that it lists both paths in its envelope `files` so one checkpoint commits them together. |
| L1 | Underspecification | LOW | plan.md "Remediate gate" (grill Q3 safety argument); spec.md Assumptions ("only a guided pass reaches it"); tasks.md T001, T006; state.json ESC1 (stage `analyze`, kind `answer`, `auto: false`) | The safety argument covers only the exhaustion question's answers. The orchestrator also records other non-auto analyze `answer` decisions, such as the escalation record ESC1. If such a record is newer than `result.at` when `loops >= 2`, the cap opens without a guided pass. It is safe today only because the re-analysis after escalation records a newer `result.at`. | In plan and `DESIGN.md` (T001), add that other analyze answers (escalation records) are always followed by a newer recorded result. Alternatively, restrict the qualifying decision to the exhaustion question's id. |
| L2 | Inconsistency | LOW | tasks.md T013 ("Exempt: verification only"); plan.md "Test seams" Exempt list; engineering.md ENG-5 | T013 claims an exemption the plan does not declare, and ENG-5 exemptions cover only documentation or configuration. T013 changes no code, so it needs no seam. | Reword it to "Not behaviour-changing: runs the test and build commands only" and drop the "Exempt" claim. |

## Coverage Summary

| Requirement | Has Task? | Task IDs | Notes |
|---|---|---|---|
| FR-001 | Yes | T005 | |
| FR-002 | Yes | T005 | |
| FR-003 | Yes | T005, T007 | Escalation through later record and no `checkpoint remediate` (grill Q4) |
| FR-004 | Yes | T004 | |
| FR-005 | Yes | T004 | |
| FR-006 | Yes | T004 | |
| FR-007 | Yes | T004, T009 | Gate check defensive (clarify Q4) |
| FR-008 | Yes | T004 | |
| FR-009 | Yes | T004 | Existing override test kept; veto list already in SKILL.md approver |
| FR-010 | Yes | T004, T005 | M2 |
| FR-011 | Yes | T004, T009 | |
| FR-012 | Yes | T005, T009 | M2 |
| FR-013 | Yes | T001, T005, T009, T011 | M1 |
| FR-014 | Yes | T006, T007, T009 | |
| FR-015 | Yes | T011 | Existing rule kept |
| FR-016 | Yes | T006, T009 | M1 |
| FR-017 | Yes | T004, T007 | |
| FR-018 | Yes | T008, T011 | M3 |
| FR-019 | Yes | T008, T011 | M3 |
| FR-020 | Yes | T011 | |
| FR-021 | Yes | T007, T009 | |
| FR-022 | Yes | T001, T002, T009-T012 | |
| FR-023 | Yes | T003-T008 | |
| FR-024 | Yes | T001, T009 | M2 |
| SC-001 | Yes | T004 | |
| SC-002 | Yes | T004, T007 | |
| SC-003 | Yes | T006 | M1 |
| SC-004 | Yes | T005, T007 | |
| SC-005 | Yes | T008 | |
| SC-006 | Yes | T013 | |

## Test-seam check (engineering.md)

- T003-T008 each carry a mapped declared seam and ordered Red / Implement / Pass steps with an observable Done. The exceptions are the two USAGE assertions in T005 and T008 (H1).
- T001, T002 and T009-T012 are plan-exempt (documentation only) and are excluded. T013 changes no code (L2).
- Confirmation: `Confirmed: 2026-11-04 - Q1 accepted` matches the current seam declarations and failure paths in plan.md "Test seams". The snapshot is `factory/relay-plan-1.json`, with a non-auto decision recorded (plan Q1). Clarify Q1 = A kept that scope. The plan now exempts two additional documentation files (`docs/factory-overview.md`, `docs/product-brief.md`); exemptions are not seams, so the confirmation stays current.
- ENG-10: every new file (ADR 0014), abstraction (`analyze.baseline`, `checks.analyze_baseline`, `amendment-check`, `--fresh-baseline`) and dependency (none) has a stated reason. There is no ENG-10 finding.
- Word budgets: every artifact is within its budget. There is no budget finding.

## Constitution Alignment Issues

There are no CRITICAL violations. Principle I is satisfied: T001 lands first. Principles II-V pass as the plan states. The Development Workflow validation entry is present (T001). Governance has the gap listed as M3.

## Unmapped Tasks

None.

## Metrics

- Total requirements: 24 FR + 6 SC = 30
- Total tasks: 13
- Coverage (requirements with at least one task): 30/30 = 100%
- Ambiguity count: 0
- Duplication count: 0
- Critical issues: 0
- Severity: CRITICAL 0, HIGH 1, MEDIUM 3, LOW 2 (total 6)

## Next Actions

- H1 blocks implementation. The scope-preserving fix is to drop the USAGE assertions from T005 and T008, which needs no user decision.
- M1-M3 and L1-L2 are targeted edits in place to spec.md FR-013, FR-018, FR-019 and FR-024, to plan.md "Orchestrator", "Remediate gate" and "Remediate role", and to tasks.md T001, T009, T011 and T013. None changes a declared seam or failure path.
