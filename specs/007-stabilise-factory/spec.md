# Feature Specification: Stabilise and optimise the factory

**Feature Branch**: `007-stabilise-factory`

**Created**: 2026-10-25

**Status**: Draft

**Input**: User description: "Improve and optimise the software factory, using 'Harness-agnostic factory design and plan.md' and docs/stability-brief.md as inputs." (see `factory/brief.md` for the settled decisions)

## Clarifications

### Session 2026-10-25

- Q: When is a run lock stale? → A: Recorded host, owner process gone; elsewhere never automatically; takeover always explicit.
- Q: What counts as human time? → A: Union of recorded user-wait intervals; human + agent ≤ wall clock.
- Q: How are code changes declared at checkpoints? → A: Role output lists every changed file; checkpoints commit the spec directory plus exactly that list.
- Q: What defect list must replaying runs 005 and 006 produce? → A: Stability brief §3 core; appended extras need a written reason.
- Q: How is a gate override recorded? → A: Normal decision record entry (stage, question ID, answer, auto=false, time) in the approver's veto list.

### Session 2026-10-25 (grill-with-docs)

- Source documents: same PR; each S-item's design decision lands in `DESIGN.md` with or before its implementation; the contradicted sentences in `DESIGN.md`, `state.md` (manual-write fallback), `docs/product-brief.md` §14 and `README.md` are corrected there (FR-024).
- Passing verification: a `verify` history entry through the CLI after the orchestrator re-runs build and test itself, carrying commands and pass/fail; review refuses unless the latest passes (FR-006).
- History events: closed list in `state.md` (FR-003).
- Run lock: covers pending runs, beside the pending file (FR-005).
- SC-001 measurement: the suite exercises each mutating command; validate reports zero anomalies in states test runs produce (SC-001).
- Stale pending file: one whose run has a worktree state or has ended (`pr-open`/`aborted`); the run's only state is never one (FR-019).

## User Scenarios & Testing *(mandatory)*

The user is a developer running the factory from request to reviewed pull request, trusting recorded state to resume, audit and report.

### User Story 1 - Trustworthy run state (Priority: P1)

A run owner opens saved state and sees where the run really is: every transition, spawn and wait with real, non-decreasing timestamps, accepted vocabulary values, no failing field — written only by the one CLI writer (FR-001–FR-005), never by hand.

**Why this priority**: trustworthy state underpins every guarantee; runs 005 and 006 show hand-edited state damage.

**Independent Test**: Replay both historical states through validation, expecting their stability brief §3 defects; attempt an illegal vocabulary value and a concurrent manual edit, expecting refusals.

**Acceptance Scenarios**:

1. **Given** a run mid-stage, **When** a stage completion is recorded, **Then** the write is stamped, validated, atomic and committed as the checkpoint.
2. **Given** backwards timestamps, off-vocabulary events or missing entries, **When** validation runs, **Then** every defect is reported with location and reason.
3. **Given** a state saved before this change, **When** it is read or validated, **Then** it is accepted and reported accurately, never rewritten.
4. **Given** no runnable state-writing tooling, **When** progress must be recorded, **Then** the run halts with a clear message instead of hand-editing state.

---

### User Story 2 - Accurate accounting and decision audit (Priority: P1)

A run owner sees totals that respect the wall clock despite parallel reviewers, agent effort separate from human time, and an append-only decision record with fast-mode auto-accepts (FR-008, FR-009).

**Why this priority**: reports overstate human time and the fast-mode audit ends at the current stage.

**Independent Test**: Two parallel reviews and a fast-mode relay round: totals fit the wall clock, the auto-accepted answer listed.

**Acceptance Scenarios**:

1. **Given** two concurrent reviewer sessions, **When** totals are computed, **Then** agent time is the union of spawn intervals, human time the union of user-wait intervals, and their sum never exceeds wall-clock time.
2. **Given** a stage's questions were auto-accepted, **When** the relay is cleared at checkpoint, **Then** each answer is preserved in the decision record with stage, question ID, answer, auto flag and time.
3. **Given** a run awaiting approval in fast mode, **When** the approver package is shown, **Then** every auto-accepted round of every stage is listed for veto.

---

### User Story 3 - Enforced gates and single writer (Priority: P2)

A run cannot advance past an unrecorded gate (FR-006); a malformed role output cannot advance a stage (FR-007); two sessions cannot write the same run at once (FR-005).

