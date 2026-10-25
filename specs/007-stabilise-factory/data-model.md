# Data model: run state, records and locks

Phase 1 output for `007-stabilise-factory`. The machine contract is `contracts/cli.md`; the narrative schema remains `core/skills/factory/references/state.md` (updated to version 4 by this change).

## Entities

### Run state (`state.json`)

One run = one file. Location: `${FACTORY_HOME:-~/.factory}/pending/<repo-name>-<short-slug>.json` before the worktree exists, then `<worktree>/specs/<branch>/factory/state.json`.

| Field | Type | Notes |
|---|---|---|
| `version` | int | `4` on write; readers accept 1–4 (FR-022) |
| `started_at`, `ended_at` | ISO-8601 UTC or null | `ended_at` set at `pr-open` / `aborted` |
| `harness` | string | adapter `name` running the run now |
| `feature`, `repo`, `default_branch`, `base`, `branch`, `worktree`, `spec_dir` | string | absolute machine paths; rewritten only by `rebind` |
| `status` | enum | `running` \| `waiting_user` \| `paused` \| `halted` \| `aborted` \| `pr-open` |
| `stage` | enum | `brainstorm`, `grill`, `worktree`, `specify`, `clarify`, `grill-with-docs`, `plan`, `tasks`, `analyze`, `remediate`, `implement`, `verify`, `review`, `fix`, `approver`, `pr` |
| `halt_reason`, `stop_at` | string or null | `stop_at` is a stage name or null |
| `mode` | object | `chain`: `full`\|`lite`; `fast`: bool |
| `skills`, `commands` | object | resolved paths / build+test commands |
| `analyze` | object | `pass`, `loops`, `reports`, `remediations`, `pending_clarify` |
| `relay` | object or null | current stage's question rounds (see below) |
| `timeline` | list | user waits, append-only (FR-009) |
| `decisions` | list | **v4**: settled answers, append-only (FR-008) |
| `ledger` | list | spawn intervals, one per spawn (FR-009) |
| `review` | object | `round`, `fix_rounds`, `ui_diff`, `ui_reviewer_skipped`, optional `pending_design_fix` |
| `history` | list | transition records, append-only (FR-003) |
| `pr_url` | string or null | set at PR |
| `design` | object, optional | unchanged additive Pen context (`design-code-mapping.md`) |

### Transition record (`history[]`)

`{ "at", "stage", "event", "commit", "harness" }`. `event` is closed (FR-003): `complete`, `verify-pass`, `verify-fail`, `approved`, `gate-override`, `aborted`, `pr-open`, `resumed`. Anything else is a validation violation with its location. `commit` is the checkpoint commit or null.

### Verify record

A history entry with `event: "verify-pass"` or `"verify-fail"` and `commands: [ { "command", "status" } ]`, written only by `factory verify` after the orchestrator re-runs build and test. The review gate reads the latest verify entry; only `verify-pass` satisfies it (research R3).

### Decision record (`decisions[]`, v4)

`{ "stage", "question", "answer", "auto", "at", "kind" }` — `kind` is `answer` (a settled relay answer) or `gate-override` (an explicit override of a gate). Append-only; written before the stage's `relay` is cleared (FR-008). The approver's veto list is every `auto: true` entry plus every `gate-override` entry (FR-006).

### Spawn interval (`ledger[]`)

`{ "at", "stage", "role", "harness", "in_est", "out_est", "reported", "duration_ms", "started_at", "ended_at" }` — `started_at`/`ended_at` new in v4 (FR-009); `duration_ms` kept and derived from them on write. `reported` is `null` or `{ "in", "out" }`, always labelled separately from the estimates (FR-010).

### User wait (`timeline[]`)

`{ "at", "kind", "stage", "summary", "answered_at", "latency_ms" }`, `kind` ∈ `questions | notice | approver | halt`. `at` → `answered_at` is the wait interval feeding human time.

### Run lock (`lock.json`)

Beside the state file it guards (worktree run) or beside the pending file (pending run). `{ "owner_pid", "host", "harness", "at", "taken_over": bool, "previous": <lock or null> }`. Stale only on its recorded host with the owner process gone; elsewhere never automatically; `lock take` sets `taken_over: true` and keeps `previous` for audit (FR-005).

### Adapter configuration

`adapters/<h>/adapter.json` `models` (shipped defaults: only `claude-code` non-empty) merged with `${FACTORY_HOME}/config.json` `models.<harness>` at render/install time; effective value printable per role (FR-015).

### Conformance fixture and golden-run result

`conformance/fixture-repo/` (files plus init instructions), `conformance/golden-run/<harness>.md` (checklist per adapter), `conformance/golden-run-results.md` (recorded per adapter and capability tier; live two-harness run recorded after merge).

## Validation rules (enforced before every write and by `validate`)

1. JSON object; `version` in 1–4 (FR-022).
2. Enumerations above: `status`, `stage`, `timeline.kind`, `history.event`; violation reported with the field's location.
3. Required fields per stage (a run at `implement` and later carries `commands`; a `pr-open` run carries `pr_url` and `ended_at`, …).
4. Timestamps parse as ISO-8601 UTC and never decrease within a record: `history`, `timeline`, `ledger`, `decisions` lists are non-decreasing by `at`; `latency_ms`, `duration_ms` ≥ 0; `ended_at` ≥ `started_at` (FR-004).
5. Exactly one open relay round; every `answers` key matches a question `id` in the same round.
6. `decisions` entries well-formed and never rewritten (compare against the previous file on write).
7. Legacy tolerance on read: version 1 relay batch, version 2 string answers, missing `decisions`/lock — reported as accepted-and-legacy, upgraded on the first write.

## State transitions

```text
create pending → brainstorm|grill → worktree → specify → [clarify → grill-with-docs] → plan → tasks → analyze
analyze → remediate → analyze (≤2 loops) | implement
implement → verify → review ⇄ fix (≤2 rounds) → approver
approver → pr | fix (request changes) | aborted
any stage → halted (halt_reason) → the recorded stage on user answer
```

Gates on the transition that would record the next stage (FR-006, checked by `checkpoint`):

| Into | Requires |
|---|---|
| `review` | latest verify record is `verify-pass` |
| `implement` | analyze clean, remediated, or a `gate-override` decision |
| `pr` | an `approved` decision recorded at `approver` (or a `gate-override` decision) |
| any write | no live lock by another owner |

Illegal transitions are refused with the missing record named; the refusal is a test case (SC-005).
