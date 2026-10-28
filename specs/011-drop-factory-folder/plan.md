# Implementation Plan: Drop the factory folder at run end

**Branch**: `011-drop-factory-folder` | **Date**: 2026-10-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/011-drop-factory-folder/spec.md`

## Summary

Add one write command, `factory drop`, to the state CLI. It runs only on the `pr-open` run of the current worktree. It copies `specs/<branch>/factory/` (minus `lock.json`) into a temporary sibling under `${FACTORY_HOME}/archive/`, verifies the copy, renames it to `archive/<repo-name>-<branch>/`, then — on Pen runs — `git mv`s `factory/design/` to `docs/design/<branch>/` and rewrites `docs/design-code-map.json` references (FR-017), `git rm -r`s the rest of the folder and commits `factory: drop run artifacts`. Its JSON carries the archive path, the PR URL and the totals sentence from the final state (FR-007). SKILL.md step 9 runs `set-status pr-open`, `factory drop`, push (one retry, then `NOTIFY` the user to `git push` from the worktree), and `NOTIFY`s from the drop JSON (FR-009). Docs and `dist/` follow.

## Technical Context

**Language/Version**: Python 3 stdlib (the existing `factory_cli` package).

**Primary Dependencies**: none new. `shutil.copytree`, `filecmp`, `os.rename`, git via the existing `commands.git` helper.

**Storage**: files: run folder in the worktree; archive in `${FACTORY_HOME:-~/.factory}/archive/`.

**Testing**: `python3 -m unittest discover -s tools` (existing runner, `tools/tests/`, `Sandbox` helper).

**Target Platform**: macOS/Linux, every harness (harness-neutral core).

**Project Type**: CLI plus agent instructions.

**Performance Goals**: drop in under 5 s for a typical run folder (SC-004); a run folder is tens of small files. Verified by the manual quickstart run (step 3), not by a timing assertion.

**Constraints**: no push from the CLI (FR-008); exactly one commit touching only the folder, plus `docs/design/<branch>/` and `docs/design-code-map.json` on Pen runs (FR-006, FR-017); a refusal changes nothing (SC-003).

**Scale/Scope**: one command (~90 lines), one test module, six docs, re-rendered `dist/`.

### Quality constraints

- **Data integrity**: archive written only after a full verified copy; temp dir + `os.rename` makes the archive appear atomically. A copy or verification failure removes the temp dir, so no partial archive exists and a retry is not blocked. The final archive is never overwritten (FR-004). The map rewrite is a textual replace of the quoted prefix `"specs/<branch>/factory/design/` with `"docs/design/<branch>/`, so every other byte of the map is preserved.
- **Error handling**: every refusal exits 1 with the reason on stderr (existing `die`/`CLIError` path). Both collision checks (archive target, `docs/design/<branch>/`) run before any copy or git change. A git failure after the archive lands restores the touched paths from HEAD (`git reset -q HEAD -- <paths>`, `git checkout -q HEAD -- <folder> <map>`), removes an untracked `docs/design/<branch>/`, removes the archive and exits 1, so a retry starts clean.
- **Concurrency**: the command takes the run lock (`lock.acquire`) for the check-and-copy and refuses under a live lock (FR-001). `lock.json` is transient: it is excluded from the copy and from verification (spec FR-003/FR-005) and released before `git rm`.
- **Push failure**: the CLI never pushes; SKILL.md step 9 retries the final push once, then `NOTIFY`s the user to `git push` from the named worktree (spec Edge Cases). No resume path is claimed.
- **Security**: archive name built with the existing `improvements.backlog_name` derivation (repo dir name + branch); branch names come from the run's own state.
- **Observability**: success JSON names `dropped`, `archive`, `design` (new path or `null`), `commit`, `pr_url`, `totals_sentence` and `dropped_at` (FR-007); `totals_sentence` is `totals.sentence(totals.compute(state))` read before removal.
- **Compatibility/delivery**: existing commands, discovery and resume unchanged (FR-010); old runs keep their folders (FR-012, brief). Rollback = revert the commit; archives are inert files.

## Constitution Check

- **I. Design First**: DESIGN.md "PR" section, the "Factory home" bullet and the Pen mapping paragraph record the drop, the archive and the design evidence move in the same change, ordered first in tasks. Pass.
- **II. Harness-Neutral Core**: SKILL.md uses `SHELL: python3 <F>/bin/factory drop`; no harness names. Pass.
- **III. Generated Dist**: render all five harnesses and commit `dist/`; the gate is `test -z "$(git status --porcelain -- dist/)"` after rendering (constitution "Development Workflow"; a bare `git diff --exit-code -- dist/` misses untracked files and is not the gate). Pass.
- **IV. Stateless Agents**: no agent memory involved; the archive is on disk. Pass.
- **V. Simplicity and Reuse**: reuses `commands.git`, `resolve`-style discovery (`find_runs`/`deduped`), `lock.acquire/release`, `factory_home`, `improvements.backlog_name`, `totals.compute/sentence`. New items listed below with reasons. Pass.

Post-design re-check: unchanged, pass.

## New files, abstractions, dependencies

- `tools/tests/test_drop.py` - file - seam tests for `factory drop`; no existing module covers run-end archiving.
- `specs/011-drop-factory-folder/research.md`, `data-model.md`, `quickstart.md`, `contracts/cli.md` - file - SpecKit plan outputs.
- `commands.cmd_drop` - abstraction - the command body; one function, like every other `cmd_*`.
- `${FACTORY_HOME}/archive/` - abstraction - the run archive directory (spec "Run archive"), sibling of `pending/` and `improvements/`.
- `docs/design/<branch>/` - abstraction - permanent home of Pen design evidence after the drop (FR-017, grill-with-docs Q1); created only on Pen runs.
- Dependencies: none.

## Design

`cmd_drop(repo, cwd)` in `core/skills/factory/bin/factory_cli/commands.py`:

1. Find the run: `deduped(find_runs(repo))` worktree entries whose recorded `worktree` realpath equals `cwd`. None → `die(1, "no run to drop from <cwd>")` (covers already dropped). Status not `pr-open` → `die(1, "run is <status>; drop needs pr-open")`.
2. `lock.acquire(path, harness)`; `LockHeld` → `die(1, …)`.
3. `target = factory_home()/"archive"/<repo-name>-<branch>` via `backlog_name` without `.json`. Exists → `die(1, "archive <target> already exists; refusing to overwrite")`. When `<folder>/design/` exists and `docs/design/<branch>/` exists → `die(1, "design target <path> already exists")`.
4. Read the final state; keep `pr_url` and `totals.sentence(totals.compute(state))`.
5. `tmp = target.with_name(f".{target.name}.{pid}.tmp")`; `copytree(folder, tmp, ignore=ignore_patterns("lock.json"))`; verify with `filecmp.dircmp` recursively, ignoring `lock.json` (no left/right-only, no `diff_files`, deep compare via `filecmp.cmp(shallow=False)`). Failure → `rmtree(tmp)`, `die(1, "archive copy failed: <files>")`.
6. `os.rename(tmp, target)`; release lock.
7. Pen run only: `mkdir -p docs/design`; `git mv <folder>/design docs/design/<branch>`; textual prefix rewrite in `docs/design-code-map.json` when present; `git add` the map.
8. `git rm -r -q -- <folder>`; `git commit -q -m "factory: drop run artifacts" -- <folder> [docs/design/<branch> docs/design-code-map.json]`; `rmtree` untracked leftovers of the folder. Git failure → restore (Quality constraints), `rmtree(target)`, `die(1, …)`.
9. Return `{"dropped", "archive", "design", "commit", "pr_url", "totals_sentence", "dropped_at"}` (contracts/cli.md).

`cli.py`: `elif command == "drop"` (no positional args; `--repo` accepted like others) and one USAGE line under "write".

## Test seams

Public seams placed under test (a task may not test beyond these; a task needing another seam stops and reports it, ENG-4):

1. `factory drop` — the `bin/factory drop` command driven as a process through `Sandbox.cli`, and `factory_cli.commands.cmd_drop` in-process for injected copy/verify failures (success: archive byte-equal to the pre-drop folder minus `lock.json`, folder gone from HEAD, one commit `factory: drop run artifacts` touching only the folder, JSON with `archive`, `pr_url` and `totals_sentence`; Pen run: `factory/design/` lands at `docs/design/<branch>/` with identical content in the same commit, every map reference rewritten, other map bytes unchanged; refusals: each non-`pr-open` status, archive collision, design target collision, live lock, already dropped, failed copy/verification leaving git, the folder and `archive/` unchanged with no temp debris).

Exempt: `DESIGN.md`, `README.md`, `CONTEXT.md`, `core/skills/factory/SKILL.md`, `core/skills/factory/references/state.md`, `core/skills/factory/references/design-code-mapping.md` - agent instructions and documentation only, no executable behavior. Exempt: `core/skills/factory/bin/factory_cli/cli.py` USAGE text - documentation string; the `drop` dispatch itself is covered by seam 1. Exempt: `specs/011-drop-factory-folder/*` - specification documents. Exempt: `dist/**` - generated output, checked by the build gate.

Overridden: none

Confirmed: 2026-10-28 - Q1 accepted - seams: `factory drop`

## Project Structure

### Documentation (this feature)

```text
specs/011-drop-factory-folder/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/cli.md
└── tasks.md        # /speckit-tasks
```

### Source Code (repository root)

```text
DESIGN.md                                   # PR section, Factory home bullet, Pen mapping paragraph
README.md                                   # drop + archive location
CONTEXT.md                                  # "Run archive", "Permanent design evidence" terms
core/skills/factory/SKILL.md                # step 9 order, push retry, NOTIFY from drop JSON
core/skills/factory/references/state.md     # Location, CLI
core/skills/factory/references/design-code-mapping.md  # evidence moves to docs/design/<branch>/ at drop
core/skills/factory/bin/factory_cli/commands.py  # cmd_drop
core/skills/factory/bin/factory_cli/cli.py       # dispatch + usage
tools/tests/test_drop.py                    # seam 1
dist/<harness>/**                           # re-rendered, five harnesses
```

**Structure Decision**: existing layout; one function in `commands.py`, one test module.

## Complexity Tracking

None.