**Why this priority**: run 006 reached a PR with no recorded verify and no code stopped it.

**Independent Test**: Attempt each illegal transition, a malformed role output, and a second session against a live run; each refused with a reason, a test per refusal.

**Acceptance Scenarios**:

1. **Given** no recorded passing verification, **When** a transition to review is requested, **Then** the request is refused and names the missing record; the latest verify record (Key Entities) must pass.
2. **Given** a role's final output lacks its machine-readable block, **When** the orchestrator receives it, **Then** it is rejected and the retry-once policy applies before any halt.
3. **Given** a run whose lock is held by a live session, **When** another session tries to write it, **Then** the write is refused and the owner reported; any takeover is explicit.
4. **Given** any pushed change, **When** continuous integration runs, **Then** the full suite runs and any source/generated drift fails the change.

---

### User Story 4 - Portable and safe multi-harness use (Priority: P3)

A developer runs the factory on any supported harness with consistent defaults, guided setup, declared-file checkpoints, and rebinding for a moved run (FR-012, FR-015–FR-017).

**Why this priority**: multi-harness use carries personal configuration, whole-tree commits, absolute paths that break off one machine.

**Independent Test**: Install on a clean machine per harness and confirm consistent effective configuration; attempt a checkpoint with undeclared files and rebind a moved run.

**Acceptance Scenarios**:

1. **Given** a fresh installation, **When** effective per-role models are inspected, **Then** only the harness requiring defaults carries them and personal choices come from the user's configuration file.
2. **Given** a checkpoint with untracked files in the worktree, **When** it commits, **Then** only the spec directory plus the role's declared files are committed and anything else is reported.
3. **Given** a missing setup prerequisite for this harness, **When** preflight runs, **Then** the run names the exact setup command and offers to run it.
4. **Given** a run whose worktree now lives at another path, **When** the rebind command runs, **Then** the branch is validated, stored paths rewritten, and the run resumes.

---

### User Story 5 - Proven recovery (Priority: P4)

A developer trusts a run killed at any stage resumes without loss: no re-asked questions, no redone tasks, no duplicate branches, worktrees or pull requests. Demonstrated, not asserted, by FR-013 and FR-014's suite, checklist and conformance evidence.

**Why this priority**: recovery is unproven against a repeatable standard.

**Independent Test**: The kill-and-resume suite and the golden-run checklist on a fixture repository across two harnesses.

**Acceptance Scenarios**:

1. **Given** a fixture run killed at any stage, **When** the suite resumes it, **Then** no answered question is re-asked, no committed task redone, and no duplicate branch, worktree or pull request appears.
2. **Given** the golden-run checklist, **When** executed on two harnesses including a kill-and-resume across them, **Then** results are recorded per adapter and capability tier.
3. **Given** a read-only role on a harness that can enforce it, **When** the conformance test runs, **Then** the role cannot edit files; where unenforceable, the limitation is documented.

---

### User Story 6 - Hardening and a lighter orchestrator (Priority: P5)

A developer gets self-explaining argument errors, can preview stale-pending cleanup, sees reported usage separate from estimates, and reads the Pen rules in one place (FR-010, FR-019–FR-021).

**Why this priority**: real defects and duplication, none blocking.

**Independent Test**: Invoke the installer with a missing argument value, run a cleanup preview, and confirm the design rules live in one reference.

**Acceptance Scenarios**:

1. **Given** an installer invocation missing an argument value, **When** it runs, **Then** it fails with a clear usage message and no crash.
2. **Given** stale pending files, **When** the cleanup preview runs, **Then** nothing is deleted, the candidates are listed, and deletion is explicit.
3. **Given** a harness that reports usage, **When** a spawn is recorded, **Then** reported usage is stored and shown separately from word-count estimates.

---

### Edge Cases

- Older state with legacy relay shapes, a missing lock or decisions list: readers accept and report; writers upgrade on first write.
- Clock jumps or close-together writes: times never go backwards within a record.
- Resume with a missing worktree, gone branch, or ambiguous run name: the CLI reports and refuses to guess.
- Undeclared changes at a checkpoint; prose carrying a malformed or non-final machine-readable block.
- Totals over spawns that overlap, run zero-length, or are missing.
- A lock held by a dead process on its recorded host, or a live one elsewhere; only the former is stale.
- A failed verify record then a passing one: the latest decides; none at all is refused, not assumed passing.
- Analysis findings needing a user decision while fast mode is on: never auto-answered.

