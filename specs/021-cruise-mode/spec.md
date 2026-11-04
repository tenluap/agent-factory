# Feature Specification: Cruise mode

**Feature Branch**: `021-cruise-mode`

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Add a cruise mode to the software factory: like YOLO, it auto-approves and auto-accepts everything (relay questions answered with the recommended answer, permissions granted, approver gates passed) with no user input, but the run always stops at the open-PR flow and never opens a PR without the user's explicit approval." (settled decisions Q1-Q7 and confirmed defaults in `factory/brief.md`)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Unattended run up to the approver gate (Priority: P1)

A user starts `/factory <feature> --cruise` and walks away. The run grills itself, specifies, implements, reviews and fixes without asking anything. The first and only time it waits on the user (barring a failure halt) is the approver gate, where the user sees everything that was decided on their behalf.

**Why this priority**: The feature's whole value: a run needing no attention until there is a finished change to judge.

**Independent Test**: Start a cruise run on a small fixture feature and confirm the run reaches the approver gate with zero user waits recorded in the run's timeline before the `approver` entry.

**Acceptance Scenarios**:

1. **Given** a new run started with `--cruise`, **When** the orchestrator reaches initial grilling, **Then** it answers its own frontier with its recommended answers, records each answer as auto-accepted, writes `brief.md` and continues to the worktree with no wait.
2. **Given** a cruise run, **When** any agent returns `needs_input`, **Then** every question is answered with its recommended answer and the stage continues with no wait.
3. **Given** a cruise run, **When** a question carries `requires_user: true` (for example the plan's test-seam confirmation, or a design scope, identity or exception decision) or comes from `analyze.pending_clarify`, **Then** it is answered with its recommended answer and recorded with the cruise-override marker.
4. **Given** a cruise run on a full chain, **When** analyze still has CRITICAL or HIGH findings after the second loop, **Then** the run proceeds to implement with no wait, records the choice with the cruise-override marker, and carries the unresolved findings to the approver.
5. **Given** a cruise run, **When** it reaches the approver gate, **Then** the orchestrator notifies the user and waits.

---

### User Story 2 - Publishing always needs the user's Approve (Priority: P1)

Whatever cruise auto-resolved, the user stays in control of what leaves the machine. Cruise stops at the existing approver gate, and nothing is pushed and no PR is created until the user picks Approve.

**Why this priority**: The safety boundary that makes unattended operation acceptable; without it cruise is unsafe to offer.

**Independent Test**: Run cruise to the approver gate and confirm the branch does not exist on the remote, no PR exists, and `decisions` holds no `approved` record until the user answers.

**Acceptance Scenarios**:

1. **Given** a cruise run at the approver gate, **When** the user has not answered, **Then** the branch is not pushed, no PR exists, and the run's status is waiting on the user.
2. **Given** a cruise run at the approver gate, **When** the user picks Approve, **Then** the PR step runs exactly as it does without cruise.
3. **Given** a cruise run at the approver gate, **When** the user picks Request changes, **Then** the fix, verify and re-review loop runs under cruise (its questions auto-answered) and returns to the approver gate, which waits again.
4. **Given** a cruise run at the approver gate, **When** the user picks Abort, **Then** the run is aborted exactly as without cruise.
5. **Given** any cruise run, **When** any step would record approval, **Then** no approval is ever recorded automatically and the approver gate is never auto-answered.

---

### User Story 3 - Veto list shows what cruise decided (Priority: P1)

At the approver gate the user reviews every decision cruise made, with the decisions that bypassed a normal protection listed first so they can veto them with Request changes.

**Why this priority**: Cruise overrides real protections; the user must see each override before publishing.

**Independent Test**: Run cruise through a stage that raises a protected question and an auto-accepted ordinary question, and confirm the approver screen lists the protected one under cruise overrides and the ordinary one under auto-accepted answers.

**Acceptance Scenarios**:

1. **Given** a cruise run with auto-answered questions, **When** the approver screen is shown, **Then** the veto list has two groups: first cruise overrides (protected questions, auto-resolved halts, accepted setup offers), then ordinary auto-accepted answers, each entry naming its stage, question and answer.
2. **Given** a cruise run whose grilling was self-answered, **When** the approver screen is shown, **Then** every self-answered grilling answer appears in the ordinary auto-accepted group.
3. **Given** a cruise run where analyze-loop exhaustion auto-proceeded, **When** the approver screen is shown, **Then** that decision appears under cruise overrides and the unresolved analyze findings are shown.
4. **Given** a cruise run where nothing was overridden, **When** the approver screen is shown, **Then** the cruise-override group says it is empty rather than being omitted.

---

### User Story 4 - Turning cruise on and off (Priority: P2)

A user opts in with `--cruise` on a new run or a resume, and opts out with `--no-cruise`. Contradictory flags are named, never silently resolved.

**Why this priority**: Needed to use the mode; builds on the existing flag pattern.

**Independent Test**: Start runs with each flag combination and confirm the stored `mode` and the rejection of `--cruise` with `--no-fast`.

**Acceptance Scenarios**:

1. **Given** a new run with no cruise flag, **When** it is created, **Then** `mode.cruise` is false and behaviour equals today's.
2. **Given** a new run with `--cruise`, **When** it is created, **Then** `mode.cruise` and `mode.fast` are both true.
3. **Given** flags `--cruise --no-cruise` (or the reverse), **When** they are parsed, **Then** the last one wins.
4. **Given** flags that leave cruise on together with `--no-fast`, in any order, **When** they are parsed, **Then** the orchestrator names the conflict and asks the user to drop one; nothing is created or changed.
5. **Given** a paused or halted run, **When** it is resumed with `--cruise` or `--no-cruise`, **Then** `mode.cruise` is updated before the stage restarts.
6. **Given** a cruise run resumed with `--no-fast` and no `--no-cruise`, **When** the flags are parsed, **Then** the conflict is named and the run is not resumed until the user corrects the flags.
7. **Given** a state file written before this feature (no `mode.cruise`), **When** it is resumed, **Then** it is read as cruise off and stays valid.

---

### User Story 5 - Setup offers, intake and preflight under cruise (Priority: P2)

On a repository that needs one-off setup, cruise accepts each offer with its recommended default so the run still needs no input, and preflight warns that the harness itself may still prompt.

**Why this priority**: Without it a cruise run on a fresh repository stops at its first setup offer.

**Independent Test**: Start a cruise run in a repository without `.specify/` and confirm SpecKit is initialised, a constitution drafted from the repository is committed, and both acceptances appear in the veto list's cruise-override group.

**Acceptance Scenarios**:

1. **Given** a cruise run in a repository without `.specify/` (or missing a SpecKit skill), **When** preflight reaches the setup offer, **Then** it runs the `specify init` command from the harness file and drafts the constitution from the repository with no question, recording the acceptance.
2. **Given** a cruise run where build or test commands were detected but not documented, **When** preflight would confirm them, **Then** the detected commands are recorded without a question and the acceptance is recorded.
3. **Given** a cruise run with a UI diff and no `impeccable` skill, **When** review would offer the global install, **Then** it runs the install with no question and records the acceptance.
4. **Given** a cruise run whose request is ambiguous between exploration and delivery, **When** intake classifies it, **Then** it takes the delivery path with no question and records the choice.
5. **Given** a cruise run on any harness, **When** preflight runs, **Then** the orchestrator tells the user once that the session may still show harness permission prompts unless it was launched with the no-prompt option named in that harness's adapter file, and continues without waiting.
6. **Given** any adapter, **When** its harness file is read, **Then** it documents that harness's no-prompt launch option, or states that the harness has none.

---

### User Story 6 - Failures and stop points still reach the user (Priority: P2)

Cruise removes decisions, not safety stops. A run that cannot make progress halts and notifies, and an explicit `--stop-at` still pauses.

**Why this priority**: Auto-resolving a failure would hide broken work behind an unattended run.

**Independent Test**: Force a red build after the fix retry in a cruise run and confirm the run halts, notifies, and waits.

**Acceptance Scenarios**:

1. **Given** a cruise run, **When** the build stays red after the one fix retry, **Then** the run halts and notifies as today.
2. **Given** a cruise run, **When** the same agent fails twice, **Then** the run halts and notifies as today.
3. **Given** a cruise run, **When** one stage returns `partial` three times with no new commit, **Then** the stall cap halts the run as today.
4. **Given** a cruise run with `--stop-at <stage>`, **When** that stage is next, **Then** the run pauses there as today.
5. **Given** a cruise run, **When** questions are auto-accepted, **Then** no notification is sent for them; the batch is reported as a log line only. Notifications go out only for real waits (the approver gate, failure halts, a stop point).

### Edge Cases

- A question with no usable recommendation (missing, or a legacy one too unclear to match): cruise invents no answer. The orchestrator shows that question to the user and waits, notifying them, and records the gap so it shows in the run's timeline.
- Cruise turned on by resume while a relay round is open: the unanswered questions in that round are auto-answered under cruise rules; answers already given are preserved.
- Cruise turned off by resume (`--no-cruise`): later protected questions, decision halts and setup offers go back to today's behaviour; decisions already recorded with the cruise-override marker stay in the veto list. `mode.fast` keeps its current value.
- Lite-to-full escalation under cruise happens as today; the added clarify and grill-with-docs rounds are auto-answered.
- A design gate exception auto-accepted under cruise: it is recorded with the cruise-override marker in the run's decisions and in the design context like any accepted exception; the approver gate still applies the design approval rule.
- Hard stops that are not decisions stay stops under cruise: a missing harness capability, an unavailable model selection, a missing required skill (including `ponytail` or `tdd` at implement), an unsupported UI framework at plan, a state-writer failure, and an unknown flag.
- Brainstorm path (exploration wording): the orchestrator answers its own brainstorm frontier and confirms its recommended direction, as for grilling; the optional visual companion is not offered.
- A setup command accepted under cruise fails (for example `specify init` or the `impeccable` install): it is handled as a failure, halting and notifying, not retried with another choice.

## Requirements *(mandatory)*

### Functional Requirements

**Mode and flags**

- **FR-001**: The orchestrator MUST accept `--cruise` and `--no-cruise` on a new run and on `resume`, last one wins, off by default, and store the result as `mode.cruise` (boolean) in run state.
- **FR-002**: Cruise on MUST set `mode.fast` to true.
- **FR-003**: When the final flags leave cruise on (from flags or from a resumed run's stored mode) and `--no-fast` is present, the orchestrator MUST name the conflict and ask the user to correct it, changing no state.
- **FR-004**: A state file with no `mode.cruise` MUST stay valid and be read as cruise off. The new field and the cruise-override marker MUST be additive to the state schema.
- **FR-005**: Every state write for cruise (mode, answers, decisions, markers) MUST go through the state writer; there is no hand-edit path.

**Answering under cruise**

- **FR-006**: Under cruise the orchestrator MUST answer its initial grilling frontier (and the brainstorm frontier on the idea path) with its own recommended answers, record each as auto-accepted, take its recommended chain, write `brief.md` and continue without a wait.
- **FR-007**: Under cruise every relay question MUST be answered with its recommended answer, including `requires_user: true` questions and `analyze.pending_clarify` questions.
- **FR-008**: Each answer to a `requires_user: true` or `pending_clarify` question accepted under cruise MUST carry a cruise-override marker distinct from the ordinary auto-accept flag.
- **FR-009**: Without cruise, fast mode MUST keep today's protections: protected and `pending_clarify` questions are never auto-answered and initial grilling stays interactive.
- **FR-010**: A question with no usable recommendation MUST be shown to the user and waited on, under cruise as elsewhere; cruise never invents an answer.

**Halts and setup offers**

- **FR-011**: Under cruise, analyze-loop exhaustion MUST resolve to "proceed to implement" with no wait, recorded with the cruise-override marker, and the unresolved findings MUST be shown at the approver gate.
- **FR-012**: Under cruise, failure halts MUST still halt and notify: a red build after the retry, a second failure of the same agent, and the stall cap. Hard stops listed in Edge Cases MUST still stop.
- **FR-013**: Under cruise, each one-off setup offer MUST be accepted with its recommended default and recorded with the cruise-override marker: `specify init` plus a constitution drafted from the repository, confirmation of detected build and test commands, the global `impeccable` install, and the ambiguous-intake question (answered delivery).
- **FR-014**: `--stop-at` MUST keep pausing the run under cruise.

**Publishing**

- **FR-015**: Cruise MUST stop at the existing approver gate and MUST NOT auto-answer it or record an approval automatically.
- **FR-016**: No push of the branch and no PR creation may happen in a cruise run before the user picks Approve.
- **FR-017**: Request changes and Abort MUST behave as today; after Request changes the fix, verify and re-review loop runs under cruise and returns to the approver gate.

**Visibility**

- **FR-018**: Under cruise the approver screen MUST show the veto list in two groups: cruise overrides first (protected questions, auto-resolved halts, accepted setup offers), then ordinary auto-accepted answers, each naming stage, question and answer. An empty group is stated, not omitted.
- **FR-019**: Under cruise the orchestrator MUST notify only when it actually waits on the user (the approver gate, failure halts, stop points, a question with no recommendation). The auto-accept batch notice MUST become a log line.
- **FR-020**: Cruise preflight MUST tell the user, once per start or resume, that the session may still show harness permission prompts unless launched with the harness's no-prompt option, then continue.
- **FR-021**: Each adapter's harness file MUST document its harness's no-prompt launch option (for example Claude Code `--permission-mode bypassPermissions`) or state that it has none. Core files MUST NOT name it.

**Documentation and build**

- **FR-022**: `DESIGN.md` MUST record cruise mode before `core/` and `adapters/` change; `CONTEXT.md` MUST define cruise mode and the cruise override; the `/factory` argument hint MUST list the new flags.
- **FR-023**: Every harness MUST still render cleanly, and existing tests MUST stay green.

### Key Entities

- **Cruise mode** (`mode.cruise`): the run-level switch. On means no user input until the approver gate except real waits. Implies fast mode.
- **Cruise override**: a decision cruise made that a normal run would have put to the user: a protected or `pending_clarify` answer, an auto-resolved decision halt, or an accepted setup offer. It is recorded in `decisions` with a marker that tells it apart from an ordinary auto-accepted answer (exact shape is a plan decision).
- **Veto list**: the approver screen's list of decisions made on the user's behalf, grouped under cruise into cruise overrides and ordinary auto-accepted answers.
- **No-prompt launch option**: a harness's own way to start a session that does not ask for tool permissions, documented per adapter and never set by the factory.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A cruise run of a fixture feature with no failure reaches the approver gate with zero user waits recorded in its timeline before the approver entry.
- **SC-002**: In 100% of cruise runs, the branch is absent from the remote and no PR exists until an `approved` decision is recorded by the user.
- **SC-003**: 100% of decisions cruise made against a normal protection (protected questions, decision halts, setup offers) appear in the veto list's cruise-override group; none appear only in the ordinary group.
- **SC-004**: A run without `--cruise`, and any state file from before this feature, behaves exactly as today: the same questions are protected, the same halts wait, and existing tests pass unchanged.
- **SC-005**: Every flag combination leaving cruise on with `--no-fast` is rejected with the conflict named, and no run state is created or changed by it.
- **SC-006**: All five harnesses render with no error after the change.

## Assumptions

- The cruise-override marker's exact shape (a field on answers and decisions, or a new decision `kind`) is settled at plan, as long as it is additive and written through the state writer.
- Turning cruise off on resume leaves `mode.fast` at its current value; the user can pass `--no-fast` with `--no-cruise` to turn both off.
- Harness permission prompts are outside the factory's control; cruise only discloses them. Changing a harness's permission mode programmatically, auto-merging and auto-approving the PR gate are out of scope.
- The constitution drafted under cruise is derived from the repository's files and listed in the veto list.
- Brainstorming under cruise follows the general rule (every question answered with its recommendation); the visual companion needs its own consent and is skipped.
- Validation uses the existing build and test commands; agent-driven flow checks go in `DESIGN.md`'s validation plan.
