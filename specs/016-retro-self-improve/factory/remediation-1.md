# Remediation — pass 1 (analyze-1.md)

- U1: plan.md signal grammar defines the fixer-recurring class as the first `ENG-n` id cited in a confirmed blocking finding's `evidence`, lower-cased; findings citing no `ENG-n` are not counted. Mirrored in tasks.md T001 and T008.
- U2: Retro inputs now include every recorded analyze report path (`analyze.reports` from `state.json`): spec.md FR-003, US1 scenario 1 and Run digest entity; plan.md role inputs, analyze-escalation definition and step 2; tasks.md T001, T008, T009.
- I1: spec.md FR-010 and Edge Cases reworded from "resumed run" to re-entry of the PR step's retro sub-step. plan.md step 9 states the manual recovery for a run interrupted between `pr-open` and the final push (`factory drop`, then `git push`). T001 (DESIGN.md) and T012 (SKILL.md) name it.
- I2: tasks.md T009 depends on T007 (task text and Dependencies section) and cites the T007 `signal_key` listing field.
- U3: spec.md FR-010, plan.md step 9 sub-steps 1 and 3, tasks.md T001/T009/T012 state that every retro spawn, failed attempts included, is ledgered, and that the marker is checked only on sub-step entry, so the in-turn retry is unaffected.
- I3: plan.md Project Structure lists `test_commands.py` instead of `test_state.py`.
- I4: spec.md FR-004 reads "recurring confirmed-blocking finding classes sent to the fixer".
- I5: spec.md FR-015 and Assumptions limit "covered" to `ready` entries from another run; the run's own `ready` entry is replaced in place.
- S1: spec.md Functional Requirements adds a note that FR IDs are stable and FR-015 to FR-017 sit next to the requirements they refine (no renumbering).
- S2: checklists/requirements.md note records the `factory improvements add` CLI and Retro entry fields as a settled grill-with-docs decision.

Test seams (S1-S4) and their failure paths are unchanged; the plan-Q1 confirmation stays current.
