# Retro envelope — run 017-per-project-models

Retro completed 2026-11-02. Sources: state.json (33 ledger entries, 7 issues), analyze-1/2/3, round-1 + round-2 verdicts. Round-3 verdict.json absent on disk and in git history — source skipped, not invented.

## Signals mined

- **halt-cluster:fix** — 2 issues in fix stage: fixer retry (ENG-4 scope handoff, refused unstated seam scope) + overrun (test-loop, full suite 244s, boundary check ~1s past 300s budget).
- **halt-cluster:review** — 2 issues in review stage: security-reviewer retry (findings in envelope, no report file) + review-judge retry (recorded deep model unspawnable, substituted glm-5.3).
- **fixer-recurring:eng-15** — ENG-15 first-cited in evidence of 2 round-1 confirmed blocking findings (no CLI writer for models block; no role-to-tier mapping shipped).
- analyze-escalation:analyze qualifies (analyze-2 HIGH 1: stale Confirmed test-scope line post-Q13) but ranks below the three above; dropped at the 3-candidate cap.
- judge-rejection: none (both verdicts `rejected: []`). in-est-outlier: none (run-wide median in_est 17000; role maxima 30000/26000/24000/24000, none ≥ 34000).

## Candidates

```json
{
  "status": "done",
  "stage": "retro",
  "summary": "Retro for 017-per-project-models: two halt-clusters (fix-stage retry+overrun, review-stage no-report+model-substitution retries) and recurring ENG-15 installed-guidance-without-operation class; round-3 verdict.json missing on disk and in git, so that source was skipped.",
  "files": [],
  "questions": [],
  "retro": {
    "candidates": [
      {
        "signal_key": "halt-cluster:fix",
        "rank": 1,
        "evidence": "state.issues: fix-stage retry 12:27:16Z (fixer refused fix round 1 — ENG-4 scope handoff, declared seam scope for 8 findings not supplied) and fix-stage overrun 12:37:26Z (cause test-loop, full suite 244s, final boundary check ~1s past the 300s budget, partial_return true, commit 1b3a97d).",
        "suggested_feature": "Orchestrator assembles each fix round's declared seam scope from the verdict's confirmed blocking fixes plus the plan's Confirmed line before spawning the fixer, and runs the final full-suite boundary check only when it fits the remaining time budget"
      },
      {
        "signal_key": "halt-cluster:review",
        "rank": 2,
        "evidence": "state.issues: review-stage retry 12:19:42Z (security-reviewer returned findings in envelope but wrote no report file; retry wrote cf49276) and review-stage retry 12:26:21Z (review-judge spawn: recorded deep model claude-code/claude-opus-5-5[1m] unavailable, substituted zai-coding-plan/glm-5.3 under bounded failure policy).",
        "suggested_feature": "Make the orchestrator persist every reviewer report to factory/reviews/<round>/ before the judge spawns and preflight-check that resolved model IDs are spawnable with pre-authorized substitution, removing mid-round review retries"
      },
      {
        "signal_key": "fixer-recurring:eng-15",
        "rank": 3,
        "evidence": "round-1 verdict confirmed_blocking: STD-1/SPEC-1 (SKILL.md:47 tells preflight to record models block but no CLI writer exists — evidence cites ENG-15, ENG-26) and STD-2/SPEC-2 (SKILL.md:24 spawn-by-tier guidance but render.py strips tier frontmatter and ships no role-to-tier map — evidence cites ENG-15): installed guidance referenced operations the shipped interface lacks, twice in one round.",
        "suggested_feature": "Add an install-time contract check that every SKILL.md preflight/spawn instruction has a matching shipped CLI operation and artifact (state writer, role-to-tier map) so installed guidance never references a non-existent interface"
      }
    ]
  }
}
```
