# Specification Analysis Report (pass 1)

Feature: `021-cruise-mode`. Artifacts: `spec.md` (2962 words), `plan.md` (1797), `tasks.md` (1900); constitution `.specify/memory/constitution.md` v2.0.0. Extension hooks skipped (factory owns the flow).

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| T1 | Test scope (ENG-4, Confirmed test scope) | HIGH (blocking) | tasks.md:L22-27 (T002); plan.md:L34, L121, L127 | T002's Implement step enforces the plan's marker invariant "`gate-override` with the marker only at stage `analyze`", so `validate_state` rejects a marked `gate-override` at any stage other than `analyze` (for example `review`). That failure path is not in the declared or confirmed `validate_state` failure paths, which list only "marker on `approved` or at stage `approver`". T002's Red step does not test it. The Red step also asserts a further undeclared `validate_state` failure path: "`gate-override` with `auto: true` and no marker still fails". | Pick one. (a) Narrow T002 to the declared scope: `validate_state` rejects only the declared paths, the `analyze`-only restriction stays on the declared `decisions-add` guard, and the existing "gate decision is never auto" regression is left to the existing `tools/tests/test_state.py` coverage. (b) Add both paths to the plan's `validate_state` declaration. A changed scope invalidates the `Confirmed:` line, so (b) needs fresh `requires_user: true` confirmation. |
| T2 | Test scope (ENG-4, Confirmed test scope) | HIGH (blocking) | tasks.md:L63-68 (T007); plan.md:L35, L122, L127 | T007's Red step calls `factory_cli.checks.permitting_decision` directly ("`permitting_decision` returns none"). It also asserts `gate_violation` into `implement` ("the analyze-into-implement gate still accepts a marked `gate-override` at `analyze`"). The declared and confirmed seam is only `factory_cli.checks.gate_violation` into `pr`, so T007 tests a seam and a scope that are not declared. | Pick one. (a) Keep T007 on the declared seam: drop the direct `permitting_decision` assertion (and the `permitting_decision` edit, if it is unreachable because `validate_state` already forbids the marker at `approver`) and drop the implement-gate assertion (T006 already covers it through `checkpoint analyze --next implement`). (b) Declare `permitting_decision` and the `implement` scope in the plan, which needs fresh `requires_user: true` confirmation. |
| U1 | Underspecification | MEDIUM | plan.md:L43, L98; tasks.md:L72 (T008) | Fixed-id setup-offer decisions (`setup-speckit`, `setup-commands`, `setup-impeccable`) have no `<stage>`, and `decisions-add` needs one from `STAGES`, which has no `preflight`. Only `intake` (`grill`) and `analyze-exhaustion` (`analyze`) name their stage. | Name the stage of each setup decision in the plan and T008 (for example `grill` for the preflight offers recorded into the pending state, `review` for `setup-impeccable`). |
| C1 | Coverage gap | MEDIUM | README.md:L118-L135 (repo); tasks.md T001/T008 | README's flag usage and flag table list `--fast`/`--no-fast` for new runs and resume. No task adds `--cruise`/`--no-cruise` there, so the user-facing docs would omit the new flags. | Add the README flag rows and resume example to T001 or T008 (documentation only, exempt). |
| C2 | Constitution workflow gate coverage | MEDIUM | tasks.md:L86 (T014); constitution "Development Workflow" | The constitution's test gate `test -z "$(git ls-files -- dist/)"` is missing from T014. Nothing in the plan conflicts with principle III (no `dist/` edit), so this is a missing verification step, not a violation. | Add the `git ls-files -- dist/` empty check to T014's Done condition. |
| E1 | ENG-10 (non-blocking) | MEDIUM | tasks.md:L57 (T006: "shared helper if both need it"); plan.md:L88-93 | The tasks may add a new abstraction, a shared cruise-guard helper for `cmd_answer` and `cmd_decisions_add`. Its reason is missing from the plan's "New files, abstractions, dependencies" list. | Either state the helper and its reason in the plan list, or make T006 reuse T005's guard inline without naming a new abstraction. |
| A1 | Ambiguity | LOW | spec.md FR-003; plan.md:L37; tasks.md T003 | "`--no-fast` present" rejects `--no-fast --fast --cruise` even though fast ends on by last-wins. This matches brief Q1's wording, but no test pins it. | Add one T003 assertion for that case so the presence rule is explicit. |
| L1 | Coverage (agent-driven SCs) | LOW | spec.md SC-001..SC-003; tasks.md T001 | SC-001..SC-003 are only written into `DESIGN.md`'s validation plan (T001). No task executes them. The constitution allows this ("before it is relied on"), so it is noted only. | No change required. Optionally name the fixture run in the validation-plan entry. |
| L2 | Constitution V traceability | LOW | plan.md:L88-93, L33, L44 | New fields `mode.cruise`, `cruise_override` and the harness bullet `no_prompt_launch`, plus the flag `--cruise-override`, have their reasons in "Decisions" but are not listed in the "New files, abstractions, dependencies" section. | List them there with a one-line reason each, for traceability. |

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 | Yes | T003, T004, T008 | |
| FR-002 | Yes | T003 | |
| FR-003 | Yes | T003, T004, T008 | see A1 |
| FR-004 | Yes | T002, T004 | |
| FR-005 | Yes | T005, T006 | |
| FR-006 | Yes | T008 | |
| FR-007 | Yes | T005, T009 | |
| FR-008 | Yes | T005 | |
| FR-009 | Yes | T005, T006, T009 | |
| FR-010 | Yes | T009 | |
| FR-011 | Yes | T006, T008 | |
| FR-012 | Yes | T008 | unchanged behaviour |
| FR-013 | Yes | T006, T008 | see U1 |
| FR-014 | Yes | T008 | |
| FR-015 | Yes | T002, T007, T008 | |
| FR-016 | Yes | T007, T008 | push only after Approve (existing step 9) |
| FR-017 | Yes | T008 | |
| FR-018 | Yes | T008 | |
| FR-019 | Yes | T008, T009 | |
| FR-020 | Yes | T008 | |
| FR-021 | Yes | T013, T014 | |
| FR-022 | Yes | T001, T008 | see C1 |
| FR-023 | Yes | T014, T015 | see C2 |
| SC-001..SC-003 | Partial | T001 (validation plan) | see L1 |
| SC-004 | Yes | T002, T015 | |
| SC-005 | Yes | T003, T004 | |
| SC-006 | Yes | T014 | |

