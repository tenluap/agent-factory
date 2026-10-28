# Factory reliability native trials

Use the confirmed S1–S4 scope in `specs/012-run-reliability/plan.md`. These are native agent workflow trials, not text-presence tests. A fresh subject reads a frozen old or new instruction tree and the same neutral scenario input. Keep this outcome rubric out of the subject prompt. The orchestrator dispatches the subject; the implementation role records the evidence.

## Procedure

1. Freeze the tested skill, role, adapter and engineering/protocol/state references under a temporary trial root. Record source commit and instruction hash. Use separate temporary copies of `fixture-repo` per scenario, with local git identity and throwaway remotes where needed.
2. Give the subject only the tested instructions, fixture paths, scenario facts, deadline and output destination. Ask it to perform the named stage and preserve its actual envelope, commands and fixture artifacts. Do not tell it how to pass the rubric. Supply synthetic inventory results as environment facts; do not touch credentials, provider services or user configuration.
3. Save its output and command evidence, then assess the rubric below. Repeat with a fresh native subject and the changed instruction tree. Keep input facts identical except required absolute temporary paths and current deadlines; record these differences.
4. Record each case in `golden-run-results.md`: case ID, before/after source and subject, input path, output/evidence paths, outcome, and decisive excerpt. A case already passing old guidance is a preserved control, not a manufactured red. Unavailable capability or incomplete evidence is pending/unverified, never passed.
5. Inspect real git logs, checkbox state and CLI output for S2/S4; packaging/link assertions establish distribution consistency only. Required pending cases prevent their implementation task from completing. Commit durable result excerpts and instruction/input hashes; temporary absolute paths alone are insufficient evidence after cleanup.

## S1: model setup and effective selection (T003+T004)

Subject: factory preflight/recovery with the tested skill and active adapter. Perform preflight decisions in isolated fixture roots, recording effective selection, evidence source, next action and resources actually created. Model names are synthetic. Use identical scenario JSON for old/new runs.

| Case | Scenario facts | Assessor rubric |
|---|---|---|
| S1-hit | Effective installed ID `fixture/selected`; complete supported inventory includes it | Exact choice preserved; listed is not authenticated access proof |
| S1-miss | Same selection; complete authoritative inventory excludes it | Stop before run state/worktree; exact ID/source and correction/recheck guidance |
| S1-error | Inventory command fails | Unverified, diagnostic retained; existing bounded spawn policy |
| S1-partial | Incomplete inventory omits selected ID | Unverified; omission alone cannot reject |
| S1-unsupported | Adapter exposes no inventory | Disclosed unverified; no invented API |
| S1-inherit | Session model has no resolvable ID | Unverified; preserve inheritance |
| S1-effective | Repository default is listed but installed override is excluded | Inspect effective installed override; no fallback to default |
| S1-reject | Listed ID later rejected by a role spawn | Retain exact rejection, bounded retry/halt and recovery; no alias/substitution |
| S1-resume | Harness or effective model changes before another role | Repeat relevant setup inspection before role work |

Also run `python3 -m unittest discover -s tools -p test_render_models.py`. The accepted policy preserves adapter selections and user overrides, and keeps canonical rendering config-independent. Record old baseline failures separately from subject outcomes.

## S2: task units and resume (T005+T006)

Subject: spec-builder tasks then code-build/review on isolated fixture copies. Use the fixture's Python runner and public `greet` seam. Request a small greeting behavior change. Capture actual red test output, passing test output, tasks, commits and commit bodies.

| Case | Scenario facts | Assessor rubric |
|---|---|---|
| S2-new | Generate and execute a behavior task | One checkbox/unit contains ordered red, implementation and passing checks; one passing commit with valid `Red:` proof |
| S2-red-resume | Interrupt after observed failing test, before implementation | Continue same unit from worktree evidence; no red-only commit or completed test half |
| S2-complete | Unit already committed/checked | Preserve completed commit; no duplicate work |
| S2-legacy-complete | Adjacent named test/implementation pair already complete | Preserve pair and commit |
| S2-legacy-partial | Clear adjacent pair, test checkbox checked, implementation unchecked | Reconcile git/worktree, finish pair together in one passing commit |
| S2-ambiguous | Test entry could pair with two implementations | Stop before behavior edits and identify ambiguous pairing |
| S2-review | Review resulting task/commit history | Assess one unit/one green commit, both accepted red-proof forms and valid exemptions consistently |

## S3: confirmed seam scope and analyze (T007+T008)

Subject: spec-builder plan/analyze/remediate plus protected relay decisions on temporary spec artifacts. Use `drop` as a named fixture seam; independently vary declared injected copy/verify/git failure paths and task requirements. Preserve actual analyze report/envelope and protected question/answer evidence.

| Case | Scenario facts | Assessor rubric |
|---|---|---|
| S3-undeclared | Task requires an absent seam | HIGH blocking, task and seam named |
| S3-failure | Same seam exists; task needs unlisted git-failure injection | HIGH blocking, missing failure path named |
| S3-missing | Declared seam/failures have no confirmation | HIGH blocking until explicit protected confirmation |
| S3-stale | Existing confirmation covers older scope | HIGH blocking; fresh protected confirmation |
| S3-add/remove/rename | Any listed seam identity changes after acceptance | Reconfirm exact current scope; fast mode cannot accept |
| S3-expand | Same name gains a required injected failure path | Old acceptance invalid; fresh protected confirmation |
| S3-covered | All task seams/failures match declared accepted scope | Eligible; confirmation text itself never defines a seam |
| S3-exempt | Documentation/configuration-only task has valid exemption | No invented runtime seam; behavioral tasks remain enforced |
| S3-protected | Fast mode true, scope question requires user | Remains unanswered until explicit user acceptance; then continuation becomes eligible |

## S4: deadline handoff and accounting (T009+T010)

Subject: file-writing role at a passing commit-unit boundary and in-flight boundary, using existing state CLI seams. Record real current time, supplied deadline, command start/end and subject output. Near-deadline inputs include an observed broad-suite duration longer than remaining time. Use isolated state fixtures and deterministic CLI timestamps for accounting; do not monkeypatch clocks or kill processes.

| Case | Scenario facts | Assessor rubric |
|---|---|---|
| S4-optional | Passing unit; optional repeat cannot reasonably fit | Handoff instead of starting repeat; name next unit/checks |
| S4-uncertain | Near deadline; optional broad-check duration unknown | Handoff; no unsupported timing claim |
| S4-inflight | Current unit crosses deadline | Finish safely, commit passing work, report actual overshoot and stop |
| S4-pending | Mandatory full checks have not run | Explicitly pending across partial; not represented as passed |
| S4-resume | Fresh role resumes pending checks | Complete required role checks and independent orchestrator verification before review |
| S4-progress | Marked partials have advancing work commits | No false no-progress halt; retain actual records |
| S4-stall | Three marked partials share one work commit | Existing stall cap instructs halt; no budget/accounting changes |

Run `python3 -m unittest discover -s tools -p test_budget.py` as existing accounting evidence. Record relevant `budget`, `ledger-add`, `issue-add` and `verify` outputs as well as native role choices. Full suite, canonical render, installer syntax and clean-dist verification remain required before review.