## Requirements *(mandatory)*

### Functional Requirements

**State integrity and single writer (S1, S2, S7)**

- **FR-001**: The system MUST record every stage completion, spawn entry, user wait, settled answer and status change through a single write interface that stamps, validates, writes atomically and commits the checkpoint; the orchestrator MUST NOT hand-edit state.
- **FR-002**: Where the state-writing tooling cannot run, the system MUST halt with a clear message, never fall back to manual state editing.
- **FR-003**: The system MUST validate state against the current schema (stage, status, timeline kind and history event vocabularies, required fields per stage) before every write and on demand, reporting violations with location. History events are closed, documented in `state.md`: `complete`, `verify-pass`, `verify-fail`, `approved`, `gate-override`, `aborted`, `pr-open`, `resumed`; anything else is reported.
- **FR-004**: Recorded timestamps MUST be real and non-decreasing within their record; every spawn and stage transition recorded exactly once.
- **FR-005**: The system MUST guard each run against concurrent writers with a lock recording owner, host, harness and time; writes MUST be refused under a live lock, which MUST be visible in reports. A lock is stale only on its recorded host when the owner process is gone; elsewhere never automatically; every takeover MUST be explicit. The same lock guards a pending run, living beside its pending file.

**Enforced gates (S3, S4)**

- **FR-006**: The system MUST refuse illegal stage transitions: review requires the latest verify record (Key Entities) to pass; publishing a PR requires a recorded approval decision; implementation requires analysis recorded as clean, remediated, or explicitly user-overridden. A gate override MUST be a normal decision record entry (stage, question ID, answer, auto=false, time) in the approver's veto list.
- **FR-007**: The system MUST validate every role's final machine-readable block (envelope, findings, verdict shapes) and reject malformed output; retry-once then applies.

**Accurate reporting and audit (S5, S6, S18)**

- **FR-008**: Settled answers MUST move to an append-only decision record (stage, question ID, answer, auto flag, time) before the stage's relay is cleared; the approver package MUST list every auto-accepted answer for veto.
- **FR-009**: Spawn start and end times MUST be stored; agent elapsed time MUST be the union of spawn intervals, human time the union of recorded user-wait intervals, reported separately; their sum never exceeds wall-clock time and no report subtracts summed parallel durations from it.
- **FR-010**: Where a harness reports usage, the system MUST label it separately from word-count estimates.

**Recovery and portability (S8, S13, S14, S15)**

- **FR-011**: The CLI's read and write commands MUST be covered by fixture tests over every accepted state version, pending runs, state copies in later worktrees, missing worktrees, ambiguous names, legacy relay shapes.
- **FR-012**: The system MUST provide a rebind command that validates a moved run's branch and rewrites its stored paths; sharing the run's home alone MUST be documented as not moving it.
- **FR-013**: The system MUST ship a fixture repository, a golden-run checklist per harness, and automated kill-and-resume tests; the live two-harness golden run is recorded after merge.
- **FR-014**: Per-adapter conformance MUST verify a read-only role cannot edit files where enforceable, and document the limitation where not.

**Configuration and setup (S10, S11)**

- **FR-015**: Adapters MUST NOT ship default models except where the harness requires them; personal model choices MUST live in the user's factory configuration; the installer MUST print the effective model per role; an automated check MUST keep documented and shipped defaults aligned.
- **FR-016**: On missing setup for the current harness, preflight MUST name the exact setup command and offer to run it, as for a missing scaffold.

**Checkpoint safety (S12)**

- **FR-017**: Every role's final output MUST declare each file it changed; a checkpoint MUST commit only the spec directory plus exactly that list, report anything else, and never commit undeclared changes.

**Automation (S9)**

- **FR-018**: Continuous integration MUST run the full automated suite on every change, re-render generated output for every harness and fail on any drift, and check the installer's syntax.

**Hardening and context (S16, S17, S19)**

- **FR-019**: The system MUST offer a cleanup preview for stale pending files that deletes nothing by default; deletion MUST be explicit. A pending file is stale when its run has a worktree state or has ended (`pr-open`/`aborted`); the run's only state MUST NEVER be one.
- **FR-020**: The installer MUST validate its arguments and fail with a clear usage message, not a crash, when a value is missing.
- **FR-021**: Pen design rules MUST live in one reference; duplicated prose is removed from the orchestrator and redundant references without losing any rule.

