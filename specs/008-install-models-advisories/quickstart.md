# Quickstart: validating `008-install-models-advisories`

Run everything from the run's worktree. No dependency beyond Python 3, `bash`, `git`.

## Gates

```bash
python3 -m unittest discover -s tools          # full suite
for h in claude-code opencode codex copilot zcode; do python3 tools/render.py "$h"; done
test -z "$(git status --porcelain -- dist/)"   # build gate: no generated drift
```

Expected: all tests pass; the re-render leaves `dist/` byte-identical (the changed `factory_cli` modules make the first re-render show a diff to commit; after committing, the gate is clean). The gate is the constitution's porcelain check; `git diff --exit-code -- dist/` cannot see untracked additions and is not the gate.

## S1 — Personal models reach the installed agents (FR-001–FR-005, FR-022)

```bash
sandbox="$(mktemp -d)"
HOME="$sandbox" bash -c 'unset FACTORY_HOME
  mkdir -p "$HOME/.factory"
  printf "%s" "{\"models\":{\"opencode\":{\"deep\":\"test-org/test-deep\"}}}" > "$HOME/.factory/config.json"
  ./install.sh --harness opencode'
```

Expected: the linked agent files under the harness's agent directory carry `test-org/test-deep` for deep-tier roles; the printed models report lists it as effective; `git status --porcelain -- dist/` is empty (the committed `dist/` is untouched). The same with `FACTORY_HOME` exported to a personal home applies to the per-user render there. Without any `config.json`, the adapter defaults are used and reported; a missing default home `~/.factory` is created, while an explicitly set `FACTORY_HOME` that does not exist or is not a writable directory fails naming the path and writes nothing. A `config.json` that does not parse aborts the install: a message naming the file and the parse error, a non-zero exit, nothing rendered or linked, `git status --porcelain -- dist/` empty (FR-022).

## S2 — Clean refusals (FR-007, FR-009, FR-012–FR-014)

Through the suite (`tools/tests/test_commands.py`, `tools/tests/test_lock.py`): `ledger-add --started-at 'yesterday'` exits 5 naming the value; a write targeting an ended pending run is refused; a lock with `owner_pid: 999999999999` is treated as live and `lock take --force` takes it over; release leaves a foreign lock file in place.

## S3 — Single writer, relay-round rule and checkpoint retry (FR-008, FR-010, FR-011)

Through the suite: `rebind` under a competing lock either refuses or re-reads under the lock; a checkpoint whose commit fails exits 1 with `state written, commit failed`, and re-running it leaves exactly one history entry for that stage; `validate` reports a run with several open relay rounds at `relay` and unanswered questions in a non-last round at `relay.rounds[i]`, while a null relay and a fully answered relay awaiting checkpoint report no anomaly.

## S4 — Truthful time (FR-015–FR-017)

Through the suite (`tools/tests/test_totals.py`, `tools/tests/test_commands.py`): with overlapping spawns the digest's aggregates are the union totals only; a fixture run without `ended_at` shows elapsed wall clock in `totals_sentence`; `runs` omits aborted runs.

## S5 — Hygiene (FR-018–FR-021)

`python3 tools/tests/replay.py` reports the same 005/006 defects as before the import move; `grep -c "def test_lock_take_cli_refuses_live_and_takes_with_force" tools/tests/test_lock.py` prints `1`; `grep -A2 "resume <run>" specs/007-stabilise-factory/contracts/cli.md` finds the new row; `grep "Overridden: ENG-3" specs/007-stabilise-factory/plan.md` finds the recorded override.

Details and rationale: [data-model.md](data-model.md), [contracts/cli-delta.md](contracts/cli-delta.md), [research.md](research.md).
