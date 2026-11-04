---
description: "Task list for Post-PR Feedback"
---

# Tasks: Post-PR Feedback

**Input**: `specs/020-post-pr-feedback/` — plan.md, spec.md; `CONTEXT.md`; ADR 0014

**Tests**: Required (engineering.md, "Commit units"). Each behavior-changing task is one checkbox and commit: failing test, implementation, passing check, and a `Red:` line. Plan-exempt tasks carry their exemption instead.

**Test command**: `python3 -m unittest discover -s tools`. **Build**: the run's build command (render all five harnesses, `dist/` untracked, `bash -n install.sh`).

**Seams** (plan.md "Test seams", confirmed 2026-11-04, Q20): S1 `factory_cli.feedback.refresh(home, repo, branch=None, gh=run_gh, now=None)` with an injected fake runner; S2 `factory_cli.improvements` feedback entries (`add_feedback`, `list_backlogs`, `claim`); S3 `bin/factory feedback [<branch>] [--repo <path>]` CLI with a fake `gh` executable on `PATH`. Every failure path below is plan-declared; T003-T010 cover them all.

**UI**: none. No task is `[UI]`.

**Fixtures**: temp-home archived runs `<home>/archive/<repo-name>-<branch>/state.json`; inline `gh` responses.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallelizable (different files, no unfinished dependency); **[Story]**: US1-US4 from spec.md

---

## Phase 1: Setup

None: `unittest` and `tools/tests.Sandbox` exist.

---

## Phase 2: Foundational (design first)

**Purpose**: Record the design before any core change (constitution I, FR-015).

