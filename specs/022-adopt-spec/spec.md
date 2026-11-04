# Feature Specification: Adopt a spec started outside factory

**Feature Branch**: `022-adopt-spec`

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Add an adopt command so factory can take over a spec started outside it (plain SpecKit spec with no factory state) and continue the flow to PR." (settled decisions Q1-Q9 in `factory/brief.md`)

## Clarifications

### Session 2026-11-04 (grill)

- Q1: Entry point? → A: Explicit verb `/factory adopt <branch|spec_dir>`; `resume` never adopts, its "no matching run" error hints at `adopt`.
- Q2: Source shapes? → A: Own feature branch (attach worktree, no new branch), remote-only branch (local tracking branch), spec dir on the default branch (new branch named after the spec dir from `base`); a spec dir name differing from its branch is kept as-is.
- Q3: Refusals? → A: Dirty spec files or source branch, existing `factory/state.json`, or missing `spec.md` refuse with exit 1 and write nothing.
- Q4: Brief? → A: Short confirmation grill seeded from `spec.md`, asking only open gaps and the chain.
- Q5: Entry stage? → A: Inferred from artifacts; the user confirms or overrides.
- Q6: Provenance? → A: New `adopted` history event and optional `adopted` state block; approver screen and retro disclose adoption.
- Q7: Sequence? → A: Read-only `--dry-run`, confirmation grill in pending state, then the write that creates the run and commits `factory: adopt <branch>`.
- Q8: Stage override? → A: `--stage` accepts only `specify`, `plan`, `tasks`, `analyze`.
- Q9: Pre-adoption commits? → A: Reviewed as part of the whole diff; ENG-2 applies only after `adopted.base_commit`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Continue a SpecKit spec on its own branch (Priority: P1)

A user wrote a spec with plain SpecKit on its feature branch (the SpecKit default) and now wants factory to finish it. They run `/factory adopt <branch>`. Factory reports what it found and the stage it would start at, asks a short confirmation grill, then attaches a worktree to the existing branch, creates the run, and continues from the inferred stage through review and the approver gate to an open PR.

**Why this priority**: The most common shape and the core value: no duplicate branch, no lost work, no manual state editing.

**Independent Test**: In a fixture repository, create a feature branch holding `spec.md` and `plan.md` with no factory state, switch the main checkout to the default branch, run adopt, and confirm a worktree on that same branch, a valid run state whose stage is `tasks`, an `adopted` history entry and one commit `factory: adopt <branch>`.

**Acceptance Scenarios**:

1. **Given** a feature branch with a spec dir holding only `spec.md`, **When** the user runs adopt and confirms, **Then** the run's entry stage is `plan`.
2. **Given** a spec dir holding `spec.md` and `plan.md`, **When** adopted, **Then** the entry stage is `tasks`.
3. **Given** a spec dir holding `tasks.md` (with or without checked boxes), **When** adopted, **Then** the entry stage is `analyze`, and implement later resumes from the `tasks.md` checkboxes as it does today.
4. **Given** a confirmed adoption, **When** the write completes, **Then** a worktree exists at `<repo>/../<repo-name>-factory/<branch>` on the existing branch (no new branch created), `state.json` and `brief.md` sit in `<spec_dir>/factory/`, and the branch has exactly one new commit, `factory: adopt <branch>`.
5. **Given** an adopted run, **When** the orchestrator continues, **Then** it runs the entry stage and every later stage exactly as for a run factory created, ending at an open PR after the user's Approve.

---

### User Story 2 - Safe preview and refusals (Priority: P1)

Before anything is written, the user sees the source shape, any dirty paths, the inferred stage and any refusal. Adoption never commits work factory did not author and never touches a run that already exists.

**Why this priority**: The safety boundary that makes adoption acceptable: a wrong adoption must cost nothing.

**Independent Test**: Run `factory adopt <src> --dry-run` against each refusal fixture and against a valid source; confirm the repository's status, refs, worktree list and files are byte-identical before and after, and that each refusal exits 1 with its reason.

**Acceptance Scenarios**:

1. **Given** any source, **When** the user runs `factory adopt <src> --dry-run`, **Then** it prints a report with the source shape, dirty paths, inferred stage and refusal (if any), and changes nothing in the repository or outside it.
2. **Given** uncommitted changes in the spec files or on the source branch, **When** adopt runs (dry-run or write), **Then** it exits 1 naming every dirty path and writes nothing.
3. **Given** a spec dir that already has `factory/state.json`, **When** adopt runs, **Then** it exits 1 and points the user to `/factory resume <branch>`.
4. **Given** a spec dir without `spec.md`, **When** adopt runs, **Then** it exits 1 saying `spec.md` is required.
5. **Given** the source branch is checked out in the main checkout or another worktree, **When** adopt runs, **Then** it exits 1 with a hint to switch that checkout away from the branch.
6. **Given** the user declines during the confirmation grill, **When** the grill ends, **Then** nothing exists in the repository from the attempt: no worktree, branch, commit or file.

---

### User Story 3 - Other source shapes (Priority: P2)

The spec may live on a branch that exists only on `origin`, or directly on the default branch with no branch of its own. Adopt handles both without the user creating branches by hand.

