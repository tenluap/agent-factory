# Run state

One run = one `state.json`. It is the single truth for where the run is; read it before acting, write it after every change.

## Location

- **Pending state** (steps 1-3, before the worktree exists): `${FACTORY_HOME:-~/.factory}/pending/<repo-name>-<short-slug>.json`, with `brief.md` beside it as `<same-name>.brief.md`.
- **Run state** (step 3 onward): `<worktree>/specs/<branch>/factory/state.json`, committed with every checkpoint.

## Schema

```json
{
  "version": 2,
  "harness": "claude-code",
  "feature": "the user's feature text",
  "repo": "/abs/path/to/main/checkout",
  "default_branch": "main",
  "base": "origin/main",
  "branch": "016-short-name",
  "worktree": "/abs/path/to/repo-factory/016-short-name",
  "spec_dir": "specs/016-short-name",
  "status": "running",
  "stage": "plan",
  "halt_reason": null,
  "stop_at": null,
  "mode": { "chain": "full", "fast": false },
  "skills": { "speckit-plan": "/abs/.../SKILL.md", "grilling": "/abs/.../SKILL.md" },
  "commands": { "build": "dotnet build", "test": "dotnet test" },
  "analyze": { "pass": 1, "loops": 0, "reports": ["factory/analyze-1.md"], "remediations": ["factory/remediation-1.md"], "pending_clarify": [] },
  "relay": null,
  "ledger": [ { "at": "2026-10-22T14:02:11Z", "stage": "plan", "role": "spec-builder", "harness": "claude-code", "in_est": 13400, "out_est": 2700, "reported": null, "duration_ms": 92000 } ],
  "review": { "round": 0, "fix_rounds": 0, "ui_diff": false, "ui_reviewer_skipped": false },
  "pr_url": null,
  "history": [ { "at": "2026-10-21T01:43:00Z", "stage": "specify", "event": "complete", "commit": "abc1234", "harness": "claude-code" } ]
}
```

- `harness`: the adapter running the run now (`harness.md`, `name`). Each `history` entry records the harness that wrote it.
- `skills`: keyed by logical name. Paths are only valid on the harness that resolved them.
- `status`: `running` | `waiting_user` | `paused` | `halted` | `aborted` | `pr-open`.
- `stop_at`: `null`, or the stage the run pauses before (SKILL.md, "Stop point").
- `mode`: the run's chain (`chain`: `full` | `lite`) and whether relays auto-accept their recommended answers (`fast`). A relay answer may carry `"auto": true` (fast mode's auto-accepts); the approver screen lists those rounds.
- `stage`: the stage in progress, or the next one to run: `grill`, `worktree`, `specify`, `clarify`, `grill-with-docs`, `plan`, `tasks`, `analyze`, `remediate`, `implement`, `verify`, `review`, `fix`, `approver`, `pr`.
- `relay`: `null`, or every question round of the current stage: `{ "stage": "clarify", "rounds": [ { "questions": [ { "id": "Q1", "text": "...", "recommended": "..." } ], "answers": { "Q1": "..." } } ] }`. The last round is the open one. Write each answer as it arrives. A version 1 state's single batch (`questions` + `answers` at the top of `relay`) is read as one round.
- `ledger`: one entry per agent spawn, appended when the spawn returns (each role of a `SPAWN_PARALLEL` gets its own entry): `{ "at", "stage", "role", "harness", "in_est", "out_est", "reported", "duration_ms" }`.
  - `in_est` / `out_est`: word count × 1.35, rounded. Input words: the role file, the resolved skill files the inputs name, and the artifacts the inputs name. Output words: the returned envelope plus files created or modified under `<spec_dir>/factory/` during the spawn (`find <spec_dir>/factory -type f -newermt "<spawn start>" | xargs wc -w`).
  - `reported`: `null`, or `{ "in", "out" }` taken from usage the harness exposes for the spawn (`harness.md` names the source; none exists in tier 1 today).
  - `duration_ms`: orchestrator clock, spawn start to result. Append the entry before the checkpoint so the checkpoint commits it.
- Paths inside `analyze` are relative to `spec_dir`. Timestamps are ISO-8601 UTC.

## Checkpoint

After a stage completes:
1. Set `stage` to the next stage, clear `relay`, append a `history` entry (`commit` left `null`, `harness` set).
2. `cd <worktree> && git add -A && git commit -m "factory: <stage> complete"`.

The commit that carries a `history` entry is the entry's commit: `git log --grep "factory: <stage> complete"` finds it. Pending state has no git: just write the file.

## Discovery

Unfinished runs of the current repo:
1. `git worktree list --porcelain`; for each worktree, read `specs/*/factory/state.json`. Keep those whose `status` is not `pr-open`.
2. Pending files in `${FACTORY_HOME:-~/.factory}/pending/` whose `repo` is the current repo.

Show each as: branch (or slug), stage, status, last `history` time.

## Resume

1. Read the state. Work in `worktree` (pending runs: `repo`). When `state.harness` differs from this harness: `RESOLVE` every name in `skills` again, set `harness`, and checkpoint before restarting the stage.
2. Restart the recorded `stage` from its beginning:
   - Pending `grill`: re-run grilling, offering the existing brief as the starting point.
   - Pending `worktree`: run step 3.
   - Spec stages: `SPAWN` a fresh `spec-builder` with the state and the stage. It reads `relay` from the state: answered questions are settled, the agent asks only the rest.
   - `implement`: `SPAWN` `code-build`; it continues from the tasks.md checkboxes and inspects any uncommitted work.
   - `verify`, `review`, `fix`: re-run step 5's verify, then step 6 from its first sub-step for the current round.
   - `approver`: show the approver screen again.
   - `pr`: check `gh pr view <branch>` first; an existing PR only needs its URL recorded.
3. `halted` or `aborted`: show `halt_reason` and ask the user how to continue before restarting the stage.
4. `paused`: set `status: running` and start the recorded stage. A `--stop-at` on the resume command sets a new `stop_at`.
