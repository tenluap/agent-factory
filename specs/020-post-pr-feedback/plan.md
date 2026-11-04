# Implementation Plan: Post-PR Feedback

**Branch**: `020-post-pr-feedback` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/020-post-pr-feedback/spec.md`; decisions Q1-Q19; `CONTEXT.md`; ADR 0014.

## Summary

Add `factory feedback [<branch>] [--repo <path>]` and a `/factory feedback` route: a manual, read-only feedback refresh of the repository's archived runs with a `pr_url`, through one injectable `gh` runner. New PR outcomes go into a per-run outcome file `${FACTORY_HOME}/outcomes/<repo-name>-<branch>.json`; actionable ones become feedback entries for their source run. Problems become classified refresh gaps (`gaps`); exit 1.

## Technical Context

**Language/Version**: Python 3 standard library; Markdown skill prose.

**Primary Dependencies**: none new; `gh` (used by the PR step).

**Storage**: factory-home JSON: `outcomes/` (new), `improvements/` (new `feedback` kind); archive read only.

**Testing**: existing `unittest` runner, `tools/tests/`.

**Target Platform**: macOS/Linux shells under the five harnesses.

**Project Type**: CLI plus agent skill prose.

**Performance Goals**: two sequential `gh` reads per non-terminal run.

**Constraints**: read-only toward GitHub and archive; harness-neutral core.

**Scale/Scope**: tens of archived runs.

## Constitution Check

- **I. Design First**: PASS. `DESIGN.md` updated first.
- **II. Harness-Neutral Core**: PASS. The route uses `SHELL`; the CLI calls `gh`.
- **III. Generated Dist**: PASS. No `render.py` change; the build re-renders all harnesses.
- **IV. Stateless Agents**: PASS. No agent spawned.
- **V. Simplicity and Reuse**: PASS. Reuses `_write_atomic`, `backlog_name`, `factory_sha`, the lock wait, `main_repo`, `parse_iso`/`iso`.

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
DESIGN.md, CONTEXT.md                    # design record, limitations; `evidence` type per kind
tools/tests/test_feedback.py             # NEW
tools/tests/test_improvements.py         # feedback entry tests
```

**Structure Decision**: new `feedback.py`; `commands.py` is run state, `improvements.py` stays sole backlog writer (ENG-6, ENG-13).

### New files, abstractions, dependencies

- `core/skills/factory/bin/factory_cli/feedback.py` - file - GitHub reads, gap classification and the outcome file have no existing home; keeps `gh` out of run-state and backlog code.
- `tools/tests/test_feedback.py` - file - tests for the new seams; inline `gh` fixtures.
- `feedback.run_gh(args) -> (returncode, stdout, stderr)` - abstraction - the single injectable GitHub runner (Q9, FR-014).
- `feedback.Gap(cls, reason)` - abstraction - one exception carrying a gap class, so every failure point maps to `gaps` the same way.
- `improvements.add_feedback(home, run, items, now=None)` - abstraction - per-run upsert rules differ from retro `add` (cap, cross-run cover).
- Dependencies: none.

## Design

### Discovery (FR-002)

- Archived runs: `archive/*/state.json` whose `repo` equals `commands.main_repo(<--repo or cwd>)` (Q18) and whose `pr_url` is a non-empty string. An unreadable archive state is `skipped` with its reason, not a gap.
- `<branch>` narrows to one run. No such archived run, or no `pr_url`: `ValueError` before any `gh` call; CLI exit 1, nothing written, not a gap (Q12).
- Outcome file name: `improvements.backlog_name(repo, branch)` under `outcomes/`, matching the archive's `<repo-name>-<branch>`.
- A run whose outcome file holds `state:merged` or `state:closed` is listed under `skipped` and not fetched.

### GitHub reads (FR-003)

- `pr_url` must match `https://<host>/<owner>/<repo>/pull/<n>` (host, owner and repo limited to `[A-Za-z0-9_.-]`); otherwise gap `missing`, "unparseable pr_url". Arguments go to the runner as a list, never through a shell.
- Read 1: `gh pr view <pr_url> --json state,mergedAt,closedAt,headRefOid,statusCheckRollup,url`.
- Read 2: `gh api --hostname <host> --paginate repos/<owner>/<repo>/pulls/<n>/reviews --jq '.[] | {id, state, submitted_at, html_url, user: .user.login}'`, one JSON object per line (REST has the numeric id and `html_url`).
- Default runner: `subprocess.run(["gh", *args], capture_output=True, text=True, timeout=60)`. Nothing reads or stores credentials.

