# Contracts: CLI, envelope, benchmark

Phase 1 output. The state CLI is `<F>/bin/factory` (stdlib Python, single writer). Exit codes are unchanged: 0 success; 1 no matching run / refused write with the reason on stderr; 2 not a git repository; 3 ambiguous run name; 4 stale recorded worktree (`show`); 5 usage error.

## New read commands

### `factory budget <role>`

```json
{ "role": "code-build", "seconds": 240, "deadline": "2026-10-27T02:15:00Z" }
```

Resolution order: `${FACTORY_HOME}/config.json` `budget.roles[<role>]` when it is a positive integer, else `budget.default_s` when it is a positive integer, else 300. `deadline` = now + seconds (ISO UTC). `orchestrator` is a valid role (FR-007). Never fails on a missing or malformed config.

### `factory improvements`

```json
{
  "improvements": [
    {
      "name": "claude-factory-010-agent-time-budget",
      "run": "010-agent-time-budget",
      "status": "ready",
      "issues_by_kind": { "overrun": 2 },
      "suggested_feature": "Improve the factory from the recorded issues of run 010-agent-time-budget: 2 overrun(s) ..."
    }
  ]
}
```

Lists every `${FACTORY_HOME}/improvements/*.json`. `suggested_feature` is built from the recorded issues (kind counts and causes); it is text for the user, never started automatically (FR-013).

### `factory improvements claim <name>`

```json
{ "claimed": "claude-factory-010-agent-time-budget", "status": "claimed", "claimed_at": "..." }
```

Refusals (exit 1, message naming the problem or the run): unknown name; status not `ready` (including a second claim); source run discoverable in the current repo and not ended — the message names that run. A successful claim rewrites the backlog file to `"status": "claimed"` with `claimed_at` (FR-012).

## Changed write commands

### `factory issue-add <kind> <stage> <role> --detail <text> --duration-ms <n> [--cause <cause>] [--commit <sha>]`

Appends one issue to `issues[]` (FR-008). `<kind>` ∈ `overrun` | `agent-failure` | `retry` | `halt` | `verify-fail`; `<stage>` in the stage vocabulary; `--cause` is required for `overrun` and must be one of `large-input`, `test-loop`, `retry`, `tool-slow`, `scope-too-big`, `other`, `unreported`; for other kinds it is optional (stored `null`). `retry` records every re-spawn of a stage after a stopped return: a failure-policy retry (FR-010) and a non-deadline `partial` stop (e.g. low context) alike. `--commit` defaults to the worktree HEAD. Refuses an unknown kind/cause or a non-integer duration (exit 1, named reason). For a record that counts toward the stall cap — kind `overrun` or `retry` of a file-writing role (spec-builder, code-build, fixer) — the result carries the stall rule:

```json
{ "added": { "kind": "overrun", "stage": "implement", "role": "code-build" },
  "stalls": { "stage": "implement", "consecutive_no_commit": 2, "cap": 3, "halt": false } }
```

`stalls.consecutive_no_commit` counts trailing `overrun`/`retry` issues of that stage sharing one `commit` — every `partial` return whatever its stop reason counts toward the three (FR-004, grill-with-docs Q1), and so does a failure-policy retry of a resumable role. Records of the never-stopped roles (reviewers, judge, orchestrator) never count, and neither do `agent-failure`, `halt` or `verify-fail`. Any new commit resets the count. `halt: true` at 3 is the orchestrator's instruction to `set-status halted` (FR-004).

Spec alignment: spec FR-008's wording (`--cause` in the signature; records "carry kind, stage, role, cause, detail and duration") predates this contract — this signature's optional `--cause`/`--commit` and the record's `at`/`commit` are the authoritative superset (the `commit` provenance is what makes FR-004 checkable). The spec-side wording update is tracked in plan.md "Spec alignment follow-ups".

### `factory ledger-add <stage> <role> [--started-at ...] [--ended-at ...] [--in-est N] [--out-est N] [--reported '<json>'] [--overrun '<json>']`

Unchanged fields plus `--overrun '<json>'` carrying the role's self-report `{ "cause", "detail" }`. After the ledger entry is appended the writer records **exactly one** issue when either signal holds: `--overrun` present → cause/detail from it; otherwise duration > role budget → `kind: overrun`, `cause: unreported`, detail naming the detected overrun; neither → no issue. The result carries `"issue"` and, for records that count toward the stall cap, `"stalls"` as above (FR-006).

### `factory set-status halted ...` / `factory verify --fail --commands '<json>'`

Gain issue recording inside the writer: `halt` (detail = `--halt-reason`) and `verify-fail` (detail = the failing commands) respectively (FR-010).

### `factory set-status pr-open|aborted ...`

After the state write, exports `${FACTORY_HOME}/improvements/<repo-name>-<branch>.json` atomically (FR-011): run identity and end, `issues[]` verbatim, `factory_cli.totals.compute` output, `factory_sha` (best-effort `git -C <F> rev-parse HEAD`, else `null`), `"status": "ready"`, `exported_at`. Zero-issue runs export too. The result names the exported file.

## Envelope change (`references/protocol.md`)

- `status: "partial"` is valid for all file-writing roles (spec-builder, code-build, fixer), not code-build alone (FR-003).
- A deadline-stopped `partial` carries `overrun: { "cause", "detail" }` with the closed cause list above (the six self-report causes) and the overshoot in `detail` (FR-002). `envelope check` validates `overrun` when present: object, known cause, non-empty detail.

## Benchmark (`tools/bench.py`)

### `tools/bench.py run --harness <h> [--bench <name>] [--home <dir>] [--out <dir>]`

Prepares a throwaway git repo from `conformance/fixture-repo` + `conformance/bench/<name>/overlay/`, seeds `${FACTORY_HOME}/pending/<repo-name>-<slug>.json` from `state-seed.json` (stage `worktree`, `mode.fast: true`, `stop_at: approver`), then drives the headless harness: `claude-code` → `claude -p <prompt>`, `opencode` → `opencode run <prompt>`, anything else refused with a message naming it (FR-014/FR-015/FR-018). The prompt resumes the seeded run; the harness session ends at the approver stop point. No auto-approve flag exists and no PR is opened.

### `tools/bench.py score <state.json>... [--bench <name>]`

Emits the score JSON of `data-model.md` — wall time, agent time, human time, spawns, overruns, issues by kind, token estimates, review rounds, and the four named pass conditions with `pass` (FR-015/FR-016). State is read through `factory_cli.state`/`totals`/`checks` (FR-017). Condition resolution is offline: `reached-approver` (stage `approver`/`pr` or a history entry at `approver`), `last-verify-green` (latest verify record `verify-pass`), `no-blocking-findings` (latest `reviews/round-*/verdict.json` beside the state has `verdict: "pass"`), `fixture-acceptance` (latest verify record runs the bench feature's `acceptance` command with `status: "pass"`). Each unmet or unresolvable condition scores a fail naming itself; the scorer never raises.

### `tools/bench.py compare a.json b.json`

Pairs scores by `run` and prints one line per metric (`metric: a -> b (delta)`), plus the `pass` transition. Exit 0 always; it compares, it does not judge.
