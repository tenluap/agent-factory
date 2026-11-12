# Specification Analysis Report — 026-commit-own-paths, pass 1

Artifacts: `spec.md` (1723 words), `plan.md` (1336), `tasks.md` (1633), `research.md`, `quickstart.md`, constitution 2.0.0. The brief's fixed AC-1..AC-5 set the scope. The brief's "Declined scope" items are not reported. The 8 base failures in `factory/verify-baseline.md` are out of scope.

Code checked against plan claims: `commit_worktree` (`core/skills/factory/bin/factory_cli/commands.py:790`) calls `git commit` without a pathspec. `_commit_run` (`adopt.py:387`) does the same. `cmd_drop` (`commands.py:706`) already uses `-- *paths`. These are the only `git commit` calls in `factory_cli`. All 14 writer call sites go through `commit_worktree`. So T002 and T003 cover every state CLI commit (AC-1). `DESIGN.md:272` ("Declared-file checkpoints") and `DESIGN.md:226` ("Approver") exist. `references/state.md` lines 203 and 210 do not contradict the change.

## Findings

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| U1 | Underspecification | MEDIUM | tasks.md T003; plan.md "Test seams" (`factory adopt`) | The adopt write path always creates a fresh worktree (`_add_worktree`, `adopt.py:322`). It refuses any dirty checkout of the branch (`_dirty`, `adopt.py:132`, refusal "uncommitted changes"). So a staged `pnpm-lock.yaml` deletion cannot exist before `adopt` runs. It can only be injected between worktree creation and `_commit_run`. T003 says "staged in the adopted worktree before the commit step" but names no injection point. An implementer can stage it in the main checkout instead, and adopt then refuses or never sees it. | In T003 step 1 (and the plan's adopt seam line), name the injection point. For example, wrap `adopt._record_worktree_run` (or `_add_worktree`) in the test so that it commits `pnpm-lock.yaml` and stages its deletion in the new worktree before `_commit_run`. Keep the seam name and failure path unchanged. |
| I1 | Inconsistency | LOW | spec.md FR-008; plan.md "Change list" item 1; tasks.md T001 | T001 and plan item 1 also put code-build's resume path-match rule (AC-4) into `DESIGN.md`. Principle I requires this. But FR-008 cites only AC-1, AC-3 and AC-5, and plan item 1's tag omits AC-4. | Add AC-4 to FR-008 (and its FR-005 reference) and to plan Change list item 1's AC tag. |
| U2 | Underspecification | LOW | plan.md "Quality constraints" ("No declared paths"); research.md R2 | The plan says "every caller passes `spec_dir`". `cmd_profile_record` (`commands.py:515-525`) writes `profile.md` under the `spec_dir` argument when one is given. But it commits with `loaded.get("spec_dir")`. With the new early return, a worktree run whose state lacks `spec_dir` would skip the commit silently instead of failing. The claim holds only while worktree state always carries `spec_dir`. | Qualify the claim in the plan: "worktree-run state always carries `spec_dir`". No task change is needed. Alternatively, note that `profile-record` keeps committing `loaded.get("spec_dir")` unchanged. |

No other findings. Scope check: every FR, SC, user story, plan change-list item, reason line and task cites an AC. No item adds work that AC-1..AC-5 do not need. The `no-declared-paths` guard is required by AC-1, because `git commit -- ` with an empty path list would commit the whole index. Test-scope check: T002–T006 each map to declared seams and failure paths. Each has ordered red, implementation and passing-check steps. The `Confirmed:` line (Q1, cruise override) matches the complete declared scope. T001 is plan-exempt (`DESIGN.md`). T007 is verification only and has no implementation. ENG-10: the new file `tools/tests/test_commit_scope.py` has a reason; abstractions and dependencies are stated as none. All word budgets are within limits.

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 | Yes | T002, T003 | Every writer goes through `commit_worktree`; adopt goes through `_commit_run` |
| FR-002 | Yes | T002, T003 | |
| FR-003 | Yes | T002, T003 | See U1 for adopt |
| FR-004 | Yes | T004 | |
| FR-005 | Yes | T005 | |
| FR-006 | Yes | T006 | |
| FR-007 | Yes | T004, T005, T006 | |
| FR-008 | Yes | T001 | See I1 |
| SC-001 | Yes | T002, T003 | |
| SC-002 | Yes | T002, T003 | |
| SC-003 | Yes | T004 | |
| SC-004 | Yes | T005, T006 | |
| SC-005 | Yes | T007 | Baseline failures excluded |

**Constitution Alignment Issues:** none. I: `DESIGN.md` comes first (T001). II: core edits name only git, no harness tool. III: no `dist/` edit, and build checks that `dist/` is untracked. IV: the resume rule reads `tasks.md` from disk. V: one new file with a stated reason.

**Unmapped Tasks:** none.

**Pre-adoption tasks:** not applicable (not an adopted run).

**Metrics:**

- Total Requirements: 8 FR + 5 SC = 13
- Total Tasks: 7
- Coverage: 100% (13/13)
- Ambiguity Count: 0
- Duplication Count: 0
- Critical Issues Count: 0
- Severity counts: CRITICAL 0, HIGH 0, MEDIUM 1, LOW 2

## Next Actions

No blocking findings. Remediation fixes U1, I1 and U2 in place in `tasks.md`, `plan.md` and `spec.md`.
