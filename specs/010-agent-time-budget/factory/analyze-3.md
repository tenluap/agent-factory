# Specification Analysis Report — pass 3

Feature: agent time budget, session issue backlog, benchmark (`010-agent-time-budget`)
Artifacts: `spec.md`, `plan.md`, `tasks.md`, with `research.md`, `data-model.md`, `contracts/cli.md`, `quickstart.md`, `CONTEXT.md`, `docs/adr/0007`, `.specify/memory/constitution.md`.
Read-only analysis. Context: pass 3 against the artifacts patched in place by remediation pass 2 (`factory/remediation-2.md`). Scope of this pass: verify the five pass-2 findings are closed and scan the remediation-touched text for contradictions it introduced. Per the orchestrator, `tasks.md` T029 owns the remaining `spec.md` wording follow-ups from `plan.md`; those stay covered, not open conflicts — T029 sufficiency is assessed below (one defect: I6).
Severity policy: HIGH (blocking) only for implementation tasks without a mapped seam/test predecessor or naming an unlisted seam (none found; plan-exempt tasks excluded); MEDIUM non-blocking for ENG-10 reason gaps and word-budget overruns (none found); constitution violations CRITICAL (none found). Cross-artifact consistency findings keep their demonstrated severity but no finding here is a demonstrated behaviour failure, so the two wording findings stay non-blocking.

## Pass-2 findings — status

