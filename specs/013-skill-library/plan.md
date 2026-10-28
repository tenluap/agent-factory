# Implementation Plan: Factory Skill Library

**Branch**: `013-skill-library` | **Date**: 2026-10-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/013-skill-library/spec.md`

## Summary

Ship a two-layer skill library: committed `skills/` (six vendored factory-required skills plus `SOURCES.md`) and per-user `${FACTORY_HOME}/skills/`. Each adapter declares a `skills_root` relative to its harness home (Codex/Copilot fixed at `~/.agents/skills`); `render.py --paths` reports it; `install.sh` prunes stale library links, links every library skill (per-user wins; dot-folders and reserved `factory` excluded) into each selected root, skips non-library paths, adds local skills with `--add-skill`, and removes only library links on `--uninstall`, keeping both layers. Nothing is rendered into `dist/` (ADR 0009); preflight `RESOLVE` is unchanged. Terms: `CONTEXT.md` "Skill library". Details: [research.md](research.md).

## Technical Context

**Language/Version**: Bash (`install.sh`), Python 3 stdlib (`tools/render.py`, tests)

**Primary Dependencies**: none new

**Storage**: filesystem (two layer directories, symlinks in harness skills roots)

**Testing**: `python3 -m unittest discover -s tools`; installer tests run `install.sh` in a throwaway `HOME`

**Target Platform**: macOS and Linux shells with symlink support

**Project Type**: CLI installer plus rendered agent distribution

**Performance Goals**: N/A (a handful of folders per install)

**Constraints**: never delete or overwrite non-library paths; no network in the installer; `dist/` unchanged by library content; idempotent re-runs

**Scale/Scope**: 6 vendored skills, 5 adapters, user-added skills unbounded but small

## Constitution Check

| Principle | Status |
|---|---|
| I. Design First | Pass: `DESIGN.md` gains a "Skill library" section before `install.sh`/adapter changes (task order). |
| II. Harness-Neutral Core | Pass: no `core/` change; roots live in `adapters/*/adapter.json`. |
| III. Generated Dist | Pass: adapter edits are followed by a render of all five harnesses; `skills_root` does not reach rendered files, so `dist/` stays unchanged; the porcelain gate `test -z "$(git status --porcelain -- dist/)"` runs after every re-render (SC-004). |
| IV. Stateless Agents | N/A: no agent or state change. |
| V. Simplicity and Reuse | Pass: extends `install.sh` and the `--paths` report; every new file/field has a reason below. |

Post-design re-check: pass, no violations.

## Quality constraints

- **Security (ENG-25)**: `--add-skill` accepts a local directory only; URLs refused; name `factory` refused; skill content is never executed; all paths quoted.
- **Data integrity (ENG-26)**: validation before any write; per-user layer created (`mkdir -p`) only after validation; copy to a dot-prefixed temp folder then `mv`, temp removed on failure; dot-folders never linked; non-library targets skipped with `skip:`; stale-link pruning and uninstall touch only symlinks whose target is inside a library layer; uninstall keeps both layers.
- **Errors (ENG-17)**: refusals print `error:`, `exists:` or `reserved: factory` naming the problem and exit 2; no tracebacks.
- **Licensing**: LICENSE copied verbatim from the upstream repository only; a skill without an obtainable upstream LICENSE is not vendored.
- **Compatibility (ENG-31)**: existing install, uninstall and models report behave as before; `readlink` without `-f`.
- **Dependencies (ENG-27)**: none; frontmatter parsed with inline stdlib Python like the `config.json` check.
- **Provenance**: `skills/SOURCES.md` records URL, path, commit and license per skill.
- **Observability/delivery**: `linked:`/`skip:`/`removed:`/`added:` lines; an unchanged link prints `linked:` again on re-run; existing CI (suite, re-render, porcelain, `bash -n install.sh`) covers the change.

## Test seams

- `render.py <harness> --paths` reports `skills_root` — each adapter prints the FR-004 root, home-expanded; with `CLAUDE_HOME`, `ZCODE_HOME`, `XDG_CONFIG_HOME` set the root follows the override; with `CODEX_HOME`/`COPILOT_HOME` set Codex and Copilot stay on `~/.agents/skills` (tests in `tools/tests/test_render_models.py`).
- `install.sh` library linking — every repo-layer skill linked into the selected root; idempotent re-run printing `linked:` again; per-user precedence; per-user folder dropped by hand gets linked; dot-prefixed folders never linked; a `factory` folder in either layer skipped with `skip:` and the factory skill link untouched; stale library link removed with `removed:` and relinked to the repo copy when one exists; non-library directory, outside symlink and dangling outside symlink skipped and untouched; shared Codex/Copilot root linked once with `--harness all` (`tools/tests/test_skill_library.py`).
- `install.sh --add-skill <path>` — valid copy plus links; per-user layer created when absent; name taken from the given path's basename (outside symlink adoption works); refusals for missing path, URL, missing `SKILL.md`, missing frontmatter, name mismatch, `reserved: factory`, existing destination, each writing nothing; failed copy leaves no temp folder (`tools/tests/test_skill_library.py`).
- `install.sh --uninstall` library links — removes only links into either layer, including links Copilot shares with Codex; non-library paths and both layer folders with their contents survive (`tools/tests/test_skill_library.py`).
- Repo skill layer layout — each `skills/<name>/` for the six required names has `SKILL.md` whose frontmatter `name` matches the folder, a `LICENSE`, and a `SOURCES.md` row with URL, path, commit and license (`tools/tests/test_skill_library.py`).

Exempt: README.md, DESIGN.md, CONTEXT.md, docs/adr/0009-library-skills-are-linked-not-rendered.md - documentation only
Exempt: skills/<name>/ vendored content - verbatim third-party documentation; structure covered by the repo skill layer layout seam
Exempt: adapters/*/adapter.json `skills_root` values - configuration; reported values covered by the `--paths` seam
Overridden: none
Confirmed: 2026-10-28 - Q1 accepted - seams: render.py --paths skills_root, install.sh library linking, install.sh --add-skill, install.sh --uninstall library links, repo skill layer layout

