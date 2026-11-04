# Remediation log (pass 2)

Source: `factory/analyze-2.md` (0 CRITICAL, 0 HIGH, 2 MEDIUM, 1 LOW). All fixed in place; nothing deferred to clarify.

- I1: spec.md FR-005 now covers only writes made after run state exists, and names the creation path as the exception that records a new run's initial `mode.cruise`. plan.md "Mode resolution" (`factory mode` caller) now says the orchestrator writes the printed JSON unchanged as the new pending file's `mode`, using the same creation write that records `mode` and `stop_at` today (SKILL.md "Route"). It calls this FR-005's only write outside the CLI, says step 3's `mode` record keeps `cruise` as created, and sends later changes through `resume`. T008's step-0 clause says the same. No new seam was added, so the confirmed test scope did not change.
- G1: T009's description and Done condition now name the three protocol.md statements with their cruise wording. Step 2's "(`mode.fast` true, except initial grilling)" adds that initial grilling is self-answered under cruise (FR-006). "Notify once per auto-accepted batch" becomes a log line under cruise (FR-019). The initial-grilling paragraph's "the user confirms shared understanding" adds the orchestrator's self-confirmation under cruise (FR-006). T009 remains exempt as documentation only.
- D1: the CONTEXT.md "Cruise override" definition now lists "a `pending_clarify` answer".

Word counts after the edits: spec.md 2998/3000, plan.md 1962/2000, tasks.md 2205/2500.
