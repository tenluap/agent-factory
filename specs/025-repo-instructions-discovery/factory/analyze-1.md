# Specification Analysis Report — pass 1

Feature: `025-repo-instructions-discovery`. Artifacts: `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `contracts/cli.md`, `quickstart.md`; constitution `.specify/memory/constitution.md` v2.0.0; engineering rules (factory `engineering.md`).

No blocking findings. No constitution MUST violation (Principle II carries its written justification, as Governance allows). Test scope is fully mapped and currently confirmed.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| C1 | Coverage gap | MEDIUM | spec.md FR-023; tasks.md T012 | FR-023 requires the orchestrator to read every `always` entry in full **at preflight and at grill**. T012's text-contract assertions name only the grill read (`git show <ref>:<path>`); the preflight read is neither asserted nor named in step 2. | Add to T012 step 1 an assertion that preflight (step 1 item 5, after `instructions-record`) reads every `always` entry at the recorded ref. |
| D1 | Constitution alignment (workflow gate) | MEDIUM | constitution "Development Workflow"; tasks.md T001; DESIGN.md "Validation plan" | The constitution says a change to the flow is validated end to end per DESIGN.md's "Validation plan". This feature changes preflight, grill and command sourcing (FR-022..FR-024), whose behaviour is role prose verified only by a text contract. T001 adds no "Validation plan" entry, unlike prior flow features (019, 021, 022, 023). Not CRITICAL: the sentence carries no MUST. | Extend T001 to add a "Repo instructions validation" entry under DESIGN.md "Validation plan": one real run showing preflight records and discloses the index, a resume showing the delta, and a fixture repo whose test command is documented only in `CONTRIBUTING.md` (SC-006). |
| A1 | Ambiguity (acceptance criterion) | MEDIUM | spec.md SC-006, US5 scenario 1; tasks.md T012 | SC-006 measures "100% of fixture checks", but the only planned proof is a text-contract test on `SKILL.md`; no fixture check exercises orchestrator command sourcing. The criterion as worded has no executable test. | Reword SC-006 to "the orchestrator text states it and the text-contract test asserts it", or point it at the validation-plan run from D1. |
| I1 | Inconsistency | LOW | spec.md Edge Cases ("Not a git repository…"); contracts/cli.md; research.md R9 | Spec says the writer "discloses the error as a note"; the contract and R9 put it in a separate `error` field (notes stay for malformed input). | Change the spec edge case to "reports it in `error`; the orchestrator discloses it". |
| I2 | Inconsistency | LOW | plan.md Technical Context "Performance Goals"; research.md R3 | Plan says "two git processes per scan"; R3 also runs `git rev-parse --verify` once, so three. | Say "three git processes per scan (rev-parse, ls-tree, cat-file --batch) regardless of entry count". |
| I3 | Inconsistency | LOW | plan.md Constitution Check II; plan.md Complexity Tracking | Constitution Check records Principle II as "PASS with justification"; Complexity Tracking says "No constitution violations". Governance requires the justification to be in the plan for a violation; the two lines disagree on whether it is one. | Make Complexity Tracking reference the Principle II justification explicitly ("Principle II: catalogue names other tools' file names as data; justification above"). |
| U1 | Underspecification | LOW | spec.md FR-005, SC-001; tasks.md T002 | T002's fixture includes a "submodule-like gitlink" but no listed assertion checks that nothing below it is indexed. | Add "no entry under the gitlink path" to T002 step 1 assertions. |
| U2 | Underspecification | LOW | spec.md FR-012, FR-024; data-model.md `source` | A root catalogue agent file also named in `instructions.include` takes `source: "config"` (config beats derived), which drops it from the top FR-024 command tier. The spec does not say whether that demotion is intended. | State in data-model.md that an include match on a catalogue file keeps `source: "catalogue"` (kind already `always`), or that config wins and the tier follows. |
| C2 | Coverage gap | LOW | spec.md FR-014; tasks.md T011 | FR-014 "`factory init` MUST NOT seed these lists" has only a done-condition note in the exempt T011, no assertion. | Add a one-line check in T011's done condition: `factory init` in a sandbox writes a `config.json` with no `instructions` key (existing init test may already cover the exact output). |
| T1 | Inconsistency | LOW | tasks.md T014; plan.md "Test seams" exemptions | T014 claims "Exempt: verification only" but plan.md declares no such exemption. T014 changes no behaviour, so no test-scope gap results. | Drop the "Exempt:" label from T014 (it is a verification step, not an exempt implementation task). |

## Test-scope check (engineering.md "Confirmed test scope")

Declared seams S1–S6 and failure paths match the `Confirmed:` line (2026-11-12, Q1 accepted, cruise override) exactly; the decision record in `state.json` carries `cruise_override: true` with the same scope.

| Task | Seam | Failure paths | Ordered red / impl / verify | Status |
|------|------|---------------|-----------------------------|--------|
| T002 | S1 | F1.1, F1.2, F1.9 | yes | OK |
| T003 | S1 | none beyond T002 | yes | OK |
| T004 | S1 | F1.4, F1.8 | yes | OK |
| T005 | S1 | F1.5, F1.6, F1.7 | yes | OK |
| T006 | S1 | F1.3 | yes | OK |
| T008 | S2, S4 | F2.2, F2.3, F4.1 | yes | OK |
| T009 | S2 | F2.1, F2.4 | yes | OK |
| T010 | S3, S5 | F3.1 | yes | OK |
| T012 | S6 | none | yes | OK |

Every declared failure path is covered by exactly one task. Plan-exempt tasks excluded: T001 (`DESIGN.md`), T007 (`.factory/config.json`), T011 (`references/state.md`, `models.py` README text), T013 (`CONTEXT.md`, ADR). T014 is verification only. No blocking test-scope finding.

## ENG-10 (new file / abstraction / dependency reasons)

Plan "New files, abstractions and dependencies" states a reason for `instructions.py`, `test_instructions.py`, `.factory/config.json`, `CATALOGUE`, the glob translator, the `instructions` state field and the `source` entry field; dependencies: none. The front-matter reader and fixpoint classifier are justified in research.md R5/R6. No ENG-10 finding.

## Word budgets

`spec.md` 2990 / 3000; `plan.md` 1206 / 2000; `tasks.md` 2301 / 2500. All within budget (spec within 10 words of its limit: remediation edits to spec.md must not grow it net).

## Coverage Summary

| Requirement | Has task? | Task IDs | Notes |
|---|---|---|---|
| FR-001 | yes | T002 | ref read, untracked/modified ignored |
| FR-002 | yes | T002, T003 | |
| FR-003 | yes | T003 | |
| FR-004 | yes | T005 | |
| FR-005 | yes | T002, T003 | submodule assertion implicit (U1) |
| FR-006 | yes | T002 | |
| FR-007 | yes | T003, T004 | |
| FR-008 | yes | T005 | |
| FR-009 | yes | T004 | |
| FR-010 | yes | T002, T003 | |
| FR-011 | yes | T002, T005, T009 | |
| FR-012 | yes | T005, T006 | |
| FR-013 | yes | T006 | |
| FR-014 | partial | T011 | no assertion (C2) |
| FR-015 | yes | T007 | |
| FR-016 | yes | T002 | |
| FR-017 | yes | T008 | |
| FR-018 | yes | T009 | |
| FR-019 | yes | T009 | |
| FR-020 | yes | T008, T011 | |
| FR-021 | yes | T010 | |
| FR-022 | yes | T012 | |
| FR-023 | partial | T012 | preflight read not asserted (C1) |
| FR-024 | yes | T012 | |
| FR-025 | yes | T001, T012, T014 | |
| FR-026 | yes | T013 | terms present in CONTEXT.md |
| FR-027 | yes | T013 | 0020 free on origin/main and every remote branch at analyze time |
| FR-028 | yes | T002–T012 | |
| SC-001 | yes | T002–T006 | |
| SC-002 | yes | T002, T005, T014 | |
| SC-003 | yes | T012 | text contract only |
| SC-004 | yes | T009 | |
| SC-005 | yes | T007, T014 | |
| SC-006 | partial | T012 | no fixture check (A1) |
| SC-007 | yes | T014 | |

## Constitution Alignment

- I Design First: T001 precedes every `core/` task. PASS.
- II Harness-Neutral Core: catalogue names other tools' file names as data; written justification in plan. PASS with justification (see I3 wording).
- III Generated Dist: build check in T012, T014. PASS.
- IV Stateless Agents: index in state and on disk. PASS.
- V Simplicity and Reuse: reuse of `resolve_target`, `write_run`, `commit_worktree`, sidecar pattern, `adopt._resolve`, `drop` verified present in code. PASS.
- Development Workflow "Validation plan": see D1.

## Unmapped Tasks

None. T013, T014 map to FR-026/FR-027 and SC-007.

## Metrics

- Total requirements: 28 FR + 7 SC = 35
- Total tasks: 14
- Coverage (≥1 task): 35/35 = 100% (3 partial)
- Ambiguity count: 1
- Duplication count: 0
- Critical issues: 0
- Severity counts: CRITICAL 0, HIGH 0, MEDIUM 3, LOW 7

## Next Actions

No CRITICAL or HIGH findings; implementation is not blocked. Remediate in place: C1 (T012 assertion), D1 (T001 validation-plan entry), A1 (SC-006 wording), then the LOW items. Keep `spec.md` under 3000 words. No seam or failure-path change is proposed, so the current confirmation stays valid.
