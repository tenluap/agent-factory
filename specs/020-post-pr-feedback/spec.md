# Feature Specification: Post-PR Feedback

**Feature Branch**: `020-post-pr-feedback`

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Collect post-PR feedback: implement the plan at docs/superpowers/plans/2026-11-03-factory-post-pr-feedback-plan.md (read-only refresh of a published run's PR state, checks and review decisions; store outcomes with stable identifiers, timestamps and evidence links, deduplicated across refreshes; feed actionable outcomes into the improvement backlog with the originating run attached; handle missing/inaccessible PRs and transient GitHub errors without inventing results; merge and deployment stay out of scope)."

## Clarifications

### Grill 2026-11-04

- Q1: How is the refresh triggered? → A: A new CLI command `factory feedback [<branch>]` plus a `/factory feedback` route in the factory skill that runs it and shows the result. Manual only; no other route refreshes automatically.
- Q2: Which runs does a refresh cover? → A: Every archived run of the current repository that has a `pr_url`; an optional `<branch>` narrows it to one run. A run whose merged or closed outcome is already recorded is not fetched again.
- Q3: Where are outcomes stored? → A: In a sidecar file `${FACTORY_HOME}/outcomes/<repo-name>-<branch>.json`, written atomically under a lock like the improvement backlog. The run archive stays byte-identical.
- Q4: Which outcomes are captured? → A: Checks (check runs and status contexts) concluding `failure`, `timed_out` or `startup_failure`; reviews in state `CHANGES_REQUESTED`; PR terminal state `MERGED` or `CLOSED` (unmerged). Passed checks, approvals, comments and cancellations are ignored.
- Q5: How are fetch problems handled? → A: `gh` missing or unauthenticated, PR not found, no access, transient (network or server) errors and malformed responses are classified as `missing`, `inaccessible` or `transient`. Nothing is written for that run, it is listed under `gaps` in the output, other runs still refresh, and the command exits 1 when any gap exists. No automatic retries.
- Q6: What identifies an outcome? → A: `check:<check-name>@<head-sha>`, `review:<github-review-id>`, `state:merged` / `state:closed`. Each record holds `id`, `kind`, `event_at`, `recorded_at`, `url` and `detail`. A re-seen outcome is left unchanged.
- Q7: How do outcomes reach the improvement backlog? → A: A new entry kind `feedback` with signal keys `ci-failure:<check-slug>`, `changes-requested:<reviewer-slug>` and `pr-closed:unmerged`; a merged PR is not actionable. One entry per run and signal key; a repeat sighting appends new evidence links to that run's `ready` entry and leaves a `claimed` entry untouched. No per-run cap and no cross-run "covered" skip.
- Q8: Who writes the suggested feature text? → A: A deterministic one-line template in the CLI, usable unchanged as `/factory <feature>`. No agent is spawned.
- Q9: What is the test seam? → A: One injectable GitHub runner in the new module; tests inject fakes returning fixtures or failing. Injected failure paths: `gh` missing, unauthenticated, PR not found, no access, transient error, malformed JSON. Formal seam confirmation happens at plan.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See CI failures and change requests against the original run (Priority: P1)

A factory maintainer has several archived runs whose PRs are open on GitHub. They run `/factory feedback`. The factory reads each run's PR, records every failed check and every request for changes against the archived run that produced the PR, and shows what it found. The maintainer now knows which factory runs produced PRs that CI or a human rejected.

**Why this priority**: This is the core learning signal the feature exists for: without visible outcomes per run, nothing downstream can use them.

**Independent Test**: Archive a run with a `pr_url`, inject a GitHub response with one failed check and one change-request review, run `factory feedback`, and confirm the run's outcome file holds both outcomes with their identifiers, times and evidence links, and the command output lists them.

**Acceptance Scenarios**:

1. **Given** an archived run with a `pr_url` whose PR has a check concluding `failure` on its head commit, **When** the maintainer runs `factory feedback`, **Then** the run's outcome file holds one `check:<check-name>@<head-sha>` record with its GitHub time, first-sighting time, evidence link and check name and conclusion.
2. **Given** the PR has a review in state `CHANGES_REQUESTED`, **When** the refresh runs, **Then** one `review:<github-review-id>` record is stored naming the reviewer.
3. **Given** the PR is merged, **When** the refresh runs, **Then** a `state:merged` record is stored; **Given** it is closed without merging, **Then** a `state:closed` record is stored.
4. **Given** the PR has only passed checks, approvals, comments or cancelled checks, **When** the refresh runs, **Then** no outcome is stored for them.
5. **Given** a `<branch>` argument, **When** the refresh runs, **Then** only that archived run is refreshed.
6. **Given** the refresh finishes, **When** the maintainer inspects the run archive, **Then** it is byte-identical to before.

---

### User Story 2 - Refreshing again creates no duplicates (Priority: P1)

The maintainer runs `/factory feedback` daily. A failure seen yesterday is still there today. The outcome file and the improvement backlog show it once, with its original first-sighting time.

**Why this priority**: The plan's acceptance requires that refreshing twice creates no duplicate outcome or improvement candidate; without it the data is unusable.

**Independent Test**: Run the refresh twice against the same injected response and confirm the outcome file and backlog entries are unchanged by the second run.

**Acceptance Scenarios**:

1. **Given** an outcome already recorded, **When** a later refresh sees the same outcome, **Then** the stored record is left unchanged, including its `recorded_at`.
2. **Given** a check is re-run on the same commit and fails again, **When** the refresh runs, **Then** it is the same outcome and no new record is stored.
3. **Given** a new push makes the same check fail on a new head commit, **When** the refresh runs, **Then** a new outcome is stored for the new commit.
4. **Given** a run whose `state:merged` or `state:closed` outcome is already recorded, **When** the refresh runs, **Then** that run is not fetched again.

---

### User Story 3 - Actionable outcomes feed the improvement backlog (Priority: P2)

A failed CI check, a change request or a PR closed without merging becomes a `ready` improvement backlog entry carrying the originating run and the evidence links. The maintainer sees it in `/factory improve` and can start a run with its suggested feature text unchanged.

**Why this priority**: This closes the self-improvement loop, but the recorded outcomes are already useful without it.

**Independent Test**: Run the refresh against an injected failed check, then list the improvement backlog and confirm one `feedback` entry with signal key `ci-failure:<check-slug>`, the originating run, the evidence link and a one-line suggested feature.

**Acceptance Scenarios**:

1. **Given** a new failed-check outcome, **When** the refresh runs, **Then** the run gains one `ready` `feedback` entry with signal key `ci-failure:<check-slug>`, its evidence link and the originating run.
2. **Given** a new change-request outcome, **Then** the entry's signal key is `changes-requested:<reviewer-slug>`; **Given** a `state:closed` outcome, **Then** it is `pr-closed:unmerged`.
3. **Given** a `state:merged` outcome, **When** the refresh runs, **Then** no backlog entry is written for it.
4. **Given** the run already has a `ready` entry for the signal key and a new outcome maps to it, **When** the refresh runs, **Then** the new evidence link is appended to that entry and no second entry is created.
5. **Given** the run's entry for the signal key is `claimed`, **When** a new outcome maps to it, **Then** the entry is left untouched and no new entry is created.
6. **Given** two different runs see the same signal key, **When** both refresh, **Then** each run has its own entry.
7. **Given** a `feedback` entry, **When** the maintainer lists the backlog, **Then** it shows its `kind`, `signal_key` and suggested feature text, which can start a run unchanged.

---

### User Story 4 - Fetch problems never invent results (Priority: P2)

GitHub is unreachable, the maintainer is signed out, or a PR was deleted. The refresh records nothing for the affected run, keeps its last known outcomes, reports the gap with its class, refreshes the other runs, and exits non-zero.

**Why this priority**: A wrong outcome would mislead the improvement loop; the plan requires gaps to be reported, not guessed.

**Independent Test**: Inject each failure path in turn and confirm the run's outcome file and backlog are unchanged, the run is listed under `gaps` with its class, other runs still refresh, and the exit code is 1.

**Acceptance Scenarios**:

1. **Given** the GitHub CLI is missing or unauthenticated, **When** the refresh runs, **Then** each affected run is listed under `gaps` as `inaccessible` and nothing is written for it.
2. **Given** the PR is not found, **Then** the run is listed as `missing`; **Given** the account has no access, **Then** `inaccessible`.
3. **Given** a network or server error or a malformed response, **Then** the run is listed as `transient`, and its previously stored outcomes and backlog entries stay intact.
4. **Given** one run fails and another succeeds, **When** the refresh runs, **Then** the successful run's outcomes are stored and the command exits 1.
5. **Given** no gaps, **When** the refresh finishes, **Then** the command exits 0.
6. **Given** any failure, **When** the refresh runs, **Then** it does not retry automatically.

### Edge Cases

- No archived run of the current repository has a `pr_url`: the refresh reports zero runs and exits 0.
- A `<branch>` names no archived run, or a run without a `pr_url`: the command reports it and writes nothing.
- An archived run's outcome file is missing: it is created on the first successful refresh.
- An existing outcome file is unreadable or malformed: the run is reported as a gap and the file is not overwritten.
- A check has no evidence link in the response: the record stores no link rather than an invented one (assumption; see Assumptions).
- Two refreshes run at once: the lock serialises writes to each outcome file and to the backlog; neither loses records.
- A refresh is interrupted mid-write: atomic writes leave each file either fully old or fully new.
- A reviewer login or check name contains characters unsafe for a signal key: it is reduced to a slug; the full name stays in `detail`.
- A PR is both merged and has failed checks: both are recorded; only the checks are actionable.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The factory MUST provide a `factory feedback [<branch>]` CLI command and a `/factory feedback` route that runs it and shows its result. Other routes MUST NOT trigger a refresh.
- **FR-002**: A refresh MUST cover every archived run of the current repository that has a `pr_url`, or only the named run when `<branch>` is given, and MUST skip runs whose `state:merged` or `state:closed` outcome is already recorded.
- **FR-003**: The refresh MUST read PR state, check outcomes (check runs and status contexts) and review decisions through the configured GitHub account, read-only. It MUST NOT write to GitHub, merge or deploy.
- **FR-004**: The refresh MUST record checks concluding `failure`, `timed_out` or `startup_failure`, reviews in state `CHANGES_REQUESTED`, and PR terminal states `MERGED` and `CLOSED` (unmerged), and MUST ignore every other check conclusion, review state and comment.
- **FR-005**: Each outcome MUST carry a stable `id` (`check:<check-name>@<head-sha>`, `review:<github-review-id>`, `state:merged` or `state:closed`), `kind`, `event_at` (GitHub time), `recorded_at` (first sighting), `url` (evidence link) and `detail` (check name and conclusion, or reviewer).
- **FR-006**: Outcomes MUST be stored in `${FACTORY_HOME}/outcomes/<repo-name>-<branch>.json`, written atomically under a lock. The run archive MUST stay byte-identical.
- **FR-007**: A refresh that sees an outcome whose `id` is already stored MUST leave that record unchanged.
- **FR-008**: Each new actionable outcome MUST map to a `feedback` improvement backlog entry for its run with signal key `ci-failure:<check-slug>`, `changes-requested:<reviewer-slug>` or `pr-closed:unmerged`. A `state:merged` outcome MUST NOT produce an entry.
- **FR-009**: Each run MUST have at most one `feedback` entry per signal key. A new outcome mapping to a `ready` entry MUST append its evidence link to that entry; one mapping to a `claimed` entry MUST leave it untouched. The refresh MUST NOT cap entries per run or skip a signal key another run's entry already covers.
- **FR-010**: A `feedback` entry MUST carry `kind: feedback`, its `signal_key`, its originating run, its evidence links and a deterministic one-line `suggested_feature` usable unchanged as `/factory <feature>`. Backlog writes MUST be atomic and under the backlog lock.
- **FR-011**: The existing improvement listing and claim flow MUST handle `feedback` entries; Run exports and Retro entries MUST behave as before.
- **FR-012**: Fetch problems MUST be classified as `missing` (PR not found), `inaccessible` (`gh` missing, unauthenticated or no access) or `transient` (network or server error, malformed response). For an affected run nothing MUST be written; the run MUST be listed under `gaps` with its class and a reason; other runs MUST still refresh.
- **FR-013**: The command MUST print JSON naming each refreshed run with its new outcomes and backlog changes, and the `gaps`. It MUST exit 1 when any gap exists and 0 otherwise. It MUST NOT retry automatically.
- **FR-014**: All GitHub access MUST go through one injectable runner so tests replace it with fakes; the command MUST store no credential.
- **FR-015**: `DESIGN.md` MUST record the feedback refresh before core and adapter files change; the new route MUST stay harness-neutral in `core/` and render for every harness.

### Key Entities

- **Archived run**: An existing run archive; read only. Its `pr_url` and branch locate the PR and name the outcome file.
- **PR outcome**: One meaningful GitHub event for a run's PR (failed check, change request, terminal state), with stable `id`, `kind`, `event_at`, `recorded_at`, `url` and `detail`.
- **Outcome file**: The per-run sidecar in the factory home holding that run's PR outcomes.
- **Feedback entry**: A new improvement backlog entry kind: one per run and signal key, carrying evidence links, the originating run and suggested feature text.
- **Gap**: A run the refresh could not read, with its class (`missing`, `inaccessible`, `transient`) and reason.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of failed checks and change requests on an archived run's PR appear against that run after one successful refresh.
- **SC-002**: Two consecutive refreshes with no new GitHub events change zero outcome records and zero backlog entries.
- **SC-003**: Under every injected fetch failure, zero outcomes or backlog entries are written for the affected run, its last known outcomes are unchanged, and the gap is reported.
- **SC-004**: 100% of `feedback` entries can start a run with their suggested feature text unchanged.
- **SC-005**: Zero writes are made to GitHub and zero archived run files change during any refresh.

## Assumptions

- Gap classes map as: PR not found → `missing`; `gh` missing, unauthenticated or no access → `inaccessible`; network or server error and malformed response → `transient`.
- An outcome without an evidence link in the GitHub response is stored with an empty `url`; no link is invented.
- A slug lowercases a name and replaces each run of characters outside letters, digits and hyphens with one hyphen.
- The refresh reads only the head commit's checks as GitHub reports them for the PR; earlier commits' checks are seen only if an earlier refresh caught them.
- The refresh is bounded by the number of archived runs with a `pr_url`; each run costs a small, fixed number of GitHub reads.
- The `<repo-name>` in the outcome file name matches the run archive's naming.
- Merging, deployment and any write to GitHub are out of scope.
