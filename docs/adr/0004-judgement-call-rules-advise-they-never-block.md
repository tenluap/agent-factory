# Judgement-call engineering rules advise; they never block

**Revised 2026-10-25:** The expanded quality checklist distinguishes guidance from demonstrated defects. This revision replaces the original blanket HIGH rating for duplication and extends the advisory principle to guidance-only findings throughout the checklist.

A finding based only on design or style guidance, including clean code, SOLID, functional preferences and over-engineering (`ENG-7`..`ENG-10`), is at most MEDIUM and never blocking, for both reviewer and judge. This ceiling overrides default severity guidance. Lower an overrated preference rather than dropping it so the user can still see it. Letting preferences block was rejected: a run halted on taste trains users to approve past review.

A demonstrated correctness, security, integrity, resource-limit, stated-performance or documented-contract failure is rated by its consequence and cites the violated requirement or applicable engineering rule. A design preference affecting the same code does not downgrade that defect. Test-first, red-proof and seam requirements (`ENG-1`..`ENG-5`) keep their enforcement. A reuse finding (`ENG-6`) establishes shared business meaning and the consequence of duplicating it; similar-looking code alone does not establish a defect or a HIGH severity.

Consequently those findings are advisory: a fix round driven by a verdict performs no fix work on them. They reach the user in the judge verdict's advisory list and on the existing approver screen, and the user's route to having one fixed is the approver's existing "Request changes", which sends the run back with the finding named and is implemented exactly as asked, like any other change request.

The same ceiling applies at artifact time. The plan must state a reason for each new file, new abstraction and new dependency (`ENG-10`), and analyze reports a missing reason as a MEDIUM, non-blocking finding: a plan-time gate that makes over-engineering visible without stopping the run.

## Consequences

- No new gate, list, severity level or stage exists for advisory findings; the verdict's advisory list and the approver screen carry them, and the approver screen is unchanged.
- An advisory finding keeps its `ENG-n` citation in the existing verdict entry (named in `summary`, evidence reachable through `sources`), so no verdict field is added.
- An advisory finding can ship unfixed. That is the accepted cost of not halting runs on judgement calls, and the user sees every one before approving.
- Reviewers and the judge distinguish design guidance from evidenced defects using the shared severity policy. An architecture preference cannot block delivery or excuse a concrete defect.
