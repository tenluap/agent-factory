# Implementation Plan: Adopt a spec started outside factory

**Branch**: `022-adopt-spec` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/022-adopt-spec/spec.md`; settled grill decisions Q1-Q9 in `factory/brief.md` (lite chain, fast on).

## Summary

Add one CLI writer, `factory adopt <src> [--stage <stage>] [--dry-run]`, in a new module `factory_cli/adopt.py`. One read-only inspection resolves the source shape, artifacts, dirty paths, markers, inferred stage and refusal; `--dry-run` prints it, the write re-runs it, creates the run and rolls back on failure. Validation gains the `adopted` event and block; `resume`'s "no run" error hints at `adopt`. The rest is prose: route and confirmation grill, reviewer ENG-2 boundary, approver and retro disclosure, `state.md`, `DESIGN.md`, `CONTEXT.md`, ADR 0017.

## Technical Context

**Language/Version**: Python 3 (standard library only), Markdown skill prose.

**Primary Dependencies**: none new; `git` via the existing `commands.git` helper.

**Storage**: run `state.json` v5; additive optional `adopted` block and `adopted` history event; no version bump.

**Testing**: `python3 -m unittest discover -s tools` (existing runner; `tools/tests/` `Sandbox` builds throwaway git repos with their own `FACTORY_HOME`).

**Target Platform**: macOS/Linux shells running the five harnesses.

**Project Type**: state CLI plus agent skill prose.

**Constraints**: Design First (constitution I); harness-neutral core (II); render clean, `dist/` untracked (III); state through the CLI (ADR 0006); never fetch, pull or push; never stage files adopt did not author (FR-014); older states valid (SC-004).

## Decisions (research)

- **Ordering**: `/factory adopt <src>` runs `factory adopt <src> --dry-run` first, before any pending file exists, so a refusal creates nothing anywhere. Only a clean report proceeds to pending creation, preflight and the confirmation grill. Rejected: dry-run after preflight (an aborted pending file per refused source).
- **Source resolution** (one function, shared by dry-run and write), first match wins:
  1. `<src>` names a local branch → shape `branch`.
  2. else `refs/remotes/origin/<src>` exists → shape `remote-branch`.
  3. else `<src>` (with or without `specs/`) names a spec dir: a local branch named after it → shape `branch`; else the dir exists on `base` → shape `default-branch`, branch = dir name.
  Spec dir on a branch: `specs/<branch>/` when present on the branch ref, else the single `specs/*/` directory the branch adds over `base` (`git diff --name-only <base>...<ref> -- specs/`). Several candidates (spec dirs, or a spec-dir name matching several dirs by the `NNN-` suffix rule `find_matches` uses) → exit 3 listing them; none → exit 1. A branch present locally and on `origin` resolves to the local branch.
- **Reading**: artifacts and markers come from the source ref (`git ls-tree`, `git show <ref>:<path>`), never a working tree.
- **Default branch and base**: the write uses the pending run's `default_branch` and `base` (preflight, as for a new run). The dry-run, run before preflight, uses `refs/remotes/origin/HEAD` (else `main`, `base` = `origin/main` when it exists, else `main`) and prints the `base` it used; the write's re-inspection is authoritative.
- **Dirty paths**: `git status --porcelain` of the main checkout limited to the spec dir, plus the full status of any checkout that has the source branch checked out. Dirty paths are reported even when another refusal also applies.
- **Refusal order** (first named in `refusal`, every dirty path listed): no match / ambiguous; dirty paths; spec dir has `factory/state.json` (names `resume <branch>`); no `spec.md`; branch checked out in a checkout (names it, hint to switch away; `branch` shape only); worktree path exists.
- **Entry stage**: `tasks.md` → `analyze`; else `plan.md` → `tasks`; else `plan`. `--stage` accepts `specify|plan|tasks|analyze`, anything else exits 5 before any read or write (`cli.py`).
- **Write steps** (holding the pending run's lock throughout, `lock.acquire` on the pending path; a live foreign lock exits 1):
  1. Resolve the single pending run (`resolve_target` from the repo); its `branch` and `spec_dir` must equal the inspected source, else exit 1.
  2. Re-run the inspection with pending `base`; any refusal exits 1, nothing written.
  3. `git worktree add <path> <branch>` (`branch`), `git worktree add --track -b <branch> <path> origin/<branch>` (`remote-branch`), or `git worktree add -b <branch> <path> <base>` (`default-branch`).
  4. Write `<worktree>/<spec_dir>/factory/state.json` from the pending state through `state.write_state`: `worktree`, `stage` = chosen stage, `status: running`, `adopted` block, one `adopted` history entry; copy `<pending>.brief.md` → `brief.md` and the pending `profile.md`.
  5. Commit through `commit_worktree(worktree, "factory: adopt <branch>", spec_dir=<spec_dir>/factory)`, staging only that folder.
  6. Only after the commit succeeds, delete the pending file, its brief and profile.
  Any failure in 3-5: `git worktree remove --force <path>`, `git branch -D <branch>` only when step 3 created it, pending untouched, exit 1 with the git error.
- **Pending reuse**: the orchestrator creates the adoption's pending file with `branch` and `spec_dir` from the report; before creating one it looks for an unfinished pending run with the same `branch` in `factory runs` and resumes that instead.
- **Declined adoption**: `set-status aborted` on the pending run, as a declined new run; nothing reached the repo. The existing `prune` cleans it.
- **Resume hint**: `one_run` gains an optional `hint` appended to its "no run" message; only `cmd_resume` passes `use adopt <branch|spec_dir> for a spec factory did not start`. The CLI names its own verb, the skill names the harness invocation (constitution II).
- **ENG-2 boundary**: SKILL.md step 7 passes `adopted_base` (= `adopted.base_commit`) to `spec-conformance` and `review-judge` when present. Spec-conformance checks `Red:` lines on `<adopted_base>..HEAD` only and lists `<base>..<adopted_base>` commits as pre-adoption; the judge never confirms an ENG-2 finding against a pre-adoption commit. All reviewers still review `<base>...HEAD`.
- **Disclosure**: `show`'s digest already passes small fields verbatim, so `adopted` reaches approver and retro unchanged; retro states adoption in its summary.

## Data model

`adopted` (optional, written only by `factory adopt`):

```json
"adopted": {
  "source": { "shape": "branch", "branch": "007-x", "spec_dir": "specs/007-x" },
  "inferred_stage": "tasks",
  "chosen_stage": "plan",
  "base_commit": "<40-hex sha of the branch HEAD at the write>"
}
```

Validation (`state.py`, `_check_adopted`): object; `source.shape` in `ADOPT_SHAPES = ("branch", "remote-branch", "default-branch")`; `source.branch` and `source.spec_dir` non-empty strings; both stages in `ADOPT_STAGES = ("specify", "plan", "tasks", "analyze")`; `base_commit` a 40-character lowercase hex string. `HISTORY_EVENTS` gains `adopted`; an `adopted` history entry requires the `adopted` block. No rule requires `complete` entries before the chosen stage (FR-017 is held by test).

## CLI contract

- `factory adopt <src> --dry-run`: prints `{source, shape, branch, spec_dir, base, artifacts, dirty, inferred_stage, needs_clarification, worktree, refusal}`; exit 0 clean, 1 refused (report still printed), 3 ambiguous, 5 usage. Writes nothing.
- `factory adopt <src> [--stage <stage>]`: prints the resume digest of the new run (as `resume` does); exit 0, 1 refused or failed (rolled back), 3 ambiguous, 5 usage.

## Constitution Check

- **I. Design First**: PASS. Task 1 records adoption in `DESIGN.md` (flow, state, review, validation plan) before core edits.
- **II. Harness-Neutral Core**: PASS. Core prose uses `SHELL`/`ASK`; the CLI hint names its own verb.
- **III. Generated Dist**: PASS. No `render.py` change; build renders all five harnesses; `dist/` stays untracked.
- **IV. Stateless Agents**: PASS. Adoption facts live in `state.json`; reviewers get `adopted_base` as input.
- **V. Simplicity and Reuse**: PASS. Reuses `git`, `write_state`, `lock`, `resolve_target`, `commit_worktree`, `one_run`, the pending-state grill and resume. Reasons below.

Re-check after design: PASS, no violations.

## Project Structure

```text
core/skills/factory/bin/factory_cli/
├── adopt.py      # NEW: inspect (dry-run report), adopt write with rollback
├── state.py      # adopted event, ADOPT_SHAPES/ADOPT_STAGES, _check_adopted
├── commands.py   # one_run hint; cmd_resume passes it
└── cli.py        # adopt dispatch, --stage/--dry-run parsing, USAGE
core/skills/factory/SKILL.md                    # argument-hint, route `adopt`, adoption grill, step 7 adopted_base, step 8 line
core/skills/factory/references/state.md         # adopted block/event, CLI line, location
core/roles/spec-conformance.md, core/roles/review-judge.md, core/roles/retro.md
DESIGN.md, README.md, CONTEXT.md (term **Adopted run**)
docs/adr/0017-adopted-runs-enter-at-most-at-analyze.md   # NEW
tools/tests/test_adopt.py                                # NEW
```

**Structure Decision**: one new module beside `feedback.py`/`detect.py`; `commands.py` only gains the resume hint.

### New files, abstractions, dependencies

- `core/skills/factory/bin/factory_cli/adopt.py` - file - source resolution, inspection and the rollback-safe write are one cohesive concern with no existing home; keeps `commands.py` from growing.
- `docs/adr/0017-adopted-runs-enter-at-most-at-analyze.md` - file - records the entry-stage ceiling and the ENG-2 pre-adoption boundary (Q5, Q8, Q9).
- `tools/tests/test_adopt.py` - file - groups this feature's CLI seams, as `test_cruise.py` does for 021.
- `adopt.inspect(repo, src, base)` - abstraction - single source of shape, refusal and stage rules for dry-run and write (FR-003, FR-012 re-check).
- `adopted` block, `adopted` event, `ADOPT_SHAPES`, `ADOPT_STAGES`, `one_run(hint=)`, `adopted_base` reviewer input - abstraction - additive fields and parameters; reasons under "Decisions".
- Dependencies: none.

## Design (orchestrator prose)

- **Route (step 0)**: `adopt <branch|spec_dir> [--stage <s>] [mode flags]` → `SHELL: factory adopt <src> [--stage <s>] --dry-run`. Non-zero: show the refusal (or candidates), create nothing, stop. Clean: reuse or create the pending file (mode as for a new run, plus `branch`, `spec_dir`, `feature` = spec title), then preflight (step 1).
- **Adoption grill (replaces steps 2-3)**: summarise `spec.md` from the report's branch, ask only open gaps (`needs_clarification` first), the chain, and the entry stage (inferred stage recommended; options `specify|plan|tasks|analyze`). Same frontier, presentation, pending storage and cruise rules as step 3. Declined: `set-status aborted`, stop. Confirmed: write `brief.md`, `checkpoint grill --next worktree`, then `SHELL: factory adopt <src> --stage <chosen>` (replaces step 4). Failure: show the error; the pending run stays for a retry. Continue from the chosen stage under "Resume".
- **Review (step 7)**: pass `adopted_base` when `adopted` exists.
- **Approver (step 8)**: "Adopted from `<shape>` `<branch>` at `<chosen_stage>` (inferred `<inferred_stage>`); commits before `<base_commit>` are pre-adoption."

### Quality constraints

- Security: `<src>` and `--stage` reach git only as argv list elements (`subprocess` without a shell); refs are validated with `git check-ref-format --branch` before use.
- Data integrity: every refusal re-checked at the write; rollback removes only what adopt created; pending deleted last; one commit staging only `<spec_dir>/factory/`.
- Compatibility: absent `adopted` reads as a factory-started run; existing tests unchanged (SC-004).

## Test seams

- Seam: `bin/factory adopt <src> --dry-run` - JSON report per shape (`branch`, `remote-branch`, `default-branch`, renamed spec dir, local-and-remote branch resolves local), inferred stage per artifact set (`spec.md` → `plan`, `+plan.md` → `tasks`, `tasks.md` with checked boxes → `analyze`), `needs_clarification` lines; repo status, refs, worktree list and files byte-identical afterwards. Failure paths: dirty spec file or dirty source-branch checkout exits 1 naming every dirty path; existing `factory/state.json` exits 1 naming `resume`; missing `spec.md` exits 1; branch checked out in the main checkout or another worktree exits 1 with the switch hint; existing worktree path exits 1 naming it; no matching source exits 1; several matching spec dirs exit 3 listing them; `--stage implement` or an unknown value exits 5; every refusal leaves the repo unchanged.
- Seam: `bin/factory adopt <src> [--stage <stage>]` (write) - per shape: worktree at `<repo>/../<repo-name>-factory/<branch>` on the existing branch (no new branch), a local branch tracking `origin/<branch>`, or a new branch from `base`; valid `state.json` with `adopted` block (inferred and chosen stages, `base_commit` = branch HEAD) and one `adopted` history entry; `brief.md` and `profile.md` moved; pending files deleted; exactly one new commit `factory: adopt <branch>` touching only `<spec_dir>/factory/`. Failure paths: a refusal arising after the dry-run (dirty file, existing state) exits 1 with nothing written; no pending run, or a pending run whose `branch` differs, exits 1; a live foreign lock exits 1; a commit rejected by a `pre-commit` hook removes the worktree and any branch adopt created, keeps the pending files, exits 1.
- Seam: `factory_cli.state.validate_state` - an adopted state with no `complete` entries before its chosen stage is valid; states without `adopted` stay valid. Failure paths: non-object `adopted`; `source.shape` off-vocabulary; missing `source.branch` or `source.spec_dir`; `inferred_stage` or `chosen_stage` outside `specify|plan|tasks|analyze`; `base_commit` not 40 lowercase hex; an `adopted` history entry without the `adopted` block.
- Seam: `bin/factory resume <run>` - a matching run resumes as before. Failure paths: no matching run exits 1 with "no run" and the `adopt <branch|spec_dir>` hint, creating no run, worktree or branch.
- Exempt: `DESIGN.md`, `README.md`, `CONTEXT.md`, `docs/adr/0017-adopted-runs-enter-at-most-at-analyze.md`, `core/skills/factory/SKILL.md`, `references/state.md`, `core/roles/spec-conformance.md`, `core/roles/review-judge.md`, `core/roles/retro.md` - documentation only (agent prose; validated by the `DESIGN.md` validation plan).
- Overridden: none

Confirmed: 2026-11-04 - Q1 accepted - seams: `adopt --dry-run`, `adopt` write, `validate_state`, `resume`; failure paths: each seam -> every failure path declared above, unchanged. Accepted scope snapshot: `specs/022-adopt-spec/factory/relay/plan-Q1.md`.

## Complexity Tracking

None.
