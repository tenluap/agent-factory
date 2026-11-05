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
  "models": {
    "resolved": { "deep": "model-id", "standard": "" },
    "source": { "deep": "project", "standard": "adapter" }
  },
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

- `version`: `5` on every write; readers accept versions 1–5 including legacy relay shapes and never rewrite what they read; the writer upgrades a run in the same atomic write that first changes it (FR-022). **v5** adds `issues[]` and the additive optional `models` block; every v4 key keeps its name and shape.
- `harness`: the adapter running the run now (`harness.md`, `name`). Each `history` entry records the harness that wrote it.
- `models`: preflight's resolved model strings and source labels for the run harness, keyed by `deep` and `standard` in both `resolved` and `source`; each source is `project`, `user`, or `adapter`. An empty model inherits the session model. A missing block in an older state means not yet resolved. On resume, preflight resolves again, discloses each changed tier's old and new values and sources, then replaces the block; no prior block means no delta.
- `skills`: keyed by logical name. Paths are only valid on the harness that resolved them.
- `status`: closed vocabulary: `running` | `waiting_user` | `paused` | `halted` | `aborted` | `pr-open`.
- `stop_at`: `null`, or the stage the run pauses before (SKILL.md, "Stop point").
- `mode`: the run's chain (`chain`: `full` | `lite`) and whether relays auto-accept their recommended answers (`fast`). A run is created with the default mode — `chain: "lite"`, `fast: true` — unless the command's flags pinned otherwise (SKILL.md, "Route"); a lite→full escalation rewrites `chain` later. A relay answer may carry `"auto": true` (fast mode's auto-accepts); the approver screen lists those rounds from `decisions`.
  - `mode.cruise` (additive, spec 021): optional boolean; absent means off. `true` requires `fast: true` (cruise implies fast). Set by `--cruise` / `--no-cruise` through `factory mode` and `factory resume` (SKILL.md, "Route"). Cruise answers the relay itself and never publishes without the user's Approve.
  - `cruise_override` (additive, spec 021): optional boolean on a relay answer and on a `decisions` record, absent otherwise. `true` marks an answer cruise took for the user; invariants: boolean when present, `true` requires `auto: true`, never on kind `approved`, never at stage `approver`. A marked `gate-override` is only accepted at stage `analyze` (analyze exhaustion) by the `decisions-add` writer. Writers refuse the marker unless the run has `mode.cruise: true`. The `pr` gate ignores any marked approver record, so a marked record never permits publication.
- `stage`: closed vocabulary, the stage in progress or the next one to run: `brainstorm`, `grill`, `worktree`, `specify`, `clarify`, `grill-with-docs`, `plan`, `tasks`, `analyze`, `remediate`, `implement`, `verify`, `review`, `fix`, `approver`, `pr`, `retro`. `brainstorm` (SKILL.md, "Brainstorm") is additive: it only ever appears on the idea path, before `grill`, and every stage value a run recorded before this value existed still resumes unchanged.
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
- `issues`: **v5**, append-only. One record per thing that went wrong: `{ "at", "kind", "stage", "role", "cause", "detail", "duration_ms", "commit", "partial_return" }`. `kind` is closed: `overrun`, `agent-failure`, `retry`, `halt`, `verify-fail`. `cause` is `null` for kinds other than `overrun`; for `overrun` it is required and from `large-input`, `test-loop`, `retry`, `tool-slow`, `scope-too-big`, `other`, plus the detected-only `unreported`. `commit` is the worktree's last work commit (latest non-`factory:` commit) at record time (null where no worktree applies) — the provenance the stall rule reads. `partial_return` is `true` exactly when the record documents a `partial` return's stop, whatever its stop reason, and is accepted only for kinds `overrun`/`retry` of the file-writing roles (`spec-builder`, `code-build`, `design-to-code`, `fixer`); failure-policy retries, post-hoc detections and the `agent-failure`/`halt`/`verify-fail` kinds are never partial returns. Records are never rewritten or removed; three trailing marked records of one stage sharing one `commit` are the stall cap's halt instruction (SKILL.md, "Time budget").
- `history`: transition records, append-only, non-decreasing by `at` (FR-003, FR-004): `{ "at", "stage", "event", "commit", "harness" }`. `event` is a closed vocabulary: `complete`, `verify-pass`, `verify-fail`, `approved`, `gate-override`, `aborted`, `pr-open`, `resumed`, `adopted` — anything else is a validation violation. Each event has exactly one writer: `checkpoint` writes `complete` (or the gate events `approved`/`gate-override` carrying `decision`), `verify` writes the verify pair, `set-status`'s `aborted`/`pr-open` forms write those two, the resume path writes `resumed`, and `factory adopt` (its write) is the only writer of `adopted`. A verify record carries `commands: [ { "command", "status" } ]`; the review gate reads the latest one (FR-006).
- Paths inside `analyze` are relative to `spec_dir`. Timestamps are ISO-8601 UTC and never decrease within a record (FR-004).
- `analyze.result`: latest recorded report, non-negative `critical`/`high`/`medium`/`low` counts and writer-stamped `at`. `analyze-record <envelope>` accepts completed analyze envelopes (bare JSON or final fenced JSON), verifies the report exists inside this run's spec directory, normalizes its path, appends it once to `reports`, and preserves pending clarification questions. Record the outcome before checkpointing into implementation; the implement gate refuses while an acceptance target is unmet, unless explicitly overridden.
- `analyze.baseline` (optional, additive, ADR 0016): `{ "critical", "high", "medium", "low", "report", "at" }` with non-negative integer counts, a non-empty spec-relative `report` and a writer-stamped `at` (equal to the `result.at` of the record that set it). `validate_state` checks its shape. `analyze-record` sets it once, from the first record, or stores the derived baseline of a legacy run (exactly one report, named by `result`) on the next record; later records change only `result` and `reports`, so resume and the lite-to-full escalation (`factory/analyze-<n>-full.md`) keep it. `analyze-record <envelope> --fresh-baseline` replaces it only when no baseline is stored or derivable (FR-012); otherwise it is refused with state and HEAD unchanged. A run with no stored and no derivable baseline is refused into implementation until the user chooses a fresh baseline, a `gate-override`, or abort.
- `analyze.loops` and `analyze.pass`: written only by `checkpoint remediate` while the recorded stage is `remediate`, in the same locked write as its history entry. A repeated checkpoint after the stage advanced changes nothing, and escalation, `analyze-record` and resume leave both unchanged (FR-003, FR-014). A gate into `remediate` refuses at `loops == 2` unless a newer non-auto analyze answer exists (the guided pass).
- `review.round` and `review.fix_rounds`: written by `checkpoint review` and `checkpoint fix`, respectively; see "Checkpoint". User config `${FACTORY_HOME}/config.json` may set `budget.review_full_s` for full-diff reviewer spawns; it is not a state field.

## Stack profile (additive, spec 017)

Preflight records `profile` (detection never halts: an unknown or mixed stack is disclosed in `notes`/`unknown_markers`, and an empty profile means no known stack was found):

```json
"profile": {
  "languages":   [{ "name": "csharp", "version": "net9.0", "evidence": ["src/App/App.csproj"] }],
  "frameworks":  [{ "name": "avalonia", "version": "11.2.0", "evidence": ["src/App/App.csproj"] }],
  "package_managers": [
    { "name": "dotnet", "primary": true,  "evidence": ["src/App"], "lockfiles": [] },
    { "name": "npm",    "primary": false, "evidence": ["web"],    "lockfiles": ["web/package-lock.json"] }
  ],
  "ui": true,
  "monorepo": false,
  "projects": ["src/App/App.csproj"],
  "commands": { "build": { "value": "dotnet build", "source": "detected", "manager": "dotnet" } },
  "unknown_markers": [],
  "notes": [],
  "detected_at": "2026-10-31T12:00:00Z",
  "detected_by": "factory detect 017"
}
```

Each language/framework entry carries its evidence path(s) and best-effort version from marker files (no subprocess, no network). `package_managers` holds every distinct manager in a mixed repo; exactly one is `primary` (root-level evidence wins, ties break toward most evidence, a mixed root is disclosed in `notes`). Detected commands carry the `manager` they belong to. This field is optional like `design`: older states without it remain valid and behave as before. The CLI light-validates presence/types (`detect.validate_profile`); unknown extra fields pass through. The human-readable rendering lives in `profile.md` (pending runs: beside the pending file; worktree runs: `<spec_dir>/factory/profile.md`, committed). On resume, preflight re-records; a changed stack is disclosed in the record result — the approved spec/plan still govern the work.

## Pen design context (additive)

When a run creates, references, or updates a Pen implementation reference, add `design` as defined in [design-code-mapping.md](design-code-mapping.md). It holds only `mode`, context/map/evidence paths, and status; source/node inventory belongs in the canonical map, and detailed checks/decisions in the referenced artifacts. `commands` may add discovered launch/capture commands; the context records their target/configuration. Design-only runs record reasons for any non-applicable application commands/gates rather than inventing an application prerequisite.

The referenced design context may also contain optional fields, with no schema version: `source_kind` (`pen | figma | image | text`), `framework` (`avalonia | web`), `scope` (a file `{ "kind": "file", "target": "<path>" }` or a surface `{ "kind": "surface", "accepted_files": [...], "excluded": [...] }`), `active_assignment` (null or `{ "role", "first", "last" }` for the active implement range), `ui_quality_pending` (null or `{ "first", "last" }` for the final UI range pending pass reconciliation and verification), and `ui_agent_pass` (null or `{ "state", "at", "applied", "skipped", "deferred" }`; `in_progress` reserves the pass before invocation and completed outcomes retain recommendations and reasons).

Pending-storage rules, the worktree-creation move of context, result persistence before checkpoints, and repository-relative artifact paths are `design-code-mapping.md` §1's. This field is optional: version 1/2 and older states without it remain readable and keep their existing behavior. The CLI passes small unknown fields through verbatim, including `design`; it does not validate the map or claim fidelity.

Use existing `review.fix_rounds` for all automatic design and other repairs. `checkpoint review --next fix --design-fix '<worktree-relative verdict path>'` sets `review.pending_design_fix` to `{ "attempt", "round", "verdict" }` with `stage: fix` before spawning; `attempt` is counter + 1 without incrementing. It reserves on entry from stored stage `implement`, `verify` or `review`, and a retry at stored stage `fix` preserves the existing reservation. After the fixer completes and verification passes, `checkpoint fix --next review` inspects and clears the reservation in the same locked write as the counter update. A legacy reservation whose attempt equals the counter is not counted again. Protected decisions and evidence invalidation live in `design-code-mapping.md` §5/§6.

## Adopted runs (spec 022)

`factory adopt <branch|spec_dir>` makes a worktree run from a spec factory did not start. Its write is the only writer of the `adopted` block; `factory adopt` writes it once, with the adopted state, and no other command sets it.

```json
"adopted": {
  "source": { "shape": "branch", "branch": "007-x", "spec_dir": "specs/007-x" },
  "inferred_stage": "tasks",
  "chosen_stage": "plan",
  "base_commit": "<40-hex sha of the branch HEAD at the write>"
}
```

- `source.shape` is `branch`, `remote-branch` or `default-branch`; `source.branch` and `source.spec_dir` are non-empty strings.
- `inferred_stage` (from the artifacts) and `chosen_stage` (the entry stage) are each one of `specify`, `plan`, `tasks`, `analyze`.
- `base_commit` is 40 lowercase hex characters: the branch HEAD the write adopted. Pre-adoption commits are `git rev-list <base>..<base_commit>`; pre-adoption tasks are the IDs checked in `git show <base_commit>:<spec_dir>/tasks.md`.
- An `adopted` history entry `{ "stage": <chosen>, "event": "adopted", "commit": null }` is written once with the block; a state with an `adopted` history entry but no block is invalid. No rule requires `complete` entries before the chosen stage, and states without `adopted` validate as before.

Pending adoption: `${FACTORY_HOME:-~/.factory}/pending/<repo-name>-adopt-<branch>.json`, with `brief.md` and `profile.md` beside it. It holds the same schema as any pending run, plus `branch` and `spec_dir`. The adoption's own pending file never refuses its own write; any other pending file of the repo does, naming it (resume or prune it first). `factory adopt` deletes the pending file, brief and profile only after the adoption commit lands; a failed write keeps them and a retry reuses them.

`resume <name>` with no matching run exits 1 with `use adopt <branch|spec_dir> for a spec factory did not start` appended to its "no run" message; `resume` never creates a run, worktree or branch.

## Totals

The approver screen and the final `NOTIFY` each carry one totals line, computed from the state by interval union (`factory_cli/totals.py`): total wall clock (`ended_at - started_at`), human wait (union of `timeline` wait intervals, with the wait count), agent time (union of ledger spawn intervals, with the spawn count), and the non-negative residual (wall clock minus the other two). No report sums parallel durations — with parallel reviewers the union, not the sum, fits the wall clock (FR-009). One shared sentence format, e.g. `Run took 2h 14m: 38m you (12 waits), 1h 12m agents (23 spawns), 24m overhead.` When the ledger carries usage, the line appends its own labelled clause: estimates as `Nk in/Nk out estimated`, harness-reported usage verbatim and separate from them, never merged into one number (FR-010).

## Checkpoint

After a stage completes the orchestrator runs the writer, which does all of it (FR-001):

```sh
python3 <F>/bin/factory checkpoint <completed-stage> [--next <stage>]
```

The command stamps the time, moves the stage's settled relay answers into `decisions` before clearing `relay`, appends the `complete` history entry (`commit` left `null`, `harness` set), sets the next stage — the linear successor, or `--next` where the flow is non-linear (the analyze loop's re-entry, a lite chain skipping `clarify`) — validates, writes atomically and commits `factory: <stage> complete`. Pending state has no git: the file is written, nothing committed. `relay` is never cleared without its answers moving to `decisions` first (FR-008).