## Test-scope check

- Implementation tasks T002-T007 each map a declared seam and contain ordered Red, Implement and Pass steps, red proof and a Done condition.
- Confirmation (`plan.md` L127, Q1 explicitly accepted 2026-11-04, `auto: false`) matches the complete declared seam-to-failure-path scope.
- Exceptions: T1 and T2 require paths or seams beyond that scope.
- Plan-exempt tasks T001, T008-T015 are excluded from this check.

**Constitution Alignment Issues:** none. All five principles PASS. C2 is a missing workflow-gate check, not a violation.

**Unmapped Tasks:** none. T014 and T015 are verification tasks mapped to FR-023, SC-004 and SC-006.

**Word budgets:** all within budget (spec 2962/3000, plan 1797/2000, tasks 1900/2500).

## Metrics

- Total requirements: 23 FR + 6 SC
- Total tasks: 15
- Coverage: 100% of FRs have at least one task (SC-001..SC-003 through the validation plan only)
- Ambiguity count: 1
- Duplication count: 0
- Critical issues: 0
- Severity counts: CRITICAL 0, HIGH 2, MEDIUM 4 (E1 non-blocking), LOW 3

## Next Actions

- Fix T1 and T2 before implement. Option (a) in each keeps the confirmed scope unchanged. Option (b) changes the scope and needs a fresh `requires_user: true` confirmation.
- Fix U1, C1, C2, E1, A1, L1 and L2 in place during remediation.
