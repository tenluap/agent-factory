# Specification Analysis Report — pass 1

Feature: agent time budget, session issue backlog, benchmark (`010-agent-time-budget`)
Artifacts: `spec.md`, `plan.md`, `tasks.md`, with `research.md`, `data-model.md`, `contracts/cli.md`, `quickstart.md`, `.specify/memory/constitution.md`.
Read-only analysis. Severity per the factory override: HIGH (blocking) for implementation tasks without a mapped seam/test predecessor; MEDIUM non-blocking for ENG-10 reason gaps and word-budget overruns (none found). Constitution violations stay CRITICAL (none found).

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| I1 | Inconsistency | HIGH | spec.md FR-008; contracts/cli.md "Changed write commands"; data-model.md "Session issue"; tasks.md T004/T005 | FR-008 states the signature `factory issue-add <kind> <stage> <role> --cause --detail --duration-ms` and an issue carrying "kind, stage, role, cause, detail and duration". The design and tasks make `--cause` optional (null for non-overrun kinds), add `--commit <sha>`, and give the record `at` and `commit` fields. Spec names the CLI contract user-facing, so the two contracts conflict on what the command requires and what a record contains. | Align `spec.md` FR-008 with `contracts/cli.md` (cause optional except for `overrun`; record `{ at, kind, stage, role, cause, detail, duration_ms, commit }`), since the `commit` provenance is what makes FR-004's stall rule checkable. Remediation is a targeted spec edit; no user decision needed. |
| I2 | Inconsistency | HIGH | spec.md FR-004, US1 scenario 4; state decisions G1; research.md "Stall cap bookkeeping"; data-model.md "Session issue"; tasks.md T005 | FR-004 (and settled grill decision G1: "halt after 3 consecutive partial spawns with no new commit") count consecutive `partial` **returns** without a new commit. The design narrows the cap to consecutive **deadline stops** ("three consecutive `overrun` issues of one stage sharing one `commit`"; low-context `partial` returns explicitly rejected from the count). A loop of non-deadline partials with no new commit halts under FR-004/G1 but never halts as designed. | Decide which trigger is authoritative and write it in one place. Extending the counter to every `partial` without a new commit matches FR-004 and the settled G1 answer; narrowing FR-004 to deadline stops only contradicts G1 and looks like a user decision — if the narrowing stands, spec FR-004, US1 scenario 4 and edge case 3 must be edited to say "deadline stops" and name what breaks the streak. Likely `pending_clarify`. |
| C1 | Coverage Gap | MEDIUM | spec.md SC-002, edge case "Run state written by the new version stays readable by readers that predate this feature"; tasks.md T002 | SC-002 requires "a run written by this version is still read successfully by an older reader". T002 tests only the new reader accepting schema 1–5. No task asserts the reverse direction (old reader on a v5 state), so the SC clause has zero test coverage. | Add to T002's failing-test scope: assert the v5 shape is purely additive — every v4 key keeps its name and shape in the upgraded state, `issues[]` is the only new top-level key — which is the checkable form of old-reader compatibility (the old reader itself cannot be run from the new suite). |
| U1 | Underspecification (ENG-10) | MEDIUM | plan.md "Project Structure" and ENG-10 table; tasks.md T002 | `tools/tests/test_state.py` is created by T002 but appears in neither the plan's file inventory (which lists only `test_{issues,budget,improvements,bench}.py`) nor the ENG-10 table, so the new file has no stated reason in the plan. | Add `tools/tests/test_state.py` to the plan's structure block and an ENG-10 row (`file | one test module per the state-schema-v5 seam`); also correct the plan's "4 new test modules" scale line to 6. Non-blocking. |
| U2 | Underspecification (ENG-10) | MEDIUM | plan.md "Project Structure" and ENG-10 table; tasks.md T010 | `tools/tests/test_envelope.py` is created by T010 but is absent from the plan's file inventory and ENG-10 table. | Add `tools/tests/test_envelope.py` to the plan's structure block and an ENG-10 row (`file | one test module per the envelope partial/overrun seam`). Non-blocking. |
| I3 | Inconsistency | LOW | spec.md FR-011 + assumption; plan.md Storage; data-model.md "Improvement backlog" | Naming drift on the same things: backlog file `<repo>-<branch>.json` (spec) vs `<repo-name>-<branch>.json` (plan, data-model); "the factory version" (US3, SC-003) vs "the factory git sha" / `factory_sha` (FR-011, data-model). The nullable `factory_sha` (best-effort, `null` outside a git tree) is documented only in the design, not in spec edge cases. | Pick one form per concept (`<repo-name>-<branch>`, `factory_sha`) in spec.md and add one edge case: export succeeds with `factory_sha: null` when the factory install is not in a git tree. |

**Total findings: 6** (HIGH 2, MEDIUM 3, LOW 1; CRITICAL 0).

