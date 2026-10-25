# Manual agent-driven checks (quickstart.md, "Manual checks")

Per `DESIGN.md`'s validation plan and `quickstart.md`: checks 1-6 need a real, live `/factory` run against an
external repository and a real user answering relay questions (DESIGN.md recommends WayUnoMcpTool). This
implementation task (`code-build`, running inside this feature's own worktree, with no second harness
session to spawn a nested `/factory` run) built and verified the routing instructions and the three
machine-checkable seams (T021), but cannot itself carry out a live multi-turn dialog. Check 7 (single-source
document agreement) needs no live run and was completed in T021.

| # | Check | Status |
|---|---|---|
| 1 | Three intake trials (explicit exploration, explicit delivery, ambiguous) route correctly with exactly one question on the ambiguous case (SC-001) | Deferred — needs a live `/factory` run with a real user |
| 2 | Stop after exploration, then resume: confirmed direction in the pending brief, zero changed files in the invoking checkout, no repeated questions at feature settlement (SC-002, SC-003) | Deferred — needs a live run with a pause/resume cycle |
| 3 | Fast-mode run: the seam confirmation is shown and waited on; resume with unchanged seams does not re-ask it, a changed seam list does (SC-005) | Deferred — needs a live run reaching the `plan` stage |
| 4 | Remove `ponytail` (or `tdd`): the affected work stops with setup guidance naming the skill, no completed work reported (SC-004) | Deferred — needs a live run with a skill directory to edit |
| 5 | Four diffs (design tokens, locale string, user-visible copy in UI code, backend only): classification correct in all four, zero UI-reviewer edits, evidence disclosed as rendered or static (SC-006, SC-007) | Deferred — needs a live run reaching `review` with a UI-touching diff |
| 6 | Resume a run saved before this change: restarts at its recorded stage with answers intact (SC-008) | Deferred — needs a pre-existing saved run from before this change |
| 7 | Single-source agreement: `DESIGN.md` and `references/skills.md` against `SKILL.md`, `code-build.md`, `fixer.md`, `ui-reviewer.md` — no restated or conflicting precedence rule (SC-010) | **Done** in T021: found and fixed a restatement (code-build.md/fixer.md previously duplicated skills.md's precedence sentences); trimmed to a link. Re-checked clean. |

Checks 1-6 are the next step before this feature is considered fully validated: run `/factory` end-to-end on
a small real feature per `DESIGN.md`'s "Validation plan", exercising each row above.
