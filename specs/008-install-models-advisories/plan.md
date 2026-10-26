# Implementation Plan: Install model pipeline and round-3 advisory fixes

**Branch**: `008-install-models-advisories` | **Date**: 2026-10-26 | **Spec**: [spec.md](spec.md)

**Input**: `spec.md`, `factory/brief.md`, `specs/007-stabilise-factory/factory/reviews/round-3/verdict.json`, `specs/007-stabilise-factory/plan.md` (seam vocabulary).

**Vocabulary**: `CONTEXT.md`'s glossary governs these artifacts — *per-user render*, *rendered distribution*, *effective model report*, *open relay round* (a relay round holding at least one unanswered question), *test seam*, *red proof*, *rule override*.

## Summary

One stacked PR off `origin/007-stabilise-factory`, two threads. **Personal models (FR-001–FR-006)**: `install.sh` renders a per-user render of each selected harness into `${FACTORY_HOME:-~/.factory}/dist/<harness>` with `config.json` models merged and links the harness's skill and agent directories from that copy — a missing default home `~/.factory` is created (`mkdir -p`, as today), an explicitly set `FACTORY_HOME` that does not exist or is not a writable directory fails naming the path and writes nothing; `tools/render.py` gains an explicit per-user render target and its canonical render never reads `config.json`, so the committed rendered distribution stays machine-independent; the effective model report resolves from the default home and writes nothing; `--uninstall` removes only the links it created and the per-user render. **Round-3 advisories (FR-007–FR-021)**: exit-5 usage refusals for malformed ledger timestamps, `rebind` through `write_run`, ended runs immutable everywhere, at most one open relay round in validation and only as the last round (a null relay and a fully answered relay awaiting checkpoint are conformant), lock liveness as a judgment (unevaluable PID counts as live, `--force` before liveness, identity-checked release), `show` and totals honest about time (union totals only, open runs measured to now, aborted runs hidden) and the hygiene items — dead test duplicates deleted, `replay.py` on shared vocabulary, `resume <run>` documented, 007's plan recording its ENG-3 override. **Installer configuration failure (FR-022, clarified 2026-10-26)**: a `config.json` that does not parse aborts the install cleanly — a message naming the file and the parse error, a non-zero exit, nothing rendered or linked, and the committed `dist/` untouched.

## Technical Context

**Language/Version**: Python 3 (stdlib) for `tools/render.py` and `core/skills/factory/bin/factory_cli/`; Bash for `install.sh`; Markdown for docs and specs.
**Primary Dependencies**: none new — Python 3 stdlib, `bash`, `git` as already used.
**Storage**: JSON files unchanged: run `state.json` (version 4), `${FACTORY_HOME:-~/.factory}/config.json`, run locks. No schema change.
**Testing**: stdlib `unittest` — `python3 -m unittest discover -s tools`, extending the existing `tools/tests/` modules; build gate re-renders all five harnesses and fails on `dist/` drift.
**Target Platform**: macOS/Linux developer machines across `claude-code`, `opencode`, `codex`, `copilot`, `zcode`.
**Project Type**: CLI tool plus installer over generated skill/agent documentation.
**Performance Goals**: one extra render per harness at install time and nothing else; per-write cost unchanged. No stated throughput requirement, so no benchmark (ENG-20 not triggered).
**Constraints**: one writer per run; ended runs immutable; the committed rendered distribution machine-independent and never touched by an installer run; stdlib only; no schema or vocabulary change.
**Scale/Scope**: no new module; changes across `install.sh`, `tools/render.py` and five `factory_cli` modules, two documentation files, two 007 spec files; tests extend seven existing modules.

## Constitution Check

*GATE: passes before Phase 0 research; re-checked after Phase 1 design.*

