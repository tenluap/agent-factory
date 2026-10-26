# Data model: Install model pipeline and round-3 advisory fixes

Phase 1 for `008-install-models-advisories`. **No state schema change**: run `state.json` stays at version 4 with its existing vocabularies (`specs/007-stabilise-factory/data-model.md`, `core/skills/factory/references/state.md`). This feature changes who writes what, and one rule about counting.

## Entities

### Per-user render (`${FACTORY_HOME:-~/.factory}/dist/<harness>`)

- A full harness tree (`skill/`, `agents/`) rendered at install time with the user's model overrides merged.
- Owner: `install.sh` via `tools/render.py <harness> --out <dir>`; disposable and re-created on every install; removed with the links by `--uninstall`, which leaves `config.json`, pending runs and the committed rendered distribution untouched.
- Validation: a missing default home `~/.factory` is created (`mkdir -p`, as today); an explicitly set `FACTORY_HOME` that does not exist, or any home that is not a directory or not writable, fails the install naming the path and writes nothing to the repository; a `config.json` that does not parse aborts the install before any render or link — message naming the file and the parse error, non-zero exit, nothing rendered or linked (FR-022).

### Committed rendered distribution (`dist/<harness>`)

- The canonical, machine-independent render; produced only by `tools/render.py <harness>` and the build gate.
- Invariant (FR-002): it never contains a personal model id, and no installer run rewrites or dirties it.

### Effective model report

- Per-role model list = adapter defaults merged (per key) with `${FACTORY_HOME:-~/.factory}/config.json` `models.<harness>`, printed by `render.py <harness> --models`.
- Invariant (FR-004): it equals what the linked agents carry; printing it writes nothing.

### Run lock

- Fields unchanged (`owner_pid`, `host`, `harness`, `at`, `taken_over`, `previous`).
- Rule changed (FR-012–FR-014): liveness is a judgment — an owner PID the OS probe cannot evaluate (wrong type, out of range) counts as **live**; `lock take --force` is evaluated before liveness; `release` unlinks only the file whose identity (`st_dev`, `st_ino`) it just read.

### Relay rounds

- Shape unchanged (`relay.rounds[]`, each `questions[]` with `answers`; version 1: one batch).
- Definition (glossary): an **open relay round** holds at least one unanswered question, awaiting the user's answers.
- New validation rule (FR-010, clarified 2026-10-26): at most one round is open and an open round must be the last; a null relay and a fully answered relay awaiting checkpoint are conformant and report no anomaly. Several open rounds are a violation reported at `relay`; unanswered questions in a non-last round at `relay.rounds[i]`.

### Checkpoint history entry

- Shape unchanged: `{at, stage, event, commit, harness}` with the closed vocabulary.
- New retry rule (FR-011): when the git commit at a checkpoint fails, the entry is written with `commit: null`; a retry of the same stage reuses that pending entry (stamping its own `at` and filling `commit` with the new SHA) instead of appending a second one. The command result distinguishes `commit: <sha>` from `commit: null, commit_error: <reason>`.

### Ledger entry

- Shape unchanged. Input rule (FR-007): `started_at` / `ended_at` must parse as ISO-8601 UTC; a malformed value is a usage error (exit 5) naming the value and never reaches the duration arithmetic.

### Totals

- Fields unchanged (`bounded`, `wall_ms`, `human_ms`, `agent_ms`, `overhead_ms`, waits, spawns, usage estimates).
- Rule changed (FR-016): for an open run (`ended_at` absent) wall clock runs from `started_at` to now; `bounded` stays true whenever `started_at` exists.
- Rule changed (FR-015): the `show` digest carries only the union-based totals; the summed `waits.human_ms` and `spawns.agent_ms` duplicates are gone.

## State transitions

None. Command vocabularies, stages and history events are unchanged; ended runs (`pr-open`, `aborted`) are already immutable and the skip is extended to pending-run selection (FR-009).
