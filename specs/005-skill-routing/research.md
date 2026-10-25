# Research: Factory skill routing

Every fact below was verified in this worktree on 2026-10-25. Line references are to the files as they
stand before this feature's changes.

## R1 - A new reference file needs no renderer change

`tools/render.py` `render()` does `shutil.copytree(ROOT/"core"/"skills"/"factory", skill)`, so every file
under `core/skills/factory/references/` lands in `dist/<harness>/skill/references/` for all five harnesses
with no renderer edit. `<F>` is substituted **only** in role bodies
(`body.replace("<F>", adapter["skill_dir"])`), so `SKILL.md` and the references keep `<F>` literal while
role agent files get the absolute installed skill directory.

**Decision**: add the shared skill-integration reference as
`core/skills/factory/references/skills.md` and address it as `<F>/references/skills.md`.
**Alternative rejected**: a top-level `docs/` note - roles cannot read repository docs at runtime; only the
rendered skill tree travels with the install.

## R2 - `brainstorm` and `requires_user` are additive to state, with no CLI change

`core/skills/factory/bin/factory` never enumerates stages or question fields:

- `cmd_runs` / `cmd_show` emit `state.get("stage")` verbatim (lines 250, 317 area), so an unknown stage
  value passes through.
- `relay_digest` copies each question dict with `{"position": position, **q}` (line 112), so an optional
  `requires_user` field reaches the orchestrator untouched.
- Backward compatibility already has explicit branches: `rounds_of` reads a version 1 single batch
  (line 95) and `relay_digest` wraps a legacy string question (line 114).

**Decision**: no change to `bin/factory` and no `version` bump (stays 3); `brainstorm` is added to the
stage vocabulary in `state.md` and `requires_user` to the question shape in `protocol.md` as optional
fields.
**Alternative rejected**: version 4 with a migration - nothing old becomes unreadable, so a bump would
force every reader to handle two versions for no gain (ENG-10, Constitution V).

## R3 - Canonical render environment

The commands recorded in `state.json` are the gate:

```sh
env -u CLAUDE_HOME -u CODEX_HOME -u COPILOT_HOME -u ZCODE_HOME -u XDG_CONFIG_HOME FACTORY_HOME=/nonexistent \
  sh -c 'for h in $(python3 tools/render.py --list); do python3 tools/render.py "$h" || exit 1; done' \
  && test -z "$(git status --porcelain -- dist/)"
```

`load_adapter` resolves `{home}` from each harness's home variable and merges
`${FACTORY_HOME}/config.json` model overrides into the frontmatter, so a render outside this wrapper
rewrites the tracked tree (specs/003, plan.md). `test -z "$(git status --porcelain -- dist/)"` is the gate
the constitution names; a bare `git diff --exit-code` cannot see untracked additions.

## R4 - The external skills, as installed, and what must be adapted

Resolved on this machine under `~/.agents/skills/<name>/SKILL.md` (the adapter's `RESOLVE` order; paths are
machine-specific and stay out of `core/`):

| Skill | Files | Facts that force an adaptation |
|---|---|---|
| `brainstorming` | `SKILL.md` | Asks one question at a time; offers a visual companion with its own consent message; step 6 writes `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` **and commits**; step 9 hands off to `writing-plans`. The factory's protocol batches the frontier, the factory owns commits, intake writes nothing to the invoking checkout, and SpecKit is the only planning chain. |
| `ponytail` | `SKILL.md` | A persona with intensities (`lite`/`full`/`ultra`, default `full`) and its own output preferences. Default intensity is kept; its output style must not replace the role envelope, and its simplification is bounded by the approved spec. |
| `tdd` | `SKILL.md`, `tests.md`, `mocking.md`, `agents/` | "Test only at pre-agreed seams ... confirm them with the user" - factory roles never talk to the user, hence the relayed seam confirmation. Defers refactoring to review, while `ENG-1` allows small behaviour-preserving refactoring while green. References its companions relatively (`tests.md`, `mocking.md`) and points at `codebase-design` through the Skill tool. |
| `impeccable` | `SKILL.md`, `reference/` (incl. `audit.md`, `audit.native.md`, `critique.md`, `craft-floor.md`), `scripts/` | Setup step 1 is `<skill-base-dir>/scripts/impeccable context`, once per session, cwd at the project. `audit` and `critique` are its Evaluate commands; `craft-floor.md` is explicitly for "immediately before any UI edit" and must not be loaded for evaluation-only work; every Refine/Enhance command edits files. |

**Decision**: the factory states these adaptations once, in `<F>/references/skills.md`, and each role links
to it instead of restating them (ENG-6, Constitution V).

## R5 - `--stop-at` keeps its current list

`SKILL.md` "Route" lists `specify` ... `pr` and already omits `grill`: there is no stop point before the
first stage, because a pause there is the same as not starting the run.

**Decision**: `brainstorm` joins the stage vocabulary (`state.stage`, resume) but **not** the `--stop-at`
list. A user who wants only exploration stops after it, which FR-005 already covers.

## R6 - UI detection lives in one place

The only UI classification today is the extension and directory list in `SKILL.md` step 6.1, read by
step 6.2 (resolve/install `impeccable`) and 6.3 (spawn `ui-reviewer`/`ux-reviewer`), and recorded as
`review.ui_diff`. Widening it to design tokens/themes, UI assets, locale and string files, and
user-visible copy inside UI code is a prose change in that one step; no other file classifies a diff.

## R7 - Where a seam confirmation can survive

`state.md` "Checkpoint" clears `relay` when a stage completes, so the confirming answer alone does not
survive the plan stage.

**Decision**: `spec-builder` records the confirmation in `plan.md`'s "Test seams" section as one
`Confirmed: <date> - <answer> - seams: <names>` line, which is committed with the plan and re-read on
resume; the confirmation is reused only when that line lists exactly the current seams, and a changed seam
list requires a new `requires_user` question.
**Alternative rejected**: a new `state.seams` object - the plan is already the seams' source of truth
(ADR 0003), and a second copy could disagree with it (ENG-6).
