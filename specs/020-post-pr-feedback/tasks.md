---
description: "Task list for Post-PR Feedback"
---

# Tasks: Post-PR Feedback

**Input**: `specs/020-post-pr-feedback/` — plan.md, spec.md

**Tests**: Required (engineering.md, "Commit units"). Every behavior-changing task is one checkbox and one commit: failing test, then implementation, then passing check. Its commit body carries a `Red:` line in one of the two engineering.md forms. Plan-exempt tasks carry their exemption instead.

**Test command**: `python3 -m unittest discover -s tools`. **Build**: the run's build command (render all five harnesses, `dist/` untracked, `bash -n install.sh`).

**Seams** (plan.md "Test seams", confirmed 2026-11-04, plan-Q1): S1 `factory_cli.feedback.refresh(home, repo, branch=None, gh=run_gh, now=None)` with an injected fake runner; S2 `factory_cli.improvements` feedback entries (`add_feedback`, `list_backlogs`, `claim`); S3 `bin/factory feedback [<branch>]` CLI with a fake `gh` executable on `PATH`.

**UI**: none. No task is `[UI]`.

**Fixtures**: archived runs at `<home>/archive/<repo-name>-<branch>/state.json` in a temp home; inline `gh` response dicts.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallelizable (different files, no unfinished dependency); **[Story]**: US1-US4 from spec.md

---

## Phase 1: Setup

No setup. The repository already has the `unittest` runner and `tools/tests.Sandbox`.

---

## Phase 2: Foundational (design first)

**Purpose**: Record the design before any core change (constitution I, FR-015).

- [ ] T001 Add a "Post-PR feedback" subsection under "Time budget, issues, improvement backlog, benchmark" in `DESIGN.md`, after "Post-run retro". Cover: the manual `factory feedback [<branch>] [--repo <path>]` command and `/factory feedback` route (no other route refreshes); discovery of archived runs of the current repository with a `pr_url`, terminal skip; the two read-only `gh` reads through one injectable runner, 60 s timeout, no retries; captured outcomes, ids (`check:<name>@<head-sha>`, `review:<id>`, `state:merged|closed`) and record fields; the outcome file `${FACTORY_HOME}/outcomes/<repo-name>-<branch>.json`, append-only under the home-level lock; the `feedback` entry kind, its three signal keys, slug and template rules, one entry per run and key, append to `ready`, never touch `claimed`; the gap classes and table; write order; JSON report and exit codes 0/1/5; merge and deployment out of scope. Exempt: `DESIGN.md` - documentation only. Done when the subsection exists and names every item above.
- [ ] T002 [P] Update `CONTEXT.md`: the **Improvement backlog** entry names three kinds (Run exports, Retro entries, Feedback entries); add **Feedback refresh**, **PR outcome**, **Outcome file**, **Feedback entry** and **Gap** with one-line definitions matching spec.md "Key Entities" and an `_Avoid_` line each. Depends on T001. Exempt: `CONTEXT.md` - documentation only. Done when the five terms are present and the backlog entry names three kinds.

**Checkpoint**: Design recorded.

---

## Phase 3: User Story 1 - See CI failures and change requests against the original run (P1) 🎯 MVP

**Goal**: A refresh records failed checks, change requests and terminal state per archived run, read-only.

**Independent test**: Archive a run with a `pr_url`, inject one failed check and one change-request review, call `refresh`, and confirm the outcome file holds both records with ids, times and links.

