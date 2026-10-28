# Conceptual Workflow Model

No production JSON schema change is proposed. Existing state versions, relay questions, decisions, ledger and issues remain authoritative.

- **Model setup result**: effective exact selection (or unresolved inheritance), installed source, inventory evidence, outcome `listed | unavailable | unverified`. Only a complete supported inventory can establish setup unavailability; errors/partial results are unverified. Listed does not imply provider access. Unavailable stops before resources; unverified retains bounded spawn handling.
- **Commit unit**: one new task, or one unambiguous legacy test/implementation pair. Contains seam/scope, observed red proof, implementation, required passing checks and single commit. States: pending → red/in-progress → passing committed. Only passing committed becomes checked. Ambiguity pauses behavior-changing work. Resume retains checked units and inspects incomplete work.
- **Confirmed scope**: ordered declaration of seam identities and injected failure paths plus separate explicit acceptance. Change of identity or scope invalidates acceptance. Fast mode cannot supply it. Analyze blocks missing declaration, uncovered paths or stale acceptance.
- **Verification handoff**: next unfinished unit, committed progress, required checks still pending and any real overshoot. Partial does not imply verification pass. Existing CLI verify evidence gates review; unchanged issue/stall rules judge no-progress partials by work commits.
