# Feature Specification: Stabilise and optimise the factory

**Feature Branch**: `007-stabilise-factory`

**Created**: 2026-10-25

**Status**: Draft

**Input**: User description: "Improve and optimise the software factory, using 'Harness-agnostic factory design and plan.md' and docs/stability-brief.md as inputs." (see `factory/brief.md` for the settled decisions)

## User Scenarios & Testing *(mandatory)*

The user is a developer who runs the factory to turn a feature request into a reviewed pull request, and who trusts the recorded state to resume runs, audit decisions and report what happened. The factory's orchestrator is the secondary actor: it records every stage, spawn, wait and decision through a single writer.

### User Story 1 - Trustworthy run state (Priority: P1)

A run owner opens a run's saved state at any time and sees where the run really is: every stage transition, spawn and user wait recorded with real, non-decreasing timestamps, only accepted vocabulary values, and no field that fails validation. Nobody — including a drifting orchestrator — can hand-edit the state file; every change goes through one CLI writer that stamps the time, validates, writes atomically and commits the checkpoint. If that tooling cannot run, the run halts rather than falling back to manual editing.

**Why this priority**: trustworthy state is the foundation of every other guarantee; runs 005 and 006 show invented timestamps, missing entries and off-vocabulary values caused by hand-edited state.

**Independent Test**: Replay the two historical runs' saved states through the validation command and see their known defects reported; attempt an illegal vocabulary value and a concurrent manual edit and see both refused.

**Acceptance Scenarios**:

1. **Given** a run mid-stage, **When** a stage completion is recorded, **Then** the write is stamped with the current time, validated, written atomically, and committed as the stage checkpoint.
2. **Given** a state containing backwards timestamps, off-vocabulary events or missing entries, **When** validation runs, **Then** every defect is reported with its location and reason.
3. **Given** a state saved before this change, **When** it is read or validated, **Then** it is accepted and reported accurately without being rewritten by the read path.
4. **Given** an environment where the state-writing tooling cannot run, **When** progress must be recorded, **Then** the run halts with a clear message instead of editing state by hand.

---

### User Story 2 - Accurate accounting and decision audit (Priority: P1)

A run owner reviewing a run sees totals that respect the wall clock even when reviewers ran in parallel, agent effort reported separately from human time, and an append-only list of every settled question and answer — including fast-mode auto-accepts — so nothing is published without a vetoable decision record.

**Why this priority**: today's reports overstate human time past the wall clock and the fast-mode audit is empty for every stage but the current one, misleading the only person who can stop a bad PR.

**Independent Test**: Run a scenario with two parallel reviews and a fast-mode relay round; totals must fit inside the wall clock and the auto-accepted answer must be listed.

**Acceptance Scenarios**:

1. **Given** two concurrent reviewer sessions, **When** totals are computed, **Then** agent time is the union of spawn intervals and human plus agent time never exceeds wall-clock time.
2. **Given** a stage's questions were auto-accepted, **When** the relay is cleared at checkpoint, **Then** each answer is preserved in the decision record with stage, question ID, answer, auto flag and time.
3. **Given** a run awaiting approval in fast mode, **When** the approver package is shown, **Then** every auto-accepted round of every stage is listed for veto.

---

### User Story 3 - Enforced gates and single writer (Priority: P2)

A run cannot advance past an unrecorded gate: implementation needs clean analysis, review needs a recorded passing verification, and the PR needs a recorded approval decision. A malformed role output — however persuasive — cannot advance a stage, and two sessions cannot write the same run at once.

**Why this priority**: run 006 reached a pull request with no recorded verify, and no code prevented it. Enforcement makes User Story 1's state trustworthy after the fact.

**Independent Test**: Attempt each illegal transition, feed in a malformed role output, and start a second session against a live run; each attempt is refused with a reason and a test exists per refusal.

**Acceptance Scenarios**:

1. **Given** no recorded passing verification, **When** a transition to review is requested, **Then** the request is refused and names the missing record.
2. **Given** a role's final output lacks its machine-readable block, **When** the orchestrator receives it, **Then** the output is rejected and the retry-once policy applies before any halt.
3. **Given** a run whose lock is held by a live session, **When** another session tries to write it, **Then** the write is refused and the owner reported; a stale lock needs explicit takeover.
4. **Given** any pushed change, **When** continuous integration runs, **Then** the full suite runs and any source/generated drift fails the change.

