# Specification Analysis Report: 022-adopt-spec (analyze pass 2, after escalation to the full chain)

Artifacts: `spec.md` (2985 words, budget 3000), `plan.md` (1497, budget 2000), `tasks.md` (2499, budget 2500), plus research.md D1-D11, data-model.md, contracts/cli.md, quickstart.md; constitution 2.0.0. All artifacts are within their word budgets, but `spec.md` and `tasks.md` are each within 15 words of the limit, so any remediation edit to them must be word-neutral. Extension hooks skipped (the factory owns hooks and commits). Analyze-1 findings U1, I1, U2, U3, T1, U4, C1 and C2 are resolved in the re-derived artifacts: the fixed pending name and sole-pending rule, the scoped no-fetch statement, the local-only default-branch refusal, FR-024 in-place edits, the "no run" wording, the `adopted` entry shape, the moved-branch test and the after-merge validation note.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| U1 | Underspecification | MEDIUM | spec.md FR-019, SC-005, US5; plan.md "Design" (Review), Project Structure; tasks.md T013; core/roles/code-standards.md:14; core/roles/spec-conformance.md:30; references/findings.md:41 | The pre-adoption boundary covers only ENG-2, but reviewers also enforce ENG-1/ENG-3 against commits. `code-standards` checks commit units ("separately completed red half or duplicated completed unit"). `spec-conformance` checks that each checked task has "one passing test-and-implementation commit". findings.md keeps ENG-1..ENG-5 blocking. For US5's own scenario (an adopted branch with checked tasks and pre-adoption commits), these checks can produce blocking findings that cannot be fixed without rewriting published commits. That is the outcome ADR 0017 rejects ("blockers no one can fix without rewriting published commits"). T013 changes only the `Red:` check, and `code-standards.md` is not among the edited role files. | Needs a user decision because it widens settled grill Q9 ("ENG-2 only after `adopted.base_commit`"): should commits before `adopted.base_commit` and pre-adoption tasks also be outside the commit-unit (ENG-3) and test-first commit-evidence (ENG-1) checks, while the code itself is still reviewed? If yes, update FR-019/SC-005, plan "Design" (Review) and D10, add `core/roles/code-standards.md` to T013 and to the plan's Exempt line, and widen T013's spec-conformance edit to the commit-unit verification. This is prose only, so the seam and failure-path scope is unchanged. Defer to clarify. |
| C1 | Coverage | MEDIUM | plan.md "Quality constraints" (Security); research.md D2; contracts/cli.md; tasks.md T003 Implement, T004 | The plan's security constraint validates `<src>` with `git check-ref-format --branch`, and T003 implements that check. No artifact says what a `<src>` that fails the check produces (exit code and message), and no Red step tests it. As planned, this untrusted-input validation branch would ship untested (ENG-1, ENG-25). | Say in D2 and contracts/cli.md that a `<src>` failing `check-ref-format` (for example `../x` or `a..b`) is reported as no match (exit 1, nothing read or written). Add one case to T004's existing "no matching source exits 1" Red step. That maps onto an already-declared failure path of the dry-run seam, so the confirmed Q2 scope is unchanged. |
| I1 | Inconsistency | LOW | tasks.md T004 Red ("committed `specs/007-x/factory/state.json` names `resume 007-x`, with dirty paths still listed"); research.md D5 | D5 puts dirty paths before the existing-state refusal, and the first reason found is the one named in `refusal`. If T004's state.json fixture is also dirty, `refusal` names the dirty cause rather than `resume`, so the stated assertion would fail. If the fixture is clean, "dirty paths still listed" asserts nothing. | Make the fixture clean and assert `refusal` names `resume 007-x` with `dirty: []`. Alternatively assert that the dirty cause wins and both dirty paths are listed. Keep the edit word-neutral (tasks.md is at 2499 of 2500 words). |
| I2 | Inconsistency | LOW | spec.md FR-016 ("source (branch and/or spec dir, and shape)"), Key Entities "Adoption source"; data-model.md; plan.md validate_state failure paths | The spec says the source holds the branch "and/or" the spec dir. The data model and the confirmed failure paths require both `source.branch` and `source.spec_dir`, and every shape resolves both (default-branch: branch = dir name). | In spec.md FR-016 and Key Entities, replace "branch and/or spec dir" with "branch and spec dir". |
| I3 | Inconsistency | LOW | spec.md FR-021, US6-1, Clarifications grill Q1; contracts/cli.md `resume`; research.md D9; tasks.md T009 | The spec requires the resume error to hint at `/factory adopt <branch\|spec_dir>`. The CLI deliberately prints `use adopt <branch\|spec_dir> ...` (D9, constitution II), and T009 asserts the CLI text. Read literally, FR-021 is unmet by design. | Reword FR-021 and US6-1: the CLI hint names `adopt <branch\|spec_dir>`, and the skill shows the harness invocation. |
| U2 | Underspecification | LOW | research.md D2 step 3 and "Several candidates"; tasks.md T004 (`007-x` and `008-x` dirs, `adopt x` exits 3), T005 Implement | The `find_matches` `-<name>` suffix rule applies when `<src>` names a spec dir. The set of candidate dirs it matches against is never stated: local branch names, `specs/*` on `base`, or `specs/*` on the local default branch. T004's fixture does not say where `007-x` and `008-x` live. | State the candidate set in D2, for example spec dirs on local branches named after them plus `specs/*/` on `base` and on local `<default>`. Name the fixture refs in T004. |

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 | Yes | T010 | prose (exempt) |
| FR-002 | Yes | T003, T006 | |
| FR-003 | Yes | T003, T004, T005 | |
| FR-004 | Yes | T003, T005, T008 | see U2 |
| FR-005 | Yes | T006, T008 | |
| FR-006 | Yes | T003, T006 | |
| FR-007 | Yes | T004, T005, T006 | see C1, I1 |
| FR-008 | Yes | T003 | |
| FR-009 | Yes | T003, T006 | |
| FR-010 | Yes | T007, T010 | retry tested in T007; grill prose |
| FR-011 | Yes | T010 | prose (exempt) |
| FR-012 | Yes | T006 | |
| FR-013 | Yes | T007, T008 | |
| FR-014 | Yes | T006 | |
| FR-015 | Yes | T002, T006 | |
| FR-016 | Yes | T002, T006 | see I2 |
| FR-017 | Yes | T002 | |
| FR-018 | Yes | T006, T010 | |
| FR-019 | Yes | T010, T013 | see U1 |
| FR-020 | Yes | T010, T013 | |
| FR-021 | Yes | T009 | see I3 |
| FR-022 | Yes | T006 | |
| FR-023 | Yes | T001, T010-T014 | |
| FR-024 | Yes | T012 | prose (exempt) |
| FR-025 | Yes | T012 | prose (exempt) |
| SC-001 | Partial | T003-T009, T001 | grill flow validated after merge (quickstart.md) |
| SC-002 | Yes | T003-T005 | |
| SC-003 | Yes | T006, T008 | |
| SC-004 | Yes | T002, T009, T015 | |
| SC-005 | Partial | T012, T013 | prose; see U1 |
| SC-006 | Yes | T014 | |

