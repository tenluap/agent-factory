# Implementation Plan: Assign factory PRs to the signed-in GitHub account

**Branch**: `023-pr-self-assign` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/023-pr-self-assign/spec.md`

## Summary

Step 9 (PR) of the factory skill opens the PR with `--assignee @me` and becomes idempotent: a Branch PR lookup (`gh pr list --head <branch> --state open --json url,assignees`) runs before creation and after any creation error, an existing open PR is reused, creation is retried at most once, and a failed lookup or repeated creation failure halts. After the URL is recorded, the signed-in login (`gh api user --jq .login`) is compared with the PR's assignees; a mismatch or unreadable value is an assignment problem reported as its own item in the final notice, never persisted and never blocking. state.md's Resume `pr` rule restarts step 9, so resume shares the same path. `DESIGN.md` records the behaviour first; a text-contract unittest guards it. Details: [research.md](research.md), [contracts/pr-publication.md](contracts/pr-publication.md).

## Technical Context

**Language/Version**: Markdown agent instructions (`core/`); Python 3 standard library for the test

**Primary Dependencies**: GitHub CLI `gh` (already required by step 9); no new dependency

**Storage**: none; `state.json` schema and vocabularies unchanged (FR-009)

**Testing**: `python3 -m unittest discover -s tools` (existing runner)

**Target Platform**: the five rendered harnesses (`claude-code`, `opencode`, `codex`, `copilot`, `zcode`)

**Project Type**: harness-neutral agent skill with a render tool

**Performance Goals**: at most 2 creation requests, 3 Branch PR lookups and 1 login read per publication attempt

**Constraints**: neutral verbs only in `core/` (constitution II); `dist/` untracked (III); approver gate untouched (FR-002); no `ASK` in step 9 (FR-003)

**Scale/Scope**: 3 existing files edited, 1 test file added

## Quality constraints

- **Security (ENG-25)**: `@me` and `gh api user` use the CLI's existing sign-in; nothing reads, stores or logs credentials or asks for a username.
- **Data integrity (ENG-24, ENG-26)**: no creation without a successful "none" lookup; reuse on "found"; one bounded retry; no URL recorded on halt. Duplicate PRs are the consequential effect guarded.
- **Errors and observability (ENG-17, ENG-30)**: lookup and creation errors become the halt reason verbatim; assignment problems surface in the final notice.
- **Compatibility and delivery (ENG-31)**: no state change, so existing runs resume unchanged; a run resumed at `pr` follows the new path. Rollback is reverting the three edited files.
- **Performance, concurrency, caching**: not applicable beyond the request bound above.

## Constitution Check

| Principle | Status |
|-----------|--------|
| I. Design First | Pass: `DESIGN.md` "PR" section and a validation-plan entry change in the first task, before `core/`. |
| II. Harness-Neutral Core | Pass: edits use `gh`/`git` commands already present in step 9 and the existing `SHELL`/`NOTIFY` verbs; no harness names. |
| III. Generated Dist | Pass: all five harnesses re-rendered by the build command; `dist/` stays untracked. |
| IV. Stateless Agents | Pass: the assignment problem lives in the orchestrator's single step 9 turn, like the existing skipped-retro note; resume recomputes it. |
| V. Simplicity and Reuse | Pass: reuses `set-status pr-open`, the halt policy and the push "retry once" pattern; one new file with a reason below. |

Post-design re-check: unchanged, all pass. No Complexity Tracking entries.

## Project Structure

### Documentation (this feature)

```text
specs/023-pr-self-assign/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/pr-publication.md
└── tasks.md            # next stage
```

### Source Code (repository root)

```text
DESIGN.md                                   # "PR" section + "PR self-assignment validation"
core/skills/factory/SKILL.md                # step 9 items 3, 4, 8
core/skills/factory/references/state.md     # Resume `pr` rule
tools/tests/test_pr_publication.py          # new: text-contract test
```

**Structure Decision**: edit the existing core files in place; the test joins the existing `tools/tests` package discovered by the existing runner. No adapter changes.

## New code reasons

- `tools/tests/test_pr_publication.py` - file - no existing test reads core instruction text; one module keeps the publication contract and its injected failure checks together.
- `pr_contract_gaps(skill_text, state_text)` - abstraction - one function checked against both the real core text and each mutated copy, so the injected failure paths exercise the same check the real-text test uses.
- dependency - none.

## Test seams

- Seam: `pr_contract_gaps(skill_text, state_text)` in `tools/tests/test_pr_publication.py`, applied to the real `core/skills/factory/SKILL.md` "## 9. PR" section and `core/skills/factory/references/state.md` Resume `pr` line; returns `[]` on the changed core (elements per [contracts/pr-publication.md](contracts/pr-publication.md)). Failure paths: real text with `--assignee @me` removed reports `self-assign`; Branch PR lookup command removed before `gh pr create` reports `lookup-before-create`; after-error lookup sentence removed reports `lookup-after-error`; assignment problem removed from the item 8 `NOTIFY` reports `assignment-report`; an `ASK` line inserted into step 9 reports `no-ask`; state.md `pr` rule reverted to `gh pr view <branch>` reports `resume-rule`.
- Exempt: `DESIGN.md` - documentation only (design record; validated by its validation plan and the manual runbook).
- Exempt: `specs/023-pr-self-assign/quickstart.md` manual runbook - documentation only; live GitHub behaviour is user-run (FR-013), never by agents.
- Overridden: none
