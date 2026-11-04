# Feature Specification: Adopt a spec started outside factory

**Feature Branch**: `022-adopt-spec`

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Add an adopt command so factory can take over a spec started outside it (plain SpecKit spec with no factory state) and continue the flow to PR." (settled decisions Q1-Q9 in `factory/brief.md`)

## Clarifications

### Session 2026-11-04 (grill)

- Q1: Entry point? → A: Explicit `/factory adopt <branch|spec_dir>`; `resume` never adopts, its `no run '<name>' in <repo>` error hints at `adopt` (FR-001, FR-021).
- Q2: Source shapes? → A: Own branch, remote-only branch, spec dir on the default branch; spec dir names kept as-is (FR-004, FR-005).
- Q3: Refusals? → A: Exit 1, nothing written (FR-007).
- Q4: Brief? → A: Confirmation grill seeded from `spec.md` (FR-010).
- Q5: Entry stage? → A: Inferred; the user confirms or overrides (FR-008).
- Q6: Provenance? → A: `adopted` event and state block, disclosed downstream (FR-015, FR-016, FR-020).
- Q7: Sequence? → A: Dry-run, pending grill, then the write (FR-003, FR-010, FR-012).
- Q8: Stage override? → A: `specify|plan|tasks|analyze` only (FR-009).
- Q9: Pre-adoption commits? → A: Whole diff reviewed; ENG-2 only after `adopted.base_commit` (FR-019).

### Session 2026-11-04 (clarify)

- Q1: How is an adoption's pending run identified? → A: Fixed name `<repo-name>-adopt-<branch>`, reused on retry (FR-010, FR-012); any other pending file of the repo refuses (FR-007).
- Q2: Spec dir on the local default branch but not on origin? → A: Refuse with exit 1 and its own reason; nothing written.
- Q3: What does "never fetches" cover? → A: The `factory adopt` command and the source branch; preflight's default-branch fetch still runs.
- Q4: What does specify do with an adopted `spec.md`? → A: Edits it in place (FR-024).
- Q5: ENG-1/ENG-3 for pre-adoption work? → A: Skipped like ENG-2; code reviewed in full (FR-019).

### Session 2026-11-04 (grill-with-docs)

- Q1: Tasks already checked in an adopted `tasks.md`? → A: Those checked at `adopted.base_commit` are pre-adoption: disclosed, outside analyze's blocking test-scope check; unchecked tasks get the full check; all code is still reviewed (FR-025).
- Q2: Do `plan` and `tasks` edit an adopted `plan.md` or `tasks.md` in place? → A: Yes, as `specify` does (FR-024).
- Q3: Which chain does the grill recommend? → A: `full` when the entry stage is `tasks` or `analyze`; the user may still choose lite.
- Q4: Glossary terms? → A: Adopted run, Adoption source, Adoption report, Pre-adoption commit (Key Entities); state field names unchanged.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Continue a SpecKit spec on its own branch (Priority: P1)

A user wrote a plain SpecKit spec on its feature branch (the SpecKit default) and wants factory to finish it. `/factory adopt <branch>` reports the inferred stage, runs a short confirmation grill, attaches a worktree to the existing branch, creates the run and continues through review and the approver gate to an open PR.

**Why this priority**: The most common shape: no duplicate branch, lost work or manual state editing.

**Independent Test**: In a fixture repository with a feature branch holding `spec.md` and `plan.md` (no factory state) and the main checkout on the default branch, run adopt and confirm a worktree on that same branch, a valid run state whose stage is `tasks`, an `adopted` history entry and one commit `factory: adopt <branch>`.

**Acceptance Scenarios**:

1. **Given** a feature branch with a spec dir holding only `spec.md`, **When** the user runs adopt and confirms, **Then** the run's entry stage is `plan`.
2. **Given** a spec dir holding `spec.md` and `plan.md`, **When** adopted, **Then** the entry stage is `tasks`.
3. **Given** a spec dir holding `tasks.md` (with or without checked boxes), **When** adopted, **Then** the entry stage is `analyze`, and implement later resumes from the `tasks.md` checkboxes as it does today.
4. **Given** a confirmed adoption, **When** the write completes, **Then** a worktree exists at `<repo>/../<repo-name>-factory/<branch>` on the existing branch (no new branch), `state.json` and `brief.md` sit in `<spec_dir>/factory/`, and the branch has exactly one new commit, `factory: adopt <branch>`.
5. **Given** an adopted run, **When** the orchestrator continues, **Then** it runs the entry stage and every later stage exactly as for a run factory created, ending at an open PR after the user's Approve.

