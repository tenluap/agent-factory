# Specification Analysis Report: 023-pr-self-assign (pass 1)

Artifacts: `spec.md` (2284 words), `plan.md` (813), `tasks.md` (1678), plus `research.md`, `data-model.md`, `contracts/pr-publication.md`, `quickstart.md`. Constitution: `.specify/memory/constitution.md` v2.0.0. Checked against the current core text (`core/skills/factory/SKILL.md` "## 9. PR", `core/skills/factory/references/state.md` Resume `pr` at line 216) and `tools/tests/`.

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| U1 | Underspecification | MEDIUM | contracts/pr-publication.md:11; data-model.md:20; tasks.md T005 Implement | Item 3 sub-step 4 (lookup after a successful creation, to read assignees) defines only the `failed` outcome. The `none` outcome (exit 0, `[]`) is unspecified, and data-model.md's Lookup outcome table maps `none` to "create". Read literally, it would open a second PR right after creating one, which is the duplicate FR-004 to FR-010 exist to prevent (ENG-24, ENG-26). | In the contract, data-model.md and T005, state that in sub-step 4 any outcome other than "found" keeps the URL `gh pr create` printed and counts as an assignment problem. It never creates. Limit the table's "create" action to sub-steps 1 and 3. |
| A1 | Ambiguity | MEDIUM | contracts/pr-publication.md:24; tasks.md T003 Red (line 45) | The `lookup-after-error` rule reads "a section line contains `gh pr create` error wording (`error`) and `Branch PR lookup` and `retry`". It does not say whether the literal `gh pr create` is a required marker on the same line. This rule is FR-012's only automated guard for FR-005, so the test author has to guess which markers to check. | Restate the rule as literal markers on one section line, e.g. contains `gh pr create`, `error`, `Branch PR lookup` and `retry`. Use the same wording in the contract and T003. |
| I1 | Inconsistency | MEDIUM | research.md:35 (R6); plan.md:78 (New code reasons); spec.md:124 (Assumptions) | research.md R6 and the plan's reason for the new file say "no existing test reads core instruction text". That is false: `tools/tests/test_render_models.py` reads `core/roles/design-to-code.md` and `core/roles/facets-advisor.md` as text contracts (around lines 615, 636 and 689). spec.md Assumptions says the opposite ("matching how other core instruction changes are tested"). The new file's stated reason rests on a wrong premise. | Correct R6 and the plan reason. For example: the existing core-text checks in `test_render_models.py` cover harness neutrality of role files, and the publication contract is a separate concept with its own injected-failure fixtures, so it gets its own module. |
| U2 | Underspecification | LOW | contracts/pr-publication.md:26; tasks.md T002 Red | The `no-ask` rule says "the section contains no `ASK` verb" but does not define the match: substring, whole word, backticked `` `ASK` `` or `ASK:`. A plain substring check would also match uppercase words that contain `ASK`. | Define it as a whole-word `\bASK\b` match within the section. |
| U3 | Underspecification | LOW | contracts/pr-publication.md:25; research.md R4 | The `assignment-report` rule accepts any numbered section line that contains both `NOTIFY` and `assignment problem`. It is not tied to item 8. R4 suggests the phrase "noted in-turn for item 8's `NOTIFY`". If item 4 copies that phrase, the rule passes even when item 8 loses the report. T005's exact-element mutation test would catch this during implementation, but only at that point. | Anchor the rule to the item 8 line (`^\s*8\.\s`), or have T005 tell the item 4 wording to avoid `NOTIFY`. |
| G1 | Coverage Gap | LOW | quickstart.md:24 (runbook step 3); spec.md US2 scenarios 2-3, SC-002 | The manual runbook simulates "interrupted publication" with `--stop-at pr` plus a PR opened by hand. That exercises lookup-before-create on resume. It never exercises the after-error path (FR-005/FR-006: creation reports an error after GitHub created the PR). Only the text contract covers that path. | Acceptable given that agents never run outward-facing checks. State in quickstart.md that the after-error path is covered only by the text contract. Optionally add a user-run step that forces a `gh pr create` error (e.g. an invalid `--assignee`) and confirms reuse. |
| I2 | Inconsistency | LOW | factory/brief.md:12 (settled Q2); research.md:14 (R2) | The settled Q2 answer names `gh pr view <branch> --json url,assignees`. Plan, contract and tasks use `gh pr list --head <branch> --state open --json url,assignees` instead. R2 justifies the change (FR-007 three-way outcome; open PRs only), and spec.md's Clarifications are command-neutral, so the intent is kept. The swap is recorded only in research.md. | Add a short note to spec.md Clarifications Q2 (or Assumptions) that the lookup command follows research R2. |

