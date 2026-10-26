# Implementation Plan: Stabilise and optimise the factory

**Branch**: `007-stabilise-factory` | **Date**: 2026-10-25 | **Spec**: [spec.md](spec.md)

**Input**: `spec.md`, `factory/brief.md`, `docs/stability-brief.md` (S1–S19), `DESIGN.md`, `docs/product-brief.md`.

## Summary

Deliver stability items S1–S19 in one PR, in milestone order M1 (trustworthy state) → M2 (enforced gates) → M3 (portable and safe) → M4 (proven recovery) → P2 (hardening and context trim). Mechanical bookkeeping — time, vocabulary, the file write, the transition check — moves out of orchestrator instructions into a Python 3 stdlib CLI: `core/skills/factory/bin/factory` stays a thin entry script, logic lives in `bin/factory_cli/` modules the renderer copies into `dist/`. Judgement stays in roles. State schema bumps to version 4 (`decisions`, spawn intervals, closed history vocabulary); readers accept versions 1–4 and writers upgrade a run on its first write.

## Technical Context

**Language/Version**: Python 3 (stdlib only) for CLI and tools; Bash for `install.sh`; Markdown for core, roles, adapters.
**Primary Dependencies**: none new — Python 3 stdlib, `git`, `gh` as already used.
**Storage**: JSON files: run `state.json`, `${FACTORY_HOME:-~/.factory}/pending/`, `${FACTORY_HOME}/config.json`, run locks. No database (brief §6 exclusion).
**Testing**: stdlib `unittest` — `python3 -m unittest discover -s tools`, extended with a new `tools/tests/` package.
**Target Platform**: macOS/Linux developer machines across five harnesses: `claude-code`, `opencode`, `codex`, `copilot`, `zcode`.
**Project Type**: CLI tool plus generated skill/agent documentation (`tools/render.py` → `dist/<harness>/`).
**Performance Goals**: orchestrator context cost stays flat (CLI digests, never whole state into context); a state write is one atomic rename plus one commit. No throughput requirement, so no benchmark (ENG-20 not triggered).
**Constraints**: one writer per run; no undeclared file in a checkpoint; no personal model configuration in shared adapters; a missing Python 3 halts the run with no manual write fallback; `dist/` is never hand-edited.
**Scale/Scope**: 7 new CLI modules, 1 new test package (~8 modules) with fixtures, 1 fixture repository, 5 golden-run checklists, 1 CI workflow, 1 schema version bump, one documentation pass over five files.

## Constitution Check

*GATE: passes before Phase 0 research; re-checked after Phase 1 design.*

- **I. Design First** — every S-item's design decision lands in `DESIGN.md` with or before its implementation (FR-024); the contradicted sentences are corrected there and in `state.md`, `docs/product-brief.md` §14, `README.md`.
- **II. Harness-Neutral Core** — all new behaviour lives under `core/` and names no harness; harness-specific work stays in `adapters/`, `install.sh` and the CI workflow.
- **III. Generated Dist (NON-NEGOTIABLE)** — every `core/` or `adapters/` change is followed by a render of all five harnesses and the rendered `dist/` is committed. The drift gate is the constitution's own `test -z "$(git status --porcelain -- dist/)"`, which sees untracked additions where a bare `git diff --exit-code -- dist/` cannot; CI uses the same gate. Tasks touching only `docs/`, `specs/` or `tools/` render nothing.
- **IV. Stateless Agents** — every new record (`decisions`, spawn intervals, lock, verify record) lives in `state.json` or its lock file; no role remembers a turn.
- **V. Simplicity and Reuse** — a stated reason per new file, abstraction and dependency below; `bin/factory` grows modules rather than a second tool; no new runtime dependency.

Post-design re-check: no violation found; Complexity Tracking unused.

## Milestones

