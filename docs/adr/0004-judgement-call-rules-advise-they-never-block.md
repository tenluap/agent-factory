# Judgement-call engineering rules advise; they never block

The clean-code, SOLID, functional-style and over-engineering rules (`ENG-7`..`ENG-10`) are rated at most MEDIUM and are never blocking, by the reviewer that raises a finding and by the judge that rates it; this ceiling overrides the shared findings reference's default severity guidance. Only duplication (`ENG-6`) and behaviour added with no asserting test stay HIGH and blocking. A finding above the ceiling is lowered, never dropped, so the user still sees it. Letting these rules block was rejected: they are matters of taste and idiom, and a run halted on taste trains users to approve past review.

Consequently those findings are advisory: the run performs no fix work on them. They reach the user in the judge verdict's advisory list and on the existing approver screen, and the user's route to having one fixed is the approver's existing "Request changes", which sends the run back with the finding named.

The same ceiling applies at artifact time. The plan must state a reason for each new file, new abstraction and new dependency (`ENG-10`), and analyze reports a missing reason as a MEDIUM, non-blocking finding: a plan-time gate that makes over-engineering visible without stopping the run.

## Consequences

- No new gate, list, severity level or stage exists for advisory findings; the verdict's advisory list and the approver screen carry them, and the approver screen is unchanged.
- An advisory finding can ship unfixed. That is the accepted cost of not halting runs on judgement calls, and the user sees every one before approving.
- Reviewers and the judge need no severity negotiation: the rule id fixes the ceiling, so two agents rate the same finding the same way.