- **I. Design First** — the corrected model-merge wording lands in `README.md`, `DESIGN.md` and the renderer comment with the code (FR-006); the per-user-render, lock-liveness and checkpoint-retry decisions are recorded in `research.md` and `data-model.md`.
- **II. Harness-Neutral Core** — all CLI fixes live under `core/`; harness-specific linking stays in `install.sh` and `adapters/`.
- **III. Generated Dist (NON-NEGOTIABLE)** — the changed `factory_cli` modules are copied into every `dist/<harness>/skill/bin/`, so each core change is followed by a render of all five harnesses and the rendered `dist/` is committed; the gate is `test -z "$(git status --porcelain -- dist/)"`. Install never renders canonical output (FR-002).
- **IV. Stateless Agents** — checkpoint retry idempotence lives in the state file's pending history entry, not in process memory.
- **V. Simplicity and Reuse** — a reason per new file, abstraction and dependency below; no new module, tool or dependency.

Post-design re-check: no violation found; Complexity Tracking unused.

## Project Structure

### Documentation (this feature)

```text
specs/008-install-models-advisories/
├── plan.md                # this file
├── research.md            # Phase 0: R1–R10 decisions
├── data-model.md          # Phase 1: no schema change, rule deltas
├── quickstart.md          # Phase 1: runnable validation
├── contracts/cli-delta.md # Phase 1: the contract rows this run changes
└── tasks.md               # Phase 2, not created here
```

### Source Code (repository root)

```text
install.sh                                   # per-user render, link from it, models report
tools/render.py                              # --out per-user target; --models/--paths never write
tools/tests/test_render_models.py, __init__.py  # render seam under the new contract
tools/tests/test_install.py                  # install seam incl. the default-home case (FR-005)
tools/tests/test_lock.py                     # liveness/force/release tests; dead duplicates deleted
tools/tests/test_commands.py                 # ledger-add, runs, show, checkpoint, rebind, validate
tools/tests/test_totals.py                   # open-run wall clock
tools/tests/test_state.py                    # exactly-one-open-relay-round rule
tools/tests/replay.py                        # shared imports from factory_cli.state
core/skills/factory/bin/factory_cli/
  cli.py       # ledger timestamp usage validation
  commands.py  # write_run for rebind, ended-run skip, digest totals, checkpoint commit failure
  state.py     # relay-round validation rule
  lock.py      # liveness judgment, force-first takeover, identity-checked release
  totals.py    # open-run wall clock
README.md, DESIGN.md                         # model-merge wording
specs/007-stabilise-factory/contracts/cli.md # resume row, runs wording
specs/007-stabilise-factory/plan.md          # Overridden: ENG-3 line
```

**Structure Decision**: every fix lands in the module that already owns the behaviour (`state.py` validates, `lock.py` guards, `totals.py` measures, `commands.py` commands, `render.py`/`install.sh` the pipeline); nothing moves, no new module, tests extend the existing `tools/tests/` modules so `python3 -m unittest discover -s tools` is unchanged.

## New files, abstractions, dependencies

| Name | Kind | Reason |
|---|---|---|
| `specs/008-install-models-advisories/{research,data-model,quickstart,contracts/cli-delta}.md` | file | Phase 0/1 design artifacts the plan workflow requires; the delta contract keeps 007's contract authoritative while naming what this run changes |
| per-user render target (`render.py <h> --out <dir>`) | abstraction | the committed rendered distribution must stay machine-independent while installed agents carry personal models (FR-001, FR-002) |
| write-free reports (`--models`, `--paths`) | abstraction | the models report must match the linked agents and may never rewrite `dist/` (FR-004) |
| unevaluable-PID-is-live liveness rule | abstraction | liveness is a judgment; a failed probe must never grant a silent takeover (FR-012, FR-013) |
| pending checkpoint history entry reused on retry | abstraction | a retried checkpoint after a failed commit must not duplicate history (FR-011) |
| New source files | none | tests and fixes extend existing modules |
| New dependencies | none | Python 3 stdlib, `bash`, `git` only |

## Quality constraints and verification

