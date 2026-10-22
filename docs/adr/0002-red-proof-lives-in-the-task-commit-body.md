# Red proof lives in the task's commit body, verified by spec-conformance

Proof that a test was seen failing before the implementation is a `Red: <test name> failed as expected` line in the one commit that carries the task's test and implementation, and the spec-conformance reviewer checks each implementation commit body against `tasks.md`. Separate red commits were rejected because they leave the history non-bisectable, and a new state field or artefact was rejected because the commit is already the per-task unit the orchestrator creates and the reviewers already read the run's diff.

## Consequences

- A behaviour already covered by an existing passing test cannot show a red run, so the body records `Red: not applicable - <existing test> already covers this` instead; no other wording counts as proof.
- The fixing role commits all its fixes once, so that body carries one `Red:` line per behaviour-changing fix.
- The proof is only as trustworthy as the role writing it. Verification is textual (a line matching a task), not a replay of the failing run; that is the accepted cost of keeping history bisectable.