The commit that carries a `history` entry is the entry's commit: `git log --grep "factory: <stage> complete"` finds it.

`checkpoint review` derives `review.round` as the maximum of the stored value and verdict folders `factory/reviews/round-<n>/verdict.json`; absent verdicts leave it unchanged. `checkpoint review --next fix --design-fix '<worktree-relative verdict path>'` atomically records the pending design reservation and the fix stage. `checkpoint fix` increments `review.fix_rounds` only while the stored stage is `fix`, except a legacy reservation whose `attempt` equals the counter, and clears the reservation in that same locked state write. This stage guard makes retries safe. Both results, including commit failures, include `review: {round, fix_rounds}`.

## CLI

`<F>/bin/factory` is the factory's state CLI (stdlib Python 3) and the **single writer**: every state mutation goes through it, and the orchestrator never hand-edits `state.json` (FR-001). Its read commands do the mechanical state work — discovery, the resume digest, validation — outside the orchestrator's context, so routing never reads a whole `state.json` into it: its token cost stays flat however large `relay`, `timeline`, `ledger` and `history` grow.

- `python3 <F>/bin/factory runs [--repo <path>]`: "Discovery" as JSON — one entry per unfinished run: `source` (`worktree` | `pending`), `branch` (or `name`), `stage`, `status`, `halt_reason`, `mode`, `feature`, `last_activity`, `state_path`, `violations`, plus `worktree` and `spec_dir` on worktree runs. A run whose state rides along as a copy in later worktrees appears once.
- `python3 <F>/bin/factory show <branch-or-name> [--repo <path>]`: the "Resume" digest as JSON — every small state field verbatim, and from the large ones only what resume needs: `relay` as the open round's unanswered questions (each with its stored `position`, ready to redisplay), `waits` and `spawns` totals, `totals` and `totals_sentence` ("Totals"), `decisions` (the approver's veto list, FR-006), and `history_tail` (the last three entries). `analyze.pending_clarify` is a count. Everything a restarting agent needs beyond the digest it reads from `state.json` itself.
- `python3 <F>/bin/factory mode [--lite|--full] [--fast|--no-fast] [--cruise|--no-cruise]`: the resolved mode as JSON `{chain, fast, cruise}`, last wins per pair, read-only; a cruise-on plus `--no-fast` conflict exits 5 naming both flags and writes nothing (spec 021).
- `python3 <F>/bin/factory validate <run> | validate --all`: every violation as `{ "location", "reason" }`; exit 1 when any is found (FR-003).
- `python3 <F>/bin/factory budget <role> [--round <n>|--full]`: returns `{ "role", "seconds", "deadline", "full" }`; `deadline` is absolute ISO UTC. Normal resolution is positive integer `budget.roles[<role>]`, else `budget.default_s`, else 300. Round 1 or `--full` selects the greater of normal and positive integer `budget.review_full_s` (default 600) for `security-reviewer`, `code-standards`, `spec-conformance`, `ui-reviewer`, `ux-reviewer`; `review-judge` and other roles stay normal. Later rounds use normal. A missing or malformed config never fails; non-positive or non-integer round and combined flags exit 2.
- `python3 <F>/bin/factory analyze-record <envelope>`: persist the validated analysis outcome through the writer before its checkpoint; requires a worktree run and commits its spec directory.
- `python3 <F>/bin/factory analyze-record <envelope> --fresh-baseline`: the same recorder, but its record becomes the baseline; refused (exit 1, nothing written) when a baseline is already stored or derivable.
- `python3 <F>/bin/factory amendment-check <draft> [--sha256 <hex>]`: prints `{"draft", "sha256"}`, the lower-case SHA-256 of the draft's bytes. Read-only. With `--sha256`, a draft whose hash differs from the approved one exits 1, naming both hashes; a missing draft exits 1 naming the path. The constitution is never written by this command.
- `python3 <F>/bin/factory improvements add --from <file> --run <branch>`: validate and persist retro candidates for a `pr-open` run.
- `python3 <F>/bin/factory feedback [<branch>] [--repo <path>]`: refresh archived runs' PR outcomes into `outcomes/` and `feedback` backlog entries; the archive is never written. Reports `refreshed`, `skipped` and `gaps` as JSON; exit 1 on any gap or a refused `<branch>`, 2 when `--repo` is not a git repository.
- `python3 <F>/bin/factory drop [--repo <path>]`: from the run worktree, archive a `pr-open` run and commit removal of its folder; never pushes. Success JSON contains `dropped`, absolute `archive`, `design` (permanent `docs/design/<branch>` path or null), short `commit`, `pr_url`, `totals_sentence` (null without a start time), and `dropped_at`. Design evidence moves to the permanent path and canonical map references are rewritten in the same commit. Refuses with exit 1 and a reason on stderr for no matching run, other status, live lock, existing archive or design target, copy or verification failure, or git failure; git failure restores touched paths and removes the archive. Usage errors exit 5.

