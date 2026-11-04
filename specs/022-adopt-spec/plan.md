# Implementation Plan: Adopt a spec started outside factory

**Branch**: `022-adopt-spec` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: `specs/022-adopt-spec/spec.md` with settled grill Q1-Q9, clarify Q1-Q4 and grill-with-docs Q1-Q4; ADR 0017; analyze-1 findings U4, C1, C2. Chain full (escalated), fast on.

## Summary

Add one CLI writer, `factory adopt <src> [--stage <stage>] [--dry-run]`, in a new module `factory_cli/adopt.py`. One read-only inspection resolves the source shape, artifacts, dirty paths, markers, inferred stage and refusal; `--dry-run` prints it; the write selects the fixed pending run `<repo-name>-adopt-<branch>`, re-runs the inspection, creates the run in one commit and rolls back on failure. Validation gains the `adopted` event and block; `resume`'s "no run" error hints at `adopt`. The rest is prose: route and adoption grill, reviewer pre-adoption boundary (ENG-1, ENG-2, ENG-3), spec-builder in-place edits and pre-adoption tasks, approver and retro disclosure, `state.md`, `DESIGN.md`, `README.md`.

Detail: [research.md](research.md) (decisions D1-D11), [data-model.md](data-model.md), [contracts/cli.md](contracts/cli.md), [quickstart.md](quickstart.md).

## Technical Context

**Language/Version**: Python 3 (standard library only); Markdown skill and role prose.

**Primary Dependencies**: none new; `git` through the existing `commands.git` helper.

**Storage**: run `state.json` v5; optional `adopted` block and `adopted` history event; no version bump.

**Testing**: `python3 -m unittest discover -s tools` (existing runner; `tools/tests/` `Sandbox` builds throwaway git repositories with their own `FACTORY_HOME`).

**Target Platform**: macOS/Linux shells running the five harnesses.

**Project Type**: state CLI plus agent skill prose.

**Performance Goals**: none beyond today's CLI; inspection runs a bounded number of `git` calls per source.

