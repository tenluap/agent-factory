# Brief: Collect post-PR feedback

Source plan: `docs/superpowers/plans/2026-11-03-factory-post-pr-feedback-plan.md` (Priority 4).

After the factory opens a PR and the run is archived, the user runs a manual, read-only refresh (`/factory feedback`, or `factory feedback [<branch>]`) that reads each archived run's PR state, check outcomes and review decisions through the configured GitHub account (`gh`). Meaningful outcomes are stored against the archived run with stable identifiers, timestamps and evidence links, deduplicated across refreshes, and actionable outcomes are fed into the existing improvement backlog with the originating run and evidence attached. Missing or inaccessible PRs and transient GitHub errors never produce an invented result: the last known outcome stays intact and the gap is reported. Merge and deployment stay outside this workflow.

## Decisions

- **Trigger (Q1):** a new CLI command `factory feedback [<branch>]` plus a SKILL.md route `/factory feedback` that runs it and shows the result. Manual only; no automatic refresh on other routes.
- **Scope (Q2):** every archived run of the current repo that has a `pr_url`; an optional `<branch>` narrows to one run. Runs whose merged/closed outcome is already recorded are not fetched again.
- **Storage (Q3):** a sidecar file `${FACTORY_HOME}/outcomes/<repo-name>-<branch>.json`, written atomically under a lock like the improvement backlog. The run archive stays byte-identical ("written once, never overwritten").
- **Outcomes captured (Q4):** checks (check runs and status contexts) concluding `failure`, `timed_out` or `startup_failure`; reviews in state `CHANGES_REQUESTED`; PR terminal state `MERGED` or `CLOSED` (unmerged). Passed checks, approvals, comments and cancellations are ignored.
- **Fetch problems (Q5):** `gh` missing or unauthenticated, PR not found, no access, transient (network/5xx) errors and malformed responses are classified as `missing`, `inaccessible` or `transient`. Nothing is written for that run, the run is listed under `gaps` in the JSON output, other runs still refresh, and the command exits 1 when any gap exists. No automatic retries.
- **Outcome identity (Q6):** `check:<check-name>@<head-sha>` (a re-run on the same commit is the same outcome; a new push is a new outcome), `review:<github-review-id>`, `state:merged` / `state:closed`. Each record holds `id`, `kind`, `event_at` (GitHub time), `recorded_at` (first sighting), `url` (evidence link) and `detail` (check name and conclusion, or reviewer). A re-seen outcome is left unchanged.
- **Backlog feed (Q7):** a new improvement entry kind `feedback`, with signal keys `ci-failure:<check-slug>`, `changes-requested:<reviewer-slug>` and `pr-closed:unmerged`; a merged PR is not actionable. One entry per run and signal key; a repeat sighting appends new evidence links to that run's `ready` entry and leaves a `claimed` entry untouched. No per-run cap and no cross-run "covered" skip, so each entry keeps its originating run.
- **Suggested feature text (Q8):** a deterministic one-line CLI template (e.g. `Prevent factory PRs failing CI check '<name>' (seen on run <branch>)`), usable unchanged as `/factory <feature>`. No agent spawn.
- **Test seam (Q9):** one injectable `gh` runner in the new module; tests inject fakes returning fixtures or failing. Injected failure paths: `gh` missing, unauthenticated, PR not found, no access, transient error, malformed JSON. Formal seam confirmation happens at plan.
- **Out of scope:** merging, deployment, and any write to GitHub.
- **Chain:** `lite`, fast mode on (default mode); analyze escalates to `full` on CRITICAL/HIGH findings.
