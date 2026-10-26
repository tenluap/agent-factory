# Research: Install model pipeline and round-3 advisory fixes

Phase 0 for `008-install-models-advisories`. Every technical unknown in `plan.md` resolves here; findings source is `specs/007-stabilise-factory/factory/reviews/round-3/verdict.json`, decisions are `factory/brief.md`'s.

## R1 — Where personal models are merged

**Decision**: `tools/render.py` gains one explicit per-user render target, `render.py <harness> --out <dir>`, which renders the harness tree into `<dir>` with `${FACTORY_HOME:-~/.factory}/config.json` `models.<harness>` merged over the adapter defaults (per-key fallback). The plain `render.py <harness>` render into `dist/<harness>` never reads `config.json` at all. `install.sh` renders each selected harness into `${FACTORY_HOME:-~/.factory}/dist/<harness>` and links the skill and agent directories from that copy.

**Rationale**: the committed rendered distribution must stay canonical and machine-independent (FR-002) while installed agents must carry the user's models (FR-001); only an explicit second render target can satisfy both. The brief fixes the target path.

**Alternatives considered**: (a) the verdict's report-only fix — leave the linked rendered distribution without personal models; rejected, the brief supersedes it. (b) keep env-gated merging inside `load_adapter` and unset `FACTORY_HOME` for canonical renders; rejected, an exported `FACTORY_HOME` would still be one forgotten `unset` away from leaking personal ids into committed output. (c) post-process the copied agent files with `sed`; rejected, the renderer already owns field generation.

## R2 — The effective-model report

**Decision**: `--models` and `--paths` become reports that never write: `render.py <harness> --models` prints the effective model per role resolved from the default home (adapter defaults merged with `config.json`, whether or not `FACTORY_HOME` is exported) without rendering anything.

**Rationale**: the report must equal what the linked agents carry (FR-004) and an installer run may never rewrite or dirty the committed rendered distribution (FR-002). Today both `install.sh` render calls re-render `dist/`, which is the demonstrated leak.

**Alternatives considered**: keeping `--models` as a post-render print; rejected, it forces a canonical render at install time.

## R3 — Default-home resolution

**Decision**: one helper resolves the factory home as `${FACTORY_HOME:-~/.factory}` (expanded) for config reads and the per-user render root; an absent `config.json` or absent keys fall back per key to adapter defaults. A missing default home `~/.factory` is created (`mkdir -p`, as today); an explicitly set `FACTORY_HOME` that does not exist, or any home that is not a directory or not writable, fails the install with a message naming the path, writing nothing — the committed rendered distribution is untouched because install never writes it. `--uninstall` removes the links it created and the per-user render at `${FACTORY_HOME:-~/.factory}/dist/<harness>`, leaving `config.json`, pending runs and the committed rendered distribution untouched.

**Rationale**: FR-003 and the edge cases in `spec.md`; today an unset `FACTORY_HOME` silently means "no config", and `test_render_models.py` asserts that false behaviour.

## R4 — Lock liveness and takeover

**Decision**: `_alive` treats a PID the OS probe cannot evaluate (wrong type, out of range, `OverflowError`/`ValueError`/`TypeError`) as **live**; `ProcessLookupError` means gone; every other `OSError` means live (conservative). `take` evaluates `force` before liveness. `release` re-checks file identity (`st_dev`/`st_ino`) before unlinking.

**Rationale**: FR-012–FR-014; a lock whose owner cannot be judged must never be silently replaced, and only `--force` takes over. The verdict demonstrated an `OverflowError` traceback in `_alive` and a `take --force` that could not bypass it.

**Alternatives considered**: raising a usage error on a malformed lock; rejected by the edge-case rule "treated as live, never a crash".

## R5 — Checkpoint commit failure and retry

**Decision**: `cmd_checkpoint` catches a `git` failure after the state write and reports `state written, commit failed: <reason>` with exit 1, its JSON result carrying `commit: null` and `commit_error`; a retry reuses the trailing history entry for the same stage whose `commit` is null instead of appending a second entry.

**Rationale**: FR-011 and SC-002 distinguish "written, not committed" from success, and a retry must not duplicate history. The state file carries the pending entry (constitution IV: no state outside the file).

**Alternatives considered**: writing the history entry only after a successful commit; rejected, it would leave state and repository out of order in the other direction and lose the checkpoint on crash.

## R6 — Malformed ledger timestamps

**Decision**: `ledger-add` validates `--started-at` / `--ended-at` with `state.parse_iso` at argument parsing and calls `die_usage` (exit 5) naming the offending value; a non-string or unparseable value never reaches the duration arithmetic.

**Rationale**: FR-007; today `None - None` raises `TypeError` (exit 1, traceback).

## R7 — Rebind through the single writer

**Decision**: `cmd_rebind` builds its rewrite as a `mutate` passed to `write_run`, so the run's lock is taken and the state re-read under it before `worktree`/`repo` are replaced.

**Rationale**: FR-008; the direct `state.write_state(path, new_state)` call raises `LockHeld` as a traceback and races with the writer.

## R8 — Validation of relay rounds, listings and digests

**Decision**: `validate_state` counts open relay rounds (a round with at least one unanswered question; version-1 shape is one round) and reports `relay` / `relay.rounds[i]` when the count is not exactly one (FR-010). `cmd_runs` skips aborted runs as it already skips `pr-open` (FR-017). `digest` drops the summed `waits.human_ms` / `spawns.agent_ms` duplicates and keeps `totals` from `totals.compute` (FR-015). `totals.compute` measures wall clock from `started_at` to `ended_at` or, when absent, to now (FR-016).

**Rationale**: each is the verdict's cited defect with its cited fix.

## R9 — Test and contract hygiene

**Decision**: delete the dead duplicate `LockCliTests` methods after `unittest.main()` in `tools/tests/test_lock.py`; `tools/tests/replay.py` imports `parse_iso`, `TIMELINE_KINDS`, `HISTORY_EVENTS` and the stage vocabularies from `factory_cli.state`; add the `resume <run>` row and the aborted-run wording to `specs/007-stabilise-factory/contracts/cli.md`; record `Overridden: ENG-3 - paired red/implement task structure` in `specs/007-stabilise-factory/plan.md`.

**Rationale**: FR-018–FR-021 and the brief's decisions; one vocabulary source (ENG-6) and one truth per document.

## R10 — Verification approach

**Decision**: no new test dependency or runner: `python3 -m unittest discover -s tools` covers every behaviour change through the seams listed in `plan.md`; the FR-015 acceptance runs `install.sh` under a throwaway `HOME` with `FACTORY_HOME` unset and asserts `git status --porcelain -- dist/` stays empty.

**Rationale**: stdlib-only constraint and the existing suite; the installer seam already runs under a throwaway `HOME`.
