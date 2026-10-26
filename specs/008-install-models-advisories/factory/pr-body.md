## Summary

Follow-up to #3. Fixes the unresolved FR-015 install-model blocker from judge round 3, every round-3 advisory, and the open-run wall clock in the totals sentence. Spec: [`specs/008-install-models-advisories/spec.md`](specs/008-install-models-advisories/spec.md).

Install now renders personal models into the factory home and never into the committed `dist/`:

```diff
 ./install.sh --harness <h>
-  render.py <h>                      # merged $FACTORY_HOME/config.json into committed dist/
-  link harness dirs -> dist/<h>
+  guard: config.json parses and has the right shape, else exit non-zero, nothing rendered or linked
+  render.py <h> --out ${FACTORY_HOME:-~/.factory}/dist/<h>   # per-user copy, models merged
+  link harness dirs -> ${FACTORY_HOME:-~/.factory}/dist/<h>
+  --models report reads effective models from the default home
 render.py <h>                        # canonical: never loads user config
```

State CLI hardening (round-3 advisories):

```text
ledger-add   malformed timestamps exit 5 (usage), not a traceback
rebind       writes through write_run (lock + re-read); refuses pr-open/aborted runs
runs/select  ended (aborted) runs skipped, including pending runs
show         digest uses union totals, not summed durations
validate     at most one open relay round, and it is the last one
lock         out-of-range PID treated as live; take --force checks force first;
             release re-checks file identity before unlinking
checkpoint   git commit failure reported explicitly; retry does not duplicate history
totals       open run measures wall clock up to now instead of 0s
```

Also: dead duplicate tests removed from `test_lock.py`, `replay.py` uses the shared `factory_cli.state` vocabulary, `resume <run>` documented in the 007 CLI contract, ENG-3 override recorded in the 007 plan.

## Evidence

- **Before:** each behaviour has a committed failing test (`T001`…`T042` red commits); e.g. `config.json` set to `[]` aborted `./install.sh --harness opencode` with `AttributeError`, and `rebind` rewrote an aborted run's state.
  **After:** `python3 -m unittest discover -s tools` passes 184 tests; build re-renders all five harnesses with no `dist/` diff.

Factory review: round 1 found 2 blocking issues (config shape/parse guard in `config_models`, `rebind` ended-status refusal), both fixed in `6cae624`. Round 2 judge verdict: **pass**, no blocking findings.

Advisory, not fixed (low):
- `commands.py:580`: a first-time successful checkpoint records `commit: null`.
- `totals.py:56`: dead `or started` fallback.
- `commands.py:533`: FR-011 reuse heuristic collapses consecutive same-stage checkpoints when `commit` is None.
- `test_install.py:227`: `InstallHomePolicyTests` duplicates `InstallSandbox` helpers.

## Merge Danger

**Door:** two-way

Revert restores the old install flow. Already-installed users keep a per-user copy under `~/.factory/dist/` until they re-run the old installer.

**Blast Radius:** installer

Install links move from the repo's `dist/` to `${FACTORY_HOME:-~/.factory}/dist/<harness>`; users must re-run `./install.sh` once. A malformed `config.json` now stops the install instead of being ignored or crashing.
