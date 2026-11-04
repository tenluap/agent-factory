---
description: "Task list for 023-pr-self-assign"
---

# Tasks: Assign factory PRs to the signed-in GitHub account

**Input**: `specs/023-pr-self-assign/` (spec.md, plan.md, research.md, data-model.md, contracts/pr-publication.md, quickstart.md)

**Tests**: Required (engineering.md). Each behaviour-changing task is one commit unit: failing test (red proof), implementation, passing check, committed together. Runner: `python3 -m unittest discover -s tools` (existing). Seam and failure paths: plan.md "Test seams" (scope confirmed: Q1 accepted (cruise override) 2026-11-04). All tests go in `tools/tests/test_pr_publication.py` (new file, reason in plan.md), which reads the real core files from `REPO = Path(__file__).resolve().parents[2]` as `tools/tests/test_skill_library.py` does. Element rules and their order are fixed by `contracts/pr-publication.md` "Text-contract elements"; each unit adds its elements to `pr_contract_gaps(skill_text, state_text)` in that order. "Section" = SKILL.md text from `## 9. PR` up to the next `## ` heading.

Every injected failure path is a mutated copy of the real core text that must make `pr_contract_gaps` return exactly `[<that element>]` (not a superset), so mutations remove only the element's marker.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallel-safe (different files, no dependency)
- **[Story]**: US1-US3 from spec.md

## Phase 1: Setup

- [x] T001 Update `DESIGN.md` "### PR" (Decisions) and add "### PR self-assignment validation" under "## Validation plan". PR section: `gh pr create ... --assignee @me` (single request, no `gh pr edit`, no username ever asked, approver gate unchanged); Branch PR lookup `gh pr list --head <branch> --state open --json url,assignees` before creation and after any creation error, with outcomes found (reuse, record via `set-status pr-open`), none (create; after an error retry creation once), failed (halt with the lookup error, never create); a second creation error with a final lookup still finding none halts with the creation error and records no URL; only open PRs are reused; assignment check with `gh api user --jq .login` against the Branch PR's assignees, a mismatch or unreadable value being an assignment problem reported as its own item in the final notice, non-blocking and never persisted (no state field, issue kind or history event); resume of `pr` restarts step 9 through the same lookup-then-create path. Validation entry: the text-contract test plus the user-run manual runbook in `specs/023-pr-self-assign/quickstart.md` (SC-001..SC-003; agents never create GitHub repositories). Exempt: `DESIGN.md` - documentation only (constitution I: lands before the `core/` edits). Done: every item above named in `DESIGN.md`; the validation entry names the runbook and SC-001..SC-003.

## Phase 2: Foundational

None: the test module is created by the first commit unit (T002), and no shared infrastructure is needed.

## Phase 3: User Story 1 - New PR is assigned to the person who opened it (P1) - MVP

**Goal**: step 9's single creation request self-assigns; no question asks for a username.
**Independent test**: `python3 -m unittest tools.tests.test_pr_publication -v` passes for `self-assign` and `no-ask`; their injected copies fail with exactly that element.

