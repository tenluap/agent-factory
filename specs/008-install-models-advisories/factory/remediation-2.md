# Remediation — analyze pass 2

Fixes applied in place to the existing artifacts; no artifact regenerated. Word budgets after edits: `spec.md` 2994/3000, `plan.md` 1675/2000, `tasks.md` 2426/2500 (untouched). The confirmed seam list is unchanged.

- **A2** (Ambiguity, MEDIUM, `spec.md` Assumptions): both Assumptions bullets now read "007 FR-015" ("the brief's decisions enumerate only 007 FR-015…", "The settled 007 FR-015 decision…"), matching the FR group heading; bare "FR-015" remains only for this spec's digest-totals requirement (`spec.md` FR-015).
- **I3** (Inconsistency, LOW, `plan.md` structure vs `tasks.md` T038): the `tools/tests/test_state.py` structure comment now reads "exactly-one-open-relay-round rule; `replay.py` import-vocabulary assertions", and the `tools/tests/replay.py` defect-detector seam line now names its test module ("asserted from `tools/tests/test_state.py`"); the seam name and the `Confirmed:` line are untouched.
- **I4** (Inconsistency, LOW, `plan.md` quality constraints vs `spec.md` SC-001/SC-002): the malformed-`config.json` item is moved out of the SC-002/SC-003 five-path list and cited as "covered by SC-001", so the refusal-path list matches SC-002's enumeration.

No finding required a user decision; `pending_clarify` is empty. Pass-1 residue from C1, I2 and S1 stayed resolved (verified in `analyze-2.md`).
