# Data model: agent time budget, session issue backlog, benchmark

Phase 1 output. Field-level detail lives in `contracts/cli.md`; this file is the entity view (spec, "Key Entities").

## Entities

### Time budget

Seconds allowed per spawned role. Source: `${FACTORY_HOME}/config.json`:

```json
{ "budget": { "default_s": 300, "roles": { "code-build": 240, "orchestrator": 600 } } }
```

- Validation: `default_s` and each role value must be a positive integer; anything else falls back to 300 per entry (never fails the run).
- Expressions: `factory budget <role>` → `{ "role", "seconds", "deadline" }`, `deadline` absolute ISO UTC = now + seconds.
- Relationships: one budget per role per spawn; `orchestrator` is a valid role key for verify timing (FR-007).

### Overrun report

A role's own account of running long, returned on a `partial` envelope:

```json
{ "status": "partial", "overrun": { "cause": "test-loop", "detail": "red test loop, 41s past deadline at unit boundary" }, "summary": "...", "files": [] }
```

- `cause` closed list: `large-input`, `test-loop`, `retry`, `tool-slow`, `scope-too-big`, `other`.
- `detail` free text; it carries the overshoot past the deadline (FR-002).
- Transitions: the report is consumed by `ledger-add --overrun` and becomes one session issue.

### Session issue

Append-only record of one thing that went wrong, in `state.json` `issues[]` (schema **v5**):

```json
{
  "at": "2026-10-27T02:10:00Z",
  "kind": "overrun",
  "stage": "implement",
  "role": "code-build",
  "cause": "test-loop",
  "detail": "red test loop, 41s past deadline at unit boundary",
  "duration_ms": 341000,
  "commit": "abc1234",
  "partial_return": true
}
```

- `kind` closed: `overrun`, `agent-failure`, `retry`, `halt`, `verify-fail`.
- `cause` is `null` for kinds other than `overrun`; for `overrun` it is required and comes from the six self-report causes plus `unreported` (detected only).
- `duration_ms` the measured duration the issue is about; `commit` the worktree's last work commit (latest non-`factory:` commit) at record time (null where no worktree applies), the provenance behind the stall rule.
- `partial_return` is `true` exactly when the record documents a `partial` return's stop (whatever its stop reason), `false` otherwise: failure-policy retries, post-hoc detections and the `agent-failure`/`halt`/`verify-fail` kinds are never partial returns. The mark is stamped by `issue-add --partial-return` / `ledger-add --partial-return`, accepted only for kinds `overrun`/`retry` of the file-writing roles (spec-builder, code-build, fixer); the writer refuses it otherwise.
- Validation: kinds/causes are closed vocabularies with the offending location named; `issues[]` is append-only (the writer only appends; FR-008).
- Relationships: one issue per event (dedupe is structural in `ledger-add`); three consecutive records marked `partial_return: true` of one stage sharing one `commit` are three stalled returns → halt (FR-004). Every `partial` return whatever its stop reason counts; a failure-policy retry is not a partial return and never counts; records of the never-stopped roles (reviewers, judge, orchestrator) never carry the mark.

### Improvement backlog

Run-end export, `${FACTORY_HOME}/improvements/<repo-name>-<branch>.json`:

```json
{
  "name": "claude-factory-010-agent-time-budget",
  "run": { "branch": "...", "spec_dir": "...", "worktree": "...", "status": "pr-open", "ended_at": "..." },
  "issues": [ /* the run's issues[] verbatim */ ],
  "totals": { /* factory_cli.totals.compute output */ },
  "factory_sha": "abc123 or null",
  "status": "ready",
  "exported_at": "...",
  "claimed_at": null
}
```

- Transitions: `ready` (written once at `set-status pr-open|aborted`) → `claimed` (`factory improvements claim`, stamped `claimed_at`); nothing else writes the file.
- Validation: the file never exists before its run ends (structural gate); `claim` re-checks the discoverable source run's end and refuses missing, non-`ready`, or not-ended cases with a message naming the problem or the run.

### Partial return

A file-writing role's (spec-builder, code-build, fixer) stopped-but-committed result: `status: "partial"` with `summary` naming the resume point and, for a deadline stop, an `overrun` report. Consumed by the orchestrator as a re-spawn instruction. Every partial return is recorded as exactly one issue — a deadline stop as `overrun` (cause from the self-report, `unreported` when the report is missing), any other stop reason (e.g. low context) as `retry` — each marked `partial_return: true`, and the stall rule reads only marked records. A failure-policy retry is not a partial return: its `retry` record is unmarked and never counts.

### Benchmark score

One run's measured outcome, emitted by `tools/bench.py score`:

```json
{
  "bench": "greet-001",
  "scores": [
    {
      "state": "path/to/state.json",
      "run": "010-...",
      "metrics": {
        "wall_ms": 0, "agent_ms": 0, "human_ms": 0,
        "spawns": 0, "overruns": 0,
        "issues_by_kind": { "overrun": 0, "agent-failure": 0, "retry": 0, "halt": 0, "verify-fail": 0 },
        "tokens": { "in_est": 0, "out_est": 0, "reported": null },
        "review_rounds": 0, "fix_rounds": 0
      },
      "conditions": {
        "reached-approver": { "met": true, "detail": "..." },
        "last-verify-green": { "met": true, "detail": "..." },
        "no-blocking-findings": { "met": true, "detail": "..." },
        "fixture-acceptance": { "met": true, "detail": "..." }
      },
      "pass": true
    }
  ]
}
```

- `pass` is true only when all four conditions are met; a missing condition is a fail that names itself (FR-016).
- `compare a.json b.json` pairs scores by `run` and prints per-metric deltas.

## State schema change (v5)

- `version: 5`; readers accept 1–5; first write upgrades in the same atomic write.
- New top-level field: `issues[]` only. Every v4 key keeps its name and shape — the additive shape that keeps readers predating this feature working (SC-002).
- No state transition changes: `history` events, statuses, stages keep their closed vocabularies; issue recording rides existing writer commands (`issue-add`, `ledger-add`, `set-status halted`, `verify --fail`).