| Pass-2 ID | Status | Where it landed |
|---|---|---|
| I4 (stall-cap counted set) | resolved | The counted set is now one thing everywhere, keyed on the new `partial_return` record mark: only records marked `partial_return: true` (a `partial` return's stop, whatever its stop reason) count; failure-policy retries are unmarked and never count. Consistent across `spec.md` FR-004 (new carve-out sentence), `research.md` §5/§7 (kind/role keying demoted to a rejected alternative), `data-model.md` (record shape, stall relationship, Partial return entity), `contracts/cli.md` (`issue-add`/`ledger-add` signatures, stalls paragraph), `quickstart.md` §1/§3, `plan.md` (Summary, seam 1, follow-up bullets), `tasks.md` T002–T005, T008, T009, T014, T018, T029, and the US1/SC-001 `partial`-return terminology. The fix follows the settled authority (grill-with-docs Q1, `spec.md` Clarifications) and needs no user decision. Residual wording defects in the new FR-010 sentence: I6, I7. |
| V1 (red suite on stale base) | resolved | The base update is verified in this worktree: `9f3c04e Merge remote-tracking branch 'origin/main'` is in HEAD, `git merge-base HEAD origin/main` = `3d47c6d` (the installer-test fix), the branch contains it, and the tree is clean. `remediation-2.md` records `python3 -m unittest discover -s tools` green (194 tests, 2026-10-27). Independent re-run by this pass was not possible (the process-capture execution tool cannot verify process ownership for the suite's spawned children in this environment); the green-suite claim is therefore second-hand, and T028/SC-005 re-run the same recorded command at delivery, so no artifact gap remains. |
| U3 (test-module inventory) | resolved | `plan.md` Project Structure splits the four NEW modules from `tools/tests/{test_state,test_envelope}.py` (# EXTENDED), both ENG-10 rows say "extend the existing … module", Scale/Scope reads "4 new test modules, 2 existing test modules extended, edits to 11 existing files" (matches the 11 edited files in the structure block: `DESIGN.md`, `core/skills/factory/SKILL.md`, `core/skills/factory/references/{protocol,state}.md`, `core/roles/{spec-builder,code-build,fixer}.md`, `factory_cli/{state,commands,checks,cli}.py`), and T002/T010 name both modules as existing/extended. |
| U4 (exemption grounding) | resolved | `plan.md` "Test seams" declares `Exempt: specs/010-agent-time-budget/spec.md — specification wording only, no executable behavior`, grounding T029's exemption. Seam names unchanged, so the `Confirmed:` line stays valid (no re-confirmation due). |
| I5 (`factory version` vs `factory_sha`) | resolved | T029 and `plan.md`'s FR-011 follow-up bullet both carry "at first use in US3/SC-003/Key Entities write 'the factory version (`factory_sha`)'". |

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| I6 | Inconsistency (new wording) | MEDIUM (non-blocking) | tasks.md T029 (FR-010 clause); plan.md "Spec alignment follow-ups" FR-010 bullet | The remediation's new sentence "`retry` records every re-spawn of a stage after a stopped return (a failure-policy retry and a non-deadline `partial` stop, e.g. low context, alike)" over-generalises in both directions: taken literally, the re-spawn after a **deadline** stop is also "a re-spawn of a stage after a stopped return", but its record is `overrun`, not `retry` (T014: "`overrun` for a deadline stop, `retry` for any other stop reason"; `research.md` §5: "a deadline stop as `overrun` … any other stop reason as `retry`"; `data-model.md` Partial return), and a failure-policy retry follows a *failure*, not a stopped return. Applied to `spec.md` FR-010 by T029 as written, the clause would claim the deadline stop's record kind as `retry` and, with FR-002's overrun report, invite two records for one stop (US2 scenario 1 and SC-002 both require exactly one). | Reword the clause in both places to name exactly the two `retry` producers: "`retry` records a non-deadline `partial` stop (e.g. low context) — marked `partial_return: true` — and a failure-policy retry — unmarked — alike; a deadline stop is recorded as `overrun` (FR-002), still marked when it is a `partial` return's stop." One clause, no behaviour change to the design. |
| I7 | Underspecification (record routing) | LOW | tasks.md T014, T009; `research.md` §5/§7; plan.md ENG-10 `append_issue` row | One stop can reach the writer twice: T014 has the orchestrator record "its stop as one issue marked `--partial-return`", while T009's `ledger-add` auto-records an issue for the same spawn from `--overrun` or the duration-over-budget detection. Which command owns the record is unstated ("via `ledger-add --overrun`/`issue-add`", research §7), and the safety net — `append_issue` "dedupe where signals meet" (plan ENG-10) — names no dedupe key and no seam test drives the cross-command case (T008 covers within-`ledger-add` dedupe only). | One clause in T014: the deadline stop's issue is recorded by `ledger-add` (self-report `--overrun`, or `unreported` from detection); `issue-add` records only what `ledger-add` leaves unrecorded (non-deadline `partial` stops, failure-policy retries). Optionally name `append_issue`'s dedupe key (stage, role, `commit`, kind) in the seam-1 description so T004's "one record per event" pins it. |

**Total findings: 2** (HIGH 0, MEDIUM 1, LOW 1; CRITICAL 0).

## Coverage Summary Table

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 | yes | T006, T007, T014 | deadline per spawn, budget fallback |
| FR-002 | yes | T010, T011, T012, T013 | clock check, overrun report, closed cause list |
| FR-003 | yes | T012, T014 | `partial` for all three file-writing roles; re-spawn |
| FR-004 | yes | T005, T014 | stall rule — counted set now the `partial_return` mark (I4 closed) |
| FR-005 | yes | T009, T013 | T013 edits the three file-writing roles; T009 records post-hoc overruns for any role |
| FR-006 | yes | T008, T009 | ledger detection, single-issue dedupe, `unreported` — cross-command routing, see I7 |
| FR-007 | yes | T006, T009, T014 | `orchestrator` role in budget lookup; verify overruns recorded only |
| FR-008 | yes | T004, T005 | signature/record superset via T029 (`--partial-return`, `partial_return` included) |
| FR-009 | yes | T002, T003 | schema v5, readers accept 1–5, `partial_return` validation |
| FR-010 | yes | T015, T016, T018 | halt / verify-fail in writer; retry / agent-failure via issue-add — T029 clause defective, see I6 |
| FR-011 | yes | T019, T020 | structural export gate, zero-issue export, `factory_sha` naming via T029 |
| FR-012 | yes | T021, T022 | list, claim refusals, `claimed` transition |
| FR-013 | yes | T023 | `/factory improve` lists and suggests, never starts |
| FR-014 | yes | T024, T026 | fixture + seeded pending state, approver stop |
| FR-015 | yes | T025, T026 | run / score / compare; score's `human_ms`/`fix_rounds` remain a superset of the spec list |
| FR-016 | yes | T025, T026 | four named pass conditions |
| FR-017 | yes | T025, T026 | state read through shared modules; recorded-state fixtures |
| FR-018 | yes | T027 | manual fallback documented |
| FR-019 | yes | T002–T026, T028 | suite coverage + re-render and drift gate (base green after the `origin/main` merge) |
| SC-001 | yes | T006–T014 | reduced-budget overrun/continuation/halt tests; `partial`-return wording aligned |
| SC-002 | yes | T002, T004, T015 | five event kinds + additive-shape assertion + `partial_return` validation |
| SC-003 | yes | T019, T021 | refusal before end, presence and claimability after |
| SC-004 | yes | T025, T026 | metrics, delta, named failing condition, no scorer crash |
| SC-005 | yes | T028 | suite + build gate clean — achievable on the current base |

FR coverage: 19/19 (100%). SC coverage: 5/5 mapped.

## Constitution Alignment Issues

None. I: T001 records `DESIGN.md` first. II: `deadline` is spawn input data in `core/`; harness headless commands live only in `tools/bench.py`. III: T028 re-renders every harness and runs the porcelain drift gate. IV: budget, issues, stall counts and backlog status all live in `state.json` / factory-home files. V: every declared new file, abstraction and dependency carries a reason in the ENG-10 table (verified: `budget.py`, `improvements.py`, `append_issue`, `bench.py`, `conformance/bench/greet-001/*`, both extended test modules, the four new test modules + fixtures, dependencies `none`); no ENG-10 finding. The I6/I7 findings are Writing Standards' "one term for one concept" / clarity discipline, not principle violations.

## Unmapped Tasks

None. Every task maps to a user story, FR, or the plan's delivery/exemption duties.

## Seams and test precedence (factory override)

Clean. All nine implementation tasks (T003, T005, T007, T009, T011, T016, T020, T022, T026) name a seam listed in plan.md "Test seams" and are each immediately preceded by a failing-test task for that seam (T002→T003, T004→T005, T006→T007, T008→T009, T010→T011, T015→T016, T019→T020, T021→T022, T025→T026). All eleven remaining tasks (T001, T012–T014, T017, T018, T023, T024, T027–T029) carry a plan-declared exemption instead of a test task — T029's `specs/**` exemption is now declared in the plan (U4 closed). The `Confirmed:` line lists the seven current seam names exactly (the remediation changed seam 1's description only), so no seam re-confirmation is due.

## Word budgets (factory override)

`wc -w`: `spec.md` 2998 / 3000, `plan.md` 1562 / 2000, `tasks.md` 2084 / 2500. All within budget; no findings. (Note for T029: `spec.md` has 2 words of headroom — the wording follow-ups must be funded by trimming, as the pass-2 remediation did.)

## Metrics

- Total Requirements: 19 FR + 5 buildable SC = 24
- Total Tasks: 29 (9 failing-test, 9 implementation, 11 exempt)
- Coverage %: 100% of FRs and SCs have >=1 task
- Ambiguity Count: 1 (I7, record routing across `issue-add`/`ledger-add`)
- Duplication Count: 0
- Critical Issues Count: 0

## Next Actions

- **I6** before `/speckit-implement`: reword the FR-010 clause in `plan.md`'s follow-up bullet and T029 so `retry` names exactly the non-deadline `partial` stop and the failure-policy retry, and the deadline stop keeps `overrun` (T014 / `research.md` §5 are the authority).
- **I7**: one clause in T014 naming `ledger-add` as the recorder of the deadline stop's issue and `issue-add` as the recorder only of what `ledger-add` leaves unrecorded; optionally pin `append_issue`'s dedupe key in seam 1's description.
- V1 needs no further artifact work: T028 runs the recorded test command and the build gate on the merged base.