---

### User Story 4 - Portable and safe multi-harness use (Priority: P3)

A developer runs the factory on any supported harness with consistent defaults: no adapter carries another person's model choices, missing setup is guided rather than fatal, checkpoints commit only declared files (never stray build output or local secrets), and a run moved to another machine or path can be rebound and resumed.

**Why this priority**: multi-harness use works but carries personal configuration, whole-tree commits and absolute paths that break outside one machine.

**Independent Test**: Install on a clean machine per harness and confirm the effective configuration is consistent; attempt a checkpoint with undeclared files present and rebind a moved run.

**Acceptance Scenarios**:

1. **Given** a fresh installation, **When** the effective per-role models are inspected, **Then** only the harness requiring defaults carries them and personal choices come from the user's configuration file.
2. **Given** a checkpoint with untracked files in the worktree, **When** it commits, **Then** only the spec directory and the role's declared files are committed and undeclared changes are reported.
3. **Given** a missing setup prerequisite for the current harness, **When** preflight runs, **Then** the run names the exact setup command and offers to run it.
4. **Given** a run whose worktree now lives at another path, **When** the rebind command runs, **Then** the branch is validated, stored paths rewritten, and the run resumes.

---

### User Story 5 - Proven recovery (Priority: P4)

A developer trusts that a run killed at any stage resumes without loss: no re-asking answered questions, no redoing committed tasks, no duplicate branches, worktrees or pull requests. Demonstrated, not asserted: an automated kill-and-resume suite on a fixture repository, a scripted golden-run checklist per harness, and per-harness evidence that read-only roles cannot edit (or an honest disclosure where unenforceable).

**Why this priority**: recovery worked twice in practice but is unproven against a repeatable standard.

**Independent Test**: Run the kill-and-resume suite and the golden-run checklist on a fixture repository across two harnesses.

**Acceptance Scenarios**:

1. **Given** a fixture run killed at any stage, **When** the suite resumes it, **Then** no answered question is re-asked, no committed task redone, and no duplicate branch, worktree or pull request appears.
2. **Given** the golden-run checklist, **When** executed on two harnesses including a kill-and-resume across them, **Then** results are recorded per adapter and capability tier.
3. **Given** a read-only role on a harness that can enforce it, **When** the conformance test runs, **Then** the role cannot edit files; where unenforceable, the limitation is documented.

---

### User Story 6 - Hardening and a lighter orchestrator (Priority: P5)

A developer sees argument errors that explain themselves instead of crashing, can preview cleanup of stale pending files, sees harness-reported usage labelled separately from estimates, and reads the Pen design rules in one place, keeping the orchestrator's instructions short.

**Why this priority**: real defects and duplication, but none blocks state trust, gates or recovery.

**Independent Test**: Invoke the installer with a missing argument value, run a cleanup preview, and confirm the design rules live in a single reference.

**Acceptance Scenarios**:

1. **Given** an installer invocation missing an argument value, **When** it runs, **Then** it fails with a clear usage message and no crash.
2. **Given** stale pending files, **When** the cleanup preview runs, **Then** nothing is deleted, the candidates are listed, and deletion is explicit.
3. **Given** a harness that reports usage, **When** a spawn is recorded, **Then** reported usage is stored and shown separately from word-count estimates.

---

### Edge Cases

- An older state file, including legacy relay shapes (single batch, string answers) and a missing lock or decisions list: readers accept and report it; writers upgrade on first write.
- A writer whose clock jumps, or two writes close together: recorded times never go backwards within a record.
- A resume with a missing worktree, gone branch, or ambiguous run name: the CLI reports it and refuses to guess.
- A checkpoint attempted with undeclared or untracked changes present.
- Totals computed over spawns that overlap, run zero-length, or are missing.
- A lock held by a dead process, or by a live one on another machine sharing the run's home directory.
- Well-formed prose with a malformed or non-final machine-readable block.
- Analysis findings needing a user decision while fast mode is on: never auto-answered.

