# Implementation Plan: Factory Skill Library

**Branch**: `013-skill-library` | **Date**: 2026-10-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/013-skill-library/spec.md`

## Summary

Ship a two-layer skill library: committed `skills/` (six vendored factory-required skills plus `SOURCES.md`) and per-user `${FACTORY_HOME}/skills/`. Each adapter declares a `skills_root`; `render.py --paths` reports it; `install.sh` links every library skill (per-user wins) into each selected root, skips non-library paths, adds local skills with `--add-skill`, and removes only library links on `--uninstall`. Nothing is rendered into `dist/`; preflight `RESOLVE` is unchanged. Details: [research.md](research.md).

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
| III. Generated Dist | Pass: adapter edits are followed by a render of all five harnesses; `skills_root` does not reach rendered files, so `dist/` stays unchanged; porcelain gate checked. |
| IV. Stateless Agents | N/A: no agent or state change. |
| V. Simplicity and Reuse | Pass: extends `install.sh` and the `--paths` report; every new file/field has a reason below. |

Post-design re-check: pass, no violations.

## Quality constraints

- **Security (ENG-25)**: `--add-skill` accepts a resolved local directory only; URLs refused; skill content is never executed; all paths quoted.
- **Data integrity (ENG-26)**: validation before any write; copy to a temp folder then `mv`; non-library targets skipped with `skip:`; uninstall matches the library-link prefix only.
- **Errors (ENG-17)**: refusals print `error:` or `exists:` naming the path and exit 2; no tracebacks.
- **Compatibility (ENG-31)**: existing install, uninstall and models report behave as before; `readlink` without `-f`.
- **Dependencies (ENG-27)**: none; frontmatter parsed with inline stdlib Python like the `config.json` check.
- **Licensing**: each vendored skill keeps upstream `LICENSE`; provenance in `skills/SOURCES.md`.
- **Observability/delivery**: `linked:`/`skip:`/`removed:`/`added:` lines; existing CI (suite, re-render, porcelain, `bash -n install.sh`) covers the change.

## Test seams

- `render.py <harness> --paths` reports `skills_root` — each adapter prints the FR-004 root, home-expanded (tests in `tools/tests/test_render_models.py`).
- `install.sh` library linking — every repo-layer skill linked into the selected root; idempotent re-run; per-user precedence; per-user folder dropped by hand gets linked; non-library directory and outside symlink skipped with `skip:` and untouched; shared Codex/Copilot root linked once with `--harness all` (`tools/tests/test_skill_library.py`).
- `install.sh --add-skill <path>` — valid copy plus links; refusals for missing path, URL, missing `SKILL.md`, missing frontmatter, name mismatch, existing destination, each writing nothing (`tools/tests/test_skill_library.py`).
- `install.sh --uninstall` library links — removes only links into either layer; non-library paths and both layer folders survive (`tools/tests/test_skill_library.py`).
- Repo skill layer layout — each `skills/<name>/` for the six required names has `SKILL.md` whose frontmatter `name` matches the folder, a `LICENSE`, and a `SOURCES.md` row with URL, path, commit and license (`tools/tests/test_skill_library.py`).

Exempt: README.md, DESIGN.md - documentation only
Exempt: skills/<name>/ vendored content - verbatim third-party documentation; structure covered by the repo skill layer layout seam
Exempt: adapters/*/adapter.json `skills_root` values - configuration; reported values covered by the `--paths` seam
Overridden: none

## New files, abstractions and dependencies

- `skills/{grilling,domain-modeling,pr,ponytail,tdd,brainstorming}/` - file - repo layer of vendored required skills (FR-001)
- `skills/SOURCES.md` - file - per-skill provenance record (FR-002)
- `tools/tests/test_skill_library.py` - file - library seam tests, kept apart from the existing installer tests; reuses `InstallSandbox` from `test_install.py`
- `skills_root` adapter key - abstraction - per-harness skills root required by FR-004; `dirname(skill_dir)` is wrong for Copilot
- `skills_root=` line in `render.py --paths` - abstraction - hands the expanded root to `install.sh` through its existing `eval`
- `link_skill`, `install_skills`, `unlink_skills`, `add_skill` functions in `install.sh` - abstraction - library-link ownership rule differs from `link`/`unlink_ours` (outside symlinks must be skipped)
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

1. `DESIGN.md` "Skill library" section first: layers, precedence, ownership rule, `--add-skill`, uninstall, manual refresh (FR-014).
2. Adapters: add `skills_root` (research R2). `render.py`: expand it in `load_adapter`, print in `print_paths`. Re-render five harnesses; confirm porcelain clean.
3. `install.sh`: parse `--add-skill <path>`; reject with `--uninstall`. In `install_one`, after factory links, call `install_skills "$skills_root"`; in uninstall branch call `unlink_skills "$skills_root"`. `add_skill` runs once before the harness loop. Contract: [contracts/install-cli.md](contracts/install-cli.md).
4. Vendor six skills per research R6; write `SOURCES.md`.
5. README: library section (layers, `--add-skill`, conflicts, refresh) and the install table note.

## Complexity Tracking

No violations.