| Milestone | Items | Exit condition (brief §5) |
|---|---|---|
| M1 — Trustworthy state | S1, S2, S5, S6, S8 | State written only through the CLI; replaying 005/006 reports their known defects; totals correct for parallel reviews |
| M2 — Enforced gates | S3, S4, S7, S9 | Illegal transition, malformed envelope, concurrent writer refused by code, a test each; CI green |
| M3 — Portable and safe | S10–S13 | Adapters carry no personal models; checkpoints commit only declared files; a moved run rebinds and resumes |
| M4 — Proven | S14, S15 | Golden run documented per harness with kill-and-resume; read-only access verified per adapter or disclosed |
| P2 + context trim | S16–S19, FR-024 | Prune preview, installer usage errors, reported-vs-estimate labels, Pen rules in one reference, corrected docs |

Each milestone opens with its `DESIGN.md` decision entries and closes green under build and test. Tasks are ordered by these milestones (`tasks.md`, phase 2).

## Project Structure

### Documentation (this feature)

```text
specs/007-stabilise-factory/
├── plan.md           # this file
├── research.md       # Phase 0
├── data-model.md     # Phase 1
├── quickstart.md     # Phase 1
├── contracts/cli.md  # Phase 1
└── tasks.md          # Phase 2, not created here
```

### Source Code (repository root)

```text
core/skills/factory/bin/factory              # thin entry (slimmed): parse argv, call factory_cli
core/skills/factory/bin/factory_cli/         # logic; render copies the folder into dist/<h>/skill/
  __init__.py cli.py state.py lock.py checks.py totals.py commands.py
core/skills/factory/references/state.md      # schema v4, writer commands, closed vocabularies
core/skills/factory/references/protocol.md   # envelope shapes as `envelope check` validates them
core/skills/factory/references/design-code-mapping.md  # single home for Pen rules (S19)
core/skills/factory/SKILL.md                 # calls the writer commands; Pen prose trimmed to pointers
adapters/<h>/adapter.json, harness.md        # model policy, read-only disclosure, setup guidance
tools/render.py, tools/test_render.py        # existing; render gains nothing beyond what S10 needs
tools/tests/                                 # new unittest package + fixtures/ (005/006 states)
conformance/fixture-repo/                    # tiny fixture repository files
conformance/golden-run/<harness>.md          # one golden-run checklist per harness
.github/workflows/ci.yml                     # tests, dist drift gate, bash -n install.sh
```

**Structure Decision**: the CLI keeps its home inside the skill folder so every rendered `dist/<harness>/skill/` stays self-contained on all five harnesses; tests live in `tools/tests/` (an importable package) so the repository's `python3 -m unittest discover -s tools` keeps working unchanged.

## New files, abstractions, dependencies

| Name | Kind | Reason |
|---|---|---|
| `bin/factory_cli/__init__.py` | file | package marker so the entry script and tests import the modules |
| `bin/factory_cli/cli.py` | file | one place for argv parsing, usage text and exit codes (FR-020) |
| `bin/factory_cli/state.py` | file | the single read/validate/atomic-write/upgrade path (FR-001–FR-004, FR-022) |
| `bin/factory_cli/lock.py` | file | the single-writer guard with stale and takeover rules (FR-005) |
| `bin/factory_cli/checks.py` | file | transition gates and role-output shape checks (FR-006, FR-007) |
| `bin/factory_cli/totals.py` | file | interval-union effort accounting (FR-009) |
| `bin/factory_cli/commands.py` | file | command implementations over the modules above (FR-011, FR-012, FR-019) |
| `tools/tests/` (8 modules + `fixtures/`) | file | S8 fixture coverage per CLI command, the 005/006 replay (SC-002), kill-and-resume |
| `tools/tests/replay.py` | file | the 005/006 replay entry point shared by the suite and `quickstart.md` |
| `conformance/fixture-repo/`, `conformance/golden-run/<harness>.md` | file | FR-013's shipped fixture repository and per-harness checklists |
| `conformance/golden-run-results.md` | file | records FR-013's per-adapter golden-run results (the live two-harness run lands after merge) |
| `.github/workflows/ci.yml` | file | FR-018: full suite, render drift and installer syntax on every change |
| interval-union accounting | abstraction | summed parallel durations overstate effort (S6) |
| run-lock lifecycle | abstraction | one guard covering a pending run and its later worktree (S7) |
| schema-v4 upgrade-on-write | abstraction | FR-022 compatibility without a separate migration command |
| gate table (stage → required records) | abstraction | one source of refusal reasons for every illegal transition (S3) |
| Dependencies | none | Python 3 stdlib only; no new runtime or test dependency |