**Constraints**: Design First (I); harness-neutral core (II); render clean, `dist/` untracked (III); state only through the CLI (ADR 0006); `factory adopt` never fetches, pulls or pushes (preflight's default-branch fetch still runs); never stages files adopt did not author (FR-014); older states valid (SC-004).

**Scale/Scope**: one repository per adoption; one pending adoption at a time.

## Constitution Check

- **I. Design First**: PASS. The first task records adoption in `DESIGN.md` (flow, state, review boundary, validation plan) before core edits.
- **II. Harness-Neutral Core**: PASS. Core prose uses `SHELL`/`ASK`; the CLI hint names its own verb.
- **III. Generated Dist**: PASS. No `render.py` change; the build renders all five harnesses; `dist/` stays untracked.
- **IV. Stateless Agents**: PASS. Adoption facts live in `state.json`; reviewers get `adopted_base` as input; the spec-builder reads `adopted` from state.
- **V. Simplicity and Reuse**: PASS. Reuses `git`, `write_state`, `lock`, `commit_worktree`, `one_run`, `find_matches`, pending-state grilling, `prune` and resume. Reasons below.

Re-check after design: PASS, no violations.

## Project Structure

```text
specs/022-adopt-spec/   plan.md, research.md, data-model.md, contracts/cli.md, quickstart.md, tasks.md
core/skills/factory/bin/factory_cli/
├── adopt.py      # NEW: inspect (dry-run report), write with rollback
├── state.py      # adopted event, ADOPT_SHAPES/ADOPT_STAGES, _check_adopted
├── commands.py   # one_run hint; cmd_resume passes it
└── cli.py        # adopt dispatch, --stage/--dry-run parsing, USAGE
core/skills/factory/SKILL.md               # argument-hint, route `adopt`, adoption grill, step 7 adopted_base, step 8 line
core/skills/factory/references/state.md    # adopted block/event, pending adoption name, CLI line
core/roles/spec-builder.md                 # FR-024 in-place specify/plan/tasks; FR-025 pre-adoption tasks in analyze
core/roles/spec-conformance.md, core/roles/code-standards.md, core/roles/review-judge.md, core/roles/retro.md
DESIGN.md, README.md
CONTEXT.md, docs/adr/0017-adopted-runs-enter-at-most-at-analyze.md   # written at grill-with-docs; edited only if the design diverges
tools/tests/test_adopt.py                  # NEW
```

**Structure Decision**: one new module beside `feedback.py`/`detect.py`; `commands.py` gains only the resume hint.

### New files, abstractions, dependencies

- `core/skills/factory/bin/factory_cli/adopt.py` - file - source resolution, inspection and the rollback-safe write are one cohesive concern with no existing home; keeps `commands.py` from growing.
- `docs/adr/0017-adopted-runs-enter-at-most-at-analyze.md` - file - records the explicit verb, entry-stage ceiling, in-place artifacts and pre-adoption boundary (already written).
- `tools/tests/test_adopt.py` - file - groups this feature's CLI seams, as `test_cruise.py` does for 021.
- `adopt.inspect(repo, src, base)` - abstraction - single source of shape, refusal and stage rules for dry-run and write (FR-003, FR-012 re-check).
- `adopted` block, `adopted` event, `ADOPT_SHAPES`, `ADOPT_STAGES` - abstraction - provenance required by FR-015/FR-016; closed vocabularies as the existing `HISTORY_EVENTS`.
- `one_run(hint=)` - abstraction - lets only `resume` add the adopt hint (FR-021) without changing other callers.
- pending name `<repo-name>-adopt-<branch>` - abstraction - the identity the write and retry select (clarify Q1, research D4).
- `adopted_base` reviewer input - abstraction - the pre-adoption boundary reviewers need (FR-019) without reading state.
- Dependencies: none.

## Design (orchestrator and role prose)

- **Route (step 0)**: `adopt <branch|spec_dir> [--stage <s>] [mode flags]` → `SHELL: factory adopt <src> [--stage <s>] --dry-run`. Non-zero: show the refusal or candidates, create nothing, stop. Clean: reuse the report's `pending` file when it exists and has not ended, else create it (ended: replace) with mode as for a new run, plus `branch`, `spec_dir`, `feature` = spec title; then preflight (step 1).
- **Adoption grill (replaces steps 2-3)**: summarise `spec.md` from the report's branch; ask only open gaps (`needs_clarification` first), the chain (recommend `full` when the entry stage is `tasks` or `analyze`) and the entry stage (inferred recommended; options `specify|plan|tasks|analyze`). Same frontier, presentation, pending storage and cruise rules as step 3. Declined: `set-status aborted`, stop. Confirmed: write `brief.md`, `checkpoint grill --next worktree`, then `SHELL: factory adopt <src> --stage <chosen>` (replaces step 4). Failure: show the error; the pending run stays for a retry. Continue from the chosen stage under "Resume".
- **Spec-builder**: `specify`/`plan`/`tasks` edit an existing artifact in place when state has `adopted` (FR-024); `analyze` excludes task IDs checked at `base_commit` from the blocking test-scope check and lists them as pre-adoption (FR-025).
- **Review (step 7)**: pass `adopted_base` when `adopted` exists. Commits in `<base>..<adopted_base>` and tasks checked at `adopted_base` are pre-adoption: code-standards skips ENG-3 for those commits; spec-conformance skips ENG-2 `Red:` checks for those commits and ENG-1 commit evidence for those tasks; the judge confirms no such finding against them. Each lists them as pre-adoption; every reviewer still reviews all of `<base>...HEAD` (FR-019, research.md D10).
- **Approver (step 8)**: "Adopted from `<shape>` `<branch>` at `<chosen_stage>` (inferred `<inferred_stage>`); commits before `<base_commit>` are pre-adoption." Retro states the same.

### Quality constraints

- Security: `<src>` and `--stage` reach git only as argv elements (no shell); `<src>` is validated with `git check-ref-format --branch` before use as a ref; spec-dir paths stay under `specs/`.
- Data integrity: every refusal re-checked at the write under the pending lock; `base_commit` read at the write; rollback removes only what adopt created; pending deleted only after the commit; one commit staging only `<spec_dir>/factory/`.
- Error handling: git failures surface their stderr; a failed step exits 1 after rollback, never a partial run.
- Compatibility: absent `adopted` reads as a factory-started run; existing tests unchanged (SC-004).
- Coverage note: SC-001's grill and SC-005's reviewer/analyze behaviour are agent prose, validated by the `DESIGN.md` validation plan after merge ([quickstart.md](quickstart.md)), as for spec 021.

## Test seams

- Seam: `bin/factory adopt <src> --dry-run` - JSON report (contracts/cli.md) per shape (`branch`, `remote-branch`, `default-branch`, renamed spec dir, local-and-remote branch resolves local), inferred stage per artifact set (`spec.md` → `plan`, `+plan.md` → `tasks`, `tasks.md` with checked boxes → `analyze`), `needs_clarification` lines, `pending` = `<repo-name>-adopt-<branch>`; the adoption's own pending file does not refuse; repo status, refs (including `refs/remotes/origin/*` when the remote moved ahead: no fetch), worktree list and files byte-identical afterwards. Failure paths: dirty spec file or dirty source-branch checkout exits 1 naming every dirty path; existing `factory/state.json` exits 1 naming `resume`; missing `spec.md` exits 1; branch checked out in the main checkout or another worktree exits 1 with the switch hint; existing worktree path exits 1 naming it; spec dir on local default branch but not on `base` exits 1 with the "push it or create its branch first" reason; another pending file of the repo exits 1 naming it with the resume/prune hint; no matching source exits 1; several matching spec dirs exit 3 listing them; `--stage implement` or an unknown value exits 5; a committed symlink or non-directory `<spec_dir>/factory` (or a symlink inside it) exits 1; no resolvable base on `origin`, including a repo with no `origin` remote, exits 1 with the named `NO_BASE` refusal; every refusal leaves the repo unchanged.
- Seam: `bin/factory adopt <src> [--stage <stage>]` (write) - per shape: worktree at `<repo>/../<repo-name>-factory/<branch>` on the existing branch (no new branch), a local branch tracking `origin/<branch>`, or a new branch from `base`; valid `state.json` with the `adopted` block (inferred and chosen stages, `base_commit` = branch HEAD at the write, including a commit made after the dry-run) and one `adopted` history entry `{stage: <chosen>, event: adopted, commit: null}`; `brief.md` and `profile.md` moved; pending files deleted; exactly one new commit `factory: adopt <branch>` touching only `<spec_dir>/factory/`; a retry after a rolled-back write reuses the same pending file and succeeds. Failure paths: a refusal arising after the dry-run (dirty file, existing state, another pending file) exits 1 with nothing written; no pending file `<repo-name>-adopt-<branch>` exits 1; an `aborted` adoption pending file exits 1; a live foreign lock exits 1; a commit rejected by a `pre-commit` hook removes the worktree and any branch adopt created, keeps the pending files, exits 1; a failing `worktree add` (for example a failing `post-checkout` hook) rolls back the same way and exits 1; a symlink created inside the checkout (factory dir, `state.json`, `brief.md`, `profile.md`) is never written through, exits 1, leaves the outside target unchanged; a rollback that leaves the worktree or branch behind exits 1 naming each leftover, pending kept; a held lock committed in the branch or a non-UTF-8 pending brief rolls back and exits 1 with a named reason, never a traceback; a pending-cleanup failure after the adoption commit exits 1 with `committed <sha>; pending cleanup failed: resume <branch>, do not retry`, keeps the worktree and commit, and does not roll back.
- Seam: `factory_cli.state.validate_state` - an adopted state with no `complete` entries before its chosen stage is valid; states without `adopted` stay valid. Failure paths: non-object `adopted`; `source.shape` off-vocabulary; missing `source.branch` or `source.spec_dir`; `inferred_stage` or `chosen_stage` outside `specify|plan|tasks|analyze`; `base_commit` not 40 lowercase hex; an `adopted` history entry without the `adopted` block.
- Seam: `bin/factory resume <run>` - a matching run resumes as before. Failure paths: no matching run exits 1 with "no run" and the `adopt <branch|spec_dir>` hint, creating no run, worktree or branch.
- Exempt: `DESIGN.md`, `README.md`, `CONTEXT.md`, `docs/adr/0017-adopted-runs-enter-at-most-at-analyze.md`, `core/skills/factory/SKILL.md`, `core/skills/factory/references/state.md`, `core/roles/spec-builder.md`, `core/roles/spec-conformance.md`, `core/roles/code-standards.md`, `core/roles/review-judge.md`, `core/roles/retro.md` - documentation only (agent prose; validated by the `DESIGN.md` validation plan).
- Overridden: none

Confirmed: 2026-11-04 - review R2-Q1 accepted (expands Q2) - seams: `bin/factory adopt <src> --dry-run`, `bin/factory adopt <src> [--stage <stage>]` (write), `factory_cli.state.validate_state`, `bin/factory resume <run>`; failure paths: each seam's "Failure paths" list exactly as declared above, verbatim snapshot in `factory/relay/plan-Q3.md` (supersedes `plan-Q2.md`).

## Complexity Tracking

None.