- [ ] T001 Add a "Post-PR feedback" subsection under "Time budget, issues, improvement backlog, benchmark" in `DESIGN.md`, after "Post-run retro", citing ADR 0014. Cover: the `factory feedback [<branch>] [--repo <path>]` command and `/factory feedback` route (no other route refreshes); discovery, terminal skip, unreadable archives `skipped`; two read-only `gh` reads via one injectable runner, 60 s timeout, no retry; outcome ids, outcome fields, `ghost` for a null login; the outcome file; the `feedback` kind, signal keys, slug and templates, one entry per run and key, `ready`/`claimed` rules; `evidence` type per kind; the gap table; nested lock order (outcomes then backlog, outcome write last); the report and exit codes 0/1/2/5; known limitations (reopened PR missed, `ERROR` contexts ignored, moved checkouts' runs not found); merge and deployment out of scope. Exempt: `DESIGN.md` - documentation only. Done when the subsection names every item above.
- [ ] T002 [P] Update `CONTEXT.md`. grill-with-docs already wrote the Post-PR feedback terms (**Feedback refresh**, **PR outcome**, **Outcome id**, **Outcome file**, **Feedback entry**, **Refresh gap**) and the three-kind **Improvement backlog**; add only that `evidence` is a list of links on a **Feedback entry** and a string on a **Retro entry**. Depends on T001. Exempt: `CONTEXT.md` - documentation only. Done when both entries state the `evidence` type and the existing terms are unchanged.

---

## Phase 3: User Story 1 - See CI failures and change requests against the original run (P1) 🎯 MVP

**Goal**: A refresh records failed checks, change requests and terminal state per archived run, read-only.

**Independent test**: inject one failed check and one change request for an archived run; the outcome file holds both with ids, times and links.

- [ ] T003 [US1] Capture outcomes into the outcome file (seam S1, base paths). Files: `core/skills/factory/bin/factory_cli/feedback.py` (new), `core/skills/factory/bin/factory_cli/improvements.py`, `tools/tests/test_feedback.py` (new). Depends on T001.
  1. Failing tests in `tools/tests/test_feedback.py` with a fake runner recording its arguments: an archived run of this repo with `pr_url` `https://github.com/o/r/pull/7`; read 1 args are `pr view <pr_url> --json state,mergedAt,closedAt,headRefOid,statusCheckRollup,url`, read 2 args are `api --hostname github.com --paginate repos/o/r/pulls/7/reviews --jq ...`. A check concluding `FAILURE`, `TIMED_OUT` or `STARTUP_FAILURE` stores `check:<name>@<headRefOid>`, `kind: check`, `event_at` = `completedAt`, `recorded_at` = injected `now`, `url` = `detailsUrl`, `detail` `{name, conclusion}` (lowercased); a `FAILURE` status context stores its `context`, `startedAt`, `targetUrl`; a `CHANGES_REQUESTED` review stores `review:<id>`, `submitted_at`, `html_url`, `detail` `{reviewer}`, and a null login gives reviewer `ghost`; `MERGED` stores `state:merged` (`mergedAt`), `CLOSED` `state:closed` (`closedAt`), both `detail` `{}` and read 1 `url`. Ignored: `SUCCESS`, `CANCELLED`, `NEUTRAL`, `SKIPPED` checks, `ERROR`/`PENDING`/`SUCCESS` contexts, `APPROVED`/`COMMENTED` reviews. Same check and head share an id, first kept; missing times/links store `null`/`""`. The file body is `{run: {repo, branch, spec_dir, pr_url}, outcomes: [...]}` at `<home>/outcomes/<repo-name>-<branch>.json`. Runs of another repo or without `pr_url` are not fetched. Declared S1 path: an unreadable archive `state.json` is listed under `skipped` with reason `unreadable archive state`, not a gap. Zero runs gives empty lists; the archive stays byte-identical. Observe red.
  2. Implement `feedback.py`: `run_gh(args)` (`subprocess.run(["gh", *args], capture_output=True, text=True, timeout=60)`, returns `(returncode, stdout, stderr)`), discovery via `improvements.backlog_name`, `pr_url` parse, the two reads, capture rules and `refresh(...)` returning the plan's report. Rename `improvements._acquire_backlog_lock(directory)` to `_acquire_home_lock(directory, harness)` and update the `add` and `claim` callers. Import `_write_atomic` by name (`from factory_cli.improvements import _write_atomic`) so T009 can patch `factory_cli.feedback._write_atomic`; write the outcome file with it under `_acquire_home_lock(<home>/outcomes, "feedback")`, re-reading under the lock. Use `state.iso` for `now`.
  3. Run the test and build commands; existing `test_improvements.py` tests pass.
  Red proof: `Red: <capture test name> failed as expected`. Done when the S1 capture and `skipped` tests pass and the archive byte-identity assertion holds.
- [ ] T004 [US1] Narrow a refresh to one run (seam S1). Files: `core/skills/factory/bin/factory_cli/feedback.py`, `tools/tests/test_feedback.py`. Depends on T003.
  1. Failing tests: with two archived runs, `refresh(..., branch="<b>")` fetches only `<b>` (runner called only with its `pr_url`) and writes only its outcome file. Declared S1 failure paths: a `<branch>` naming no archived run, or a run without `pr_url`, raises `ValueError` naming the reason; the runner is never called and nothing is written. Observe red.
  2. Implement the `branch` filter and the two refusals (reuse `ValueError`; no new exception class).
  3. Run the test command; pass.
  Red proof: `Red: <branch narrowing test name> failed as expected`. Done when narrowing and both refusals pass.

---

## Phase 4: User Story 2 - Refreshing again creates no duplicates (P1)

**Goal**: Repeat refreshes never rewrite or duplicate stored outcomes.

**Independent test**: a second identical refresh leaves the outcome file bytes unchanged.

- [ ] T005 [US2] Deduplicate across refreshes and skip terminal runs (seam S1). Files: `core/skills/factory/bin/factory_cli/feedback.py`, `tools/tests/test_feedback.py`. Depends on T004.
  1. Failing tests: a second refresh with the same response and a later `now` leaves the outcome file byte-identical and reports no new outcomes; a stored outcome keeps its `recorded_at`; a re-run failing check on the same head adds nothing; the same check failing on a new `headRefOid` adds one outcome; a run whose file holds `state:merged` or `state:closed` is under `skipped` with reason `terminal outcome recorded` and is not fetched; an outcome appended to the outcome file during the fetch (concurrent refresh) is kept beside the new ones. Observe red.
  2. Implement: terminal check on an unlocked read before fetching; after the fetch take the outcomes lock, re-read, compute ids not yet stored, append them and write only when anything changed.
  3. Run the test command; pass.
  Red proof: `Red: <second refresh unchanged test name> failed as expected`. Done when SC-002 holds for the outcome file and the concurrent-append test keeps both outcomes.

---

## Phase 5: User Story 3 - Actionable outcomes feed the improvement backlog (P2)

**Goal**: Failed checks, change requests and unmerged closes become `ready` `feedback` entries for their run.

**Independent test**: one failed check gives one listed `feedback` entry with key `ci-failure:<slug>`, the run, the link and a suggested feature.

- [ ] T006 [P] [US3] Add feedback backlog entries (seam S2). Files: `core/skills/factory/bin/factory_cli/improvements.py`, `tools/tests/test_improvements.py`. Depends on T003.
  1. Failing tests in `tools/tests/test_improvements.py`: `add_feedback(home, run, items, now)` with items `{signal_key, evidence, suggested_feature}` creates `<repo-name>-<branch>.<repo-hash>.feedback.<kind>.<subject>.json` (retro naming rule, `:` to `.`) with body `name`, `kind: "feedback"`, `run: {repo, branch, spec_dir}`, `signal_key`, `evidence: [links]`, `suggested_feature`, `factory_sha`, `status: "ready"`, `exported_at`, `claimed_at: null`; a repeat for the same run and key appends only new non-empty links to a `ready` entry; a `claimed` entry stays byte-identical and is reported; two runs with one key get two entries; result `{created, updated, claimed}`; no cap. `list_backlogs` shows a feedback entry's `kind`, `signal_key` and stored `suggested_feature`; `claim` claims it. Regressions: retro `add` ignores feedback entries for cover and cap; Run export bodies unchanged. Declared S2 failure paths: an unreadable or foreign file at the target name is refused (existing `AddError`), not overwritten; the backlog lock (`lock.acquire` planted) held past the 5 s wait is refused (`AddError` from `lock.LockHeld`), nothing written. Observe red.
  2. Implement `add_feedback` under `_acquire_home_lock(<home>/improvements, "improvements")` with `_write_atomic`, reusing `AddError` (no new exception class); scan once for own-run `feedback` entries.
  3. Run the test command; pass, including existing `ExportTests` and retro tests.
  Red proof: `Red: <add_feedback create test name> failed as expected`. Done when every S2 test passes.
- [ ] T007 [US3] Map new actionable outcomes to feedback entries (seam S1). Files: `core/skills/factory/bin/factory_cli/feedback.py`, `tools/tests/test_feedback.py`. Depends on T005, T006.
  1. Failing tests: a new failed check `Lint / test` gives key `ci-failure:lint-test` and feature `Prevent factory PRs failing CI check 'Lint / test' (seen on run <branch>)`; a change request by `Some.User` gives `changes-requested:some-user` and `Address the changes Some.User requests on factory PRs (seen on run <branch>)`; `state:closed` gives `pr-closed:unmerged` and `Find why factory PRs are closed without merging (seen on run <branch>)`; `state:merged` gives no entry. Slug: lowercase, runs outside `[a-z0-9-]` become one `-`, trimmed, at most 64 chars, else `unnamed`. A 300-char name with a newline becomes one printable line of at most 100 chars. The report's `backlog` field carries the `add_feedback` result. Only new outcomes reach the backlog: a second refresh with the same response changes no backlog file (SC-002). Observe red.
  2. Implement key, slug and template functions; call `improvements.add_feedback` while holding the outcomes lock (nested backlog lock, order outcomes then backlog), before the outcome write.
  3. Run the test command; pass.
  Red proof: `Red: <ci-failure entry test name> failed as expected`. Done when the three keys, the merged exclusion and backlog idempotence pass.

---

## Phase 6: User Story 4 - Fetch problems never invent results (P2)

**Goal**: Every fetch or local-file problem becomes a classified gap; other runs still refresh.

**Independent test**: each injected failure leaves the run's files unchanged and lists it under `gaps`; a healthy run still refreshes.

- [ ] T008 [US4] Classify GitHub failures as gaps (seam S1). Files: `core/skills/factory/bin/factory_cli/feedback.py`, `tools/tests/test_feedback.py`. Depends on T007.
  1. Failing tests, each with a stored outcome and a `ready` feedback entry for the failing run and a second healthy run. Declared S1 failure paths: runner raises `OSError` (`gh` missing) -> `inaccessible`; exit 4, or stderr naming `gh auth login` or `HTTP 401` (unauthenticated) -> `inaccessible`; stderr `Could not resolve to a PullRequest` or `HTTP 404` -> `missing`; stderr `Could not resolve to a Repository`, `HTTP 403` or `Resource not accessible` -> `inaccessible`; `subprocess.TimeoutExpired` or a 5xx/network non-zero exit -> `transient`; unparseable JSON or wrong shape from read 1 (`state` outside `OPEN`/`CLOSED`/`MERGED`, non-hex `headRefOid`, non-list rollup) or read 2 (a review not an object with a string `state`, or a `CHANGES_REQUESTED` review without an integer `id`) -> `transient`; unparseable `pr_url` -> `missing`, reason `unparseable pr_url`, no runner call. Not a gap: an `APPROVED` review without `id`. Each: gap `{run, pr_url, class, reason}` (first stderr line or exception text); files byte-identical; each read called at most once; the healthy run refreshed. Observe red.
  2. Implement `Gap(cls, reason)` and the classification table; catch `Gap` per run.
  3. Run the test command; pass.
  Red proof: `Red: <gh missing inaccessible test name> failed as expected`. Done when every GitHub failure path passes (SC-003).
- [ ] T009 [US4] Classify local-file failures as gaps (seam S1). Files: `core/skills/factory/bin/factory_cli/feedback.py`, `tools/tests/test_feedback.py`. Depends on T008.
  1. Failing tests, each with a stored outcome, a `ready` feedback entry and a second healthy run that still refreshes. Declared S1 failure paths, each writing nothing for that run and keeping earlier outcomes and entries byte-identical: a malformed existing outcome file -> `inaccessible`; a foreign or unreadable backlog file at the entry name -> `inaccessible`; the outcomes lock (`lock.acquire` planted on `<home>/outcomes`) held past the 5 s wait -> `transient`; the backlog lock planted on `<home>/improvements` held past the wait -> `transient`, outcome file unchanged. Then: `factory_cli.feedback._write_atomic` patched to raise `OSError` for the outcome write after the backlog write -> `transient`, the new backlog links kept; an unpatched second refresh stores the outcomes and adds no duplicate link. Observe red.
  2. Implement: map `lock.LockHeld` (direct, or as the cause of `AddError`) and a failed outcome write to `transient`; unreadable or malformed outcome files and other `AddError` refusals (written links stay) to `inaccessible`; keep the plan's nested lock order.
  3. Run the test command; pass.
  Red proof: `Red: <malformed outcome file test name> failed as expected`. Done when every local failure path passes and only the post-backlog write failure leaves a write behind.

---

## Phase 7: Entry points (US1 command, FR-001, FR-013)

- [ ] T010 [US1] Add the `factory feedback` command (seam S3). Files: `core/skills/factory/bin/factory_cli/cli.py`, `core/skills/factory/bin/factory_cli/commands.py`, `tools/tests/test_feedback.py`. Depends on T009.
  1. Failing tests through `Sandbox.cli` with `FACTORY_HOME` set and a fake `gh` script on `PATH` returning inline JSON (exercises the default `run_gh`): `factory feedback` prints `{refreshed, skipped, gaps}` and exits 0 with no gaps; exits 0 with zero runs; `factory feedback <branch>` refreshes one run; `--repo <path>` run from another directory selects that repository's runs. Declared S3 failure paths: unknown `<branch>` -> exit 1, not a gap, nothing written; `<branch>` without `pr_url` -> exit 1, not a gap, nothing written; `--repo` not a git repository -> exit 2, nothing written; `gh` not on `PATH` -> `inaccessible` gap, exit 1; fake `gh` exiting with an HTTP 502 message -> `transient` gap, exit 1. Observe red.
  2. Implement `commands.cmd_feedback(repo, branch)` (`main_repo` of `--repo` or cwd, `factory_home`, `ValueError` to `die(1, ...)`; print the report and exit 1 when `gaps` is non-empty) and the `feedback [<branch>] [--repo <path>]` dispatch (`value_flags=("--repo",)`) and USAGE line in `cli.py`.
  3. Run the test command and the build command; pass.
  Red proof: `Red: <cli exit 0 test name> failed as expected`. Done when every S3 test passes.
- [ ] T011 [US1] Add the `feedback [<branch>]` route to `core/skills/factory/SKILL.md` step 0 and the `argument-hint`: `SHELL: python3 <F>/bin/factory feedback [<branch>]`; show each refreshed run's new outcomes and backlog changes, skipped runs with reasons and every gap with class and reason; stop. State that no other route refreshes. Extend the `improve` route to show each entry's `kind` and `signal_key` (US3 AS7). Use only `SHELL`. Depends on T010. Exempt: `core/skills/factory/SKILL.md` - documentation only. Done when both routes read as above and stay harness-neutral.
- [ ] T012 [P] [US1] Add the CLI line `python3 <F>/bin/factory feedback [<branch>] [--repo <path>]` to the CLI section of `core/skills/factory/references/state.md`: read-only refresh of archived runs' PR outcomes into `outcomes/` and `feedback` backlog entries; report `refreshed`/`skipped`/`gaps`; exit 1 on any gap or refused `<branch>`, 2 when `--repo` is not a git repository. Depends on T010. Exempt: `core/skills/factory/references/state.md` - documentation only. Done when the line is present.

---

## Phase 8: Polish

- [ ] T013 Run the build command and the full test command; confirm `git status` shows no `dist/` files. Manual smoke, when a real archived run has a `pr_url`: `factory feedback <branch>` twice; the second reports nothing new. Depends on T001-T012. Exempt: final verification task - runs the build and test commands, changes no file. Done when both commands pass.

---

## Dependencies and strategy

Each task names its dependencies. T003-T005 and T007-T009 edit `feedback.py` in order; parallel: T002 with T003, T006 with T004/T005, T011 with T012. MVP is T001-T005; the command comes last because its exit codes need gap classification.
