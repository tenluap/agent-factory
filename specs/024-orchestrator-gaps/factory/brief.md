# Brief: close run-018 orchestrator bookkeeping gaps

Source backlog: `claude-factory-018-orchestrator-gaps` (improvements export, checked against main c385ab5).

Four recorded observations from run 018-live-conformance (claude-code), all in the factory's own tooling:

1. No CLI writer updates `review.round` / `review.fix_rounds`; `checkpoint review` and `checkpoint fix` leave both at 0, so the SKILL.md step-7 fix-round cap (`fix_rounds < 2`) and `bench.py score` read stale values. Run 018's orchestrator hand-edited state.json (commit 9dc242c), contradicting FR-001/FR-002.
2. `ledger-add`'s detected-overrun detail misstates the excess: it prints total duration as "ran Ns past its Bs budget". A 319s spawn on a 300s budget should read the excess (19s) or "against".
3. The 300s default budget is too tight for round-1 full-diff reviews (all three round-1 reviewers overran in run 018; every delta round fit). Round-1 reviews need a larger budget; delta rounds keep 300s.
4. A relay question raised by a review verdict (requires_user seam confirmation) has no writer rendering the human-readable relay record (`factory/relay/<stage>-<qid>.md` in run 018 was hand-written).

Chain: **lite** (cruise default; the feature is well-bounded CLI/reference work).
