# Brief: adopt a spec started outside factory

Factory today can only resume runs it created: discovery and `resume` look for `specs/*/factory/state.json` in a worktree or a pending file, so a plain SpecKit spec (spec.md / plan.md / tasks.md with no factory state) cannot be continued — `/factory resume <branch>` exits 1 with "no matching run", and `/factory <text naming the spec>` starts a fresh, duplicate run on a new branch. This feature adds an `adopt` command that inspects such a spec, runs a short confirmation grill, then creates the factory state (and worktree) the existing resume flow expects, so the run continues from the right stage through to an open PR. Resume itself stays unchanged.

## Decisions

- **Entry point (Q1):** explicit verb. `/factory adopt <branch|spec_dir>` routes to a new CLI writer `factory adopt`. When `resume` finds no matching run, its error message hints at `adopt`. `resume` never adopts implicitly.
- **Sequence (Q7):** `factory adopt <src> --dry-run` is read-only and reports the source shape, dirty paths, the inferred stage and any refusal. The orchestrator then runs a confirmation grill in pending state (same pending storage as a new run). Finally `factory adopt <src>` attaches or creates the worktree, writes `state.json` from the pending state, moves `brief.md` into `<spec_dir>/factory/`, and commits `factory: adopt <branch>`. A declined adoption leaves nothing in the repo.
- **Source shapes (Q2):**
  - Spec on its own feature branch (SpecKit default): attach a worktree to the existing branch (`git worktree add <path> <branch>`, no `-b`). If the branch is checked out in the main checkout (or another worktree), refuse with a hint to switch away.
  - Branch exists only on `origin`: create a local tracking branch.
  - Spec dir already on the default branch with no branch of its own: create a new branch named after the spec dir from `base`.
  - A spec dir whose name differs from its branch is recorded as-is in `spec_dir`.
  - Worktree path is the standard `<repo>/../<repo-name>-factory/<branch>`.
- **Refusals (Q3):** uncommitted changes in the spec files or on the source branch → exit 1 naming the dirty paths, nothing written; factory never commits work it did not author. A spec that already has `factory/state.json` → refuse and point to `resume`. A spec dir without `spec.md` → refuse.
- **Brief (Q4):** short confirmation grill seeded from `spec.md`: the orchestrator summarises the spec, asks only open gaps and the chain, then writes `brief.md`.
- **Entry stage (Q5):** inferred from artifacts — `spec.md` only → `plan`; `spec.md` + `plan.md` → `tasks`; `tasks.md` present → always `analyze` (even with checked boxes). Implement then resumes from the tasks.md checkboxes as today. The user confirms the inferred stage or overrides it.
- **Stage override (Q8):** `--stage` accepts only `specify`, `plan`, `tasks`, `analyze`; it can move the entry earlier or at most to analyze, never past analyze into `implement`.
- **Provenance (Q6):** add `adopted` to the closed history-event vocabulary, and an optional `adopted` block in state: source (branch and/or spec_dir and shape), inferred stage, chosen stage, and `base_commit` (HEAD of the adopted branch at adoption). Validation accepts an adopted run with no `complete` entries for stages before its entry stage. The approver screen and the retro show that the run was adopted.
- **Pre-adoption commits (Q9):** reviewers review the whole `base...HEAD` diff. ENG-2 (red step recorded in the task commit body) applies only to commits after `adopted.base_commit`; earlier commits are disclosed as pre-adoption and never blocking for ENG-2.
- **Touch points:** CLI writer + state validation/event vocabulary in `core/skills/factory/bin/factory_cli/`; `SKILL.md` route; `references/state.md`; `DESIGN.md`; `CONTEXT.md` (new term **Adopted run**); a new ADR; reviewer role files for the ENG-2 boundary; tests in `tools/tests/`; regenerate `dist/` via `tools/render.py`.
- **Chain:** lite, fast on (confirmed by the user); analyze CRITICAL/HIGH escalates to full.
