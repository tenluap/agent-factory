# Run state

One run = one `state.json`. It is the single truth for where the run is; read it before acting, and write it only through the CLI's write commands ("CLI") — never by hand.

## Location

- **Pending state** (steps 1-4, before the worktree exists): `${FACTORY_HOME:-~/.factory}/pending/<repo-name>-<short-slug>.json`, with `brief.md` beside it as `<same-name>.brief.md`.
- **Run state** (step 4 onward): `<worktree>/specs/<branch>/factory/state.json`, committed with every checkpoint.
- **Run archive** (after drop): `${FACTORY_HOME:-~/.factory}/archive/<repo-name>-<branch>/`, a verified copy of the run folder excluding transient `lock.json`.

The pending file uses this same schema from the moment the run is created: `started_at` is set then, and `relay` and `timeline` capture the grilling rounds too. Step 3 writes both into the run state unchanged.

## Schema

```json
{
  "version": 5,
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
  "skills": {
    "speckit-plan": "/abs/.../SKILL.md",
    "grilling": "/abs/.../SKILL.md"
  },
  "commands": { "build": "dotnet build", "test": "dotnet test" },
  "analyze": {
    "pass": 1,
    "loops": 0,
    "reports": ["factory/analyze-1.md"],
    "remediations": ["factory/remediation-1.md"],
    "pending_clarify": []
  },
  "relay": null,
  "timeline": [],
  "decisions": [
    {
      "stage": "plan",
      "question": "Q1",
      "answer": "full",
      "auto": false,
      "at": "2026-10-22T14:07:30Z",
      "kind": "answer"
    }
  ],
  "ledger": [
    {
      "at": "2026-10-22T14:02:11Z",
      "stage": "plan",
      "role": "spec-builder",
      "harness": "claude-code",
      "in_est": 13400,
      "out_est": 2700,
      "reported": null,
      "duration_ms": 92000,
      "started_at": "2026-10-22T14:02:11Z",
      "ended_at": "2026-10-22T14:03:43Z"
    }
  ],
  "review": {
    "round": 0,
    "fix_rounds": 0,
    "ui_diff": false,
    "ui_reviewer_skipped": false
  },
  "ended_at": null,
  "pr_url": null,
  "history": [
    {
      "at": "2026-10-21T01:43:00Z",
      "stage": "specify",
      "event": "complete",
      "commit": "abc1234",
      "harness": "claude-code"
    }
  ]
}
```