- **Security**: no personal model id enters the committed `dist/`, adapters or shared output — asserted by a canonical-render test and a `git status --porcelain -- dist/` check after the sandbox install (SC-001); the installer links only the directories `--paths` names.
- **Data integrity**: every mutation goes through `write_run` (lock, re-read under the lock, validate, atomic write); ended runs are immutable including pending ones; a checkpoint retry reuses its pending history entry — a test each (SC-002, SC-005).
- **Error and resource limits**: every refusal exits with the documented code and a message naming the cause, zero tracebacks — one test per path (ledger-add timestamp, ended pending run, unevaluable lock PID, foreign release, failed checkpoint commit, malformed `config.json` aborting the install) (SC-002, SC-003); explicit `--force` is the only takeover.
- **Performance**: no stated requirement, so no measurement or benchmark; install adds exactly one render per harness into the factory home (ENG-20).
- **Dependencies**: none new; stdlib only (ENG-27).
- **Observability**: install prints the effective model per role; checkpoint reports `commit: null` plus `commit_error` and the "state written, commit failed" message; `validate` names the location of a relay-round violation (SC-005).
- **Compatibility**: state files and saved runs untouched (no schema change); existing installs keep working after re-running the installer; `--uninstall` removes the links it created and the per-user render `${FACTORY_HOME:-~/.factory}/dist/<harness>`, leaving `config.json`, pending runs and the committed rendered distribution untouched; a missing default home `~/.factory` is created while an explicitly configured home that does not exist or is unusable fails naming its path, so no existing layout is rewritten; documentation corrections confined to the sentences the brief names.
- **Delivery**: one stacked PR targeting `007-stabilise-factory`; the build re-renders all five harnesses (the changed `factory_cli` lands in every `dist/<harness>/skill/bin/`) and fails on any drift (SC-006).

## Test seams

- Seam: `bin/factory` CLI command surface — `ledger-add` usage refusals, `runs`, `show`, `validate`, `checkpoint` (commit failure and retry), `rebind` — driven as a process over fixture states. (007 seam, extended.)
- Seam: `factory_cli.state` module API — `read_state`, `validate_state`, `write_state`, now including the relay-round rule: at most one open relay round and only as the last round, a null relay and a fully answered relay awaiting checkpoint conformant, violations reported at `relay` or `relay.rounds[i]`. (007 seam, extended.)
- Seam: `factory_cli.lock` lifecycle — unevaluable owner PID counts as live, `take --force` evaluated before liveness, identity-checked release beside the existing stale/takeover rules. (007 seam, extended.)
- Seam: `factory_cli.totals` interval unions — open-run wall clock measured from start to now, union aggregates only in the digest. (007 seam, extended.)
- Seam: `tools/render.py` render output — canonical render never merges config, per-user `--out` render merges from the default home per key, `--models`/`--paths` write nothing. (007 seam, extended.)
- Seam: `install.sh` install/uninstall flow — per-user render, link targets, effective model report, the factory-home policy (missing default home `~/.factory` created; an explicitly set `FACTORY_HOME` that does not exist or is unusable fails naming the path; a malformed `config.json` aborts the install cleanly, nothing rendered or linked) and `--uninstall` under a throwaway `HOME`, including the default-home case with `FACTORY_HOME` unset. (007's usage-error-only seam, extended.)
- Seam: `tools/tests/replay.py` defect detectors — the 005/006 replay reports the same defects after the imports move to `factory_cli.state`. (007 seam, reused.)
- Exempt: `README.md` and `DESIGN.md` model-merge wording, `tools/render.py` docstring and comment lines - documentation only; the behaviour they describe is checked through the render and install seams.
- Exempt: `specs/007-stabilise-factory/contracts/cli.md` `resume <run>` row and `runs` wording - documentation only.
- Exempt: `specs/007-stabilise-factory/plan.md` `Overridden:` line - documentation only.
- Overridden: ENG-3 - paired red/implement task structure
- Confirmed: 2026-10-26 - Q1 accepted - seams: `bin/factory` CLI command surface, `factory_cli.state` module API, `factory_cli.lock` lifecycle, `factory_cli.totals` interval unions, `tools/render.py` render output, `install.sh` install/uninstall flow, `tools/tests/replay.py` defect detectors

## Complexity Tracking

None. No constitution violation needs justification.
