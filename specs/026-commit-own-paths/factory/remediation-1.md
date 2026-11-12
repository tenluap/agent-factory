# Remediation — pass 1

- U1: tasks.md T003 step 1 now names the injection point: the test wraps `adopt._record_worktree_run` (after `_add_worktree`, before `_commit_run`), which calls the original, commits `pnpm-lock.yaml` in the new worktree and stages its deletion. plan.md "Test seams" adopt line names the same point. Seam (`factory adopt (_commit_run)`) and failure path (`unrelated-staged-deletion`) unchanged, so the Q1 confirmation still matches.
- I1: spec.md FR-008 now references FR-005 and cites AC-4; plan.md "Change list" item 1 tag now reads (AC-1, AC-3, AC-4, AC-5).
- U2: plan.md "No declared paths" and research.md R2 now state that `profile-record` passes `loaded.get("spec_dir")` unchanged and that worktree-run state always carries `spec_dir`. No behaviour or task change.
