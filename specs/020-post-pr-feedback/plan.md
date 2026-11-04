# Implementation Plan: Post-PR Feedback

**Branch**: `020-post-pr-feedback` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/020-post-pr-feedback/spec.md`; settled decisions Q1-Q9 in `factory/brief.md`.

## Summary

Add `factory feedback [<branch>]`: a manual, read-only refresh of every archived run of the current repository that has a `pr_url`. It reads PR state and failed checks with `gh pr view` and change requests with `gh api .../reviews`, through one injectable runner. New outcomes are merged into a per-run sidecar `${FACTORY_HOME}/outcomes/<repo-name>-<branch>.json`, and actionable ones become `feedback` entries in the existing improvement backlog. Fetch problems become classified `gaps`; nothing is written for that run and the command exits 1. A `/factory feedback` route runs it and shows the result. Phase 0/1 outputs (decisions, data model, CLI contract, validation) live in this plan, following the 016/017 precedent.

## Technical Context

**Language/Version**: Python 3 standard library; Markdown skill prose.

**Primary Dependencies**: none new. `gh` (already used by the PR step) is invoked as an external process.

**Storage**: JSON files in the factory home: `outcomes/<repo-name>-<branch>.json` (new), `improvements/*.json` (new `feedback` kind). The run archive is read only.

**Testing**: `python3 -m unittest discover -s tools` (existing runner, `tools/tests/`).

**Target Platform**: macOS/Linux shells under the five harnesses.

**Project Type**: CLI plus agent skill prose.

**Performance Goals**: bounded by archived runs with a `pr_url`; two `gh` reads per non-terminal run, sequential.

**Constraints**: read-only toward GitHub and the archive (FR-003, FR-006); no automatic retries (FR-013); harness-neutral core (constitution II).

**Scale/Scope**: tens of archived runs per repository.

## Constitution Check

- **I. Design First**: PASS. `DESIGN.md` gains the feedback refresh in the first task, before core edits.
- **II. Harness-Neutral Core**: PASS. The route uses `SHELL: python3 <F>/bin/factory feedback`; `gh` is called only by the CLI, like `factory_sha` calls `git`. No adapter change.
- **III. Generated Dist**: PASS. No `render.py` change; the build command re-renders all five harnesses.
- **IV. Stateless Agents**: PASS. No agent is spawned; results live on disk.
- **V. Simplicity and Reuse**: PASS. Reuses `improvements._write_atomic`, `backlog_name`, `factory_sha`, the home-level lock wait, `commands.main_repo`/`factory_home`, `state.parse_iso`/`iso`. New file, abstractions and fields are reasoned below.

Post-design re-check: PASS, no violations.

## Project Structure

```text
core/skills/factory/bin/factory_cli/
├── feedback.py        # NEW: discovery, gh runner, classification, outcome merge
├── improvements.py    # add_feedback(); lock wait generalised; feedback in listing
├── commands.py        # cmd_feedback()
└── cli.py             # `feedback [<branch>]` dispatch, USAGE, exit 1 on gaps
core/skills/factory/SKILL.md             # `feedback` route + argument-hint
core/skills/factory/references/state.md  # CLI section: feedback command
DESIGN.md, CONTEXT.md                    # design record, glossary terms
tools/tests/test_feedback.py             # NEW
```

**Structure Decision**: a new `feedback.py` module rather than a section of `commands.py` (over 1500 lines of run-state commands) or `improvements.py` (backlog only). The refresh is one concern with its own external integration and error policy; backlog writes stay in `improvements.py`, their single owner (ENG-6, ENG-13).

### New files, abstractions, dependencies

- `core/skills/factory/bin/factory_cli/feedback.py` - file - GitHub reads, gap classification and the outcome file have no existing home; keeps `gh` out of run-state and backlog code.
- `tools/tests/test_feedback.py` - file - tests for the new seams; `gh` responses are inline dict fixtures, no fixture files.
- `feedback.run_gh(args) -> (returncode, stdout, stderr)` - abstraction - the single injectable GitHub runner (Q9, FR-014).
- `feedback.Gap(cls, reason)` - abstraction - one exception carrying a gap class, so every failure point maps to `gaps` the same way.
- `improvements.add_feedback(home, run, items, now=None)` - abstraction - feedback upsert rules (one entry per run and key, append to `ready`, never touch `claimed`) differ from retro `add` (cap, cross-run cover).
- Dependencies: none.

## Design

### Discovery (FR-002)

- Archived runs: `${FACTORY_HOME}/archive/*/state.json` whose `repo` resolves to `commands.main_repo(cwd)` and whose `pr_url` is a non-empty string. Unreadable archive states are skipped, as `list_backlogs` skips unreadable files.
- `<branch>` narrows to one run; no matching archived run, or one without `pr_url`: exit 1 naming the reason, nothing written.
- Outcome file name: `improvements.backlog_name(repo, branch)` under `outcomes/`, matching the archive's `<repo-name>-<branch>`.
- A run whose outcome file holds `state:merged` or `state:closed` is listed under `skipped` and not fetched.

### GitHub reads (FR-003)

- `pr_url` must match `https://<host>/<owner>/<repo>/pull/<n>` (host, owner and repo limited to `[A-Za-z0-9_.-]`); otherwise gap `missing`, "unparseable pr_url". Arguments go to the runner as a list, never through a shell.
- Read 1: `gh pr view <pr_url> --json state,mergedAt,closedAt,headRefOid,statusCheckRollup,url`.
- Read 2: `gh api --hostname <host> --paginate repos/<owner>/<repo>/pulls/<n>/reviews --jq '.[] | {id, state, submitted_at, html_url, user: .user.login}'`, one JSON object per line. REST gives the numeric review id and its `html_url`, which `gh pr view --json reviews` lacks.
- Default runner: `subprocess.run(["gh", *args], capture_output=True, text=True, timeout=60)`. Nothing reads or stores credentials.

