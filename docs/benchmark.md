# Benchmark factory versions

The `greet-001` fixture adds optional uppercase greetings to the small existing
Python greeting module. Its brief, acceptance cases and seed live under
`conformance/bench/greet-001/`. Use the same fixture and harness for both versions.
Install the version being measured before each replay; the driver uses the
installed factory skill, not an implicit install from this checkout.

## Headless replay (manual, token-costing)

From the factory checkout:

```sh
python3 tools/bench.py run --harness opencode --bench greet-001
# Or: --harness claude-code
# Optional: --home <isolated-factory-home> --out <new-output-directory>
```

The driver creates a disposable git repository, copies the existing SpecKit
scripts/templates and fixture overlay, seeds a fast/lite pending run at
`worktree`, and invokes `opencode run` or `claude -p` with its resume prompt.
Its local origin points to itself, so fetching the fixture base needs no network.
Required skills must already be installed. Unsupported or missing headless
commands are refused by name, with exit 1. An existing output directory is refused.

Output names the repository, factory home, pending state and harness log.
The pending file may move into a worktree during replay. Locate the final state
under the sibling `*-factory/` worktree directory. Check the harness log if the
run stops early. A successful harness process exit is not a successful score.
The automated suite tests recorded scores only; it never spends model tokens.

## Manual fallback (any supported factory harness)

When headless execution is unavailable, prepare a fixture copy from the factory
checkout. These commands create only a throwaway repository:

```sh
bench=$(mktemp -d "${TMPDIR:-/tmp}/factory-bench.XXXXXX")
cp -R conformance/fixture-repo "$bench/repo"
cp -R conformance/bench/greet-001/overlay/. "$bench/repo/"
cp conformance/bench/greet-001/brief.md "$bench/repo/BENCHMARK.md"
cp -R .specify/scripts .specify/templates "$bench/repo/.specify/"
git -C "$bench/repo" init -b main
git -C "$bench/repo" add -A
git -C "$bench/repo" -c user.name='Factory Benchmark' \
  -c user.email=benchmark@example.invalid commit -m 'Benchmark fixture baseline'
git -C "$bench/repo" remote add origin "$bench/repo"
git -C "$bench/repo" fetch origin main
```

Open the installed harness in `$bench/repo`. Set an isolated `FACTORY_HOME` if
desired. Start `/factory` (or that harness's factory invocation) with:

```text
/factory Implement the settled feature in BENCHMARK.md; preserve its acceptance tests and record the acceptance command separately in verify. Use local origin/main. --lite --fast --stop-at approver
```

Answer any required protected confirmations explicitly; fast mode does not
approve them. Stop before approver, without approval or a PR. Score the resulting
worktree's `specs/<branch>/factory/state.json` using the factory checkout's tool.

## Offline score and comparison

```sh
python3 tools/bench.py score <before-state.json> --bench greet-001 > before.json
python3 tools/bench.py score <after-state.json> --bench greet-001 > after.json
python3 tools/bench.py compare before.json after.json
```

Each score includes wall/agent/human milliseconds, spawn and overrun counts,
issues by kind, estimated/reported token usage, and review/fix rounds. Time and
usage come from the shared state reader and interval-union totals implementation.
An unfinished run's wall time uses the shared totals reader's current-time rule.

The four named conditions are:

- `reached-approver`: current stage is approver/PR, or history records approver.
- `last-verify-green`: the latest verify event is `verify-pass`.
- `no-blocking-findings`: the latest numeric review round's `verdict.json` says
  `pass` with no confirmed blocking findings.
- `fixture-acceptance`: the latest verify command list records
  `python3 -m unittest test_acceptance` as passing (`pass` or exit status `0`).

Missing or unreadable evidence fails by condition name. Scoring is offline: it
does not rerun acceptance or infer green from a harness exit. `score` reports
failure in JSON, not its process exit status. `compare` pairs by run, reports
unpaired runs, prints each metric delta and pass transition, and exits 0; inspect
the result instead of treating its exit status as a quality gate.

Implementation validation: offline recorded-state tests and a manual external-CLI
double checked replay preparation/dispatch. No live model replay is claimed by
that smoke check. Run the token-costing path above to measure an installed version.
