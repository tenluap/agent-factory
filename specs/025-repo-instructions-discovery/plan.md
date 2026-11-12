# Implementation Plan: The factory discovers the repository's own instructions

**Branch**: `025-repo-instructions-discovery` | **Date**: 2026-11-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/025-repo-instructions-discovery/spec.md`

## Summary

Add a stdlib-only scanner module to the factory CLI that lists tracked files at a resolved commit with `git ls-tree`, reads only needed blobs through one `git cat-file --batch`, matches a table-driven catalogue plus governance documents, follows imports and links to a fixpoint, applies the three config lists, and emits a deterministic index. Two commands expose it: the read-only `factory instructions` report and the `factory instructions-record` writer, which reuses `profile-record`'s run targeting, sidecar placement and commit path. The orchestrator calls the writer at every preflight, discloses the result, reads `always` entries at the recorded ref, and sources build and test commands from every root-scope entry. Design: [research.md](research.md), [data-model.md](data-model.md), [contracts/cli.md](contracts/cli.md), [quickstart.md](quickstart.md).

## Technical Context

**Language/Version**: Python 3 (CI `3.x`), standard library only; git CLI.

**Primary Dependencies**: none new.

**Storage**: run state (`state.json` or the pending file); `instructions.json` in the run folder; `.factory/config.json` read at the scanned ref.

**Testing**: `python3 -m unittest discover -s tools`; sandbox git repos from `tools/tests/__init__.py` (`Sandbox`).

**Target Platform**: macOS, Linux and Windows wherever the factory CLI runs; every harness renders the same core.

**Project Type**: CLI plus harness-neutral orchestrator skill.

**Performance Goals**: two git processes per scan regardless of entry count; only matched or followed blobs are read (ENG-21).

**Constraints**: deterministic byte-identical output (SC-002); never reads the working tree; never stops a run; never truncates the index.

**Scale/Scope**: repositories with tens of thousands of tracked paths; one tree listing per scan.

### Quality constraints

- **Security (ENG-25)**: git arguments are passed as argv lists, never through a shell; `--ref` is checked with `rev-parse --verify <ref>^{commit}` before any other use; link, import and symlink targets that resolve outside the repository are ignored; blob content is never executed.
- **Data integrity (ENG-26)**: the writer uses the existing validate-then-atomic-write path under the run lock; a failed scan writes nothing and keeps the previous summary.
- **Error and resource limits (ENG-17, ENG-24)**: import depth 4, link depth 1, a visited set against cycles; malformed input becomes a note; git failures become `error` (writer) or exit 5/2 (report).
- **Compatibility (ENG-31)**: the state field is optional; older states validate unchanged; no schema version bump.
- **Observability (ENG-30)**: notes, warning, delta and `error` in the writer's JSON; the orchestrator discloses them.
- **Delivery**: `drop` already removes the run folder, so the index file leaves the branch.

## Constitution Check

- **I. Design First**: PASS. `DESIGN.md` is updated in the first task, before `core/` changes.
- **II. Harness-Neutral Core**: PASS with justification. Justification: the catalogue in `core/skills/factory/bin/factory_cli/instructions.py` names other tools' instruction file names as data about consuming repositories, identical on every harness; it names no harness tool, path or command the factory invokes, exactly as `SKILL.md` already names `CLAUDE.md` and `AGENTS.md`. `SKILL.md` changes use only `SHELL`.
- **III. Generated Dist**: PASS. No `dist/` edits; the build check renders all five harnesses.
- **IV. Stateless Agents**: PASS. The index lives in state and on disk; the orchestrator re-reads it at grill.
- **V. Simplicity and Reuse**: PASS. Reuses `resolve_target`, `write_run`, `commit_worktree`, the pending sidecar pattern, `adopt._resolve` and the `drop` folder removal. Every new file, field and abstraction has a reason below.

Post-design re-check: unchanged, PASS.

## Project Structure

### Documentation (this feature)

```text
specs/025-repo-instructions-discovery/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/cli.md
└── tasks.md            (tasks stage)
```

### Source Code (repository root)

```text
core/skills/factory/bin/factory_cli/
├── instructions.py     NEW: catalogue, git object reads, front matter, imports/links, precedence, index, delta
├── commands.py         cmd_instructions, cmd_instructions_record
├── cli.py              usage lines and dispatch for both commands
├── state.py            light validation of the optional `instructions` summary
├── adopt.py            move and clean the `.instructions.json` sidecar like `.profile.md`
└── models.py           config README text documents the three lists (FR-014)
core/skills/factory/SKILL.md                 preflight item 5, step 4.3, grill, adoption
core/skills/factory/references/state.md      `instructions` summary, writer, report
DESIGN.md                                    decision recorded first
.factory/config.json                         NEW: this repository's lists (FR-015)
tools/tests/test_instructions.py             NEW: scanner, report, writer, contract tests
```

`CONTEXT.md` (FR-026) and `docs/adr/0020-the-factory-discovers-repo-instructions-itself.md` (FR-027) are already written; implement checks the ADR number is still free on `origin/main` and every remote branch and renumbers if not.

**Structure Decision**: one new module beside `detect.py`, wired through the existing `commands.py` / `cli.py` split.

### New files, abstractions and dependencies

- `core/skills/factory/bin/factory_cli/instructions.py` - file - `detect.py` profiles the working tree for stacks; discovery reads git objects at a ref and has its own catalogue, classification and delta, so mixing them would couple two unrelated reasons to change.
- `tools/tests/test_instructions.py` - file - one home for scanner, CLI, writer and text-contract tests, mirroring `test_detect.py` / `test_profile_record.py`; fixture trees are built in sandbox git repos, not tracked fixture directories, because tracked fixture instruction files would be indexed by this repository's own scan and cannot express untracked or locally modified files.
- `.factory/config.json` - file - FR-015 requires this repository's tracked lists; none exists yet.
- `CATALOGUE` (tuple of row records in `instructions.py`) - abstraction - FR-002 requires a table-driven catalogue, one row per tool, with its default kind and front-matter mapping.
- Glob-to-regex translator in `instructions.py` - abstraction - `fnmatch` lacks `**` and crosses `/`; `PurePath.full_match` needs Python 3.13 (research.md R4).
- State field `instructions`, entry field `source` - fields - FR-017 summary; FR-024 source tiering (data-model.md).
- Dependencies: none.

## Test seams

Seams are the public CLI and the orchestrator text; tests drive them through `Sandbox` git repos and `Sandbox.cli`.

- **S1 `factory instructions`** (read-only report). Required injected failure paths: F1.1 not a git repository (exit 2); F1.2 ref does not resolve (exit 5, names the ref); F1.3 malformed `instructions` config section (note, catalogue alone); F1.4 unparseable rule front matter (row default kind, note); F1.5 import target missing or untracked (note, importer kept); F1.6 import cycle (followed once); F1.7 import chain past 4 hops (note naming the stop); F1.8 non-UTF-8 blob (indexed, empty title, note); F1.9 symlink to a missing or outside target (skipped, note).
- **S2 `factory instructions-record`** (writer). Required injected failure paths: F2.1 scan failure because the run's ref does not resolve (exit 0, `error`, nothing written, previous summary kept); F2.2 no writable run (exit 1); F2.3 live lock (exit 1, nothing written); F2.4 previous index file unreadable (delta `null`, note).
- **S3 `factory adopt`** (existing; pending sidecar move). Required injected failure path: F3.1 refused adoption keeps the pending `.instructions.json` sidecar.
- **S4 `factory validate`** (state validation of the summary). Required injected failure path: F4.1 malformed `instructions` summary reported as a violation.
- **S5 `factory drop`** (existing; index leaves the branch). Required injected failure paths: none.
- **S6 orchestrator text contract** (`core/skills/factory/SKILL.md` read by the test). Required injected failure paths: none.

Exempt: `DESIGN.md` - documentation only.
Exempt: `core/skills/factory/references/state.md` - documentation only.
Exempt: `models.py` config README text - documentation text emitted by `factory init`; no command result changes.
Exempt: `.factory/config.json` - configuration only; its effect (SC-005) is asserted under S1.
Exempt: `CONTEXT.md` and the ADR - documentation only, already written.

Overridden: none

## Complexity Tracking

No constitution violations; Principle II carries the justification line above.
