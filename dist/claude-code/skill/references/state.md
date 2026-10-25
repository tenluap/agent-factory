# Run state

One run = one `state.json`. It is the single truth for where the run is; read it before acting, write it after every change.

## Location

- **Pending state** (steps 1-4, before the worktree exists): `${FACTORY_HOME:-~/.factory}/pending/<repo-name>-<short-slug>.json`, with `brief.md` beside it as `<same-name>.brief.md`.
- **Run state** (step 4 onward): `<worktree>/specs/<branch>/factory/state.json`, committed with every checkpoint.

The pending file uses this same schema from the moment the run is created: `started_at` is set then, and `relay` and `timeline` capture the grilling rounds too. Step 3 writes both into the run state unchanged.

## Schema

```json
{
  "version": 3,
  "started_at": "2026-10-22T14:00:00Z",
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
  "mode": { "chain": "lite", "fast": true },
  "skills": { "speckit-plan": "/abs/.../SKILL.md", "grilling": "/abs/.../SKILL.md" },
  "commands": { "build": "dotnet build", "test": "dotnet test" },
  "analyze": { "pass": 1, "loops": 0, "reports": ["factory/analyze-1.md"], "remediations": ["factory/remediation-1.md"], "pending_clarify": [] },
  "relay": null,
  "timeline": [],
  "ledger": [ { "at": "2026-10-22T14:02:11Z", "stage": "plan", "role": "spec-builder", "harness": "claude-code", "in_est": 13400, "out_est": 2700, "reported": null, "duration_ms": 92000 } ],
  "review": { "round": 0, "fix_rounds": 0, "ui_diff": false, "ui_reviewer_skipped": false },
  "ended_at": null,
  "pr_url": null,
  "history": [ { "at": "2026-10-21T01:43:00Z", "stage": "specify", "event": "complete", "commit": "abc1234", "harness": "claude-code" } ]
}
```