- `version`: `5` on every write; readers accept versions 1–5 including legacy relay shapes and never rewrite what they read; the writer upgrades a run in the same atomic write that first changes it (FR-022). **v5** adds one top-level field, `issues[]`; every v4 key keeps its name and shape.
- `harness`: the adapter running the run now (`harness.md`, `name`). Each `history` entry records the harness that wrote it.
- `skills`: keyed by logical name. Paths are only valid on the harness that resolved them.
- `status`: closed vocabulary: `running` | `waiting_user` | `paused` | `halted` | `aborted` | `pr-open`.
- `stop_at`: `null`, or the stage the run pauses before (SKILL.md, "Stop point").
- `mode`: the run's chain (`chain`: `full` | `lite`) and whether relays auto-accept their recommended answers (`fast`). A run is created with the default mode — `chain: "lite"`, `fast: true` — unless the command's flags pinned otherwise (SKILL.md, "Route"); a lite→full escalation rewrites `chain` later. A relay answer may carry `"auto": true` (fast mode's auto-accepts); the approver screen lists those rounds from `decisions`.
- `stage`: closed vocabulary, the stage in progress or the next one to run: `brainstorm`, `grill`, `worktree`, `specify`, `clarify`, `grill-with-docs`, `plan`, `tasks`, `analyze`, `remediate`, `implement`, `verify`, `review`, `fix`, `approver`, `pr`. `brainstorm` (SKILL.md, "Brainstorm") is additive: it only ever appears on the idea path, before `grill`, and every stage value a run recorded before this value existed still resumes unchanged.
- `relay`: `null`, or every question round of the current stage: `{ "stage": "clarify", "rounds": [ { "questions": [ { "id": "Q1", "text": "...", "recommended": "..." } ], "answers": { "Q1": { "answer": "...", "at": "2026-10-22T14:07:30Z", "auto": false } } } ] }`. Each answer is an object: the user's text, the time it arrived, and `auto: true` when fast mode chose it. The last round is the open one. Answers are written as they arrive through `factory answer` (protocol.md, "Relay"). A version 1 state's single batch (`questions` + `answers` at the top of `relay`) is read as one round; a version 2 string answer is read as `{ "answer": <string>, "at": null }`.
  - Question fields and rendering are defined in protocol.md, "Questions". Rich question fields are additive: accept structured options and legacy string options, retaining saved answers and IDs. Derive progress from each question's stored position in the round; keep the original positions when redisplaying unanswered questions. Accepted new-format answers store the option ID or proposed text, separate from the rationale; legacy recommendations remain verbatim. The optional `requires_user` field (protocol.md, "Questions") is one such additive field: fast mode (protocol.md, "Relay", step 2) must skip a question carrying it, exactly like `pending_clarify`; a question saved without the field keeps today's fast-mode behaviour unchanged.
  - At the checkpoint the stage's settled answers move into `decisions` (append-only) before `relay` is cleared (FR-008).
- `decisions`: **v4**, append-only. One record per settled answer or gate decision: `{ "stage", "question", "answer", "auto", "at", "kind" }`, `kind` ∈ `answer` (a settled relay answer) | `approved` (the approver's approval, the record the `pr` gate requires) | `gate-override` (an explicit override of a gate). Gate kinds are never `auto`. The approver's veto list is every `auto: true` entry plus every `gate-override` entry (FR-006, SC-004). Entries are never rewritten or removed.
- `timeline`: every user wait of the run, oldest first (protocol.md, "Timeline"): `{ "at", "kind", "stage", "summary", "answered_at": null, "latency_ms": null }`. `kind` is closed: `questions` (a relay round), `notice` (any other `NOTIFY` that ends the turn), `approver`, or `halt`. `factory wait-open` appends the entry; `factory wait-close` sets `answered_at` and `latency_ms` (shown → answered) in place. Append-only for the whole run: never cleared at checkpoint. A round with several answers closes on its last answer; a wait the run never came back from keeps its nulls.
- `started_at` / `ended_at`: set `started_at` when the run is created; `ended_at` when the run reaches `pr-open` or `aborted`.
- `ledger`: one entry per agent spawn, appended by `factory ledger-add` when the spawn returns (each role of a `SPAWN_PARALLEL` gets its own entry): `{ "at", "stage", "role", "harness", "in_est", "out_est", "reported", "duration_ms", "started_at", "ended_at" }`. **v4** adds the spawn interval `started_at`/`ended_at`; `duration_ms` is derived from it on write (pre-v4 entries keep their stored duration and gain an interval on the first write).
  - `in_est` / `out_est`: word count × 1.35, rounded. Input words: the role file, the resolved skill files the inputs name, and the artifacts the inputs name. Output words: the returned envelope plus files created or modified under `<spec_dir>/factory/` during the spawn (`find <spec_dir>/factory -type f -newermt "<spawn start>" | xargs wc -w`).
  - `reported`: `null`, or `{ "in", "out" }` taken from usage the harness exposes for the spawn (`harness.md` names the source; none exists in tier 1 today). It is always labelled separately from the estimates (FR-010), never merged with them.
  - Effort totals are interval unions: agent time is the union of `started_at`/`ended_at`, human time the union of `timeline` wait intervals — never a sum of parallel durations (FR-009, "Totals").
- `issues`: **v5**, append-only. One record per thing that went wrong: `{ "at", "kind", "stage", "role", "cause", "detail", "duration_ms", "commit", "partial_return" }`. `kind` is closed: `overrun`, `agent-failure`, `retry`, `halt`, `verify-fail`. `cause` is `null` for kinds other than `overrun`; for `overrun` it is required and from `large-input`, `test-loop`, `retry`, `tool-slow`, `scope-too-big`, `other`, plus the detected-only `unreported`. `commit` is the worktree's last work commit (latest non-`factory:` commit) at record time (null where no worktree applies) — the provenance the stall rule reads. `partial_return` is `true` exactly when the record documents a `partial` return's stop, whatever its stop reason, and is accepted only for kinds `overrun`/`retry` of the file-writing roles (`spec-builder`, `code-build`, `ui-designer`, `fixer`); failure-policy retries, post-hoc detections and the `agent-failure`/`halt`/`verify-fail` kinds are never partial returns. Records are never rewritten or removed; three trailing marked records of one stage sharing one `commit` are the stall cap's halt instruction (SKILL.md, "Time budget").
- `history`: transition records, append-only, non-decreasing by `at` (FR-003, FR-004): `{ "at", "stage", "event", "commit", "harness" }`. `event` is a closed vocabulary: `complete`, `verify-pass`, `verify-fail`, `approved`, `gate-override`, `aborted`, `pr-open`, `resumed` — anything else is a validation violation. Each event has exactly one writer: `checkpoint` writes `complete` (or the gate events `approved`/`gate-override` carrying `decision`), `verify` writes the verify pair, `set-status`'s `aborted`/`pr-open` forms write those two, the resume path writes `resumed`. A verify record carries `commands: [ { "command", "status" } ]`; the review gate reads the latest one (FR-006).
- Paths inside `analyze` are relative to `spec_dir`. Timestamps are ISO-8601 UTC and never decrease within a record (FR-004).
- `analyze.result`: latest recorded report, non-negative `critical`/`high`/`medium`/`low` counts and writer-stamped `at`. `analyze-record <envelope>` accepts completed analyze envelopes (bare JSON or final fenced JSON), verifies the report exists inside this run's spec directory, normalizes its path, appends it once to `reports`, and preserves pending clarification questions. Record the outcome before checkpointing into implementation; CRITICAL/HIGH counts still block that transition unless explicitly overridden.

## Pen design context (additive)

When a run creates, references, or updates a Pen implementation reference, add `design` as defined in [design-code-mapping.md](design-code-mapping.md). It holds only `mode`, context/map/evidence paths, and status; source/node inventory belongs in the canonical map, and detailed checks/decisions in the referenced artifacts. `commands` may add discovered launch/capture commands; the context records their target/configuration. Design-only runs record reasons for any non-applicable application commands/gates rather than inventing an application prerequisite.

The referenced design context may also contain optional fields, with no schema version: `source_kind` (`pen | figma | image | text`), `framework` (`avalonia | web`), `scope` (a file `{ "kind": "file", "target": "<path>" }` or a surface `{ "kind": "surface", "accepted_files": [...], "excluded": [...] }`), and `ui_agent_pass` (null or `{ "state", "at", "applied", "skipped", "deferred" }`; `in_progress` reserves the pass before invocation and completed outcomes retain recommendations and reasons).

Pending-storage rules, the worktree-creation move of context, result persistence before checkpoints, and repository-relative artifact paths are `design-code-mapping.md` §1's. This field is optional: version 1/2 and older states without it remain readable and keep their existing behavior. The CLI passes small unknown fields through verbatim, including `design`; it does not validate the map or claim fidelity.

Use existing `review.fix_rounds` for all automatic design and other repairs; the reservation rules — `review.pending_design_fix` shaped `{ "attempt", "round", "verdict" }`, set before the fixer spawns with `stage: fix` and cleared after the attempt — plus protected decisions and evidence invalidation live in `design-code-mapping.md` §5/§6.

## Totals

The approver screen and the final `NOTIFY` each carry one totals line, computed from the state by interval union (`factory_cli/totals.py`): total wall clock (`ended_at - started_at`), human wait (union of `timeline` wait intervals, with the wait count), agent time (union of ledger spawn intervals, with the spawn count), and the non-negative residual (wall clock minus the other two). No report sums parallel durations — with parallel reviewers the union, not the sum, fits the wall clock (FR-009). One shared sentence format, e.g. `Run took 2h 14m: 38m you (12 waits), 1h 12m agents (23 spawns), 24m overhead.` When the ledger carries usage, the line appends its own labelled clause: estimates as `Nk in/Nk out estimated`, harness-reported usage verbatim and separate from them, never merged into one number (FR-010).

## Checkpoint

After a stage completes the orchestrator runs the writer, which does all of it (FR-001):

```sh
python3 <F>/bin/factory checkpoint <completed-stage> [--next <stage>]
```

The command stamps the time, moves the stage's settled relay answers into `decisions` before clearing `relay`, appends the `complete` history entry (`commit` left `null`, `harness` set), sets the next stage — the linear successor, or `--next` where the flow is non-linear (the analyze loop's re-entry, a lite chain skipping `clarify`) — validates, writes atomically and commits `factory: <stage> complete`. Pending state has no git: the file is written, nothing committed. `relay` is never cleared without its answers moving to `decisions` first (FR-008).

The commit that carries a `history` entry is the entry's commit: `git log --grep "factory: <stage> complete"` finds it.

## CLI

`<F>/bin/factory` is the factory's state CLI (stdlib Python 3) and the **single writer**: every state mutation goes through it, and the orchestrator never hand-edits `state.json` (FR-001). Its read commands do the mechanical state work — discovery, the resume digest, validation — outside the orchestrator's context, so routing never reads a whole `state.json` into it: its token cost stays flat however large `relay`, `timeline`, `ledger` and `history` grow.

- `python3 <F>/bin/factory runs [--repo <path>]`: "Discovery" as JSON — one entry per unfinished run: `source` (`worktree` | `pending`), `branch` (or `name`), `stage`, `status`, `halt_reason`, `mode`, `feature`, `last_activity`, `state_path`, `violations`, plus `worktree` and `spec_dir` on worktree runs. A run whose state rides along as a copy in later worktrees appears once.
- `python3 <F>/bin/factory show <branch-or-name> [--repo <path>]`: the "Resume" digest as JSON — every small state field verbatim, and from the large ones only what resume needs: `relay` as the open round's unanswered questions (each with its stored `position`, ready to redisplay), `waits` and `spawns` totals, `totals` and `totals_sentence` ("Totals"), `decisions` (the approver's veto list, FR-006), and `history_tail` (the last three entries). `analyze.pending_clarify` is a count. Everything a restarting agent needs beyond the digest it reads from `state.json` itself.
- `python3 <F>/bin/factory validate <run> | validate --all`: every violation as `{ "location", "reason" }`; exit 1 when any is found (FR-003).
- `python3 <F>/bin/factory budget <role>`: the role's resolved time budget as `{ "role", "seconds", "deadline" }` — `deadline` absolute ISO UTC, now + seconds. Resolution: `${FACTORY_HOME}/config.json` `budget.roles[<role>]` positive integer, else `budget.default_s` positive integer, else 300; a missing or malformed config never fails.
- `python3 <F>/bin/factory analyze-record <envelope>`: persist the validated analysis outcome through the writer before its checkpoint; requires a worktree run and commits its spec directory.
- `python3 <F>/bin/factory drop [--repo <path>]`: from the run worktree, archive a `pr-open` run and commit removal of its folder; never pushes. Success JSON contains `dropped`, absolute `archive`, `design` (permanent `docs/design/<branch>` path or null), short `commit`, `pr_url`, `totals_sentence` (null without a start time), and `dropped_at`. Design evidence moves to the permanent path and canonical map references are rewritten in the same commit. Refuses with exit 1 and a reason on stderr for no matching run, other status, live lock, existing archive or design target, copy or verification failure, or git failure; git failure restores touched paths and removes the archive. Usage errors exit 5.