## Requirements *(mandatory)*

### Functional Requirements

**State integrity and single writer (S1, S2, S7)**

- **FR-001**: The system MUST record every stage completion, spawn entry, user wait, settled answer and status change through a single write interface that stamps the time, validates the vocabulary, writes atomically and commits the checkpoint. The orchestrator MUST NOT hand-edit state.
- **FR-002**: Where the state-writing tooling cannot run, the system MUST halt the run with a clear message and MUST NOT fall back to manual state editing.
- **FR-003**: The system MUST validate state against the current schema — stage, status, timeline kind and history event vocabularies, required fields per stage — before every write and on demand, reporting violations with their location.
- **FR-004**: Recorded timestamps MUST be real and non-decreasing within their record; every spawn and stage transition MUST be recorded exactly once.
- **FR-005**: The system MUST guard each run against concurrent writers with a lock recording owner, harness and time; writes MUST be refused while a live lock exists, the lock MUST be visible in reports, and a stale lock MUST need explicit takeover.

**Enforced gates (S3, S4)**

- **FR-006**: The system MUST refuse illegal stage transitions: review requires a recorded passing verification; publishing a PR requires a recorded approval decision; implementation requires analysis recorded as clean, remediated, or explicitly user-overridden.
- **FR-007**: The system MUST validate every role's final machine-readable block (envelope, findings, verdict shapes) and reject malformed output; the retry-once policy then applies.

**Accurate reporting and audit (S5, S6, S18)**

- **FR-008**: Settled answers MUST move to an append-only decision record (stage, question ID, answer, auto flag, time) before the stage's relay is cleared; the approver package MUST read this record and list every auto-accepted answer for veto.
- **FR-009**: Spawn start and end times MUST be stored; agent elapsed time MUST be the union of spawn intervals, reported separately from human time; reports MUST never subtract summed parallel durations from wall-clock time.
- **FR-010**: Where a harness reports usage, the system MUST label it separately from word-count estimates.

**Recovery and portability (S8, S13, S14, S15)**

- **FR-011**: The CLI's read and write commands MUST be covered by fixture-based tests over every accepted state version, pending runs, state copies in later worktrees, missing worktrees, ambiguous names and legacy relay shapes.
- **FR-012**: The system MUST provide a rebind command that validates a moved run's branch and rewrites its stored paths, and MUST document that sharing the run's home alone does not move a run.
- **FR-013**: The system MUST ship a fixture repository, a scripted golden-run checklist per harness, and automated kill-and-resume tests; the live two-harness golden run (start, pause, kill, cross-harness resume, approve) is recorded after merge.
- **FR-014**: Per-adapter conformance MUST verify that a read-only role cannot edit files where the harness can enforce it, and document the limitation where it cannot.

**Configuration and setup (S10, S11)**

- **FR-015**: Adapters MUST NOT ship default models except where the harness requires them; personal model choices MUST live in the user's factory configuration; the installer MUST print the effective model per role; an automated check MUST keep documented and shipped defaults in agreement.
- **FR-016**: On missing setup for the current harness, preflight MUST name the exact setup command and offer to run it, as it already does for a missing project scaffold.

**Checkpoint safety (S12)**

- **FR-017**: A checkpoint MUST commit only the spec directory and the files the role declared in its output; undeclared or untracked changes MUST be reported, never committed.

**Automation (S9)**

- **FR-018**: Continuous integration MUST run the full automated suite on every change, re-render generated output for every harness and fail on any drift, and check the installer's syntax.

**Hardening and context (S16, S17, S19)**

- **FR-019**: The system MUST offer a cleanup preview for stale pending files that deletes nothing by default; deletion MUST be explicit.
- **FR-020**: The installer MUST validate its arguments and fail with a clear usage message rather than a crash when a value is missing.
- **FR-021**: Pen design rules MUST live in one reference, with duplicated prose removed from the orchestrator and redundant references, shortening its context without removing any rule.

**Compatibility and delivery**

