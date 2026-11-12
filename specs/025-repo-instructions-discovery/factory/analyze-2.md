# Specification Analysis Report — pass 2

Feature: `025-repo-instructions-discovery`. Loop pass after remediation 1. Artifacts: `spec.md`, `plan.md`, `tasks.md`, `research.md`, `data-model.md`, `contracts/cli.md`, `quickstart.md`; constitution `.specify/memory/constitution.md` v2.0.0; engineering rules (factory `engineering.md`). Inputs: `factory/analyze-1.md`, `factory/remediation-1.md`.

No findings at any severity. No constitution MUST violation. Test scope is fully mapped and currently confirmed.

## Pass-1 findings: verification

| ID | Pass-1 severity | Status | Evidence |
|----|-----------------|--------|----------|
| C1 | MEDIUM | Resolved | tasks.md T012 step 1 asserts "preflight, after `instructions-record`, reads every `always` entry in full at the recorded ref", alongside the grill read (FR-023 both reads covered). |
| D1 | MEDIUM | Resolved | tasks.md T001 adds a "Repo instructions validation" entry under `DESIGN.md` "Validation plan" (machine checks S1-S6; agent-driven runs: preflight record and disclosure, resume delta, `CONTRIBUTING.md`-only test command; SC-003, SC-006). `DESIGN.md` has the "Validation plan" heading (line 352). |
| A1 | MEDIUM | Resolved | spec.md SC-006 now reads "The orchestrator text records a test command documented only in a root-scope file other than `CLAUDE.md` or `AGENTS.md` as documented; the text-contract test asserts it." T012 asserts it; the fixture run lives in the T001 validation entry. |
| I1 | LOW | Resolved | spec.md edge case: "the writer at preflight records nothing new and reports it in `error`; the orchestrator discloses it", matching contracts/cli.md and research R9. |
| I2 | LOW | Resolved | plan.md Performance Goals: "three git processes per scan (`rev-parse`, `ls-tree`, `cat-file --batch`)", matching research R3 and T002 step 2. |
| I3 | LOW | Resolved | plan.md Complexity Tracking carries a Principle II row pointing at the Constitution Check II justification; the two sections now agree. |
| U1 | LOW | Resolved | tasks.md T002 step 1 asserts "no entry at or under the gitlink path" (FR-005). |
| U2 | LOW | Resolved | data-model.md `source` reason: a root catalogue agent file matched by `instructions.include` keeps `source: "catalogue"`; T006 step 1 asserts it. Consistent with FR-012 (which governs kind, not source) and FR-024 tiering. |
| C2 | LOW | Resolved | tasks.md T011 done condition: `factory init` in a sandbox writes a `config.json` with no `instructions` key (FR-014). |
| T1 | LOW | Resolved | tasks.md T014 no longer carries an "Exempt:" label; it is a verification step that changes no files. |

## New findings

None. The remediation edits were checked for knock-on inconsistencies:

- U2's source exception versus FR-012 / research R6 / T006 step 2 precedence: FR-012 and R6 decide kind and scope; the exception decides only the recorded `source` and is pinned by the T006 test. No conflict.
- D1's validation entry versus T001 exemption: the entry is `DESIGN.md` text, inside the existing `DESIGN.md` exemption; T001's done condition still limits the diff to `DESIGN.md`.
- A1's reworded SC-006 versus US5 scenario and FR-024: all three state that a test command documented only in a non-agent root-scope file counts as documented.
- ADR number: `0020` is free on `origin/main` and every remote branch (only `origin/024-windows-install` adds an ADR, `0019`). T013 still re-checks at implement time.

## Test-scope check (engineering.md "Confirmed test scope")

Declared seams S1-S6 and failure paths are unchanged by remediation 1 and match the `Confirmed:` line (2026-11-12, Q1 accepted, cruise override) exactly. Confirmation is current.

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

Every declared failure path is covered by a task. Plan-exempt tasks excluded from the check: T001, T007, T011, T013. T014 is verification only. No blocking test-scope finding.

## ENG-10 (new file / abstraction / dependency reasons)

Unchanged since pass 1: every new file (`instructions.py`, `test_instructions.py`, `.factory/config.json`), abstraction (`CATALOGUE`, glob translator), field (`instructions`, `source`) has a stated reason; dependencies: none. No ENG-10 finding.

## Word budgets

`spec.md` 2994 / 3000; `plan.md` 1252 / 2000; `tasks.md` 2392 / 2500. All within budget. `spec.md` has 6 words of headroom.

## Coverage Summary

All 28 FRs and 7 SCs map to at least one task with full coverage; the three pass-1 partials (FR-014, FR-023, SC-006) are now fully covered by T011, T012 and T012 + T001 respectively.

## Constitution Alignment

- I Design First: T001 precedes every `core/` task. PASS.
- II Harness-Neutral Core: written justification in Constitution Check, referenced from Complexity Tracking. PASS with justification.
- III Generated Dist: build check in T012, T014. PASS.
- IV Stateless Agents: PASS.
- V Simplicity and Reuse: PASS.
- Development Workflow "Validation plan": entry planned in T001. PASS.

## Unmapped Tasks

None.

## Metrics

- Total requirements: 28 FR + 7 SC = 35
- Total tasks: 14
- Coverage (≥1 task): 35/35 = 100% (0 partial)
- Ambiguity count: 0
- Duplication count: 0
- Critical issues: 0
- Severity counts: CRITICAL 0, HIGH 0, MEDIUM 0, LOW 0

## Next Actions

No findings. Implementation is not blocked; no further remediation is needed.
