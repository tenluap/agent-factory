# Specification Analysis Report: 023-pr-self-assign (pass 2)

Artifacts: `spec.md` (2321 words), `plan.md` (831), `tasks.md` (1717), plus `research.md`, `data-model.md`, `contracts/pr-publication.md`, `quickstart.md`. Constitution: `.specify/memory/constitution.md` v2.0.0. Checked against the current core text (`core/skills/factory/SKILL.md` "## 9. PR", `core/skills/factory/references/state.md` line 216) and `tools/tests/`, after remediation 1 (`factory/remediation-1.md`).

## Pass 1 findings

All seven are resolved in the artifacts:

- U1: contract item 3 sub-step 4, data-model.md "Lookup outcome" and T005 Implement now say the post-creation lookup uses assignees only on "found". Any other outcome keeps the `gh pr create` URL and counts as an assignment problem; it never creates, retries or halts. The table's actions are limited to sub-steps 1 and 3.
- A1: `lookup-after-error` is now one section line containing the four literals, in both the contract and T003 Red.
- I1: research.md R6, plan.md "New code reasons" and spec.md Assumptions now describe `test_render_models.py` correctly.
- U2: `no-ask` is defined as a whole-word `\bASK\b` match.
- U3: `assignment-report` is anchored to the item 8 line `^\s*8\.\s`.
- G1: quickstart.md step 5 states the coverage limit and adds an optional user-run after-error check.
- I2: spec.md Clarifications Q2 records the switch to the `gh pr list` lookup.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| I3 | Inconsistency | MEDIUM | contracts/pr-publication.md:15 (Item 4: "never halt, never `ASK`"); tasks.md T005 Implement ("continue, never halt, never `ASK`, never issue a separate assignment request"); contracts/pr-publication.md:31 and T002 Red (`no-ask` = no whole-word `\bASK\b` match in the section) | Remediation U2 made `no-ask` precise. It now conflicts with the item 4 wording that T005 tells the implementer to write. If item 4 carries "never `ASK`" as the contract and T005 phrase it, the real step 9 section matches `\bASK\b`, and `pr_contract_gaps` returns `["no-ask"]` on the changed core. That breaks T005's Pass and Done conditions ("real text gives `[]`"). The test would catch it, but the artifacts give the implementer two instructions that cannot both hold. | Reword contract item 4 and T005 Implement so the core text states the rule without the token `ASK`, for example "continue; never halt and never ask the user". Alternatively, add a note in T005 that this guidance is not core text and item 4 must not contain the literal `ASK`. Keep the `no-ask` rule unchanged. |

No CRITICAL or HIGH findings. No LOW findings.

## Test-scope check (engineering.md "Confirmed test scope")

- Declared seam: `pr_contract_gaps(skill_text, state_text)` in `tools/tests/test_pr_publication.py`. Failure paths: `self-assign`, `lookup-before-create`, `lookup-after-error`, `assignment-report`, `no-ask`, `resume-rule`. Remediation 1 did not change the plan's "Test seams" declarations. U2 and U3 tightened only how each element is matched. The injected mutations stay as declared: `--assignee @me` removed, lookup command removed, after-error sentence removed, `assignment problem` removed from the item 8 `NOTIFY`, `ASK` line inserted, `pr` rule reverted.
- Confirmation: plan.md `Confirmed: 2026-11-04 - Q1 accepted (cruise override)` is backed by the `state.decisions` plan Q1 record (`cruise_override: true`). The accepted scope still matches the complete declaration, so the acceptance is current.
- T002 to T005: each maps to the declared seam. Each has ordered Red, Implement and Pass steps, red-proof commit wording, an observable Done condition and only declared failure paths. The Red expectations still hold against the current core text:
  - T002 fails with `["self-assign"]` because the section has no `ASK` today.
  - T003 fails with the two lookup elements.
  - T004 fails with `["resume-rule"]` because line 216 still uses `gh pr view <branch>`, and `git grep 'gh pr view' core/` finds only that line.
  - T005 fails with `["assignment-report"]`.
- T001 (`DESIGN.md`) and T006 (`quickstart.md`) are plan-exempt and excluded from this check.
- ENG-10: the new file and abstraction keep stated reasons (the file reason has been corrected), and dependency is `none`. No ENG-10 finding.
- Word budgets: spec.md 2321/3000, plan.md 831/2000, tasks.md 1717/2500. All within budget.

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 single creation request with `--assignee @me` | Yes | T002 | `self-assign` |
| FR-002 approver gate unchanged | Yes | T002 (constraint) | Preservation |
| FR-003 no username question | Yes | T002, T005 | `no-ask` (see I3) |
| FR-004 lookup before create, reuse | Yes | T003 | `lookup-before-create` |
| FR-005 lookup after creation error | Yes | T003 | `lookup-after-error` |
| FR-006 one retry, then halt | Yes | T003 | Optional live check in quickstart step 5 |
| FR-007 failed lookup halts | Yes | T003 | |
| FR-008 assignment check, non-blocking report | Yes | T005 | Sub-step 4 outcomes now specified |
| FR-009 no state field / issue kind / event | Yes | T005 (constraint) | |
| FR-010 resume same path | Yes | T004 | `resume-rule` |
| FR-011 DESIGN.md + neutral core + five renders | Yes | T001-T006 | |
| FR-012 automated text-contract test | Yes | T002-T005 | |
| FR-013 manual runbook | Yes | T006 | quickstart steps 1-6 |
| SC-001 to SC-005 | Yes | T002-T006 | Same mapping as pass 1 |

## Constitution Alignment

No violations. The pass 1 assessment of principles I to V is unchanged: remediation edited only spec artifacts, and no core, dist or constitution files.

## Unmapped Tasks

None.

## Metrics

- Total requirements: 18 (13 FR, 5 SC)
- Total tasks: 6
- Coverage: 100% (18/18)
- Ambiguity count: 0
- Underspecification count: 0
- Inconsistency count: 1 (I3)
- Duplication count: 0
- Critical issues: 0
- Severity counts: CRITICAL 0, HIGH 0, MEDIUM 1, LOW 0

## Next Actions

There are no blocking findings. Remediation edits in place for I3: reword contract item 4 and T005 Implement so the item 4 core text never contains the literal `ASK`.