- [ ] T003 [US1] Capture outcomes into the outcome file (seam S1, base paths). Files: `core/skills/factory/bin/factory_cli/feedback.py` (new), `core/skills/factory/bin/factory_cli/improvements.py`, `tools/tests/test_feedback.py` (new). Depends on T001.
  1. Failing tests in `tools/tests/test_feedback.py` with a fake runner recording its argument lists: an archived run of this repo with `pr_url` `https://github.com/o/r/pull/7`; read 1 args are `pr view <pr_url> --json state,mergedAt,closedAt,headRefOid,statusCheckRollup,url`, read 2 args are `api --hostname github.com --paginate repos/o/r/pulls/7/reviews --jq ...`. A check run concluding `FAILURE`, `TIMED_OUT` or `STARTUP_FAILURE` stores `check:<name>@<headRefOid>` with `kind: check`, `event_at` = `completedAt`, `recorded_at` = injected `now`, `url` = `detailsUrl`, `detail` `{name, conclusion}` (conclusion lowercased); a status context in `FAILURE` stores its `context` name, `startedAt`, `targetUrl`; a `CHANGES_REQUESTED` review stores `review:<id>`, `submitted_at`, `html_url`, `detail` `{reviewer}`; `MERGED` stores `state:merged` (`mergedAt`), `CLOSED` stores `state:closed` (`closedAt`), both `detail` `{}`. Ignored: `SUCCESS`, `CANCELLED`, `NEUTRAL`, `SKIPPED` checks, `ERROR`/`PENDING`/`SUCCESS` contexts, `APPROVED`/`COMMENTED` reviews. Two runs of one check on one head share an id and the first in response order is kept. Missing times/links store `null`/`""`. The file body is `{run: {repo, branch, spec_dir, pr_url}, outcomes: [...]}` at `<home>/outcomes/<repo-name>-<branch>.json`. Runs of another repo, runs without `pr_url` and unreadable archive states are not fetched; zero runs gives empty `refreshed`, `skipped`, `gaps`. The archive tree is byte-identical after the refresh. Observe red.
  2. Implement `feedback.py`: `run_gh(args)` (default runner, `subprocess.run(["gh", *args], capture_output=True, text=True, timeout=60)`, returns `(returncode, stdout, stderr)`), discovery via `improvements.backlog_name`, `pr_url` pattern parse, the two reads, capture rules and `refresh(...)` returning the plan's report shape. Rename `improvements._acquire_backlog_lock(directory)` to `_acquire_home_lock(directory, harness)` and update its `add` and `claim` callers; write the outcome file with `improvements._write_atomic` under `_acquire_home_lock(<home>/outcomes, "feedback")`, re-reading under the lock. Use `state.iso` for `now`.
  3. Run the test command and the build command; existing `test_improvements.py` lock and claim tests still pass.
  Red proof: `Red: <capture test name> failed as expected`. Done when the S1 capture tests pass and the archive byte-identity assertion holds.
- [ ] T004 [US1] Narrow a refresh to one run (seam S1). Files: `core/skills/factory/bin/factory_cli/feedback.py`, `tools/tests/test_feedback.py`. Depends on T003.
  1. Failing tests: with two archived runs, `refresh(..., branch="<b>")` fetches only `<b>` (runner called only with its `pr_url`) and writes only its outcome file. Failure paths (plan S1 discovery, surfaced by S3 in T010): a `<branch>` naming no archived run, or a run without `pr_url`, raises `ValueError` naming the reason; the runner is never called and nothing is written. Observe red.
  2. Implement the `branch` filter and the two refusals (reuse `ValueError`; no new exception class).
  3. Run the test command; pass.
  Red proof: `Red: <branch narrowing test name> failed as expected`. Done when narrowing and both refusals pass.

**Checkpoint**: Outcomes captured per run (entry point in T010).

---

## Phase 4: User Story 2 - Refreshing again creates no duplicates (P1)

**Goal**: Repeat refreshes never rewrite or duplicate stored outcomes.

**Independent test**: Refresh twice with the same response; the outcome file bytes are unchanged by the second refresh.

- [ ] T005 [US2] Deduplicate across refreshes and skip terminal runs (seam S1). Files: `core/skills/factory/bin/factory_cli/feedback.py`, `tools/tests/test_feedback.py`. Depends on T004.
  1. Failing tests: a second refresh with the same response and a later `now` leaves the outcome file byte-identical and reports no new outcomes; a stored record keeps its `recorded_at`; a re-run failing check on the same head adds nothing; the same check failing on a new `headRefOid` adds one record; a run whose file holds `state:merged` or `state:closed` is listed under `skipped` with reason `terminal outcome recorded` and the runner is not called for it; a fake runner that appends a record to the outcome file during the fetch (a concurrent refresh) leaves both that record and the new ones stored. Observe red.
  2. Implement: compute new outcomes against the stored ids; under the outcomes lock re-read, append only ids not yet stored, write only when anything changed; terminal check before fetching.
  3. Run the test command; pass.
  Red proof: `Red: <second refresh unchanged test name> failed as expected`. Done when SC-002 holds for the outcome file and the concurrent-append test keeps both records.

---

## Phase 5: User Story 3 - Actionable outcomes feed the improvement backlog (P2)

**Goal**: Failed checks, change requests and unmerged closes become `ready` `feedback` entries for their run.

**Independent test**: Refresh with one failed check, then `list_backlogs`; one `feedback` entry with key `ci-failure:<slug>`, the run, the link and a one-line suggested feature.