Adoption command (spec 022): `adopt <branch|spec_dir> [--stage <stage>] [--dry-run]`. `--dry-run` resolves the source from git refs only (never fetches, checks out or writes) and prints the adoption report as JSON: `shape`, `branch`, `spec_dir`, `base`, `artifacts`, `dirty`, `inferred_stage`, `needs_clarification`, `worktree`, `pending` and `refusal`. Without `--dry-run` it writes the worktree run (the `adopted` block, the `adopted` entry, brief and profile moved, one commit `factory: adopt <branch>` touching only `<spec_dir>/factory/`) and prints the resume digest. `--stage` is one of `specify`, `plan`, `tasks`, `analyze`; any other value exits 5. Exit codes: 0 success; 1 refused (the reason names the cause; nothing is written), an ended or missing pending adoption, a live lock, or a rolled-back write; 3 an ambiguous source; 5 usage error.

Write commands (each stamps its own time, validates before writing, writes atomically, refuses under a live lock, and commits on worktree runs): `checkpoint <stage> [--next <stage>]` ("Checkpoint"), `profile-record` ("Stack profile": detects the repo and records `profile` into the one writable run, writes `profile.md`, discloses a changed stack on re-record), `ledger-add <stage> <role> [--started-at <iso>] [--ended-at <iso>] [--in-est N] [--out-est N] [--reported '<json>'] [--overrun '<json>'] [--partial-return]` (the overrun self-report `{ "cause", "detail" }` wins over detection; a duration over the role's budget yields cause `unreported`; an overrun both self-reported and detected is recorded exactly once; `--partial-return` marks a `partial` return's stop), `issue-add <kind> <stage> <role> --detail <text> --duration-ms <n> [--cause <cause>] [--commit <sha>] [--partial-return]` (appends one `issues[]` record; `--cause` required for `overrun`; the mark accepted only for `overrun`/`retry` of the file-writing roles `spec-builder`, `code-build`, `design-to-code`, `fixer`; a marked record's result carries the stall rule `stalls` with `halt: true` at three), `wait-open <kind> <stage> <summary>` (prints `wait-id`), `wait-close <wait-id>`, `answer <qid> '<answer>' [--auto] [--stage <stage>] [--cruise-override]` (the marker needs `mode.cruise: true`, else exit 1), `set-status <status> [--halt-reason <text>] [--pr-url <url>]` (`halted` records a `halt` issue with the reason as detail), `decisions-add <stage> <qid> '<answer>' [--kind answer|approved|gate-override] [--cruise-override]` (the marker needs `mode.cruise: true`, never with `approved`, and with `gate-override` only at `analyze`; marked records are `auto: true`), `verify --pass|--fail --commands '<json>'` (writes the verify pair the review gate reads; `--fail` records a `verify-fail` issue with the failing commands as detail), `rebind <run> --worktree <path>` (rewrites a moved run's stored paths, FR-012), and `resume <branch-or-name> [--lite|--full] [--fast|--no-fast] [--cruise|--no-cruise]` (applies mode flags and records the `resumed` entry in one write, then prints the digest). Also on the surface: `detect [--repo <path>]` (read-only profile JSON, "Stack profile"), `envelope check <file>` (FR-007), `lock take <run> [--force]` (FR-005), and `prune [--dry-run|--delete]` (FR-019).

