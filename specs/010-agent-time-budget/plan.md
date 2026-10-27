# Implementation Plan: Agent time budget, session issue backlog, benchmark

**Branch**: `010-agent-time-budget` | **Date**: 2026-10-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/010-agent-time-budget/spec.md`

## Summary

Every spawned role receives a `deadline` derived from `${FACTORY_HOME}/config.json` `budget` (default 300s, per-role override). File-writing roles (spec-builder, code-build, fixer) check the clock between work units, stop at a unit boundary past the deadline, commit progress and return `partial` with an `overrun` report; the orchestrator re-spawns, every `partial` return whatever its stop reason is recorded as one issue (a failure-policy retry is not a `partial` return and never counts), and a stall cap (three partial returns of one stage without a new commit) halts the run. Reviewers and the judge finish and are recorded post-hoc. Every overrun, failure, retry, halt and red verify becomes one append-only session issue in `state.json` (schema v5). At run end (`pr-open`/`aborted`) the writer exports a gated improvement backlog under `${FACTORY_HOME}/improvements/`; `/factory improve` lists ready backlogs and suggests feature text, never starting anything. `tools/bench.py` replays a pre-settled fixture feature headlessly, scores recorded run state, and compares two scores. Research decisions: [research.md](research.md); schemas: [data-model.md](data-model.md); command contracts: [contracts/cli.md](contracts/cli.md); validation: [quickstart.md](quickstart.md).

## Technical Context

**Language/Version**: Python 3, stdlib only (`core/skills/factory/bin/factory_cli/`, `tools/`); Markdown for roles/references.

**Primary Dependencies**: none new (stdlib `unittest` is the existing runner).

**Storage**: run `state.json` (schema v5, `issues[]`); `${FACTORY_HOME}/improvements/<repo-name>-<branch>.json` backlog files; `${FACTORY_HOME}/config.json` budget section.

**Testing**: `python3 -m unittest discover -s tools` (existing), plus the build/test commands recorded for this run.

**Target Platform**: macOS/Linux developer machines; all five harnesses (claude-code, opencode, codex, copilot, zcode).

**Project Type**: CLI + agent-skill factory (existing repository layout).

**Performance Goals**: per-spawn overhead is one `budget` lookup plus one clock read per work unit; scoring runs offline on recorded state.

**Constraints**: stdlib only; append-only issues; atomic single-write backlog export; no secrets in exports or scores; every refusal names its problem (exit code 1, stderr).

**Scale/Scope**: 2 new CLI modules, 1 bench driver, 4 new test modules, 2 existing test modules extended, edits to 11 existing files; all five harnesses re-rendered.

## Constitution Check

*GATE: passes before Phase 0 research; re-checked after Phase 1 design — still passing.*

| Principle | Status | Evidence |
|---|---|---|
| I. Design First | Pass | `DESIGN.md` gains the "Time budget, issues, improvement backlog, benchmark" section in the same change; `core/` and `adapters/` edits follow it. |
| II. Harness-neutral core | Pass | `core/` changes use the neutral verbs and spawn inputs (`deadline` is input data); harness headless commands live only in `tools/bench.py`, outside `core/`. |
| III. Generated Dist | Pass | Build command re-renders all five harnesses; `test -z "$(git status --porcelain -- dist/)"` is part of the recorded test command. |
| IV. Stateless Agents | Pass | Budgets, issues, stall counts, backlog status all live in `state.json` / factory-home files read through the writer; roles read `deadline` from inputs and report in the envelope. |
| V. Simplicity and Reuse | Pass | `issues[]` is the only schema addition; one shared `append_issue` helper; `totals`/`checks`/`state` are reused by export and scorer. Reasons below. |

**Complexity Tracking**: none — no constitution violation to justify.

## Project Structure

### Documentation (this feature)

```text
specs/010-agent-time-budget/
├── plan.md              # this file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/cli.md     # Phase 1
└── tasks.md             # Phase 2 (/speckit-tasks - NOT created here)
```

### Source Code (repository root)

```text
DESIGN.md                                        # behavior source of truth: new section, edited first
core/skills/factory/SKILL.md                     # deadline per spawn, overrun/stall policy, issue emission, /factory improve route
core/skills/factory/references/protocol.md       # partial for all file-writing roles; overrun report shape
core/skills/factory/references/state.md          # schema v5, issues[], new/changed commands
core/roles/spec-builder.md                       # deadline check between units, partial + overrun return
core/roles/code-build.md                         # same (deadline stop replaces nothing; low-context partial stays)
core/roles/fixer.md                              # same
core/skills/factory/bin/factory_cli/budget.py     # NEW: budget resolution, deadline derivation
core/skills/factory/bin/factory_cli/improvements.py  # NEW: backlog export, list, claim
core/skills/factory/bin/factory_cli/state.py      # VERSION 5, issues validation, upgrade
core/skills/factory/bin/factory_cli/commands.py   # issue-add, budget, improvements, ledger-add --overrun, set-status/verify issue recording
core/skills/factory/bin/factory_cli/checks.py     # envelope overrun shape
core/skills/factory/bin/factory_cli/cli.py        # routing for the new commands
tools/bench.py                                    # NEW: run / score / compare
conformance/bench/greet-001/{bench.json,brief.md,state-seed.json,overlay/}   # NEW
tools/tests/{test_issues,test_budget,test_improvements,test_bench}.py             # NEW
tools/tests/{test_state,test_envelope}.py                                       # EXTENDED (existing modules)
tools/tests/fixtures/{state-v5.json, bench-pass/, bench-fail/}               # NEW
dist/<harness>/                                   # regenerated by the build command
```

**Structure Decision**: keep the existing single-repo layout; new code extends `factory_cli/` and `tools/`, bench fixtures live beside the existing `conformance/` material. No new project, package or framework.

## New files, abstractions, dependencies (ENG-10)

| Item | Kind | Reason |
|---|---|---|
| `factory_cli/budget.py` | file | one source of truth for budget fallback rules and deadline derivation, shared by `budget` and `ledger-add` |
| `factory_cli/improvements.py` | file | backlog export/list/claim logic shared by `set-status` and `improvements`, keeping `commands.py` from absorbing the backlog domain |
| `append_issue(...)` | abstraction | single append path for issues from `issue-add`, `ledger-add`, `set-status halted`, `verify --fail` (DRY, dedupe on (stage, role, `commit`, kind) where signals meet) |
| `tools/bench.py` | file | benchmark driver/scorer/compare CLI, outside the state writer's responsibility |
| `conformance/bench/greet-001/*` | file | pre-settled fixture feature so replay is reproducible and comparable across factory versions |
| `tools/tests/test_state.py` | file | extend the existing state module with the v5 seam (module predates this feature) |
| `tools/tests/test_envelope.py` | file | extend the existing envelope module with the envelope partial/overrun seam (module predates this feature) |
| `tools/tests/test_{issues,budget,improvements,bench}.py` + fixtures | file | one test module per the remaining seams, recorded states for offline scorer tests |
| dependencies | none | stdlib only (ENG-27) |

## Quality constraints and verification

- **Data integrity** (ENG-26): issues append-only through the single writer; backlog export written once, atomically; claim cannot create a backlog. Verified by `test_issues`, `test_improvements`.
- **Security** (ENG-25): exports and scores carry run facts only; the improvement route writes only under `${FACTORY_HOME}`. Verified by the export test asserting file location and contents.
- **Error/resource limits** (ENG-24): every new command refuses bad input with exit 1 and a named reason, no traceback; the budget check is one lookup plus one clock read per unit. Verified by refusal-path tests.
- **Performance** (ENG-20/21): scoring is offline; per-spawn overhead is bounded as above. No optimisation beyond this.
- **Dependencies** (ENG-27): stdlib only — no new runtime or test dependency.
- **Observability** (ENG-30): every issue visible in state and `improvements` output; score JSON names every metric and every failed condition.
- **Compatibility** (ENG-31): readers accept schema 1–5; older states resume unchanged; all five harnesses re-rendered.
- **Delivery**: build re-renders every harness and the porcelain drift gate passes after the change (constitution III).

## Test seams

Public seams placed under test (a task may not test beyond these; a task needing another seam stops and reports it, ENG-4):

1. `factory issue-add` writer command — `factory_cli.commands.cmd_issue_add` (issue append, one record per event deduped on (stage, role, `commit`, kind) across `issue-add`/`ledger-add`, closed kind/cause vocabularies, `partial_return` mark rules, stall rule result over every partial-return record).
2. Budget check — `factory_cli.budget` resolution/deadline derivation, `factory budget <role>`, and `factory ledger-add`'s overrun detection with its single-issue dedupe.
3. Run-end backlog export — `factory set-status pr-open|aborted` → `factory_cli.improvements.export` (absent before end, present after, zero-issue export, atomic write).
4. Backlog surface — `factory improvements` and `factory improvements claim <name>` (listing, suggested feature text, refusals, `claimed` transition).
5. State schema v5 — `factory_cli.state.read_state` / `validate_state` / `upgrade` (1–5 acceptance, v5 migration and additive shape — every v4 key keeps its name and shape, `issues[]` the only new top-level key — issue validation, append-only).
6. Envelope `partial`/`overrun` shape — `factory_cli.checks.block_problems` (cause vocabulary, detail presence).
7. Benchmark scorer and compare — `tools/bench.py score` / `compare` on recorded fixture states (metrics emission, four named pass conditions, per-metric delta).

Exempt: `DESIGN.md`, `README.md`, `docs/**`, `core/skills/factory/SKILL.md`, `core/skills/factory/references/*.md`, `core/roles/*.md` — agent instructions and documentation only, no executable behavior. Exempt: `specs/010-agent-time-budget/spec.md` — specification wording only, no executable behavior. Exempt: `conformance/bench/**` and `dist/**` — configuration/fixture data and generated output, exercised through seams 2 and 7 and the build gate.

Overridden: none.

Confirmed: 2026-10-27 - Q1 accepted - seams: issue-add writer, budget check, run-end backlog export, backlog surface, state schema v5, envelope partial/overrun shape, benchmark scorer and compare (exemptions as listed above)

## Phases

- **Phase 0** — [research.md](research.md): all unknowns resolved (enforcement model, budget resolution, dedupe, stall bookkeeping, schema v5, export and claim gates, bench fixture, headless drivers, scorer single source, pass conditions, quality constraints).
- **Phase 1** — [data-model.md](data-model.md) (entities and schemas), [contracts/cli.md](contracts/cli.md) (command/envelope/bench contracts with exit codes), [quickstart.md](quickstart.md) (runnable validation scenarios). Constitution re-check post-design: still passing.

## Spec alignment follow-ups (spec.md wording)

The design contract is authoritative for implementation (the `commit` provenance makes FR-004 checkable); these `spec.md` wording updates are noted here (analyze I1/I3) for the pass that owns `spec.md`, not applied by this stage:

- **FR-008**: adopt the design superset — signature `factory issue-add <kind> <stage> <role> --detail --duration-ms [--cause] [--commit] [--partial-return]`, record `{ at, kind, stage, role, cause, detail, duration_ms, commit, partial_return }`, `--cause` required only for `overrun` (null otherwise).
- **FR-010 / US2 scenario 2**: `retry` records a non-deadline `partial` stop (e.g. low context) — marked `partial_return: true` — and a failure-policy retry — unmarked — alike; a deadline stop is recorded as `overrun` (FR-002), still marked when it is a `partial` return's stop. The stall cap reads only marked records, so a failure-policy retry never counts (FR-004).
- **FR-011 + assumption**: name the backlog file `<repo-name>-<branch>.json` and the exported sha `factory_sha` (one form per concept); at first use in US3/SC-003/Key Entities write "the factory version (`factory_sha`)".
- **Edge case**: the export succeeds with `factory_sha: null` when the factory install is not in a git tree.