## Test-scope and commit-unit check (factory override)

- Behaviour-changing tasks T002-T009 each have a mapped seam, ordered Red, Implement and Pass steps, red proof and a Done condition. Every failure path these tasks require is declared in plan.md "Test seams". Every declared failure path is required by at least one task:
  - dry-run: T003 (exit 5), T004 (dirty, state, spec.md, checkout, worktree path, other pending, no match, exit 3), T005 (local-only default dir);
  - write: T006 (post-dry-run refusals, no pending, aborted, live lock), T007 and T008 (`pre-commit` rollback);
  - `validate_state`: T002 (all paths);
  - `resume`: T009.
- Confirmation: `Confirmed: 2026-11-04 - Q2 accepted` names all four seams and references the snapshot `factory/relay/plan-Q2.md`. The snapshot is byte-identical to the current "Test seams" section (lines 93-98). `state.json` records `Q2-test-scope` and plan `Q2` as explicit answers (`auto: false`), superseding `Q1-test-scope`. The confirmation is current and complete. C1's recommended fix stays inside the declared "no matching source exits 1" path, and U1's fix is prose only, so neither invalidates it.
- Plan-exempt tasks T001 and T010-T013 are excluded from this check. T014 and T015 are verification only and change no behaviour.
- ENG-10: `adopt.py`, ADR 0017 and `test_adopt.py` (files), `inspect`, the `adopted` block, event and vocabularies, `one_run(hint=)`, the pending name and `adopted_base` (abstractions), and dependencies (`none`) each carry a reason. No finding.
- The plan has `Overridden: none`. The repository has a runner, so no `Test runner:` line is needed.
- Pre-adoption tasks: not applicable (this run is not adopted).

## Constitution Alignment Issues

None.
- I (Design First): T001 lands first, and the dependencies keep it first.
- II (Harness-Neutral Core): SKILL.md prose uses `SHELL` and `ASK`, and the CLI hint names its own verb.
- III (Generated Dist): T014 builds all five harnesses, checks that `dist/` is untracked, and confirms `render.py` and `install.sh` are unchanged.
- IV (Stateless Agents): adoption facts live in `state.json`, and `adopted_base` is passed as reviewer input.
- V (Simplicity and Reuse): reuse is stated, and every new file, field and verb has a reason.

## Unmapped Tasks

None. T014 and T015 verify FR-023, SC-004 and SC-006.

## Metrics

- Total requirements: 31 (25 FR, 6 SC)
- Total tasks: 15
- Coverage: 100% (31/31 with at least one task; SC-001 and SC-005 are partly prose, validated after merge)
- Ambiguity count: 1 (U2)
- Duplication count: 0
- Critical issues: 0
- Severity counts: CRITICAL 0, HIGH 0, MEDIUM 2, LOW 4

## Next Actions

- No blocking findings. Implementation may proceed after remediation.
- U1 needs a user decision (extending the settled Q9 boundary to ENG-1 and ENG-3 commit evidence): remediation should defer it to clarify as a `pending_clarify` question.
- C1, I1, I2, I3 and U2 are in-place wording and test-case edits within the confirmed scope. Keep `spec.md` and `tasks.md` within budget by trimming as much text as each edit adds.
