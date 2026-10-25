# Implementation Plan: Factory skill routing

**Branch**: `005-skill-routing` | **Date**: 2026-10-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-skill-routing/spec.md`

## Summary

Carry the approved design (`docs/superpowers/specs/2026-10-25-factory-skill-routing-design.md`) into the
factory's own instruction set, in the constitution's order: `DESIGN.md` first, then one new compact shared
reference `core/skills/factory/references/skills.md` holding the skill-integration and precedence rules,
then the orchestrator `SKILL.md` (intake classification and the single intent question, a new `brainstorm`
stage, conditional `RESOLVE` of `brainstorming`/`ponytail`/`tdd`/`impeccable`, the two code-craft paths in
`code-build` and `fixer` inputs, widened UI detection), then the two references (`state.md` gains the
`brainstorm` stage and resume handling; `protocol.md` gains the optional `requires_user` question field that
fast mode must not auto-answer), then five roles (`spec-builder` relays the plan's seams as a
`requires_user` question; `code-build` and `fixer` read the shared reference and their new skill paths;
`ui-reviewer` states impeccable's evaluation route and its evidence disclosure; `ux-reviewer` keeps its
distinct lens), then the documents (ADR 0001 revised in place, `README.md` and `docs/product-brief.md`
separating required from conditional skills, `CONTEXT.md` glossary), and finally a canonical re-render of
all five harnesses with `dist/` committed alongside its source.

No renderer or state-CLI code changes: `tools/render.py` copies the whole skill tree, and
`core/skills/factory/bin/factory` passes unknown stage values and question fields through verbatim
([research.md](./research.md), R1-R2). `state.version` stays 3; `core/.../engineering.md` is not touched -
`ENG-1`..`ENG-31` keep their wording and the skill adaptations are stated in the new reference instead
(FR-014).

## Technical Context

**Language/Version**: Markdown instruction files and JSON data; Python 3 for the existing renderer
(`tools/render.py`) and the read-only state CLI (`core/skills/factory/bin/factory`). Neither is edited.

**Primary Dependencies**: none added. Externally resolved, user-installed skills referenced by logical name
only: `brainstorming`, `ponytail`, `tdd`, `impeccable` (plus today's `grilling`, `domain-modeling`, `pr`,
`speckit-*`). Machine paths stay out of `core/` - every lookup is the adapter's `RESOLVE` verb.

**Storage**: files only - `core/`, `adapters/` untouched, generated and tracked `dist/` (five harnesses),
plus run state in `${FACTORY_HOME:-~/.factory}/pending/` and `specs/<branch>/factory/state.json`.

**Testing**: the repository's documented commands in the canonical render environment (research.md, R3):
render every harness, then `test -z "$(git status --porcelain -- dist/)"`; plus two `python3 -` assertions
(link integrity, schema/CLI compatibility over temporary state fixtures). The repository documents build and
test commands, so no test runner is introduced.

**Target Platform**: any supported harness (`claude-code`, `codex`, `copilot`, `opencode`, `zcode`); the
rendered skill is byte-identical on all of them.

**Project Type**: single repository that generates per-harness distributions of an instruction set.

**Performance Goals**: none measurable in the product; the render stays under a second per harness. The one
context-cost constraint is below.

**Constraints**:
- `core/` stays harness-neutral (Constitution II): no tool, path or command name; only the neutral verbs.
- `dist/` is generated, never hand-edited, and committed with its source (Constitution III); no
  adapter-specific model setting changes in this feature (FR-029).
- **Context cost**: `references/skills.md` loads into every `code-build` and `fixer` turn, so it stays
  compact (under 60 lines) and restates no `ENG-n` rule - both asserted by Seam 2; roles link to it (ENG-6,
  Constitution V).
- **Compatibility** (FR-006, FR-017, SC-008): additive state and question fields only, version stays 3; old
  stage values, saved answers, question IDs and resume digests keep working.
- **Security**: nothing installed or fetched beyond the existing authorised `impeccable` offer (FR-011); no
  secret or machine path enters `core/` or `state.json` beyond the resolved skill paths already stored.
- **Resource and wait limits**: at most one extra user wait (the intent question) and one protected seam
  confirmation per run; review and fix round caps, the analyze loop cap and the ledger are unchanged
  (FR-030).
- **Observability**: the existing `ledger`, `history` and `timeline` carry the new stage and role activity;
  no new telemetry mechanism (FR-030).
- **Delivery**: source and render land in the same commits, so revert of those commits is the rollback; no
  migration, since nothing persisted is rewritten.

**Scale/Scope**: 1 new file; 13 edited source and document files (`DESIGN.md`, `SKILL.md`, `state.md`,
`protocol.md`, 5 roles, ADR 0001, `README.md`, `docs/product-brief.md`, `CONTEXT.md`); 5 re-rendered
distributions.

## Constitution Check

*GATE: passed before Phase 0; re-checked after Phase 1 design - still passing.*

- **I. Design First**: `DESIGN.md` is edited first and in the same change (task order below), recording the
  routing table, the idea path, skill precedence, protected confirmations, widened UI detection and the
  validation additions; the brainstormed design record under `docs/superpowers/specs/` is the input, not the
  source of truth. Pass.
- **II. Harness-Neutral Core**: all new text in `core/` names logical skill names and the `RESOLVE` verb
  only; no harness tool, path or command. The impeccable launcher path stays expressed as "the skill's own
  directory" (the reviewer reads it from the resolved `SKILL.md` path it is given). Pass.
- **III. Generated Dist (NON-NEGOTIABLE)**: every harness is re-rendered canonically and the whole of
  `dist/` committed with the source; Seam 1 is that gate. Pass.
- **IV. Stateless Agents**: the new seam confirmation, intake intent and skill paths live in `plan.md`,
  `brief.md` and `state.json`, never in an agent's memory; no role talks to the user (FR-019). Pass.
- **V. Simplicity and Reuse**: one new file, one new stage value, one new optional question field - each
  with a reason below; no new role, verb, model tier, flag, planning chain or telemetry (FR-030). Pass.

**Complexity Tracking**: no violations, table omitted.

## Project Structure

### Documentation (this feature)

```text
specs/005-skill-routing/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── tasks.md          # /speckit-tasks output
```

### Source Code (repository root)

```text
DESIGN.md                                       # edited first: skill routing, precedence, protected
                                                #   confirmations, UI detection, validation plan
