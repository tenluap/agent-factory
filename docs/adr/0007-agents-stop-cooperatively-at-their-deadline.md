# Agents stop cooperatively at their deadline

A spawn past its time budget is asked to stop, never killed: a file-writing role finishes the unit of work in flight, commits it, and returns `partial` with an overrun report, while roles that are never stopped (reviewers, the judge, orchestrator verify) are measured after the fact from the ledger. A hard kill (background spawn plus watchdog) bounds time exactly but loses uncommitted work and the role's own account of why it ran long — the very data the session issues and the improvement backlog exist to collect — and detect-only leaves runs unbounded, so both were rejected (brief, Q2/Q8). The trade is deliberate: time-to-stop is bounded by one unit of work rather than by the deadline itself, in exchange for trustworthy progress and self-reported causes.

## Consequences

- A role can overshoot its deadline by the unit of work in flight; the overshoot is recorded in the overrun report's detail rather than prevented.
- Resumption is bounded by the stall cap on stops without new progress, not by the deadline: three consecutive `partial` returns of one stage with no new commit between them halt the run, counting every partial return whatever its stop reason, never a failure-policy retry (a crash or unparseable output is not a partial return, and issue records carry a `partial_return` mark that tells the two apart), and never the overrun records of never-stopped roles (FR-004 is the authority).
- Enforcement lives in role prompts and writer-recorded facts, so it needs no harness capability beyond the `deadline` spawn input.