Write commands (each stamps its own time, validates before writing, writes atomically, refuses under a live lock, and commits on worktree runs): `checkpoint <stage> [--next <stage>]` ("Checkpoint"), `ledger-add <stage> <role> [--started-at <iso>] [--ended-at <iso>] [--in-est N] [--out-est N] [--reported '<json>'] [--overrun '<json>'] [--partial-return]` (the overrun self-report `{ "cause", "detail" }` wins over detection; a duration over the role's budget yields cause `unreported`; an overrun both self-reported and detected is recorded exactly once; `--partial-return` marks a `partial` return's stop), `issue-add <kind> <stage> <role> --detail <text> --duration-ms <n> [--cause <cause>] [--commit <sha>] [--partial-return]` (appends one `issues[]` record; `--cause` required for `overrun`; the mark accepted only for `overrun`/`retry` of the file-writing roles `spec-builder`, `code-build`, `ui-designer`, `fixer`; a marked record's result carries the stall rule `stalls` with `halt: true` at three), `wait-open <kind> <stage> <summary>` (prints `wait-id`), `wait-close <wait-id>`, `answer <qid> '<answer>' [--auto] [--stage <stage>]`, `set-status <status> [--halt-reason <text>] [--pr-url <url>]` (`halted` records a `halt` issue with the reason as detail), `decisions-add <stage> <qid> '<answer>' [--kind answer|approved|gate-override]`, `verify --pass|--fail --commands '<json>'` (writes the verify pair the review gate reads; `--fail` records a `verify-fail` issue with the failing commands as detail), `rebind <run> --worktree <path>` (rewrites a moved run's stored paths, FR-012), and `resume <branch-or-name>` (records the `resumed` entry, then prints the digest). Also on the surface: `envelope check <file>` (FR-007), `lock take <run> [--force]` (FR-005), and `prune [--dry-run|--delete]` (FR-019).

