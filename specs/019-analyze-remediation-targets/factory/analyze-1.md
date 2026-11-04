# Specification Analysis Report — 019-analyze-remediation-targets (pass 1)

Artifacts: `spec.md` (2589 words), `plan.md` (1948 words), `tasks.md` (1847 words); constitution 2.0.0. All artifacts are within word budget (3000 / 2000 / 2500). Code facts cited below were checked against the worktree (`factory_cli/checks.py`, `commands.py`, `cli.py`, `state.py`, `DESIGN.md`, `docs/`).

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| T1 | Test scope (engineering.md "Confirmed test scope", ENG-4) | HIGH (blocking) | tasks.md T003 (Red, Done); plan.md "Test seams" (validate_state), "Confirmed:" line; plan.md "Data model" | T003 requires two things the confirmed declarations lack: (a) the failure path "unparsable `at`" (Red step), which plan "Data model" says `validate_state` rejects but the `validate_state` seam declaration and the Q1-accepted scope list only negative, missing and non-integer counts and empty `report`; (b) a `write_run` refusal assertion (Done), which tests through the state writer. That writer is not a declared seam. | Either remove both from T003, or add "unparsable `at`" (and, if wanted, the writer refusal as a declared seam or failure path) to the plan declarations. Adding a failure path invalidates the Q1 confirmation, so remediation must return a fresh `requires_user` scope question. |
| I1 | Inconsistency | MEDIUM | spec.md US2 scenario 6, FR-011, FR-008; plan.md "Implement gate" step 2; tasks.md T004 Red ("zero reports refuses (existing wording)") | Spec: when there is no baseline and zero reports, the refusal says no trustworthy baseline exists, and the orchestrator offers fresh baseline, override or abort. Plan and T004 keep the old early return, "analyze.reports is empty", for zero reports. The orchestrator's "untrustworthy baseline" branch may then not recognise the case. | Align the two. Either the zero-reports refusal also states "no trustworthy baseline", or the spec scopes US2.6/FR-011 to "one or more reports" and says what the orchestrator does with zero reports (re-run analyze). |
| U1 | Underspecification | MEDIUM | plan.md "Orchestrator (SKILL.md step 5)"; tasks.md T009; plan.md "Implement gate" (single `; `-joined reason) | The orchestrator branches on the refusal cause: targets with `loops < 2`, `loops >= 2`, untrustworthy baseline. The gate returns one free-text string, and the plan does not say how the orchestrator tells the causes apart (text matching, or reading `show`/state counts). No branch is defined for a refusal caused only by `pending_clarify` or an unanswered `requires_user` question while targets are met. | State the classification source, for example reading `analyze.baseline`/`result`/`loops` from `show` rather than parsing reason text. Add the protected-question-only branch: route to clarify or the relay wait, with no cycle charged. |
| I2 | Inconsistency | MEDIUM | plan.md "Research" Skipped ("escalated report reuses the pass number"); spec.md US2 scenario 4, Key Entities "Baseline" (report path); brief ("retain the first analyze report as baseline") | On lite-to-full escalation the re-analysis reuses pass 1. `analyze-1.md` is overwritten, so `analyze.baseline.report` names a file whose content is no longer the baseline report. The counts survive but the baseline evidence does not. | Either give the escalated re-analysis a distinct report number (for example bump `pass` on escalation without charging `loops`), or state in spec/plan that the baseline's report path may be superseded and that only the stored counts are authoritative. |
| C1 | Coverage gap | MEDIUM | spec.md FR-003 (escalation), FR-013, SC-004 ("Across resume and escalation tests"), US2 scenario 4, US3 scenario 3; tasks.md T007 | Tests cover baseline/`loops` preservation on resume only. No task tests escalation preserving the baseline or consuming no cycle. No CLI writer exists for `mode.chain` (SKILL.md step 5 "set `mode.chain` to `full`"), so SC-004's escalation half cannot be tested as written. | Map US2.4 explicitly to T005's "second record keeps baseline" case (the escalated re-analysis is just a later record). Reword SC-004/FR-013 so escalation-consumes-no-cycle is checked through T007 (`loops` unchanged without `checkpoint remediate`), or record the untestable part as prose-only. |
| I3 | Inconsistency (stale docs) | MEDIUM | `docs/factory-overview.md:63` ("Remediate once" diagram node); `docs/product-brief.md:230` ("MEDIUM/LOW-only analysis findings receive one remediation pass ... do not trigger another verification loop"); plan.md "Source Code"; tasks.md T001/T009-T011 | Two tracked docs still describe the rule this feature replaces (FR-014), and no task updates them. After delivery the repository will contradict itself. | Add both files to the T001 or T009 prose updates (documentation exemption), or record in the plan why they are left unchanged. |
| G1 | Constitution workflow / validation gap | MEDIUM | constitution "Development Workflow" ("A change to the flow is validated end to end per the 'Validation plan' in DESIGN.md"); DESIGN.md "Validation plan" (per-feature subsections); plan.md "Validation"; tasks.md T001, T012 | This changes the analyze flow, but the plan's Validation covers only unit tests and the build. Nothing adds or references an end-to-end check in DESIGN.md "Validation plan", as earlier flow features did (for example "Skill routing validation"). | Add a short "Analyze acceptance targets validation" item to the T001 DESIGN.md edit. It should say what an end-to-end run must show: baseline kept, cycle cap, exhaustion question not auto-answered. Reference it from plan "Validation". |
| U2 | Underspecification | MEDIUM | spec.md FR-007, US1 scenario 7; plan.md "Research" Skipped (no `pending_clarify` writer); `core/skills/factory/SKILL.md:110` ("stored in state"); ADR 0006 | The gate, now the single decision point, refuses on a non-empty `analyze.pending_clarify`. The plan confirms no CLI writer persists that field, and ADR 0006 forbids hand edits, so in real runs the FR-007 check can never fire. Enforcement then rests only on orchestrator routing. | Either persist `pending_clarify` through an existing writer (for example `checkpoint remediate --envelope`), or state in spec/plan that FR-007's `pending_clarify` clause is enforced by relay routing and the gate check is defensive only. |
| L1 | Underspecification | LOW | plan.md "Remediate gate"; tasks.md T006 | At `loops >= 2`, any non-auto analyze `answer` newer than `result.at` authorises remediate. That includes an "abort" or "fresh baseline" answer, not only the guided-pass choice. | Name the qualifying answer (the exhaustion question's guided-pass option or custom guidance), or note why any newer answer is acceptable. |
| L2 | Inconsistency | LOW | `core/skills/factory/SKILL.md:115` ("Done when analyze is clean, MEDIUM/LOW were remediated, or the user chose to proceed"); tasks.md T009 | T009 rewrites the step 5 rules but does not mention the step's done condition, which encodes the old rule. | Add "update the step 5 done condition (targets met or `gate-override`)" to T009. |
| L3 | Constitution alignment (Governance) | LOW | constitution "Governance" ("committed together with any `DESIGN.md` change they imply"); plan.md "Remediate role"; tasks.md T011 | The amendment draft contract (text, rationale, version bump) does not ask for the `DESIGN.md` changes the amendment implies. | Add "implied `DESIGN.md` changes, if any" to the draft contents in plan and T011. |
| L4 | Terminology drift | LOW | spec.md ("implementation checkpoint", "implementation transition gate", "recheck", "fresh analysis"); plan.md ("implement gate"); tasks.md | Several names are used for one concept, against constitution Writing Standards ("one term for one concept"). This matters because T001/T009-T011 carry the wording into agent prose. | Pick "implement gate" and "recheck" (or the spec's terms) and use them consistently in the prose tasks. |
| L5 | Ambiguity | LOW | spec.md US4 scenario 2 ("declined or has not answered, When the cycle continues"); FR-020 | An unanswered `requires_user` approval question holds the remediate relay, so the cycle cannot continue. The "has not answered" branch of the scenario is unreachable as written. | Reword to "declined, or the run is aborted/overridden without approval", or drop "has not answered". |

## Coverage Summary

| Requirement | Has Task? | Task IDs | Notes |
|---|---|---|---|
| FR-001 | Yes | T005 | |
| FR-002 | Yes | T005 | |
| FR-003 | Partial | T007 | Resume only; escalation untested (C1) |
| FR-004 | Yes | T004 | |
| FR-005 | Yes | T004 | |
| FR-006 | Yes | T004 | New HIGH on clean baseline |
| FR-007 | Yes | T004 | No state writer for `pending_clarify` (U2) |
| FR-008 | Yes | T004 | Zero-report wording conflict (I1) |
| FR-009 | Yes | T004 | Existing override test kept |
| FR-010 | Yes | T004, T005 | |
| FR-011 | Yes | T004 | I1 |
| FR-012 | Yes | T005, T009 | |
| FR-013 | Prose only | T009 | C1 |
| FR-014 | Yes | T006, T007, T009 | |
| FR-015 | Yes | T011 (existing rule kept) | |
| FR-016 | Yes | T006, T009 | |
| FR-017 | Yes | T004, T007 | |
| FR-018 | Yes | T008, T011 | |
| FR-019 | Yes | T008, T011 | |
| FR-020 | Yes | T011 | L5 |
| FR-021 | Yes | T007, T009 | |
| FR-022 | Yes | T001, T002, T009-T012 | Stale docs outside list (I3) |
| FR-023 | Yes | T003-T008 | |
| SC-001 | Yes | T004 | |
| SC-002 | Yes | T004, T007 | |
| SC-003 | Yes | T006 | |
| SC-004 | Partial | T007 | Escalation half (C1) |
| SC-005 | Yes | T008 | |
| SC-006 | Yes | T012 | |

## Test-seam check (engineering.md)

- T003-T008 each carry a mapped declared seam and ordered Red / Implement / Pass steps with an observable Done. T003 is the exception noted in T1.
- T001, T002, T009-T011 and T012 are plan-exempt (documentation or verification only) and are excluded from this check.
- Confirmation: `Confirmed: 2026-11-04 - Q1 accepted` matches the declared seams and failure paths verbatim (snapshot `factory/relay-plan-1.json`, decision recorded non-auto). It is current for everything except T3's extra path and seam (T1).
- ENG-10: the plan states a reason for every new file (ADR 0014), abstraction (`analyze.baseline`, `analyze_baseline`, `amendment-check`, `--fresh-baseline`) and dependency (none). There are no unexplained-new-code findings.

## Constitution Alignment Issues

There are no CRITICAL violations. Principle I (Design First) is satisfied: T001 lands first. Principle II is honoured: T009 requires harness-neutral verbs. Principles III, IV and V pass as the plan states. Workflow and governance gaps are listed as G1 and L3.

## Unmapped Tasks

None. T012 maps to SC-006.

## Metrics

- Total requirements: 23 FR + 6 SC = 29
- Total tasks: 12
- Coverage (requirements with at least one task): 29/29 = 100% (2 partial: FR-003, SC-004; FR-013 prose only)
- Ambiguity count: 3 (U1, U2, L5)
- Duplication count: 0
- Critical issues: 0
- Severity: CRITICAL 0, HIGH 1, MEDIUM 7, LOW 5 (total 13)

## Next Actions

- T1 blocks implementation. Remediation either trims T003 to the confirmed scope or extends the declarations and returns a fresh `requires_user` scope-confirmation question.
- Fix the MEDIUM and LOW findings in place in spec.md, plan.md and tasks.md. I1, U1, U2, I2 and C1 are targeted wording or test-mapping edits. I3 and G1 add items to the existing documentation tasks.
