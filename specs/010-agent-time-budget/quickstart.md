# Quickstart: validation scenarios

Run from the worktree root. Nothing here needs a live harness except scenario 5, which is the documented manual path and costs tokens.

## Prerequisites

- Python 3, git. No new dependency is installed (stdlib only).
- Build and test commands (the run's recorded commands):
  - build: `for h in claude-code opencode codex copilot zcode; do python3 tools/render.py "$h" || exit; done`
  - test: `python3 -m unittest discover -s tools && bash -n install.sh && test -z "$(git status --porcelain -- dist/)"`

## 1. Automated suite (the gate)

```sh
python3 -m unittest discover -s tools
```

Expected: green, covering `issue-add` (kinds, causes, append-only), the stall rule (every partial-return record — `overrun`/`retry` of a file-writing role — counts toward the three with no new commit; never-stopped roles' records never count), the budget check (fallbacks, deadline, `ledger-add` overrun detection and single-issue dedupe), the export gate (no file before run end, file at `pr-open`/`aborted`, zero-issue export), claim refusals and the `claimed` transition, schema v5 migration (additive shape: every v4 key keeps its name and shape, `issues[]` the only new top-level key) and 1–5 read acceptance, the envelope `overrun` shape, and the scorer/compare on recorded states (`tools/tests/fixtures/bench-*`).

## 2. Build gate (constitution III)

```sh
for h in claude-code opencode codex copilot zcode; do python3 tools/render.py "$h" || exit; done
test -z "$(git status --porcelain -- dist/)"
```

Expected: every `dist/<harness>/` tree re-rendered from `core/`+`adapters/`, no drift.

## 3. Budget and issue recording by hand

```sh
FACTORY_HOME=/tmp/fh python3 core/skills/factory/bin/factory budget code-build
FACTORY_HOME=/tmp/fh python3 core/skills/factory/bin/factory issue-add overrun implement code-build \
  --cause test-loop --detail "41s past deadline" --duration-ms 341000   # repeat with --commit held fixed 3x -> "halt": true
FACTORY_HOME=/tmp/fh python3 core/skills/factory/bin/factory issue-add retry implement code-build \
  --detail "low context at unit boundary"   # a non-deadline stop counts the same way
```

Expected: `deadline` always well-formed (300s default, per-role override honoured); the third identical-commit stop returns `stalls.halt: true` whatever the stop reason; overrun records of reviewers/judge/orchestrator never move the count. Details in `contracts/cli.md`.

## 4. Backlog gate by hand

```sh
# inside a run worktree, at run end:
python3 <F>/bin/factory set-status aborted
ls ${FACTORY_HOME}/improvements/           # the export exists, status ready
python3 <F>/bin/factory improvements claim <name>   # refused while a copy's source run is still running
```

Expected: no export exists before `pr-open`/`aborted`; the export appears once with issues, totals, `factory_sha` (`null` when the factory install is not in a git tree), `ready`; a second claim and an unknown name are refused with a message naming the problem.

## 5. Benchmark (manual, token-costing)

```sh
python3 tools/bench.py run --harness opencode --bench greet-001 --home /tmp/fh-bench
python3 tools/bench.py score /tmp/fh-bench/worktree/*/specs/*/factory/state.json --bench greet-001
python3 tools/bench.py compare a.json b.json
```

Expected: the run stops at the approver gate (no PR, nothing approved); the score names every metric and every pass condition, `pass: true` only when all four are met; `compare` prints per-metric deltas. Fallback without a headless harness: run `/factory` on the fixture copy manually to the approver stop, then `score` the recorded state (FR-018).

## Reference

- Command surface and shapes: [`contracts/cli.md`](contracts/cli.md)
- Entities and schemas: [`data-model.md`](data-model.md)
- Decisions: [`research.md`](research.md)