Exit codes: 0 success; 1 no matching run or refused write (validation) with the reason on stderr; 2 not a git repository or git not runnable; 3 ambiguous run name; 4 the run's recorded `worktree` no longer exists (`show` only: halt and ask rather than resume); 5 usage error. A missing Python 3 or a missing `<F>/bin/factory` halts the run with a clear message (FR-002) — there is no manual state-write fallback.

## Discovery

Unfinished runs of the current repo, produced by `python3 <F>/bin/factory runs` ("CLI"). Its manual equivalent, and the definition of what the script does:

1. `git worktree list --porcelain`; for each worktree, read `specs/*/factory/state.json`. Keep those whose `status` is not `pr-open`; a run whose state appears in several worktrees (copies branched after it) counts once.
2. Pending files in `${FACTORY_HOME:-~/.factory}/pending/` whose `repo` is the current repo.

Show each as: branch (or slug), stage, status, last `history` time.

## Resume

1. `python3 <F>/bin/factory show <branch>` ("CLI"). Work in the digest's `worktree` (pending runs: `repo`). When the harness or effective installed model setup changed, repeat the adapter's supported setup inspection before another role starts. Preserve exact choices; unavailable selections require correction/recheck, while unsupported or failed inspection stays disclosed as unverified under the existing bounded spawn policy. When `harness` differs from this harness: `RESOLVE` every name in `skills` again, set `harness`, and checkpoint before restarting the stage. An open relay's unanswered questions are `relay.unanswered` in the digest, in stored order — redisplay exactly those.
   - For active `design`, read [design-code-mapping.md](design-code-mapping.md), its context and canonical map first; resolve `pen-design` if absent (and again on harness change), and recheck freshness, anchors, evidence and exceptions under its §5/§6 before restarting the stage, keeping valid cached evidence instead of restarting full discovery.
   - Before implementation/fixing on resume, compare task requirements, declared seams/failure paths and accepted scope evidence per engineering.md's "Confirmed test scope". Preserve matching acceptance; changed or unproven scope returns to protected confirmation before behavior edits.