No CRITICAL or HIGH findings.

## Test-scope check (engineering.md "Confirmed test scope")

- Declared seam: `pr_contract_gaps(skill_text, state_text)` in `tools/tests/test_pr_publication.py`. Failure paths: `self-assign`, `lookup-before-create`, `lookup-after-error`, `assignment-report`, `no-ask`, `resume-rule`.
- Confirmation: plan.md `Confirmed: 2026-11-04 - Q1 accepted (cruise override)`, backed by the `state.decisions` plan Q1 record (`cruise_override: true`). The accepted scope matches the declaration exactly. The acceptance is current.
- T002 to T005: each maps to the declared seam. Each has ordered Red, Implement and Pass steps, red proof wording that matches engineering.md's first form, and an observable Done condition. Each failure path a task requires is declared in the plan. No task needs an unlisted seam.
- T001 (`DESIGN.md`) and T006 (`quickstart.md` runbook): both covered by plan exemptions, so excluded from this check.
- ENG-10: the new file and the new abstraction each have a stated reason, and dependency is `none`. No ENG-10 finding. I1 covers the factual error in the file's reason.
- Word budgets: spec.md 2284/3000, plan.md 813/2000, tasks.md 1678/2500. All within budget.

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 single creation request with `--assignee @me` | Yes | T002 | `self-assign` element |
| FR-002 approver gate unchanged | Yes | T002 (constraint) | Preservation; approver text untouched |
| FR-003 no username question | Yes | T002 | `no-ask` element |
| FR-004 lookup before create, reuse open PR | Yes | T003 | `lookup-before-create` element |
| FR-005 lookup after creation error | Yes | T003 | `lookup-after-error` (see A1) |
| FR-006 one retry, then halt | Yes | T003 | Text only; see G1 |
| FR-007 failed lookup halts, never creates | Yes | T003 | |
| FR-008 assignment check, non-blocking report | Yes | T005 | `assignment-report` (see U1, U3) |
| FR-009 no state field / issue kind / event | Yes | T005 (constraint) | Preservation |
| FR-010 resume follows the same path | Yes | T004 | `resume-rule` element |
| FR-011 DESIGN.md + neutral core + five renders | Yes | T001, T002-T006 | Build command in every Pass step |
| FR-012 automated text-contract test | Yes | T002-T005 | Six elements |
| FR-013 manual runbook | Yes | T006 | quickstart.md exists; G1 |
| SC-001 assignee 100% (runbook) | Yes | T006 | Runbook step 2 |
| SC-002 exactly 1 PR on resume (runbook) | Yes | T006 | Runbook step 3 |
| SC-003 assignment problem reported (runbook) | Yes | T005, T006 | Runbook step 4 |
| SC-004 zero username questions | Yes | T002, T006 | |
| SC-005 test fails on removal; renders pass | Yes | T002-T006 | |

## Constitution Alignment

No violations:
- **I. Design First**: T001 updates `DESIGN.md` "### PR" and the Validation plan before any `core/` edit.
- **II. Harness-Neutral Core**: the change uses `gh`/`git` commands already present in step 9 and the existing verbs.
- **III. Generated Dist**: no `dist/` is committed, and T006 checks `git ls-files -- dist/`.
- **IV. Stateless Agents**: the assignment problem lives only in the orchestrator's step 9 turn, and resume recomputes it.
- **V. Simplicity and Reuse**: the change reuses `set-status pr-open`, the halt policy and the existing retry-once pattern.

## Unmapped Tasks

None. T001 and T006 map to FR-011 and FR-013.

## Metrics

- Total requirements: 18 (13 FR, 5 SC)
- Total tasks: 6
- Coverage: 100% (18/18 have at least one task)
- Ambiguity count: 1 (A1)
- Underspecification count: 3 (U1, U2, U3)
- Duplication count: 0
- Critical issues: 0
- Severity counts: CRITICAL 0, HIGH 0, MEDIUM 3, LOW 4

## Next Actions

There are no blocking findings. Remediate edits in place:
- U1: specify how sub-step 4 handles a lookup result other than "found" in contracts/pr-publication.md, data-model.md and T005.
- A1, U2, U3: tighten the element rules in contracts/pr-publication.md and the matching Red steps in T002, T003 and T005.
- I1: correct research.md R6 and the plan's new-file reason.
- G1, I2: add notes to quickstart.md and spec.md.
