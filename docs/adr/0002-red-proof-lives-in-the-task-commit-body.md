# Red proof lives in the task's commit body, verified by spec-conformance

Proof that a test was seen failing before the implementation is a `Red: <test name> failed as expected` line in the one commit that carries the task's test and implementation, and the spec-conformance reviewer checks each implementation commit body against `tasks.md`. Separate red commits were rejected because they leave the history non-bisectable, and a new state field or artefact was rejected because the commit is already the per-task unit the orchestrator creates and the reviewer can read the run's commit log in the same spawn as the diff.

## Consequences

- A behaviour already covered by an existing passing test cannot show a red run, so the body records `Red: not applicable - <existing test> already covers this` instead; no other wording counts as proof.
- The squashed diff carries no commit messages, so the reviewer reads `git log <base>..HEAD` (subjects and bodies) as well; the shared findings reference states that scope for any lens needing commit metadata, and a commit-level finding puts the sha in `file` and omits `line`.
- The fixing role commits all its fixes once, so that body carries one `Red:` line per behaviour-changing fix. In a verdict-driven fix round those lines are matched against the round's confirmed blocking findings, not against `tasks.md`, because a fix's test belongs to a finding rather than to a task.
- A user-changes fix round answers the user and no verdict, so its commit (`factory(fix): user changes`) is matched against neither the verdict nor `tasks.md`: the reviewer checks the grammar of each `Red:` line and that every behaviour-changing fix the diff shows carries one, and an empty confirmed-blocking list for the round is not by itself a finding. Matching the request's prose instead was rejected: a change request is not a finding list, and two reviewers reading it would disagree on the same commit.
- The proof is only as trustworthy as the role writing it. Verification is textual (a line matching a task), not a replay of the failing run; that is the accepted cost of keeping history bisectable.
