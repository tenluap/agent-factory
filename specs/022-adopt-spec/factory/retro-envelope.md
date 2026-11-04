Retro complete. Three candidates qualify (halt-cluster:review, fixer-recurring:eng-1, fixer-recurring:eng-4); analyze-escalation:analyze and in-est outliers qualify but rank below the cap; judge-rejection not triggered.

Orchestrator-observed, verified: review.round and review.fix_rounds stay 0 in state despite three verdict rounds (no writer); the round-3 escalate came from orchestrator-directed doc edits missing from Adjacent: lines; tests passing first run lacked a valid red record (mutation evidence belongs in the retro); missing New: lines in 9508de4; early T013 tick (fb2d038); T014/T015 mislabelled Exempt. Not verifiable from inputs: code-build partial stops, stale installed skill, --files CLI shape, fixer commit rule.

```json
{
  "status": "done",
  "stage": "retro",
  "summary": "Three candidates from halt-cluster and fixer-recurring signals. Analyze escalation and in-est outliers qualify but rank below the cap. Judge rejection not triggered.",
  "files": [],
  "questions": [],
  "analyze": null,
  "error": null,
  "retro": {
    "candidates": [
      {
        "signal_key": "halt-cluster:review",
        "rank": 1,
        "evidence": "state.json issues: 4 overrun entries, all stage review, role reviewers, cause unreported, partial_return false; reviewer durations 998s, 395s, 530s, 360s against a 300s budget (commits 736b480, 6e8d1ac, 9508de4 twice). Reviewers in_est 494447 is the largest in the run.",
        "suggested_feature": "Make reviewer subagents self-report elapsed time and stop at the 300s review budget, returning a partial report with an overrun cause instead of running unreported past it"
      },
      {
        "signal_key": "fixer-recurring:eng-1",
        "rank": 2,
        "evidence": "ENG-1 is the first ENG-n in 6 confirmed-blocking entries across 3 rounds: round 1 three (default_base; untested declared dry-run failure path; judge pre-adoption rule), round 2 one (two added fix failure branches untested, 66 tests still pass with them mutated), round 3 delta and full one each (four plan-Q3 failure paths untested). Round-3 full still blocks on it.",
        "suggested_feature": "Require the fixer to add an asserting test with mutation proof for every declared failure path its fix touches, and to check the full Test seams list before returning, so ENG-1 coverage gaps stop recurring across review rounds"
      },
      {
        "signal_key": "fixer-recurring:eng-4",
        "rank": 3,
        "evidence": "ENG-4 is the first ENG-n in 2 round-2 confirmed-blocking entries: STD-3/SPEC-11 (plan.md test scope changed without fresh confirmation, which the fixer cannot clear with code) and STD-2 (test patches private _clear_pending, a seam not in the plan). Round-3 entries cite ENG-4 only as second.",
        "suggested_feature": "Route any test or failure path that review adds beyond the confirmed test scope to a fresh protected scope confirmation before the fixer edits code, so ENG-4 scope findings stop recurring"
      }
    ]
  }
}
```
