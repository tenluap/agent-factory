# Feature Specification: Commit only what the run wrote

**Feature Branch**: `026-commit-own-paths`

**Created**: 2026-11-12

**Status**: Draft

**Input**: User description: "Story: As a factory user, I want every factory commit to contain only the files the run wrote, so that a run never commits, deletes or absorbs work that is not its own." (acceptance criteria AC-1..AC-5 and settled decisions Q1-Q8 in `factory/brief.md`)

## Acceptance Criteria (verbatim, fixed for this run)

- AC-1 (story 1). Every state CLI command that commits (checkpoint, resume, adopt and the other writer commands) stages its declared paths and commits with exactly that pathspec, as `drop` already does.
  - Note: "the other writer commands" are every state CLI command that commits through the shared commit helper: rebind, models-record, profile-record, analyze-record, ledger-add, issue-add, wait-open, wait-close, answer, set-status, decisions-add and verify (brief Q1). "Declared paths" are the run's spec folder plus any extra paths the command already declares today; this run adds no new declared path.
- AC-2 (story 2). Given an unrelated staged change, such as a deleted pnpm-lock.yaml, when checkpoint, resume or adopt commits, then that change is not in the commit and is still staged afterwards.
- AC-3 (story 3). code-build, design-to-code and fixer stage files by explicit path, never with `git add -A`, `git add .` or `git commit -a`.
- AC-4 (story 4). code-build treats an uncommitted change as its interrupted work only when the task it resumes names that path; it neither commits nor discards any other uncommitted change.
  - Note: "neither commits nor discards" also excludes staging and stashing that change (brief Q4). The rule applies to code-build only; design-to-code and fixer are declined scope.
- AC-5 (story 5). At the approver, every path `git status --porcelain` reports in the worktree is listed under "📂 Uncommitted local changes the run didn't make"; the run neither commits nor discards them.
  - Note: the section is shown only when `git status --porcelain` reports at least one path (brief Q5).

Out of scope: any other approver change.

## Clarifications

### Session 2026-11-12 (grill, settled under cruise; see `factory/brief.md`)

- Q1 (AC-1): The shared state-CLI commit helper and adopt's commit pass their declared paths as the commit pathspec, as `drop` does. No factory state-CLI commit runs without a pathspec. No new abstraction.
- Q2 (AC-2): Regression tests cover exactly checkpoint, resume and adopt, each starting from an unrelated staged deletion of `pnpm-lock.yaml`. The other writer commands are covered through the shared helper.
- Q3 (AC-3): One sentence at the commit step of each of the code-build, design-to-code and fixer role files. Not an engineering-reference rule.
- Q4 (AC-4): Only code-build's first work step is rewritten. No new envelope field.
- Q5 (AC-5): One item in the orchestrator's approver step. No new CLI command or field.
- Q6 (AC-3, AC-4, AC-5): The prose rules are verified by text-contract tests, as run 023 did. No live-harness run.
- Q7 (AC-1, AC-3, AC-5): Docs change only where the constitution requires: `DESIGN.md` where it describes writer commits, role staging and the approver screen, plus any core reference line that would otherwise contradict the change.
- Q8: The orchestrator's own `factory: start` commit is not a state CLI command and stays out of this run.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - State CLI commits contain only their declared paths (Priority: P1) (AC-1, AC-2)

A user has their own change staged in the run's worktree, for example a deleted `pnpm-lock.yaml`. The factory checkpoints a stage, resumes the run or adopts a branch. The resulting factory commit contains only the paths the command declared, and the user's staged change is left exactly as it was.

**Why this priority**: Factory commits run many times per run; one swept-in change silently commits or deletes the user's work.

**Independent Test**: In a scratch repository, stage an unrelated deletion, run checkpoint, resume and adopt, and inspect each commit and the index afterwards. (AC-2)

**Acceptance Scenarios**:

1. **Given** a run worktree with an unrelated staged deletion of `pnpm-lock.yaml`, **When** checkpoint commits, **Then** the commit does not contain the deletion and the deletion is still staged afterwards. (AC-2)
2. **Given** a run worktree with an unrelated staged deletion of `pnpm-lock.yaml`, **When** resume commits, **Then** the commit does not contain the deletion and the deletion is still staged afterwards. (AC-2)
3. **Given** a worktree with an unrelated staged deletion of `pnpm-lock.yaml`, **When** adopt commits, **Then** the commit does not contain the deletion and the deletion is still staged afterwards. (AC-2)
4. **Given** any state CLI writer command, **When** it commits, **Then** it stages its declared paths and commits with exactly that pathspec. (AC-1)

---

### User Story 2 - Code-writing roles stage by explicit path (Priority: P1) (AC-3)

When code-build, design-to-code or fixer commits its work, it stages each file it wrote by explicit path. It never stages everything in the worktree.

**Why this priority**: Role commits are the other route by which unrelated work enters a factory commit.

**Independent Test**: Text-contract test reads each of the three role files and checks the commit step requires explicit-path staging and forbids the three bulk forms. (AC-3)

**Acceptance Scenarios**:

