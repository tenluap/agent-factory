# Implementation Plan: Commit only what the run wrote

**Branch**: `026-commit-own-paths` | **Date**: 2026-11-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/026-commit-own-paths/spec.md`

## Summary

Every state CLI commit passes its declared paths to `git commit` as a pathspec, the way `cmd_drop` already does, so an unrelated staged change is neither committed nor unstaged (AC-1, AC-2). The change is two lines of code: `commit_worktree` in `core/skills/factory/bin/factory_cli/commands.py` and `_commit_run` in `core/skills/factory/bin/factory_cli/adopt.py`. The code-writing roles gain an explicit-path staging sentence (AC-3). code-build's Work step 1 claims only paths the resumed task names (AC-4). The approver step lists `git status --porcelain` paths under a fixed heading (AC-5). `DESIGN.md` records all three behaviours first (constitution principle I). Research: [research.md](research.md). Validation: [quickstart.md](quickstart.md).

## Technical Context

**Language/Version**: Python 3 (standard library only) for `factory_cli`; Markdown for roles, skill and `DESIGN.md`.

**Primary Dependencies**: git CLI (already used through `commands.git`). No new dependency.

**Storage**: git index and commits in the run worktree; `state.json` unchanged.

**Testing**: `python3 -m unittest discover -s tools` (existing runner, `tools/tests`).

**Target Platform**: macOS/Linux shells running the five rendered harnesses.

**Project Type**: CLI plus harness-neutral agent instructions rendered by `tools/render.py`.

**Performance Goals**: none beyond today; one `git commit` per writer call, unchanged.

**Constraints**: no new CLI surface, field, logging, ADR, CONTEXT.md term or README change (brief, "Declined scope"). `core/` stays harness-neutral (principle II). `dist/` stays untracked (principle III).

**Scale/Scope**: 2 code call sites, 3 role files, 1 skill step, 1 design doc, 2 extended test files, 1 new test file.

### Quality constraints

- **Data integrity (ENG-26)**: a factory commit contains only declared paths; an unrelated staged change keeps its index state. `git commit -q -m <msg> -- <paths>` (git's default `--only` mode) commits those paths from the working tree and leaves every other index entry as it was. This is the mechanism `cmd_drop` already relies on.
- **Errors (ENG-17)**: git failures keep surfacing through `commands.git` (`die(2, stderr)`); checkpoint keeps its existing `commit_error` report. No new error path.
- **No declared paths** (open point from specify): `commit_worktree` returns `None` without calling `git commit` when it has no declared path (no `spec_dir` and empty `extra`), as it already does when `worktree` is empty. FR-001 forbids any factory commit without a pathspec, and this is the narrowest behaviour that honours it: no new error, exit code or field. Today every caller passes `spec_dir`, so the branch guards malformed state only.
- **Security, performance, observability, delivery**: not affected; no new input, I/O or output.
- **Compatibility**: commit messages, declared paths and command output are unchanged. Writers whose declared paths hold no change behave as before: git reports nothing to commit and `commands.git` exits 2.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Design First | Pass | `DESIGN.md` is edited first: "Declared-file checkpoints" bullet (writer and adopt pathspec, role explicit-path staging) and "Approver" section (uncommitted-paths listing). Task order puts the `DESIGN.md` task before core edits. |
| II. Harness-Neutral Core | Pass | Role and skill edits use plain git commands inside `SHELL`-style steps that already exist; no harness tool, path or command is named. |
| III. Generated Dist | Pass | No `dist/` edit; build command re-renders all five harnesses and checks `dist/` is untracked. |
| IV. Stateless Agents | Pass | AC-4 rule reads the resumed task from `tasks.md` on disk; no memory of an earlier turn. |
| V. Simplicity and Reuse | Pass | Reuses `cmd_drop`'s pathspec pattern and `commit_worktree`; one new test file, reason below; no new field, verb or reference. |
| Writing Standards | Pass | Each prose addition is one imperative sentence or short item. |

Post-design re-check: Pass, no violations; Complexity Tracking is empty.

## Change list

1. `DESIGN.md` (AC-1, AC-3, AC-5): in the "Declared-file checkpoints" bullet, state that every writer command and `adopt` commit with exactly their declared pathspec (as `drop` does) and that an unrelated staged change stays staged; add that code-build, design-to-code and fixer stage by explicit path, and that code-build claims uncommitted work only for paths its resumed task names. In "Approver", add the "📂 Uncommitted local changes the run didn't make" list, shown only when non-empty, never committed or discarded.
2. `core/skills/factory/bin/factory_cli/commands.py` `commit_worktree` (AC-1, AC-2): return `None` when the declared list is empty; otherwise `git add -- <paths>` then `git commit -q -m <message> -- <paths>`. Update the docstring.
3. `core/skills/factory/bin/factory_cli/adopt.py` `_commit_run` (AC-1, AC-2): `git commit -q -m "factory: adopt <branch>" -- <spec_dir>/factory`.
4. `core/roles/code-build.md` (AC-3, AC-4): rewrite Work step 1 only: an uncommitted change is interrupted work only when the task being resumed names its path; finish or discard only those paths; leave every other uncommitted change untouched (no stage, commit, stash or discard). Add one sentence at the commit item of step 3: stage by explicit path (`git add -- <path>...`), never `git add -A`, `git add .` or `git commit -a`.
5. `core/roles/design-to-code.md` (AC-3): same staging sentence in step 4's commit-unit text.
6. `core/roles/fixer.md` (AC-3): same staging sentence in step 5.
7. `core/skills/factory/SKILL.md` step 8 (AC-5): one item: run `git status --porcelain` in the worktree; list every reported path under "📂 Uncommitted local changes the run didn't make" when it reports any; the run neither commits nor discards them.
8. Core reference lines: `references/state.md` lines 203 and 210 already describe "commits its spec directory" and "touching only `<spec_dir>/factory/`"; they do not contradict the change and stay unchanged.

Not planned: the `factory: start` commit, the AC-4 rule for design-to-code and fixer, any `engineering.md` rule, any CLI or `show` field, ADR, CONTEXT.md or README change, and the 7 tests already failing on base 0c3bf71 (`test_render_models`, `test_skill_library`).

## New files, abstractions, dependencies

- `tools/tests/test_commit_scope.py` - file - AC-3, AC-4, AC-5 - text-contract tests for the three prose rules; no existing test file reads role files, and `test_pr_publication.py` is scoped to SKILL.md step 9.
- Abstractions: none.
- Dependencies: none.

## Test seams

Declared public seams and their required injected failure paths:

- `factory checkpoint` (`commands.cmd_checkpoint`), in `tools/tests/test_commands.py` (AC-2): injected failure path `unrelated-staged-deletion` - `pnpm-lock.yaml` committed on the base, then `git rm --cached`/`git rm` staged before checkpoint; assert the checkpoint commit does not touch `pnpm-lock.yaml` (`git show --name-only HEAD`) and `git diff --cached --name-status` still shows `D pnpm-lock.yaml`.
- `factory resume` (`commands.cmd_resume`, worktree source), in `tools/tests/test_commands.py` (AC-2): injected failure path `unrelated-staged-deletion`, same assertions on the `factory: resume <name>` commit.
- `factory adopt` write (`adopt` without `--dry-run`, through `_commit_run`), in `tools/tests/test_adopt.py` (AC-2): injected failure path `unrelated-staged-deletion` staged in the adopted worktree before the commit step, same assertions on the `factory: adopt <branch>` commit.
- `commands.commit_worktree`, in `tools/tests/test_commands.py` (AC-1): injected failure path `no-declared-paths` - `spec_dir=None`, `extra=()` with a staged change; assert it returns `None`, HEAD is unchanged and the change is still staged.
- Prose contract `commit_scope_gaps` in `tools/tests/test_commit_scope.py` (AC-3, AC-4, AC-5), reading `core/roles/code-build.md`, `core/roles/design-to-code.md`, `core/roles/fixer.md` and `core/skills/factory/SKILL.md` step 8: injected failure path `marker-removed` - each mutated copy with one required marker removed (explicit-path staging, each forbidden bulk form, the resume path-match rule, the leave-untouched rule, `git status --porcelain`, the exact heading, the no-commit/no-discard rule) reports exactly that gap, as run 023's `test_pr_publication.py` does.

The other writer commands (rebind, models-record, profile-record, analyze-record, ledger-add, issue-add, wait-open, wait-close, answer, set-status, decisions-add, verify) are covered through `commit_worktree`; no per-command test (brief Q2).

Exempt: `DESIGN.md` - documentation only; behaviour it describes is tested through the seams above.

Overridden: none

Confirmed: 2026-11-12 - Q1 accepted (cruise override) - seams: factory checkpoint, factory resume (worktree), factory adopt (_commit_run), commands.commit_worktree, commit_scope_gaps; failure paths: checkpoint -> unrelated-staged-deletion; resume -> unrelated-staged-deletion; adopt -> unrelated-staged-deletion; commit_worktree -> no-declared-paths; commit_scope_gaps -> marker-removed

## Project Structure

### Documentation (this feature)

```text
specs/026-commit-own-paths/
├── plan.md
├── research.md
├── quickstart.md
└── tasks.md        # next stage
```

No `data-model.md` (no entity or state change) and no `contracts/` (no new or changed command interface; command output is unchanged).

### Source Code (repository root)

```text
DESIGN.md
core/skills/factory/SKILL.md
core/skills/factory/bin/factory_cli/commands.py
core/skills/factory/bin/factory_cli/adopt.py
core/roles/code-build.md
core/roles/design-to-code.md
core/roles/fixer.md
tools/tests/test_commands.py
tools/tests/test_adopt.py
tools/tests/test_commit_scope.py   # new
```

**Structure Decision**: existing layout; code under `core/skills/factory/bin/factory_cli/`, tests under `tools/tests/`.

## Complexity Tracking

None.