---

### User Story 2 - Safe preview and refusals (Priority: P1)

The user sees the dry-run report before anything is written; adoption never commits work factory did not author or touches an existing run.

**Why this priority**: A wrong adoption must cost nothing.

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

Adopt also handles a branch only on `origin` and a spec dir on the default branch, without hand-made branches.

**Why this priority**: Each otherwise forces manual git work or a duplicate run.

**Independent Test**: For each shape, run adopt in a fixture repository and confirm the branch, worktree and recorded `adopted.source` shape.

**Acceptance Scenarios**:

1. **Given** the branch exists only on `origin`, **When** adopted, **Then** a local branch tracking it is created and the worktree is attached to it.
2. **Given** the spec dir is on `base` (the default branch on `origin`) with no branch of its own, **When** adopted, **Then** a new branch named after the spec dir is created from `base` and the worktree is attached to it.
3. **Given** a spec dir whose name differs from its branch name, **When** adopted, **Then** `spec_dir` records the spec dir's actual path unchanged.

---

### User Story 4 - Choose the entry stage (Priority: P2)

The inferred stage is a suggestion. The user can start earlier (for example to redo a weak plan) but never skip analysis.

**Why this priority**: Outside artifacts may be stale; analysis gates implementation.

**Independent Test**: Run adopt with each `--stage` value and with `implement`; confirm the first four are recorded as the chosen stage and `implement` is refused as a usage error.

**Acceptance Scenarios**:

1. **Given** an inferred stage, **When** the user overrides with `--stage specify|plan|tasks|analyze`, **Then** the run starts at the chosen stage and `adopted` records both inferred and chosen stages.
2. **Given** any source, **When** the user passes `--stage implement` or any other value, **Then** adopt exits with a usage error and writes nothing.

---

### User Story 5 - Provenance through review, approver and retro (Priority: P2)

Everyone downstream knows the run was adopted and which commits predate factory, so reviewers judge the whole change without blaming pre-adoption commits for factory-only rules.

**Why this priority**: Otherwise reviewers raise unfixable commit-rule blockers and the approver cannot tell what factory authored.

**Independent Test**: Adopt a branch carrying pre-existing commits and checked tasks, run analyze, review, approver and retro, and confirm scenarios 1-4.

**Acceptance Scenarios**:

1. **Given** an adopted run, **When** reviewers run, **Then** they review the whole `base...HEAD` diff, apply ENG-1, ENG-2 and ENG-3 commit checks only after `adopted.base_commit`, and list earlier commits and tasks as pre-adoption.
2. **Given** an adopted run at the approver gate, **When** the screen is shown, **Then** it states the run was adopted, from which source and at which stage.
3. **Given** an adopted run, **When** the retro runs, **Then** it records that the run was adopted.
4. **Given** an adopted `tasks.md` with tasks checked at `adopted.base_commit`, **When** analyze runs, **Then** those tasks are excluded from its blocking test-scope check and listed as pre-adoption, and every unchecked task gets the full check.

---

### User Story 6 - Resume points to adopt (Priority: P3)

A user who tries `/factory resume <branch>` on a plain SpecKit spec learns the right command instead of hitting a dead end.

**Independent Test**: Run `factory resume` with no matching run and with an existing run; confirm both scenarios and unchanged resume.

**Acceptance Scenarios**:

1. **Given** no matching run, **When** the user runs resume, **Then** it exits 1 with `no run '<name>' in <repo>` and a hint to use `adopt <branch|spec_dir>`.
2. **Given** a plain SpecKit spec, **When** the user runs resume, **Then** no run, worktree or branch is created.

### Edge Cases

