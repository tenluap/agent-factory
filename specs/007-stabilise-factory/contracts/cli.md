# Contract: `bin/factory` CLI

Phase 1 output for `007-stabilise-factory`. Invocation: `python3 <F>/bin/factory <command> ...` (stdlib Python 3). Every command exits `0` on success and non-zero with the reason on stderr otherwise. JSON output is UTF-8, printed to stdout. The thin entry script delegates to `factory_cli`; `dist/<harness>/skill/bin/` carries the same surface on every harness.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | success |
| 1 | no matching run / refused write (gate, lock, validation) with the reason named |
| 2 | not a git repository, or `git` not runnable |
| 3 | ambiguous run name |
| 4 | the run's recorded worktree no longer exists |
| 5 | usage error (unknown command, missing or invalid argument value) |

## Read commands

| Command | Output (JSON) | Notes |
|---|---|---|
| `runs [--repo <path>]` | discovery list | one entry per unfinished run; reports lock and validation violations instead of hiding them |
| `show <run> [--repo <path>]` | resume digest | scalars plus aggregates, `relay.unanswered`, `decisions` (the approver's veto list), `waits`, `spawns`, `totals_sentence`, `history_tail`; never the whole state |
| `validate <run> [--all]` | violation list | each violation: `location`, `reason`; exit 1 when any is found (S2, FR-003) |

## Write commands (the single writer, FR-001)

Each stamps its own time, validates before writing, writes atomically (temp + rename), and refuses under a live lock. A run is upgraded to version 4 in the same write.

| Command | Effect |
|---|---|
| `checkpoint <stage> [--files <path>...] [--envelope <file>]` | gate check for the transition, then: append the `complete` history entry, set the next stage, move the stage's settled relay answers into `decisions` before clearing `relay` (FR-008), commit `spec_dir` + exactly the declared files as `factory: <stage> complete`, report any other dirty path without committing it (FR-017) |
| `verify --pass\|--fail --commands '<json>'` | append the verify record (`verify-pass` / `verify-fail`, FR-006) |
| `ledger-add <stage> <role> [--started-at <iso>] [--ended-at <iso>] [--in-est N] [--out-est N] [--reported '<json>']` | append one spawn interval (FR-009); `reported` labelled separately from estimates (FR-010) |
| `wait-open <kind> <stage> <summary>` → `wait-id` | append an open timeline entry (`kind` ∈ `questions\|notice\|approver\|halt`) |
| `wait-close <wait-id>` | set `answered_at` and `latency_ms` in place |
| `answer <qid> '<answer>' [--auto] [--stage <stage>]` | write one settled answer into the open relay round (`auto` marks fast-mode acceptance) |
| `set-status <status> [--halt-reason <text>] [--pr-url <url>]` | record a status change (`halted` carries its reason; `pr-open` its URL and `ended_at`) |
| `decisions-add <stage> <qid> '<answer>' [--kind answer\|gate-override]` | append a decision record entry directly (gate overrides use `--kind gate-override`, `auto` false) |

## Gate and output checks

| Command | Behaviour |
|---|---|
| `checkpoint ...` (gate table) | refuses → `review` without a passing latest verify record, → `implement` without analyze clean/remediated/overridden, → `pr` without a recorded approval; names the missing record (FR-006) |
| `envelope check <file>` | validates the final fenced `json` block against the envelope (protocol.md), reviewer report and judge verdict shapes (findings.md); exit 1 with the offending location on malformed output (FR-007) |

## Lock

| Command | Behaviour |
|---|---|
| `lock take <run> [--force]` | the only takeover path; records `taken_over` and the previous lock; refuses without `--force` when the lock is live |

All write commands acquire the run's lock for the duration of the write and release it; a live foreign lock refuses with the owner reported (FR-005).

## Portability and maintenance

| Command | Behaviour |
|---|---|
| `rebind <run> --worktree <path>` | validates the path is a git worktree on the recorded branch, rewrites stored absolute paths (`worktree`, `repo`), reports the rewrite (FR-012) |
| `prune [--dry-run\|--delete]` | lists stale pending files (run has a worktree state or ended `pr-open`/`aborted`; a run whose only state is the pending file is never stale); deletes nothing without `--delete` (FR-019) |

## Non-goals

No command edits `dist/`, no command merges or pushes, no command deletes a worktree (brief §6). A missing Python 3 or a missing `bin/factory` halts the run with a clear message; there is no manual write fallback (FR-002).