## Coverage Summary Table

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 | yes | T006, T007, T014 | deadline per spawn, budget fallback |
| FR-002 | yes | T010, T011, T012, T013 | clock check, overrun report, closed cause list |
| FR-003 | yes | T012, T014 | partial for all three file-writing roles; re-spawn |
| FR-004 | yes | T005, T014 | stall rule — trigger wording conflict, see I2 |
| FR-005 | yes | T009, T013 | implicit: T013 edits only the three file-writing roles; T009 records post-hoc overruns for any role |
| FR-006 | yes | T008, T009 | ledger detection, single-issue dedupe, `unreported` |
| FR-007 | yes | T006, T009, T014 | `orchestrator` role in budget lookup; verify overruns recorded only |
| FR-008 | yes | T004, T005 | signature/record conflict with design, see I1 |
| FR-009 | yes | T002, T003 | schema v5, readers accept 1–5 |
| FR-010 | yes | T015, T016, T018 | halt / verify-fail in writer; retry / agent-failure via issue-add per SKILL.md |
| FR-011 | yes | T019, T020 | structural export gate, zero-issue export |
| FR-012 | yes | T021, T022 | list, claim refusals, `claimed` transition |
| FR-013 | yes | T023 | `/factory improve` lists and suggests, never starts |
| FR-014 | yes | T024, T026 | fixture + seeded pending state, approver stop |
| FR-015 | yes | T025, T026 | run / score / compare |
| FR-016 | yes | T025, T026 | four named pass conditions |
| FR-017 | yes | T025, T026 | state read through shared modules; recorded-state fixtures |
| FR-018 | yes | T027 | manual fallback documented |
| FR-019 | yes | T002–T026, T028 | suite coverage + re-render and drift gate |
| SC-001 | yes | T006–T014 | reduced-budget overrun/continuation/halt tests |
| SC-002 | partial | T002, T004, T015 | five event kinds covered; older-reader clause uncovered, see C1 |
| SC-003 | yes | T019, T021 | refusal before end, presence and claimability after |
| SC-004 | yes | T025, T026 | metrics, delta, named failing condition, no scorer crash |
| SC-005 | yes | T028 | suite + build gate clean |

FR coverage: 19/19 (100%). SC coverage: 4/5 fully covered (SC-002 partial).

## Constitution Alignment Issues

None. I: T001 records `DESIGN.md` first. II: `deadline` is spawn input data in `core/`; the harness map lives in `tools/bench.py`, matching existing `tools/render.py` precedent — no `core/` file names a harness. III: T028 re-renders every harness and runs the porcelain drift gate. IV: budget, issues, stall counts and backlog status all live in `state.json` / factory-home files. V: every declared new file, abstraction and dependency carries a reason in the plan except the two test modules in U1/U2 (inventory drift, not a principle violation).

## Unmapped Tasks

None. Every task maps to a user story, FR, or the plan's delivery/exemption duties.

## Seams and test precedence (factory override)

Clean. All nine implementation tasks (T003, T005, T007, T009, T011, T016, T020, T022, T026) name a seam listed in plan.md "Test seams" and are each immediately preceded by a failing-test task for that seam. All ten plan-exempt tasks (T001, T012–T014, T017, T018, T023, T024, T027, T028) carry their exemption instead of a test task. Seam names in tasks.md match the plan's `Confirmed:` seam list exactly.

## Word budgets (factory override)

`spec.md` 2999 / 3000, `plan.md` 1278 / 2000, `tasks.md` 1745 / 2500. All within budget; no findings. (`spec.md` is one word under its budget — worth trimming in remediation anyway.)

## Metrics

- Total Requirements: 19 FR + 5 buildable SC = 24
- Total Tasks: 28
- Coverage %: 100% of FRs have >=1 task; SC 4/5 fully (1 partial)
- Ambiguity Count: 0 (no vague adjectives, no placeholders)
- Duplication Count: 0
- Critical Issues Count: 0

## Next Actions

- **Resolve I1 and I2 before `/speckit-implement`**: both are MUST-level contract conflicts between `spec.md` and the design/tasks. I1 is a mechanical spec alignment to `contracts/cli.md`. I2 needs an authority decision (FR-004/G1 "consecutive partial returns" vs the design's "consecutive deadline stops") — the design's narrowing contradicts the settled G1 answer, so it belongs in `pending_clarify` rather than a guess.
- C1, U1, U2 and I3 are in-place edits: extend T002's test scope, add the two test modules to the plan's inventory/ENG-10 table (and fix the "4 new test modules" count), and unify the backlog/`factory_sha` naming in `spec.md` with one added edge case.
- Command suggestions: run remediation against this report; if the user confirms the FR-004 trigger, edit `spec.md` FR-004 accordingly, otherwise widen the stall counter in T005 and `data-model.md`.