## Quality constraints and verification

- **Security**: a checkpoint stages only the spec directory plus declared files; an undeclared change is reported and never committed (test per case). Rendered read-only agents deny editing where the harness can (static test over `dist/` output); where a harness cannot enforce it, `harness.md` discloses it (S15). No personal model values ship in any adapter (alignment test).
- **Data integrity**: temp-file + rename atomic writes, validation before every write, append-only `decisions`/`timeline`/`history`, non-decreasing timestamps within a record — one test each (FR-001–FR-004).
- **Error and resource limits**: writer commands exit non-zero with the reason on stderr; retry-once-then-halt stays the orchestrator's policy; lock takeover is explicit; `prune` previews before any deletion.
- **Performance**: flat context cost preserved via digest commands; no stated performance requirement, so no benchmark is added (ENG-20).
- **Dependencies**: stdlib only; `git`/`gh` already required by the flow. No new dependency.
- **Observability**: every spawn, wait, decision and transition is visible in `state.json` and in `show`'s digest; tests assert the digest reports them (FR-009, US2).
- **Compatibility**: versions 1–4 and legacy relay shapes readable (fixtures); first-write upgrade; saved runs resume at their recorded stage (resume fixtures, FR-022).
- **Delivery**: one PR in milestone order; build re-renders all five harnesses and fails on `dist/` drift with the porcelain gate; CI runs the suite, the gate and `bash -n install.sh` (FR-018, FR-023).

## Test seams

- Seam: `bin/factory` CLI command surface — `runs`, `show`, `validate`, `checkpoint`, `ledger-add`, `wait-open`, `wait-close`, `answer`, `decisions-add`, `set-status`, `verify`, `envelope check`, `lock take`, `rebind`, `prune` — driven as a process over fixture states.
- Seam: `factory_cli.state` module API — `read_state`, `validate_state`, `write_state` (atomic write, first-write upgrade).
- Seam: `factory_cli.checks` transition rules — one refusal test per illegal transition and one pass test per legal one.
- Seam: `factory_cli.checks` output-shape checker — envelope, reviewer-report and judge-verdict blocks, valid and malformed (the examples in `protocol.md`/`findings.md` are fixtures).
- Seam: `factory_cli.totals` interval unions — overlapping spawns, overlapping waits, human + agent never exceeding wall clock.
- Seam: `factory_cli.lock` lifecycle — live-lock refusal with owner reported, stale only on its recorded host, explicit takeover, the pending-run lock beside its file.
- Seam: `tools/render.py` render output — adapter model fields, read-only permissions, dist parity (existing seam, extended for S10/S15).
- Seam: `install.sh` argument validation — the usage-error path only (`--harness` with no value), run under a throwaway `HOME`.
- Exempt: `DESIGN.md` decision entries and corrections - documentation only.
- Exempt: `docs/` moves and `docs/product-brief.md` §14 corrections - documentation only.
- Exempt: `README.md`, `references/state.md`, `references/protocol.md`, `references/design-code-mapping.md`, `SKILL.md` prose - documentation only.
- Exempt: `adapters/*/adapter.json` model fields, `adapters/*/harness.md`, `.github/workflows/ci.yml` - configuration and documentation only; their behaviour is checked through the render and install seams.
- Exempt: `conformance/golden-run/<harness>.md` checklists, `conformance/golden-run-results.md` and `conformance/fixture-repo/` contents - documentation and test data only.
- Overridden: ENG-3 - paired red/implement task structure

Confirmed: 2026-10-25 - Q1 accepted - seams: `bin/factory` CLI command surface, `factory_cli.state` module API, `factory_cli.checks` transition rules, `factory_cli.checks` output-shape checker, `factory_cli.totals` interval unions, `factory_cli.lock` lifecycle, `tools/render.py` render output, `install.sh` argument validation

## Complexity Tracking

None. No constitution violation needs justification.
