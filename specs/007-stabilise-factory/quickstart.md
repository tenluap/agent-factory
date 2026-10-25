# Quickstart: validating the stabilised factory

Phase 1 output for `007-stabilise-factory`. Every command runs from the repository root. No implementation code is described here; task detail lives in `tasks.md`, the machine contract in `contracts/cli.md`.

## Prerequisites

- Python 3 (stdlib only), `git`, `gh` (only for PR scenarios).
- No network access is needed for the automated suite.

## 1. Build and drift gate

```bash
for h in claude-code opencode codex copilot zcode; do python3 tools/render.py "$h"; done
test -z "$(git status --porcelain -- dist/)"
```

Expected: renders succeed, the porcelain gate prints nothing (constitution's Development Workflow gate; it also sees untracked additions).

## 2. Full automated suite

```bash
python3 -m unittest discover -s tools
```

Expected: all tests green, including `tools/tests/` (state validation, every mutating CLI command, gate refusals, envelope checks, totals unions, lock lifecycle, kill-and-resume, installer usage errors, adapter model alignment).

## 3. Replay runs 005 and 006 (SC-002)

```bash
python3 tools/tests/replay.py tools/tests/fixtures/run-005-state.json
python3 tools/tests/replay.py tools/tests/fixtures/run-006-state.json
```

Expected: each replay reports every stability-brief §3 core defect for that run (005: backwards history timestamps, totals exceeding wall clock; 006: missing `implement`/`verify` history entries, missing ledger entries and a zero duration, off-vocabulary values) and nothing passes falsely. Any reported defect beyond the core list carries the written reason from `tools/tests/fixtures/defects.json`. Fixture recovery, if ever needed again:

```bash
git log --all -- 'specs/*/factory/state.json'   # commits before 5a8e7da (005) / 37e7d86 (006)
```

## 4. Writer, gates and lock (fixture run)

```bash
python3 <F>/bin/factory show 007-stabilise-factory --repo .          # digest: waits, spawns, decisions, totals
python3 <F>/bin/factory validate 007-stabilise-factory --repo .       # zero violations in states the suite writes
python3 <F>/bin/factory checkpoint review --files src/x.py            # refused: names the missing verify record
python3 <F>/bin/factory verify --pass --commands '[{"command":"python3 -m unittest discover -s tools","status":0}]'
python3 <F>/bin/factory checkpoint review --files src/x.py            # now allowed
```

Expected: each refusal names the missing record; after `verify --pass` the transition is allowed; a second concurrent session's write is refused with the lock owner named (SC-005). Declared-file rule: a checkpoint with an undeclared dirty file commits only the spec directory plus declared files and reports the rest (SC-008).

## 5. Rebind and prune

```bash
python3 <F>/bin/factory rebind <run> --worktree /tmp/moved-worktree   # validates branch, rewrites paths
python3 <F>/bin/factory prune --dry-run                               # lists stale pending files, deletes nothing
python3 <F>/bin/factory prune --delete                                # explicit deletion only
```

## 6. Installer and models (S10, S17)

```bash
HOME=/tmp/fake-home bash install.sh --harness            # clear usage message, non-zero exit, no crash
HOME=/tmp/fake-home bash install.sh --harness opencode   # prints the effective model per role
```

Expected: only `claude-code` agents carry a rendered `model` field without a `config.json`; the personal values from `${FACTORY_HOME}/config.json` appear when set; README and `adapters/` agree (alignment test in the suite).

## 7. Continuous integration (SC-007)

Push any branch: the workflow runs the suite, the render drift gate and `bash -n install.sh`. A hand edit under `dist/` or a `core/` change without a re-render fails the change.

## 8. Manual golden run (recorded after merge)

`conformance/golden-run/<harness>.md` on `conformance/fixture-repo/`, per harness, including the kill at `review` and the resume on a second harness; results per adapter and capability tier go to `conformance/golden-run-results.md` (FR-013). Read-only access is checked statically by the suite; the golden run records any harness-level limitation the checklist names (FR-014).