- [ ] T006 [P] [US3] Add feedback backlog entries (seam S2). Files: `core/skills/factory/bin/factory_cli/improvements.py`, `tools/tests/test_improvements.py`. Depends on T003.
  1. Failing tests in `tools/tests/test_improvements.py`: `add_feedback(home, run, items, now)` with items `{signal_key, evidence, suggested_feature}` creates `<repo-name>-<branch>.<repo-hash>.feedback.<kind>.<subject>.json` (retro naming rule, `:` to `.`) with body `name`, `kind: "feedback"`, `run: {repo, branch, spec_dir}`, `signal_key`, `evidence: [links]`, `suggested_feature`, `factory_sha`, `status: "ready"`, `exported_at`, `claimed_at: null`; a second call for the same run and key appends only new non-empty links to the `ready` entry; a `claimed` entry is left byte-identical and reported in `claimed`; two runs with one key get two entries; the result is `{created, updated, claimed}`; no cap (five keys give five entries). `list_backlogs` shows a feedback entry's `kind`, `signal_key` and stored `suggested_feature`; `claim` claims it. Regressions: retro `add` ignores feedback entries for cover and cap; Run export bodies unchanged. Failure paths: an unreadable file, or one owned by another run, at the target name is refused (raises) and not overwritten; the backlog lock held past the 5 s wait is refused and nothing is written. Observe red.
  2. Implement `add_feedback` under `_acquire_home_lock(<home>/improvements, "improvements")` with `_write_atomic`; scan once for own-run `feedback` entries.
  3. Run the test command; pass, including existing `ExportTests` and retro tests.
  Red proof: `Red: <add_feedback create test name> failed as expected`. Done when every S2 test passes.
- [ ] T007 [US3] Map new actionable outcomes to feedback entries (seam S1). Files: `core/skills/factory/bin/factory_cli/feedback.py`, `tools/tests/test_feedback.py`. Depends on T005, T006.
  1. Failing tests: a new failed check `Lint / test` gives key `ci-failure:lint-test` and feature `Prevent factory PRs failing CI check 'Lint / test' (seen on run <branch>)`; a change request by `Some.User` gives `changes-requested:some-user` and `Address the changes Some.User requests on factory PRs (seen on run <branch>)`; `state:closed` gives `pr-closed:unmerged` and `Find why factory PRs are closed without merging (seen on run <branch>)`; `state:merged` gives no entry. Slug: lowercase, runs outside `[a-z0-9-]` become one `-`, trimmed, at most 64 chars, `unnamed` when empty. A name with a newline and 300 chars is reduced to one printable line of at most 100 chars in the feature. The report's `backlog` field carries the `add_feedback` result. Only new outcomes reach the backlog: a second refresh with the same response changes no backlog file (SC-002). Observe red.
  2. Implement key, slug and template functions and call `improvements.add_feedback` before the outcome write.
  3. Run the test command; pass.
  Red proof: `Red: <ci-failure entry test name> failed as expected`. Done when the three keys, the merged exclusion and backlog idempotence pass.

---

## Phase 6: User Story 4 - Fetch problems never invent results (P2)

**Goal**: Every fetch or local-file problem becomes a classified gap; nothing is written for that run; other runs still refresh.

**Independent test**: Inject each failure in turn; the run's files are unchanged, it is under `gaps` with its class, and a second healthy run is refreshed.

- [ ] T008 [US4] Classify GitHub failures as gaps (seam S1). Files: `core/skills/factory/bin/factory_cli/feedback.py`, `tools/tests/test_feedback.py`. Depends on T007.
  1. Failing tests, each with a stored outcome and a `ready` feedback entry for the failing run and a second healthy run. Failure paths: runner raises `OSError` -> `inaccessible`; exit 4, or stderr naming `gh auth login` or `HTTP 401` -> `inaccessible`; stderr `Could not resolve to a PullRequest` or `HTTP 404` -> `missing`; stderr `Could not resolve to a Repository`, `HTTP 403` or `Resource not accessible` -> `inaccessible`; `subprocess.TimeoutExpired` or a 5xx/network non-zero exit -> `transient`; unparseable JSON or wrong shape from read 1 (`state` outside `OPEN`/`CLOSED`/`MERGED`, non-hex `headRefOid`, non-list rollup) or read 2 (review without integer `id` or string `state`/`user`) -> `transient`; unparseable `pr_url` -> `missing` with reason `unparseable pr_url` and no runner call. Each: gap `{run, pr_url, class, reason}` with the first stderr line or exception text; outcome file and backlog entries byte-identical; each read called at most once (no retry); the healthy run is refreshed. Observe red.
  2. Implement `Gap(cls, reason)` and the classification table; catch `Gap` per run.
  3. Run the test command; pass.
  Red proof: `Red: <gh missing inaccessible test name> failed as expected`. Done when every GitHub failure path passes (SC-003).