`ledger-add ... [--round <n>|--full]` uses the same budget selection as `budget` for detection. `answer <qid> '<answer>' [--question '<json>'] ...` accepts a question object with matching id; malformed JSON or mismatched id exits 1 before writing. A `requires_user` answer on a worktree run commits immutable `<spec_dir>/factory/relay/<stage>-<qid>.md` with state, returning `record`. When a record is due, stage and qid must match `[A-Za-z0-9_-]+`; unsafe names exit 1 without writing. An identical re-answer returns `unchanged: true` without a commit only when record and state are clean and the record is in HEAD; otherwise it completes the pending commit. A different answer exits 1 naming the record. Records include a JSON-encoded answer for exact comparison. Older records without that field are accepted when their answer boundary is unambiguous; otherwise the command refuses without writing. Pending runs and questions without `requires_user` write no record.

On a `pr-open` run only `ledger-add` and `issue-add` with stage `retro` may write; every other write to an ended run and every write to an `aborted` run is refused.

Exit codes: 0 success; 1 no matching run or refused write (validation) with the reason on stderr; 2 not a git repository, git not runnable, or invalid `--round`/`--full` selection; 3 ambiguous run name; 4 the run's recorded `worktree` no longer exists (`show` only: halt and ask rather than resume); 5 other usage errors. A missing Python 3 or a missing `<F>/bin/factory` halts the run with a clear message (FR-002) — there is no manual state-write fallback.