- [x] T002 [US1] Create `tools/tests/test_pr_publication.py` with `pr_contract_gaps(skill_text, state_text)` covering `self-assign` and `no-ask`, and add `--assignee @me` to step 9 item 3 in `core/skills/factory/SKILL.md`.
  - Seam: `pr_contract_gaps(skill_text, state_text)`. Failure paths: `self-assign` (real text with `--assignee @me` removed from the section's `gh pr create` line); `no-ask` (real text with an `ASK: ...` line inserted into the section).
  - Red: write tests first: real `core/skills/factory/SKILL.md` and `core/skills/factory/references/state.md` give `[]`; the `self-assign` copy gives `["self-assign"]`; the `no-ask` copy gives `["no-ask"]`. Implement `pr_contract_gaps` with the two contract rules (`self-assign`: a section line contains `gh pr create` and `--assignee @me`; `no-ask`: no whole-word `\bASK\b` regular-expression match in the section; markers are case-sensitive literals). Run; the real-text test fails with `["self-assign"]`. Commit body: `Red: tools.tests.test_pr_publication.PrPublicationContractTests.test_real_core_text_has_no_gaps failed as expected`.
  - Implement: step 9 item 3 becomes `gh pr create --base <default-branch> --head <branch> --title "<title>" --body-file <file> --assignee @me`, ready for review. No `gh pr edit`, no `ASK`, no username prompt (FR-001, FR-003). Approver gate text untouched (FR-002).
  - Pass: `python3 -m unittest discover -s tools` green; build command renders all five harnesses and `bash -n install.sh` passes.
  - Done: the three tests pass; `git grep -n -- '--assignee @me' core/skills/factory/SKILL.md` prints the item 3 line.

## Phase 4: User Story 2 - Retry or resume never opens a duplicate PR (P1)

**Goal**: lookup-then-create in step 9; resume of `pr` follows the same path.
**Independent test**: the `lookup-before-create`, `lookup-after-error` and `resume-rule` tests pass, and their injected copies fail with exactly that element.

- [x] T003 [US2] Add `lookup-before-create` and `lookup-after-error` to `pr_contract_gaps` in `tools/tests/test_pr_publication.py`, and rewrite step 9 item 3 of `core/skills/factory/SKILL.md` as lookup-then-create (depends on T002).
  - Seam: `pr_contract_gaps(skill_text, state_text)`. Failure paths: `lookup-before-create` (real text with the Branch PR lookup command removed before the first `gh pr create`); `lookup-after-error` (real text with the after-error Branch PR lookup sentence removed).
  - Red: tests first: the real-text test (now also asserting these two rules: the section contains `gh pr list --head <branch> --state open --json url,assignees` before its first `gh pr create`; one section line contains all four literals `gh pr create`, `error`, `Branch PR lookup` and `retry`); each injected copy gives exactly its element. Run; the real-text test fails with `["lookup-before-create", "lookup-after-error"]`. Commit body: `Red: tools.tests.test_pr_publication.PrPublicationContractTests.test_real_core_text_has_no_gaps failed as expected`.
  - Implement: item 3 per `contracts/pr-publication.md` sub-steps 1-3. (1) Branch PR lookup `gh pr list --head <branch> --state open --json url,assignees`: exit 0 with entries = found, reuse the first entry's `url` and skip creation; exit 0 with `[]` = none; non-zero = failed, halt through the existing Halt policy (`set-status halted --halt-reason "<lookup error>"`), never create (FR-004, FR-007). (2) None: the T002 `gh pr create ... --assignee @me`. (3) After a `gh pr create` error, repeat the Branch PR lookup before any retry (this one line carries `gh pr create`, `error`, `Branch PR lookup` and `retry`): found = reuse; failed = halt with the lookup error; none = retry creation once; after a second error and a lookup still finding none, halt with the creation error. No URL recorded on any halt (FR-005, FR-006). Only open PRs are reused. Keep the lookup command and the phrase "Branch PR lookup" on separate lines so each mutation removes one marker only. Item numbers 1-8 unchanged.
  - Pass: runner green; build command green.
  - Done: all tests pass; at most 2 creation requests and 3 Branch PR lookups per attempt are stated in item 3.

- [ ] T004 [US2] Add `resume-rule` to `pr_contract_gaps` in `tools/tests/test_pr_publication.py`, and replace the Resume `pr` line in `core/skills/factory/references/state.md` (depends on T003).
  - Seam: `pr_contract_gaps(skill_text, state_text)`. Failure paths: `resume-rule` (real state text with the `pr` line reverted to `- \`pr\`: check \`gh pr view <branch>\` first; an existing PR only needs its URL recorded.`).
  - Red: tests first: the real-text test also asserts the rule (the state.md Resume line whose stripped text starts `` - `pr`: `` contains `step 9` and `Branch PR lookup` and not `gh pr view`); the injected copy gives `["resume-rule"]`. Run; the real-text test fails with `["resume-rule"]` (current line uses `gh pr view <branch>`). Commit body: `Red: tools.tests.test_pr_publication.PrPublicationContractTests.test_real_core_text_has_no_gaps failed as expected`.
  - Implement: state.md line ``- `pr`:`` becomes: restart SKILL.md step 9 from item 1; its Branch PR lookup reuses an existing open PR, so resume never opens a duplicate (FR-010). `git push -u` of an already-pushed branch is a no-op (research R5). Leave the existing manual recovery for interruptions after `set-status pr-open` unchanged.
  - Pass: runner green; build command green.
  - Done: all tests pass; `git grep -n 'gh pr view' core/` prints nothing.

## Phase 5: User Story 3 - A failed assignment is visible but does not block publication (P2)

**Goal**: assignment check after the PR is known; assignment problem reported separately in the final notice, never persisted.
**Independent test**: the `assignment-report` test passes, and its injected copy fails with exactly `["assignment-report"]`.

- [ ] T005 [US3] Add `assignment-report` to `pr_contract_gaps` in `tools/tests/test_pr_publication.py`, and edit step 9 items 3, 4 and 8 of `core/skills/factory/SKILL.md` (depends on T004).
  - Seam: `pr_contract_gaps(skill_text, state_text)`. Failure paths: `assignment-report` (real text with `assignment problem` removed from the item 8 `NOTIFY` line).
  - Red: tests first: the real-text test also asserts the rule (the item 8 line, matched by `^\s*8\.\s`, contains `NOTIFY` and `assignment problem`); the injected copy gives `["assignment-report"]`. Run; the real-text test fails with `["assignment-report"]`. Commit body: `Red: tools.tests.test_pr_publication.PrPublicationContractTests.test_real_core_text_has_no_gaps failed as expected`.
  - Implement: item 3 sub-step 4: after a successful creation, repeat the Branch PR lookup once to read its assignees; found supplies them, and any other outcome (none or failed) keeps the URL `gh pr create` printed and counts as an assignment problem. This lookup never creates, retries or halts (FR-004 to FR-010). Item 4: `SHELL: python3 <F>/bin/factory set-status pr-open --pr-url <url>`, then read the signed-in login with `gh api user --jq .login`; when it is not among the Branch PR's `assignees[].login`, or either read failed, note an assignment problem for item 8; continue, never halt, never `ASK`, never issue a separate assignment request (FR-008). Item 8 (also fix its stray leading space): `NOTIFY` names any assignment problem as its own item, separate from `pr_url`. No state field, issue kind or history event (FR-009); nothing reads or logs credentials (ENG-25).
  - Pass: runner green; build command green.
  - Done: all six elements asserted; real text gives `[]`; each injected copy gives exactly its element.

## Phase 6: Polish and verification

- [ ] T006 Reconcile `specs/023-pr-self-assign/quickstart.md` with the final core text (commands, step 9 item references, SC-001..SC-003 checks, cleanup step) and run its "Automated checks" block: `python3 -m unittest tools.tests.test_pr_publication -v`, `python3 -m unittest discover -s tools`, the five-harness render plus `bash -n install.sh`, and `test -z "$(git ls-files -- dist/)"`. Exempt: `specs/023-pr-self-assign/quickstart.md` manual runbook - documentation only (live GitHub check is user-run, FR-013; agents never run it or create repositories). Done: all automated checks pass; the runbook names exactly the commands now in step 9 and state.md.

## Dependencies

- T001 first (constitution I).
- T002 -> T003 -> T004 -> T005: all extend the same test module and SKILL.md step 9 in sequence.
- T006 after T005.
- US1 is the MVP; US2 depends on US1's creation command; US3 depends on US2's Branch PR lookup.

## Parallel execution

None safe: every unit edits `tools/tests/test_pr_publication.py` and `core/skills/factory/SKILL.md` or depends on the previous unit's text. T001 and T006 touch only documentation but bracket the sequence by design.

## Implementation strategy

MVP = T001 + T002 (self-assigned PRs). T003-T004 make publication idempotent, T005 surfaces assignment problems, T006 verifies. `dist/` is never committed; adapters are unchanged.