- [ ] T009 [US4] Classify local-file failures as gaps (seam S1). Files: `core/skills/factory/bin/factory_cli/feedback.py`, `tools/tests/test_feedback.py`. Depends on T008.
  1. Failing tests. Failure paths: an unreadable or malformed existing outcome file -> `inaccessible`, file unchanged, no backlog write; the outcomes lock held past the 5 s wait -> `transient`, nothing written for that run; the backlog lock held past the wait -> `transient`, both files untouched; a foreign or unreadable backlog file at the entry name -> `inaccessible`, both files untouched. Also: an outcome write that fails after the backlog succeeded leaves the next refresh to re-add the same outcomes with no duplicate backlog link. Observe red.
  2. Implement: map `lock.LockHeld` to `transient` and malformed outcome files and refused backlog writes to `inaccessible`; keep the write order of the plan.
  3. Run the test command; pass.
  Red proof: `Red: <malformed outcome file test name> failed as expected`. Done when the local failure paths pass and no failed run writes a file.

---

## Phase 7: Entry points (US1 command, FR-001, FR-013)

- [ ] T010 [US1] Add the `factory feedback` command (seam S3). Files: `core/skills/factory/bin/factory_cli/cli.py`, `core/skills/factory/bin/factory_cli/commands.py`, `tools/tests/test_feedback.py`. Depends on T009.
  1. Failing tests through `Sandbox.cli` with `FACTORY_HOME` set and a fake `gh` script on `PATH` returning inline JSON (exercises the default `run_gh`): `factory feedback` prints `{refreshed, skipped, gaps}` and exits 0 with no gaps; exits 0 with zero runs; `factory feedback <branch>` refreshes one run. Failure paths: unknown `<branch>` -> exit 1, nothing written; `<branch>` without `pr_url` -> exit 1, nothing written; `gh` not on `PATH` -> `inaccessible` gap, exit 1; fake `gh` exiting with an HTTP 502 message -> `transient` gap, exit 1. Extra positional arguments exit 5. Observe red.
  2. Implement `commands.cmd_feedback(repo, branch)` (`main_repo`, `factory_home`, `ValueError` to `die(1, ...)`; print the report and exit 1 when `gaps` is non-empty) and the `feedback [<branch>]` dispatch and USAGE line in `cli.py`.
  3. Run the test command and the build command; pass.
  Red proof: `Red: <cli exit 0 test name> failed as expected`. Done when every S3 test passes.
- [ ] T011 [US1] Add the `feedback [<branch>]` route to `core/skills/factory/SKILL.md` step 0 and the `argument-hint`: `SHELL: python3 <F>/bin/factory feedback [<branch>]`; show each refreshed run's new outcomes and backlog changes, skipped runs and every gap with class and reason; on exit 1 show the reported gaps; stop. State that no other route refreshes. Use only `SHELL`. Depends on T010. Exempt: `core/skills/factory/SKILL.md` - documentation only. Done when the route is present and harness-neutral.
- [ ] T012 [P] [US1] Add the CLI line `python3 <F>/bin/factory feedback [<branch>]` to the CLI section of `core/skills/factory/references/state.md`: read-only refresh of archived runs' PR outcomes into `outcomes/` and `feedback` backlog entries; exit 1 on any gap. Depends on T010. Exempt: `core/skills/factory/references/state.md` - documentation only. Done when the line is present.

---

## Phase 8: Polish

- [ ] T013 Run the build command and the full test command; confirm `git status` shows no `dist/` files. Manual read-only smoke when a real archived run with a `pr_url` exists: `factory feedback <branch>` twice; the second reports no new outcomes and changes no files. Depends on T001-T012. Exempt: verification only, no code change. Done when both commands pass.

---

## Dependencies

- T002 after T001; T003 after T001; T004 after T003; T005 after T004.
- US3: T006 after T003 (parallel with T004/T005); T007 after T005 and T006.
- US4: T008 after T007; T009 after T008.
- Entry points: T010 after T009; T011 and T012 after T010 (parallel).
- T013 last.

T003-T005 and T007-T009 edit `feedback.py`; run them in order. Parallel: T006 with T004/T005; T011 with T012; T002 with T003.

## Implementation strategy

MVP is T001-T005: outcomes captured and deduplicated through the S1 seam. T006-T007 feed the backlog; T008-T009 make every failure a gap; T010-T012 expose the command and route last, because the exit codes need gap classification. Each task is one passing commit.
