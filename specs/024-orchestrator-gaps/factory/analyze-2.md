# Specification Analysis Report — 024-orchestrator-gaps, pass 2

Artifacts: `spec.md` (2695 words), `plan.md` (1730), `tasks.md` (2190), `contracts/cli.md`, `research.md`, `data-model.md`, `quickstart.md`, constitution 2.0.0. Inputs: `analyze-1.md`, `remediation-1.md`, `state.json` (decisions; commits 425f018 "answer Q1", 629138f "remediate complete"). Code facts checked against the worktree: `core/skills/factory/SKILL.md:147-149`, `references/state.md:154,238`, `references/design-code-mapping.md:102`.

## Pass-1 findings: resolution check

| ID | Pass-1 severity | Status | Evidence |
|----|-----------------|--------|----------|
| F1 | HIGH | Resolved in artifacts; confirmation line still missing (see G1) | S2(c) now reads "with a record due" in plan.md:42, :116, :126; tasks.md:55-57 (T004 red step uses `requires_user: true` for both refusals, and the unsafe qid without `requires_user` is answered as today); spec.md FR-009; contracts/cli.md; research.md R5. All five agree. |
| F2 | HIGH | Resolved | Single counter writer: reservations store `attempt` = counter + 1 without incrementing; the orchestrator clears, then `checkpoint fix --next review` counts once (plan.md:114, :119; spec.md:89, FR-003; research.md R2). FR-019 and the plan tree name design-code-mapping.md §5 (plan.md:81, :135). T009 amends state.md:154, state.md:238 and §5 (`increment it, save` exists today at design-code-mapping.md:102, so the Done grep is meaningful). T010 replaces SKILL.md:147 "reserve/persist that increment". Legacy guard (S1(c)) unchanged. |
| F3 | MEDIUM | Resolved | plan.md:119 and T010 state `checkpoint fix --next review`, `checkpoint review --next fix`, `checkpoint review --next approver`; T010 Done greps `checkpoint fix --next review`. Matches quickstart.md step 3. |
| F4 | MEDIUM | Resolved | Approver-fix counting edge case removed from spec.md; plan.md:114 states no special rule. No remaining artifact claims an approver-specific increment. |
| F5 | LOW | Resolved | T007 and T008 red steps include `--round 1 --full` exit 2. |
| F6 | LOW | Resolved | T005 red step asserts the result's `record` field. |
| F7 | LOW | Resolved | plan.md:101-106 add one reason line per new flag and result field, each citing an FR. |
| F8 | LOW | Resolved | T003 red/Done and T010 Done cite SC-002. |

## New findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| G1 | Confirmed test scope | HIGH (blocking) | plan.md:138; tasks.md:9; `state.json` decisions (remediate Q1) | The fresh acceptance exists: `state.json` decisions hold remediate Q1 = `A` with `cruise_override: true` at 2026-11-04T22:13:55Z, which counts as recorded acceptance (engineering.md "Confirmed test scope"). The artifacts do not record it. plan.md:138 still reads "Confirmation pending ... the `Confirmed:` line is written only after it", and plan.md has no `Confirmed:` line. tasks.md:9 says implementation waits for that line. The relay stored Q1 as id-only (commit 425f018), so no immutable snapshot of the accepted scope exists either. Engineering.md requires the accepted scope to be stored with the `Confirmed:` line or a referenced snapshot. As written, the artifacts block implementation by their own text. | Replace plan.md:138 with `Confirmed: 2026-11-04 - remediate Q1 accepted (cruise override) - seams: S1, S2, S3, S4; failure paths: S1(a-d), S2(a-d) with S2(c) "unsafe qid/stage with a record due exits 1, nothing written; no record due answers as today", S3(a-b), S4(a-b)` (full seam-to-path wording as declared at plan.md:125-128). Drop the "confirmation pending" clause in tasks.md:9. The scope is unchanged since the acceptance, so no new question is needed. |
| G2 | Coverage gap | MEDIUM | state.md:238 ("Resume", non-design branch); tasks.md:101 (T009); FR-002; SC-002 | T009 restates only the design-reservation branch of the `verify`/`review`/`fix` resume step. The non-design branch ("Otherwise re-run step 6's verify, then step 7 from its first sub-step") skips `checkpoint fix`. A run interrupted after a completed ordinary fix round, before `checkpoint fix --next review`, resumes at stored stage `fix`, re-reviews, and never counts that round. The cap then allows a third automatic fix. | Extend T009: on resume at stored stage `fix` with no reservation, after verify run `checkpoint fix --next review` (one increment; the stage guard makes it safe), then re-review. Add the same sentence to T010's step-7 resume note if SKILL.md repeats it. |
| G3 | Inconsistency | LOW | data-model.md:11 | `pending_design_fix` is still described as "design flow (unchanged)". After remediation 1, the reservation stores `attempt` = counter + 1 and no longer increments (research.md R2). | Reword the row: the reservation stores `attempt` = counter + 1 without incrementing; `attempt == fix_rounds` (legacy reservation) suppresses the checkpoint increment. |

