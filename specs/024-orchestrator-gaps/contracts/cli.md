# CLI contract changes

Exit codes follow the existing CLI: 0 success, 1 refusal (nothing written), 2 usage error.

## `factory checkpoint review|fix [...]`

`checkpoint review --next fix --design-fix '<worktree-relative verdict path>'` atomically records the design reservation and fix stage on entry from stored stage `implement`, `verify` or `review`; a retry at stored stage `fix` preserves the existing reservation. The flag is refused when the completed-stage argument is not `review`, the target is not `fix`, or the run has no worktree. After fixer completion and successful verification, `checkpoint fix --next review` counts and clears it atomically, without recounting a legacy reservation. Result for `review` and `fix` adds:

```json
{ "review": { "round": 2, "fix_rounds": 1 } }
```

Also present on the `commit_error` result.

## `factory answer <qid> '<answer>' [--auto] [--stage s] [--cruise-override] [--question '<json>']`

- `--question` (new): protocol question object; `id` must equal `<qid>`, else exit 1.
- `requires_user` question on a worktree run: writes `<spec_dir>/factory/relay/<stage>-<qid>.md`, committed with the answer. Result adds `"record": "<path>"`.
- Existing record, same answer: exit 0, `{"answered": qid, "unchanged": true}`, no write when the record is in HEAD and record and state are clean; otherwise commit the pending state and record.
- Existing record, different answer: exit 1 `relay record <path> already holds a different answer`.
- `<stage>` or `<qid>` outside `[A-Za-z0-9_-]+` with a record due: exit 1.

## `factory budget <role> [--round <n> | --full]`

Result `{ "role", "seconds", "deadline", "full" }`. `--round` not a positive integer: exit 2. Both flags given: exit 2.

## `factory ledger-add <stage> <role> [...] [--round <n> | --full]`

Overrun detection uses the same resolution as `budget`. Detected detail: `<role> ran <excess>s past its <seconds>s budget (<total>s total) without a self-report`.