- **FR-022**: Readers MUST accept state versions 1 through the current one, including legacy relay shapes; writers MUST upgrade a run on its first write; saved runs MUST keep resuming unchanged.
- **FR-023**: The change MUST be delivered as one run and one pull request, ordered by the milestones in the Assumptions, with the build re-rendering all harnesses and failing on any generated-output diff.

### Key Entities

- **Run state**: the single record of where a run is — stage, status, mode, harness, timestamps, waits, ledger, decisions, history. Only the write interface changes it.
- **Transition record**: a history entry proving a stage or gate happened: vocabulary-checked event, time, commit, harness.
- **Decision record**: an append-only entry per settled question and answer, keeping the auto flag so fast-mode choices can be vetoed.
- **Spawn interval**: one role execution's start and end times, feeding the union-based effort computation.
- **Run lock**: owner process, harness and time, guarding one run against concurrent writers.
- **Adapter configuration**: per-harness defaults and personal overrides, with the effective value reportable per role.
- **Conformance fixture and golden-run result**: the fixture repository, its scripted checklist and the recorded per-adapter results.

### Quality and Verification Constraints

- **Data integrity**: atomic writes, vocabulary validation before every write, append-only decisions and timeline, non-decreasing timestamps, upgrade only through the writer.
- **Security**: no undeclared files or local secrets in checkpoints; read-only roles cannot edit, or the limitation is disclosed; no personal model choices in shared adapters.
- **Error and resource limits**: retry-once-then-halt preserved; stale locks need explicit takeover; cleanup is preview-first.
- **Compatibility**: state versions 1–3 stay readable, legacy question shapes usable, pre-existing runs resumable at their recorded stage.
- **Dependencies**: standard-library-only tooling preserved; any new runtime dependency needs a stated reason in the plan.
- **Observability**: every spawn, transition, wait and decision is visible in state and the run report.
- **Verification**: fixture-based tests for every read and write command, a CI regression suite, replay of the two historical run states, and the golden-run checklist on two harnesses.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of state writes go through the validated atomic writer; zero hand-edited fields appear in any test run.
- **SC-002**: Replaying the two historical run states through validation reports every known defect from the stability brief, with zero false passes.
- **SC-003**: With parallel reviews, reported human plus agent time is within wall-clock time in 100% of test runs, and agent effort reflects the union of spawn intervals.
- **SC-004**: Every auto-accepted answer of every stage appears in the approver's veto list before publication.
- **SC-005**: Every illegal transition, malformed role output and concurrent write attempt is refused in the automated suite, with a test per refusal.
- **SC-006**: A run killed at each stage of the fixture suite resumes with zero repeated questions, zero redone tasks and zero duplicate branches, worktrees or pull requests.
- **SC-007**: Continuous integration runs the whole suite on every change and blocks any source/generated drift within one change cycle.
- **SC-008**: Checkpoints commit only declared files in 100% of test runs, and no personal model configuration ships in any adapter.

## Assumptions

- Scope is all of S1–S19 (P0–P2) plus the context trim: consolidated Pen design rules and removal of prose made redundant by the CLI writer.
- The state schema advances one version; readers accept 1 through the new one; writers upgrade a run on its first write.
- State writes go only through the CLI: the orchestrator never hand-edits state, and a missing Python 3 runtime halts the run. The CLI entry point stays thin, its logic in importable modules the renderer copies into the generated output.
- Only the Claude Code adapter ships default models (opus/sonnet); Codex, Copilot, OpenCode and ZCode inherit the session's models. The current personal OpenCode model choices move to the user's factory configuration.
- The live two-harness golden run is recorded after merge; the kill-and-resume suite and fixture repository ship with this change.
- The historical run states 005 and 006, recovered from git history, serve as validation fixtures with their known defects as expected reports.
- "Harness-agnostic factory design and plan.md" moves into the docs directory with its status marked implemented.
- Out of scope: renaming the repository, and the brief's exclusions — automatic merge or deploy, hosted dashboard, multi-repository features, a database, automatic worktree deletion.
- Build re-renders all five harnesses and fails on any generated-output diff; tests run through the standard-library runner, discovery extended as new test folders appear.
- Judgement stays in roles; only mechanical bookkeeping (time, vocabulary, file write, transition check) moves into code.