## New files, abstractions and dependencies

- `skills/{grilling,domain-modeling,pr,ponytail,tdd,brainstorming}/` - file - repo layer of vendored required skills (FR-001)
- `skills/SOURCES.md` - file - per-skill provenance record (FR-002)
- `tools/tests/test_skill_library.py` - file - library seam tests, kept apart from the existing installer tests; reuses `InstallSandbox` from `test_install.py`
- `skills_root` adapter key - abstraction - per-harness skills root required by FR-004; `dirname(skill_dir)` is wrong for Copilot
- `skills_root=` line in `render.py --paths` - abstraction - hands the expanded root to `install.sh` through its existing `eval`
- `link_skill`, `install_skills`, `unlink_skills`, `add_skill` functions in `install.sh` - abstraction - library-link ownership rule differs from `link`/`unlink_ours` (outside symlinks must be skipped; ADR 0009); `install_skills` also prunes stale library links, `unlink_skills` is shared with uninstall
- `CONTEXT.md` "Skill library" section, `docs/adr/0009-library-skills-are-linked-not-rendered.md` - file - settled terms and the link-not-render decision (written by grill-with-docs)
- dependency - none

## Project Structure

### Documentation (this feature)

```text
specs/013-skill-library/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/install-cli.md
└── tasks.md            # next stage
```

### Source Code (repository root)

```text
skills/                     # new repo layer
├── SOURCES.md
└── <six skills>/ (SKILL.md, LICENSE, upstream files)
adapters/<harness>/adapter.json   # + skills_root
tools/render.py             # load_adapter expands skills_root; --paths prints it
install.sh                  # library link/add/uninstall
tools/tests/test_skill_library.py # new
tools/tests/test_render_models.py # + skills_root paths test
README.md, DESIGN.md        # library documentation
```

**Structure Decision**: Single repository; changes confined to installer, adapters, renderer path report, new `skills/` layer, tests and docs.

## Implementation notes

1. `DESIGN.md` "Skill library" section first: layers, precedence, ownership rule, reserved `factory`, stale-link pruning, `--add-skill`, uninstall (layers kept, shared Codex/Copilot root), manual refresh (FR-014); cite ADR 0009.
2. Adapters: add `skills_root` (research R2). `render.py`: expand it in `load_adapter`, print in `print_paths`. Re-render five harnesses; run the porcelain gate.
3. `install.sh`: parse `--add-skill <path>`; reject with `--uninstall`. In `install_one`, after factory links, call `install_skills "$skills_root"` (prune stale, then link); in uninstall branch call `unlink_skills "$skills_root"`. `add_skill` runs once before the harness loop. Contract: [contracts/install-cli.md](contracts/install-cli.md).
4. Vendor six skills per research R6 (upstream clone only); write `SOURCES.md`.
5. README: library section (layers, `--add-skill`, reserved name, conflicts, shared-root uninstall, refresh) and the install table note.

## Complexity Tracking

No violations.