## Discovery

Unfinished runs of the current repo, produced by `python3 <F>/bin/factory runs` ("CLI"). Its manual equivalent, and the definition of what the script does:

1. `git worktree list --porcelain`; for each worktree, read `specs/*/factory/state.json`. Keep those whose `status` is not `pr-open`; a run whose state appears in several worktrees (copies branched after it) counts once.
2. Pending files in `${FACTORY_HOME:-~/.factory}/pending/` whose `repo` is the current repo.

Show each as: branch (or slug), stage, status, last `history` time.

## Resume

1. `python3 <F>/bin/factory show <branch>` ("CLI"). Work in the digest's `worktree` (pending runs: `repo`). When the harness or effective installed model setup changed, repeat the adapter's supported setup inspection before another role starts. Preserve exact choices; unavailable selections require correction/recheck, while unsupported or failed inspection stays disclosed as unverified under the existing bounded spawn policy. When `harness` differs from this harness: `RESOLVE` every name in `skills` again, set `harness`, and checkpoint before restarting the stage. An open relay's unanswered questions are `relay.unanswered` in the digest, in stored order — redisplay exactly those.
   - For active `design`, read [design-code-mapping.md](design-code-mapping.md), its context and canonical map first; branch on `source_kind`: resolve `pen-design` if absent (and again on harness change) only for Pen; for Figma rediscover its skill or available MCP inspection capability as in SKILL.md step 5, including on implement and harness change; image and text require neither. If a legacy context lacks `source_kind`, determine it from its recorded source identity; relay ambiguity rather than guess. Recheck freshness, anchors, evidence and exceptions under §5/§6 before restarting the stage, keeping valid cached evidence instead of restarting full discovery.
   - Before implementation/fixing on resume, compare task requirements, declared seams/failure paths and accepted scope evidence per engineering.md's "Confirmed test scope". Preserve matching acceptance; changed or unproven scope returns to protected confirmation before behavior edits.
