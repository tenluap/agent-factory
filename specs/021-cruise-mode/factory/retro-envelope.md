Retro for 021-cruise-mode: one candidate qualified (analyze-escalation:analyze); fixer-recurring, judge-rejection and in-est-outlier did not meet thresholds; halt-cluster:review already covered. Observation: state.analyze.remediations is [] though remediation-2.md exists (no writer for it).

```json
{
  "status": "done",
  "stage": "retro",
  "summary": "One candidate: analyze pass 1 raised two HIGH test-scope drifts that recurred as undeclared test seams in implement review. Judge-rejection, fixer-recurring and in-est-outlier signals did not meet thresholds; halt-cluster:review was already covered.",
  "files": [],
  "questions": [],
  "analyze": null,
  "error": null,
  "retro": {
    "candidates": [
      {
        "signal_key": "analyze-escalation:analyze",
        "rank": 1,
        "evidence": "analyze-1.md reports HIGH 2: T1 (tasks.md T002, validate_state paths beyond the confirmed scope) and T2 (tasks.md T007, permitting_decision and implement-gate seams beyond the confirmed scope), both tagged ENG-4. analyze-2.md resolved both via clarify Q1 and remediation-2.md. The same drift recurred in implement: round-1 STD-2 and SPEC-10 (advisory) flagged undeclared settled_answers and permitting_decision seams, and round-2 blocking STD-1, SPEC-13 and SPEC-14 flagged an undeclared set-status pr-open seam with edited existing tests.",
        "suggested_feature": "Make the tasks stage check every Red-step seam and failure path against the plan's confirmed test scope before analyze runs"
      }
    ]
  }
}
```
