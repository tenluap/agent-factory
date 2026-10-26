# Contract delta: CLI and installer after `008-install-models-advisories`

Phase 1 for `008-install-models-advisories`. The base contract is `specs/007-stabilise-factory/contracts/cli.md`; the rows below are the only ones this run changes or adds. Exit-code table unchanged (0 success, 1 refused, 2 git, 3 ambiguous, 4 missing worktree, 5 usage).

## `bin/factory` rows

| Command | Change |
|---|---|
| `ledger-add ... [--started-at <iso>] [--ended-at <iso>]` | a malformed or non-string timestamp exits **5** naming the offending value; no traceback (FR-007) |
| `runs [--repo <path>]` | lists unfinished runs only: `pr-open` **and `aborted`** are skipped, since resume refuses them (FR-017) |
| `show <run> [--repo <path>]` | the digest's elapsed aggregates come from `totals`; the summed `waits.human_ms` / `spawns.agent_ms` duplicates are removed; for an open run the totals sentence shows wall clock from start to now, never `0s` (FR-015, FR-016) |
| `validate <run> [--all]` | additionally reports a relay holding zero or several open rounds, at `relay` / `relay.rounds[i]` (FR-010) |
| `checkpoint <stage> ...` | when the git commit fails after the state write, the command exits **1** with `state written, commit failed: <reason>`; its JSON result carries `commit: null` and `commit_error`; a retry reuses the pending history entry and does not duplicate it (FR-011) |
| `rebind <run> --worktree <path>` | rewrites through the single writer: run lock held, state re-read under the lock (FR-008) |
| `resume <run>` | **new row** (documented in `specs/007-stabilise-factory/contracts/cli.md`): records a `resumed` history entry through the writer, clears `halt_reason`, sets `status: running`, returns the resume digest; refuses a `pr-open` or `aborted` run (FR-020) |
| write commands generally | an ended run (including a **pending** one) is never writable (FR-009) |
| `lock take <run> [--force]` | `--force` takes over regardless of holder liveness; without it a live lock — including one whose owner PID cannot be evaluated — refuses with the owner reported (FR-012, FR-013) |
| `lock release` (internal) | unlinks only the lock file whose identity was just read; a foreign lock stays (FR-014) |

## `tools/render.py` surface

| Invocation | Behaviour |
|---|---|
| `render.py <harness>` | canonical render into `dist/<harness>`; **never** reads `config.json` (FR-002) |
| `render.py <harness> --out <dir>` | per-user render into `<dir>` with `${FACTORY_HOME:-~/.factory}/config.json` models merged per key over adapter defaults (FR-001, FR-003) |
| `render.py <harness> --models` | report only, writes nothing: effective model per role resolved from the default home (FR-004) |
| `render.py <harness> --paths` | report only, writes nothing: `dist`, `skill_dir`, `agent_dir` |
| `render.py --list` | unchanged |

## `install.sh` surface

| Invocation | Behaviour |
|---|---|
| `./install.sh [--harness <name>\|all]` | renders each harness into `${FACTORY_HOME:-~/.factory}/dist/<harness>` with the user's models merged, links `skill/` and `agents/*` from that per-user copy, prints the effective-model report; never renders or dirties the committed rendered distribution (FR-001–FR-005) |
| `./install.sh --uninstall` | removes the links it created and the per-user render `${FACTORY_HOME:-~/.factory}/dist/<harness>`; `config.json`, pending runs and the committed rendered distribution are untouched (FR-001) |
| failure | a missing default home `~/.factory` is created; an explicitly set `FACTORY_HOME` that does not exist, or any home that is not a directory or is not writable, fails with a message naming the path, writing nothing (FR-001) |