2. Restart the recorded `stage` from its beginning. Apply protocol.md's "Verification handoff": preserve completed commits and outstanding mandatory checks; resume pending checks before claiming completion, with independent orchestrator verification still required:
   - Pending `brainstorm`: re-run step 2 (brainstorm) with the existing brief and saved relay answers as the starting point, then continue into step 3 (grill). Redisplay only unanswered questions in the existing open round before recomputing the frontier (protocol.md).
   - Pending `grill`: re-run grilling with the existing brief and saved relay answers as the starting point. Redisplay only unanswered questions in the existing open round before recomputing the frontier (protocol.md).
   - Pending `worktree`: run step 4.
   - Spec stages: `SPAWN` a fresh `spec-builder` with the state and the stage. It reads `relay` from the state: answered questions are settled, the agent asks only the rest.
   - `implement`: for a run with a saved UI design context, re-enter SKILL.md step 6 routing. Restore the persisted `active_assignment` and finish that role/range first; if `ui_quality_pending` remains, respawn `design-to-code` for its recorded final range to reconcile the pass and checks even if all `[UI]` boxes are checked. Then select further ranges by `[UI]` marker in task order. Non-design and pre-feature runs retain `code-build` resume. Writers resolve commit units using engineering.md, inspect task status/worktree/test/commit evidence, and continue the first unfinished unit. Completed commits remain complete. A checked red half in an unambiguous legacy pair is not a finished unit; finish the pair together. Ambiguous pairing stops before behavior edits for resolution.
   - `verify`, `review`, `fix`: for an active design run with `review.pending_design_fix`, re-spawn the saved fixer attempt with its verdict/context and current uncommitted work, preserving the reservation and failure policy. Otherwise, when the stored stage is `fix` with no reservation, re-spawn the fixer with the latest `factory/reviews/round-<n>/verdict.json` and current work. In either case, only after the fixer returns `done`, run step 6's verify, then `checkpoint fix --next review` (which clears any reservation), then re-review; the stage guard makes a repeated checkpoint safe. For other stages, re-run step 6's verify, then step 7 from its first sub-step for the current round.
   - `approver`: show the approver screen again.
   - `pr`: restart SKILL.md step 9 from item 1; its Branch PR lookup reuses an existing open PR, so resume never opens a duplicate. `git push -u` of an already-pushed branch is a no-op.
3. `halted` or `aborted`: show `halt_reason` and ask the user how to continue before restarting the stage.
4. `paused`: set `status: running` and start the recorded stage. Flags on the resume command update the state first: `--stop-at <stage>` sets a new `stop_at`, `--lite` / `--full` set `mode.chain`, `--fast` / `--no-fast` set `mode.fast`, `--cruise` / `--no-cruise` set `mode.cruise` (`--cruise` also sets `fast`; `--no-fast` with cruise on exits 5 before any write).
