# Collect post-PR feedback

**Priority 4.** Let the factory learn from CI and human review outcomes after it opens a PR.

## Tasks

- [ ] Add a read-only refresh for a published run. Start with the PR URL already in its archive. Read PR state, check outcomes, and review decisions using the configured GitHub account.
- [ ] Store meaningful outcomes with stable identifiers, timestamps, and evidence links. Capture failed checks, requests for changes, and whether the PR merged or closed. Reuse the same record when a refresh sees the same event again.
- [ ] Feed actionable outcomes into the existing improvement backlog. Keep the originating run and its evidence attached to each suggestion.
- [ ] Handle missing or inaccessible PRs and transient GitHub errors without recording an invented result. Keep merge and deployment outside this workflow.

## Acceptance

A failed CI check or a human request for changes becomes visible against the original archived run. Refreshing twice creates no duplicate outcome or improvement candidate. A temporary fetch failure leaves the last known outcome intact and reports the gap.
