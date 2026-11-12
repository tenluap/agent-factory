# Specification Analysis Report — 026-commit-own-paths, pass 2

Artifacts: `spec.md` (1725 words), `plan.md` (1360), `tasks.md` (1663), `research.md`, `quickstart.md`, constitution 2.0.0. This is a loop pass after remediation 1. The brief's fixed AC-1..AC-5 set the scope. The brief's "Declined scope" items are not reported. The tests already failing on the base commit (`factory/verify-baseline.md`) are out of scope and are not findings.

## Remediation 1 check

- U1 (MEDIUM): fixed. T003 step 1 and the plan's adopt seam line name the injection point `adopt._record_worktree_run`. The code confirms the order: `_adopt_worktree` (`adopt.py:296-298`) calls `_add_worktree`, then `_record_worktree_run`, then `_commit_run`. The seam name and failure path are unchanged, so the Q1 confirmation still matches.
- I1 (LOW): fixed. FR-008 now cites AC-4 and references FR-005. Plan Change list item 1 is tagged (AC-1, AC-3, AC-4, AC-5).
- U2 (LOW): fixed. Plan "No declared paths" and research.md R2 now state that `profile-record` passes `loaded.get("spec_dir")` unchanged, and that worktree-run state always carries `spec_dir`.

Code re-checked: `commit_worktree` (`commands.py:790-799`) still calls `git commit` without a pathspec. That matches the plan's premise.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| I2 | Inconsistency | LOW | spec.md Assumptions; plan.md Change list "Not planned"; tasks.md header "Out of scope", T002 step 3, T007; `factory/verify-baseline.md` | The artifacts hard-code "the 7 tests already failing on base" (`test_render_models` x3, `test_skill_library` x4). `verify-baseline.md` records 8 local failures. The 7 CI failures are listed first. The eighth is `test_exceptions_are_still_needed (graphify)`, which fails only locally. Under "no failure beyond the 7 base failures", an implementer running the suite locally sees 8 failures. That implementer could treat the graphify failure as new, or could try to repair it. | Make the "Out of scope" and "no new failures" wording refer to the list in `factory/verify-baseline.md`, not to a hard-coded count of 7. If a count is kept, use "8 locally (7 on CI)". Do not change any task's scope. |

No other findings.

Scope check: every FR, SC, user story, plan change-list item, reason line and task cites an AC. No item adds work that AC-1..AC-5 do not need.

Test-scope check: T002–T006 each map to declared seams and failure paths. Each has ordered red, implementation and passing-check steps, a red proof and a done condition. The `Confirmed:` line (Q1, cruise override) matches the complete declared scope: 5 seams and 5 failure paths, unchanged by remediation 1. T001 is plan-exempt (`DESIGN.md`). T007 is verification only and changes no code.

ENG-10: the new file `tools/tests/test_commit_scope.py` has a stated reason. Abstractions and dependencies are stated as none.

Word budgets: all three artifacts are within budget (1725/3000, 1360/2000, 1663/2500).

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 | Yes | T002, T003 | |
| FR-002 | Yes | T002, T003 | |
| FR-003 | Yes | T002, T003 | Adopt injection point now named |
| FR-004 | Yes | T004 | |
| FR-005 | Yes | T005 | |
| FR-006 | Yes | T006 | |
| FR-007 | Yes | T004, T005, T006 | |
| FR-008 | Yes | T001 | |
| SC-001 | Yes | T002, T003 | |
| SC-002 | Yes | T002, T003 | |
| SC-003 | Yes | T004 | |
| SC-004 | Yes | T005, T006 | |
| SC-005 | Yes | T007 | See I2 |

**Constitution Alignment Issues:** none. I: T001 edits `DESIGN.md` first. II: the core edits name only git, never a harness tool. III: no edit to `dist/`. IV: the resume rule reads `tasks.md` from disk. V: one new file, with a stated reason.

**Unmapped Tasks:** none.

**Pre-adoption tasks:** not applicable (not an adopted run).

**Metrics:**

- Total Requirements: 8 FR + 5 SC = 13
- Total Tasks: 7
- Coverage: 100% (13/13)
- Ambiguity Count: 0
- Duplication Count: 0
- Critical Issues Count: 0
- Severity counts: CRITICAL 0, HIGH 0, MEDIUM 0, LOW 1

## Next Actions

No blocking findings. Remediation fixes I2 with in-place wording edits in `spec.md`, `plan.md` and `tasks.md`.