**Why this priority**: Less common than the SpecKit default, but each otherwise forces manual git work or a duplicate run.

**Independent Test**: For each shape, run adopt in a fixture repository and confirm the branch, worktree and recorded `adopted.source` shape.

**Acceptance Scenarios**:

1. **Given** the branch exists only on `origin`, **When** adopted, **Then** a local branch tracking it is created and the worktree is attached to it.
2. **Given** the spec dir is on the default branch with no branch of its own, **When** adopted, **Then** a new branch named after the spec dir is created from `base` and the worktree is attached to it.
3. **Given** a spec dir whose name differs from its branch name, **When** adopted, **Then** `spec_dir` records the spec dir's actual path unchanged.

---

### User Story 4 - Choose the entry stage (Priority: P2)

The inferred stage is a suggestion. The user can start earlier (for example to redo a weak plan) but never skip analysis.

**Why this priority**: Artifacts written outside factory may be stale or incomplete; analysis is the factory's gate before implementation.

**Independent Test**: Run adopt with each `--stage` value and with `implement`; confirm the first four are recorded as the chosen stage and `implement` is refused as a usage error.

**Acceptance Scenarios**:

1. **Given** an inferred stage, **When** the user overrides with `--stage specify|plan|tasks|analyze`, **Then** the run starts at the chosen stage and `adopted` records both inferred and chosen stages.
2. **Given** any source, **When** the user passes `--stage implement` or any other value, **Then** adopt exits with a usage error and writes nothing.

---

### User Story 5 - Provenance through review, approver and retro (Priority: P2)

Everyone downstream knows the run was adopted and which commits predate factory, so reviewers judge the whole change without blaming pre-adoption commits for factory-only rules.

**Why this priority**: Without it, reviewers would raise ENG-2 blockers no one can fix, and the approver could not tell what factory authored.

**Independent Test**: Adopt a branch carrying pre-existing commits, run through review, and confirm reviewers cover the whole `base...HEAD` diff, report pre-adoption commits as disclosed and non-blocking for ENG-2, and the approver screen and retro both state the run was adopted.

**Acceptance Scenarios**:

1. **Given** an adopted run, **When** reviewers run, **Then** they review the whole `base...HEAD` diff, apply ENG-2 only to commits after `adopted.base_commit`, and list earlier commits as pre-adoption.
2. **Given** an adopted run at the approver gate, **When** the screen is shown, **Then** it states the run was adopted, from which source and at which stage.
3. **Given** an adopted run, **When** the retro runs, **Then** it records that the run was adopted.

---

### User Story 6 - Resume points to adopt (Priority: P3)

A user who tries `/factory resume <branch>` on a plain SpecKit spec learns the right command instead of hitting a dead end.

**Why this priority**: Discoverability; small change.

**Independent Test**: Run `factory resume <name>` where no run matches; confirm exit 1 and an error message naming `adopt`; confirm resume of an existing factory run behaves as before.

**Acceptance Scenarios**:

1. **Given** no matching run, **When** the user runs resume, **Then** it exits 1 with "no matching run" and a hint to use `/factory adopt <branch|spec_dir>`.
2. **Given** a plain SpecKit spec, **When** the user runs resume, **Then** no run, worktree or branch is created.

### Edge Cases

