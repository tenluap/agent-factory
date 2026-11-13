Retro for 024-orchestrator-gaps.

```json
{
  "status": "done",
  "stage": "retro",
  "summary": "Retro for 024-orchestrator-gaps: 2 uncovered candidates, both in-est-outlier (security-reviewer, review-judge). Analyze escalation and halt-cluster review/implement are already covered keys. No confirmed blocking finding cites ENG-n in `evidence`, so no fixer-recurring signal. Only spec-conformance had rejections, and that key is covered. No adopted block.",
  "files": [],
  "questions": [],
  "analyze": null,
  "retro": {
    "candidates": [
      {
        "signal_key": "in-est-outlier:security-reviewer",
        "rank": 1,
        "evidence": "Ledger: 43 entries, run-wide in_est median 11200. security-reviewer had 7 entries with a max in_est of 60000 (5.4x the median). Rounds 1-3 on 2026-11-04/05 were 3400-3600; rounds 4-6 on 2026-11-13 were 60000, 25000 and 60000. The 2026-11-13T10:59 overrun shows security-reviewer 908s past its 300s budget.",
        "suggested_feature": "Bound security-reviewer input on re-review rounds to the fix delta so in_est stays near earlier rounds"
      },
      {
        "signal_key": "in-est-outlier:review-judge",
        "rank": 2,
        "evidence": "review-judge had 7 entries with a max in_est of 30000 (2.7x the run median of 11200). Rounds 1-3 were 5200-6000; rounds 4-6 were 30000, 20000 and 30000. Overruns of 410s and 415s total ran past the 300s budget without a self-report (2026-11-04T23:24, 2026-11-05T00:01).",
        "suggested_feature": "Feed review-judge only reviewer findings and cited diff hunks to cap its input estimate on later review rounds"
      }
    ]
  },
  "error": null
}
```