2. Restart the recorded `stage` from its beginning. Apply protocol.md's "Verification handoff": preserve completed commits and outstanding mandatory checks; resume pending checks before claiming completion, with independent orchestrator verification still required:
   - Pending `brainstorm`: re-run step 2 (brainstorm) with the existing brief and saved relay answers as the starting point, then continue into step 3 (grill). Redisplay only unanswered questions in the existing open round before recomputing the frontier (protocol.md).
   - Pending `grill`: re-run grilling with the existing brief and saved relay answers as the starting point. Redisplay only unanswered questions in the existing open round before recomputing the frontier (protocol.md).
   - Pending `worktree`: run step 4.
   - Spec stages: `SPAWN` a fresh `spec-builder` with the state and the stage. It reads `relay` from the state: answered questions are settled, the agent asks only the rest.
   - `implement`: `SPAWN` `code-build`; it resolves commit units using engineering.md, inspects task status/worktree/test/commit evidence, and continues the first unfinished unit. Completed commits remain complete. A checked red half in an unambiguous legacy pair is not a finished unit; finish the pair together. Ambiguous pairing stops before behavior edits for resolution.
   - `verify`, `review`, `fix`: for an active design run with `review.pending_design_fix`, resume that saved fixer attempt first using its verdict/context and current uncommitted work, preserving the reservation and failure policy; clear it on completion, then verify/re-review. Otherwise re-run step 6's verify, then step 7 from its first sub-step for the current round.
   - `approver`: show the approver screen again.
   - `pr`: check `gh pr view <branch>` first; an existing PR only needs its URL recorded.
3. `halted` or `aborted`: show `halt_reason` and ask the user how to continue before restarting the stage.
4. `paused`: set `status: running` and start the recorded stage. Flags on the resume command update the state first: `--stop-at <stage>` sets a new `stop_at`, `--lite` / `--full` set `mode.chain`, `--fast` / `--no-fast` set `mode.fast`.
