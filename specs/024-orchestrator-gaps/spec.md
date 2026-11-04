# Feature Specification: Close Orchestrator Bookkeeping Gaps

**Feature Branch**: `024-orchestrator-gaps`

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Close orchestrator bookkeeping gaps found in run 018: CLI writers for review.round/fix_rounds and review-stage relay records, correct the overrun excess wording in ledger-add, and raise the round-1 reviewer budget." Source backlog: `claude-factory-018-orchestrator-gaps` (four observations from run 018-live-conformance, checked against main c385ab5).

## User Scenarios & Testing *(mandatory)*

The "user" of this feature is the factory orchestrator (and the human who reads a run's state and records afterwards). Every gap below forced the orchestrator in run 018 either to hand-edit `state.json` or a run file, or to record a misleading fact. The state CLI is the single writer (state.md, "CLI"); after this feature no review-loop bookkeeping needs a hand edit.

### User Story 1 - Review and fix counters are written by the CLI (Priority: P1)

During review, the orchestrator checkpoints each completed review round and each completed fix round through the state CLI. The CLI records the current review round number and the count of completed fix rounds, so the fix-round cap (SKILL.md step 7: an automatic fix runs only while `review.fix_rounds < 2`) and the benchmark score (`bench.py score`, metrics `review_rounds` and `fix_rounds`) read true values without any hand edit of `state.json`.

**Why this priority**: The fix-round cap is a run-safety rule. With both counters stuck at 0 the cap never triggers through the CLI, and run 018 broke the "never edit state.json by hand" rule (commit 9dc242c) to keep it working.

**Independent Test**: Drive a throwaway fixture run through `checkpoint review` (round folder 1 with a verdict), `checkpoint fix`, `checkpoint review` (round folder 2), `checkpoint fix`; read `state.json` after each step and confirm `review.round` and `review.fix_rounds` without editing the file.

**Acceptance Scenarios**:

1. **Given** a run at stage `review` whose spec directory holds `factory/reviews/round-1/verdict.json`, **When** the orchestrator runs `checkpoint review`, **Then** `review.round` is 1.
2. **Given** a run at stage `fix` with `review.fix_rounds` 0, **When** the orchestrator runs `checkpoint fix`, **Then** `review.fix_rounds` is 1.
3. **Given** a run that completed fix round 1 and review round 2 (`round-2/verdict.json` present), **When** `checkpoint review` and then `checkpoint fix` run, **Then** `review.round` is 2 and `review.fix_rounds` is 2, and the step-7 cap stops further automatic fixes.
4. **Given** a `checkpoint fix` whose state write landed but whose commit failed, **When** the orchestrator retries the same checkpoint, **Then** `review.fix_rounds` is incremented once in total, not twice.
5. **Given** a completed run, **When** `bench.py score` reads its state, **Then** the review and fix round metrics equal the rounds the run actually performed.

---

### User Story 2 - Relay records for user-confirmed questions are rendered by the CLI (Priority: P2)

When a question that needs the user (`requires_user: true`) is answered — including one raised by a review verdict, such as a test-scope confirmation for a confirmed blocking finding — the CLI stores the answer and also writes the human-readable relay record `<spec_dir>/factory/relay/<stage>-<qid>.md`. Fixers, reviewers and the plan's `Confirmed:` line cite this record as the accepted-scope snapshot. SKILL.md step 7 documents how the orchestrator relays a verdict-raised question.

**Why this priority**: The record is the immutable evidence of explicit acceptance (engineering.md, "Confirmed test scope"). Hand-written records (run 018 `plan-Q1.md` and `review-Q1.md`) can drift from the stored answer, and nothing guarantees that they exist.

**Independent Test**: On a fixture worktree run, answer a `requires_user` review question through the CLI, supplying the full question; confirm the record file exists with the question, the options and the answer, that it is committed with the answer, and that `state.json` holds the same answer.

**Acceptance Scenarios**:

1. **Given** a worktree run whose open relay round stores question Q1 with `requires_user: true` for stage `review`, **When** the orchestrator records the answer, **Then** `factory/relay/review-Q1.md` exists and states the stage, the question id, the question title and text, each option, the answer, the answer time, and whether the answer was explicit, automatic, or a cruise override.
2. **Given** a verdict-raised question that is not yet stored in the relay, **When** the orchestrator records the answer and supplies the question in the protocol question shape, **Then** the CLI stores the question in the open round and renders the record from it.
3. **Given** an ordinary question without `requires_user`, **When** it is answered, **Then** no relay record is written and the existing answer behaviour is unchanged.
4. **Given** a record that already exists for the same stage and question id with the same answer, **When** the answer is recorded again, **Then** nothing changes; **Given** a different answer, **Then** the CLI refuses (exit 1) naming the existing record and writes nothing.

---

### User Story 3 - Detected overrun detail states the real excess (Priority: P3)

When `ledger-add` detects an overrun without a self-report, the issue detail states how far past the budget the spawn ran, not its total duration.

**Why this priority**: The current text ("ran 319s past its 300s budget" for a 319 s spawn) overstates the excess about seventeen times, and the retro and the approver read it as fact.

**Independent Test**: Record a 319-second spawn for a role with a 300-second budget and no self-report; read the `issues` record detail.

**Acceptance Scenarios**:

1. **Given** a 319 000 ms spawn of `spec-conformance` with a 300 s budget and no `--overrun`, **When** `ledger-add` runs, **Then** the recorded `unreported` overrun detail says the role ran 19 s past its 300 s budget and also states the 319 s total.
2. **Given** a spawn of 300 001 ms on a 300 s budget, **When** `ledger-add` runs, **Then** the detail states an excess of 1 s (the excess is rounded up, so a detected overrun never reads as 0 s).
3. **Given** a spawn that carries a self-report, **When** `ledger-add` runs, **Then** the self-reported detail is recorded unchanged.

---

### User Story 4 - Round-1 reviewers get a larger budget (Priority: P3)

Before spawning reviewers, the orchestrator asks the CLI for each reviewer's budget for the current review round. A full-diff review (round 1, or an escalated full-mode re-run) gets the round-1 reviewer budget, 600 s by default. A delta round keeps the role's normal budget (300 s by default). Overrun detection after the spawn uses the same budget the spawn was given.

**Why this priority**: In run 018 all three round-1 reviewers overran the 300 s budget, and every delta review fit. The resulting `unreported` overrun issues are noise that feeds the retro's halt-cluster signal.

**Independent Test**: With no budget configuration, resolve the `code-standards` budget for round 1 and for round 2; then record a 450-second round-1 review spawn and confirm that no overrun issue is recorded.

**Acceptance Scenarios**:

1. **Given** no budget configuration, **When** the orchestrator resolves a reviewer budget for round 1, **Then** the CLI prints 600 seconds and the matching deadline; **When** it resolves round 2, **Then** the CLI prints 300 seconds.
2. **Given** a round-1 reviewer spawn of 450 s, **When** `ledger-add` records it as a full-diff review, **Then** no overrun issue is recorded; **Given** a delta-round spawn of 450 s, **Then** an `unreported` overrun with an excess of 150 s is recorded.
3. **Given** a configured per-role budget for a reviewer, **When** a round-1 budget is resolved, **Then** the larger of the per-role budget and the round-1 reviewer budget applies.
4. **Given** a verdict carrying `escalate` that re-runs the round in full mode, **When** the orchestrator resolves reviewer budgets for the re-run, **Then** the round-1 (full-diff) budget applies.

---

### Edge Cases

- `checkpoint review` runs with no `round-<n>/verdict.json` in the spec directory (for example an old fixture): `review.round` stays unchanged and the checkpoint proceeds as today.
- Round folders exist out of order or with gaps: `review.round` takes the highest round number that has a verdict, and it never decreases.
- An escalated full-mode re-run reuses the same round number: `review.round` does not change.
- `checkpoint fix` runs again after the stage has already moved on (a repeated call): the counter does not increment a second time. This mirrors the `remediate` counter rule (ADR 0006).
- An active design run reserves the fix attempt before spawning (`review.pending_design_fix`) without incrementing the counter; after the attempt it clears the reservation, then `checkpoint fix` counts the attempt once (design-code-mapping.md §5 order). A legacy reservation whose `attempt` already equals the current `review.fix_rounds` is not counted again.
- A `requires_user` question is answered on a pending run (no worktree, no spec directory): the answer is stored and no record is written, because the record needs a spec directory.
- Question ids repeat across review rounds (for example Q1 in round 1 and Q1 in round 2): the orchestrator gives verdict-raised questions round-unique ids (for example `R2-Q1`, as run 022 did), and the immutability refusal in Story 2 catches a collision instead of overwriting evidence.
- The budget is resolved for a role that is not a reviewer (for example `fixer`) with a round given: the round is ignored and normal resolution applies.
- Budget configuration is missing or malformed: every value falls back per entry (round-1 reviewer budget to 600, others to 300), and the run never fails.

## Requirements *(mandatory)*

### Functional Requirements

**Review counters**

- **FR-001**: `checkpoint review` MUST set `review.round` to the highest `n` for which `<spec_dir>/factory/reviews/round-<n>/verdict.json` exists. It MUST NOT decrease the value, and it MUST leave the value unchanged when no such verdict exists.
- **FR-002**: `checkpoint fix` MUST increment `review.fix_rounds` by exactly 1 per completed fix round, only when the run's current stage is `fix`. A retried or repeated checkpoint for the same fix round MUST NOT increment it again.
- **FR-003**: `checkpoint fix` MUST NOT increment `review.fix_rounds` for an attempt that a design reservation in `review.pending_design_fix` already counted (its `attempt` equals the current counter). Design reservations made under this feature do not increment the counter; the orchestrator clears the reservation, then `checkpoint fix` counts the attempt.
- **FR-004**: The checkpoint result MUST report the resulting `review.round` and `review.fix_rounds` for `review` and `fix` checkpoints, so the orchestrator reads the cap state without opening `state.json`.

**Relay records**

- **FR-005**: The `answer` writer MUST accept an optional full question in the protocol question shape (protocol.md, "Questions"). When the open round does not yet store that question id, or stores only its id, the writer MUST store the supplied question there.
- **FR-006**: When the answered question carries `requires_user: true` and the run has a worktree, the writer MUST render `<spec_dir>/factory/relay/<stage>-<qid>.md`, where `<stage>` is the relay's stage. The record MUST state the stage, the question id, the title, any text, every option (id, label, description), the answer, the answer time, and the answer's origin (explicit, `auto`, or `cruise_override`).
- **FR-007**: The record MUST be committed in the same commit as the answer's state write.
- **FR-008**: An existing record MUST NOT be overwritten. Re-recording an identical answer is a no-op; a different answer MUST be refused with exit 1, naming the record path, with nothing written.
- **FR-009**: An answer to a question without `requires_user: true` MUST behave exactly as today and write no record. When a record is due, a `<stage>` or `<qid>` outside `[A-Za-z0-9_-]+` MUST be refused with exit 1, with nothing written.
- **FR-010**: SKILL.md step 7 MUST document the review-stage relay path: how a verdict-raised `requires_user` question is relayed (stored with the full question, round-unique id, answered through the writer, cited by its record path), and that cruise answers it only with `--cruise-override`, as protocol.md requires.

**Overrun wording**

- **FR-011**: A detected (`unreported`) overrun detail MUST state the excess, defined as the ledger duration minus the budget and rounded up to whole seconds, plus the budget and the total duration. Example: `spec-conformance ran 19s past its 300s budget (319s total) without a self-report`.
- **FR-012**: Self-reported overrun details MUST be recorded unchanged.

**Round-1 reviewer budget**

- **FR-013**: The budget read command MUST accept the review round, or a full-review flag, for a reviewer role. For a full-diff review (round 1, or an escalated full-mode re-run) it MUST resolve the round-1 reviewer budget. That budget is the configured round-1 reviewer value when it is a positive integer, else 600 seconds, and never less than the role's normal budget.
- **FR-014**: Delta-round reviewer spawns and every non-reviewer role MUST resolve exactly as today (per-role value, then `default_s`, then 300).
- **FR-015**: The reviewer roles are `security-reviewer`, `code-standards`, `spec-conformance`, `ui-reviewer` and `ux-reviewer`. `review-judge` keeps its normal budget.
- **FR-016**: `ledger-add` overrun detection MUST compare a reviewer spawn against the budget that spawn was given (round-1 or delta), using the same round or full-review input as the budget read.
- **FR-017**: A missing or malformed round-1 configuration value MUST fall back to 600 without failing the run.
- **FR-018**: SKILL.md step 7 MUST pass the round (or the full-review mode) to the budget read before each reviewer spawn and to `ledger-add` after it.

**Governance and delivery**

- **FR-019**: DESIGN.md MUST record each behaviour change first (Constitution I). state.md ("Checkpoint", "CLI", "Schema"), SKILL.md and design-code-mapping.md §5 (reservation order) MUST describe the new writer behaviour and flags.
- **FR-020**: Core files MUST stay harness-neutral (Constitution II). Every harness MUST still render cleanly, and no build output may be tracked (Constitution III).
- **FR-021**: The existing test suite MUST still pass, and each new behaviour above MUST be covered by tests that run through the CLI's public seams.

### Key Entities

- **Review counters** (`state.review.round`, `state.review.fix_rounds`): the current review round number and the number of completed fix rounds. The fix-round cap and benchmark scoring read them.
- **Relay record** (`<spec_dir>/factory/relay/<stage>-<qid>.md`): an immutable, human-readable snapshot of one `requires_user` question and its accepted answer. Plans, fixers and reviewers cite it as acceptance evidence.
- **Overrun issue** (`state.issues[]`, kind `overrun`, cause `unreported`): a detected budget overrun whose detail states the excess, the budget and the total.
- **Round-1 reviewer budget**: the time allowance for a full-diff review spawn. It is configurable and defaults to 600 s; it sits next to the existing per-role and default budgets.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A run that completes two review rounds and two fix rounds ends with `review.round` = 2 and `review.fix_rounds` = 2, with zero hand edits of `state.json` (no commit touching `state.json` other than the writers' `factory:` commits).
- **SC-002**: The fix-round cap stops automatic fixing after exactly two fix rounds in 100% of fixture runs that drive the review loop through the CLI.
- **SC-003**: Every answered `requires_user` question on a worktree run has exactly one matching relay record, and its answer equals the stored answer, with zero hand-written records.
- **SC-004**: For any detected overrun, the stated excess equals the duration minus the budget (rounded up to whole seconds); a 319 s spawn on a 300 s budget states 19 s.
- **SC-005**: A round-1 reviewer spawn of up to 600 s with no configuration records zero overrun issues; delta-round spawns over 300 s are still recorded.
- **SC-006**: The build renders all five harnesses, and the full test suite passes.

## Assumptions

- The counters follow the brief's first option: `checkpoint review` and `checkpoint fix` set them. The alternative separate `review-record` writer is not added (Constitution V: extend an existing writer).
- The relay record is rendered for `requires_user` questions in any stage, not only review. Plan-stage test-scope confirmations (run 018 `plan-Q1.md`) had the same hand-written gap, and limiting the record to review would leave that gap open.
- The record format follows the hand-written run 018 records: a heading naming the stage, the question id and `requires_user`, then the answer with its origin and date, then the question body. Exact layout is a plan decision.
- 600 s is the round-1 reviewer default, as the backlog item suggests. Scaling the budget by diff size is out of scope.
- A hard stop or check-in for reviewers far past their budget (run 018's 23 869 s security review) is out of scope. Reviewers stay never-stopped, per the time-budget policy in DESIGN.md.
- Existing runs are compatible: no state schema version bump is needed, because `review.round` and `review.fix_rounds` already exist in the schema, and the new budget configuration key is optional.
- The verdict-raised question uses a round-unique id chosen by the orchestrator. The CLI does not invent ids.