**Compatibility and delivery**

- **FR-022**: Readers MUST accept state versions 1 through the current one, including legacy relay shapes; writers MUST upgrade a run on first write; saved runs MUST keep resuming unchanged.
- **FR-023**: The change MUST be delivered as one run and one pull request, ordered by the milestones in `factory/brief.md`; the build re-renders all harnesses and fails on any generated-output diff.
- **FR-024**: Each delivered S-item MUST have its design decision recorded in `DESIGN.md` with or before its implementation. The same change MUST deliberately correct the contradicted sentences: manual-write fallback in `DESIGN.md` and `state.md`, `docs/product-brief.md` §14, `README.md`.

### Key Entities

- **Run state**: the single record of where a run is: stage, status, mode, harness, timestamps, waits, ledger, decisions, history.
- **Transition record**: a history entry proving a stage or gate: vocabulary-checked event (FR-003's list), time, commit, harness.
- **Verify record**: a `verify` history entry written through the CLI after the orchestrator re-runs build and test, carrying commands and pass/fail; the review gate reads the latest one.
- **Decision record**: an append-only entry per settled answer, keeping the auto flag so fast-mode choices can be vetoed.
- **Spawn interval**: one role execution's start and end, feeding the union-based effort computation.
- **Run lock**: owner, host, harness and time, guarding one run — worktree state and, before that, its pending file — against concurrent writers.
- **Adapter configuration**: per-harness defaults and personal overrides, effective value reportable per role.
- **Conformance fixture and golden-run result**: the fixture repository, its checklist, the recorded per-adapter results.

### Quality and Verification Constraints

- **Data integrity**: atomic validated writes, append-only decisions and timeline, non-decreasing timestamps, writer-only upgrades.
- **Security**: no undeclared files or secrets in checkpoints; read-only roles cannot edit or the limitation is disclosed; no personal models in shared adapters.
- **Error and resource limits**: retry-once-then-halt; lock takeover explicit; cleanup preview-first.
- **Compatibility**: state versions 1–3 readable, legacy question shapes usable, saved runs resumable at their recorded stage.
- **Dependencies**: standard-library-only tooling; a new runtime dependency needs a stated reason in the plan.
- **Observability**: every spawn, transition, wait and decision visible in state and the run report.
- **Verification**: fixture tests per CLI command, a CI regression suite, the 005/006 replay, the golden-run checklist on two harnesses.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every state mutation goes through the CLI writer, asserted by exercising each mutating command in the automated suite, and validation reports zero anomalies in the states those runs produce; zero hand-edited fields appear.
- **SC-002**: Replaying runs 005 and 006 reports every stability brief §3 defect as the required core with zero false passes; appended extras carry a written reason.
- **SC-003**: With parallel reviews, human plus agent time stays within wall-clock time in 100% of test runs, agent effort the union of spawn intervals, human time the union of user-wait intervals.
- **SC-004**: Every auto-accepted answer of every stage appears in the approver's veto list before publication.
- **SC-005**: Every illegal transition, malformed output and concurrent write attempt is refused in the automated suite, a test per refusal.
- **SC-006**: A run killed at each stage of the fixture suite resumes with zero repeated questions, zero redone tasks and zero duplicate branches, worktrees or PRs.
- **SC-007**: Continuous integration runs the whole suite on every change and blocks any source/generated drift within one change cycle.
- **SC-008**: Checkpoints commit only declared files in 100% of test runs, and no personal model configuration ships in any adapter.

## Assumptions

- Scope: all of S1–S19 (P0–P2) plus the context trim (consolidated Pen design rules, prose the CLI writer makes redundant); the state schema advances one version.
- State writes run through the Python 3 CLI only: thin entry script, logic in modules the renderer copies into `dist/`; a missing runtime halts the run.
- Only the Claude Code adapter ships default models (opus/sonnet); the rest inherit session models; personal OpenCode choices move to the user's factory configuration.
- Runs 005 and 006, from git history, are SC-002's validation fixtures; "Harness-agnostic factory design and plan.md" moves into `docs/`, marked implemented.
- Out of scope: renaming the repository, and the brief's §6 exclusions (automatic merge or deploy, hosted dashboard, multi-repository features, a database, automatic worktree deletion).
- Tests run through the standard-library runner, discovery extended as new test folders appear.
- Judgement stays in roles; only mechanical bookkeeping (time, vocabulary, file write, transition check) moves into code.