### Gap classification (FR-012)

| Condition | Class |
|---|---|
| runner raises `OSError` (`gh` not installed) | `inaccessible` |
| exit 4, or stderr names `gh auth login` or `HTTP 401` | `inaccessible` |
| stderr `Could not resolve to a PullRequest` or `HTTP 404` | `missing` |
| stderr `Could not resolve to a Repository`, `HTTP 403` or `Resource not accessible` | `inaccessible` (GitHub hides private repositories as unresolvable) |
| `subprocess.TimeoutExpired`, any other non-zero exit | `transient` |
| unparseable JSON or wrong shape (`state` not `OPEN`/`CLOSED`/`MERGED`, `headRefOid` not hex, non-list rollup, review without integer `id` or string `state`/`user`) | `transient` |
| existing outcome file unreadable or malformed | `inaccessible`, file kept |
| backlog entry at the target name unreadable or owned by another run | `inaccessible` |
| outcome or backlog lock still held after the 5 s wait | `transient` |

Each gap is `{run, pr_url, class, reason}`; `reason` carries the first stderr line or the exception text. No retry (FR-013).

### Outcome capture (FR-004, FR-005)

- Check runs: `conclusion` in `FAILURE`, `TIMED_OUT`, `STARTUP_FAILURE`; id `check:<name>@<headRefOid>`, `event_at` = `completedAt`, `url` = `detailsUrl`.
- Status contexts: `state` `FAILURE` only (`ERROR`, `PENDING`, `SUCCESS` ignored per FR-004's "every other conclusion"); name = `context`, `event_at` = `startedAt`, `url` = `targetUrl`.
- Two runs of one check on one head commit share an id: the first in response order is kept (observed on PR 15: two `test` runs from push and pull_request workflows).
- Reviews: `state` `CHANGES_REQUESTED`; id `review:<id>`, `event_at` = `submitted_at`, `url` = `html_url`, `detail` `{reviewer}`.
- PR state: `MERGED` gives `state:merged` (`mergedAt`); `CLOSED` gives `state:closed` (`closedAt`).
- Missing times or links are stored as `null`/`""`, never invented. Values are lowercased conclusions; names keep GitHub's text.

### Data model

Outcome file:

```json
{"run": {"repo": "...", "branch": "...", "spec_dir": "...", "pr_url": "..."},
 "outcomes": [{"id": "check:test@b167...", "kind": "check", "event_at": "...",
   "recorded_at": "...", "url": "...", "detail": {"name": "test", "conclusion": "failure"}}]}
```

`kind` is `check` | `review` | `state`; `detail` is `{name, conclusion}`, `{reviewer}` or `{}`. Records are append-only; a stored id is never rewritten (FR-007).

Feedback entry (`improvements/<repo-name>-<branch>.<repo-hash>.feedback.<kind>.<subject>.json`, the retro naming rule):

```json
{"name": "...", "kind": "feedback", "run": {"repo", "branch", "spec_dir"},
 "signal_key": "ci-failure:test", "evidence": ["https://..."],
 "suggested_feature": "Prevent factory PRs failing CI check 'test' (seen on run 020-x)",
 "factory_sha": "...", "status": "ready", "exported_at": "...", "claimed_at": null}
```

- Keys: `ci-failure:<slug(name)>`, `changes-requested:<slug(login)>`, `pr-closed:unmerged`; `state:merged` maps to nothing. Slug: lowercase, runs outside `[a-z0-9-]` become one `-`, trimmed, at most 64 characters, `unnamed` when empty.
- Templates: `Prevent factory PRs failing CI check '<name>' (seen on run <branch>)`; `Address the changes <reviewer> requests on factory PRs (seen on run <branch>)`; `Find why factory PRs are closed without merging (seen on run <branch>)`. Untrusted names are reduced to one printable line, at most 100 characters, before templating.
- `add_feedback`: create a `ready` entry when absent; on `ready`, append links not already present (empty links skipped); on `claimed`, leave untouched and report it. No cap, no cross-run cover. Result `{created, updated, claimed}`.

### Write order and integrity (FR-006, FR-009, FR-010, ENG-26)

Per run: read the outcome file (no lock) for the terminal check and to compute new outcomes; fetch; on success, `add_feedback` for new actionable outcomes under the backlog lock; then, under the outcomes lock, re-read, append ids not yet stored with `recorded_at` = now, and write atomically when anything changed. A backlog failure leaves both files untouched. An outcome-write failure after the backlog succeeded repeats the same new outcomes next refresh, and `add_feedback` is idempotent for them. A concurrent refresh never loses records: each write re-reads under its lock. The archive is opened read-only.

`_acquire_backlog_lock` becomes `_acquire_home_lock(directory, harness)`, shared by the backlog and outcome writes.

### CLI contract (FR-013)

`factory feedback [<branch>] [--repo <path>]` prints:

```json
{"refreshed": [{"run": "...", "pr_url": "...", "new_outcomes": [...],
  "backlog": {"created": [], "updated": [], "claimed": []}}],
 "skipped": [{"run": "...", "reason": "terminal outcome recorded"}],
 "gaps": [{"run": "...", "pr_url": "...", "class": "transient", "reason": "..."}]}
```

Exit 0 without gaps (zero runs included), 1 with any gap or a refused `<branch>`, 5 usage.

### Route (FR-001)

`SKILL.md` step 0: `feedback [<branch>]` runs `SHELL: python3 <F>/bin/factory feedback [<branch>]`, shows each refreshed run's new outcomes and backlog changes, skipped runs and every gap with class and reason, then stops. No other route refreshes.

### Quality constraints

- Security: untrusted GitHub text is never executed; it is validated, slugged for keys and file names, and reduced to one line for feature text. `pr_url` parts are pattern-checked; `gh` gets argument lists. No credentials stored or logged.
- Errors and limits: 60 s timeout per `gh` call; a failed run never stops the others. ENG-24's retry guidance yields to FR-013: refresh is manual, so the user re-runs.
- Compatibility: Run exports and Retro entries unchanged (FR-011); retro `add` already filters `kind: retro`.
- Observability: the JSON report is the record; no logs.

## Test seams

- Seam: `factory_cli.feedback.refresh(home, repo, branch=None, gh=run_gh, now=None)` with an injected fake runner - discovery, `<branch>` narrowing, terminal skip, capture and ignore rules, ids, dedup across refreshes, new-commit outcome, archive byte-identical, other runs refreshed beside a gap. Failure paths: `gh` missing -> inaccessible; unauthenticated -> inaccessible; PR not found -> missing; no access -> inaccessible; transient error (5xx/network/timeout) -> transient; malformed JSON from either read -> transient; unparseable `pr_url` -> missing; malformed existing outcome file -> inaccessible, file unchanged; lock held past the wait -> transient. Each: nothing written for that run, earlier outcomes and entries intact.
- Seam: `factory_cli.improvements` feedback entries (`add_feedback`, `list_backlogs`, `claim`) - create, append to `ready`, untouched `claimed`, one entry per run per key, separate runs, merged not actionable, listing shows `kind`/`signal_key`/`suggested_feature`, Run export and Retro regressions. Failure paths: unreadable or foreign file at the entry name -> refused, not overwritten; backlog lock held past the wait -> refused, nothing written.
- Seam: `bin/factory feedback [<branch>]` CLI with a fake `gh` executable on `PATH` (exercises the default `run_gh`) - JSON shape, exit 0 with no gaps and with zero runs. Failure paths: unknown `<branch>` -> exit 1, nothing written; `<branch>` without `pr_url` -> exit 1, nothing written; `gh` not on `PATH` -> inaccessible gap, exit 1; fake `gh` failing with a server error -> transient gap, exit 1.
- Exempt: `DESIGN.md`, `CONTEXT.md`, `core/skills/factory/SKILL.md`, `core/skills/factory/references/state.md` - documentation only; rendering is verified by the build command.
- Overridden: none

Confirmed: 2026-11-04 - Q1 accepted - seams: `factory_cli.feedback.refresh`, `factory_cli.improvements` feedback entries (`add_feedback`, `list_backlogs`, `claim`), `bin/factory feedback [<branch>]` CLI; failure paths: `refresh` -> `gh` missing inaccessible, unauthenticated inaccessible, PR not found missing, no access inaccessible, transient error (5xx/network/timeout) transient, malformed JSON from either read transient, unparseable `pr_url` missing, malformed existing outcome file inaccessible with file unchanged, lock held past the wait transient, each writing nothing for that run and keeping earlier outcomes and entries; `improvements` -> unreadable or foreign file at the entry name refused and not overwritten, backlog lock held past the wait refused with nothing written; CLI -> unknown `<branch>` exit 1 nothing written, `<branch>` without `pr_url` exit 1 nothing written, `gh` not on `PATH` inaccessible gap exit 1, fake `gh` server error transient gap exit 1.

## Verification

- `python3 -m unittest discover -s tools` and the build command (all five harnesses render, `dist/` untracked, `bash -n install.sh`).
- Manual smoke, read-only: with a real archived run, `factory feedback <branch>` twice; the second run reports no new outcomes and changes no files.

## Complexity Tracking

None.