- `harness`: the adapter running the run now (`harness.md`, `name`). Each `history` entry records the harness that wrote it.
- `skills`: keyed by logical name. Paths are only valid on the harness that resolved them.
- `status`: `running` | `waiting_user` | `paused` | `halted` | `aborted` | `pr-open`.
- `stop_at`: `null`, or the stage the run pauses before (SKILL.md, "Stop point").
- `mode`: the run's chain (`chain`: `full` | `lite`) and whether relays auto-accept their recommended answers (`fast`). A run is created with the default mode — `chain: "lite"`, `fast: true` — unless the command's flags pinned otherwise (SKILL.md, "Route"); a lite→full escalation rewrites `chain` later. A relay answer may carry `"auto": true` (fast mode's auto-accepts); the approver screen lists those rounds.
- `stage`: the stage in progress, or the next one to run: `brainstorm`, `grill`, `worktree`, `specify`, `clarify`, `grill-with-docs`, `plan`, `tasks`, `analyze`, `remediate`, `implement`, `verify`, `review`, `fix`, `approver`, `pr`. `brainstorm` (SKILL.md, "Brainstorm") is additive: it only ever appears on the idea path, before `grill`, and every stage value a run recorded before this value existed still resumes unchanged.
- `relay`: `null`, or every question round of the current stage: `{ "stage": "clarify", "rounds": [ { "questions": [ { "id": "Q1", "text": "...", "recommended": "..." } ], "answers": { "Q1": { "answer": "...", "at": "2026-10-22T14:07:30Z", "auto": false } } } ] }`. Each answer is an object: the user's text, the time it arrived, and `auto: true` when fast mode chose it. The last round is the open one. Write each answer as it arrives (protocol.md, "Relay"). A version 1 state's single batch (`questions` + `answers` at the top of `relay`) is read as one round; a version 2 string answer is read as `{ "answer": <string>, "at": null }`.
  - Question fields and rendering are defined in protocol.md, "Questions". Rich question fields are additive within version 3: accept structured options and legacy string options, retaining saved answers and IDs. Derive progress from each question's stored position in the round; keep the original positions when redisplaying unanswered questions. Accepted new-format answers store the option ID or proposed text, separate from the rationale; legacy recommendations remain verbatim. The optional `requires_user` field (protocol.md, "Questions") is one such additive field: fast mode (protocol.md, "Relay", step 2) must skip a question carrying it, exactly like `pending_clarify`; a question saved without the field keeps today's fast-mode behaviour unchanged.
- `timeline`: every user wait of the run, oldest first (protocol.md, "Timeline"): `{ "at", "kind", "stage", "summary", "answered_at": null, "latency_ms": null }`. `kind` is `questions` (a relay round), `notice` (any other `NOTIFY` that ends the turn), `approver`, or `halt`. Append the entry when the message is shown; when the user answers, set `answered_at` and `latency_ms` (orchestrator clock, shown → answered) in place. Append-only for the whole run: never cleared at checkpoint, never rewritten. A round with several answers closes on its last answer; a wait the run never came back from keeps its nulls.
- `started_at` / `ended_at`: set `started_at` when the run is created; `ended_at` when the run reaches `pr-open` or `aborted`.
- `ledger`: one entry per agent spawn, appended when the spawn returns (each role of a `SPAWN_PARALLEL` gets its own entry): `{ "at", "stage", "role", "harness", "in_est", "out_est", "reported", "duration_ms" }`.
  - `in_est` / `out_est`: word count × 1.35, rounded. Input words: the role file, the resolved skill files the inputs name, and the artifacts the inputs name. Output words: the returned envelope plus files created or modified under `<spec_dir>/factory/` during the spawn (`find <spec_dir>/factory -type f -newermt "<spawn start>" | xargs wc -w`).
  - `reported`: `null`, or `{ "in", "out" }` taken from usage the harness exposes for the spawn (`harness.md` names the source; none exists in tier 1 today).
  - `duration_ms`: orchestrator clock, spawn start to result. Append the entry before the checkpoint so the checkpoint commits it.
- Paths inside `analyze` are relative to `spec_dir`. Timestamps are ISO-8601 UTC.

## Pen design context (additive)

When a run creates, references, or updates a Pen implementation reference, add `design` as defined in [design-code-mapping.md](design-code-mapping.md). It holds only `mode`, context/map/evidence paths, and status; source/node inventory belongs in the canonical map, and detailed checks/decisions in the referenced artifacts. `commands` may add discovered launch/capture commands; the context records their target/configuration. Design-only runs record reasons for any non-applicable application commands/gates rather than inventing an application prerequisite.

Use pending storage before the worktree exists. On worktree creation move context into `<spec_dir>/factory/design/context.json`, update paths, and remove references to the deleted pending files. Persist every returned `design` result before checkpointing. Repository artifact paths are relative to the worktree; externally hosted sources retain their source references and an exported baseline.

This is optional within version 3: version 1/2 and older version-3 states without it remain readable and keep their existing behavior. If a resumed stage actually encounters a Pen reference, activate the contract and bootstrap scoped context/coverage. The read-only CLI already passes small unknown fields through verbatim, including `design`; it does not validate the map or claim fidelity.

Use existing `review.fix_rounds` for all automatic design and other repairs. Before an active-design automatic fixer starts, increment/persist it with `stage: fix` and optional `review.pending_design_fix: { "attempt": 1, "round": 1, "verdict": "specs/016-feature/factory/reviews/round-1/verdict.json" }`. Clear the marker after the attempt completes; a crash/restart continues that reservation with the saved verdict and uncommitted work, not another increment. Neither resume nor the evidence's change of phase resets the limit. Save protected user decisions and explicit scoped exceptions in context/map/evidence as well as relay answers, because checkpoints clear `relay`. Changed source/code/capture identity invalidates affected evidence and exceptions, not the consumed repair counter. Failed/missing gates remain recorded even when the status is `exception-accepted`.

## Totals

The approver screen and the final `NOTIFY` each carry one totals line, computed from the state: total wall clock (`ended_at - started_at`), human wait (sum of `timeline.latency_ms`, with the wait count), agent time (sum of `ledger.duration_ms`, with the spawn count), and the residual (wall clock minus the other two). One shared sentence format, e.g. `Run took 2h 14m: 38m you (12 waits), 1h 12m agents (23 spawns), 24m overhead.`

## Checkpoint

After a stage completes:
1. Set `stage` to the next stage, clear `relay` (`timeline` is never cleared), append a `history` entry (`commit` left `null`, `harness` set).
2. `cd <worktree> && git add -A && git commit -m "factory: <stage> complete"`.

The commit that carries a `history` entry is the entry's commit: `git log --grep "factory: <stage> complete"` finds it. Pending state has no git: just write the file.

## CLI

`<F>/bin/factory` is the skill's read-only state CLI (stdlib Python 3). It does the mechanical state work — discovery and the resume digest — outside the orchestrator's context, so routing never reads a whole `state.json` into it: its token cost stays flat however large `relay`, `timeline`, `ledger` and `history` grow. It writes nothing.

- `python3 <F>/bin/factory runs [--repo <path>]`: "Discovery" as JSON — one entry per unfinished run: `source` (`worktree` | `pending`), `branch` (or `name`), `stage`, `status`, `halt_reason`, `mode`, `feature`, `last_activity`, `state_path`, plus `worktree` and `spec_dir` on worktree runs. A run whose state rides along as a copy in later worktrees appears once.
- `python3 <F>/bin/factory show <branch-or-name> [--repo <path>]`: the "Resume" digest as JSON — every small state field verbatim, and from the large ones only what resume needs: `relay` as the open round's unanswered questions (each with its stored `position`, ready to redisplay), `waits` and `spawns` totals, `totals_sentence` ("Totals"), and `history_tail` (the last three entries). `analyze.pending_clarify` is a count. Everything a restarting agent needs beyond the digest it reads from `state.json` itself.

`<branch-or-name>` is the run's `branch`, or a pending file's name with or without its `<repo-name>-` prefix. Both commands exit non-zero with the reason on stderr (no match, ambiguous name, not a git repo). The orchestrator uses the manual paths below only when the script is missing or Python 3 is not installed.

## Discovery

Unfinished runs of the current repo, produced by `python3 <F>/bin/factory runs` ("CLI"). Its manual equivalent, and the definition of what the script does:

1. `git worktree list --porcelain`; for each worktree, read `specs/*/factory/state.json`. Keep those whose `status` is not `pr-open`; a run whose state appears in several worktrees (copies branched after it) counts once.
2. Pending files in `${FACTORY_HOME:-~/.factory}/pending/` whose `repo` is the current repo.

Show each as: branch (or slug), stage, status, last `history` time.

## Resume

1. `python3 <F>/bin/factory show <branch>` ("CLI"). Work in the digest's `worktree` (pending runs: `repo`). When `harness` differs from this harness: `RESOLVE` every name in `skills` again, set `harness`, and checkpoint before restarting the stage. An open relay's unanswered questions are `relay.unanswered` in the digest, in stored order — redisplay exactly those.
   - For active `design`, read [design-code-mapping.md](design-code-mapping.md), its context and canonical map first. Resolve `pen-design` if absent (and again on harness change), verify source freshness, code anchors, capture configuration, evidence and exception identity, and retain consumed `review.fix_rounds`. Return to invalid checks/decisions before resuming approval or publication; keep valid cached design evidence instead of restarting full discovery. Apply the same activation to a newly encountered Pen reference on an older run.
2. Restart the recorded `stage` from its beginning:
   - Pending `brainstorm`: re-run step 2 (brainstorm) with the existing brief and saved relay answers as the starting point, then continue into step 3 (grill). Redisplay only unanswered questions in the existing open round before recomputing the frontier (protocol.md).
   - Pending `grill`: re-run grilling with the existing brief and saved relay answers as the starting point. Redisplay only unanswered questions in the existing open round before recomputing the frontier (protocol.md).
   - Pending `worktree`: run step 4.
   - Spec stages: `SPAWN` a fresh `spec-builder` with the state and the stage. It reads `relay` from the state: answered questions are settled, the agent asks only the rest.
   - `implement`: `SPAWN` `code-build`; it continues from the tasks.md checkboxes and inspects any uncommitted work.
   - `verify`, `review`, `fix`: for an active design run with `review.pending_design_fix`, resume that saved fixer attempt first using its verdict/context and current uncommitted work, preserving the reservation and failure policy; clear it on completion, then verify/re-review. Otherwise re-run step 6's verify, then step 7 from its first sub-step for the current round.
   - `approver`: show the approver screen again.
   - `pr`: check `gh pr view <branch>` first; an existing PR only needs its URL recorded.
3. `halted` or `aborted`: show `halt_reason` and ask the user how to continue before restarting the stage.
4. `paused`: set `status: running` and start the recorded stage. Flags on the resume command update the state first: `--stop-at <stage>` sets a new `stop_at`, `--lite` / `--full` set `mode.chain`, `--fast` / `--no-fast` set `mode.fast`.
