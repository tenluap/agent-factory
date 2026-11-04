# Data model: Adopt a spec started outside factory

State stays `version: 5`; every addition is optional and additive (SC-004).

## `adopted` block

Written only by `factory adopt`:

```json
"adopted": {
  "source": { "shape": "branch", "branch": "007-x", "spec_dir": "specs/007-x" },
  "inferred_stage": "tasks",
  "chosen_stage": "plan",
  "base_commit": "<40-hex sha of the branch HEAD at the write>"
}
```

Validation (`state.py`, `_check_adopted`), only when the block is present:

- object;
- `source.shape` in `ADOPT_SHAPES = ("branch", "remote-branch", "default-branch")`;
- `source.branch` and `source.spec_dir` non-empty strings;
- `inferred_stage` and `chosen_stage` in `ADOPT_STAGES = ("specify", "plan", "tasks", "analyze")`;
- `base_commit` a 40-character lowercase hex string.

## `adopted` history entry

`HISTORY_EVENTS` gains `adopted`. The adopt write appends exactly one entry:

```json
{ "at": "<now>", "stage": "<chosen_stage>", "event": "adopted", "commit": null, "harness": "<harness>" }
```

`commit` is `null` as on `complete` entries (the sha does not exist until the commit). An `adopted` history entry requires the `adopted` block. No rule requires `complete` entries before the chosen stage (FR-017, held by test).

## Pending adoption run

`${FACTORY_HOME:-~/.factory}/pending/<repo-name>-adopt-<branch>.json`, with `.brief.md` and `.profile.md` beside it; same schema as any pending run, plus `branch` and `spec_dir` from the dry-run report and `feature` = the spec's title. Lifecycle: created after a clean dry-run; reused on retry; replaced when `aborted`; deleted by a successful write.

## Pre-adoption sets (derived, not stored)

- Pre-adoption commits: `git rev-list <base>..<adopted.base_commit>`.
- Pre-adoption tasks: task IDs checked in `git show <adopted.base_commit>:<spec_dir>/tasks.md`.