No CRITICAL findings: I (T001 first), II (neutral-verb checks in T009/T010), III (T011 checks `git ls-files -- dist/`), IV (state on disk), V (existing writers extended) all hold.

No ENG-10 finding: plan.md:94-107 states a reason for each new file, abstraction, flag and result field, and records "Dependencies: none".

No word-budget finding: spec.md 2695/3000, plan.md 1730/2000, tasks.md 2190/2500.

## Confirmed test scope check

| Task | Seam | Failure paths claimed | Declared in plan | Ordered red/implement/pass | Status |
|------|------|-----------------------|------------------|-----------------------------|--------|
| T002 | S1 | S1(b) | yes | yes | OK |
| T003 | S1 | S1(a), S1(c), S1(d) | yes | yes | OK |
| T004 | S2 | S2(b), S2(c) | yes (S2(c) wording matches plan.md:126) | yes | OK |
| T005 | S2 | S2(a), S2(d) | yes | yes | OK |
| T006 | S4 | S4(a), S4(b) | yes | yes | OK |
| T007 | S3 | S3(a), S3(b) | yes | yes | OK |
| T008 | S4 | S4(a), S4(b) re-asserted | yes | yes | OK |
| T001, T009, T010 | — | — | plan `Exempt:` lines (plan.md:132-135) | exempt | excluded |
| T011 | — | — | verification only, no file change | n/a | excluded |

Every declared failure path (S1a-d, S2a-d, S3a-b, S4a-b) is claimed by at least one task, and each task's claims match the plan declarations exactly. Acceptance: remediate Q1 (`A`, cruise override, 22:13:55Z) postdates the S2(c) change and no seam or path changed afterwards, so it is current. The plan does not yet record it (G1).

## Coverage summary

| Requirement | Has task? | Task IDs | Notes |
|-------------|-----------|----------|-------|
| FR-001 | yes | T002 | |
| FR-002 | yes | T003 | resume branch G2 |
| FR-003 | yes | T003, T009, T010 | |
| FR-004 | yes | T002, T003 | |
| FR-005 | yes | T004 | |
| FR-006 | yes | T005 | |
| FR-007 | yes | T005 | |
| FR-008 | yes | T005 | |
| FR-009 | yes | T004, T005 | |
| FR-010 | yes | T010 | |
| FR-011 | yes | T006 | |
| FR-012 | yes | T006, T008 | |
| FR-013 | yes | T007 | |
| FR-014 | yes | T007 | |
| FR-015 | yes | T007 | |
| FR-016 | yes | T008 | |
| FR-017 | yes | T007 | |
| FR-018 | yes | T010 | |
| FR-019 | yes | T001, T009, T010 | |
| FR-020 | yes | T009, T010, T011 | |
| FR-021 | yes | T002-T008, T011 | |
| SC-001 | yes | T003 | |
| SC-002 | yes | T003, T010 | |
| SC-003 | yes | T005 | |
| SC-004 | yes | T006 | |
| SC-005 | yes | T008 | |
| SC-006 | yes | T011 | |

**Unmapped tasks:** none.

## Metrics

- Total requirements: 21 FR + 6 SC = 27
- Total tasks: 11
- Coverage: 27/27 (100%)
- Ambiguity count: 0
- Duplication count: 0
- Critical issues: 0
- Severity counts: critical 0, high 1, medium 1, low 1

## Next actions

- G1 (HIGH, blocking): write the `Confirmed:` line from the existing remediate Q1 acceptance and drop the pending notes. This is a recording edit, not a new question.
- G2 (MEDIUM): extend T009 with the non-design `fix` resume step.
- G3 (LOW): reword data-model.md:11.