### Gap classification (FR-012)

| Condition | Class |
|---|---|
| runner raises `OSError` (`gh` not installed) | `inaccessible` |
| exit 4, or stderr names `gh auth login` or `HTTP 401` | `inaccessible` |
| stderr `Could not resolve to a PullRequest` or `HTTP 404` | `missing` |
| stderr `Could not resolve to a Repository`, `HTTP 403` or `Resource not accessible` | `inaccessible` |
| `subprocess.TimeoutExpired`, any other non-zero exit | `transient` |
| unparseable JSON or wrong shape (`state` not `OPEN`/`CLOSED`/`MERGED`, `headRefOid` not hex, non-list rollup, a review that is not an object with a string `state`, a `CHANGES_REQUESTED` review without an integer `id`) | `transient` |
| existing outcome file unreadable or malformed | `inaccessible`, file kept |
| backlog entry at the target name unreadable or owned by another run | `inaccessible`, both files kept |
| outcome or backlog lock still held after the 5 s wait | `transient`, both files kept |
| outcome-file write fails after the backlog write | `transient`, backlog links kept |

Each gap is `{run, pr_url, class, reason}`; `reason` is the first stderr line or exception text.

### Outcome capture (FR-004, FR-005)

- Check runs: `conclusion` in `FAILURE`, `TIMED_OUT`, `STARTUP_FAILURE`; id `check:<name>@<headRefOid>`, `event_at` = `completedAt`, `url` = `detailsUrl`.
- Status contexts: `state` `FAILURE` only (`ERROR`, `PENDING`, `SUCCESS` ignored per FR-004's "every other conclusion"); name = `context`, `event_at` = `startedAt`, `url` = `targetUrl`.
- Two runs of one check on one head commit share an id; the first in response order is kept.
- Reviews: `state` `CHANGES_REQUESTED`; id `review:<id>`, `event_at` = `submitted_at`, `url` = `html_url`, `detail` `{reviewer}`. A null login (deleted account) is stored as `ghost`; other reviews need no `id` (Q13).
- PR state: `MERGED` gives `state:merged` (`mergedAt`); `CLOSED` gives `state:closed` (`closedAt`).
- Missing times or links are stored as `null`/`""`, never invented. Conclusions lowercased; names verbatim.

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
- `add_feedback`: create a `ready` entry when absent; on `ready`, append new non-empty links; on `claimed`, leave untouched and report it. Result `{created, updated, claimed}`.
- `evidence` is a list here and a string on Retro entries; `CONTEXT.md` and `DESIGN.md` state the type per kind.

### Write order and integrity (FR-006, FR-009, FR-010, ENG-26)

Per run (FR-010, Q10): read the outcome file unlocked for the terminal skip; fetch; take the outcomes lock, re-read and compute unstored ids; `add_feedback` under the nested backlog lock; then append the new outcomes (`recorded_at` = now) and write atomically. Lock order is always outcomes then backlog; retro `add` and `claim` take only the backlog lock, so no deadlock. A lock timeout or refused backlog entry writes nothing. A failed outcome write after the backlog write is a `transient` gap: links stay, and the next refresh re-sees the ids while `add_feedback` skips present links. The archive is opened read-only.

`_acquire_backlog_lock` becomes `_acquire_home_lock(directory, harness)` for both writes. `feedback.py` imports `_write_atomic` by name, so a test can fail the outcome write alone.

### CLI contract (FR-013)

`factory feedback [<branch>] [--repo <path>]` prints:

```json
{"refreshed": [{"run": "...", "pr_url": "...", "new_outcomes": [...],
  "backlog": {"created": [], "updated": [], "claimed": []}}],
 "skipped": [{"run": "...", "reason": "terminal outcome recorded | unreadable archive state"}],
 "gaps": [{"run": "...", "pr_url": "...", "class": "transient", "reason": "..."}]}
```

Exit 0 without gaps (zero runs included), 1 with any gap or a refused `<branch>`, 2 when `--repo` is not a git repository (`main_repo`), 5 usage. `--repo` uses the existing `value_flags` convention.

### Route (FR-001)

`SKILL.md` step 0: `feedback [<branch>]` runs `SHELL: python3 <F>/bin/factory feedback [<branch>]`, shows new outcomes, backlog changes, skipped runs and every gap with class and reason, then stops. No other route refreshes. The `improve` route also shows each entry's `kind` and `signal_key` (US3 AS7).

### Quality constraints

- Security: untrusted GitHub text is validated, slugged, one-lined, never executed; no credentials stored.
- Errors and limits: 60 s `gh` timeout; no retry (FR-013 over ENG-24).
- Compatibility: Run exports and Retro entries unchanged; retro `add` filters `kind: retro`.
- Observability: the JSON report is the record; no logs.
- Known limitations, recorded in `DESIGN.md`: a reopened PR is missed after `state:closed` (ADR 0014); `ERROR` status contexts are ignored (Q4); moved checkouts' runs are not found.

## Test seams

Injection: a fake runner passed as `gh`; bad files, foreign entries and held locks (`lock.acquire`) planted in a temporary factory home; the outcome-file write failed by patching `factory_cli.feedback._write_atomic` to raise `OSError`.

- Seam: `factory_cli.feedback.refresh(home, repo, branch=None, gh=run_gh, now=None)` - discovery, narrowing, terminal skip, capture/ignore rules, null login as `ghost`, ids, dedup, new-commit outcome, archive byte-identical, other runs refreshed beside a gap. Failure paths: `gh` missing -> inaccessible; unauthenticated -> inaccessible; PR not found -> missing; no access -> inaccessible; transient error (5xx/network/timeout) -> transient; malformed JSON or shape from either read (including a review not an object with a string `state`, or a `CHANGES_REQUESTED` review without an integer `id`) -> transient; unparseable `pr_url` -> missing; malformed existing outcome file -> inaccessible; foreign or unreadable backlog file at the entry name -> inaccessible; outcomes lock held past the wait -> transient; backlog lock held past the wait -> transient; each writing nothing for that run and keeping earlier outcomes and entries. Outcome-file write failing after the backlog write -> transient, backlog links kept, next refresh stores the outcomes with no duplicate link. `<branch>` naming no archived run, or a run without `pr_url` -> `ValueError`, runner never called, nothing written. Unreadable archive state -> listed under `skipped`, not a gap.
- Seam: `factory_cli.improvements` feedback entries (`add_feedback`, `list_backlogs`, `claim`) - create, append to `ready`, untouched `claimed`, one entry per run per key, separate runs, merged not actionable, listing shows `kind`/`signal_key`/`suggested_feature`, Run export and Retro regressions. Failure paths: unreadable or foreign file at the entry name -> refused, not overwritten; backlog lock held past the wait -> refused, nothing written.
- Seam: `bin/factory feedback [<branch>] [--repo <path>]` CLI with a fake `gh` executable on `PATH` (exercises the default `run_gh`) - JSON shape with `refreshed`/`skipped`/`gaps`, exit 0 with no gaps and with zero runs, `--repo` selects that repository's runs from another directory. Failure paths: unknown `<branch>` -> exit 1, not a gap, nothing written; `<branch>` without `pr_url` -> exit 1, not a gap, nothing written; `--repo` not a git repository -> exit 2, nothing written; `gh` not on `PATH` -> inaccessible gap, exit 1; fake `gh` failing with a server error -> transient gap, exit 1.
- Exempt: `DESIGN.md`, `CONTEXT.md`, `core/skills/factory/SKILL.md`, `core/skills/factory/references/state.md` - documentation only; rendering is verified by the build command.
- Exempt: final verification task - runs the build and test commands, changes no file.
- Overridden: none

Confirmed: 2026-11-04 - Q20 accepted - seams: `factory_cli.feedback.refresh`, `factory_cli.improvements` feedback entries, `bin/factory feedback` CLI; failure paths: refresh -> `gh` missing, unauthenticated, no access, malformed outcome file, foreign or unreadable backlog file (inaccessible); PR not found, unparseable `pr_url` (missing); transient error, malformed JSON or shape from either read incl. review shape and `CHANGES_REQUESTED` without integer `id`, outcomes lock held, backlog lock held, patched `_write_atomic` outcome write failing after the backlog write (transient); unknown `<branch>`, `<branch>` without `pr_url` (`ValueError`); unreadable archive state (skipped); improvements -> unreadable or foreign entry file, backlog lock held (refused); CLI -> unknown `<branch>`, `<branch>` without `pr_url` (exit 1), `--repo` not git (exit 2), `gh` not on `PATH` (inaccessible, exit 1), server error (transient, exit 1); exempt: `DESIGN.md`, `CONTEXT.md`, `SKILL.md`, `state.md`, final verification task; overridden: none.

## Verification

- The test and build commands.
- Manual smoke: `factory feedback <branch>` twice on a real run; the second reports nothing new.

## Complexity Tracking

None.
