```json
{
  "status": "done",
  "stage": "retro",
  "summary": "3 candidates: verify overrun cluster (3 tool-slow overruns, suite 315-589s vs 300s budget) and 2 reviewer in_est outliers (~2.5x median). Analyze clean, all review rounds pass with no blocking or rejections, no adoption.",
  "files": [],
  "questions": [],
  "analyze": null,
  "error": null,
  "retro": {
    "candidates": [
      {"signal_key": "halt-cluster:verify", "rank": 1, "evidence": "3 overrun issues in stage verify (orchestrator, cause tool-slow): build+full suite 315s, 589s, 585s vs 300s orchestrator budget (commits a726c52, 2a489fc, 80be123a)", "suggested_feature": "Size the orchestrator verify budget from observed build and full-suite duration so verify stops overrunning its 300s budget"},
      {"signal_key": "in-est-outlier:spec-conformance", "rank": 2, "evidence": "spec-conformance max in_est 35569 = 2.53x run-wide median 14033 across 25 ledger entries (review round 1)", "suggested_feature": "Trim spec-conformance reviewer input by passing only the spec sections and diff hunks relevant to the change"},
      {"signal_key": "in-est-outlier:code-standards", "rank": 3, "evidence": "code-standards max in_est 34929 = 2.49x run-wide median 14033 across 25 ledger entries (review round 1)", "suggested_feature": "Trim code-standards reviewer input by passing only the instruction files that apply to the changed paths"}
    ]
  }
}
```