core/skills/factory/references/skills.md        # new: shared skill-integration reference
core/skills/factory/SKILL.md                    # intake, brainstorm stage, conditional RESOLVE,
                                                #   role inputs, widened UI detection
core/skills/factory/references/state.md         # brainstorm stage + resume, requires_user note
core/skills/factory/references/protocol.md      # optional requires_user field, fast-mode exclusion
core/roles/spec-builder.md                      # plan stage relays the seam confirmation
core/roles/code-build.md                        # ponytail/tdd inputs + shared reference
core/roles/fixer.md                             # ponytail/tdd inputs + shared reference
core/roles/ui-reviewer.md                       # impeccable evaluation route, evidence disclosure
core/roles/ux-reviewer.md                       # distinct complementary lens
docs/adr/0001-factory-owns-its-engineering-rules.md   # revised in place
README.md · docs/product-brief.md · CONTEXT.md  # required vs conditional skills; glossary terms
dist/<five harnesses>/                          # regenerated, committed with the source

core/skills/factory/references/engineering.md   # deliberately unchanged (FR-014)
tools/render.py · core/skills/factory/bin/factory · adapters/**   # unchanged (research.md R1, R2)
```

**Structure Decision**: the existing core/adapters/dist layout. A shared rule set belongs under
`core/skills/factory/references/` because that tree is what every harness's install carries (research.md,
R1); nothing here needs a new directory.

## Test seams

The product is an instruction set: its public, machine-checkable seams are the rendered distribution, the
links inside it, and the state/question contract the CLI and saved runs depend on. Role-following behaviour
is validated by the agent-driven runs in `DESIGN.md`'s "Validation plan" (spec Assumptions), not by these
checks. Exact commands: [quickstart.md](./quickstart.md).

- **Seam 1 - canonical render of every harness, then `test -z "$(git status --porcelain -- dist/)"`**: the
  repository's documented build and test (`state.commands`, research.md R3). Proves every `core/` edit,
  including the new `references/skills.md`, reaches all five `dist/<harness>/skill/` trees and that no
  distribution is hand-edited (FR-029, SC-009). Red: with any `core/` file edited and `dist/` not
  re-rendered, the gate exits non-zero.
- **Seam 2 - relative-link integrity of the changed Markdown** (`python3 -` assertion over
  `core/skills/factory/**`, `core/roles/**`, `DESIGN.md`, `README.md`, `CONTEXT.md`, `docs/**`): every
  relative link target exists, and `references/skills.md` is linked from `SKILL.md`, `core/roles/code-build.md`
  and `core/roles/fixer.md` (FR-026, SC-010). The same assertion enforces the context-cost constraint:
  `references/skills.md` is under 60 lines and contains no `ENG-` match. Red: the link added to `SKILL.md`
  before the reference file exists fails the check.
- **Seam 3 - state and question contract via `core/skills/factory/bin/factory show`**: over temporary
  pending-state fixtures (not committed) under a throwaway `FACTORY_HOME`, a run with `stage: "brainstorm"`
  and an unanswered question carrying `requires_user: true` digests with the stage and the field passed
  through verbatim, and version 1 (single `relay.questions` batch) and version 2 (string answer) fixtures
  still digest - with `brainstorm` named in `state.md`'s stage list and `requires_user` documented in
  `protocol.md`'s question fields and `state.md`'s fast-mode step (FR-006, FR-017, SC-008). Red: before those two reference edits, the
  documented-vocabulary half of the assertion fails.

Exemptions (documentation or configuration only - prose that agents read at runtime, whose packaging is
covered by Seam 1 and whose links are covered by Seam 2):

- `Exempt: setup/environment steps - configuration only - no product file changes.`
- `Exempt: DESIGN.md - documentation only - the design record.`
- `Exempt: core/skills/factory/references/skills.md - documentation only - agent instructions; Seam 2 proves it exists and is linked, Seam 1 that it ships.`
- `Exempt: core/skills/factory/SKILL.md - documentation only - orchestrator instructions.`
- `Exempt: core/skills/factory/references/state.md - documentation only - schema prose; its new vocabulary is asserted by Seam 3.`
- `Exempt: core/skills/factory/references/protocol.md - documentation only - protocol prose; its new field is asserted by Seam 3.`
- `Exempt: core/roles/*.md - documentation only - role instructions (spec-builder, code-build, fixer, ui-reviewer, ux-reviewer).`
- `Exempt: docs/adr/0001-factory-owns-its-engineering-rules.md - documentation only.`
- `Exempt: README.md - documentation only.`
- `Exempt: docs/product-brief.md - documentation only.`
- `Exempt: CONTEXT.md - documentation only.`
- `Exempt: dist/** - generated output for all five harnesses, produced by the canonical render and guarded by Seam 1, never hand-written.`
- `Exempt: specs/005-skill-routing/** - documentation only - this feature's own spec artifacts.`

`Overridden: none`

## New files, abstractions and dependencies (ENG-10)

- `core/skills/factory/references/skills.md - file - the orchestrator, code-build and fixer need the same skill precedence and loading rules; one reference is the single source of truth the three link to instead of three copies that can drift (FR-026, ENG-6, Constitution V).`
- `abstraction - state.stage value "brainstorm" - the idea path needs a resumable stage of its own; reusing "grill" would make a paused exploration resume as a feature interview (FR-006).`
- `abstraction - question field "requires_user" - fast mode needs one declarative way to mark a confirmation it must not answer; the existing pending_clarify list is keyed to remediation findings and cannot carry a plan-stage seam question (FR-017).`
- `dependency - none added. ponytail, tdd, brainstorming and impeccable are user-installed skills resolved by logical name, not vendored, fetched or auto-installed (spec Assumptions, FR-011).`

## Phase 1 outputs

- [data-model.md](./data-model.md): intake intent, the `brainstorm` stage, the `requires_user` field, skill
  map entries, the seam confirmation line, the UI change signal.
- [quickstart.md](./quickstart.md): the canonical render environment and the three seam commands, plus the
  manual routing checks that `DESIGN.md`'s validation plan takes over.
- `contracts/`: not produced - the only contracts are the run-state schema and the relay question shape,
  both specified in `data-model.md` and asserted by Seam 3.