- The source argument matches several spec dirs or branches: exit 3 (ambiguous run name), listing the candidates, nothing written.
- The source matches no branch or spec dir: exit 1 with the reason.
- The branch exists both locally and on `origin`: the local branch is used, unfetched.
- The spec dir is committed on the local default branch but not on `base`: refused (FR-007).
- A retry after a failed write reuses the pending file; after a declined attempt it is replaced (FR-010); never duplicated.
- Another pending file of the same repository exists: dry-run and write both refuse (FR-007).
- Default-branch shape whose spec-dir-named branch already exists: treated as the own-branch shape.
- `spec.md` still contains `[NEEDS CLARIFICATION]` markers: the dry-run report lists them and the confirmation grill raises them as open gaps.
- A task checked at `adopted.base_commit` whose ID changes later, or a task added after adoption, is not pre-adoption and gets the full test-scope check.
- The source branch moves between dry-run and the write: the write re-checks every refusal and records `base_commit` from the branch HEAD at the write.
- The adoption commit fails (for example a git hook rejects it): rolled back, the run stays pending (FR-013).
- Older states and history without `adopted` remain valid and unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The factory skill MUST route `/factory adopt <branch|spec_dir>` to the adopt flow, and MUST NOT adopt implicitly from `resume` or from a new-feature request.
- **FR-002**: The state CLI MUST provide `factory adopt <src> [--stage <stage>] [--dry-run]` as the single writer that creates an adopted run.
- **FR-003**: `--dry-run` MUST be read-only and MUST print a machine-readable report with: source shape, branch, spec dir, artifacts found, dirty paths, inferred stage, open `[NEEDS CLARIFICATION]` markers, the target worktree path, and the refusal reason when refused.
- **FR-004**: Adopt MUST recognise three source shapes: spec on its own local branch, branch only on `origin`, and spec dir on `base` (the default branch on `origin`) with no own branch; it MUST record the shape in `adopted.source`.
- **FR-005**: For a local branch adopt MUST attach the worktree to the existing branch without creating a branch; for a remote-only branch it MUST create a local branch tracking it; for the default-branch shape it MUST create a branch named after the spec dir from `base`.
- **FR-006**: The worktree path MUST be the standard `<repo>/../<repo-name>-factory/<branch>`.
- **FR-007**: Adopt MUST refuse with exit 1, naming the cause and writing nothing, when: the spec files or source branch have uncommitted changes (every dirty path named); the spec dir already has `factory/state.json` (pointing to `resume`); the spec dir has no `spec.md`; the source branch is checked out in another checkout (with a hint to switch away); the target worktree path exists; the spec dir is on the local default branch but not on `base` ("spec dir is on local `<default>` but not on `<base>`; push it or create its branch first"); or a pending file of the repository other than the adoption's own exists (named, with a hint to resume or prune it).
- **FR-008**: Adopt MUST infer the entry stage: `spec.md` only → `plan`; `spec.md` and `plan.md` → `tasks`; `tasks.md` present → `analyze`, regardless of checkbox state.
- **FR-009**: `--stage` MUST accept only `specify`, `plan`, `tasks` and `analyze`; any other value MUST be a usage error (exit 5) with nothing written.
- **FR-010**: The orchestrator MUST run the confirmation grill in pending state, using the same pending storage as a new run under the fixed name `<repo-name>-adopt-<branch>` (reused on retry; an ended one is replaced), seeded from `spec.md`: summarise the spec, ask only open gaps, the chain (recommending `full` when the entry stage is `tasks` or `analyze`) and confirmation of the entry stage, then write `brief.md`.
- **FR-011**: A declined adoption MUST leave nothing in the repository and MUST end its pending run the same way a declined new run ends.
- **FR-012**: The adopt write MUST select its pending run by the name `<repo-name>-adopt-<branch>`, re-check every refusal, then create or attach the worktree, write `state.json` from the pending state, move `brief.md` (and the pending profile) into `<spec_dir>/factory/`, append one `adopted` history entry, and commit `factory: adopt <branch>` — and nothing else.
- **FR-013**: If any step of the adopt write fails, adopt MUST remove everything it created (worktree, created branch, written files), leave the pending run intact, and exit with the reason.
- **FR-014**: Adopt MUST never commit, stage or modify files it did not author.
- **FR-015**: The history-event vocabulary MUST gain `adopted`, written only by the adopt command.
- **FR-016**: State MUST accept an optional `adopted` block holding source (branch and spec dir, and shape), inferred stage, chosen stage and `base_commit` (the adopted branch's HEAD at the write); validation MUST check its shape when present, and states without it MUST stay valid.
- **FR-017**: Validation MUST accept an adopted run with no `complete` history entries for stages before its chosen stage.
- **FR-018**: After adoption, the run MUST continue through the existing resume and stage flow unchanged, from the chosen stage to an open PR after the user's Approve.
- **FR-019**: Reviewers MUST review the whole `base...HEAD` diff of an adopted run, apply ENG-1, ENG-2 and ENG-3 commit checks only to commits after, and tasks unchecked at, `adopted.base_commit`, and disclose earlier ones as pre-adoption, never blocking for those rules.
- **FR-020**: The approver screen and the retro MUST state that the run was adopted, with its source and chosen stage.
- **FR-021**: When `resume` finds no matching run, its error (`no run '<name>' in <repo>`) MUST hint at `adopt <branch|spec_dir>` (the CLI's own verb); resume behaviour is otherwise unchanged.
- **FR-022**: Adopt MUST respect the run lock like every other writer and MUST refuse under a live lock.
- **FR-023**: `DESIGN.md`, `references/state.md`, `CONTEXT.md` (the Key Entities terms), a new ADR and the reviewer role files MUST describe the adopt flow, the `adopted` block and event, and the pre-adoption boundary; `dist/` MUST render cleanly for every harness.
- **FR-024**: When state has an `adopted` block, the `specify`, `plan` and `tasks` stages MUST treat an existing `spec.md`, `plan.md` or `tasks.md` respectively as their base and apply targeted edits (brief and grill answers, upstream changes, sections factory requires), never regenerating it.
- **FR-025**: Analyze MUST exclude tasks checked in `tasks.md` at `adopted.base_commit` (by task ID) from its blocking test-scope check and list them as pre-adoption; every other task gets the full check.

### Key Entities

- **Adopted run**: a factory run created from a spec that factory did not start; carries the `adopted` block and an `adopted` history entry, and otherwise behaves as any run.
- **Adoption source**: what the user named: branch and spec dir, and its shape (`branch`, `remote-branch`, `default-branch`); stored as `adopted.source`.
- **Adoption report**: the dry-run's read-only description of an adoption source, its inferred stage and any refusal.
- **Pre-adoption commit**: a commit reachable from `adopted.base_commit` (the adopted branch's HEAD at the adopt write) and not from `base`; reviewed, never blocking for ENG-1, ENG-2 or ENG-3. Tasks checked at `base_commit` are pre-adoption tasks.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can take a plain SpecKit spec from any of the three source shapes to a running factory stage with one adopt command, one confirmation grill and no manual git or state editing.
- **SC-002**: 100% of dry-runs and refusals leave the repository's status, refs, worktree list and files unchanged.
- **SC-003**: Adoption never creates a second branch or spec dir for a spec that already has one (zero duplicate runs in tests of every shape).
- **SC-004**: Every adopted run passes state validation, and every existing factory-created run's resume behaviour and tests stay unchanged.
- **SC-005**: Reviewers raise zero blocking ENG-1, ENG-2 or ENG-3 findings and analyze zero blocking test-scope findings for pre-adoption commits and tasks, while reviewers still review 100% of the `base...HEAD` diff.
- **SC-006**: The rendered distribution builds for every harness with the change.

## Assumptions

- Cross-repository adoption is out of scope.
- `factory adopt` never fetches, pulls or pushes, nor fetches the source branch (a stale view is the user's to refresh); the `/factory adopt` route's preflight still fetches the default branch, and the write re-inspects against that fresh `base`.
- `base` and the default branch are resolved as for a new run.
- The chain (lite or full) and fast mode are chosen in the confirmation grill, as for a new run.
- FR-024 and FR-025 are prose changes to the spec-builder role only.
- Work already in implementation enters at `analyze` at the latest; later entry is out of scope.
- Abandoned pending adoption files are cleaned by the existing `prune` path; no new cleanup command is added.
