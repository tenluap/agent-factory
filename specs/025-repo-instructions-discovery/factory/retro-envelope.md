Retro for run 025 found no new candidates. Every signal is either already covered or below its threshold.

- **Halt-cluster:** below threshold. There are 3 issues: one `retry` in implement (code-build partial handoff after T004), plus one `verify-fail` and one `halt` in verify. The halt came from 8 tests that also fail on origin/main 0c3bf71. `verify-fail` is not a counted kind, so no stage has 2 or more counted issues.
- **Judge-rejection:** covered. The only rejection is SPEC-1 in round 1, a config-only change at ad4ec77, so 1 of 6 spec-conformance findings.
- **Fixer-recurring:** no evidence. `confirmed_blocking` is empty in all 3 rounds.
- **Analyze-escalation:** covered, and both reports show CRITICAL 0 and HIGH 0.
- **In-est-outlier:** fails the entry rule (reviewer peaks 2.35-2.39x the median with only 3 ledger entries each; spec-builder 11 entries, peak 1.93x).
- **Adoption:** `adopted` is null.

The state does not record the two change requests from the approver (fefb766, 72e4035): there are no issues for them, and `review.round` and `review.fix_rounds` are still 0. So none of the five signals sees them.

```json
{
  "status": "done",
  "stage": "retro",
  "summary": "Run 025 (cruise, full chain): no new candidates. 1 counted issue in implement and 1 in verify, so no halt-cluster. The only rejection, SPEC-1, is covered. No confirmed-blocking findings in rounds 1-3. Analyze CRITICAL/HIGH is 0. Reviewer in_est peaks are 2.35-2.39x the median 21587.5 but each reviewer has only 3 ledger entries. Not adopted. The approver's two change requests are not recorded as issues and review.round/fix_rounds stay 0, so no signal sees them.",
  "files": [],
  "questions": [],
  "retro": { "candidates": [] }
}
```
