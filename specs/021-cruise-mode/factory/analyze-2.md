# Specification Analysis Report (pass 2)

Feature: `021-cruise-mode`, the first full-chain analyze after the lite->full escalation (decision `ESCALATE`). Artifacts: `spec.md` (2989 words), `plan.md` (1927), `tasks.md` (2126), `CONTEXT.md` (cruise terms, L171-L192) and `docs/adr/0014-cruise-mode-overrides-protections-but-never-publishes.md`. Constitution `.specify/memory/constitution.md`. Extension hooks skipped (the factory owns the flow).

## Pass-1 findings

| Pass-1 ID | Status | Evidence |
|-----------|--------|----------|
| T1 (HIGH) | Resolved | tasks.md L23-L25: T002 asserts only the declared `validate_state` paths. The `analyze`-only rule moved to T006's `decisions-add` guard (clarify Q1). |
| T2 (HIGH) | Resolved | tasks.md L65: T007 asserts through `gate_violation` into `pr` only. The implement gate is left to T006. |
| U1 | Resolved | plan.md L43; tasks.md L18, L72: each setup id names its stage (`grill` or `review`). |
| C1 | Resolved | tasks.md L18: T001 updates the README "Usage" and "Flags" sections. |
| C2 | Resolved | tasks.md L86: T014 runs `test -z "$(git ls-files -- dist/)"`. |
| E1 | Resolved | plan.md L36; tasks.md L57: the guard stays inline, with no shared helper. |
| A1 | Resolved | tasks.md L33: T003 asserts `--no-fast --fast --cruise` exits 5. |
| L1 | Resolved | tasks.md L18: the validation-plan entry names the fixture run and the SC-001..SC-003 checks. |
| L2 | Resolved | plan.md L96: the fields, flag and bullet are listed with a reason. |

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| I1 | Inconsistency | MEDIUM | spec.md L150 (FR-005); plan.md L38; core/skills/factory/SKILL.md L45, L72; references/state.md L3, L170 | FR-005 says every cruise state write, mode included, goes through the state writer, with "no hand-edit path". On a new run, though, plan L38 writes the `factory mode` result into the pending state "at creation (today's creation path)". The CLI has no command that creates pending state or sets `mode` (the run's own `ESCALATE` decision notes "state CLI has no mode.chain writer"), so a new run's `mode.cruise` would be written outside the writer. Resume is covered (`resume <run> [mode flags]`); the new-run path is not. | Without changing scope, state in plan L38 and T008 exactly how `mode.cruise` reaches the pending state at creation: the same path that records `mode` and `stop_at` today (SKILL.md L45). Narrow FR-005 to "every write after the state exists" and name the creation path as the existing exception. Adding a writer instead would add a seam, so it would need a fresh `requires_user: true` scope confirmation. |
| G1 | Coverage gap | MEDIUM | tasks.md L74 (T009); core/skills/factory/references/protocol.md Relay step 2 and the initial-grilling paragraph; spec FR-006, FR-019 | T009 edits protocol.md relay step 2 and "Questions" and is done when "step 2 states both modes". It does not name three protocol.md statements that contradict cruise: (1) step 2's "(`mode.fast` true, except initial grilling)"; (2) "Notify once per auto-accepted batch", which FR-019 makes a log line under cruise; (3) the closing paragraph, "Grilling finishes only when the frontier is empty and the user confirms shared understanding", which FR-006 replaces with self-confirmation under cruise. T008 covers these only in SKILL.md, so the shipped protocol would contradict it. | Extend T009's description and Done condition to name all three statements and their cruise wording. The task stays documentation-only and exempt. |
| D1 | Terminology drift | LOW | CONTEXT.md L183-L184; spec.md L188 (Key Entities), FR-008 | CONTEXT.md defines "Cruise override" as a protected question's answer, an auto-resolved decision halt, or an accepted setup offer. It leaves out `analyze.pending_clarify` answers. The spec's Key Entities and FR-008 include them, and CONTEXT.md's "Protected question" covers only `requires_user: true`. | Add "or a `pending_clarify` answer" to the CONTEXT.md "Cruise override" definition. |

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 | Yes | T003, T004, T008 | |
| FR-002 | Yes | T003, T004 | |
| FR-003 | Yes | T003, T004, T008 | |
| FR-004 | Yes | T002, T004 | |
| FR-005 | Partial | T002-T006 | new-run creation path, see I1 |
| FR-006 | Yes | T008 | protocol.md side, see G1 |
| FR-007 | Yes | T005, T009 | |
| FR-008 | Yes | T005, T006 | |
| FR-009 | Yes | T005, T006, T009 | |
| FR-010 | Yes | T009 | |
| FR-011 | Yes | T006, T008 | |
| FR-012 | Yes | T008 | unchanged behaviour |
| FR-013 | Yes | T006, T008 | |
| FR-014 | Yes | T008 | |
| FR-015 | Yes | T002, T007, T008 | |
| FR-016 | Yes | T007, T008 | |
| FR-017 | Yes | T008 | |
| FR-018 | Yes | T008 | |
| FR-019 | Yes | T008, T009 | protocol.md batch notice, see G1 |
| FR-020 | Yes | T008 | |
| FR-021 | Yes | T013, T014 | |
| FR-022 | Yes | T001, T008 | |
| FR-023 | Yes | T014, T015 | |
| SC-001..SC-003 | Validation plan | T001 | agent-driven; the constitution allows this |
| SC-004 | Yes | T002, T015 | |
| SC-005 | Yes | T003, T004 | |
| SC-006 | Yes | T014 | |

## Test-scope check

- Implementation tasks T002-T007 each map one declared seam (plan.md L121-L126). Each has ordered Red, Implement and Pass steps, red proof and a Done condition.
- Every failure path the tasks require is in the plan's declarations. No task asserts an undeclared seam or path.
- Confirmation: plan.md L131 (`plan` Q1, `auto: false`, answered by the user 2026-11-04) matches the complete declared seam-to-failure-path scope, entry for entry. `git log` shows no change to the `Seam:` or `Confirmed:` lines since the confirmation commit, so the acceptance is current.
- Plan-exempt tasks T001 and T008-T015 are excluded from this check.

**Constitution Alignment Issues:** none. Principles I-V pass: `DESIGN.md` comes first (T001), the core stays harness-neutral (T014's grep), `dist/` is untouched (T014), state stays in `state.json`, and new items carry reasons.

**ENG-10:** every new file, abstraction and dependency has a stated reason (plan.md L90-L97). No finding.

**Word budgets:** all three artifacts are within budget (spec 2989/3000, plan 1927/2000, tasks 2126/2500).

**Unmapped Tasks:** none.

## Metrics

- Total requirements: 23 FR + 6 SC
- Total tasks: 15
- Coverage: 100% of FRs have at least one task (FR-005 partial, see I1)
- Ambiguity count: 0
- Duplication count: 0
- Critical issues: 0
- Severity counts: CRITICAL 0, HIGH 0, MEDIUM 2, LOW 1

## Next Actions

- Nothing blocks the run. Fix I1, G1 and D1 in place during remediation. None of them needs a user decision if I1 takes the scope-preserving wording fix.
