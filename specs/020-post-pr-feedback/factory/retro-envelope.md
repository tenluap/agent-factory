Retro over 3 verdicts, 3 analyze reports, 31 ledger entries and 3 issues. Two new candidates (fixer-recurring eng-17, eng-1). Covered keys skipped (fixer-recurring:eng-15, halt-cluster:fix, halt-cluster:review, analyze-escalation:analyze). judge-rejection and in-est-outlier did not qualify. state.json review/mode counters are stale (no CLI writer); verdict files show fix, fix, pass.

```json
{
  "status": "done",
  "stage": "retro",
  "summary": "Retro over 3 verdicts, 3 analyze reports, 31 ledger entries and 3 issues. Two new candidates (fixer-recurring eng-17, eng-1). Covered keys skipped. judge-rejection and in-est-outlier did not qualify.",
  "files": [],
  "questions": [],
  "analyze": null,
  "error": null,
  "retro": {
    "candidates": [
      {
        "signal_key": "fixer-recurring:eng-17",
        "rank": 1,
        "evidence": "Confirmed blocking in round 1 (feedback.py:241): a valid-JSON outcome file of the wrong shape (a top-level list, outcomes null, outcomes containing a non-object) raises AttributeError or TypeError in _is_terminal outside the Gap handler, aborting the whole refresh. Round 2 (feedback.py:235): an outcome id that is a list or object passes the shape check and raises TypeError in _store; a null id is silently accepted. Both findings cite ENG-17 first. The round-1 fix did not remove the class. Count 2 across 2 rounds, tied with eng-1 and ranked first for recurrence across a fix round.",
        "suggested_feature": "Make factory feedback refresh classify every malformed stored outcome file shape as an inaccessible gap (non-object body, non-list outcomes, non-object entry, non-string id) with per-shape tests and proof that other runs still refresh"
      },
      {
        "signal_key": "fixer-recurring:eng-1",
        "rank": 2,
        "evidence": "Confirmed blocking twice in round 1, both citing ENG-1 first: feedback.py:23 (TIMED_OUT and STARTUP_FAILURE check conclusions have no asserting test; a judge mutant reducing CHECK_FAILURES to FAILURE only left all 43 feedback tests green) and feedback.py:225 (the CLOSED terminal skip has no test; a mutant dropping state:closed from TERMINAL_IDS left the suite green). Not repeated in rounds 2 or 3. Count 2 in one round.",
        "suggested_feature": "Add asserting tests for each declared factory feedback capture and terminal-skip rule: TIMED_OUT and STARTUP_FAILURE check conclusions, the CLOSED terminal skip, and malformed JSON from the review read"
      }
    ]
  }
}
```