1. **Given** the code-build, design-to-code and fixer role instructions, **When** a role reaches its commit step, **Then** the instructions tell it to stage by explicit path and never use `git add -A`, `git add .` or `git commit -a`. (AC-3)

---

### User Story 3 - code-build claims only its own interrupted work (Priority: P2) (AC-4)

A fresh code-build resumes a task and finds uncommitted changes in the worktree. It treats a change as its interrupted work only when the resumed task names that path. Every other uncommitted change is left untouched.

**Why this priority**: Resume is the moment a role is most likely to absorb or discard a user's in-progress work.

**Independent Test**: Text-contract test reads code-build's first work step and checks the path-match rule and the leave-untouched rule. (AC-4)

**Acceptance Scenarios**:

1. **Given** an uncommitted change to a path the resumed task names, **When** code-build starts, **Then** it treats that change as its interrupted work. (AC-4)
2. **Given** an uncommitted change to a path the resumed task does not name, **When** code-build starts and later commits, **Then** that change is neither committed nor discarded. (AC-4)

---

### User Story 4 - The approver lists uncommitted local changes (Priority: P2) (AC-5)

At the approver, the user sees every uncommitted path in the worktree under "📂 Uncommitted local changes the run didn't make", so nothing is pushed or lost without the user knowing.

**Why this priority**: The approver is the last point at which the user can act on stray local changes before the PR.

**Independent Test**: Text-contract test reads the orchestrator's approver step and checks for the `git status --porcelain` listing, the exact heading and the no-commit, no-discard rule. (AC-5)

**Acceptance Scenarios**:

1. **Given** a worktree where `git status --porcelain` reports paths, **When** the approver is shown, **Then** every reported path is listed under "📂 Uncommitted local changes the run didn't make". (AC-5)
2. **Given** those listed paths, **When** the run continues past the approver, **Then** the run neither commits nor discards them. (AC-5)

### Edge Cases

- The unrelated staged change is a deletion, not an edit: it stays staged after the factory commit (AC-2).
- The unrelated change sits inside a path a state CLI command declares: the command commits it, because it is within the declared pathspec (AC-1).
- `git status --porcelain` reports no paths: the approver shows no "📂" section (AC-5, note).
- An uncommitted change exists both in a path the resumed task names and in other paths: code-build claims only the named path (AC-4).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every state CLI command that commits, including checkpoint, resume, adopt and the writer commands named in AC-1's note, MUST stage its declared paths and commit with exactly that pathspec, as `drop` does. (AC-1)
- **FR-002**: A factory commit made by checkpoint, resume or adopt MUST NOT contain an unrelated staged change, and that change MUST still be staged after the commit. (AC-2)
- **FR-003**: Regression tests MUST cover checkpoint, resume and adopt, each with an unrelated staged deletion of `pnpm-lock.yaml`, checking that the deletion is absent from the commit and still staged afterwards. (AC-2)
- **FR-004**: The code-build, design-to-code and fixer role instructions MUST tell the role to stage files by explicit path and never to use `git add -A`, `git add .` or `git commit -a`. (AC-3)
- **FR-005**: code-build's instructions MUST treat an uncommitted change as interrupted work only when the resumed task names its path, and MUST leave every other uncommitted change uncommitted and undiscarded. (AC-4)
- **FR-006**: The orchestrator's approver step MUST list every path `git status --porcelain` reports in the worktree under "📂 Uncommitted local changes the run didn't make", and the run MUST neither commit nor discard those paths. (AC-5)
- **FR-007**: Text-contract tests MUST verify FR-004, FR-005 and FR-006 in the instruction files. (AC-3, AC-4, AC-5)
- **FR-008**: `DESIGN.md`, and any core reference line that would otherwise contradict FR-001, FR-004, FR-005 or FR-006, MUST describe the changed behaviour (constitution principle I). (AC-1, AC-3, AC-4, AC-5)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the regression tests, 0 of 3 commits (checkpoint, resume, adopt) contain the unrelated staged deletion, and in 3 of 3 the deletion is still staged afterwards. (AC-2)
- **SC-002**: 100% of state CLI commits are made with an explicit pathspec of their declared paths. (AC-1)
- **SC-003**: 3 of 3 code-writing role files require explicit-path staging and forbid the three bulk forms. (AC-3)
- **SC-004**: code-build's resume rule and the approver's uncommitted-paths listing each pass their text-contract test. (AC-4, AC-5)
- **SC-005**: The test suite reports no failures beyond those already failing on the base commit. (AC-1..AC-5)

## Assumptions

- The writer commands' existing declared paths are correct; this run changes only how they commit, not what they declare. (AC-1)
- The 7 tests already failing on base commit 0c3bf71 (`test_render_models`, `test_skill_library`) are out of scope and are neither repaired nor edited.
- Declined scope (follow-ups, not specified here): extending the AC-4 rule to design-to-code and fixer; a CLI command or `show` field for the uncommitted-path list; a pathspec on the orchestrator's `factory: start` commit; a staging rule in `engineering.md`; an ADR, CONTEXT.md terms or README changes; repairing the base-commit test failures.
