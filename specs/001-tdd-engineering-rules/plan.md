# Implementation Plan: Engineering discipline for factory code-writing roles

**Branch**: `001-tdd-engineering-rules` | **Date**: 2026-10-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-tdd-engineering-rules/spec.md`

## Summary

Give the factory one shared, harness-neutral engineering rules reference (`core/skills/factory/references/engineering.md`) whose rules carry stable `ENG-n` ids, and point the code-writing, planning, reviewing and judging roles at it. The planning role's own stage instructions gain the test-first behaviour (a "Test seams" section in the plan, a failing-test task before each implementation task, a HIGH blocking seam-mapping check in analyze, seam questions in clarify only when seams are ambiguous). The implementing and fixing roles gain red-green-refactor, the `Red:` proof line in the task commit body, the bounded reuse search, and the stop-on-missing-seam failure. `DESIGN.md` records the discipline first (constitution I), then `core/` changes, then every harness is re-rendered and the generated `dist/` is committed with the source (constitution III).

The change is instructions and generated output only: nine Markdown files under `DESIGN.md` and `core/`, plus the four rendered copies under `dist/`. No product code, no renderer change, no orchestrator flow stage, no new state field.

## Technical Context

**Language/Version**: Markdown instruction files (role prompts, skill references, design document); Python 3 only as the existing, unchanged renderer `tools/render.py`

**Primary Dependencies**: `tools/render.py` and the four adapters in `adapters/` (`claude-code`, `codex`, `copilot`, `opencode`); the roles' existing `<F>/references/<name>.md` reference mechanism

**Storage**: Files in git. The red proof lives in the task's commit body; nothing new is persisted in `state.json`

**Testing**: The repository has no test runner and needs none for this change (see "Test seams" below). Verification is `commands.build` (render every harness) followed by `commands.test` (`git diff --exit-code -- dist/`)

**Target Platform**: Any agent harness the factory supports; the rules file and role text are byte-identical across harnesses

**Project Type**: Instruction set / prompt library with a generator (`core/` + `adapters/` -> `dist/`)

**Performance Goals**: N/A. The only budget that matters is prompt length: role prompts stay short, and the rules live in one reference the roles point at rather than restate

**Constraints**: `core/` names no harness tool, path or command (constitution II); `dist/` is never hand-edited (constitution III); role prompts stay short, imperative and unambiguous with one term per concept (Writing Standards); agents are stateless, so every rule must be readable from disk in a single spawn (constitution IV)

**Scale/Scope**: 1 new reference file, 1 design-document section, 6 role prompts touched, 1 shared reference touched, 4 rendered harness trees regenerated; 11 rules (`ENG-1` .. `ENG-11`)

## Test seams

**This change is documentation/configuration-exempt from test-first, in whole (FR-025).**

**Reason**: the change adds and edits Markdown instruction files for agents (`DESIGN.md`, the new `core/skills/factory/references/engineering.md`, six role prompts, one shared reference) and the generated per-harness copies of them. It introduces no executable behaviour: there is no function, no entry point and no runtime path a test could call. The repository has no test runner and this change does not create a need for one, so FR-018's runner-setup task does not apply here.

**Seams under test**: none. There is no public entry point in this change.

**Verification instead of tests** (FR-025, SC-005):

1. `commands.build` - `for h in $(python3 tools/render.py --list); do python3 tools/render.py "$h" || exit 1; done` - renders every harness; a malformed role file (missing frontmatter, or a `'''` in a body that breaks the TOML agents) fails the build.
2. `commands.test` - `git diff --exit-code -- dist/` - proves the committed `dist/` matches `core/` + `adapters/` for every harness, so no harness carries stale or hand-edited rules.
3. Inspection checks in [quickstart.md](./quickstart.md): the rules appear in exactly one source file (SC-004), every rule has a unique `ENG-n` id (SC-004a), each of the six roles references the file, and the rendered tree contains it for every harness.

End-to-end behaviour (a real run producing red proofs and seam findings) is observed on the next factory run, per the "Validation plan" in `DESIGN.md`.

**Overridden**: none. No rule of the shared reference is overridden by this repository's constitution; the two agree (constitution V is the source of `ENG-10`).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I. Design First | The behaviour change is recorded in `DESIGN.md` before `core/` and `adapters/` carry it, in this change | PASS - task order puts the `DESIGN.md` "Engineering discipline" section first (FR-022); `core/` edits follow |
| II. Harness-Neutral Core | No file added or edited under `core/` names a harness tool, path or command | PASS - `engineering.md` and the role edits use only the `<F>/references/...` form and the neutral verbs; no adapter needs a change |
| III. Generated Dist (NON-NEGOTIABLE) | Every `core/`/`adapters/` change is followed by a render of every harness, and `dist/` is committed with the source | PASS - the render task renders all four harnesses and commits `dist/`; `commands.test` proves no drift (SC-005) |
| IV. Stateless Agents | No role relies on memory of an earlier turn | PASS - the rules are read from the shared reference each spawn; the red proof is read from the commit body and `tasks.md`; the seams are read from `plan.md`. The external `tdd` skill is rejected for exactly this reason (ADR 0001) |
| V. Simplicity and Reuse | Smallest change; a new file needs a stated reason in the plan | PASS - one new file, `core/skills/factory/references/engineering.md`. **Reason**: FR-001 requires the rules in exactly one harness-neutral place that six roles point at; inlining them in six prompts would duplicate them and let them drift (SC-004). Nothing else is added: no new verb, no new state field, no new stage, no new commit type, no renderer change; the change reuses the existing reference mechanism, the existing per-task commit, and the existing failure policy |
| Writing Standards | Prompts and references short, imperative, unambiguous, one term per concept | PASS - the rules reference is one numbered rule per entry; terms come from the glossary in `CONTEXT.md`; the role edits add lines, not prose |
| Development Workflow | Build renders every harness; `git diff --exit-code -- dist/` passes; flow changes validated per `DESIGN.md` | PASS - both commands are the stated verification; end-to-end validation is deferred to the next real run, as the design document's validation plan already prescribes |

Post-design re-check (after Phase 1): unchanged, all PASS. The Phase 1 artifacts add no file to `core/`, no verb and no adapter change; `contracts/` only writes down the three textual contracts the change already implies.

## Project Structure

### Documentation (this feature)

```text
specs/001-tdd-engineering-rules/
├── plan.md              # This file
├── spec.md
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── engineering-reference.md
│   ├── commit-body.md
│   └── plan-artifact.md
├── checklists/requirements.md
└── factory/             # run state, brief, analyze and remediation logs
```

Repository-level documentation already written in grill-with-docs: `CONTEXT.md` (glossary) and `docs/adr/0001-factory-owns-its-engineering-rules.md`, `docs/adr/0002-red-proof-lives-in-the-task-commit-body.md`, `docs/adr/0003-test-seams-are-settled-at-plan-time.md`. This plan changes none of them.

### Source Code (repository root)

```text
DESIGN.md                                   # + "Engineering discipline" section (written first)
core/
├── skills/factory/
│   ├── SKILL.md                            # unchanged
│   └── references/
│       ├── engineering.md                  # NEW: ENG-1 .. ENG-11, the shared rules
│       ├── findings.md                     # + engineering findings cite the ENG-n id
│       ├── protocol.md                     # unchanged
│       ├── state.md                        # unchanged
│       └── verbs.md                        # unchanged
└── roles/
    ├── spec-builder.md                     # plan/tasks/analyze/clarify test-first instructions
    ├── code-build.md                       # red-green-refactor, Red: line, reuse search, missing-seam failure
    ├── fixer.md                            # same rules; one Red: line per behaviour-changing fix
    ├── code-standards.md                   # untested behaviour and duplication HIGH blocking, cite ENG-n
    ├── spec-conformance.md                 # check each implementation commit body's Red: line against tasks.md
    ├── review-judge.md                     # reference the rules; rate engineering findings by id
    ├── security-reviewer.md                # unchanged
    ├── ui-reviewer.md                      # unchanged
    └── ux-reviewer.md                      # unchanged
adapters/                                   # unchanged (no harness-specific behaviour added)
tools/render.py                             # unchanged
dist/{claude-code,codex,copilot,opencode}/  # regenerated, committed with the source
```

**Structure Decision**: the existing `core/` + `adapters/` -> `dist/` layout is kept exactly. The rules land in `core/skills/factory/references/` because `tools/render.py` already copies that whole directory into `dist/<harness>/skill/references/` and the roles already address it as `<F>/references/<name>.md`; that is why no renderer and no adapter change is needed (research.md, D3).

## Complexity Tracking

> Fill ONLY if Constitution Check has violations that must be justified

None. No principle is violated and no simpler alternative was rejected on complexity grounds; the one new file is justified in the Constitution Check (V) and in ADR 0001.