- The source argument matches several spec dirs or branches: exit 3 (ambiguous run name), listing the candidates, nothing written.
- The source matches neither a local branch, a remote branch nor a spec dir on the default branch: exit 1 with the reason.
- The branch exists both locally and on `origin`: the local branch is used; adopt does not fetch, pull or push.
- The standard worktree path already exists: exit 1 naming the path, nothing written.
- A pending file for an adoption of the same source already exists: the existing pending run is reused, never duplicated.
- The default-branch shape when a branch named after the spec dir already exists: treated as the own-branch shape for that branch.
- `spec.md` still contains `[NEEDS CLARIFICATION]` markers: the dry-run report lists them and the confirmation grill raises them as open gaps.
- The source branch moves between dry-run and the write: the write re-checks every refusal and records `base_commit` from the branch HEAD at the write.
- The adoption commit fails (for example a git hook rejects it): the worktree, any branch adopt created and the written files are removed; the run stays pending and the error is reported.
- Older states without an `adopted` block and older history without the `adopted` event remain valid and behave unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The factory skill MUST route `/factory adopt <branch|spec_dir>` to the adopt flow, and MUST NOT adopt implicitly from `resume` or from a new-feature request.
- **FR-002**: The state CLI MUST provide `factory adopt <src> [--stage <stage>] [--dry-run]` as the single writer that creates an adopted run.
- **FR-003**: `--dry-run` MUST be read-only and MUST print a machine-readable report with: source shape, branch, spec dir, artifacts found, dirty paths, inferred stage, open `[NEEDS CLARIFICATION]` markers, the target worktree path, and the refusal reason when refused.
- **FR-004**: Adopt MUST recognise three source shapes: spec on its own local branch, branch only on `origin`, and spec dir on the default branch with no own branch; it MUST record the shape in `adopted.source`.
- **FR-005**: For a local branch adopt MUST attach the worktree to the existing branch without creating a branch; for a remote-only branch it MUST create a local branch tracking it; for the default-branch shape it MUST create a branch named after the spec dir from `base`.
- **FR-006**: The worktree path MUST be the standard `<repo>/../<repo-name>-factory/<branch>`.
- **FR-007**: Adopt MUST refuse with exit 1, naming the cause and writing nothing, when: the spec files or source branch have uncommitted changes (every dirty path named); the spec dir already has `factory/state.json` (pointing to `resume`); the spec dir has no `spec.md`; the source branch is checked out in another checkout (with a hint to switch away); or the target worktree path exists.
- **FR-008**: Adopt MUST infer the entry stage: `spec.md` only → `plan`; `spec.md` and `plan.md` → `tasks`; `tasks.md` present → `analyze`, regardless of checkbox state.
- **FR-009**: `--stage` MUST accept only `specify`, `plan`, `tasks` and `analyze`; any other value MUST be a usage error (exit 5) with nothing written.
- **FR-010**: The orchestrator MUST run the confirmation grill in pending state, using the same pending storage as a new run, seeded from `spec.md`: summarise the spec, ask only open gaps, the chain and confirmation of the entry stage, then write `brief.md`.
- **FR-011**: A declined adoption MUST leave nothing in the repository and MUST end its pending run the same way a declined new run ends.
- **FR-012**: The adopt write MUST re-check every refusal, then create or attach the worktree, write `state.json` from the pending state, move `brief.md` (and the pending profile) into `<spec_dir>/factory/`, append one `adopted` history entry, and commit `factory: adopt <branch>` — and nothing else.
- **FR-013**: If any step of the adopt write fails, adopt MUST remove everything it created (worktree, created branch, written files), leave the pending run intact, and exit with the reason.
- **FR-014**: Adopt MUST never commit, stage or modify files it did not author.
- **FR-015**: The history-event vocabulary MUST gain `adopted`, written only by the adopt command.
- **FR-016**: State MUST accept an optional `adopted` block holding source (branch and/or spec dir, and shape), inferred stage, chosen stage and `base_commit` (the adopted branch's HEAD at the write); validation MUST check its shape when present, and states without it MUST stay valid.
- **FR-017**: Validation MUST accept an adopted run with no `complete` history entries for stages before its chosen stage.
- **FR-018**: After adoption, the run MUST continue through the existing resume and stage flow unchanged, from the chosen stage to an open PR after the user's Approve.
- **FR-019**: Reviewers MUST review the whole `base...HEAD` diff of an adopted run, apply ENG-2 only to commits after `adopted.base_commit`, and disclose earlier commits as pre-adoption, never blocking for ENG-2.
- **FR-020**: The approver screen and the retro MUST state that the run was adopted, with its source and chosen stage.
- **FR-021**: When `resume` finds no matching run, its error MUST hint at `/factory adopt <branch|spec_dir>`; resume behaviour is otherwise unchanged.
- **FR-022**: Adopt MUST respect the run lock like every other writer and MUST refuse under a live lock.
- **FR-023**: `DESIGN.md`, `references/state.md`, `CONTEXT.md` (new term **Adopted run**), a new ADR and the reviewer role files MUST describe the adopt flow, the `adopted` block and event, and the ENG-2 boundary; `dist/` MUST render cleanly for every harness.

### Key Entities

- **Adopted run**: a factory run created from a spec that factory did not start; carries the `adopted` block and an `adopted` history entry, and otherwise behaves as any run.
- **Source**: what the user named: branch and/or spec dir, and its shape (`branch`, `remote-branch`, `default-branch`).
- **Adoption report**: the dry-run's read-only description of a source, its inferred stage and any refusal.
- **Base commit**: the adopted branch's HEAD at the adopt write; the boundary between pre-adoption commits and factory's own.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can take a plain SpecKit spec from any of the three source shapes to a running factory stage with one adopt command, one confirmation grill and no manual git or state editing.
- **SC-002**: 100% of dry-runs and refusals leave the repository's status, refs, worktree list and files unchanged.
- **SC-003**: Adoption never creates a second branch or spec dir for a spec that already has one (zero duplicate runs in tests of every shape).
- **SC-004**: Every adopted run passes state validation, and every existing factory-created run's resume behaviour and tests stay unchanged.
- **SC-005**: Reviewers raise zero blocking ENG-2 findings for pre-adoption commits, while still reviewing 100% of the `base...HEAD` diff.
- **SC-006**: The rendered distribution builds for every harness with the change.

## Assumptions

- The user adopts specs in the current repository only; cross-repository adoption is out of scope.
- Adopt reads git locally and never fetches, pulls or pushes; a stale remote view is the user's to refresh.
- `base` and the default branch are resolved as for a new run.
- The chain (lite or full) and fast mode are chosen in the confirmation grill, as for a new run.
- Re-running `specify` on an adopted spec updates the existing `spec.md` in place, as any specify pass does.
- Adoption of a run already in implementation (implement or later) is out of scope; such work enters at `analyze` at the latest.
- Abandoned pending adoption files are cleaned by the existing `prune` path; no new cleanup command is added.
