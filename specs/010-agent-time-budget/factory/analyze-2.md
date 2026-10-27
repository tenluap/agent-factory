# Specification Analysis Report — pass 2

Feature: agent time budget, session issue backlog, benchmark (`010-agent-time-budget`)
Artifacts: `spec.md`, `plan.md`, `tasks.md`, with `research.md`, `data-model.md`, `contracts/cli.md`, `quickstart.md`, `CONTEXT.md`, `docs/adr/0007`, `.specify/memory/constitution.md`.
Read-only analysis. Context: pass 2 after the escalated chain (clarify: no changes; grill-with-docs: FR-004 stall cap settled in favour of the spec, CONTEXT.md + ADR 0007 recorded; plan.md and tasks.md edited in place). Per the orchestrator, `tasks.md` T029 owns the plan's "Spec alignment follow-ups (spec.md wording)"; those items are covered, not open conflicts — unless T029 is insufficient (one case: I4).
Severity policy: HIGH (blocking) for implementation tasks without a mapped seam/test predecessor or naming an unlisted seam (none found); MEDIUM non-blocking for ENG-10 reason gaps and word-budget overruns; constitution violations stay CRITICAL (none found).

## Pass 1 findings — status

| Pass-1 ID | Status | Where it landed |
|---|---|---|
| I1 (FR-008 signature/record vs design) | resolved | T029 adopts the design superset (signature, record `{ at, kind, stage, role, cause, detail, duration_ms, commit }`, `--cause` only required for `overrun`). |
| I2 (FR-004 stall-cap trigger) | resolved | grill-with-docs Q1: FR-004 stands, every `partial` return counts whatever its stop reason; design widened (research.md §5, data-model.md, contracts/cli.md, plan.md summary, T004/T014); spec.md Clarifications records the decision. Residual on the counted set: I4. |
| C1 (SC-002 older-reader clause) | resolved | T002 and plan seam 5 now assert the additive v5 shape (every v4 key keeps name and shape, `issues[]` the only new top-level key) — the checkable form of old-reader compatibility. |
| U1/U2 (test_state.py / test_envelope.py missing from plan) | resolved, over-corrected | Both now in the plan's inventory and ENG-10 table, but marked NEW and counted as "6 new test modules" although both modules already exist on `origin/main` — see U3. |
| I3 (backlog filename / `factory_sha` naming) | mostly resolved | T029 fixes FR-011, its assumption and adds the `factory_sha: null` edge case. Prose occurrences outside T029's scope remain — see I5. |

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| I4 | Inconsistency | HIGH | spec.md FR-004 vs US1 scenario 4 ("stopped returns") and SC-001 ("stops"); contracts/cli.md `issue-add` stall note ("and so does a failure-policy retry of a resumable role"); research.md §5 (counted set keys on kind/role); tasks.md T004 (kind/role keying) vs T014 ("three partial returns"); docs/adr/0007 ("three consecutive `partial` returns"); plan.md "Spec alignment follow-ups" | The stall-cap counted set is still not one thing. FR-004 and ADR 0007 count three consecutive `partial` returns; the design keys the counter on kind+role — trailing `overrun`/`retry` records of a file-writing role sharing one `commit` — which also counts **failure-policy retry** records (cli.md says so explicitly). Both retry sources share one record shape (`kind: retry`, no discriminator), so the design's counter cannot exclude failure-policy retries, while FR-004's wording excludes them. T029's FR-010 edit ("the stall cap reads that record") does not restate FR-004's counted set — T029 is insufficient here. Behaviour difference: a streak mixing failure-policy retries with partial stops halts at 3 under the design, but counts only the partial returns under FR-004. | Extend T029 with one FR-004 sentence naming the counted set in record terms: three consecutive `overrun`/`retry` issues of one file-writing role sharing one `commit` — a `partial` return's stop whatever its reason and a failure-policy retry alike (they are the same record) — halt; never-stopped roles' records and `agent-failure`/`halt`/`verify-fail` never count. This is the authority-consistent, mechanically forced reading (ADR 0007's rationale — "the stall cap on stops without new progress" — supports it). The narrower FR-004 reading would need a discriminator in the issue record (schema change beyond `issues[]`) — if that reading is wanted, raise it as `pending_clarify` rather than guessing. |
| V1 | Verification (delivery) | MEDIUM (non-blocking) | state `commands.test`; plan.md "Testing"; tasks.md T028; spec.md SC-005 | `python3 -m unittest discover -s tools` is red in this worktree: 194 tests, 2 failures, both in `tools/tests/test_install.py` (`FACTORY_HOME does not exist` — the tests set an explicit `FACTORY_HOME` they do not create). Root cause is base staleness, not this feature: the branch base predates `3d47c6d` "Fix OpenCode installer test setup for explicit factory home (#5)" on `origin/main` (the branch is exactly that one commit behind; the commit fixes both tests). As-is, T028's recorded test command and SC-005 cannot go green in this worktree. | Update the base (rebase/merge onto current `origin/main`, or cherry-pick `3d47c6d`) before the build/test gate, and name that prerequisite in T028 or plan "Testing" so the gate's red is never mistaken for this feature's regression. No feature-scope change. |
| U3 | Underspecification (inventory) | MEDIUM (non-blocking) | plan.md "Project Structure" (`# NEW` on the test-module line), ENG-10 table, "Scale/Scope"; tasks.md T002/T010 | `tools/tests/test_state.py` and `tools/tests/test_envelope.py` already exist on `origin/main` (state seam: v1–4 read acceptance, v4 upgrade, atomic write; envelope seam: `factory_cli.checks` against the references' fenced shapes). T002/T010 extend them; the plan marks all six modules NEW and the scale line counts "6 new test modules" (only 4 are new) and "edits to 8 existing core files" (the structure block lists 11: `DESIGN.md` + 10 under `core/`, plus `README.md`/`docs/` in T027). | Split the structure line into new (`test_issues`, `test_budget`, `test_improvements`, `test_bench`) and extended (`test_state`, `test_envelope`), reword the two ENG-10 rows to "extend existing module with the v5 seam" / "…the envelope partial/overrun seam", and correct Scale/Scope ("4 new test modules, 2 existing extended; edits to 11 existing files"). Inventory accuracy only; no behavioural consequence. |
| U4 | Underspecification (exemption coverage) | LOW | plan.md "Test seams" exemption lists; tasks.md T029 | The plan exempts `DESIGN.md`, `README.md`, `docs/**`, `core/**/*.md`, `conformance/bench/**`, `dist/**`, but not `specs/**`. T029 carries "Exempt: `specs/010-agent-time-budget/spec.md` - specification wording only" — an exemption the plan does not declare, so the task's exemption is ungrounded in the plan's seam contract (the plan delegates those edits in prose only). | Add `specs/010-agent-time-budget/spec.md` to the plan's documentation exemption line ("specification wording only, no executable behavior"). One line; keeps the "every task is test-preceded or plan-exempt" invariant literally true. |
| I5 | Inconsistency (terminology) | LOW | spec.md US3, SC-003, Key Entities vs FR-011 | "the factory version" remains in US3 scenario 2, SC-003 and the Improvement-backlog entity where T029 names the field `factory_sha` (T029 covers FR-011 + its assumption only). One concept, two names. | Add one clause to T029: at first use in US3/SC-003/Key Entities write "the factory version (`factory_sha`)". |

**Total findings: 5** (HIGH 1, MEDIUM 2, LOW 2; CRITICAL 0).

## Coverage Summary Table

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 | yes | T006, T007, T014 | deadline per spawn, budget fallback |
| FR-002 | yes | T010, T011, T012, T013 | clock check, overrun report, closed cause list |
| FR-003 | yes | T012, T014 | partial for all three file-writing roles; re-spawn |
| FR-004 | yes | T005, T014 | stall rule — counted-set drift remains, see I4 |
| FR-005 | yes | T009, T013 | T013 edits only the three file-writing roles; T009 records post-hoc overruns for any role |
| FR-006 | yes | T008, T009 | ledger detection, single-issue dedupe, `unreported` |
| FR-007 | yes | T006, T009, T014 | `orchestrator` role in budget lookup; verify overruns recorded only |
| FR-008 | yes | T004, T005 | signature/record aligned to design via T029 (was I1) |
| FR-009 | yes | T002, T003 | schema v5, readers accept 1–5 |
| FR-010 | yes | T015, T016, T018 | halt / verify-fail in writer; retry / agent-failure via issue-add per SKILL.md |
| FR-011 | yes | T019, T020 | structural export gate, zero-issue export |
| FR-012 | yes | T021, T022 | list, claim refusals, `claimed` transition |
| FR-013 | yes | T023 | `/factory improve` lists and suggests, never starts |
| FR-014 | yes | T024, T026 | fixture + seeded pending state, approver stop; `conformance/fixture-repo` exists (README, src, test_greet.py) |
| FR-015 | yes | T025, T026 | run / score / compare; design's score adds `human_ms`/`fix_rounds` beyond the spec list — a superset, SC-004's "every listed metric" still holds, no finding |
| FR-016 | yes | T025, T026 | four named pass conditions |
| FR-017 | yes | T025, T026 | state read through shared modules; recorded-state fixtures |
| FR-018 | yes | T027 | manual fallback documented |
| FR-019 | yes | T002–T026, T028 | suite coverage + re-render and drift gate (gate currently red on stale base, see V1) |
| SC-001 | yes | T006–T014 | reduced-budget overrun/continuation/halt tests |
| SC-002 | yes | T002, T004, T015 | five event kinds + additive-shape assertion (was C1) |
| SC-003 | yes | T019, T021 | refusal before end, presence and claimability after |
| SC-004 | yes | T025, T026 | metrics, delta, named failing condition, no scorer crash |
| SC-005 | yes | T028 | suite + build gate clean — unachievable on the current base, see V1 |

FR coverage: 19/19 (100%). SC coverage: 5/5 mapped; SC-005 gated on V1.

## Constitution Alignment Issues

None. I: T001 records `DESIGN.md` first. II: `deadline` is spawn input data in `core/`; harness headless commands live only in `tools/bench.py` (adr 0007 and the roles use the neutral verbs). III: T028 re-renders every harness and runs the porcelain drift gate. IV: budget, issues, stall counts and backlog status all live in `state.json` / factory-home files. V: every declared new file, abstraction and dependency carries a reason (U3 corrects provenance labels, not reasons). Writing Standards' "one term for one concept" is what I5 tidies in the spec prose.

## Unmapped Tasks

None. Every task maps to a user story, FR, or the plan's delivery/exemption duties.

## Seams and test precedence (factory override)

Clean. All nine implementation tasks (T003, T005, T007, T009, T011, T016, T020, T022, T026) name a seam listed in plan.md "Test seams" and are each immediately preceded by a failing-test task for that seam. All eleven remaining tasks (T001, T012–T014, T017, T018, T023, T024, T027–T029) carry an exemption instead of a test task. The `Confirmed:` line still lists the seven current seam names exactly (the seam list changed only inside seam 5's description), so no seam re-confirmation is due. One grounding gap in the exemption lists: U4.

## Word budgets (factory override)

`spec.md` 2997 / 3000, `plan.md` 1488 / 2000, `tasks.md` 1952 / 2500. All within budget; no findings.

## Metrics

- Total Requirements: 19 FR + 5 buildable SC = 24
- Total Tasks: 29 (9 failing-test, 9 implementation, 11 exempt)
- Coverage %: 100% of FRs and SCs have >=1 task
- Ambiguity Count: 1 (I4, the stall-cap counted set)
- Duplication Count: 0
- Critical Issues Count: 0

## Next Actions

- **I4 before `/speckit-implement`**: extend T029's FR-004 wording (and, if desired, ADR 0007's consequence sentence) to the record-level counted set; only a user wanting the narrower FR-004 semantics needs a `pending_clarify` round, since that reading requires a schema discriminator the v5 record does not have.
- **V1** is a base update, not an artifact rewrite: rebase/merge onto `origin/main` (or cherry-pick `3d47c6d`) and note the prerequisite in T028 or plan "Testing".
- U3, U4 and I5 are in-place edits to `plan.md` and one clause added to T029's wording.
