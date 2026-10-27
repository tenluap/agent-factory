# Brief: FR-015 install model pipeline and PR #3 round-3 advisories

Follow-up to run 007 (PR #3, `specs/007-stabilise-factory/`). Fix the unresolved FR-015 blocker from judge round 3, every round-3 advisory, and the open-run wall-clock bug in the totals sentence. Source of findings: `specs/007-stabilise-factory/factory/reviews/round-3/verdict.json`.

## Decisions

- Base: stacked branch from `origin/007-stabilise-factory`; the PR targets `007-stabilise-factory`.
- FR-015: `install.sh` renders a per-user copy into `${FACTORY_HOME:-~/.factory}/dist/<harness>` with `config.json` models merged, and links harness directories from there. The committed `dist/` stays canonical: `render.py` never merges personal config into it. The `--models` report prints effective models read from the default home. A test covers the default-home case. Correct the false `render.py` comment and README/DESIGN wording.
- Medium advisories: `ledger-add` malformed timestamps exit 5 (usage) instead of a traceback; `rebind` writes through `write_run` (lock plus re-read under the lock); ended pending runs are not writable; the `show` digest uses the union totals instead of summed durations; validation enforces exactly one open relay round; an out-of-range lock PID is treated as live and `lock take --force` checks force before liveness.
- Low advisories: delete the dead duplicate tests after `unittest.main()` in `tools/tests/test_lock.py`; `runs` skips aborted runs; `tools/tests/replay.py` imports `parse_iso` and the vocabularies from `factory_cli.state`; add `resume <run>` to `specs/007-stabilise-factory/contracts/cli.md`; `lock.release` re-checks file identity before unlinking; checkpoint reports a git commit failure explicitly and a retry does not silently duplicate history.
- Totals: an open run (no `ended_at`) measures wall clock up to now instead of reporting `0s`.
- STD-24: record `Overridden: ENG-3 - paired red/implement task structure` in `specs/007-stabilise-factory/plan.md`.
- Commands: build re-renders all five harnesses and fails on any `dist/` diff; test is `python3 -m unittest discover -s tools`.
- Chain: lite. Fast mode on.
